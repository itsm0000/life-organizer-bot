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


def search_items(query: str):
    """Search Life Areas for items matching the query - tries multiple strategies"""
    db_id = os.getenv("LIFE_AREAS_DB_ID")
    
    try:
        # Strategy 1: Direct search with full query
        results = notion.databases.query(
            database_id=db_id,
            filter={
                "property": "Name",
                "title": {"contains": query}
            }
        )
        
        if results["results"]:
            print(f"Search found {len(results['results'])} items with full query: '{query}'")
            return results["results"]
        
        # Strategy 2: Try first significant word (skip common words)
        skip_words = {"the", "a", "an", "my", "to", "change", "update", "set", "make", "mark", "delete", "remove"}
        words = [w for w in query.lower().split() if w not in skip_words and len(w) > 2]
        
        if words:
            first_word = words[0]
            results = notion.databases.query(
                database_id=db_id,
                filter={
                    "property": "Name",
                    "title": {"contains": first_word}
                }
            )
            
            if results["results"]:
                print(f"Search found {len(results['results'])} items with word: '{first_word}'")
                return results["results"]
        
        # Strategy 3: Get all active items and do local fuzzy matching
        all_items = notion.databases.query(
            database_id=db_id,
            filter={"property": "Status", "select": {"equals": "Active"}}
        )
        
        # Local fuzzy match
        query_lower = query.lower()
        matched = []
        for item in all_items.get("results", []):
            title = item["properties"].get("Name", {}).get("title", [{}])
            if title:
                title_text = title[0].get("text", {}).get("content", "").lower()
                # Check if any query word is in the title
                if any(word in title_text for word in query_lower.split() if len(word) > 2):
                    matched.append(item)
        
        print(f"Local fuzzy search found {len(matched)} items for: '{query}'")
        return matched
        
    except Exception as e:
        print(f"Error searching items: {e}")
        return []


def get_items_by_category(category: str):
    """Get all items in a specific category"""
    db_id = os.getenv("LIFE_AREAS_DB_ID")
    
    try:
        results = notion.databases.query(
            database_id=db_id,
            filter={
                "and": [
                    {"property": "Category", "select": {"equals": category}},
                    {"property": "Status", "select": {"equals": "Active"}}
                ]
            },
            sorts=[{"property": "Priority", "direction": "ascending"}]
        )
        return results["results"]
    except Exception as e:
        print(f"Error getting items by category: {e}")
        return []


def update_item(page_id: str, updates: dict):
    """
    Update an item's properties
    
    updates can contain:
    - priority: "High" | "Medium" | "Low"
    - status: "Active" | "Done" | "Archived"
    - category: category name
    """
    properties = {}
    
    if "priority" in updates:
        properties["Priority"] = {"select": {"name": updates["priority"]}}
    
    if "status" in updates:
        properties["Status"] = {"select": {"name": updates["status"]}}
    
    if "category" in updates:
        properties["Category"] = {"select": {"name": updates["category"]}}
    
    try:
        page = notion.pages.update(page_id=page_id, properties=properties)
        return page["id"]
    except Exception as e:
        print(f"Error updating item: {e}")
        return None


def delete_item(page_id: str):
    """Archive/delete an item (Notion doesn't truly delete, it archives)"""
    try:
        notion.pages.update(page_id=page_id, archived=True)
        return True
    except Exception as e:
        print(f"Error deleting item: {e}")
        return False


def format_item_for_display(item: dict) -> str:
    """Format a Notion page for display in Telegram"""
    props = item["properties"]
    
    # Get title
    title = "Untitled"
    if props.get("Name", {}).get("title"):
        title = props["Name"]["title"][0]["text"]["content"]
    
    # Get priority emoji
    priority = props.get("Priority", {}).get("select", {}).get("name", "Low")
    priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
    
    # Get category
    category = props.get("Category", {}).get("select", {}).get("name", "Unknown")
    
    return f"{priority_emoji} {title} ({category})"

