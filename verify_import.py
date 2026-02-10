
import os
import sys

# Mock env vars for the import to succeed
os.environ["RAILWAY_PUBLIC_DOMAIN"] = "true" 
os.environ["TELEGRAM_TOKEN"] = "test_token"
os.environ["NOTION_TOKEN"] = "test_token"
os.environ["LIFE_AREAS_DB_ID"] = "test_id"
os.environ["GROQ_API_KEY"] = "test_key"
os.environ["ALLOWED_USER_IDS"] = "123,456"

try:
    print("Attempting to import starlette_app from bot...")
    from bot import starlette_app
    print(f"Success! Imported: {type(starlette_app)}")
except Exception as e:
    print(f"FAILED to import: {e}")
    import traceback
    traceback.print_exc()
