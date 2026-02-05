"""
Long-term memory management for persistent user data.
Handles storage and retrieval of user preferences, events, and historical interactions.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from memory.models import User, Conversation, Event, Reminder, Note, Task, UserPreference
from utils.logger import get_logger

logger = get_logger(__name__)


class LongTermMemory:
    """
    Long-term memory for persistent storage of user data.
    Interfaces with the database to store and retrieve information.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize long-term memory.
        
        Args:
            db: Database session
        """
        self.db = db
    
    # User Management
    async def get_or_create_user(self, telegram_id: int, **kwargs) -> User:
        """
        Get existing user or create new one.
        
        Args:
            telegram_id: Telegram user ID
            **kwargs: Additional user fields
            
        Returns:
            User object
        """
        result = await self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(telegram_id=telegram_id, **kwargs)
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            logger.info("created_new_user", telegram_id=telegram_id)
        
        return user
    
    # Conversation History
    async def save_conversation(
        self,
        user_id: int,
        role: str,
        content: str,
        message_id: Optional[int] = None,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Save a conversation message."""
        import json
        from datetime import datetime, timedelta
        
        # Convert datetime and timedelta objects in entities to serializable format
        if entities:
            entities_copy = {}
            for key, value in entities.items():
                if isinstance(value, datetime):
                    entities_copy[key] = value.isoformat()
                elif isinstance(value, timedelta):
                    # Convert timedelta to total seconds
                    entities_copy[key] = value.total_seconds()
                else:
                    entities_copy[key] = value
            entities_json = json.dumps(entities_copy)
        else:
            entities_json = None
        
        conversation = Conversation(
            user_id=user_id,
            message_id=message_id,
            role=role,
            content=content,
            intent=intent,
            entities=entities_json
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        logger.debug("saved_conversation", user_id=user_id, role=role)
        return conversation
    
    async def get_conversation_history(self, user_id: int, limit: int = 50) -> List[Conversation]:
        """
        Get recent conversation history for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation messages
        """
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.timestamp))
            .limit(limit)
        )
        conversations = result.scalars().all()
        return list(reversed(conversations))  # Return in chronological order
    
    # Events
    async def create_event(self, user_id: int, title: str, start_time: datetime, **kwargs) -> Event:
        """
        Create a new event.
        
        Args:
            user_id: User ID
            title: Event title
            start_time: Event start time
            **kwargs: Additional event fields
            
        Returns:
            Event object
        """
        event = Event(
            user_id=user_id,
            title=title,
            start_time=start_time,
            **kwargs
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        logger.info("created_event", user_id=user_id, title=title, start_time=start_time)
        return event
    
    async def get_upcoming_events(self, user_id: int, limit: int = 10) -> List[Event]:
        """
        Get upcoming events for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of events to retrieve
            
        Returns:
            List of upcoming events
        """
        now = datetime.now()
        result = await self.db.execute(
            select(Event)
            .where(and_(
                Event.user_id == user_id,
                Event.start_time >= now,
                Event.status == "confirmed"
            ))
            .order_by(Event.start_time)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    # Reminders
    async def create_reminder(self, user_id: int, title: str, remind_at: datetime, **kwargs) -> Reminder:
        """
        Create a new reminder.
        
        Args:
            user_id: User ID
            title: Reminder title
            remind_at: When to send reminder
            **kwargs: Additional reminder fields
            
        Returns:
            Reminder object
        """
        reminder = Reminder(
            user_id=user_id,
            title=title,
            remind_at=remind_at,
            **kwargs
        )
        self.db.add(reminder)
        await self.db.commit()
        await self.db.refresh(reminder)
        logger.info("created_reminder", user_id=user_id, title=title, remind_at=remind_at)
        return reminder
    
    async def get_active_reminders(self, user_id: int) -> List[Reminder]:
        """Get all active reminders for a user."""
        result = await self.db.execute(
            select(Reminder)
            .where(and_(
                Reminder.user_id == user_id,
                Reminder.status == "active"
            ))
            .order_by(Reminder.remind_at)
        )
        return list(result.scalars().all())
    
    # User Preferences
    async def save_preference(self, user_id: int, key: str, value: Any, confidence: float = 1.0) -> UserPreference:
        """
        Save or update user preference.
        
        Args:
            user_id: User ID
            key: Preference key
            value: Preference value
            confidence: Confidence score (0-1)
            
        Returns:
            UserPreference object
        """
        # Check if preference exists
        result = await self.db.execute(
            select(UserPreference)
            .where(and_(
                UserPreference.user_id == user_id,
                UserPreference.preference_key == key
            ))
        )
        preference = result.scalar_one_or_none()
        
        if preference:
            # Update existing preference
            preference.preference_value = value
            preference.confidence_score = confidence
            preference.learn_count += 1
            logger.info("updated_preference", user_id=user_id, key=key)
        else:
            # Create new preference
            preference = UserPreference(
                user_id=user_id,
                preference_key=key,
                preference_value=value,
                confidence_score=confidence
            )
            self.db.add(preference)
            logger.info("created_preference", user_id=user_id, key=key)
        
        await self.db.commit()
        await self.db.refresh(preference)
        return preference
    
    async def get_preference(self, user_id: int, key: str) -> Optional[Any]:
        """
        Get user preference value.
        
        Args:
            user_id: User ID
            key: Preference key
            
        Returns:
            Preference value or None
        """
        result = await self.db.execute(
            select(UserPreference)
            .where(and_(
                UserPreference.user_id == user_id,
                UserPreference.preference_key == key
            ))
        )
        preference = result.scalar_one_or_none()
        return preference.preference_value if preference else None
    
    async def get_all_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get all preferences for a user as a dictionary."""
        result = await self.db.execute(
            select(UserPreference)
            .where(UserPreference.user_id == user_id)
        )
        preferences = result.scalars().all()
        return {pref.preference_key: pref.preference_value for pref in preferences}
