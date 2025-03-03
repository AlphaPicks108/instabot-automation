import requests
import json
import os

# Get credentials from GitHub Secrets
CJ_API_KEY = os.getenv("CJ_API_KEY")
CJ_API_ENDPOINT = "https://developers.cjdropshipping.com/api/product/list"  # Ensure correct API endpoint
ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_EMAIL = os.getenv("ODOO_EMAIL")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

# Function to fetch products from CJ Dropshipping
def fetch_cj_products():
    headers = {
        "Content-Type": "application/json",
        "Authorization": CJ_API_KEY  # Ensure API Key is passed correctly
    }
    payload = {
        "apiKey": CJ_API_KEY,
        "country": "IN",
        "page": 1,
        "size": 50
    }

    response = requests.post(CJ_API_ENDPOINT, json=payload, headers=headers)

    # Debugging print
    print("Response Status:", response.status_code)
    print("Response JSON:", response.text)

    if response.status_code != 200:
        print("❌ Failed to fetch CJ products:", response.text)
        return []

    data = response.json()
    if not isinstance(data, dict) or "result" not in data or "list" not in data["result"]:
        print("❌ Unexpected API response format")
        return []

    return data["result"]["list"]

# Function to get market price (Dummy function, replace with web scraping later)
def get_market_price(product_name):
    return 5000  # Placeholder, integrate scraping from Amazon/Flipkart later

# Function to upload product to Odoo
def upload_to_odoo(product):
    odoo_api = f"{ODOO_URL}/web/dataset/call_kw/product.template/create"
    headers = {"Content-Type": "application/json"}

    try:
        cj_price = float(product.get("sellPrice", 0))
        market_price = get_market_price(product.get("name", "Unknown Product"))
        profit_margin = market_price - cj_price

        if profit_margin < 1500:
            print(f"⚠️ Skipping {product.get('name', 'Unknown')} - Profit too low ({profit_margin})")
            return

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
                    "image_1920": product.get("image", ""),
                    "type": "product"
                }],
                "kwargs": {},
                "session_id": ODOO_PASSWORD
            }
        }

        response = requests.post(odoo_api, json=payload, headers=headers)

        if response.status_code == 200:
            print(f"✅ Product uploaded: {product.get('name', 'Unnamed')}")
        else:
            print(f"❌ Failed to upload {product.get('name', 'Unnamed')}: {response.text}")

    except Exception as e:
        print(f"❌ Error uploading {product.get('name', 'Unknown')}: {str(e)}")

# Main function
def main():
    products = fetch_cj_products()
    if not products:
        print("❌ No products fetched. Exiting.")
        return
    
    for product in products:
        upload_to_odoo(product)

if __name__ == "__main__":
    main()
