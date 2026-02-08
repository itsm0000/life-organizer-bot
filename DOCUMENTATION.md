# Life Organizer Bot - Complete Documentation

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Build Journey & Obstacles](#build-journey--obstacles)
- [Task Management Feature (NEW)](#task-management-feature-new)
- [Setup Guide](#setup-guide)
- [Environment Variables](#environment-variables)
- [Future Improvements](#future-improvements)
- [Troubleshooting](#troubleshooting)
- [Version History](#version-history)

---

## Overview

The **Life Organizer Bot** is an ADHD-friendly Telegram bot that helps organize life by automatically categorizing and storing messages into Notion. Built for people who need a zero-friction way to capture thoughts, tasks, and ideas without the mental overhead of manual organization.

### The Problem It Solves
People with ADHD often struggle with:
- Remembering to write things down
- Deciding where to categorize items
- Maintaining organization systems

This bot removes all friction: just dump your thoughts via Telegram, and AI handles the rest.

### How It Works
1. **User sends a message** to the Telegram bot (text, photo, document, or voice)
2. **AI categorizes** the message using Groq's Llama 3.3 70B model
3. **Notion stores** the item in the appropriate database with metadata
4. **Bot responds** with confirmation, category, priority, and suggestions

---

## Features

### Core Features

| Feature | Status | Description |
|---------|--------|-------------|
| Text Messages | ✅ Working | AI-categorized and stored in Notion Life Areas |
| Arabic Support | ✅ Working | Full Arabic language understanding |
| Photo Messages | ✅ Working | Analyzed with Llama 4 Scout Vision AI |
| Documents/PDFs | ✅ Working | Saved to Brain Dump for review |
| Voice Notes | ✅ Working | Transcribed with Groq Whisper, then AI-categorized |
| AI Suggestions | ✅ Working | Contextual action suggestions for each item |
| Task Management | ✅ Working | Modify/delete existing tasks via chat |

### v2.0 Features (Added February 2026)

| Feature | Command | Description |
|---------|---------|-------------|
| 🛡️ Security | - | User whitelist + Rate limiting |
| 🧘 Focus Mode | `/focus` | ADHD-friendly single-task mode |
| 📊 XP/Levels | `/stats` | Gamification with streak tracking |
| 📅 Weekly Review | `/weekly` | Progress summary + category breakdown |
| 🏃 Category Views | `/health`, `/study`, etc. | Quick access to specific categories |
| 👋 Smart Nudges | Auto (10 AM) | Daily reminder about high-priority tasks |
| 🔁 Habits System | `/habits` | Recurring tasks with scheduled reminders |
| ⏰ Morning/Evening Reminders | Auto (8AM/8PM) | Habit reminders at key times |

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `/start` | Introduction and welcome message |
| `/help` | List of all commands |
| `/active` | View all active tasks |
| `/focus` | Enter Focus Mode - pick ONE task to work on |
| `/stats` | View your XP, level, and daily streak |
| `/weekly` | Weekly progress review |
| `/habits` | 🔁 View recurring habits and completion status |
| `/health` | 🏃 View Health category tasks |
| `/study` | 📚 View Study category tasks |
| `/work` | 💼 View Work category tasks |
| `/ideas` | 💡 View Ideas |
| `/shopping` | 🛒 View Shopping list |

---

## Security Features

### User Whitelist
Only whitelisted Telegram users can interact with the bot.

**Configuration:**
```env
ALLOWED_USER_IDS=123456789,987654321
```

- Comma-separated list of Telegram user IDs
- If empty, bot is open to everyone (not recommended)
- Unauthorized users are silently ignored

### Rate Limiting
Prevents spam and abuse.

- **Limit:** 20 requests per minute per user
- **Response:** "⏳ Too many requests. Please wait a moment."

---

## Gamification System

### XP Rewards

| Action | XP Earned |
|--------|-----------|
| Add a task | +5 XP |
| Complete via Focus Mode | +25 XP |
| 7-day streak bonus | +50 XP |

### Levels

| Level | Title | XP Required |
|-------|-------|-------------|
| 1 | 🌱 Seedling | 0 |
| 2 | 🌿 Sprout | 50 |
| 3 | 🌳 Sapling | 150 |
| 4 | 🌲 Tree | 350 |
| 5 | 🏔️ Mountain | 600 |
| 6 | ⭐ Star | 1000 |
| 7 | 🌟 Superstar | 2000 |
| 8 | 🚀 Legend | 5000 |

### Streaks
- Daily streak increments when you use the bot on consecutive days
- Streak resets if you miss a day
- 7-day streak bonus: +50 XP

---

## Focus Mode

ADHD-friendly feature to help concentrate on one task at a time.

### How it works:
1. Send `/focus`
2. Bot shows top 5 high/medium priority tasks
3. Tap to select ONE task
4. Bot enters Focus Mode - reminds you to stay on task
5. Say "done" (or "تم" in Arabic) when finished
6. Task is marked complete in Notion + you earn +25 XP

### Focus Mode Keywords:
- English: `done`, `finished`, `complete`
- Arabic: `تم`, `خلص`
- Cancel: `/cancel`

---

## Smart Nudges

Automatic daily reminder about your high-priority tasks.

- **Time:** 10:00 AM (server time)
- **Recipients:** All whitelisted users
- **Content:** Highlights a random high-priority task
- **Purpose:** Gentle reminder to stay productive

### Message Types

#### Text Messages
- Full AI categorization with Llama 3.3 70B
- Detects category, priority, and type (Task/Reference/Goal)
- Provides actionable suggestions
- Supports both English and Arabic

#### Photo/Image Messages
- **Vision AI Analysis**: Llama 4 Scout describes what's in the image
- Automatically recognizes products, documents, receipts, screenshots
- Categorizes based on image content (e.g., vitamins → Health)
- Images are resized and compressed before analysis (max 1024px, JPEG quality 80%)
- Caption is used for additional context if provided

#### Voice Notes
- **Transcription**: Groq Whisper converts speech to text
- Text is then passed through management intent detection
- If user is modifying a task, it handles that
- Otherwise categorizes as new item
- Supports Arabic and English voice messages

#### Documents/PDFs
- Saved to Brain Dump database for manual review
- Document URL stored for easy access
- Marked as "Unprocessed" for later triage

### Categories
- **Health**: fitness, nutrition, skincare, sleep, medical, supplements
- **Study**: university courses, exams, assignments, learning
- **Personal Projects**: coding, side businesses, entrepreneurship
- **Skills**: learning instruments, chess, cooking, drawing, languages
- **Creative**: content creation, streaming, video editing, art
- **Shopping**: things to buy, product research, wishlist items
- **Ideas**: random thoughts, future possibilities, brainstorming

### Priority Levels
- **High**: university deadlines, health issues, urgent tasks (🔴)
- **Medium**: personal projects, skill development, regular tasks (🟡)
- **Low**: ideas, shopping, exploration, nice-to-have (🟢)

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Telegram      │────▶│   Railway       │────▶│   Notion        │
│   (User Input)  │     │   (Bot Host)    │     │   (Storage)     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Groq API      │
                        │   - Llama 3.3   │
                        │   - Llama 4     │
                        │   - Whisper     │
                        └─────────────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Bot Framework | python-telegram-bot 20.7+ | Handle Telegram messages |
| Hosting | Railway | Cloud deployment with webhooks |
| Text AI | Groq (Llama 3.3 70B) | Message categorization |
| Vision AI | Groq (Llama 4 Scout 17B) | Image analysis |
| Speech-to-Text | Groq (Whisper Large V3 Turbo) | Voice transcription |
| Task Matching | Groq (Llama 3.3 70B) | Semantic task matching |
| Storage | Notion API | Database for organized items |

### File Structure
```
life-organizer-bot/
├── bot.py                  # Main bot - handles Telegram messages
├── ai_categorizer.py       # AI: categorization, vision, intent parsing, task matching
├── voice_transcriber.py    # Groq Whisper for voice transcription
├── notion_integration.py   # Notion API: CRUD operations
├── setup_notion.py         # Database property setup script
├── clear_webhook.py        # Utility to clear Telegram webhooks
├── requirements.txt        # Python dependencies
├── railway.toml            # Railway deployment config
├── .env                    # Local environment variables
├── .env.example            # Environment template
├── DOCUMENTATION.md        # This file
└── README.md               # Quick start guide
```

---

## Build Journey & Obstacles

This project was built on **February 6-7, 2026** with significant debugging. Here's every obstacle we encountered:

### Obstacle 1: Railway Deployment - Polling Mode Failure
**Problem:** The bot used `run_polling()` which works locally but fails on Railway.

**Error:** `telegram.error.Conflict: terminated by other getUpdates request`

**Solution:** Converted to webhook mode:
```python
if os.getenv("RAILWAY_PUBLIC_DOMAIN"):
    application.run_webhook(listen="0.0.0.0", port=PORT, webhook_url=URL)
else:
    application.run_polling()
```
**Effective:** ✅ Yes

---

### Obstacle 2: Missing Webhook Dependencies
**Problem:** Webhook mode requires additional packages.

**Error:** `RuntimeError: To use start_webhook, PTB must be installed via pip install "python-telegram-bot[webhooks]"`

**Solution:** Updated `requirements.txt`:
```
python-telegram-bot[webhooks]>=20.7
```
**Effective:** ✅ Yes

---

### Obstacle 3: Gemini API Quota Exhausted
**Problem:** Free tier quota for `gemini-2.0-flash-lite` was used up.

**Error:** `429 RESOURCE_EXHAUSTED - You exceeded your current quota`

**Solution:** Switched to **Groq** - completely free with 30 requests/minute.

**Effective:** ✅ Yes

---

### Obstacle 4: Groq Text Model Decommissioned
**Problem:** The initial Groq model was deprecated.

**Error:** `The model llama-3.1-70b-versatile has been decommissioned`

**Solution:** Updated to `llama-3.3-70b-versatile`

**Effective:** ✅ Yes

---

### Obstacle 5: Wrong Notion Database IDs
**Problem:** User copied VIEW IDs instead of DATABASE IDs from Notion URLs.

**URL Structure:**
```
https://www.notion.so/DATABASE_ID?v=VIEW_ID
                      ↑ Need this    ↑ Not this!
```

**Solution:** Extracted correct IDs from before the `?v=` parameter.

**Effective:** ✅ Yes

---

### Obstacle 6: Notion Integration Token Mismatch
**Problem:** Integration was deleted and recreated, but old token was still in use.

**Error:** `401 Unauthorized - API token is invalid`

**Solution:** Created new integration, updated NOTION_TOKEN, connected to all databases.

**Effective:** ✅ Yes

---

### Obstacle 7: Missing Database Properties
**Problem:** Notion databases had no properties (just empty tables).

**Error:** `400 Bad Request - Category is not a property that exists`

**Solution:** Created `setup_notion.py` script that adds all required properties.

**Effective:** ✅ Yes

---

### Obstacle 8: Notion Workspace Confusion
**Problem:** Integration showed as connected but API said "not found".

**Root Cause:** "Mo's Notion" (workspace) vs "Mo's Notion HQ" (page name) confusion.

**Solution:** Verified the integration workspace matched where databases lived.

**Effective:** ✅ Yes

---

### Obstacle 9: Groq Vision Model Size Limit
**Problem:** Groq has a 4MB limit for base64-encoded images.

**Error:** `400 Bad Request - Request too large`

**Solution:** Added PIL image compression (resize to max 1024px, JPEG quality 80%).

**Effective:** ✅ Yes

---

### Obstacle 10: Groq Vision Models Decommissioned
**Problem:** On April 14, 2025, Groq deprecated all Llama 3.2 Vision models.

**Error:** `The model llama-3.2-11b-vision-preview has been decommissioned`

**Attempted:**
1. `llama-3.2-90b-vision-preview` - ❌ Also decommissioned
2. `llama-3.2-11b-vision-preview` - ❌ Also decommissioned

**Final Solution:** Switched to `meta-llama/llama-4-scout-17b-16e-instruct`

**Effective:** ✅ Yes

---

### Obstacle 11: Vision Response JSON Parsing
**Problem:** Llama 4 Scout returns JSON wrapped in markdown code blocks.

**Error:** `json.JSONDecodeError`

**Solution:** Added code to strip markdown fences and extract JSON:
```python
if content.startswith("```"):
    lines = content.split("\n")
    lines = lines[1:-1]
    content = "\n".join(lines)
```

**Effective:** ✅ Yes

---

### Obstacle 12: Voice Notes Not Detecting Management Commands
**Problem:** Voice notes were always creating new tasks, never updating existing ones.

**Root Cause:** `handle_voice()` was directly categorizing transcribed text without checking for management intent first.

**Solution:** Added management intent check after transcription in `handle_voice()`:
```python
intent = await parse_management_intent(transcription)
if intent.get("intent") != "none":
    await handle_management_command(update, intent, user.id)
    return
```

**Effective:** ✅ Yes (intent detection works)

---

### Obstacle 13: Task Search Not Finding Items (FIXED)
**Problem:** `notion-client` threw `AttributeError: 'DatabasesEndpoint' object has no attribute 'query'` when trying to search.
**Root Cause:** In the installed environment (v2.7.0 and v2.2.1), the `query` method was inexplicably missing from `notion.databases`, despite being in the official documentation.
**Solution:** Replaced all `notion.databases.query(...)` calls with the raw API request method:
```python
notion.request(path=f"databases/{db_id}/query", method="POST", body={...})
```
**Effective:** ✅ Yes - validated with `inspect_notion.py` script.

### Obstacle 14: Restrictive Status Filtering
**Problem:** "Skincare Routine" wasn't found because it wasn't strictly "Active" or the filter was too rigid.
**Solution:** Removed the API-level `Status="Active"` filter. Now fetching ALL items and filtering in Python with robust logging.
**Effective:** ✅ Yes

---

## Task Management Feature (NEW)

### Overview
This feature allows users to modify existing Notion entries via natural language in Telegram.

### Supported Commands

| Command Type | Example | Status |
|--------------|---------|--------|
| Query | "What tasks do I have?" | ✅ Working |
| Query Category | "Show my Health items" | ✅ Working |
| Update Priority | "Make Java high priority" | 🔄 In Progress |
| Mark Complete | "Mark gym as done" | 🔄 In Progress |
| Delete | "Delete the skincare task" | 🔄 In Progress |

### How It Works

1. **Intent Detection**: AI determines if message is add/modify command
   - Function: `parse_management_intent()` in `ai_categorizer.py`
   - Returns: `{intent, target, category, new_priority}`

2. **Task Matching**: AI finds which task user is referring to
   - Function: `ai_match_task()` in `ai_categorizer.py`
   - Sends list of all active tasks to LLM
   - LLM picks the best semantic match

3. **Action Execution**: Bot performs the action
   - Functions in `notion_integration.py`: `update_item()`, `delete_item()`
   - Delete requires confirmation (user must reply "YES")

### Known Issues

**Issue: Task not found even when it exists**
- Root cause: Possibly filter on Status="Active" not matching items
- Items might have different Status values or none at all

---

## Setup Guide

### Prerequisites
- Python 3.9+
- Telegram account
- Notion account (free tier works)
- Groq account (free at console.groq.com)

### Step 1: Clone Repository
```bash
git clone https://github.com/itsm0000/life-organizer-bot.git
cd life-organizer-bot
pip install -r requirements.txt
```

### Step 2: Create Telegram Bot
1. Message @BotFather on Telegram
2. Send `/newbot` and follow prompts
3. Copy the bot token

### Step 3: Create Notion Integration
1. Go to https://www.notion.so/my-integrations
2. Create new integration
3. Copy the Internal Integration Secret

### Step 4: Create Notion Databases
1. Create a page in Notion called "Life Organizer"
2. Create 3 databases: Life Areas, Brain Dump Inbox, Progress Log
3. Connect your integration to each database (⋯ → Connections)
4. Copy each database ID from URL (before `?v=`)

### Step 5: Get Groq API Key
1. Go to https://console.groq.com/keys
2. Create API key
3. Copy the key

### Step 6: Configure Environment
Create `.env` file:
```env
TELEGRAM_BOT_TOKEN=your_token
NOTION_TOKEN=your_notion_secret
GROQ_API_KEY=your_groq_key
LIFE_AREAS_DB_ID=your_db_id
BRAIN_DUMP_DB_ID=your_db_id
PROGRESS_DB_ID=your_db_id
```

### Step 7: Setup Database Properties
```bash
python setup_notion.py
```

### Step 8: Run Locally
```bash
python bot.py
```

### Step 9: Deploy to Railway
1. Push to GitHub
2. Connect repo to Railway
3. Add all environment variables + `RAILWAY_PUBLIC_DOMAIN`
4. Generate public domain in Railway settings

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Token from @BotFather |
| `NOTION_TOKEN` | Yes | Notion integration secret |
| `GROQ_API_KEY` | Yes | Groq API key (free) |
| `LIFE_AREAS_DB_ID` | Yes | Notion database ID |
| `BRAIN_DUMP_DB_ID` | Yes | Notion database ID |
| `PROGRESS_DB_ID` | Yes | Notion database ID |
| `HABITS_DB_ID` | Yes | Notion Habits database ID |
| `RAILWAY_PUBLIC_DOMAIN` | Railway only | Enables webhook mode |
| `PORT` | Railway only | Auto-set by Railway |

---

## Future Improvements

### 1. Fix Task Search (HIGH PRIORITY)
**Problem:** AI can't find tasks when user wants to modify them.
**Proposed Solution:**
- Remove Status="Active" filter from `get_active_items()` temporarily
- Add logging to see what items are being returned
- Verify all items have consistent Status values
**Implementation:** Modify `notion_integration.py` line 94-98

---

### 2. PDF Text Extraction
**Status:** Planned
**Technology:** PyMuPDF library
**Benefit:** Extract text from PDFs for AI analysis
**Implementation:**
```python
# In bot.py handle_document()
import fitz  # PyMuPDF
doc = fitz.open(stream=pdf_bytes, filetype="pdf")
text = ""
for page in doc:
    text += page.get_text()
# Then categorize the extracted text
```

---

### 3. Weekly Summary Reports
**Status:** Planned
**Benefit:** "What did I accomplish this week?"
**Implementation:**
- Add `/weekly` command
- Query Notion for items from last 7 days
- Use AI to summarize accomplishments
- Send as formatted Telegram message

---

### 4. Progress Analytics
**Status:** Planned
**Benefit:** Charts showing time spent per category
**Implementation:**
- Use `matplotlib` to generate charts
- Track when items are completed
- Send chart as image to Telegram

---

### 5. Custom Categories
**Status:** Planned
**Benefit:** Let users add their own categories
**Implementation:**
- Store user preferences in a JSON file or Notion page
- Update AI prompt with user's custom categories
- Persist across sessions

---

### 6. Reminders for High-Priority Items
**Status:** Planned
**Benefit:** "You have 3 High priority items pending!"
**Implementation:**
- Use `python-telegram-bot` JobQueue for scheduling
- Check for High priority items every morning
- Send Telegram notification

---

### 7. Multi-User Support
**Status:** Planned  
**Benefit:** Multiple users can each have their own Notion workspace
**Implementation:**
- Store user_id → notion_token mapping
- Each user runs `/setup` to link their Notion
- Isolate databases per user

---

### 11. Multilingual Support (Arabic & English)
The bot now intelligently handles bilingual input:
- **Arabic Input:** Preserves the original Arabic text for titles, summaries, and notes.
- **English Input:** Preserves English text.
- **Unified Organization:** Categories, Priorities, and Types remain in English (e.g., "Health", "Study") regardless of input language, ensuring consistent sorting and filtering in Notion.

---

## Troubleshooting

### Bot not responding?
1. Check Railway logs for errors
2. Verify webhook is set: `python clear_webhook.py`
3. Ensure RAILWAY_PUBLIC_DOMAIN is set

### Notion 404 errors?
1. Verify database IDs (from URL before `?v=`)
2. Check integration is connected to databases
3. Confirm NOTION_TOKEN is correct

### AI categorization failing?
1. Check GROQ_API_KEY is set
2. Verify Groq account is active
3. Check model name is current (`llama-3.3-70b-versatile`)

### Vision/Photo analysis failing?
1. Check Groq API key is valid
2. Ensure model is `meta-llama/llama-4-scout-17b-16e-instruct`
3. Check Railway logs for specific error messages

### Voice notes not transcribing?
1. Verify GROQ_API_KEY is set
2. Check Whisper model: `whisper-large-v3-turbo`
3. Voice file must be under 25MB

### Task management not finding items?
1. Check if items have Status="Active" in Notion (Bot now searches ALL non-archived items)
2. Run `/active` command to see what bot can see
3. Check Railway logs for search results (Enhanced logging added v1.1.1)
   - Look for "Item found:" logs to see what Notion returned
   - Look for "Returning X active items" to see what survived filtering

---

## Version History

### v1.0.0 (February 7, 2026)
**Initial Stable Release - Git Tag: `v1.0.0-stable`**

Features:
- ✅ Text message categorization (Llama 3.3 70B)
- ✅ Photo/Image analysis (Llama 4 Scout Vision)
- ✅ Voice note transcription (Whisper Large V3 Turbo)
- ✅ Document/PDF storage to Brain Dump
- ✅ Full Arabic language support
- ✅ Notion 3-database integration
- ✅ Railway webhook deployment

---

### v1.1.0-wip (February 7, 2026)
**Task Management - Work in Progress - Git Tag: `v1.1.0-task-management-wip`**

Added:
- Task management via chat (query, delete, update, complete)
- AI-powered intent detection
- AI-powered semantic task matching
- Voice notes support management commands
- Multi-strategy task search

Known Issues:
- Task search not reliably finding items
- May need to debug Status filter or item properties

---

### v2.0.0 (February 8, 2026)
**Major Update - Branch: `refactor/v2` | Tag: `v1.1.0-stable` (rollback point)**

Security:
- User whitelist (`ALLOWED_USER_IDS`)
- Rate limiting (20 req/min)
- Silent ignore for unauthorized users

ADHD Features:
- Focus Mode (`/focus`) - Single-task concentration mode
- Smart Nudges - Daily 10 AM reminder for high-priority tasks

Gamification:
- XP system (+5 add, +25 complete, +50 streak bonus)
- 8 levels: Seedling → Legend
- Daily streak tracking
- `/stats` command with progress bar

New Commands:
- `/stats` - XP, level, streak
- `/weekly` - Weekly progress review
- `/focus` - Focus Mode
- `/health`, `/study`, `/work`, `/ideas`, `/shopping` - Category quick views

Dependencies:
- Added `python-telegram-bot[job-queue]` for scheduled reminders

---

### v2.1.0 (February 8, 2026)
**Habits System - Branch: `refactor/v2`**

Habits (Recurring Tasks):
- New Notion database: Habits
- `/habits` command - View all habits with ✅/⏳ status
- Natural language habit creation: "Add a skincare habit twice daily"
- Natural language habit completion: "skincare done"
- Works via both text and voice messages
- XP rewards for habit completion
- Progress logging for habits

Scheduled Reminders:
- 🌅 8:00 AM (Iraq time) - Morning habits reminder
- 🌙 8:00 PM (Iraq time) - Evening habits check-in

Fixes:
- Progress Log now records completed tasks (was never called)
- Task completion awards +25 XP
- Notion pages get category-based icons and covers

New Files:
- `habits.py` - Habit CRUD operations
- `setup_habits_db.py` - Creates Habits database in Notion
- `migrate_visuals.py` - Adds icons/covers to existing pages

---

## Credits

Built with:
- [python-telegram-bot](https://python-telegram-bot.org/)
- [Groq](https://groq.com/) - Free AI inference
- [Notion API](https://developers.notion.com/)
- [Railway](https://railway.app/) - Free cloud hosting
- [Pillow](https://pillow.readthedocs.io/) - Image processing

---

## License

MIT License - Use freely!

---

## Habits System

### Overview
Recurring tasks that remind you daily/weekly and reward XP when completed.

### Habits Database Properties
| Property | Type | Description |
|----------|------|-------------|
| Name | Title | Habit name |
| Frequency | Select | Daily, Twice Daily, Weekly, Monthly |
| Times | Multi-select | Morning, Evening, Afternoon |
| Category | Select | Health, Study, Work, Personal, Skills |
| XP Reward | Number | Points earned per completion (default: 25) |
| Active | Checkbox | Enable/disable the habit |
| Last Completed | Date | Tracks most recent completion |

### Natural Language Examples

**Creating habits:**
- "Add a skincare routine habit, twice daily, morning and evening"
- "Create a daily workout habit"
- "Add a weekly meal prep habit"

**Completing habits:**
- "skincare done"
- "finished workout"
- "completed my study session"

### Scheduled Reminders
| Time (Iraq) | Purpose |
|-------------|----------|
| 8:00 AM | Morning habits list with potential XP |
| 8:00 PM | Evening check-in with pending habits |

---

*Last updated: February 8, 2026 - v2.1.0*
