"""
Proactive notification system for sending scheduled reminders via Telegram.
"""

from typing import Optional
from telegram import Bot
from telegram.error import TelegramError
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Service for sending proactive notifications to users."""
    
    def __init__(self):
        """Initialize the notification service."""
        self.bot = Bot(token=settings.telegram_bot_token)
        logger.info("notification_service_initialized")
    
    async def send_reminder(self, telegram_id: int, title: str, description: Optional[str] = None) -> bool:
        """
        Send a reminder notification to a user.
        
        Args:
            telegram_id: Telegram user ID
            title: Reminder title
            description: Optional reminder description
            
        Returns:
            True if sent successfully, False otherwise
        """
        message = f"⏰ **Reminder**\n\n{title}"
        if description:
            message += f"\n\n{description}"
        
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info("reminder_sent", telegram_id=telegram_id, title=title)
            return True
        
        except TelegramError as e:
            logger.error("reminder_send_failed", telegram_id=telegram_id, error=str(e))
            return False
    
    async def send_event_notification(self, telegram_id: int, event_title: str, 
                                     start_time: str, location: Optional[str] = None) -> bool:
        """
        Send an event notification to a user.
        
        Args:
            telegram_id: Telegram user ID
            event_title: Event title
            start_time: Event start time (formatted string)
            location: Optional event location
            
        Returns:
            True if sent successfully, False otherwise
        """
        message = f"📅 **Upcoming Event**\n\n{event_title}\n🕐 {start_time}"
        if location:
            message += f"\n📍 {location}"
        
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info("event_notification_sent", telegram_id=telegram_id, event=event_title)
            return True
        
        except TelegramError as e:
            logger.error("event_notification_failed", telegram_id=telegram_id, error=str(e))
            return False
    
    async def send_custom_notification(self, telegram_id: int, message: str) -> bool:
        """
        Send a custom notification to a user.
        
        Args:
            telegram_id: Telegram user ID
            message: Message to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info("custom_notification_sent", telegram_id=telegram_id)
            return True
        
        except TelegramError as e:
            logger.error("custom_notification_failed", telegram_id=telegram_id, error=str(e))
            return False


# Global notification service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get the global notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
