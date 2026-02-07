"""
Clear any existing webhook and pending updates
Run this once before deploying to fix conflicts
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN not set in .env")
    exit(1)

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 1. Delete any existing webhook
print("Deleting existing webhook...")
resp = requests.post(f"{BASE_URL}/deleteWebhook", json={"drop_pending_updates": True})
print(f"   Response: {resp.json()}")

# 2. Get current webhook info
print("\nCurrent webhook info:")
resp = requests.get(f"{BASE_URL}/getWebhookInfo")
info = resp.json()
print(f"   URL: {info['result'].get('url', 'None')}")
print(f"   Pending updates: {info['result'].get('pending_update_count', 0)}")
print(f"   Last error: {info['result'].get('last_error_message', 'None')}")

print("\nWebhook cleared! You can now deploy to Railway.")
print("   Make sure to set RAILWAY_PUBLIC_DOMAIN in Railway variables.")
