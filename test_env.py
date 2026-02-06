"""
Test script to verify Notion connection and environment variables
"""
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

print("Testing environment variables...")
print(f"TELEGRAM_BOT_TOKEN: {'OK' if os.getenv('TELEGRAM_BOT_TOKEN') else 'MISSING'}")
print(f"NOTION_TOKEN: {'OK' if os.getenv('NOTION_TOKEN') else 'MISSING'}")
print(f"GOOGLE_API_KEY: {'OK' if os.getenv('GOOGLE_API_KEY') else 'MISSING'}")
print(f"LIFE_AREAS_DB_ID: {os.getenv('LIFE_AREAS_DB_ID') or 'MISSING'}")
print(f"BRAIN_DUMP_DB_ID: {os.getenv('BRAIN_DUMP_DB_ID') or 'MISSING'}")
print(f"PROGRESS_DB_ID: {os.getenv('PROGRESS_DB_ID') or 'MISSING'}")

print("\nTesting Notion connection...")
try:
    notion = Client(auth=os.getenv("NOTION_TOKEN"))
    # Try to query the Brain Dump database
    db_id = os.getenv("BRAIN_DUMP_DB_ID")
    if db_id:
        result = notion.databases.retrieve(database_id=db_id)
        print(f"OK - Successfully connected to Notion!")
        print(f"OK - Brain Dump database found: {result['title'][0]['plain_text']}")
    else:
        print("ERROR - BRAIN_DUMP_DB_ID not set")
except Exception as e:
    print(f"ERROR - Notion connection failed: {e}")

print("\nTesting Gemini API...")
try:
    from google import genai
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    print("OK - Gemini client initialized")
except Exception as e:
    print(f"ERROR - Gemini initialization failed: {e}")
