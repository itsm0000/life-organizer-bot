"""Add missing properties to Notion databases"""
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))

# Update Life Areas database with properties
life_areas_id = os.getenv("LIFE_AREAS_DB_ID")
print(f"Updating Life Areas database: {life_areas_id}")

try:
    result = notion.databases.update(
        database_id=life_areas_id,
        properties={
            "Category": {
                "select": {
                    "options": [
                        {"name": "Health", "color": "green"},
                        {"name": "Study", "color": "blue"},
                        {"name": "Personal Projects", "color": "purple"},
                        {"name": "Skills", "color": "yellow"},
                        {"name": "Creative", "color": "pink"},
                        {"name": "Shopping", "color": "orange"},
                        {"name": "Ideas", "color": "gray"},
                    ]
                }
            },
            "Type": {
                "select": {
                    "options": [
                        {"name": "Task", "color": "default"},
                        {"name": "Goal", "color": "blue"},
                        {"name": "Idea", "color": "gray"},
                        {"name": "Resource", "color": "brown"},
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Active", "color": "green"},
                        {"name": "Parked", "color": "yellow"},
                        {"name": "Done", "color": "blue"},
                        {"name": "Dropped", "color": "red"},
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "High", "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "gray"},
                    ]
                }
            },
            "Date Added": {"date": {}},
            "Notes": {"rich_text": {}},
            "Image": {"files": {}},
        }
    )
    print("SUCCESS! Life Areas properties updated!")
except Exception as e:
    print(f"ERROR updating Life Areas: {e}")

# Update Brain Dump database
brain_dump_id = os.getenv("BRAIN_DUMP_DB_ID")
print(f"\nUpdating Brain Dump database: {brain_dump_id}")

try:
    result = notion.databases.update(
        database_id=brain_dump_id,
        properties={
            "Content": {"rich_text": {}},
            "Processed": {"checkbox": {}},
            "Date": {"date": {}},
            "Type": {
                "select": {
                    "options": [
                        {"name": "Text", "color": "default"},
                        {"name": "Image", "color": "blue"},
                        {"name": "PDF", "color": "red"},
                        {"name": "Voice", "color": "green"},
                    ]
                }
            },
            "Files": {"files": {}},
        }
    )
    print("SUCCESS! Brain Dump properties updated!")
except Exception as e:
    print(f"ERROR updating Brain Dump: {e}")
