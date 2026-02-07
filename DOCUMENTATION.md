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
| Text Messages | ✅ Working | AI-categorized and stored in Notion |
| Arabic Support | ✅ Working | Full Arabic language understanding |
| Photo Messages | ✅ Working | Stored with caption-based categorization |
| Documents/PDFs | ✅ Working | Saved to Brain Dump for review |
| Voice Notes | ⚠️ Partial | Saved to Brain Dump (transcription planned) |
| AI Suggestions | ✅ Working | Contextual action suggestions |

### Categories
- **Health**: fitness, nutrition, skincare, sleep, medical
- **Study**: university courses, exams, assignments
- **Personal Projects**: coding, side businesses, entrepreneurship
- **Skills**: learning instruments, chess, cooking, drawing
- **Creative**: content creation, streaming, video editing
- **Shopping**: things to buy, product research
- **Ideas**: random thoughts, future possibilities

### Priority Levels
- **High**: university deadlines, health issues, critical tasks
- **Medium**: personal projects, skill development
- **Low**: ideas, shopping, exploration

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
                        └─────────────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Bot Framework | python-telegram-bot | Handle Telegram messages |
| Hosting | Railway | Cloud deployment with webhooks |
| AI | Groq (Llama 3.3 70B) | Message categorization |
| Storage | Notion API | Database for organized items |

### File Structure
```
life-organizer-bot/
├── bot.py                  # Main bot - handles Telegram messages
├── ai_categorizer.py       # Groq integration for AI categorization
├── notion_integration.py   # Notion API handlers
├── setup_notion.py         # Database property setup script
├── clear_webhook.py        # Utility to clear Telegram webhooks
├── requirements.txt        # Python dependencies
├── railway.toml            # Railway deployment config
├── .env                    # Local environment variables
├── .env.example            # Environment template
└── README.md               # Quick start guide
```

---

## Build Journey & Obstacles

This project was built on **February 6-7, 2026** with significant debugging along the way. Here's the complete journey:

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

---

### Obstacle 2: Missing Webhook Dependencies
**Problem:** Webhook mode requires additional packages.

**Error:** `RuntimeError: To use start_webhook, PTB must be installed via pip install "python-telegram-bot[webhooks]"`

**Solution:** Updated `requirements.txt`:
```
python-telegram-bot[webhooks]>=20.7
```

---

### Obstacle 3: Gemini API Quota Exhausted
**Problem:** Free tier quota for `gemini-2.0-flash-lite` was used up.

**Error:** `429 RESOURCE_EXHAUSTED - You exceeded your current quota`

**Solution:** Switched from Gemini to **Groq** which offers:
- Completely free API
- 30 requests per minute
- Llama 3.3 70B model (excellent for categorization)

---

### Obstacle 4: Groq Model Decommissioned
**Problem:** The initial Groq model was deprecated.

**Error:** `The model llama-3.1-70b-versatile has been decommissioned`

**Solution:** Updated to latest model:
```python
"model": "llama-3.3-70b-versatile"  # Current supported version
```

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

---

### Obstacle 6: Notion Integration Token Mismatch
**Problem:** Integration was deleted and recreated, but old token was still in use.

**Error:** `401 Unauthorized - API token is invalid`

**Solution:** 
1. Created new integration in correct workspace
2. Updated NOTION_TOKEN in Railway
3. Connected integration to all databases

---

### Obstacle 7: Missing Database Properties
**Problem:** Notion databases had no properties (just empty tables).

**Error:** `400 Bad Request - Category is not a property that exists`

**Solution:** Created `setup_notion.py` script that adds all required properties:
- Life Areas: Category, Type, Status, Priority, Date Added, Notes
- Brain Dump: Content, Processed, Date, Type
- Progress Log: Category, Date, Duration, Notes

---

### Obstacle 8: Notion Workspace Confusion
**Problem:** Integration was showing as connected but API said "not found". 

**Root Cause:** "Mo's Notion" (workspace) vs "Mo's Notion HQ" (page name) confusion.

**Solution:** Verified the integration workspace matched where databases lived.

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

### Voice Note Transcription
**Status:** Planned  
**Technology:** Groq Whisper API (free)  
**Benefit:** Speak your thoughts, bot transcribes and categorizes

### Image Analysis
**Status:** Planned  
**Technology:** Llama 3.2 Vision on Groq  
**Benefit:** Bot can describe and categorize images without captions

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

### Items not appearing in Notion?
1. Run `python setup_notion.py` to add properties
2. Check database has required columns
3. Verify integration has write access

---

## Credits

Built with:
- [python-telegram-bot](https://python-telegram-bot.org/)
- [Groq](https://groq.com/) - Free AI inference
- [Notion API](https://developers.notion.com/)
- [Railway](https://railway.app/) - Free cloud hosting

---

## License

MIT License - Use freely!

---

*Last updated: February 7, 2026*
