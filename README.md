# Agentic AI Personal Assistant 🤖

An intelligent, autonomous personal assistant powered by agentic AI, accessible through Telegram. This system demonstrates advanced AI concepts including autonomous planning, tool use via MCPs (Model Context Protocols), multi-tiered memory systems, and proactive user interaction.

## 🌟 Features

### Core Capabilities
- **📅 Calendar Management**: Create, view, and manage calendar events with Google Calendar integration
- **⏰ Smart Reminders**: Set one-time or recurring reminders with intelligent timing
- **📝 Notes**: Save and retrieve information easily
- **✅ Task Management**: Create and track tasks with priorities and due dates
- **🧠 Memory Systems**: 
  - Short-term memory for conversation context
  - Long-term memory for user preferences and history
  - Temporal memory for scheduled actions

### Agentic Behaviors
- **🎯 Intent Understanding**: Natural language processing to understand user requests
- **🤔 Intelligent Planning**: Multi-step action planning from single commands
- **❓ Clarifying Questions**: Asks for missing information when needed
- **📚 Preference Learning**: Learns and adapts to user habits over time
- **🔔 Proactive Notifications**: Sends timely reminders and alerts
- **🛠️ Tool Selection**: Automatically chooses the right tools for each task

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Interface                    │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 Agent Orchestrator                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Planner  │  │ Executor │  │  Memory Systems      │  │
│  │          │  │          │  │  - Short-term        │  │
│  │ - Intent │  │ - MCP    │  │  - Long-term         │  │
│  │ - Entity │  │   Calls  │  │  - Temporal          │  │
│  │ - Plan   │  │ - Results│  │                      │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  MCP Framework                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ Calendar │  │ Reminder │  │  Notes   │  │ Tasks  │  │
│  │   MCP    │  │   MCP    │  │   MCP    │  │  MCP   │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OpenAI API Key or Anthropic API Key
- PostgreSQL (optional, SQLite works for development)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd Agentic_AI_DW
```

2. **Create virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
# Copy the example file
copy .env.example .env

# Edit .env and add your credentials:
# - TELEGRAM_BOT_TOKEN
# - OPENAI_API_KEY (or ANTHROPIC_API_KEY)
# - DATABASE_URL (optional, defaults to SQLite)
```

5. **Run the application**
```bash
python main.py
```

The bot will start and be accessible via Telegram!

## 📱 Usage Examples

### Creating Events
```
User: "Save the date March 1st, I have a dental appointment at 8 AM"
Bot: "I'll create a calendar event for your dental appointment on March 1st at 8 AM. 
      Would you like me to set a reminder? If so, how long before the appointment?"

User: "Yes, remind me 1 hour before"
Bot: "✅ Done! I've created:
     - Calendar event: Dental appointment on March 1st at 8 AM
     - Reminder: 1 hour before (7 AM on March 1st)"
```

### Setting Reminders
```
User: "Remind me to call John tomorrow at 3 PM"
Bot: "✅ I'll remind you to call John tomorrow at 3 PM"
```

### Querying Calendar
```
User: "What's on my calendar this week?"
Bot: "📅 Here are your upcoming events:
     1. Team meeting - Tomorrow at 10 AM
     2. Dental appointment - March 1st at 8 AM
     3. Project deadline - Friday at 5 PM"
```

## 🛠️ Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# LLM Provider (openai, anthropic)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite+aiosqlite:///./agentic_ai.db

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# Features
ENABLE_CLARIFYING_QUESTIONS=True
ENABLE_PROACTIVE_SUGGESTIONS=True
```

### Database Setup

**SQLite (Default - No setup needed)**
```bash
# Automatically creates agentic_ai.db on first run
```

**PostgreSQL (Production)**
```bash
# Install PostgreSQL and create database
createdb agentic_ai_db

# Update .env
DATABASE_URL=postgresql://user:password@localhost:5432/agentic_ai_db
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agent.py -v
```

## 📦 Project Structure

```
Agentic_AI_DW/
├── agent/              # Agent core (orchestrator, planner, executor)
├── mcps/               # Model Context Protocol tools
├── memory/             # Memory systems (short-term, long-term, temporal)
├── telegram_bot/       # Telegram bot interface
├── scheduler/          # Background task scheduler
├── utils/              # Utilities (logging, NLP)
├── tests/              # Test suite
├── main.py             # Application entry point
├── config.py           # Configuration management
└── requirements.txt    # Dependencies
```

## 🔌 Adding New MCPs

The system uses a plug-and-play MCP architecture. To add a new tool:

1. **Create MCP class** (inherit from `BaseMCP`)
```python
from mcps.base import BaseMCP, MCPInput, MCPOutput, MCPStatus

class MyMCP(BaseMCP):
    async def execute(self, input_data: MCPInput, **kwargs) -> MCPOutput:
        # Your implementation
        pass
    
    def get_capabilities(self) -> List[MCPCapability]:
        # Define capabilities
        pass
```

2. **Register the MCP**
```python
from mcps.registry import register_mcp
register_mcp(MyMCP(db))
```

## 🎓 Research & Academic Use

This project demonstrates key agentic AI concepts suitable for research:

- **Autonomy**: Self-directed planning and execution
- **Tool Use**: Dynamic MCP selection and orchestration
- **Memory Architecture**: Multi-tiered memory (short/long/temporal)
- **Proactive Behavior**: Scheduled and context-aware engagement
- **Natural Language Understanding**: Intent and entity extraction
- **Graceful Degradation**: Error handling and recovery

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:

- Additional MCPs (Email, Weather, News, etc.)
- Advanced NLP with spaCy
- Voice message support
- Multi-language support
- Web dashboard
- Analytics and insights

## 📄 License

MIT License - feel free to use for personal or commercial projects.

## 🙏 Acknowledgments

Built with:
- FastAPI
- python-telegram-bot
- OpenAI / Anthropic
- SQLAlchemy
- APScheduler

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Check the documentation
- Review example conversations

---

**Made with ❤️ for the agentic AI community**
