import requests
import json
import os

# Get credentials from GitHub Secrets
CJ_API_KEY = os.getenv("CJ_API_KEY")
ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_EMAIL = os.getenv("ODOO_EMAIL")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

# Function to fetch products from CJ Dropshipping
def fetch_cj_products():
    url = "https://developers.cjdropshipping.com/api/product/list"
    headers = {"Content-Type": "application/json"}
    payload = {
        "apiKey": CJ_API_KEY,
        "country": "IN",
        "page": 1,
        "size": 50
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["result"]["list"]
    else:
        print("Error fetching CJ products:", response.text)
        return []

# Function to get market price (Dummy function, replace with web scraping later)
def get_market_price(product_name):
    return 5000  # Placeholder, you need to integrate scraping from Amazon/Flipkart

# Function to upload product to Odoo
def upload_to_odoo(product):
    odoo_api = f"{ODOO_URL}/web/dataset/call_kw/product.template/create"
    headers = {"Content-Type": "application/json"}

    # Calculate profit margin
    cj_price = float(product["sellPrice"])
    market_price = get_market_price(product["name"])
    profit_margin = market_price - cj_price

    if profit_margin < 1500:
        print(f"Skipping {product['name']} - Profit too low ({profit_margin})")
        return

    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": "product.template",
            "method": "create",
            "args": [{
                "name": product["name"],
                "list_price": market_price,
                "standard_price": cj_price,
                "description_sale": product["description"] + "\n\nThis product is not returnable.",
                "image_1920": product["image"],
                "type": "product"
            }],
            "kwargs": {},
            "session_id": ODOO_PASSWORD
        }
    }

    response = requests.post(odoo_api, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"✅ Product uploaded: {product['name']}")
    else:
        print(f"❌ Failed to upload {product['name']}:", response.text)

# Main function
def main():
    products = fetch_cj_products()
    for product in products:
        upload_to_odoo(product)

if __name__ == "__main__":
    main()
