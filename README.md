# Life Organizer Bot

An ADHD-friendly Telegram bot that helps you organize your life by automatically categorizing and storing everything you send it into Notion.

## Features

- 🤖 **AI-Powered Categorization**: Uses Gemini Flash to automatically categorize your messages
- 📝 **Multi-Format Support**: Text, images, PDFs, voice notes
- 📊 **Notion Integration**: Automatically organizes everything in your Notion workspace
- 🎯 **Zero Friction**: Just dump your thoughts, the bot handles the rest
- 💰 **Cost-Effective**: ~$1-2/month in API costs

## How It Works

1. **Send anything to the bot**:
   - "Buy whey protein" → Shopping
   - "Study chapter 5" → Study
   - Photo of a guitar → Asks what it's for
   - "Learn piano" → Skills

2. **AI categorizes it** into:
   - Health, Study, Personal Projects, Skills, Creative, Shopping, Ideas

3. **Stored in Notion** with:
   - Category, Priority, Type, Date
   - Notes and attachments

## Setup

### 1. Prerequisites

- Python 3.9+
- Telegram account
- Notion account (free tier)
- Google API key (for Gemini Flash)

### 2. Install Dependencies

```bash
cd life-organizer-bot
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
NOTION_TOKEN=your_notion_integration_token_here
GOOGLE_API_KEY=your_google_api_key_here
```

### 4. Set Up Notion Databases

Run the setup script:

```bash
python setup_notion.py
```

This will create three databases in your Notion workspace and output the database IDs. Add them to your `.env`:

```env
LIFE_AREAS_DB_ID=xxx
BRAIN_DUMP_DB_ID=xxx
PROGRESS_DB_ID=xxx
```

### 5. Run the Bot

```bash
python bot.py
```

## Deployment to Railway

1. Create a Railway account at railway.app
2. Connect your GitHub repository
3. Add environment variables in Railway dashboard:
   - `TELEGRAM_BOT_TOKEN`
   - `NOTION_TOKEN`
   - `GOOGLE_API_KEY`
   - `LIFE_AREAS_DB_ID`
   - `BRAIN_DUMP_DB_ID`
   - `PROGRESS_DB_ID`
4. **Generate a public domain**:
   - Go to Settings → Networking → Generate Domain
   - Copy the domain (e.g., `life-organizer-bot-production.up.railway.app`)
5. **Add the domain as an environment variable**:
   - Name: `RAILWAY_PUBLIC_DOMAIN`
   - Value: `your-app-name.up.railway.app` (without `https://`)
6. Deploy! The bot will automatically use webhook mode.

**Note**: Railway's free tier gives you $5/month credit, which is more than enough for this bot.

## Bot Commands

- `/start` - Introduction and welcome message
- `/help` - Show help and examples
- `/active` - See your current active items

## Project Structure

```
life-organizer-bot/
├── bot.py                  # Main bot code
├── ai_categorizer.py       # Gemini Flash integration
├── notion_integration.py   # Notion API handlers
├── setup_notion.py         # Database setup script
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
└── README.md              # This file
```

## Cost Breakdown

- **Railway hosting**: $0/month (free tier: $5 credit/month)
- **Gemini Flash API**: ~$1-2/month (100 messages/day)
- **Notion**: $0/month (free tier)

**Total: ~$1-2/month**

## Databases

### Life Areas
Main database for organized items:
- Categories: Health, Study, Personal Projects, Skills, Creative, Shopping, Ideas
- Types: Task, Goal, Idea, Resource
- Status: Active, Parked, Done, Dropped
- Priority: High, Medium, Low

### Brain Dump Inbox
Temporary storage for items needing manual review:
- Unprocessed messages
- Files and attachments
- Voice notes

### Progress Log
Track your activities:
- What you did
- When you did it
- How long it took
- Category

## Tips for ADHD Users

1. **Don't overthink it** - Just send messages, the bot organizes
2. **Use voice notes** - Easier than typing when ideas flow
3. **Check /active weekly** - See what you're actually working on
4. **Let items "park"** - It's okay to not do everything at once
5. **Trust the system** - Your ideas are saved, you can explore them later

## Troubleshooting

**Bot not responding?**
- Check if bot is running: `ps aux | grep bot.py`
- Check logs for errors

**Items not appearing in Notion?**
- Verify database IDs in `.env`
- Check Notion integration has access to the databases

**High API costs?**
- Check Gemini API usage in Google Cloud Console
- Consider reducing message frequency

## Future Improvements

- Voice transcription
- Weekly summary reports
- Progress analytics
- Custom categories
- Reminders for high-priority items

## License

MIT License - Use freely!

## Credits

Built with:
- python-telegram-bot
- Google Gemini Flash
- Notion API
