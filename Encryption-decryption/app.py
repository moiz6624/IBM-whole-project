from flask import Flask, request, render_template_string
import os
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

# ==========================
#  MERGED ENCRYPTION LOGIC
# ==========================

def load_public_key(path):
    with open(path, 'rb') as f:
        return RSA.import_key(f.read())

def load_private_key(path):
    with open(path, 'rb') as f:
        raw_data = f.read()

        try:
            # Try importing raw (normal DER)
            return RSA.import_key(raw_data)
        except ValueError:
            # Try base64 decoding if needed
            decoded = base64.b64decode(raw_data)
            return RSA.import_key(decoded)

def encrypt(data, public_key_path):
    key = load_public_key(public_key_path)
    cipher = PKCS1_v1_5.new(key)
    return base64.b64encode(cipher.encrypt(data.encode())).decode()

def decrypt(data, private_key_path):
    key = load_private_key(private_key_path)
    cipher = PKCS1_v1_5.new(key)
    decoded = base64.b64decode(data)
    sentinel = b"decryption-error"
    return cipher.decrypt(decoded, sentinel).decode()

# ==========================
#        FLASK APP
# ==========================

app = Flask(__name__)

# Key paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_BASE = os.path.join(BASE_DIR, "Keys")

KEYS = {
    "sub": {
        "public": os.path.join(KEY_BASE, "subgateway.der"),
        "private": os.path.join(KEY_BASE, "private", "subgateway.der")
    },
    "ret": {
        "public": os.path.join(KEY_BASE, "retailergateway.der"),
        "private": os.path.join(KEY_BASE, "private", "retailergateway.der")
    }
}

# ==========================
#   HTML PAGE TEMPLATE
# ==========================

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>RSA Encryption / Decryption</title>
    <style>
      .dashboard-btn {
        display: inline-block;
        margin-bottom: 20px;
        padding: 10px 15px;
        background-color: #4f46e5; /* A nice purple/blue */
        color: white;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        transition: background-color 0.3s;
      }
      .dashboard-btn:hover {
        background-color: #3730a3;
      }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #f3f4f6;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 50px auto;
            background: white;
            padding: 30px 40px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 10px;
        }
        h2 {
            text-align: center;
            color: #111827;
        }
        label {
            display: block;
            margin-top: 20px;
            margin-bottom: 6px;
            font-weight: 500;
            color: #374151;
        }
        select, textarea, input[type="submit"] {
            width: 100%;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #ccc;
            font-size: 16px;
            margin-bottom: 10px;
            box-sizing: border-box;
        }
        input[type="submit"] {
            background-color: #2563eb;
            color: white;
            border: none;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #1e40af;
        }
        .result {
            margin-top: 20px;
            background-color: #f9fafb;
            padding: 15px;
            border-left: 6px solid #2563eb;
            border-radius: 6px;
            font-family: monospace;
            color: #111827;
            word-break: break-all;
        }
        .error {
            color: red;
            margin-top: 20px;
            background-color: #fef2f2;
            padding: 15px;
            border-left: 6px solid #dc2626;
            border-radius: 6px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
    <a href="/" class="dashboard-btn">← Back to Dashboard</a>
        <h2>RSA Encryption / Decryption Tool</h2>
        <form method="POST">
            <label for="type">Key Type:</label>
            <select name="type" id="type" required>
                <option value="sub" {% if key_type == 'sub' %}selected{% endif %}>Subscriber</option>
                <option value="ret" {% if key_type == 'ret' %}selected{% endif %}>Retailer</option>
            </select>

            <label for="mode">Operation:</label>
            <select name="mode" id="mode" required>
                <option value="encrypt" {% if mode == 'encrypt' %}selected{% endif %}>Encrypt</option>
                <option value="decrypt" {% if mode == 'decrypt' %}selected{% endif %}>Decrypt</option>
            </select>

            <label for="data">Input Text:</label>
            <textarea name="data" id="data" rows="5" required>{{ input_data }}</textarea>

            <input type="submit" value="Submit">
        </form>

        {% if result %}
        <div class="result">
            {{ mode.capitalize() }}ing "<strong>{{ input_data }}</strong>" using
            <strong>{{ key_type }}gateway</strong> →
            <br><br>
            <strong>Result:</strong> {{ result }}
        </div>
        {% endif %}

        {% if error %}
        <div class="error">
            <strong>Error:</strong> {{ error }}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

# ==========================
#        ROUTES
# ==========================

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    mode = None
    key_type = None
    data = None

    if request.method == "POST":
        key_type = request.form.get("type")
        mode = request.form.get("mode")
        data = request.form.get("data")

        try:
            if not key_type or not mode or not data:
                error = "Missing input fields"
            elif key_type not in KEYS:
                error = "Invalid key type selected"
            else:
                if mode == "encrypt":
                    result = encrypt(data, KEYS[key_type]["public"])
                elif mode == "decrypt":
                    result = decrypt(data, KEYS[key_type]["private"])
                else:
                    error = "Invalid operation mode"
        except Exception as e:
            error = f"Error: {str(e)}"

    return render_template_string(
        HTML_PAGE,
        result=result,
        error=error,
        mode=mode,
        key_type=key_type,
        input_data=data,
    )

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)
