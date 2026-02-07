"""Test Notion with new database IDs"""
import os
from dotenv import load_dotenv
from notion_client import Client
from datetime import datetime

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))
db_id = os.getenv("LIFE_AREAS_DB_ID")
print(f"Using DB ID: {db_id}")

try:
    result = notion.pages.create(
        parent={"database_id": db_id},
        properties={
            "Name": {"title": [{"text": {"content": "Test Entry"}}]},
            "Category": {"select": {"name": "Shopping"}},
            "Type": {"select": {"name": "Task"}},
            "Status": {"select": {"name": "Active"}},
            "Priority": {"select": {"name": "Medium"}},
            "Date Added": {"date": {"start": datetime.now().isoformat()[:10]}},
            "Notes": {"rich_text": [{"text": {"content": "Test from local"}}]},
        }
    )
    print(f"SUCCESS! Created entry ID: {result['id']}")
except Exception as e:
    print(f"ERROR: {e}")
