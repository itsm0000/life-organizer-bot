"""
Clear any existing webhooks for the bot
Run this if you get "Conflict: terminated by other getUpdates" errors
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"

response = requests.get(url)
print(f"Webhook deletion response: {response.json()}")

# Also get bot info to verify token works
info_url = f"https://api.telegram.org/bot{token}/getMe"
info_response = requests.get(info_url)
print(f"\nBot info: {info_response.json()}")
