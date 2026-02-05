"""
Main application entry point for the Agentic AI Personal Assistant.
Initializes all components and starts the Telegram bot.
"""

import asyncio
import signal
from contextlib import asynccontextmanager
from fastapi import FastAPI
from config import settings
from memory.models import init_db
from telegram_bot import TelegramBot
from scheduler import get_scheduler
from utils.logger import get_logger

logger = get_logger(__name__)


# Global instances
telegram_bot: TelegramBot = None
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("application_starting", environment=settings.environment)
    
    try:
        # Initialize database
        logger.info("initializing_database")
        await init_db()
        logger.info("database_initialized")
        
        # Start scheduler
        global scheduler
        scheduler = get_scheduler()
        await scheduler.start()
        logger.info("scheduler_started")
        
        # Start Telegram bot
        global telegram_bot
        telegram_bot = TelegramBot(scheduler=scheduler)
        telegram_bot.build()
        
        # Set bot reference in scheduler for notifications
        scheduler.set_bot(telegram_bot)
        
        # Start bot in background task
        asyncio.create_task(telegram_bot.start_polling())
        logger.info("telegram_bot_started")
        
        logger.info("application_ready", 
                   app_name=settings.app_name,
                   llm_provider=settings.llm_provider)
        
        yield
        
    finally:
        # Shutdown
        logger.info("application_shutting_down")
        
        if telegram_bot:
            await telegram_bot.stop()
            logger.info("telegram_bot_stopped")
        
        if scheduler:
            await scheduler.stop()
            logger.info("scheduler_stopped")
        
        logger.info("application_shutdown_complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Agentic AI Personal Assistant with Telegram Interface",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "status": "running",
        "app": settings.app_name,
        "version": "1.0.0",
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "telegram_bot": "running" if telegram_bot else "not started",
        "scheduler": "running" if scheduler else "not started"
    }


@app.get("/stats")
async def get_stats():
    """Get application statistics."""
    from memory.short_term import _user_memories
    from mcps.registry import get_registry
    
    registry = get_registry()
    
    return {
        "active_users": len(_user_memories),
        "registered_mcps": len(registry),
        "mcp_list": registry.list_mcps()
    }


def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    logger.info("received_shutdown_signal", signal=signum)
    # FastAPI will handle graceful shutdown via lifespan


if __name__ == "__main__":
    import uvicorn
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Run the application
    logger.info("starting_uvicorn_server")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )
