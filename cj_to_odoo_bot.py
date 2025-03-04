import requests
import json
import os
import base64
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# ✅ Set Environment Variables (Update if needed)
CJ_API_KEY = os.getenv("CJ_API_KEY")  # Your CJ API Key
ODOO_URL = "https://alphapicks.odoo.com"  # Your Odoo Instance
ODOO_DB = "alphapicks"  # Database Name
ODOO_EMAIL = "tanmaykrishna888@gmail.com"
ODOO_PASSWORD = "JAIBHAWANI@123"

# Ensure all credentials are provided
if not all([CJ_API_KEY, ODOO_URL, ODOO_DB, ODOO_EMAIL, ODOO_PASSWORD]):
    raise ValueError("❌ Missing required environment variables.")

# ✅ Setup Requests Session with Retries
def get_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

session = get_session()

# ✅ Authenticate Odoo
def authenticate_odoo():
    url = f"{ODOO_URL}/web/session/authenticate"
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "db": ODOO_DB,
            "login": ODOO_EMAIL,
            "password": ODOO_PASSWORD
        }
    }
    try:
        response = session.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200 and response.json().get("result"):
            print("✅ Odoo Authentication Successful!")
            return response.json()["result"]["session_id"]
        else:
            print(f"❌ Odoo Authentication Failed: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {str(e)}")
        return None

# ✅ Fetch CJ Dropshipping Products
def fetch_cj_products():
    url = "https://developers.cjdropshipping.com/api/product/list"
    headers = {"Content-Type": "application/json", "Authorization": CJ_API_KEY}
    payload = {"apiKey": CJ_API_KEY, "country": "IN", "page": 1, "size": 50}

    try:
        response = session.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json().get("result", {}).get("list", [])
        else:
            print(f"❌ Failed to fetch CJ products: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {str(e)}")
        return []

# ✅ Upload Products to Odoo
def upload_to_odoo(product, session_id):
    url = f"{ODOO_URL}/web/dataset/call_kw/product.template/create"
    headers = {"Content-Type": "application/json"}

    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": "product.template",
            "method": "create",
            "args": [{
                "name": product.get("name", "Unnamed Product"),
                "list_price": product.get("sellPrice", 0),
                "standard_price": product.get("sellPrice", 0),
                "description_sale": (product.get("description", "") + "\n\nThis product is not returnable."),
                "type": "product"
            }],
            "kwargs": {},
            "session_id": session_id
        }
    }

    try:
        response = session.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            print(f"✅ Product Uploaded: {product.get('name', 'Unnamed')}")
        else:
            print(f"❌ Upload Failed: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error uploading product: {str(e)}")

# ✅ Main Execution
def main():
    session_id = authenticate_odoo()
    if not session_id:
        print("❌ Exiting due to authentication failure.")
        return

    products = fetch_cj_products()
    if not products:
        print("⚠️ No products found. Check API credentials.")
        return
    
    for product in products:
        upload_to_odoo(product, session_id)

if __name__ == "__main__":
    main()
