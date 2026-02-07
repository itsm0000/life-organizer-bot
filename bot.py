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
from ai_categorizer import categorize_message, analyze_image, parse_management_intent
from notion_integration import (
    add_to_life_areas, add_to_brain_dump, log_progress, get_active_items,
    search_items, update_item, delete_item, get_items_by_category, format_item_for_display
)
from voice_transcriber import transcribe_voice

# Store pending delete confirmations {user_id: page_id}
pending_deletes = {}

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
    
    # For delete, complete, update - need to search for the item
    if not target:
        await update.message.reply_text("❓ Which item? Please be more specific.")
        return
    
    items = search_items(target)
    
    if not items:
        await update.message.reply_text(f"🔍 Couldn't find any item matching '{target}'.")
        return
    
    if len(items) > 1:
        # Multiple matches - show options
        response = f"🔍 Found {len(items)} items matching '{target}':\n\n"
        for i, item in enumerate(items[:5], 1):
            response += f"{i}. {format_item_for_display(item)}\n"
        response += "\nPlease be more specific."
        await update.message.reply_text(response)
        return
    
    # Single match found
    item = items[0]
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
        
        # Now categorize the transcribed text
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
