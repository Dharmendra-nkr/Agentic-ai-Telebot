"""
Reminder MCP for creating and managing reminders.
Integrates with the scheduler for time-based notifications.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from mcps.base import BaseMCP, MCPInput, MCPOutput, MCPStatus, MCPCapability
from memory.long_term import LongTermMemory
from utils.logger import get_logger

logger = get_logger(__name__)


class ReminderInput(MCPInput):
    """Input parameters for reminder operations."""
    action: str = Field(..., description="Action to perform: create, list, cancel")
    title: Optional[str] = Field(None, description="Reminder title")
    description: Optional[str] = Field(None, description="Reminder description")
    remind_at: Optional[datetime] = Field(None, description="When to send reminder")
    is_recurring: bool = Field(default=False, description="Is this a recurring reminder")
    recurrence_rule: Optional[str] = Field(None, description="Recurrence rule (cron format)")
    reminder_id: Optional[int] = Field(None, description="Reminder ID for cancel/update operations")


class ReminderMCP(BaseMCP):
    """MCP for managing reminders."""
    
    def __init__(self, db: AsyncSession, scheduler=None):
        """
        Initialize Reminder MCP.
        
        Args:
            db: Database session
            scheduler: Reminder scheduler instance
        """
        super().__init__()
        self.db = db
        self.memory = LongTermMemory(db)
        self.scheduler = scheduler
    
    async def execute(self, input_data: ReminderInput, user_id: int, **kwargs) -> MCPOutput:
        """
        Execute reminder operation.
        
        Args:
            input_data: Reminder operation parameters
            user_id: User ID
            **kwargs: Additional context
            
        Returns:
            MCPOutput with operation results
        """
        try:
            if input_data.action == "create":
                return await self._create_reminder(input_data, user_id)
            elif input_data.action == "list":
                return await self._list_reminders(user_id)
            elif input_data.action == "cancel":
                return await self._cancel_reminder(input_data, user_id)
            else:
                return MCPOutput(
                    status=MCPStatus.FAILURE,
                    message=f"Unknown action: {input_data.action}",
                    error="Invalid action"
                )
        
        except Exception as e:
            logger.error("reminder_mcp_error", error=str(e), action=input_data.action)
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to execute reminder operation",
                error=str(e)
            )
    
    async def _create_reminder(self, input_data: ReminderInput, user_id: int) -> MCPOutput:
        """Create a new reminder."""
        if not input_data.remind_at:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Remind_at time is required for creating reminders",
                error="Missing required field: remind_at"
            )
        
        # Generate a default title if none provided
        if not input_data.title:
            # Use description if available, otherwise create a generic title
            if input_data.description:
                input_data.title = input_data.description
            else:
                # Create a simple title from the time
                time_str = input_data.remind_at.strftime("%I:%M %p")
                input_data.title = f"Reminder at {time_str}"
        
        reminder = await self.memory.create_reminder(
            user_id=user_id,
            title=input_data.title,
            remind_at=input_data.remind_at,
            description=input_data.description,
            is_recurring=input_data.is_recurring,
            recurrence_rule=input_data.recurrence_rule
        )
        
        # Schedule the reminder with APScheduler
        if self.scheduler:
            try:
                # Get the user's telegram_id from the database
                from sqlalchemy import select
                from memory.models import User
                
                result = await self.db.execute(
                    select(User.telegram_id).where(User.id == user_id)
                )
                telegram_id = result.scalar_one()
                
                await self.scheduler.schedule_reminder(
                    reminder_id=reminder.id,
                    remind_at=input_data.remind_at,
                    telegram_id=telegram_id,  # Use actual Telegram ID
                    title=input_data.title,
                    description=input_data.description
                )
                logger.info("reminder_scheduled_successfully", reminder_id=reminder.id, telegram_id=telegram_id)
            except Exception as e:
                logger.error("reminder_scheduling_failed", reminder_id=reminder.id, error=str(e))
        
        return MCPOutput(
            status=MCPStatus.SUCCESS,
            message=f"Created reminder: {input_data.title}",
            data={
                'reminder_id': reminder.id,
                'title': reminder.title,
                'remind_at': reminder.remind_at.isoformat()
            }
        )
    
    async def _list_reminders(self, user_id: int) -> MCPOutput:
        """List active reminders."""
        reminders = await self.memory.get_active_reminders(user_id)
        
        reminder_list = [
            {
                'id': r.id,
                'title': r.title,
                'remind_at': r.remind_at.isoformat(),
                'is_recurring': r.is_recurring
            }
            for r in reminders
        ]
        
        return MCPOutput(
            status=MCPStatus.SUCCESS,
            message=f"Found {len(reminders)} active reminders",
            data={'reminders': reminder_list}
        )
    
    async def _cancel_reminder(self, input_data: ReminderInput, user_id: int) -> MCPOutput:
        """Cancel a reminder."""
        if not input_data.reminder_id:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="reminder_id is required for cancelling",
                error="Missing reminder_id"
            )
        
        # TODO: Add user_id check for security
        from memory.temporal import TemporalMemory
        temporal = TemporalMemory(self.db)
        success = await temporal.cancel_reminder(input_data.reminder_id)
        
        if success:
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                message=f"Cancelled reminder {input_data.reminder_id}"
            )
        else:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Reminder {input_data.reminder_id} not found",
                error="Reminder not found"
            )
    
    def get_capabilities(self) -> List[MCPCapability]:
        """Get reminder MCP capabilities."""
        return [
            MCPCapability(
                name="create_reminder",
                description="Create a new reminder with optional recurrence",
                parameters={
                    "title": "string (required)",
                    "remind_at": "datetime (required)",
                    "description": "string (optional)",
                    "is_recurring": "boolean (optional)",
                    "recurrence_rule": "string (optional)"
                },
                examples=[
                    "Remind me to call John tomorrow at 3 PM",
                    "Set a reminder for my dentist appointment 1 hour before",
                    "Remind me every Monday at 9 AM to submit weekly report"
                ]
            ),
            MCPCapability(
                name="list_reminders",
                description="List all active reminders",
                parameters={},
                examples=["Show my reminders", "What reminders do I have?"]
            ),
            MCPCapability(
                name="cancel_reminder",
                description="Cancel an existing reminder",
                parameters={"reminder_id": "integer (required)"},
                examples=["Cancel reminder #5", "Delete my 3 PM reminder"]
            )
        ]
    
    def get_description(self) -> str:
        """Get MCP description."""
        return "Manages user reminders including creation, listing, and cancellation. Supports one-time and recurring reminders."
