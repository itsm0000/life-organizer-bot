"""
Habits Module - Recurring Tasks
Handles daily, twice-daily, weekly, and monthly recurring habits
"""
import os
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))

# Configure logging
import logging
logger = logging.getLogger(__name__)


def create_habit(name, frequency, category, times=None, xp_reward=25):
    """
    Create a recurring habit/task
    
    Args:
        name: Habit name (e.g., "Skincare Routine")
        frequency: "Daily" | "Twice Daily" | "Weekly" | "Monthly"
        category: Category name (e.g., "Health")
        times: List of times ["Morning", "Evening"] for twice daily
        xp_reward: XP awarded on completion (default 25)
    """
    db_id = os.getenv("HABITS_DB_ID")
    if not db_id:
        logger.warning("HABITS_DB_ID not set. Habits feature unavailable.")
        return None
    
    properties = {
        "Name": {"title": [{"text": {"content": name}}]},
        "Frequency": {"select": {"name": frequency}},
        "Category": {"select": {"name": category}},
        "XP Reward": {"number": xp_reward},
        "Active": {"checkbox": True},
        "Created": {"date": {"start": datetime.now().isoformat()}},
    }
    
    if times:
        properties["Times"] = {"multi_select": [{"name": t} for t in times]}
    
    CATEGORY_ICONS = {
        "Health": "💪", "Study": "📚", "Work": "💼", "Ideas": "💡",
        "Shopping": "🛒", "Skills": "🎯", "Finance": "💰", "Social": "👥",
        "Personal": "🌟",
    }
    icon = CATEGORY_ICONS.get(category, "🔁")
    
    try:
        page = notion.pages.create(
            parent={"database_id": db_id},
            properties=properties,
            icon={"type": "emoji", "emoji": icon}
        )
        logger.info(f"Created habit: {name} ({frequency})")
        return page["id"]
    except Exception as e:
        logger.error(f"Error creating habit: {e}")
        return None


def get_habits(active_only=True, frequency=None, time_of_day=None):
    """Get habits, optionally filtered by frequency and time"""
    db_id = os.getenv("HABITS_DB_ID")
    if not db_id:
        return []
    
    try:
        filters = []
        if active_only:
            filters.append({"property": "Active", "checkbox": {"equals": True}})
        if frequency:
            filters.append({"property": "Frequency", "select": {"equals": frequency}})
        
        body = {}
        if filters:
            body["filter"] = {"and": filters} if len(filters) > 1 else filters[0]
        
        response = notion.request(
            path=f"databases/{db_id}/query",
            method="POST",
            body=body
        )
        
        habits = response.get("results", [])
        
        # Filter by time of day if specified (for Morning/Evening filtering)
        if time_of_day:
            filtered = []
            for habit in habits:
                times_prop = habit.get("properties", {}).get("Times", {}).get("multi_select", [])
                times = [t.get("name") for t in times_prop]
                # Include if time matches, or if no times set (always show)
                if time_of_day in times or not times:
                    filtered.append(habit)
            habits = filtered
        
        return habits
    except Exception as e:
        logger.error(f"Error getting habits: {e}")
        return []


def complete_habit(habit_id):
    """Mark a habit as completed for today (updates Last Completed date)"""
    try:
        notion.pages.update(
            page_id=habit_id,
            properties={
                "Last Completed": {"date": {"start": datetime.now().isoformat()}}
            }
        )
        logger.info(f"Marked habit {habit_id} as completed")
        return True
    except Exception as e:
        logger.error(f"Error completing habit: {e}")
        return False


def get_habit_by_name(name_query):
    """Find a habit by partial name match"""
    habits = get_habits(active_only=True)
    
    name_lower = name_query.lower()
    for habit in habits:
        habit_name = habit.get("properties", {}).get("Name", {}).get("title", [{}])
        if habit_name:
            title = habit_name[0].get("text", {}).get("content", "").lower()
            if name_lower in title or title in name_lower:
                return habit
    return None


def format_habit_for_display(habit) -> str:
    """Format a habit for display in Telegram"""
    props = habit.get("properties", {})
    
    name = "Untitled"
    if props.get("Name", {}).get("title"):
        name = props["Name"]["title"][0].get("text", {}).get("content", "Untitled")
    
    frequency = props.get("Frequency", {}).get("select", {})
    freq_name = frequency.get("name", "Daily") if frequency else "Daily"
    
    xp = props.get("XP Reward", {}).get("number", 25)
    
    # Check if completed today
    last_completed = props.get("Last Completed", {}).get("date", {})
    last_date = last_completed.get("start", "") if last_completed else ""
    today = datetime.now().date().isoformat()
    is_done_today = last_date.startswith(today) if last_date else False
    
    emoji = "✅" if is_done_today else "⏳"
    
    return f"{emoji} {name} ({freq_name}) - {xp} XP"


def get_habit_xp(habit) -> int:
    """Get XP reward for a habit"""
    return habit.get("properties", {}).get("XP Reward", {}).get("number", 25)


def get_habit_name(habit) -> str:
    """Get habit name"""
    title = habit.get("properties", {}).get("Name", {}).get("title", [{}])
    return title[0].get("text", {}).get("content", "Habit") if title else "Habit"


def get_habit_category(habit) -> str:
    """Get habit category"""
    cat = habit.get("properties", {}).get("Category", {}).get("select", {})
    return cat.get("name", "General") if cat else "General"
