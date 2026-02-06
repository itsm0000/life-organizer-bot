"""
Notion Integration Module
Handles all interactions with Notion API
"""
import os
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))


def add_to_life_areas(category, title, item_type, priority, notes="", image_url=None):
    """Add an item to the Life Areas database"""
    db_id = os.getenv("LIFE_AREAS_DB_ID")
    
    properties = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Category": {"select": {"name": category}},
        "Type": {"select": {"name": item_type}},
        "Status": {"select": {"name": "Active"}},
        "Priority": {"select": {"name": priority}},
        "Date Added": {"date": {"start": datetime.now().isoformat()}},
    }
    
    if notes:
        properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
    
    if image_url:
        properties["Image"] = {"files": [{"name": "Image", "external": {"url": image_url}}]}
    
    try:
        page = notion.pages.create(parent={"database_id": db_id}, properties=properties)
        return page["id"]
    except Exception as e:
        print(f"Error adding to Life Areas: {e}")
        return None


def add_to_brain_dump(title, content, msg_type, file_url=None):
    """Add an item to the Brain Dump inbox"""
    db_id = os.getenv("BRAIN_DUMP_DB_ID")
    
    properties = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Content": {"rich_text": [{"text": {"content": content[:2000]}}]},  # Notion limit
        "Processed": {"checkbox": False},
        "Date": {"date": {"start": datetime.now().isoformat()}},
        "Type": {"select": {"name": msg_type}},
    }
    
    if file_url:
        properties["Files"] = {"files": [{"name": "Attachment", "external": {"url": file_url}}]}
    
    try:
        page = notion.pages.create(parent={"database_id": db_id}, properties=properties)
        return page["id"]
    except Exception as e:
        print(f"Error adding to Brain Dump: {e}")
        return None


def log_progress(activity, category, duration=None, notes=""):
    """Log an activity to the Progress Tracker"""
    db_id = os.getenv("PROGRESS_DB_ID")
    
    properties = {
        "Activity": {"title": [{"text": {"content": activity}}]},
        "Category": {"select": {"name": category}},
        "Date": {"date": {"start": datetime.now().isoformat()}},
    }
    
    if duration:
        properties["Duration"] = {"number": duration}
    
    if notes:
        properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
    
    try:
        page = notion.pages.create(parent={"database_id": db_id}, properties=properties)
        return page["id"]
    except Exception as e:
        print(f"Error logging progress: {e}")
        return None


def get_active_items():
    """Get all active items from Life Areas"""
    db_id = os.getenv("LIFE_AREAS_DB_ID")
    
    try:
        results = notion.databases.query(
            database_id=db_id,
            filter={"property": "Status", "select": {"equals": "Active"}},
            sorts=[{"property": "Priority", "direction": "ascending"}]
        )
        return results["results"]
    except Exception as e:
        print(f"Error getting active items: {e}")
        return []
