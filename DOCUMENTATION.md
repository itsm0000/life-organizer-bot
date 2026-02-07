# Life Organizer Bot - Complete Documentation

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Build Journey & Obstacles](#build-journey--obstacles)
- [Setup Guide](#setup-guide)
- [Environment Variables](#environment-variables)
- [Future Improvements](#future-improvements)
- [Troubleshooting](#troubleshooting)

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

| Feature | Status | Description |
|---------|--------|-------------|
| Text Messages | ✅ Working | AI-categorized and stored in Notion Life Areas |
| Arabic Support | ✅ Working | Full Arabic language understanding |
| Photo Messages | ✅ Working | Analyzed with Llama 4 Scout Vision AI (sees what's in the image!) |
| Documents/PDFs | ✅ Working | Saved to Brain Dump for review |
| Voice Notes | ✅ Working | Transcribed with Groq Whisper, then AI-categorized |
| AI Suggestions | ✅ Working | Contextual action suggestions for each item |

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
- Text is then passed to AI categorizer
- Supports Arabic and English voice messages
- Transcribed content stored in notes

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

### Item Types
- **Task**: Actionable items with deadlines
- **Goal**: Long-term objectives
- **Reference**: Information to remember
- **Resource**: Files, images, documents

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
                        │   (AI/LLM)      │
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
| Storage | Notion API | Database for organized items |

### File Structure
```
life-organizer-bot/
├── bot.py                  # Main bot - handles Telegram messages
├── ai_categorizer.py       # Groq integration for AI categorization + vision
├── voice_transcriber.py    # Groq Whisper for voice transcription
├── notion_integration.py   # Notion API handlers
├── setup_notion.py         # Database property setup script
├── clear_webhook.py        # Utility to clear Telegram webhooks
├── requirements.txt        # Python dependencies
├── railway.toml            # Railway deployment config
├── .env                    # Local environment variables
├── .env.example            # Environment template
├── DOCUMENTATION.md        # This file
└── README.md               # Quick start guide
```

### Dependencies (requirements.txt)
```
python-telegram-bot[webhooks]>=20.7
notion-client>=2.2.1
python-dotenv>=1.0.0
Pillow>=10.4.0
requests>=2.31.0
httpx>=0.25.0
```

---

## Build Journey & Obstacles

This project was built on **February 6-7, 2026** with significant debugging along the way. Here's the complete journey with all obstacles encountered and their solutions:

### Obstacle 1: Railway Deployment - Polling Mode Failure
**Problem:** The bot used `run_polling()` which works locally but fails on Railway because:
- Railway expects apps to listen on a PORT
- Polling connections are unstable on cloud platforms
- Railway may sleep idle containers

**Error:** `telegram.error.Conflict: terminated by other getUpdates request`

**Solution:** Converted to webhook mode:
```python
if os.getenv("RAILWAY_PUBLIC_DOMAIN"):
    application.run_webhook(listen="0.0.0.0", port=PORT, webhook_url=URL)
else:
    application.run_polling()  # Local dev fallback
```

**Effective:** ✅ Yes - Bot now works perfectly on Railway

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

**Solution:** Switched from Gemini to **Groq** which offers:
- Completely free API
- 30 requests per minute
- Llama 3.3 70B model (excellent for categorization)

**Effective:** ✅ Yes - Groq free tier has been more than sufficient

---

### Obstacle 4: Groq Text Model Decommissioned
**Problem:** The initial Groq model was deprecated.

**Error:** `The model llama-3.1-70b-versatile has been decommissioned`

**Solution:** Updated to latest model:
```python
"model": "llama-3.3-70b-versatile"  # Current supported version
```

**Effective:** ✅ Yes

---

### Obstacle 5: Wrong Notion Database IDs
**Problem:** User copied VIEW IDs instead of DATABASE IDs from Notion URLs.

**URL Structure:**
```
https://www.notion.so/DATABASE_ID?v=VIEW_ID
                      ↑ Need this    ↑ Not this!
```

**Error:** `404 Not Found - Could not find database with ID`

**Solution:** Extracted correct IDs from before the `?v=` parameter.

**Effective:** ✅ Yes

---

### Obstacle 6: Notion Integration Token Mismatch
**Problem:** Integration was deleted and recreated, but old token was still in use.

**Error:** `401 Unauthorized - API token is invalid`

**Solution:** 
1. Created new integration in correct workspace
2. Updated NOTION_TOKEN in Railway
3. Connected integration to all databases

**Effective:** ✅ Yes

---

### Obstacle 7: Missing Database Properties
**Problem:** Notion databases had no properties (just empty tables).

**Error:** `400 Bad Request - Category is not a property that exists`

**Solution:** Created `setup_notion.py` script that adds all required properties:
- Life Areas: Name, Category, Type, Status, Priority, Date Added, Notes, Image
- Brain Dump: Name, Content, Processed, Date, Type, Files
- Progress Log: Name, Category, Date, Duration, Notes

**Effective:** ✅ Yes

---

### Obstacle 8: Notion Workspace Confusion
**Problem:** Integration was showing as connected but API said "not found". 

**Root Cause:** "Mo's Notion" (workspace) vs "Mo's Notion HQ" (page name) confusion.

**Solution:** Verified the integration workspace matched where databases lived.

**Effective:** ✅ Yes

---

### Obstacle 9: Groq Vision Model Size Limit (NEW)
**Problem:** Groq has a 4MB limit for base64-encoded images. Telegram photos often exceeded this.

**Error:** `400 Bad Request - Request too large`

**Solution:** Added image compression using PIL:
```python
from PIL import Image
# Resize to max 1024px
# Compress to JPEG quality 80%
# Reduces 600KB+ images to ~150KB
```

**Effective:** ✅ Yes - All images now process successfully

---

### Obstacle 10: Groq Vision Models Decommissioned (NEW)
**Problem:** On April 14, 2025, Groq deprecated all Llama 3.2 Vision models.

**Error:** `The model llama-3.2-11b-vision-preview has been decommissioned and is no longer supported`

**Attempted Solutions:**
1. First tried `llama-3.2-90b-vision-preview` - ❌ Also decommissioned
2. Then tried `llama-3.2-11b-vision-preview` - ❌ Also decommissioned

**Final Solution:** Switched to Llama 4 Scout (the official replacement):
```python
"model": "meta-llama/llama-4-scout-17b-16e-instruct"
```

**Effective:** ✅ Yes - Vision now works perfectly with Llama 4 Scout

---

### Obstacle 11: Vision Response JSON Parsing (NEW)
**Problem:** Llama 4 Scout returns JSON wrapped in markdown code blocks.

**Error:** `json.JSONDecodeError` - couldn't parse response

**Response looked like:**
```
Here is the analysis:
\`\`\`json
{"description": "...", "category": "..."}
\`\`\`
```

**Solution:** Added code to strip markdown fences and extract JSON:
```python
if content.startswith("```"):
    lines = content.split("\n")
    lines = lines[1:-1]  # Remove fence lines
    content = "\n".join(lines)
```

**Effective:** ✅ Yes - Vision responses now parse correctly

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
| `RAILWAY_PUBLIC_DOMAIN` | Railway only | Enables webhook mode |
| `PORT` | Railway only | Auto-set by Railway |

---

## Future Improvements

### Task Management via Chat (NEXT UP!)
**Status:** Planned
**Benefit:** Say "delete the skincare task" or "change priority of Java study to high" and bot will update/delete Notion entries

### PDF Text Extraction
**Status:** Planned  
**Technology:** PyMuPDF library  
**Benefit:** Extract text from PDFs for AI analysis

### Weekly Summary Reports
**Status:** Planned  
**Benefit:** Automated summary of what you worked on

### Progress Analytics
**Status:** Planned  
**Benefit:** Charts showing time spent per category

### Custom Categories
**Status:** Planned  
**Benefit:** User-defined categories beyond defaults

### Reminders for High-Priority Items
**Status:** Planned  
**Benefit:** Telegram reminders for urgent items

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

### Items not appearing in Notion?
1. Run `python setup_notion.py` to add properties
2. Check database has required columns
3. Verify integration has write access

---

## Version History

### v1.0.0 (February 7, 2026)
**Initial Stable Release**

Features:
- ✅ Text message categorization (Llama 3.3 70B)
- ✅ Photo/Image analysis (Llama 4 Scout Vision)
- ✅ Voice note transcription (Whisper Large V3 Turbo)
- ✅ Document/PDF storage to Brain Dump
- ✅ Full Arabic language support
- ✅ Notion integration with 3 databases
- ✅ Railway webhook deployment

Git tag: `v1.0.0-stable`

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

*Last updated: February 7, 2026 - v1.0.0*
