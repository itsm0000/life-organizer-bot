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
import asyncio

# Import our modules
from ai_categorizer import categorize_message, analyze_image
from notion_integration import add_to_life_areas, add_to_brain_dump, log_progress, get_active_items

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


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
        "/help - This message",
        parse_mode="Markdown"
    )


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


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    text = update.message.text
    user = update.effective_user
    
    logger.info(f"Received text from {user.first_name}: {text[:50]}...")
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    # Categorize with AI
    result = await categorize_message(text)
    
    # Add to Notion
    notion_id = add_to_life_areas(
        category=result["category"],
        title=result["title"],
        item_type=result["type"],
        priority=result["priority"],
        notes=result["summary"]
    )
    
    if notion_id:
        response = (
            f"✅ Got it! Added to *{result['category']}*\n\n"
            f"📌 {result['title']}\n"
            f"🎯 Priority: {result['priority']}\n"
        )
        if result.get("suggested_action"):
            response += f"\n💡 Suggestion: {result['suggested_action']}"
        
        await update.message.reply_text(response, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "⚠️ Something went wrong. Added to Brain Dump for manual processing."
        )
        add_to_brain_dump(text[:100], text, "Text")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages"""
    photo = update.message.photo[-1]  # Get highest resolution
    caption = update.message.caption or ""
    user = update.effective_user
    
    logger.info(f"Received photo from {user.first_name}")
    
    await update.message.reply_text("📸 Analyzing image...")
    
    # Download photo
    file = await context.bot.get_file(photo.file_id)
    file_url = file.file_path
    
    # Analyze with AI
    try:
        # For now, use caption + image URL
        # In production, you'd download and send image bytes to Gemini
        result = await categorize_message(
            f"Image: {caption}" if caption else "Image received",
            has_image=True
        )
        
        # Add to Notion
        notion_id = add_to_life_areas(
            category=result["category"],
            title=result["title"],
            item_type=result["type"],
            priority=result["priority"],
            notes=result["summary"],
            image_url=file_url
        )
        
        if notion_id:
            await update.message.reply_text(
                f"✅ Image saved to *{result['category']}*\n"
                f"📌 {result['title']}",
                parse_mode="Markdown"
            )
        else:
            add_to_brain_dump(caption or "Image", caption, "Image", file_url)
            await update.message.reply_text("⚠️ Added to Brain Dump for review")
    
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        add_to_brain_dump(caption or "Image", caption, "Image", file_url)
        await update.message.reply_text("⚠️ Error processing image. Saved to Brain Dump.")


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


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages"""
    voice = update.message.voice
    
    logger.info("Received voice message")
    
    await update.message.reply_text(
        "🎤 Voice note received!\n\n"
        "Voice transcription coming soon. For now, saved to Brain Dump."
    )
    
    file = await context.bot.get_file(voice.file_id)
    file_url = file.file_path
    
    add_to_brain_dump("Voice note", "Voice message", "Voice", file_url)


def main():
    """Start the bot"""
    # Create the Application
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("active", active_command))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    # Start the Bot
    logger.info("Starting Life Organizer Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
