# Agentic AI Telebot

An intelligent Telegram bot powered by Groq LLM that manages your calendar, reminders, notes, and tasks with natural language processing.

## 🌟 Features

- **🤖 AI-Powered Agent**: Uses Groq's Llama 3.3 70B for intelligent conversation
- **📅 Calendar Management**: Create and manage events with natural language
- **⏰ Smart Reminders**: Set reminders with relative time ("in 2 minutes", "in 1 hour")
- **📝 Notes & Tasks**: Organize your thoughts and to-dos
- **🧠 Memory System**: Learns your preferences over time
- **⚡ APScheduler Integration**: Reliable reminder notifications

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Telegram Bot Token
- Groq API Key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Dharmendra-nkr/Agentic-ai-Telebot.git
cd Agentic-ai-Telebot
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials:
# - TELEGRAM_BOT_TOKEN
# - GROQ_API_KEY
# - ALLOWED_USER_IDS
```

5. **Run the bot**
```bash
python main.py
```

## 📖 Usage Examples

### Reminders
```
"Remind me to drink water in 5 minutes"
"Remind me for meeting in 1 hour"
"Set a reminder for lunch in 30 minutes"
```

### Calendar Events
```
"Schedule a meeting tomorrow at 3 PM"
"Create an event for dinner on Friday at 7 PM"
```

### Notes & Tasks
```
"Note: Buy groceries"
"Add task: Complete project report"
```

## 🏗️ Architecture

```
├── agent/              # AI agent components (planner, executor, orchestrator)
├── mcps/              # Microservice Communication Patterns (calendar, reminder)
├── memory/            # Short-term, long-term, and temporal memory
├── scheduler/         # APScheduler for reminder notifications
├── telegram_bot/      # Telegram bot integration
├── utils/             # NLP utilities and logging
└── main.py           # Application entry point
```

## 🔧 Configuration

See [SETUP.md](SETUP.md) for detailed setup instructions.

See [GROQ_SETUP.md](GROQ_SETUP.md) for Groq API configuration.

## 📚 Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Groq Integration](GROQ_INTEGRATION.md)
- [Quick Start Guide](QUICKSTART_GROQ.md)

## 🛠️ Tech Stack

- **LLM**: Groq (Llama 3.3 70B)
- **Framework**: FastAPI + python-telegram-bot
- **Database**: SQLite with SQLAlchemy
- **Scheduler**: APScheduler
- **NLP**: dateparser, dateutil

## 🔐 Security

- Environment variables for sensitive data
- User ID whitelist for access control
- `.gitignore` configured to exclude secrets

## 📝 License

MIT License

## 👨‍💻 Author

Dharmendra

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on GitHub.
