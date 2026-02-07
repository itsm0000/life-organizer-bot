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
from ai_categorizer import categorize_message, analyze_image, parse_management_intent, ai_match_task
from notion_integration import (
    add_to_life_areas, add_to_brain_dump, log_progress, get_active_items,
    search_items, update_item, delete_item, get_items_by_category, format_item_for_display
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
    """Show active items from Notion"""
    await update.message.reply_text("🔍 Fetching your active items...")
    
    items = get_active_items()
    
    if not items:
        await update.message.reply_text(
            "No active items yet! Start dumping your thoughts and I'll organize them."
        )
        return
    
    # Group by category
    by_category = {}
    for item in items[:10]:  # Limit to 10 most important
        props = item["properties"]
        category = props.get("Category", {}).get("select", {}).get("name", "Other")
        title = props.get("Name", {}).get("title", [{}])[0].get("plain_text", "Untitled")
        priority = props.get("Priority", {}).get("select", {}).get("name", "Medium")
        
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(f"  • {title} [{priority}]")
    
    message = "📋 *Your Active Items:*\n\n"
    for category, items_list in by_category.items():
        message += f"*{category}:*\n" + "\n".join(items_list) + "\n\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")


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
        # First, check if this is a management command
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
            await update.message.reply_text(f"✅ Marked *{title}* as Done!", parse_mode="Markdown")
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
        
        # First check if this is a management command
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
    """Complete the focused task."""
    user_id = update.effective_user.id
    text = update.message.text.lower()
    
    if text in ["done", "finished", "complete", "تم", "خلص"]:
        session = _focus_sessions.pop(user_id, None)
        if session:
            # Mark task as done in Notion
            update_item(session["page_id"], {"status": "Done"})
            
            # Award XP for completing task via Focus Mode (bonus!)
            stats = add_xp(user_id, XP_FOCUS_COMPLETED, "focus mode completion")
            level, title = get_level(stats["xp"])
            
            await update.message.reply_text(
                f"🎉 *AMAZING!*\n\n"
                f"You crushed it! ✅ *{session['task']}* is DONE!\n\n"
                f"+{XP_FOCUS_COMPLETED} XP 💫 (Level {level}: {title})\n\n"
                f"Take a breather, then /focus on the next one.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("No active focus session. Start with /focus")
        return ConversationHandler.END
    
    # User is chatting while in focus mode - gentle reminder
    session = _focus_sessions.get(user_id, {})
    task = session.get("task", "your task")
    await update.message.reply_text(
        f"🧘 Still in Focus Mode on: *{task}*\n\n"
        f"Say *done* when finished, or /cancel to exit.",
        parse_mode="Markdown"
    )
    return FOCUS_ACTIVE


async def focus_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel focus mode."""
    user_id = update.effective_user.id
    _focus_sessions.pop(user_id, None)
    await update.message.reply_text("Focus mode ended. No worries, you can try again anytime! 💪")
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
    
    # Focus Mode (must be before generic text handler)
    application.add_handler(focus_handler)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
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
