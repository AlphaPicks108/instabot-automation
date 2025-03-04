import requests
import json
import os
import base64
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Get credentials from environment variables
CJ_API_KEY = os.getenv("CJ_API_KEY")
CJ_API_ENDPOINT = "https://developers.cjdropshipping.com/api/product/list"
ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_EMAIL = os.getenv("ODOO_EMAIL")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

# Ensure all environment variables are set
if not all([CJ_API_KEY, ODOO_URL, ODOO_DB, ODOO_EMAIL, ODOO_PASSWORD]):
    raise ValueError("❌ Missing one or more required environment variables.")

# Function to create a session with retries
def get_session():
    session = requests.Session()
    retries = Retry(
        total=3,  # Retry up to 3 times
        backoff_factor=1,  # Wait time between retries: 1s, 2s, 4s...
        status_forcelist=[500, 502, 503, 504]  # Retry on these HTTP errors
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

session = get_session()

# Function to authenticate and get Odoo session ID
def authenticate_odoo():
    login_url = f"{ODOO_URL}/web/session/authenticate"
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
        response = session.post(login_url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            result = response.json()
            return result.get("result", {}).get("session_id")
        else:
            print(f"❌ Odoo Authentication Failed: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Odoo Authentication Error: {str(e)}")
        return None

# Function to fetch products from CJ Dropshipping
def fetch_cj_products():
    headers = {
        "Content-Type": "application/json",
        "Authorization": CJ_API_KEY  # Ensure API key is included correctly
    }
    payload = {
        "apiKey": CJ_API_KEY,
        "country": "IN",
        "page": 1,
        "size": 50
    }

    try:
        response = session.post(CJ_API_ENDPOINT, json=payload, headers=headers, timeout=15)

        print("Response Status:", response.status_code)

        if response.status_code == 401:
            print("❌ Authentication failed! Invalid CJ_API_KEY.")
            return []

        if response.status_code != 200:
            print("❌ Failed to fetch CJ products:", response.text)
            return []

        data = response.json()

        if not isinstance(data, dict) or "result" not in data or "list" not in data["result"]:
            print("❌ Unexpected API response format:", json.dumps(data, indent=2))
            return []

        return data["result"]["list"]

    except requests.exceptions.RequestException as e:
        print("❌ Request Error while fetching CJ products:", str(e))
        return []

# Function to fetch and convert image to base64
def get_base64_image(image_url):
    if not image_url:
        return ""

    try:
        response = session.get(image_url, timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode("utf-8")
        else:
            print(f"⚠️ Failed to fetch image: {image_url}")
            return ""
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Image request error: {str(e)}")
        return ""

# Function to get market price (Dummy function, replace with web scraping later)
def get_market_price(product_name):
    return 5000  # Placeholder for real market price lookup

# Function to upload product to Odoo
def upload_to_odoo(product, session_id):
    odoo_api = f"{ODOO_URL}/web/dataset/call_kw/product.template/create"
    headers = {"Content-Type": "application/json"}

    try:
        cj_price = float(product.get("sellPrice") or 0)  # Handle None values
        market_price = get_market_price(product.get("name", "Unknown Product"))
        profit_margin = market_price - cj_price

        if profit_margin < 1500:
            print(f"⚠️ Skipping {product.get('name', 'Unknown')} - Profit too low ({profit_margin})")
            return

        product_image = product.get("image", "")
        base64_image = get_base64_image(product_image) if product_image else ""

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "product.template",
                "method": "create",
                "args": [{
                    "name": product.get("name", "Unnamed Product"),
                    "list_price": market_price,
                    "standard_price": cj_price,
                    "description_sale": (product.get("description", "") + "\n\nThis product is not returnable."),
                    "image_1920": base64_image,
                    "type": "product"
                }],
                "kwargs": {},
                "session_id": session_id  # Use valid session ID
            }
        }

        response = session.post(odoo_api, json=payload, headers=headers, timeout=15)

        if response.status_code == 200:
            print(f"✅ Product uploaded: {product.get('name', 'Unnamed')}")
        else:
            print(f"❌ Failed to upload {product.get('name', 'Unnamed')}: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error while uploading {product.get('name', 'Unknown')}: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error uploading {product.get('name', 'Unknown')}: {str(e)}")

# Main function
def main():
    # Authenticate Odoo and get session ID
    session_id = authenticate_odoo()
    if not session_id:
        print("❌ Exiting. Odoo authentication failed.")
        return

    products = fetch_cj_products()
    if not products:
        print("⚠️ No products fetched. Check API key, parameters, or API status.")
        return
    
    for product in products:
        upload_to_odoo(product, session_id)

if __name__ == "__main__":
    main()
