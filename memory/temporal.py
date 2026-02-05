"""
Temporal memory for managing scheduled actions and future events.
Integrates with the scheduler for time-based triggers.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from memory.models import Reminder, Event
from utils.logger import get_logger

logger = get_logger(__name__)


class TemporalMemory:
    """
    Temporal memory for managing time-based actions and scheduled events.
    Provides interface for querying and managing future actions.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize temporal memory.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def get_pending_reminders(self, before: Optional[datetime] = None) -> List[Reminder]:
        """
        Get reminders that need to be sent.
        
        Args:
            before: Get reminders before this time (defaults to now)
            
        Returns:
            List of pending reminders
        """
        if before is None:
            before = datetime.now()
        
        result = await self.db.execute(
            select(Reminder)
            .where(and_(
                Reminder.remind_at <= before,
                Reminder.status == "active",
                Reminder.is_sent == False
            ))
            .order_by(Reminder.remind_at)
        )
        return list(result.scalars().all())
    
    async def mark_reminder_sent(self, reminder_id: int) -> None:
        """
        Mark a reminder as sent.
        
        Args:
            reminder_id: Reminder ID
        """
        result = await self.db.execute(
            select(Reminder).where(Reminder.id == reminder_id)
        )
        reminder = result.scalar_one_or_none()
        
        if reminder:
            reminder.is_sent = True
            reminder.sent_at = datetime.now()
            reminder.status = "sent"
            await self.db.commit()
            logger.info("marked_reminder_sent", reminder_id=reminder_id)
    
    async def get_events_in_range(self, user_id: int, start: datetime, end: datetime) -> List[Event]:
        """
        Get events within a time range.
        
        Args:
            user_id: User ID
            start: Start of time range
            end: End of time range
            
        Returns:
            List of events in range
        """
        result = await self.db.execute(
            select(Event)
            .where(and_(
                Event.user_id == user_id,
                Event.start_time >= start,
                Event.start_time <= end,
                Event.status == "confirmed"
            ))
            .order_by(Event.start_time)
        )
        return list(result.scalars().all())
    
    async def get_upcoming_in_window(self, user_id: int, hours: int = 24) -> Dict[str, List]:
        """
        Get all upcoming events and reminders in a time window.
        
        Args:
            user_id: User ID
            hours: Time window in hours
            
        Returns:
            Dictionary with 'events' and 'reminders' lists
        """
        now = datetime.now()
        window_end = now + timedelta(hours=hours)
        
        # Get events
        events_result = await self.db.execute(
            select(Event)
            .where(and_(
                Event.user_id == user_id,
                Event.start_time >= now,
                Event.start_time <= window_end,
                Event.status == "confirmed"
            ))
            .order_by(Event.start_time)
        )
        events = list(events_result.scalars().all())
        
        # Get reminders
        reminders_result = await self.db.execute(
            select(Reminder)
            .where(and_(
                Reminder.user_id == user_id,
                Reminder.remind_at >= now,
                Reminder.remind_at <= window_end,
                Reminder.status == "active"
            ))
            .order_by(Reminder.remind_at)
        )
        reminders = list(reminders_result.scalars().all())
        
        logger.info("retrieved_upcoming_window", 
                   user_id=user_id, 
                   hours=hours, 
                   events_count=len(events), 
                   reminders_count=len(reminders))
        
        return {
            'events': events,
            'reminders': reminders
        }
    
    async def cancel_reminder(self, reminder_id: int) -> bool:
        """
        Cancel a reminder.
        
        Args:
            reminder_id: Reminder ID
            
        Returns:
            True if cancelled, False if not found
        """
        result = await self.db.execute(
            select(Reminder).where(Reminder.id == reminder_id)
        )
        reminder = result.scalar_one_or_none()
        
        if reminder:
            reminder.status = "cancelled"
            await self.db.commit()
            logger.info("cancelled_reminder", reminder_id=reminder_id)
            return True
        
        return False
    
    async def get_reminder_by_job_id(self, job_id: str) -> Optional[Reminder]:
        """
        Get reminder by scheduler job ID.
        
        Args:
            job_id: Scheduler job ID
            
        Returns:
            Reminder object or None
        """
        result = await self.db.execute(
            select(Reminder).where(Reminder.scheduler_job_id == job_id)
        )
        return result.scalar_one_or_none()
