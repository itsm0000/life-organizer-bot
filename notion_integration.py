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


def add_to_life_areas(category, title, item_type, priority, notes="", image_url=None, due_date=None):
    """Add an item to the Life Areas database with visual styling"""
    db_id = os.getenv("LIFE_AREAS_DB_ID")
    
    # Category-specific emoji icons for visual appeal
    CATEGORY_ICONS = {
        "Health": "💪",
        "Study": "📚",
        "Work": "💼",
        "Ideas": "💡",
        "Shopping": "🛒",
        "Skills": "🎯",
        "Finance": "💰",
        "Social": "👥",
        "Personal": "🌟",
    }
    
    # Category-specific cover images (Unsplash - reliable and matching content)
    CATEGORY_COVERS = {
        "Health": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200",  # Fitness/wellness
        "Study": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=1200",  # Books/study
        "Work": "https://images.unsplash.com/photo-1497215842964-222b430dc094?w=1200",  # Modern office
        "Ideas": "https://images.unsplash.com/photo-1493612276216-ee3925520721?w=1200",  # Creative lightbulbs
        "Shopping": "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=1200",  # Shopping bags
        "Skills": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=1200",  # Learning/skills
        "Finance": "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=1200",  # Finance/money
        "Social": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=1200",  # Friends/social
        "Personal": "https://images.unsplash.com/photo-1516534775068-ba3e7458af70?w=1200",  # Personal growth
        "Personal Projects": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200",  # Projects/laptop
    }
    DEFAULT_COVER = "https://images.unsplash.com/photo-1557683316-973673baf926?w=1200"  # Purple gradient fallback
    
    properties = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Category": {"select": {"name": category}},
        "Type": {"select": {"name": item_type}},
        "Status": {"select": {"name": "Active"}},
        "Priority": {"select": {"name": priority}},
        "Date Added": {"date": {"start": datetime.now().isoformat()}},
    }
    
    if due_date:
        properties["Date"] = {"date": {"start": due_date}}
    
    if notes:
        properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
    
    if image_url:
        properties["Image"] = {"files": [{"name": "Image", "external": {"url": image_url}}]}
    
    # Get icon and cover for visual appeal (based on category)
    icon_emoji = CATEGORY_ICONS.get(category, "📌")
    cover_url = CATEGORY_COVERS.get(category, DEFAULT_COVER)
    
    try:
        page = notion.pages.create(
            parent={"database_id": db_id}, 
            properties=properties,
            icon={"type": "emoji", "emoji": icon_emoji},
            cover={"type": "external", "external": {"url": cover_url}}
        )
        return page["id"]
    except Exception as e:
        print(f"Error adding to Life Areas: {e}")
        return None


def add_to_brain_dump(title, content, msg_type, file_url=None):
    """Add an item to the Brain Dump inbox with visual styling"""
    db_id = os.getenv("BRAIN_DUMP_DB_ID")
    
    # Type-based icons for visual appeal
    TYPE_ICONS = {
        "text": "💭",
        "voice": "🎤",
        "photo": "📸",
        "document": "📄",
        "idea": "💡",
        "reminder": "⏰",
    }
    
    properties = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Content": {"rich_text": [{"text": {"content": content[:2000]}}]},  # Notion limit
        "Processed": {"checkbox": False},
        "Date": {"date": {"start": datetime.now().isoformat()}},
        "Type": {"select": {"name": msg_type}},
    }
    
    if file_url:
        properties["Files"] = {"files": [{"name": "Attachment", "external": {"url": file_url}}]}
    
    icon_emoji = TYPE_ICONS.get(msg_type, "📝")
    
    try:
        page = notion.pages.create(
            parent={"database_id": db_id}, 
            properties=properties,
            icon={"type": "emoji", "emoji": icon_emoji}
        )
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


def get_upcoming_deadlines(limit=3):
    """Get active items with upcoming deadlines, sorted by date"""
    db_id = os.getenv("LIFE_AREAS_DB_ID")
    
    try:
        # Fetch all active items first (client-side filtering is more reliable for variable date property names)
        # We reuse the logic from get_active_items but only query specific properties to be lighter? 
        # Actually easier to just get active items and filter/sort in python
        items = get_active_items()
        
        deadlines = []
        for item in items:
            props = item.get("properties", {})
            
            # Look for date property (Date, Deadline, Due Date)
            date_prop = None
            if "Date" in props: date_prop = props["Date"]
            elif "Due Date" in props: date_prop = props["Due Date"]
            elif "Deadline" in props: date_prop = props["Deadline"]
            
            if not date_prop or not date_prop.get("date"):
                continue
                
            date_str = date_prop["date"]["start"]
            # Parse date (ISO format)
            try:
                # Handle YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS...
                if "T" in date_str:
                    target_date = datetime.fromisoformat(date_str).replace(tzinfo=None)
                else:
                    target_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                # Calculate days left
                now = datetime.now()
                # For day-only dates, compare with today's date
                if "T" not in date_str:
                    days_left = (target_date.date() - now.date()).days
                else:
                    days_left = (target_date - now).days
                
                # Only include future or today's deadlines (or slightly past due)
                # Let's show everything from "yesterday" onwards
                
                # Format Countdown String efficiently here so it's available in JSON
                if "T" in date_str:
                    # ISO format with time
                    diff_seconds = (target_date - now).total_seconds()
                    hours = int(diff_seconds / 3600)
                    
                    if diff_seconds < 0:
                        formatted_time = f"🔥 OVERDUE ({abs(hours)}h)"
                    elif hours < 24:
                        formatted_time = f"💣 {hours}h LEFT"
                    else:
                        formatted_time = f"{days_left} DAYS LEFT"
                else:
                    # Date only
                    if days_left < 0: formatted_time = f"🔥 OVERDUE ({abs(days_left)}d)"
                    elif days_left == 0: formatted_time = "💣 DUE TODAY"
                    else: formatted_time = f"{days_left} DAYS LEFT"

                if days_left >= -1:
                    title = props.get("Name", {}).get("title", [{}])[0].get("text", {}).get("content", "Untitled")
                    deadlines.append({
                        "id": item["id"],
                        "title": title,
                        "date": date_str,
                        "days_left": days_left,
                        "formatted_time": formatted_time
                    })
            except Exception as e:
                logger.error(f"Error parsing date for item {item['id']}: {e}")
                continue
        
        # Sort by days remaining
        deadlines.sort(key=lambda x: x["days_left"])
        
        return deadlines[:limit]
        
    except Exception as e:
        logger.error(f"Error getting deadlines: {e}")
        return []


def get_completed_today():
    """Get items completed today"""
    db_id = os.getenv("LIFE_AREAS_DB_ID")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # We need to query for Done items specifically as get_active_items filters them out
        # AND check if they were updated today (approximation) or have a specific "Completed At" date
        # Since we don't track "Completed At" explicitly in a property usually, we rely on "Last Edited Time" 
        # provided by Notion meta-properties
        
        response = notion.request(
            path=f"databases/{db_id}/query",
            method="POST",
            body={
                "filter": {
                     "or": [
                        {"property": "Status", "select": {"equals": "Done"}},
                        {"property": "Status", "select": {"equals": "Completed"}}
                     ]
                }
            }
        )
        
        items = response.get("results", [])
        completed_today = []
        
        for item in items:
            # Check last edited time
            last_edited = item.get("last_edited_time", "")
            if last_edited.startswith(today_str):
                title = item["properties"].get("Name", {}).get("title", [{}])[0].get("text", {}).get("content", "Untitled")
                category = item["properties"].get("Category", {}).get("select", {}).get("name", "General")
                completed_today.append({
                    "id": item["id"],
                    "title": title,
                    "category": category
                })
        
        return completed_today
        
    except Exception as e:
        logger.error(f"Error getting completed items: {e}")
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


def get_high_priority_tasks(limit=3):
    """Get active High Priority items"""
    db_id = os.getenv("LIFE_AREAS_DB_ID")
    
    try:
        # WORKAROUND: databases.query() is missing, using raw request
        response = notion.request(
            path=f"databases/{db_id}/query",
            method="POST",
            body={
                "filter": {
                    "and": [
                        {"property": "Priority", "select": {"equals": "High"}},
                        {"property": "Status", "select": {"equals": "Active"}}
                    ]
                },
                # Sort by Date Added descending (newest first) or maybe deadline?
                # Let's simple sort by Name for stability or Date Added
                "sorts": [{"property": "Date Added", "direction": "descending"}],
                "page_size": limit
            }
        )
        
        items = response.get("results", [])
        high_priority = []
        
        for item in items:
            title = item["properties"].get("Name", {}).get("title", [{}])[0].get("text", {}).get("content", "Untitled")
            category = item["properties"].get("Category", {}).get("select", {}).get("name", "General")
            
            high_priority.append({
                "id": item["id"],
                "title": title,
                "category": category,
                "priority": "High"
            })
            
        return high_priority
        
    except Exception as e:
        logger.error(f"Error getting high priority tasks: {e}")
        return []


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

