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


# Configure logging
import logging
logger = logging.getLogger(__name__)

def get_active_items():
    """Get all non-archived items from Life Areas (fetches all, filters in memory)"""
    db_id = os.getenv("LIFE_AREAS_DB_ID")
    
    try:
        logger.info(f"Querying Notion DB {db_id} for ALL items (no filter)...")
        # Query without filter to ensure we see everything
        # WORKAROUND: databases.query() is missing in some environments, using raw request
        response = notion.request(
            path=f"databases/{db_id}/query",
            method="POST",
            body={
                "sorts": [{"property": "Priority", "direction": "ascending"}]
            }
        )
        
        items = response.get("results", [])
        logger.info(f"Notion returned {len(items)} items raw.")
        
        active_items = []
        for item in items:
            props = item["properties"]
            
            # Extract basic info for logging
            title = "Untitled"
            if props.get("Name", {}).get("title"):
                title = props["Name"]["title"][0].get("text", {}).get("content", "Untitled")
            
            status = props.get("Status", {}).get("select", {})
            status_name = status.get("name", "No Status") if status else "No Status"
            
            category = props.get("Category", {}).get("select", {})
            category_name = category.get("name", "No Category") if category else "No Category"
            
            # Log every item seen
            logger.info(f"Item found: '{title}' | Status: '{status_name}' | Category: '{category_name}'")
            
            # In-memory filter: Keep everything that isn't explicitly "Done" or "Archived"
            # This is safer than filtering for "Active" which might be case-sensitive or misspelled
            if status_name.lower() not in ["done", "completed", "archived"]:
                active_items.append(item)
        
        logger.info(f"Returning {len(active_items)} active items after local filtering.")
        return active_items
        
    except Exception as e:
        logger.error(f"Error getting active items: {e}", exc_info=True)
        return []


def search_items(query: str):
    """Search Life Areas for items matching the query - tries multiple strategies"""
    db_id = os.getenv("LIFE_AREAS_DB_ID")
    
    try:
        # Strategy 1: Direct search with full query
        # WORKAROUND: databases.query() is missing, using raw request
        response = notion.request(
            path=f"databases/{db_id}/query",
            method="POST",
            body={
                "filter": {
                    "property": "Name",
                    "title": {"contains": query}
                }
            }
        )
        
        items = response.get("results", [])
        if items:
            print(f"Search found {len(items)} items with full query: '{query}'")
            return items
        
        # Strategy 2: Try first significant word (skip common words)
        skip_words = {"the", "a", "an", "my", "to", "change", "update", "set", "make", "mark", "delete", "remove"}
        words = [w for w in query.lower().split() if w not in skip_words and len(w) > 2]
        
        if words:
            first_word = words[0]
            # Use raw request here too
            response = notion.request(
                path=f"databases/{db_id}/query",
                method="POST",
                body={
                    "filter": {
                        "property": "Name",
                        "title": {"contains": first_word}
                    }
                }
            )
            
            if response.get("results"):
                print(f"Search found {len(response['results'])} items with word: '{first_word}'")
                return response["results"]
        
        # Strategy 3: Get all active items and do local fuzzy matching
        # Use raw request here too
        response = notion.request(
            path=f"databases/{db_id}/query",
            method="POST",
            body={
                 "filter": {"property": "Status", "select": {"equals": "Active"}}
            }
        )
        all_items = response
        
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
        # WORKAROUND: databases.query() is missing, using raw request
        response = notion.request(
            path=f"databases/{db_id}/query",
            method="POST",
            body={
                "filter": {
                    "and": [
                        {"property": "Category", "select": {"equals": category}},
                        {"property": "Status", "select": {"equals": "Active"}}
                    ]
                },
                "sorts": [{"property": "Priority", "direction": "ascending"}]
            }
        )
        return response.get("results", [])
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

