"""
Telegram bot implementation.
Handles incoming messages and sends responses.
"""

from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from memory.models import get_db
from agent.orchestrator import AgentOrchestrator
from utils.logger import get_logger

logger = get_logger(__name__)


class TelegramBot:
    """Telegram bot handler for the agentic AI assistant."""
    
    def __init__(self, scheduler=None):
        """Initialize the Telegram bot."""
        self.token = settings.telegram_bot_token
        self.application: Optional[Application] = None
        self.scheduler = scheduler
        logger.info("telegram_bot_initialized")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        welcome_message = f"""👋 Hello {user.first_name}!

I'm your intelligent personal assistant. I can help you with:

📅 **Calendar Events** - Schedule appointments and meetings
⏰ **Reminders** - Set reminders for important tasks
📝 **Notes** - Save and retrieve information
✅ **Tasks** - Manage your to-do list

Just message me naturally, like:
• "Remind me about the dentist appointment tomorrow at 8 AM"
• "What's on my calendar this week?"
• "Create a note about project ideas"

How can I help you today?"""
        
        await update.message.reply_text(welcome_message)
        logger.info("start_command", user_id=user.id, username=user.username)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_message = """🤖 **How to use me:**

**Calendar Events:**
• "Schedule a meeting with John tomorrow at 3 PM"
• "I have a dentist appointment on March 1st at 8 AM"
• "What's on my calendar?"

**Reminders:**
• "Remind me to call Mom tomorrow at 5 PM"
• "Set a reminder for my meeting 30 minutes before"
• "Show my reminders"

**Notes:**
• "Save a note: Buy groceries - milk, eggs, bread"
• "Create a note about project ideas"

**Tasks:**
• "Add task: Finish report by Friday"
• "Mark task #5 as complete"

Just talk to me naturally - I'll understand! 😊"""
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle incoming text messages.
        
        Args:
            update: Telegram update
            context: Bot context
        """
        user = update.effective_user
        message_text = update.message.text
        
        logger.info("received_message", 
                   user_id=user.id, 
                   username=user.username,
                   message=message_text[:100])
        
        # Check if user is allowed (if restrictions are enabled)
        if settings.allowed_users and user.id not in settings.allowed_users:
            await update.message.reply_text(
                "Sorry, you don't have access to this bot. Please contact the administrator."
            )
            return
        
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
        try:
            # Get database session
            async for db in get_db():
                # Create orchestrator with scheduler
                orchestrator = AgentOrchestrator(db, scheduler=self.scheduler)
                
                # Process message
                response = await orchestrator.process_message(
                    user_id=user.id,
                    telegram_id=user.id,
                    message=message_text
                )
                
                # Send response
                await update.message.reply_text(response)
                logger.info("sent_response", user_id=user.id, response_length=len(response))
                break
        
        except Exception as e:
            logger.error("message_handling_error", error=str(e), user_id=user.id)
            await update.message.reply_text(
                "I apologize, but I encountered an error. Please try again in a moment."
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors."""
        logger.error("telegram_error", error=str(context.error), update=str(update))
    
    def setup_handlers(self) -> None:
        """Set up message and command handlers."""
        if not self.application:
            raise RuntimeError("Application not initialized. Call build() first.")
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Message handler
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
        
        logger.info("handlers_registered")
    
    def build(self) -> Application:
        """
        Build the Telegram application.
        
        Returns:
            Telegram Application instance
        """
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        logger.info("telegram_application_built")
        return self.application
    
    async def start_polling(self) -> None:
        """Start the bot in polling mode."""
        if not self.application:
            self.build()
        
        logger.info("starting_telegram_bot_polling")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        
        logger.info("telegram_bot_running")
    
    async def stop(self) -> None:
        """Stop the bot."""
        if self.application:
            logger.info("stopping_telegram_bot")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
