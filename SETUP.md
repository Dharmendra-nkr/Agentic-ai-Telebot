# Quick Setup Guide

## ✅ Environment Setup Complete!

Your development environment is ready:
- ✅ Virtual environment created (`venv/`)
- ✅ All dependencies installed
- ✅ `.env` file created

## 🔑 Next Steps: Add Your API Keys

### 1. Get Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get LLM API Key

**Option A: Groq (Recommended - Fast & Free)** ⚡
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Create an API key
4. See [GROQ_SETUP.md](GROQ_SETUP.md) for detailed instructions

**Option B: OpenAI**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create an account and navigate to API keys
3. Create a new API key

**Option C: Anthropic**
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account and get API key

### 3. Update `.env` File

**Minimal `.env` configuration**:
```env
# Required
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Choose ONE LLM provider:
# Option 1: Groq (Fast & Free - Recommended)
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq

# Option 2: OpenAI
# OPENAI_API_KEY=your_openai_api_key_here
# LLM_PROVIDER=openai

# Option 3: Anthropic
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# LLM_PROVIDER=anthropic

# Optional (defaults work for development)
DATABASE_URL=sqlite+aiosqlite:///./agentic_ai.db
ENVIRONMENT=development
DEBUG=True
```

**That's it!** The database is already configured to use SQLite (no setup needed).

## 🚀 Run the Application

```bash
# Activate virtual environment (if not already active)
venv\Scripts\activate

# Run the application
python main.py
```

You should see:
```
INFO: Application starting
INFO: Database initialized
INFO: Scheduler started
INFO: Telegram bot started
INFO: Application ready
```

## 📱 Test Your Bot

1. Open Telegram
2. Search for your bot by username
3. Send `/start` command
4. Try: "Remind me to buy groceries tomorrow at 5 PM"

## 📚 Documentation

- [README.md](README.md) - Full documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details
- [Walkthrough](../brain/.../walkthrough.md) - Complete guide

## ❓ Troubleshooting

**Bot not responding?**
- Check `.env` has correct `TELEGRAM_BOT_TOKEN`
- Verify bot is running (`python main.py`)

**Import errors?**
- Make sure venv is activated: `venv\Scripts\activate`
- Reinstall: `pip install -r requirements.txt`

---

**Need help?** Check the walkthrough document for detailed instructions!
