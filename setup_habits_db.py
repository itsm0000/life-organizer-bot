"""
Setup Habits Database in Notion
Run this once to create the Habits database with proper properties
"""
import os
import sys

# Fix Windows console encoding for emojis
sys.stdout.reconfigure(encoding='utf-8')

from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))


def create_habits_database():
    """Create the Habits database in Notion"""
    
    # Get the parent page (Life Organizer workspace)
    # We'll create it as a child of the existing Life Areas database's parent
    life_areas_id = os.getenv("LIFE_AREAS_DB_ID")
    
    if not life_areas_id:
        print("ERROR: LIFE_AREAS_DB_ID not set. Cannot determine parent page.")
        return None
    
    # Get the Life Areas database to find its parent
    try:
        db_info = notion.databases.retrieve(database_id=life_areas_id)
        parent = db_info.get("parent", {})
        
        if parent.get("type") == "page_id":
            parent_page_id = parent.get("page_id")
        else:
            print("ERROR: Could not find parent page. Creating in workspace root.")
            parent_page_id = None
    except Exception as e:
        print(f"ERROR: Could not retrieve parent info: {e}")
        return None
    
    # Define database properties
    properties = {
        "Name": {"title": {}},
        "Frequency": {
            "select": {
                "options": [
                    {"name": "Daily", "color": "blue"},
                    {"name": "Twice Daily", "color": "purple"},
                    {"name": "Weekly", "color": "green"},
                    {"name": "Monthly", "color": "yellow"},
                ]
            }
        },
        "Times": {
            "multi_select": {
                "options": [
                    {"name": "Morning", "color": "yellow"},
                    {"name": "Evening", "color": "purple"},
                    {"name": "Afternoon", "color": "orange"},
                ]
            }
        },
        "Category": {
            "select": {
                "options": [
                    {"name": "Health", "color": "green"},
                    {"name": "Study", "color": "blue"},
                    {"name": "Work", "color": "gray"},
                    {"name": "Personal", "color": "pink"},
                    {"name": "Skills", "color": "orange"},
                ]
            }
        },
        "XP Reward": {"number": {"format": "number"}},
        "Active": {"checkbox": {}},
        "Last Completed": {"date": {}},
        "Created": {"date": {}},
    }
    
    try:
        # Create the database
        new_db = notion.databases.create(
            parent={"page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": "Habits"}}],
            icon={"type": "emoji", "emoji": "🔁"},
            properties=properties
        )
        
        db_id = new_db["id"]
        print(f"✅ Created Habits database!")
        print(f"\n📋 Add this to your .env file:")
        print(f"HABITS_DB_ID={db_id}")
        print(f"\n🔗 Database URL: https://notion.so/{db_id.replace('-', '')}")
        
        return db_id
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("🔁 Creating Habits Database in Notion")
    print("=" * 50)
    print()
    create_habits_database()
