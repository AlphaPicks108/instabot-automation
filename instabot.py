from instagrapi import Client
import time
import random
import schedule
import requests
import os

# Fetch Credentials from GitHub Secrets (Environment Variables)
USERNAME = os.getenv("INSTAGRAM_USERNAME")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_EMAIL = os.getenv("ODOO_EMAIL")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

# DM Messages (Rotating)
DM_MESSAGES = [
    "🔥 Upgrade your home with this amazing product! Limited stock available! DM to order. 🚀",
    "🏋️‍♂️ Boost your fitness with top-quality equipment! Grab yours now! DM for details. 💪",
    "🛋️ Transform your workspace with ergonomic furniture! Shop now before stock runs out! 😍",
]

# Initialize Instagram Client
cl = Client()
cl.login(USERNAME, PASSWORD)

# Safe DM Scaling Plan
DM_LIMITS = {
    1: 20, 2: 20, 3: 20,  # Days 1-3
    4: 25, 5: 25, 6: 30,  # Days 4-6
    7: 30, 8: 35, 9: 35,  # Days 7-9
    10: 35, 11: 35, 12: 35, 13: 35, 14: 35,  # Days 10-14
    15: 40, 16: 40, 17: 45, 18: 45, 19: 45  # After 14 days
}

# Track Start Date
START_TIME = time.time()


def get_current_day():
    """Calculate how many days since the bot started running."""
    return int((time.time() - START_TIME) // (24 * 3600)) + 1


def send_dms():
    """Send Direct Messages based on the daily limit."""
    current_day = get_current_day()
    max_dms = DM_LIMITS.get(current_day, 45)  # Default to max safe limit

    followers = cl.user_followers(cl.user_id)
    users = list(followers.keys())

    sent_count = 0
    for user in users:
        if sent_count >= max_dms:
            break

        message = random.choice(DM_MESSAGES)
        try:
            # Engage before DM
            cl.user_like(user)
            time.sleep(random.randint(2, 5))  # Short delay

            cl.direct_send(message, [user])
            sent_count += 1
            print(f"Sent DM to {user}")

            time.sleep(random.randint(30, 90))  # Pause between DMs
        except Exception as e:
            print(f"Failed to send DM to {user}: {e}")

    print(f"✅ Sent {sent_count} DMs today.")


def fetch_odoo_product_images():
    """Fetch product images from Odoo store."""
    try:
        response = requests.get(f"{ODOO_URL}/api/products", auth=(ODOO_EMAIL, ODOO_PASSWORD))
        products = response.json()

        product_images = []
        for product in products:
            if "image_url" in product:
                product_images.append(product["image_url"])

        return product_images
    except Exception as e:
        print(f"❌ Failed to fetch images from Odoo: {e}")
        return []


def post_story():
    """Auto-post stories using product images from Odoo."""
    images = fetch_odoo_product_images()

    if not images:
        print("⚠️ No images found, skipping story post.")
        return

    image_url = random.choice(images)
    image_path = "temp_story.jpg"

    # Download Image
    with open(image_path, "wb") as img_file:
        img_file.write(requests.get(image_url).content)

    # Post Story
    try:
        cl.photo_upload_to_story(image_path, "🚀 Check out our latest product! Available now!")
        print("✅ Story posted successfully!")
    except Exception as e:
        print(f"❌ Failed to post story: {e}")


# Story Posting Schedule
schedule.every().day.at("10:00").do(post_story)
schedule.every().day.at("14:00").do(post_story)
schedule.every().day.at("18:00").do(post_story)
schedule.every().day.at("22:00").do(post_story)

# After 4 days, increase to 6 posts per day
schedule.every().day.at("12:00").do(post_story)
schedule.every().day.at("16:00").do(post_story)


# Run Bot
while True:
    send_dms()
    schedule.run_pending()
    time.sleep(3600)  # Wait 1 hour before running again
