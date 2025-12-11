# main_dashboard.py
# Single-entry launcher that mounts existing Flask apps under path prefixes.
import os
import importlib.util
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from flask import Flask, send_from_directory, abort

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
        print(f"Failed to load {filepath}: {e}")

# Compose a dispatcher that serves root_app at "/" and sub-apps under their prefixes
application = DispatcherMiddleware(root_app.wsgi_app, mounted)

if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting unified server on http://{host}:{port}/")
    # Using werkzeug.run_simple for a simple dev server that runs the combined WSGI app
    run_simple(host, port, application, use_reloader=True, use_debugger=True)
