# app.py
import os
from flask import Flask, request, jsonify, render_template_string
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64
import binascii
import requests

# === Subgateway Public Key (hex) ===
PUB_KEY_HEX_SUB = """
30820122300d06092a864886f70d01010105000382010f003082010a0282010100d1fabdd1cb9a2e8d2799b96b8abcd6
fd5ee0aacd3baa893d5f46f3e4c463f1337569fb8e89e46b7649dc782cca237c461317e29b9474d948cfbe7da6ed1ca8
bbb499119ecff2ecf9d1eb72074a9d848b70d60767de4b7746cefd1fc287f5c8d00a22d73677b294a49d710a7ba0ecbc
6e96d498686938264cad2b03a9fe50d7f592b31defbfc3489f70be98192ebcbd56bf867c077e9b47e83245a3c30124d5
e9a1cfb31e5f7d4f5ca48d7ac7b617e1f06a543ff4ebdd9c4e1a544410c7d7be43afa50731814c14d76dc63cbce872c2
dfe703bae795a44929eef0a78b10af5626bcb608b00a6c4f50fd322e92a654ac64aaae0a9b51d01c1a7700dc63024f10
cf0203010001
""".replace("\n", "").replace(" ", "")

# === Retailergateway Public Key (hex) ===
PUB_KEY_HEX_RETAILER = """
30820122300d06092a864886f70d01010105000382010f003082010a0282010100bbf6f7fbe5f31b33028e9c0d10ab31
06a6d9ec6df0afc7651d3a3288a0c371fea36b141ecd6fdc10bac8821bf54a9d7ba216717cfb7469cd63faaa a579413e
dd14527ebbe465c06b1dd353f7e594eb9d1a4b5405208d589a96d9a21750fc490852399a7ae3ccfa259ca43bf045010a
45ea2cfa068d489c55788a58063885362e26acbface064d404cf2d28fe5568c04aea549385a40339b88b139f2ce5139a
8b3874b973cc9c866c98e22a9d8e64b205f06f7abb015997a02fa6b90108d4ab777ba3145bd03f63c6d2712a842fe0f6
fb288da26eb44d638a37941611e3b5e1ee5093ab966d4d31d9dd553764616d9c06fd927ab36b3a44e706130aab7b9812
ff0203010001
""".replace("\n", "").replace(" ", "")

# === Helpers ===
def load_public_key_from_hex(hex_data):
    key_bytes = binascii.unhexlify(hex_data)
    return RSA.import_key(key_bytes)

def encrypt_data(data, public_key):
    cipher = PKCS1_v1_5.new(public_key)
    encrypted = cipher.encrypt(data.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

# === Flask app ===
app = Flask(__name__)

# === Frontend ===
@app.route("/", methods=["GET"])
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Login Payload Tool</title>
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
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin:0; padding:0; }
            .container { max-width: 600px; margin: 50px auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); padding: 30px; }
            h2 { text-align: center; color: #333; margin-bottom: 20px; }
            input[type=text], input[type=password] { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #ccc; font-size: 16px; }
            button { width: 100%; padding: 14px; background: #007bff; color: #fff; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; margin-top: 10px; transition: background 0.3s; }
            button:hover { background: #0056b3; }
            button:disabled { background: #6c757d; cursor: not-allowed; }
            .response { margin-top: 20px; background: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px solid #ddd; }
            .section { margin-bottom: 15px; }
            .section h4 { margin-bottom: 5px; color: #555; display: flex; justify-content: space-between; align-items: center; }
            pre { background: #e9ecef; padding: 10px; border-radius: 6px; overflow-x: auto; font-size: 13px; }
            
            /* Compact, professional copy button */
            .copy-btn {
                background: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 12px;
                cursor: pointer;
                position: relative;
                display: inline-flex;
                align-items: center;
                transition: background 0.3s;
                height: 28px;
                line-height: 1;
            }
            .copy-btn:hover { background: #0056b3; }
            .copy-btn:active { background: #004080; }
            .copy-btn .tooltip {
                visibility: hidden;
                background-color: #333;
                color: #fff;
                text-align: center;
                border-radius: 5px;
                padding: 4px 6px;
                position: absolute;
                top: -30px;
                right: 0;
                font-size: 11px;
                opacity: 0;
                transition: opacity 0.3s;
                white-space: nowrap;
                z-index: 10;
            }
            .copy-btn.show-tooltip .tooltip {
                visibility: visible;
                opacity: 1;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="dashboard-btn">← Back to Dashboard</a>
            <h2>Login Payload Tool</h2>
            <form id="loginForm">
                <input type="text" name="number" placeholder="Enter MSISDN (e.g., 923319154345)" value="923319154345" required>
                <input type="password" name="pin" placeholder="PIN" required>
                <button type="submit" id="generateBtn">Generate Payload</button>
            </form>

            <div class="response" id="responseDiv" style="display:none;">
                <div class="section">
                    <h4>Input</h4>
                    <pre id="inputVal"></pre>
                </div>
                <div class="section">
                    <h4>
                        LoginPayload
                        <button class="copy-btn" onclick="copyText('loginPayloadVal', this)">
                            Copy
                            <span class="tooltip">Copied!</span>
                        </button>
                    </h4>
                    <pre id="loginPayloadVal"></pre>
                </div>
                <div class="section">
                    <h4>
                        x-hash
                        <button class="copy-btn" onclick="copyText('xHashVal', this)">
                            Copy
                            <span class="tooltip">Copied!</span>
                        </button>
                    </h4>
                    <pre id="xHashVal"></pre>
                </div>
                <div class="section">
                    <h4>Remote Response</h4>
                    <pre id="remoteResponseVal"></pre>
                </div>
            </div>
        </div>

        <script>
            const form = document.getElementById('loginForm');
            const responseDiv = document.getElementById('responseDiv');
            const generateBtn = document.getElementById('generateBtn');

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                responseDiv.style.display = 'none';
                generateBtn.disabled = true;
                const originalText = generateBtn.textContent;
                generateBtn.textContent = 'Processing...';

                const formData = new FormData(form);
                const data = {
                    number: formData.get('number'),
                    pin: formData.get('pin')
                };

                try {
                    const resp = await fetch('loginpayload', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const json = await resp.json();

                    responseDiv.style.display = 'block';
                    document.getElementById('inputVal').textContent = json.input || '';
                    document.getElementById('loginPayloadVal').textContent = json.LoginPayload || '';
                    document.getElementById('xHashVal').textContent = json['x-hash'] || json['x-hash-retailer'] || '';
                    document.getElementById('remoteResponseVal').textContent = JSON.stringify(json.remote_response || json, null, 4);
                } catch (err) {
                    alert('Error: ' + err);
                } finally {
                    generateBtn.disabled = false;
                    generateBtn.textContent = originalText;
                }
            });

            function copyText(elementId, btn) {
                const text = document.getElementById(elementId).textContent;
                navigator.clipboard.writeText(text).then(() => {
                    btn.classList.add('show-tooltip');
                    setTimeout(() => btn.classList.remove('show-tooltip'), 1500);
                });
            }
        </script>
    </body>
    </html>
    """)

# === Backend API ===
@app.route("/loginpayload", methods=["POST"])
def loginpayload():
    try:
        body = request.get_json(force=True)
        number = body.get("number")
        pin = body.get("pin")

        if not number or not pin:
            return jsonify({"error": "please provide both 'number' and 'pin' in JSON body"}), 400

        # Detect gateway type
        if "@" in number:
            # Retailergateway flow
            input_enc = f"{number}:{pin}"
            public_key = load_public_key_from_hex(PUB_KEY_HEX_RETAILER)
            LoginPayload = encrypt_data(input_enc, public_key)
            headers = {
                "X-IBM-Client-Id": os.environ.get("IBM_CLIENT_ID", ""),
                "X-IBM-Client-Secret": os.environ.get("IBM_CLIENT_SECRET", ""),
                "X-Channel": "retailergateway",
                "Content-Type": "application/json"
            }
            gateway_type = "retailergateway"
        else:
            # Subgateway flow
            input_enc = f"{number}:{pin}"
            public_key = load_public_key_from_hex(PUB_KEY_HEX_SUB)
            LoginPayload = encrypt_data(input_enc, public_key)
            headers = {
                "X-IBM-Client-Id": os.environ.get("IBM_CLIENT_ID", ""),
                "X-IBM-Client-Secret": os.environ.get("IBM_CLIENT_SECRET", ""),
                "X-Channel": "subgateway",
                "Content-Type": "application/json"
            }
            gateway_type = "subgateway"

        # Send LoginPayload
        login_url = "https://rgw.8798-f464fa20.eu-de.ri1.apiconnect.appdomain.cloud/tmfb/dev-catalog/CorporateLogin/"
        payload_body = {"LoginPayload": LoginPayload}
        remote_resp = requests.post(login_url, headers=headers, json=payload_body, timeout=15)

        try:
            remote_json = remote_resp.json()
        except ValueError:
            remote_json = {"text": remote_resp.text}

        # Build x-hash
        x_hash = None
        if "User" in remote_json and "Timestamp" in remote_json:
            to_encrypt = f"{remote_json['User']}~{remote_json['Timestamp']}"
            x_hash = encrypt_data(to_encrypt, public_key)

        # Return response
        if gateway_type == "retailergateway":
            return jsonify({
                "input": input_enc,
                "LoginPayload": LoginPayload,
                "remote_status_code": remote_resp.status_code,
                "remote_response": remote_json,
                "x-hash-retailer": x_hash
            }), 200
        else:
            return jsonify({
                "input": input_enc,
                "LoginPayload": LoginPayload,
                "remote_status_code": remote_resp.status_code,
                "remote_response": remote_json,
                "x-hash": x_hash
            }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "request to remote API failed", "details": str(e)}), 502
    except Exception as e:
        return jsonify({"error": "internal server error", "details": str(e)}), 500

# === Run App ===
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5050, debug=False)
