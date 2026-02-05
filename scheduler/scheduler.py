"""
Background task scheduler for proactive reminders and notifications.
Uses APScheduler for time-based job execution.
"""

from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from memory.models import AsyncSessionLocal
from memory.temporal import TemporalMemory
from telegram_bot.notifications import get_notification_service
from utils.logger import get_logger

logger = get_logger(__name__)

# Global bot instance for standalone reminder function
_bot_instance = None


async def send_reminder_notification(reminder_id: int, telegram_id: int, 
                                     title: str, description: Optional[str] = None):
    """
    Standalone function to send reminder notification.
    This is a module-level function that can be serialized by APScheduler.
    
    Args:
        reminder_id: Reminder ID
        telegram_id: Telegram user ID
        title: Reminder title
        description: Optional description
    """
    logger.info("sending_reminder", reminder_id=reminder_id, telegram_id=telegram_id)
    
    try:
        # Get notification service
        notification_service = get_notification_service()
        
        # Build message
        message = f"🔔 **Reminder**\n\n{title}"
        if description:
            message += f"\n\n{description}"
        
        # Send notification
        success = await notification_service.send_reminder(
            telegram_id=telegram_id,
            title=title,
            description=description
        )
        
        if success:
            # Mark reminder as sent in database
            async with AsyncSessionLocal() as db:
                temporal = TemporalMemory(db)
                await temporal.mark_reminder_sent(reminder_id)
                await db.commit()
            
            logger.info("reminder_sent_and_marked", reminder_id=reminder_id)
        else:
            logger.error("reminder_send_failed", reminder_id=reminder_id)
    except Exception as e:
        logger.error("reminder_notification_error", reminder_id=reminder_id, error=str(e))


class ReminderScheduler:
    """Scheduler for managing reminder jobs."""
    
    def __init__(self):
        """Initialize the scheduler."""
        # Configure job store
        jobstores = {
            'default': SQLAlchemyJobStore(url=settings.database_url.replace('+aiosqlite', ''))
        }
        
        # Create scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            timezone=settings.scheduler_timezone
        )
        
        self.notification_service = get_notification_service()
        self.bot = None  # Will be set later
        logger.info("reminder_scheduler_initialized", timezone=settings.scheduler_timezone)
    
    def set_bot(self, bot):
        """Set the bot instance for sending notifications."""
        self.bot = bot
        logger.info("scheduler_bot_set")
    
    async def start(self) -> None:
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("scheduler_started")
        
        # Note: Periodic reminder check disabled to avoid serialization issues
        # Reminders are scheduled individually when created
    
    async def schedule_reminder(self, reminder_id: int, telegram_id: int, 
                               title: str, remind_at: datetime, 
                               description: Optional[str] = None) -> str:
        """
        Schedule a reminder job.
        
        Args:
            reminder_id: Database reminder ID
            telegram_id: Telegram user ID
            title: Reminder title
            remind_at: When to send the reminder
            description: Optional description
            
        Returns:
            Job ID
        """
        job_id = f"reminder_{reminder_id}"
        
        # Store bot reference globally for the standalone function to use
        global _bot_instance
        _bot_instance = self.bot
        
        # Add job to scheduler using standalone function (can be serialized)
        self.scheduler.add_job(
            send_reminder_notification,
            trigger=DateTrigger(run_date=remind_at),
            args=[reminder_id, telegram_id, title, description],
            id=job_id,
            replace_existing=True
        )
        
        logger.info("reminder_scheduled", 
                   reminder_id=reminder_id, 
                   job_id=job_id, 
                   remind_at=remind_at.isoformat())
        
        return job_id
    
    async def stop(self) -> None:
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("scheduler_stopped")
    
    async def schedule_recurring_reminder(self, reminder_id: int, telegram_id: int,
                                         title: str, cron_expression: str,
                                         description: Optional[str] = None) -> str:
        """
        Schedule a recurring reminder.
        
        Args:
            reminder_id: Database reminder ID
            telegram_id: Telegram user ID
            title: Reminder title
            cron_expression: Cron expression for recurrence
            description: Optional description
            
        Returns:
            Job ID
        """
        job_id = f"reminder_recurring_{reminder_id}"
        
        # Parse cron expression
        # Format: minute hour day month day_of_week
        parts = cron_expression.split()
        
        self.scheduler.add_job(
            self._send_reminder_job,
            trigger=CronTrigger.from_crontab(cron_expression),
            args=[reminder_id, telegram_id, title, description],
            id=job_id,
            replace_existing=True
        )
        
        logger.info("recurring_reminder_scheduled",
                   reminder_id=reminder_id,
                   job_id=job_id,
                   cron=cron_expression)
        
        return job_id
    
    async def cancel_reminder(self, job_id: str) -> bool:
        """
        Cancel a scheduled reminder.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if cancelled, False if not found
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info("reminder_cancelled", job_id=job_id)
            return True
        except Exception as e:
            logger.warning("reminder_cancel_failed", job_id=job_id, error=str(e))
            return False
    
    async def _send_reminder_job(self, reminder_id: int, telegram_id: int,
                                 title: str, description: Optional[str] = None) -> None:
        """
        Job function to send a reminder.
        
        Args:
            reminder_id: Reminder ID
            telegram_id: Telegram user ID
            title: Reminder title
            description: Optional description
        """
        logger.info("sending_reminder", reminder_id=reminder_id, telegram_id=telegram_id)
        
        # Send notification
        success = await self.notification_service.send_reminder(
            telegram_id=telegram_id,
            title=title,
            description=description
        )
        
        if success:
            # Mark reminder as sent in database
            async with AsyncSessionLocal() as db:
                temporal = TemporalMemory(db)
                await temporal.mark_reminder_sent(reminder_id)
                await db.commit()
            
            logger.info("reminder_sent_and_marked", reminder_id=reminder_id)
        else:
            logger.error("reminder_send_failed", reminder_id=reminder_id)
    
    async def _check_pending_reminders(self) -> None:
        """Periodic job to check for pending reminders."""
        try:
            async with AsyncSessionLocal() as db:
                temporal = TemporalMemory(db)
                pending = await temporal.get_pending_reminders()
                
                if pending:
                    logger.info("found_pending_reminders", count=len(pending))
                    
                    for reminder in pending:
                        # This is a backup check - reminders should already be scheduled
                        # But this catches any that might have been missed
                        await self._send_reminder_job(
                            reminder.id,
                            reminder.user.telegram_id,
                            reminder.title,
                            reminder.description
                        )
        
        except Exception as e:
            logger.error("pending_reminders_check_failed", error=str(e))


# Global scheduler instance
_scheduler: Optional[ReminderScheduler] = None


def get_scheduler() -> ReminderScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = ReminderScheduler()
    return _scheduler
