# IBM Dashboard Project

A comprehensive Flask-based microservices dashboard that integrates multiple API services for IBM payment gateway operations, encryption/decryption, and credential management.

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Services](#services)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Security Considerations](#security-considerations)
- [Development](#development)

## Overview

The IBM Dashboard Project is a centralized management platform that orchestrates multiple Flask-based microservices using a middleware dispatcher pattern. It provides:

- **Unified Dashboard**: A single entry point to access all microservices
- **Encryption/Decryption Services**: RSA-based encryption for secure data handling
- **API Gateway Services**: Integration with IBM payment gateways (Retailer and Sub-gateways)
- **BVS APIs**: Business Verification System API management
- **Authentication**: Login and credential management system

The project uses `DispatcherMiddleware` from Werkzeug to mount multiple Flask applications under different URL prefixes, creating a modular and scalable architecture.

## Project Structure

```
IBM-dashboard-project/
├── main_dashboard.py              # Main entry point - mounts all services
├── dashboard.html                 # Web UI for the dashboard
├── requirements.txt               # Python dependencies
│
├── Encryption-decryption/         # Encryption/Decryption microservice
│   ├── app.py                     # Encryption service implementation
│   └── Keys/                      # Cryptographic keys storage
│       ├── retailergateway.der    # Retailer gateway DER key
│       ├── subgateway.der         # Sub-gateway DER key
│       ├── private/               # Private key storage
│       │   ├── retailergateway.der
│       │   └── subgateway.der
│       └── public pem files/      # Public PEM format keys
│
├── login/                         # Authentication microservice
│   └── app.py                     # Login and credential verification
│
├── ret-apis/                      # Retailer Gateway API service
│   └── app.py                     # Retailer API endpoints
│
├── sub-apis/                      # Sub-Gateway API service
│   └── app.py                     # Sub-gateway API endpoints
│
└── bvs-apis/                      # Business Verification System APIs
    └── app.py                     # BVS API management
```

## Architecture

### Service Mounting Architecture

```
┌─────────────────────────────────────────────────────┐
│            main_dashboard.py (Root App)             │
│                 (Port 5000)                         │
├─────────────────────────────────────────────────────┤
│  DispatcherMiddleware (URL Prefix Routing)          │
├──────────┬──────────┬──────────┬──────────┬─────────┤
│  /       │ /login   │ /encrypt │ /ret     │ /sub    │
│ (Root)   │ (Auth)   │ (Crypto) │ (Retail) │ (SubGW) │
└──────────┴──────────┴──────────┴──────────┴─────────┘
```

Each microservice:
- Runs independently with its own Flask context
- Handles requests to its specific URL prefix
- Can be developed and tested in isolation
- Communicates with external IBM services as needed

## Services

### 1. **Root Dashboard** (`/`)
- **File**: `main_dashboard.py`, `dashboard.html`
- **Purpose**: Provides the main web UI and acts as the central routing point
- **Features**:
  - Interactive dashboard with project cards
  - Navigation to all microservices
  - Static key file serving (development only)

### 2. **Encryption/Decryption Service** (`/encryption`)
- **File**: `Encryption-decryption/app.py`
- **Purpose**: Handles RSA encryption and decryption operations
- **Capabilities**:
  - Load public and private keys from DER/PEM formats
  - Encrypt data using public keys (PKCS1_v1_5)
  - Decrypt data using private keys
  - Support for multiple gateway keys (Retailer and Sub-gateway)

### 3. **Login Service** (`/login`)
- **File**: `login/app.py`
- **Purpose**: User authentication and credential verification
- **Features**:
  - RSA-based credential verification
  - Integration with gateway public keys
  - Session management
  - User login/logout functionality

### 4. **Retailer Gateway API** (`/ret`)
- **File**: `ret-apis/app.py`
- **Purpose**: Interface with IBM Retailer Gateway
- **Features**:
  - Authentication with IBM services
  - Encrypted request handling
  - Payment transaction APIs
  - CORS enabled for cross-origin requests
  - Environment-based configuration

### 5. **Sub-Gateway API** (`/sub`)
- **File**: `sub-apis/app.py`
- **Purpose**: Interface with IBM Sub-Gateway
- **Features**:
  - Similar to Retailer API but for sub-gateway operations
  - Separate credentials and key management
  - Transaction processing and verification

### 6. **BVS API Service** (`/bvs`)
- **File**: `bvs-apis/app.py`
- **Purpose**: Business Verification System API management
- **Features**:
  - Business identity verification
  - Integration with IBM BVS endpoints
  - HTML-based dashboard for verification operations

## Installation

### Prerequisites
- Python 3.7+
- pip package manager
- Git (optional)

### Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd IBM-dashboard-project
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up cryptographic keys**
   - Ensure all `.der` and `.pem` files are placed in `Encryption-decryption/Keys/`
   - Verify the directory structure matches the project layout
   - Place public PEM files in `Encryption-decryption/Keys/public pem files/`
   - Place private keys in `Encryption-decryption/Keys/private/`

5. **Configure environment variables** (optional)
   ```bash
   export IBM_CLIENT_ID="your_client_id"
   export IBM_CLIENT_SECRET="your_client_secret"
   export X_CHANNEL="retailergateway"  # or "subgateway"
   ```

## Configuration

### Environment Variables

The application uses the following environment variables (with defaults):

| Variable | Default | Service | Purpose |
|----------|---------|---------|---------|
| `IBM_CLIENT_ID` | `924726a...............10c4e4` | ret-apis, sub-apis | IBM authentication ID |
| `IBM_CLIENT_SECRET` | `7154c95b..............2f297eb5a9c` | ret-apis, sub-apis | IBM authentication secret |
| `X_CHANNEL` | `retailergateway` or `subgateway` | Gateway services | Channel identifier |

### Key Management

- **Public Keys**: Used for encrypting data to send to IBM services
- **Private Keys**: Used for decrypting responses from IBM services
- **Supported Formats**: DER (binary) and PEM (text)
- **Key Paths**:
  - Retailer: `Encryption-decryption/Keys/retailergateway.der`
  - Sub-gateway: `Encryption-decryption/Keys/subgateway.der`

## Usage

### Starting the Application

```bash
python main_dashboard.py
```

The dashboard will be available at `http://localhost:5000`

### Accessing Services

- **Dashboard**: `http://localhost:5000/`
- **Encryption**: `http://localhost:5000/encryption`
- **Login**: `http://localhost:5000/login`
- **Retailer APIs**: `http://localhost:5000/ret`
- **Sub-Gateway APIs**: `http://localhost:5000/sub`
- **BVS APIs**: `http://localhost:5000/bvs`

### Example: Using the Encryption Service

```python
import requests
import json

# Encrypt data
data = {"message": "sensitive data"}
response = requests.post(
    "http://localhost:5000/encryption/encrypt",
    json=data,
    headers={"X-Gateway": "retailergateway"}
)
encrypted_result = response.json()
```

## API Endpoints

### Encryption/Decryption Service

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/encryption/encrypt` | Encrypt data using public key |
| POST | `/encryption/decrypt` | Decrypt data using private key |
| GET | `/encryption/status` | Service health check |

### Login Service

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/login` | Login page |
| POST | `/login/verify` | Verify credentials |
| GET | `/login/logout` | Logout user |

### Retailer Gateway API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/ret/api/payment` | Process payment transaction |
| GET | `/ret/api/status` | Get transaction status |
| POST | `/ret/api/verify` | Verify transaction |

### Sub-Gateway API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/sub/api/payment` | Process payment transaction |
| GET | `/sub/api/status` | Get transaction status |
| POST | `/sub/api/verify` | Verify transaction |

### BVS API Service

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/bvs` | BVS dashboard page |
| POST | `/bvs/verify` | Verify business |
| GET | `/bvs/status` | Get verification status |

## Security Considerations

### ⚠️ Important Security Notes

1. **Key Management**
   - Never commit private keys to version control
   - Use `.gitignore` to exclude key files:
     ```
     Encryption-decryption/Keys/
     *.der
     *.pem
     ```
   - Store keys securely in production (e.g., AWS Secrets Manager, HashiCorp Vault)

2. **File Serving**
   - The `/keys/` endpoint in `main_dashboard.py` is intended for **development only**
   - **DISABLE in production** to prevent unauthorized key exposure
   - Implement proper authentication for key access

3. **Credentials**
   - Never hardcode IBM credentials in code
   - Always use environment variables
   - Rotate credentials regularly
   - Use HTTPS in production

4. **Session Security**
   - Change `app.secret_key` in production to a strong random value
   - Use secure session cookies (`SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`)
   - Implement session timeout mechanisms

5. **CORS Configuration**
   - Review and restrict CORS origins in production
   - Currently allows all origins (`CORS(app)`)
   - Configure specific allowed domains:
     ```python
     CORS(app, origins=["https://yourdomain.com"])
     ```

6. **Input Validation**
   - Validate and sanitize all user inputs
   - Implement rate limiting for API endpoints
   - Use request size limits to prevent DoS attacks

## Development

### Project Structure Best Practices

Each microservice (`login/`, `ret-apis/`, `sub-apis/`, `bvs-apis/`, `Encryption-decryption/`) follows this pattern:

```
service/
├── app.py              # Main Flask application
├── __pycache__/        # Python cache (auto-generated)
└── (optional additional modules)
```

### Adding a New Microservice

1. Create a new directory: `mkdir new-service`
2. Create `new-service/app.py` with a Flask app instance named `app`
3. Update `main_dashboard.py` with the new mount mapping:
   ```python
   MOUNT_MAP = {
       "/new-service": os.path.join(BASE_DIR, "new-service", "app.py"),
       # ... existing services
   }
   ```
4. Restart the application

### Running Tests

```bash
# Test individual services
python -m pytest ret-apis/
python -m pytest sub-apis/

# Test the dashboard
python -m pytest main_dashboard.py
```

### Debugging

1. Enable Flask debug mode (development only):
   ```bash
   export FLASK_ENV=development
   export FLASK_DEBUG=1
   ```

2. Check logs:
   ```bash
   tail -f app.log
   ```

3. Use Flask shell for testing:
   ```bash
   export FLASK_APP=main_dashboard.py
   flask shell
   ```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | >=2.0 | Web framework |
| werkzeug | >=2.0 | WSGI utilities (DispatcherMiddleware) |
| pycryptodome | >=3.15.0 | Cryptographic operations (RSA) |
| cryptography | >=3.4.7 | Cryptography primitives |
| requests | >=2.28 | HTTP client for external APIs |
| flask-cors | (implicit) | CORS support for APIs |

## Troubleshooting

### Common Issues

**1. Module Import Errors**
```
ModuleNotFoundError: No module named 'app'
```
- Ensure all microservice directories contain `app.py`
- Verify the `MOUNT_MAP` paths are correct

**2. Key Not Found**
```
FileNotFoundError: Public key not found at ...
```
- Check that key files exist in the correct directories
- Verify file permissions (readable by the application user)

**3. Port Already in Use**
```
Address already in use
```
- Change the port in `main_dashboard.py` or kill the existing process:
  ```bash
  lsof -i :5000  # Find process
  kill -9 <PID>  # Kill it
  ```

**4. CORS Issues**
- Ensure `flask-cors` is installed: `pip install flask-cors`
- Check CORS configuration in each microservice



## Contact & Support

For issues, questions, or support, please contact the development team (usmanfarooq317@gmail.com)

---

**Last Updated**: December 2025
**Version**: 1.0.0
