"""
Notion Database Setup Script
Creates the necessary databases in Notion workspace
"""
import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))

def create_life_areas_database(parent_page_id):
    """Create the Life Areas database"""
    database = notion.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Life Areas"}}],
        properties={
            "Name": {"title": {}},
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
        },
    )
    return database["id"]


def create_brain_dump_database(parent_page_id):
    """Create the Brain Dump inbox database"""
    database = notion.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Brain Dump Inbox"}}],
        properties={
            "Name": {"title": {}},
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
        },
    )
    return database["id"]


def create_progress_tracker(parent_page_id):
    """Create the Progress Tracker database"""
    database = notion.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Progress Log"}}],
        properties={
            "Activity": {"title": {}},
            "Category": {
                "select": {
                    "options": [
                        {"name": "Health", "color": "green"},
                        {"name": "Study", "color": "blue"},
                        {"name": "Personal Projects", "color": "purple"},
                        {"name": "Skills", "color": "yellow"},
                        {"name": "Creative", "color": "pink"},
                    ]
                }
            },
            "Date": {"date": {}},
            "Duration": {"number": {}},
            "Notes": {"rich_text": {}},
        },
    )
    return database["id"]


def setup_notion_workspace():
    """Main setup function"""
    print("Setting up Notion workspace...")
    
    # Get the first page in the workspace to use as parent
    search_results = notion.search(filter={"property": "object", "value": "page"})
    if not search_results["results"]:
        print("Error: No pages found in workspace. Please create a page first.")
        return
    
    parent_page = search_results["results"][0]
    parent_id = parent_page["id"]
    
    print(f"Using page '{parent_page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'Untitled')}' as parent")
    
    # Create databases
    print("Creating Life Areas database...")
    life_areas_id = create_life_areas_database(parent_id)
    print(f"✓ Life Areas DB created: {life_areas_id}")
    
    print("Creating Brain Dump database...")
    brain_dump_id = create_brain_dump_database(parent_id)
    print(f"✓ Brain Dump DB created: {brain_dump_id}")
    
    print("Creating Progress Tracker...")
    progress_id = create_progress_tracker(parent_id)
    print(f"✓ Progress Tracker created: {progress_id}")
    
    print("\n" + "="*50)
    print("Setup complete! Add these to your .env file:")
    print("="*50)
    print(f"LIFE_AREAS_DB_ID={life_areas_id}")
    print(f"BRAIN_DUMP_DB_ID={brain_dump_id}")
    print(f"PROGRESS_DB_ID={progress_id}")
    print("="*50)


if __name__ == "__main__":
    setup_notion_workspace()
