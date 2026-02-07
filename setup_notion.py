"""
Setup Notion Database Properties
Run this locally to add required properties to your databases
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
LIFE_AREAS_DB_ID = os.getenv("LIFE_AREAS_DB_ID")
BRAIN_DUMP_DB_ID = os.getenv("BRAIN_DUMP_DB_ID")
PROGRESS_DB_ID = os.getenv("PROGRESS_DB_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def update_database(db_id, db_name, properties):
    """Update a database with new properties"""
    print(f"\nSetting up {db_name}...")
    
    url = f"https://api.notion.com/v1/databases/{db_id}"
    data = {"properties": properties}
    
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print(f"  SUCCESS: {db_name} properties added!")
        return True
    else:
        print(f"  ERROR: {response.status_code}")
        print(f"  {response.text}")
        return False

# Life Areas Database Properties
life_areas_properties = {
    "Category": {
        "select": {
            "options": [
                {"name": "Health", "color": "green"},
                {"name": "Study", "color": "blue"},
                {"name": "Personal Projects", "color": "purple"},
                {"name": "Skills", "color": "orange"},
                {"name": "Creative", "color": "pink"},
                {"name": "Shopping", "color": "yellow"},
                {"name": "Ideas", "color": "gray"}
            ]
        }
    },
    "Type": {
        "select": {
            "options": [
                {"name": "Task", "color": "blue"},
                {"name": "Goal", "color": "green"},
                {"name": "Idea", "color": "yellow"},
                {"name": "Resource", "color": "gray"}
            ]
        }
    },
    "Status": {
        "select": {
            "options": [
                {"name": "Active", "color": "green"},
                {"name": "Parked", "color": "yellow"},
                {"name": "Done", "color": "gray"},
                {"name": "Dropped", "color": "red"}
            ]
        }
    },
    "Priority": {
        "select": {
            "options": [
                {"name": "High", "color": "red"},
                {"name": "Medium", "color": "yellow"},
                {"name": "Low", "color": "gray"}
            ]
        }
    },
    "Date Added": {"date": {}},
    "Notes": {"rich_text": {}},
    "Image": {"files": {}}
}

# Brain Dump Database Properties
brain_dump_properties = {
    "Content": {"rich_text": {}},
    "Processed": {"checkbox": {}},
    "Date": {"date": {}},
    "Type": {
        "select": {
            "options": [
                {"name": "Text", "color": "blue"},
                {"name": "Image", "color": "green"},
                {"name": "PDF", "color": "orange"},
                {"name": "Voice", "color": "purple"}
            ]
        }
    },
    "Files": {"files": {}}
}

# Progress Log Database Properties  
progress_log_properties = {
    "Category": {
        "select": {
            "options": [
                {"name": "Health", "color": "green"},
                {"name": "Study", "color": "blue"},
                {"name": "Personal Projects", "color": "purple"},
                {"name": "Skills", "color": "orange"},
                {"name": "Creative", "color": "pink"}
            ]
        }
    },
    "Date": {"date": {}},
    "Duration": {"number": {"format": "number"}},
    "Notes": {"rich_text": {}}
}


if __name__ == "__main__":
    print("=" * 50)
    print("Notion Database Setup")
    print("=" * 50)
    
    if not NOTION_TOKEN:
        print("ERROR: NOTION_TOKEN not set in .env")
        exit(1)
    
    # Update each database
    success = True
    
    if LIFE_AREAS_DB_ID:
        success &= update_database(LIFE_AREAS_DB_ID, "Life Areas", life_areas_properties)
    else:
        print("WARNING: LIFE_AREAS_DB_ID not set")
    
    if BRAIN_DUMP_DB_ID:
        success &= update_database(BRAIN_DUMP_DB_ID, "Brain Dump", brain_dump_properties)
    else:
        print("WARNING: BRAIN_DUMP_DB_ID not set")
    
    if PROGRESS_DB_ID:
        success &= update_database(PROGRESS_DB_ID, "Progress Log", progress_log_properties)
    else:
        print("WARNING: PROGRESS_DB_ID not set")
    
    print("\n" + "=" * 50)
    if success:
        print("All databases set up successfully!")
        print("You can now use the bot.")
    else:
        print("Some databases failed to set up. Check errors above.")
    print("=" * 50)
