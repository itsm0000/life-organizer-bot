"""Check Notion database properties"""
import os
import json
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))
db_id = os.getenv("LIFE_AREAS_DB_ID")
print(f"Checking database ID: {db_id}")

try:
    result = notion.databases.retrieve(database_id=db_id)
    print(f"\nDatabase title: {result.get('title', [{}])[0].get('plain_text', 'Unknown')}")
    print(f"\nProperties found: {list(result.get('properties', {}).keys())}")
    
    if 'properties' in result:
        for prop_name, prop_data in result['properties'].items():
            print(f"  - {prop_name}: {prop_data.get('type', 'unknown')}")
    else:
        print("NO PROPERTIES FIELD IN RESPONSE!")
        print(f"\nFull response keys: {list(result.keys())}")
except Exception as e:
    print(f"ERROR: {e}")
