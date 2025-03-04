import requests
import json

ODOO_URL = "https://your-odoo-instance.com"
ODOO_DB = "your_db_name"
ODOO_EMAIL = "your_email@example.com"
ODOO_PASSWORD = "your_password"

payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "db": ODOO_DB,
        "login": ODOO_EMAIL,
        "password": ODOO_PASSWORD
    }
}

response = requests.post(f"{ODOO_URL}/web/session/authenticate", json=payload)
print(response.json())  # Check if it returns "session_id"
