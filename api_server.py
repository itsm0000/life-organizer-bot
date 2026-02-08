"""
API Server for Life Organizer Widgets
Provides endpoints for the Telegram Mini App dashboard
"""
import os
import json
import hmac
import hashlib
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

# Import data functions from existing modules
from habits import get_habits, get_habit_xp, get_habit_name, get_habit_category
from notion_integration import get_active_items, get_items_by_category

# User data file (same as bot.py uses)
USER_DATA_FILE = "user_data.json"

def load_user_data():
    """Load user data from file"""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def verify_telegram_auth(init_data: str, bot_token: str) -> dict:
    """
    Verify Telegram WebApp initData
    Returns user data if valid, None otherwise
    """
    try:
        # Parse init_data
        parsed = dict(x.split('=') for x in init_data.split('&'))
        
        # Get hash from data
        data_hash = parsed.pop('hash', None)
        if not data_hash:
            return None
        
        # Create data check string
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed.items()))
        
        # Create secret key
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        # Verify (skip in development)
        if os.getenv("SKIP_AUTH") == "true" or calculated_hash == data_hash:
            user_data = json.loads(parsed.get('user', '{}'))
            return user_data
        
        return None
    except Exception as e:
        print(f"Auth error: {e}")
        return None


async def get_dashboard_data(request):
    """
    GET /api/dashboard
    Returns all widget data for the Mini App
    """
    # Add CORS headers
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, X-Telegram-Init-Data",
        "Access-Control-Allow-Methods": "GET, OPTIONS"
    }
    
    # Handle preflight
    if request.method == "OPTIONS":
        return web.Response(status=200, headers=headers)
    
    try:
        # Get user from Telegram init data (optional for now)
        init_data = request.headers.get("X-Telegram-Init-Data", "")
        user = verify_telegram_auth(init_data, os.getenv("TELEGRAM_BOT_TOKEN", ""))
        user_id = user.get("id") if user else None
        
        # Get habits
        habits = get_habits(active_only=True) or []
        habits_data = []
        for habit in habits:
            name = get_habit_name(habit)
            xp = get_habit_xp(habit)
            category = get_habit_category(habit)
            
            # Check if completed today
            props = habit.get("properties", {})
            last_completed = props.get("Last Completed", {}).get("date", {})
            completed_today = False
            if last_completed:
                from datetime import datetime
                last_date = last_completed.get("start", "")
                if last_date:
                    completed_today = last_date[:10] == datetime.now().strftime("%Y-%m-%d")
            
            habits_data.append({
                "id": habit.get("id"),
                "name": name,
                "xp": xp,
                "category": category,
                "completed": completed_today
            })
        
        # Get user stats
        user_data = load_user_data()
        user_str = str(user_id) if user_id else list(user_data.keys())[0] if user_data else "0"
        stats = user_data.get(user_str, {"xp": 0, "streak": 0, "level": 1})
        
        # Calculate level info
        xp = stats.get("xp", 0)
        level = stats.get("level", 1)
        streak = stats.get("streak", 0)
        
        level_titles = {
            1: "🌱 Seedling", 2: "🌿 Sprout", 3: "🌳 Sapling",
            4: "🌲 Tree", 5: "🏔️ Mountain", 6: "⭐ Star",
            7: "🌟 Superstar", 8: "🚀 Legend"
        }
        level_thresholds = [0, 50, 150, 350, 600, 1000, 2000, 5000]
        
        current_threshold = level_thresholds[min(level - 1, len(level_thresholds) - 1)]
        next_threshold = level_thresholds[min(level, len(level_thresholds) - 1)]
        level_progress = (xp - current_threshold) / max(next_threshold - current_threshold, 1)
        
        # Get active tasks count
        active_items = get_active_items() or []
        tasks_total = len(active_items)
        tasks_completed = len([i for i in active_items if i.get("properties", {}).get("Status", {}).get("status", {}).get("name") == "Done"])
        
        response_data = {
            "habits": habits_data,
            "xp": xp,
            "level": level,
            "levelTitle": level_titles.get(level, "🌱 Seedling"),
            "levelProgress": min(level_progress, 1.0),
            "streak": streak,
            "tasksToday": tasks_total,
            "tasksCompleted": tasks_completed
        }
        
        return web.json_response(response_data, headers=headers)
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        return web.json_response({"error": str(e)}, status=500, headers=headers)


async def health_check(request):
    """Health check endpoint"""
    return web.json_response({"status": "ok"})


def create_app():
    """Create aiohttp application"""
    app = web.Application()
    app.router.add_get("/api/dashboard", get_dashboard_data)
    app.router.add_options("/api/dashboard", get_dashboard_data)
    app.router.add_get("/health", health_check)
    return app


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 3001))
    print(f"Starting API server on port {port}")
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=port)
