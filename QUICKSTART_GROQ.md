# Quick Start - Using Your Groq API Key

Since you have a Groq API key, here's the fastest way to get started:

## 1️⃣ Add Your Groq API Key

Open the `.env` file and update line 23:

```env
GROQ_API_KEY=paste_your_groq_key_here
```

**That's it!** The system is already configured to use Groq (line 28 shows `LLM_PROVIDER=groq`).

## 2️⃣ Add Your Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the bot token

Open `.env` and update line 8:

```env
TELEGRAM_BOT_TOKEN=paste_your_bot_token_here
```

## 3️⃣ Run the Application

```bash
# Make sure virtual environment is activated
venv\Scripts\activate

# Run the app
python main.py
```

You should see:
```
INFO: Application starting
INFO: Database initialized
INFO: Scheduler started
INFO: Telegram bot started
INFO: Application ready (LLM provider: groq)
```

## 4️⃣ Test in Telegram

1. Open Telegram
2. Search for your bot
3. Send `/start`
4. Try: **"Remind me to buy groceries tomorrow at 5 PM"**

You'll notice **blazing fast responses** thanks to Groq! ⚡

## 🎯 Why Groq is Great

- ⚡ **10x faster** than OpenAI
- 🆓 **Free tier** with generous limits
- 🤖 **Llama 3.1 70B** model (very capable)
- 🔥 **Perfect for development** and personal use

## 📚 Next Steps

- Read [GROQ_SETUP.md](GROQ_SETUP.md) for advanced Groq configuration
- Check [README.md](README.md) for full documentation
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details

## 🔄 Want to Switch Providers Later?

Just change one line in `.env`:

```env
# Use Groq (current)
LLM_PROVIDER=groq

# Or switch to OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here

# Or Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here
```

---

**You're all set!** Enjoy your ultra-fast AI assistant! 🚀
