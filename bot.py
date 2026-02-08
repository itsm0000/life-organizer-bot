"""
Life Organizer Telegram Bot
ADHD-friendly brain dump bot with AI categorization
"""
import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

import asyncio

# Import our modules
from ai_categorizer import categorize_message, analyze_image, parse_management_intent, ai_match_task, parse_habit_intent
from notion_integration import (
    add_to_life_areas, add_to_brain_dump, log_progress, get_active_items,
    search_items, update_item, delete_item, get_items_by_category, format_item_for_display
)
from habits import (
    get_habits, create_habit, complete_habit, get_habit_by_name,
    format_habit_for_display, get_habit_xp, get_habit_name, get_habit_category
)
from voice_transcriber import transcribe_voice

# Store pending delete confirmations {user_id: page_id}
pending_deletes = {}

# Load environment variables
load_dotenv()

# =============================================================================
# SECURITY: Whitelist & Rate Limiting (Phase 1)
# =============================================================================
from collections import defaultdict
import time
from functools import wraps

# Parse ALLOWED_USER_IDS from env (comma-separated list)
_allowed_ids_str = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS = [int(x.strip()) for x in _allowed_ids_str.split(",") if x.strip().isdigit()]

# Rate limiting config
_request_history = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
MAX_REQUESTS_PER_WINDOW = 20


def authorized_only(func):
    """Only allow whitelisted users. Silently ignore unauthorized."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
            return
        # If whitelist is empty, allow everyone (for backwards compatibility)
        if ALLOWED_USER_IDS and user.id not in ALLOWED_USER_IDS:
            logger.warning(f"Unauthorized access attempt: {user.id} ({user.first_name})")
            return  # Silently ignore
        return await func(update, context, *args, **kwargs)
    return wrapper


def rate_limited(func):
    """Limit requests per user to prevent abuse."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
            return await func(update, context, *args, **kwargs)
        
        user_id = user.id
        now = time.time()
        
        # Clean old requests
        _request_history[user_id] = [
            t for t in _request_history[user_id] 
            if now - t < RATE_LIMIT_WINDOW
        ]
        
        if len(_request_history[user_id]) >= MAX_REQUESTS_PER_WINDOW:
            await update.message.reply_text("⏳ Too many requests. Please wait a moment.")
            return
        
        _request_history[user_id].append(now)
        return await func(update, context, *args, **kwargs)
    return wrapper


def secure(func):
    """Combined decorator: authorized + rate limited."""
    return authorized_only(rate_limited(func))


# =============================================================================
# GAMIFICATION: XP, Levels & Streaks (Phase 4)
# =============================================================================
from datetime import datetime, timedelta

# In-memory XP storage (persists via Notion Progress DB for durability)
_user_xp = defaultdict(lambda: {"xp": 0, "last_action": None, "streak": 0})

# XP rewards
XP_TASK_ADDED = 5
XP_TASK_COMPLETED = 15
XP_VOICE_NOTE = 3
XP_FOCUS_COMPLETED = 25  # Bonus for using focus mode

# Level thresholds
LEVELS = [
    (0, "🌱 Seedling"),
    (50, "🌿 Sprout"),
    (150, "🌳 Sapling"),
    (350, "🌲 Tree"),
    (600, "🏔️ Mountain"),
    (1000, "⭐ Star"),
    (2000, "🌟 Superstar"),
    (5000, "🚀 Legend"),
]


def get_level(xp: int) -> tuple[int, str]:
    """Get level number and title for given XP."""
    level = 0
    title = LEVELS[0][1]
    for i, (threshold, name) in enumerate(LEVELS):
        if xp >= threshold:
            level = i + 1
            title = name
    return level, title


def add_xp(user_id: int, amount: int, reason: str = "") -> dict:
    """Add XP and update streak. Returns updated stats."""
    user = _user_xp[user_id]
    today = datetime.now().date()
    
    # Check streak
    if user["last_action"]:
        last_date = user["last_action"]
        if isinstance(last_date, str):
            last_date = datetime.fromisoformat(last_date).date()
        
        days_diff = (today - last_date).days
        if days_diff == 1:
            user["streak"] += 1
        elif days_diff > 1:
            user["streak"] = 1  # Reset streak
        # Same day = streak stays the same
    else:
        user["streak"] = 1
    
    user["last_action"] = today.isoformat()
    user["xp"] += amount
    
    # Streak bonus (every 7 days = +50 XP)
    if user["streak"] > 0 and user["streak"] % 7 == 0:
        user["xp"] += 50
        logger.info(f"User {user_id} got 7-day streak bonus! +50 XP")
    
    logger.info(f"User {user_id}: +{amount} XP ({reason}). Total: {user['xp']}")
    return user


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


@secure
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f"Hey {user.first_name}! 👋\n\n"
        "I'm your Life Organizer Bot. Just dump anything on your mind:\n\n"
        "📝 Text messages\n"
        "📸 Images (with or without captions)\n"
        "📄 PDFs/Documents\n"
        "🎤 Voice notes\n\n"
        "I'll automatically categorize and organize everything in your Notion workspace.\n\n"
        "Commands:\n"
        "/active - See what you're currently working on\n"
        "/help - Get help"
    )


@secure
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "🤖 *Life Organizer Bot Help*\n\n"
        "*How to use:*\n"
        "Just send me anything! I'll organize it for you.\n\n"
        "*Examples:*\n"
        "• \"Buy whey protein\" → Goes to Shopping\n"
        "• \"Study chapter 5 for midterm\" → Goes to Study\n"
        "• Photo of a guitar → I'll ask what it's for\n"
        "• \"Learn to play piano\" → Goes to Skills\n\n"
        "*Commands:*\n"
        "/start - Introduction\n"
        "/active - See active items\n"
        "/focus - 🎯 Focus on ONE task\n"
        "/stats - 📊 Your XP & level\n"
        "/weekly - 📅 Weekly review\n"
        "/help - This message",
        parse_mode="Markdown"
    )


@secure
async def active_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show active items from Notion with pagination"""
    await update.message.reply_text("🔍 Fetching your active items...")
    
    items = get_active_items()
    
    if not items:
        await update.message.reply_text(
            "No active items yet! Start dumping your thoughts and I'll organize them."
        )
        return
    
    # Store items in context for pagination
    context.user_data["active_items"] = items
    context.user_data["active_page"] = 0
    
    await send_paginated_active(update.message, context, items, 0)


async def send_paginated_active(message_or_query, context, items, page, is_edit=False):
    """Send paginated active items list."""
    per_page = 5
    total_pages = (len(items) + per_page - 1) // per_page
    start = page * per_page
    end = min(start + per_page, len(items))
    page_items = items[start:end]
    
    # Group by category
    by_category = {}
    for item in page_items:
        props = item["properties"]
        category = props.get("Category", {}).get("select", {}).get("name", "Other")
        title = props.get("Name", {}).get("title", [{}])[0].get("plain_text", "Untitled")
        priority = props.get("Priority", {}).get("select", {}).get("name", "Medium")
        p_icon = {"🔴": "High", "🟡": "Medium", "🟢": "Low"}.get(priority, "⚪")
        # Reverse lookup
        p_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
        
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(f"  {p_icon} {title}")
    
    text = f"📋 *Active Items* (Page {page + 1}/{total_pages})\n\n"
    for category, items_list in by_category.items():
        text += f"*{category}:*\n" + "\n".join(items_list) + "\n\n"
    text += f"_{len(items)} total items_"
    
    # Build pagination keyboard
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"active_page_{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if end < len(items):
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"active_page_{page+1}"))
    
    keyboard = InlineKeyboardMarkup([nav_buttons]) if len(nav_buttons) > 1 else None
    
    if is_edit:
        await message_or_query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await message_or_query.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


async def handle_active_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pagination callback for /active command."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "noop":
        return
    
    # Parse page number
    page = int(query.data.replace("active_page_", ""))
    items = context.user_data.get("active_items", [])
    
    if not items:
        await query.edit_message_text("Session expired. Use /active again.")
        return
    
    context.user_data["active_page"] = page
    await send_paginated_active(query, context, items, page, is_edit=True)


@secure
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's XP, level, and streak."""
    user_id = update.effective_user.id
    user_data = _user_xp[user_id]
    
    xp = user_data["xp"]
    streak = user_data["streak"]
    level, title = get_level(xp)
    
    # Find next level threshold
    next_threshold = None
    for threshold, _ in LEVELS:
        if threshold > xp:
            next_threshold = threshold
            break
    
    # Progress bar to next level
    if next_threshold:
        prev_threshold = LEVELS[level - 1][0] if level > 0 else 0
        progress = (xp - prev_threshold) / (next_threshold - prev_threshold)
        bar_filled = int(progress * 10)
        progress_bar = "█" * bar_filled + "░" * (10 - bar_filled)
        progress_text = f"{progress_bar} {xp}/{next_threshold} XP"
    else:
        progress_text = "🏆 MAX LEVEL!"
    
    # Streak emoji
    if streak >= 7:
        streak_emoji = "🔥🔥🔥"
    elif streak >= 3:
        streak_emoji = "🔥🔥"
    elif streak >= 1:
        streak_emoji = "🔥"
    else:
        streak_emoji = "💤"
    
    await update.message.reply_text(
        f"📊 *Your Stats*\n\n"
        f"*Level {level}*: {title}\n"
        f"{progress_text}\n\n"
        f"*Streak*: {streak} days {streak_emoji}\n\n"
        f"_Keep adding and completing tasks to level up!_",
        parse_mode="Markdown"
    )


@secure
async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show weekly progress summary."""
    user_id = update.effective_user.id
    
    await update.message.reply_text("📅 Generating your weekly review...")
    
    # Get all items
    items = get_active_items()
    
    # Count by status (we can only see Active items, need to query differently for Done)
    # For now, show active items count and XP progress
    active_count = len(items)
    
    # Count by category
    by_category = defaultdict(int)
    high_priority_count = 0
    for item in items:
        props = item.get("properties", {})
        cat = props.get("Category", {}).get("select", {}).get("name", "Other")
        by_category[cat] += 1
        if props.get("Priority", {}).get("select", {}).get("name") == "High":
            high_priority_count += 1
    
    # Get user stats
    user_data = _user_xp[user_id]
    xp = user_data["xp"]
    streak = user_data["streak"]
    level, title = get_level(xp)
    
    # Build categories list
    cat_lines = "\n".join([f"  • {cat}: {count}" for cat, count in sorted(by_category.items())])
    
    await update.message.reply_text(
        f"📅 *Weekly Review*\n\n"
        f"*Active Tasks:* {active_count}\n"
        f"🔴 High Priority: {high_priority_count}\n\n"
        f"*By Category:*\n{cat_lines}\n\n"
        f"──────────────\n"
        f"*Your Progress:*\n"
        f"Level {level}: {title}\n"
        f"🔥 {streak} day streak\n"
        f"⭐ {xp} XP total\n\n"
        f"_Use /focus to tackle your top task!_",
        parse_mode="Markdown"
    )


# =============================================================================
# CATEGORY QUICK COMMANDS (Phase 4)
# =============================================================================
CATEGORY_ICONS = {
    "Health": "🏃",
    "Study": "📚",
    "Work": "💼",
    "Ideas": "💡",
    "Shopping": "🛒",
    "Skills": "🎯",
    "Finance": "💰",
    "Social": "👥",
}


async def category_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    """Generic handler for category commands with pagination."""
    items = get_items_by_category(category)
    icon = CATEGORY_ICONS.get(category, "📂")
    
    if not items:
        await update.message.reply_text(f"{icon} No active items in *{category}*", parse_mode="Markdown")
        return
    
    # Store for pagination
    context.user_data[f"cat_{category}_items"] = items
    context.user_data[f"cat_{category}_page"] = 0
    
    await send_paginated_category(update.message, context, items, category, 0)


async def send_paginated_category(message_or_query, context, items, category, page, is_edit=False):
    """Send paginated category items list."""
    per_page = 5
    total_pages = (len(items) + per_page - 1) // per_page
    start = page * per_page
    end = min(start + per_page, len(items))
    page_items = items[start:end]
    
    icon = CATEGORY_ICONS.get(category, "📂")
    text = f"{icon} *{category}* ({len(items)} items, Page {page + 1}/{total_pages})\n\n"
    
    for item in page_items:
        props = item.get("properties", {})
        title = props.get("Name", {}).get("title", [{}])[0].get("plain_text", "Untitled")
        priority = props.get("Priority", {}).get("select", {}).get("name", "Low")
        p_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
        text += f"{p_icon} {title}\n"
    
    # Build pagination keyboard
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"cat_{category}_{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if end < len(items):
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"cat_{category}_{page+1}"))
    
    keyboard = InlineKeyboardMarkup([nav_buttons]) if len(nav_buttons) > 1 else None
    
    if is_edit:
        await message_or_query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await message_or_query.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


async def handle_category_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pagination callback for category commands."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "noop":
        return
    
    # Parse category and page: cat_Health_1
    parts = query.data.split("_")
    if len(parts) < 3:
        return
    
    category = parts[1]
    page = int(parts[2])
    items = context.user_data.get(f"cat_{category}_items", [])
    
    if not items:
        await query.edit_message_text("Session expired. Use category command again.")
        return
    
    context.user_data[f"cat_{category}_page"] = page
    await send_paginated_category(query, context, items, category, page, is_edit=True)


@secure
async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await category_command_handler(update, context, "Health")

@secure
async def study_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await category_command_handler(update, context, "Study")

@secure
async def work_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await category_command_handler(update, context, "Work")

@secure
async def ideas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await category_command_handler(update, context, "Ideas")

@secure
async def shopping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await category_command_handler(update, context, "Shopping")


@secure
async def habits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all active habits with completion status"""
    habits = get_habits(active_only=True)
    
    if not habits:
        await update.message.reply_text(
            "🔁 *No habits yet!*\n\n"
            "Add one via Notion or ask me to create habits database.",
            parse_mode="Markdown"
        )
        return
    
    # Group by completion status
    done_today = []
    pending = []
    
    for habit in habits:
        formatted = format_habit_for_display(habit)
        if formatted.startswith("✅"):
            done_today.append(formatted)
        else:
            pending.append(formatted)
    
    # Build response
    response = "🔁 *Your Habits*\n\n"
    
    if pending:
        response += "⏳ *Pending Today:*\n"
        for h in pending:
            response += f"  {h}\n"
        response += "\n"
    
    if done_today:
        response += "✅ *Completed Today:*\n"
        for h in done_today:
            response += f"  {h}\n"
    
    response += f"\n📊 {len(done_today)}/{len(habits)} done today"
    
    await update.message.reply_text(response, parse_mode="Markdown")


@secure
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages - both new items and task management"""
    text = update.message.text
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"Received text from {user.first_name}: {text[:50]}...")
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    # Check for delete confirmation
    if user_id in pending_deletes and text.upper() in ["YES", "نعم", "اي"]:
        page_id = pending_deletes.pop(user_id)
        if delete_item(page_id):
            await update.message.reply_text("✅ Deleted successfully!")
        else:
            await update.message.reply_text("❌ Failed to delete. Try again.")
        return
    elif user_id in pending_deletes:
        pending_deletes.pop(user_id)
        await update.message.reply_text("❌ Delete cancelled.")
        return
    
    try:
        # First, check if this is a habit-related command (create or complete)
        logger.info("Checking for habit intent...")
        habit_intent = await parse_habit_intent(text)
        logger.info(f"Habit intent: {habit_intent}")
        
        if habit_intent.get("intent") == "create_habit":
            await handle_habit_create(update, habit_intent, user_id)
            return
        elif habit_intent.get("intent") == "complete_habit":
            await handle_habit_complete(update, habit_intent, user_id)
            return
        
        # Next, check if this is a management command
        logger.info("Checking for management intent...")
        intent = await parse_management_intent(text)
        logger.info(f"Management intent: {intent}")
        
        if intent.get("intent") != "none":
            await handle_management_command(update, intent, user_id)
            return
        
        # Not a management command - categorize and add as new item
        logger.info("Calling AI categorizer...")
        result = await categorize_message(text)
        logger.info(f"AI result: {result}")
        
        # Add to Notion
        logger.info(f"Adding to Notion Life Areas: {result['category']}")
        notion_id = add_to_life_areas(
            category=result["category"],
            title=result["title"],
            item_type=result["type"],
            priority=result["priority"],
            notes=result["summary"]
        )
        logger.info(f"Notion response ID: {notion_id}")
        
        if notion_id:
            response = (
                f"✅ Got it! Added to *{result['category']}*\n\n"
                f"📌 {result['title']}\n"
                f"🎯 Priority: {result['priority']}\n"
            )
            if result.get("suggested_action"):
                response += f"\n💡 Suggestion: {result['suggested_action']}"
            
            await update.message.reply_text(response, parse_mode="Markdown")
            
            # Award XP for adding a task
            add_xp(user_id, XP_TASK_ADDED, "added task")
        else:
            logger.error("Notion returned None - adding to Brain Dump")
            add_to_brain_dump(text[:100], text, "Text")
            await update.message.reply_text(
                "⚠️ Something went wrong. Added to Brain Dump for manual processing."
            )
    
    except Exception as e:
        logger.error(f"Error in handle_text: {e}", exc_info=True)
        try:
            add_to_brain_dump(text[:100], text, "Text")
            await update.message.reply_text(
                f"⚠️ Error: {str(e)}\nAdded to Brain Dump for manual processing."
            )
        except Exception as e2:
            logger.error(f"Even Brain Dump failed: {e2}", exc_info=True)
            await update.message.reply_text(
                f"❌ Critical error: {str(e)}\nPlease check logs."
            )


async def handle_habit_create(update: Update, habit_intent: dict, user_id: int):
    """Handle creating a new habit from natural language"""
    name = habit_intent.get("habit_name", "New Habit")
    frequency = habit_intent.get("frequency", "Daily")
    times = habit_intent.get("times")
    category = habit_intent.get("category", "Personal")
    xp_reward = habit_intent.get("xp_reward", 25)
    
    # Create the habit
    habit_id = create_habit(
        name=name,
        frequency=frequency,
        category=category,
        times=times,
        xp_reward=xp_reward
    )
    
    if habit_id:
        times_str = f" ({', '.join(times)})" if times else ""
        await update.message.reply_text(
            f"🔁 *Habit Created!*\n\n"
            f"📝 {name}\n"
            f"⏰ {frequency}{times_str}\n"
            f"📂 {category}\n"
            f"🎮 {xp_reward} XP per completion\n\n"
            f"Say \"{name} done\" when you complete it!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Failed to create habit. Make sure HABITS_DB_ID is set in Railway."
        )


async def handle_habit_complete(update: Update, habit_intent: dict, user_id: int):
    """Handle completing a habit from natural language"""
    habit_name = habit_intent.get("habit_name", "")
    
    if not habit_name:
        await update.message.reply_text("🤔 Which habit did you complete?")
        return
    
    # Find matching habit
    habit = get_habit_by_name(habit_name)
    
    if not habit:
        await update.message.reply_text(
            f"🔍 Couldn't find a habit matching '{habit_name}'.\n\n"
            f"💡 Use /habits to see your habits."
        )
        return
    
    # Mark as completed
    habit_id = habit.get("id")
    if complete_habit(habit_id):
        name = get_habit_name(habit)
        xp = get_habit_xp(habit)
        category = get_habit_category(habit)
        
        # Log to progress
        log_progress(
            activity=f"Habit: {name}",
            category=category,
            notes="Daily habit completed"
        )
        
        # Award XP
        user_data = add_xp(user_id, xp, f"habit_complete:{name}")
        
        await update.message.reply_text(
            f"✅ *{name}* done!\n\n"
            f"🎮 +{xp} XP | Total: {user_data['xp']} | Streak: {user_data['streak']}🔥\n"
            f"📊 Progress logged!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Failed to mark habit as complete.")


async def handle_management_command(update: Update, intent: dict, user_id: int):
    """Handle task management commands (delete, update, query)"""
    action = intent.get("intent")
    target = intent.get("target", "")
    category = intent.get("category")
    new_priority = intent.get("new_priority")
    
    if action == "query":
        # List items in category or all active items
        if category:
            items = get_items_by_category(category)
            if not items:
                await update.message.reply_text(f"No active items in {category}.")
                return
            
            response = f"📋 *{category}* ({len(items)} items):\n\n"
            for item in items[:15]:
                response += format_item_for_display(item) + "\n"
            await update.message.reply_text(response, parse_mode="Markdown")
        else:
            items = get_active_items()
            if not items:
                await update.message.reply_text("No active items yet!")
                return
            
            response = f"📋 *Active Items* ({len(items)}):\n\n"
            for item in items[:15]:
                response += format_item_for_display(item) + "\n"
            await update.message.reply_text(response, parse_mode="Markdown")
        return
    
    # For delete, complete, update - need to find the item using AI matching
    # Get all active items and let AI pick the best match
    all_items = get_active_items()
    
    if not all_items:
        await update.message.reply_text("📋 No active items to manage.")
        return
    
    # Use AI to find the best matching task
    matched_item = await ai_match_task(target or intent.get("original_text", ""), all_items)
    
    if not matched_item:
        await update.message.reply_text(
            f"🔍 Couldn't find a matching task for '{target}'.\n\n"
            f"💡 Try saying: /active to see all your tasks"
        )
        return
    
    # AI found a match
    item = matched_item
    page_id = item["id"]
    title = item["properties"].get("Name", {}).get("title", [{}])[0].get("text", {}).get("content", "Untitled")
    
    if action == "delete":
        # Ask for confirmation
        pending_deletes[user_id] = page_id
        await update.message.reply_text(
            f"⚠️ Delete *{title}*?\n\nReply YES to confirm, anything else to cancel.",
            parse_mode="Markdown"
        )
    
    elif action == "complete":
        if update_item(page_id, {"status": "Done"}):
            # Get category for progress logging
            category = item["properties"].get("Category", {}).get("select", {})
            category_name = category.get("name", "General") if category else "General"
            
            # Log to Progress Tracker
            log_progress(
                activity=f"Completed: {title}",
                category=category_name,
                notes="Marked done via bot"
            )
            
            # Award XP
            user_data = add_xp(user_id, 25, f"task_complete:{title}")
            xp_msg = f"\n🎮 +25 XP | Total: {user_data['xp']} | Streak: {user_data['streak']}🔥"
            
            await update.message.reply_text(
                f"✅ Marked *{title}* as Done!{xp_msg}\n📊 Progress logged!",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Failed to update. Try again.")
    
    elif action == "update_priority":
        if new_priority and update_item(page_id, {"priority": new_priority}):
            await update.message.reply_text(
                f"✅ Updated *{title}* → Priority: {new_priority}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Failed to update priority. Try again.")


@secure
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages with AI vision analysis"""
    photo = update.message.photo[-1]  # Get highest resolution
    caption = update.message.caption or ""
    user = update.effective_user
    
    logger.info(f"Received photo from {user.first_name}")
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Download photo
    file = await context.bot.get_file(photo.file_id)
    
    try:
        # Download the image bytes
        image_bytes = await file.download_as_bytearray()
        
        # Analyze with AI Vision
        logger.info("Analyzing image with Llama Vision...")
        result = await analyze_image(bytes(image_bytes), caption)
        
        logger.info(f"Vision result: {result}")
        
        # Extract results
        description = result.get("description", caption or "Image")
        category = result.get("category", "Ideas")
        title = result.get("suggested_title", "Image")
        priority = result.get("priority", "Low")
        suggestion = result.get("suggested_action", "")
        
        # Add to Notion
        notion_id = add_to_life_areas(
            category=category,
            title=title,
            item_type="Resource",
            priority=priority,
            notes=f"📸 Image Analysis:\n\n{description}",
            image_url=file.file_path
        )
        
        if notion_id:
            response = (
                f"📸 Image analyzed & added to {category}\n\n"
                f"👁️ \"{description[:100]}{'...' if len(description) > 100 else ''}\"\n\n"
                f"📌 {title}\n"
                f"🎯 Priority: {priority}"
            )
            if suggestion:
                response += f"\n💡 Suggestion: {suggestion}"
            
            await update.message.reply_text(response)
        else:
            add_to_brain_dump(title, description, "Image", file.file_path)
            await update.message.reply_text("⚠️ Analyzed but couldn't save. Added to Brain Dump.")
    
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        add_to_brain_dump(caption or "Image", f"Error: {str(e)}", "Image", file.file_path)
        await update.message.reply_text("⚠️ Error processing image. Saved to Brain Dump.")


@secure
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document/PDF messages"""
    document = update.message.document
    caption = update.message.caption or document.file_name
    
    logger.info(f"Received document: {document.file_name}")
    
    await update.message.reply_text("📄 Processing document...")
    
    file = await context.bot.get_file(document.file_id)
    file_url = file.file_path
    
    # Categorize based on caption/filename
    result = await categorize_message(
        f"Document: {caption}",
        has_file=True
    )
    
    # Add to Brain Dump (documents need manual review)
    add_to_brain_dump(caption, f"Document: {caption}", "PDF", file_url)
    
    await update.message.reply_text(
        f"📄 Document saved to Brain Dump\n"
        f"Suggested category: *{result['category']}*\n\n"
        f"Review it in Notion when you have time!",
        parse_mode="Markdown"
    )


@secure
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages with transcription"""
    voice = update.message.voice
    user = update.message.from_user
    
    logger.info(f"Received voice message from {user.first_name}")
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Download voice file
    file = await context.bot.get_file(voice.file_id)
    
    try:
        # Download the audio bytes
        audio_bytes = await file.download_as_bytearray()
        
        # Transcribe using Groq Whisper
        logger.info("Transcribing voice note...")
        transcription = await transcribe_voice(bytes(audio_bytes), "voice.ogg")
        
        if transcription.startswith("["):
            # Transcription failed
            logger.error(f"Transcription failed: {transcription}")
            await update.message.reply_text(
                f"🎤 Voice note received but transcription failed.\n\n"
                f"Saved to Brain Dump for manual review."
            )
            add_to_brain_dump("Voice note (transcription failed)", "Voice message", "Voice", file.file_path)
            return
        
        logger.info(f"Transcription: {transcription[:100]}...")
        
        # First check if this is a habit-related command (create or complete)
        logger.info("Checking for habit intent in voice...")
        habit_intent = await parse_habit_intent(transcription)
        logger.info(f"Voice habit intent: {habit_intent}")
        
        if habit_intent.get("intent") == "create_habit":
            await handle_habit_create(update, habit_intent, user.id)
            await update.message.reply_text(f"🎤 \"{transcription}\"")
            return
        elif habit_intent.get("intent") == "complete_habit":
            await handle_habit_complete(update, habit_intent, user.id)
            await update.message.reply_text(f"🎤 \"{transcription}\"")
            return
        
        # Next check if this is a management command
        logger.info("Checking for management intent in voice...")
        intent = await parse_management_intent(transcription)
        logger.info(f"Voice management intent: {intent}")
        
        if intent.get("intent") != "none":
            # Handle as management command
            await handle_management_command(update, intent, user.id)
            # Also show what was transcribed
            await update.message.reply_text(f"🎤 \"{transcription}\"")
            return
        
        # Not a management command - categorize as new item
        logger.info("Calling AI categorizer...")
        result = await categorize_message(transcription)
        logger.info(f"AI result: {result}")
        
        # Add to appropriate Notion database
        category = result.get("category", "Ideas")
        item_type = result.get("type", "Idea")
        priority = result.get("priority", "Low")
        title = result.get("title", transcription[:50])
        summary = result.get("summary", transcription)
        suggestion = result.get("suggested_action", "")
        
        # Store in Life Areas
        logger.info(f"Adding to Notion Life Areas: {category}")
        notion_id = add_to_life_areas(
            title=title,
            category=category,
            item_type=item_type,
            priority=priority,
            notes=f"🎤 Voice note transcription:\n\n{transcription}"
        )
        
        logger.info(f"Notion response ID: {notion_id}")
        
        if notion_id:
            response = (
                f"🎤 Voice transcribed & added to {category}\n\n"
                f"📝 \"{transcription[:100]}{'...' if len(transcription) > 100 else ''}\"\n\n"
                f"📌 {title}\n"
                f"🎯 Priority: {priority}"
            )
            if suggestion:
                response += f"\n💡 Suggestion: {suggestion}"
            
            await update.message.reply_text(response)
        else:
            logger.error("Notion returned None - adding to Brain Dump")
            add_to_brain_dump(title, transcription, "Voice")
            await update.message.reply_text(
                "⚠️ Transcribed but couldn't categorize. Added to Brain Dump."
            )
            
    except Exception as e:
        logger.error(f"Voice handling error: {e}")
        await update.message.reply_text(
            "⚠️ Error processing voice note. Added to Brain Dump for review."
        )
        add_to_brain_dump("Voice note (error)", f"Error: {str(e)}", "Voice", file.file_path)


# =============================================================================
# FOCUS MODE: ADHD-Friendly Single Task Mode (Phase 2)
# =============================================================================
from telegram.ext import ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

FOCUS_CHOOSING, FOCUS_ACTIVE = range(2)
_focus_sessions = {}  # {user_id: {"task": task_name, "page_id": page_id}}
_focus_pending_tasks = defaultdict(list)  # {user_id: [task_texts]} - tasks queued during focus mode


@secure
async def focus_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Focus Mode - show high priority tasks to choose from."""
    user_id = update.effective_user.id
    
    await update.message.reply_text("🎯 *Focus Mode*\n\nFetching your top priority tasks...", parse_mode="Markdown")
    
    items = get_active_items()
    if not items:
        await update.message.reply_text("No active tasks! Add some tasks first.")
        return ConversationHandler.END
    
    # Filter and sort by priority
    high_priority = []
    for item in items:
        props = item.get("properties", {})
        priority = props.get("Priority", {}).get("select", {}).get("name", "Medium")
        title = props.get("Name", {}).get("title", [{}])[0].get("plain_text", "Untitled")
        if priority in ["High", "Medium"]:
            high_priority.append({
                "id": item["id"],
                "title": title,
                "priority": priority
            })
    
    if not high_priority:
        await update.message.reply_text("No high priority tasks. Enjoy your break! ☕")
        return ConversationHandler.END
    
    # Create inline keyboard with top 5 tasks
    keyboard = []
    for i, task in enumerate(high_priority[:5]):
        icon = "🔴" if task["priority"] == "High" else "🟡"
        keyboard.append([InlineKeyboardButton(
            f"{icon} {task['title'][:40]}", 
            callback_data=f"focus_{i}"
        )])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="focus_cancel")])
    
    # Store tasks in context for callback
    context.user_data["focus_tasks"] = high_priority[:5]
    
    await update.message.reply_text(
        "🧘 *Pick ONE task to focus on:*\n\n"
        "Everything else will wait. Just this one thing.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return FOCUS_CHOOSING


async def focus_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle task selection in Focus Mode."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "focus_cancel":
        await query.edit_message_text("Focus mode cancelled. Back to chaos! 🌪️")
        return ConversationHandler.END
    
    # Parse task index
    task_idx = int(query.data.replace("focus_", ""))
    tasks = context.user_data.get("focus_tasks", [])
    
    if task_idx >= len(tasks):
        await query.edit_message_text("Something went wrong. Try /focus again.")
        return ConversationHandler.END
    
    task = tasks[task_idx]
    user_id = update.effective_user.id
    
    # Store active focus session
    _focus_sessions[user_id] = {
        "task": task["title"],
        "page_id": task["id"]
    }
    
    await query.edit_message_text(
        f"🎯 *FOCUS MODE ACTIVE*\n\n"
        f"📌 *{task['title']}*\n\n"
        f"This is your ONE thing right now.\n"
        f"Everything else can wait.\n\n"
        f"When done, say: *done* or *finished*\n"
        f"To exit focus mode: /cancel",
        parse_mode="Markdown"
    )
    return FOCUS_ACTIVE


async def focus_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Complete the focused task or queue new tasks."""
    user_id = update.effective_user.id
    text = update.message.text
    text_lower = text.lower()
    
    if text_lower in ["done", "finished", "complete", "تم", "خلص"]:
        session = _focus_sessions.pop(user_id, None)
        pending_tasks = _focus_pending_tasks.pop(user_id, [])
        
        if session:
            # Mark task as done in Notion
            update_item(session["page_id"], {"status": "Done"})
            
            # Award XP for completing task via Focus Mode (bonus!)
            stats = add_xp(user_id, XP_FOCUS_COMPLETED, "focus mode completion")
            level, title = get_level(stats["xp"])
            
            completion_msg = (
                f"🎉 *AMAZING!*\n\n"
                f"You crushed it! ✅ *{session['task']}* is DONE!\n\n"
                f"+{XP_FOCUS_COMPLETED} XP 💫 (Level {level}: {title})"
            )
            
            # Process any queued tasks
            if pending_tasks:
                completion_msg += f"\n\n📝 Processing {len(pending_tasks)} queued task(s)..."
            
            await update.message.reply_text(completion_msg, parse_mode="Markdown")
            
            # Add queued tasks to Notion
            for queued_text in pending_tasks:
                try:
                    result = await categorize_message(queued_text)
                    notion_id = add_to_life_areas(
                        category=result["category"],
                        title=result["title"],
                        item_type=result["type"],
                        priority=result["priority"],
                        notes=result["summary"]
                    )
                    if notion_id:
                        await update.message.reply_text(
                            f"✅ Added: *{result['title']}* → {result['category']}",
                            parse_mode="Markdown"
                        )
                        add_xp(user_id, XP_TASK_ADDED, "added queued task")
                except Exception as e:
                    logger.error(f"Error processing queued task: {e}")
                    await update.message.reply_text(f"⚠️ Failed to add: {queued_text[:30]}...")
            
            if pending_tasks:
                await update.message.reply_text("Take a breather, then /focus on the next one. 💪")
        else:
            await update.message.reply_text("No active focus session. Start with /focus")
        return ConversationHandler.END
    
    # User sent something while in focus mode - queue it as a new task
    session = _focus_sessions.get(user_id, {})
    task = session.get("task", "your task")
    
    # Queue the text as a pending task (it will be processed after focus ends)
    _focus_pending_tasks[user_id].append(text)
    pending_count = len(_focus_pending_tasks[user_id])
    
    await update.message.reply_text(
        f"📝 Noted! I'll add this after you're done focusing.\n\n"
        f"🧘 Still in Focus Mode on: *{task}*\n"
        f"📋 {pending_count} task(s) queued\n\n"
        f"Say *done* when finished, or /cancel to exit.",
        parse_mode="Markdown"
    )
    return FOCUS_ACTIVE


async def focus_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel focus mode and discard queued tasks."""
    user_id = update.effective_user.id
    _focus_sessions.pop(user_id, None)
    pending_count = len(_focus_pending_tasks.pop(user_id, []))
    
    cancel_msg = "Focus mode ended. No worries, you can try again anytime! 💪"
    if pending_count > 0:
        cancel_msg += f"\n\n⚠️ {pending_count} queued task(s) discarded."
    
    await update.message.reply_text(cancel_msg)
    return ConversationHandler.END


# Create the ConversationHandler
focus_handler = ConversationHandler(
    entry_points=[CommandHandler("focus", focus_start)],
    states={
        FOCUS_CHOOSING: [CallbackQueryHandler(focus_chosen, pattern="^focus_")],
        FOCUS_ACTIVE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, focus_complete),
            CommandHandler("cancel", focus_cancel),
        ],
    },
    fallbacks=[CommandHandler("cancel", focus_cancel)],
)


# =============================================================================
# SMART NUDGES: Daily Reminder for Stale Tasks (Phase 4)
# =============================================================================
async def daily_nudge_callback(context: ContextTypes.DEFAULT_TYPE):
    """Send daily reminder about high-priority tasks."""
    # Get all whitelisted users
    if not ALLOWED_USER_IDS:
        return  # No whitelisted users
    
    items = get_active_items()
    high_priority = [
        item for item in items
        if item.get("properties", {}).get("Priority", {}).get("select", {}).get("name") == "High"
    ]
    
    if not high_priority:
        return  # No high priority tasks
    
    # Pick a random one to nudge about
    import random
    task = random.choice(high_priority)
    title = task.get("properties", {}).get("Name", {}).get("title", [{}])[0].get("plain_text", "a task")
    
    message = (
        f"👋 *Morning Nudge*\n\n"
        f"You have {len(high_priority)} high-priority tasks.\n\n"
        f"🔴 *{title}* is waiting for you!\n\n"
        f"Use /focus to crush it today 💪"
    )
    
    # Send to all whitelisted users
    for user_id in ALLOWED_USER_IDS:
        try:
            await context.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send nudge to {user_id}: {e}")


async def daily_nudge_callback(context):
    """Send daily nudge to all users"""
    message = "🌅 *Good morning!*\n\nUse /habits to see today's habits.\nUse /active to see your tasks."
    
    for user_id in ALLOWED_USER_IDS:
        if user_id == 0:
            continue
        try:
            await context.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send daily nudge to {user_id}: {e}")


async def morning_habits_callback(context):
    """Send morning habit reminder"""
    for user_id in ALLOWED_USER_IDS:
        if user_id == 0:
            continue
        try:
            # Get morning habits
            habits = get_habits(active_only=True, time_of_day="Morning")
            if not habits:
                # Also get daily habits without specific times
                habits = get_habits(active_only=True, frequency="Daily")
            
            if not habits:
                continue  # No habits to remind about
            
            # Build message
            message = "🌅 *Good Morning!*\n\n⏳ *Today's Habits:*\n"
            total_xp = 0
            for habit in habits:
                formatted = format_habit_for_display(habit)
                message += f"  {formatted}\n"
                total_xp += get_habit_xp(habit)
            
            message += f"\n🎮 Potential XP: {total_xp}\n\nSay \"[habit] done\" when complete!"
            
            await context.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send morning habits to {user_id}: {e}")


async def evening_habits_callback(context):
    """Send evening habit reminder"""
    for user_id in ALLOWED_USER_IDS:
        if user_id == 0:
            continue
        try:
            # Get evening habits
            habits = get_habits(active_only=True, time_of_day="Evening")
            
            if not habits:
                continue  # No evening habits
            
            # Count completed today
            done_count = 0
            pending = []
            for habit in habits:
                formatted = format_habit_for_display(habit)
                if formatted.startswith("✅"):
                    done_count += 1
                else:
                    pending.append(formatted)
            
            if not pending:
                # All done!
                message = f"🌙 *Evening Check-in*\n\n✅ All {done_count} habits complete! Great job! 🎉"
            else:
                message = "🌙 *Evening Reminder*\n\n⏳ *Still pending:*\n"
                for p in pending:
                    message += f"  {p}\n"
                message += f"\n✅ Completed: {done_count}/{len(habits)}"
            
            await context.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send evening habits to {user_id}: {e}")


def main():
    """Start the bot"""
    # Create the Application
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("active", active_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("weekly", weekly_command))
    
    # Category quick commands
    application.add_handler(CommandHandler("health", health_command))
    application.add_handler(CommandHandler("study", study_command))
    application.add_handler(CommandHandler("work", work_command))
    application.add_handler(CommandHandler("ideas", ideas_command))
    application.add_handler(CommandHandler("shopping", shopping_command))
    
    # Habits (recurring tasks)
    application.add_handler(CommandHandler("habits", habits_command))
    
    # Focus Mode (must be before generic text handler)
    application.add_handler(focus_handler)
    
    # Pagination callback handlers for /active and category views
    application.add_handler(CallbackQueryHandler(handle_active_pagination, pattern="^active_page_|^noop$"))
    application.add_handler(CallbackQueryHandler(handle_category_pagination, pattern="^cat_"))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    # Schedule daily nudge at 10:00 AM (user's local time)
    job_queue = application.job_queue
    if job_queue:
        from datetime import time as dt_time
        # Schedule for 10:00 AM daily (adjust timezone as needed)
        job_queue.run_daily(
            daily_nudge_callback,
            time=dt_time(hour=10, minute=0),
            name="daily_nudge"
        )
        logger.info("Scheduled daily nudge for 10:00 AM")
        
        # Morning habit reminder at 8 AM (Iraq time = UTC+3)
        job_queue.run_daily(
            morning_habits_callback,
            time=dt_time(hour=5, minute=0),  # 5 AM UTC = 8 AM Iraq
            name="morning_habits"
        )
        logger.info("Scheduled morning habits reminder for 8:00 AM Iraq time")
        
        # Evening habit reminder at 8 PM (Iraq time = UTC+3)
        job_queue.run_daily(
            evening_habits_callback,
            time=dt_time(hour=17, minute=0),  # 5 PM UTC = 8 PM Iraq
            name="evening_habits"
        )
        logger.info("Scheduled evening habits reminder for 8:00 PM Iraq time")
    
    # Start the Bot
    logger.info("Starting Life Organizer Bot...")
    
    # Check if we're running on Railway (webhook mode) or locally (polling mode)
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    port = int(os.getenv("PORT", 8443))
    
    if railway_domain:
        # Production: Use webhook mode for Railway
        webhook_url = f"https://{railway_domain}"
        logger.info(f"Running in WEBHOOK mode on port {port}")
        logger.info(f"Webhook URL: {webhook_url}")
        
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url,
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        # Local development: Use polling mode
        logger.info("Running in POLLING mode (local development)")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
