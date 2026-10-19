# main_dashboard.py
# Single-entry launcher that mounts existing Flask apps under path prefixes.
import os
import importlib.util
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from flask import Flask, send_from_directory, abort, redirect, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_flask_app_from_path(module_path):
    """
    Load a Python module from a path and return its `app` attribute (Flask instance).
    Raises an informative error if not found.
    """
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"Module file not found: {module_path}")
    spec = importlib.util.spec_from_file_location("loaded_module_" + os.path.basename(module_path).replace(".","_"), module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "app"):
        raise AttributeError(f"No 'app' Flask instance found in module: {module_path}")
    return getattr(mod, "app")

# Map URL prefix -> relative path to app.py inside your project
MOUNT_MAP = {
    "/encryption": os.path.join(BASE_DIR, "Encryption-decryption", "app.py"),
    "/sub":        os.path.join(BASE_DIR, "sub-apis", "app.py"),
    "/ret":        os.path.join(BASE_DIR, "ret-apis", "app.py"),
    "/bvs":        os.path.join(BASE_DIR, "bvs-apis", "app.py"),
    "/login":      os.path.join(BASE_DIR, "login", "app.py"),
}

# Root Flask app serves the main dashboard and static assets (if any)
root_app = Flask(__name__, static_folder=None)

@root_app.route("/")
def dashboard():
    # Try to serve dashboard.html from project root (your file).
    dashboard_path = os.path.join(BASE_DIR, "dashboard.html")
    if os.path.exists(dashboard_path):
        return send_from_directory(BASE_DIR, "dashboard.html")
    return "<h3>Dashboard file not found. Place dashboard.html in project root.</h3>", 404

# Optional: serve raw files (keys) under /keys/ (only for dev/staging; don't expose in prod)
@root_app.route("/keys/<path:filename>")
def serve_keys(filename):
    # SECURITY: this is only intended for local dev. Remove or protect in production.
    keys_dir = os.path.join(BASE_DIR, "Encryption-decryption", "Keys")
    full = os.path.join(keys_dir, filename)
    if os.path.exists(full) and os.path.commonpath([keys_dir, full]) == keys_dir:
        return send_from_directory(keys_dir, filename)
    abort(404)

# Load the other apps as WSGI apps
mounted = {}
for prefix, filepath in MOUNT_MAP.items():
    try:
        flask_app = load_flask_app_from_path(filepath)
        # Ensure the sub-apps don't attempt to rerun the server; they should only expose `app`.
        mounted[prefix] = flask_app.wsgi_app
        print(f"Mounted {filepath} -> {prefix}")
    except Exception as e:
        raise RuntimeError(f"Failed to mount {prefix} from {filepath}") from e

# Add simple redirects for requests to the exact mount prefix without a trailing slash.
# DispatcherMiddleware expects requests to include the trailing slash for sub-app root routes
# (e.g. '/sub/' to reach the sub-app's '/'). People often request '/sub' which would 404,
# so add redirects from '/sub' -> '/sub/'.
for prefix in list(MOUNT_MAP.keys()):
    route = prefix
    endpoint_name = f"redirect_{route.strip('/').replace('/', '_') or 'root'}"
    # view_func uses default arg to capture `route` value correctly in loop
    root_app.add_url_rule(route, endpoint=endpoint_name, view_func=(lambda r=route: redirect(r + '/')))

# Compose a dispatcher that serves root_app at "/" and sub-apps under their prefixes
_dispatch = DispatcherMiddleware(root_app.wsgi_app, mounted)

# --- Basic Auth gate over the entire dashboard (credentials from env) ---
import hmac
import base64

_AUTH_USER = os.environ.get("APP_AUTH_USER", "apic")
_AUTH_PASS = os.environ.get("APP_AUTH_PASS", "")


def _auth_ok(environ):
    if not _AUTH_PASS:
        return False
    hdr = environ.get("HTTP_AUTHORIZATION", "")
    if not hdr.startswith("Basic "):
        return False
    try:
        user, _, pw = base64.b64decode(hdr[6:]).decode("utf-8", "replace").partition(":")
    except Exception:
        return False
    return hmac.compare_digest(user, _AUTH_USER) and hmac.compare_digest(pw, _AUTH_PASS)


def application(environ, start_response):
    if not _auth_ok(environ):
        start_response(
            "401 Unauthorized",
            [("WWW-Authenticate", 'Basic realm="IBM Dashboard"'),
             ("Content-Type", "text/plain")],
        )
        return [b"Authentication required.\n"]
    return _dispatch(environ, start_response)


@root_app.route("/mounted")
def mounted_info():
    # Returns a small JSON summary of what was mounted at startup.
    return jsonify({"mounted_prefixes": list(mounted.keys())})

if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting unified server on http://{host}:{port}/")
    # Using werkzeug.run_simple for a simple dev server that runs the combined WSGI app
    # Enable threaded=True so the dev server can handle multiple simultaneous
    # requests (useful for lightweight staging). For production, run behind
    # a proper WSGI server like gunicorn with multiple workers.
    run_simple(host, port, application, use_reloader=False, use_debugger=False, threaded=True)
