"""
Calendar MCP for Google Calendar integration.
Handles event creation, retrieval, and management.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from mcps.base import BaseMCP, MCPInput, MCPOutput, MCPStatus, MCPCapability
from memory.long_term import LongTermMemory
from utils.logger import get_logger
from utils.google_calendar_helper import get_google_calendar_client
logger = get_logger(__name__)


class CalendarInput(MCPInput):
    """Input parameters for calendar operations."""
    action: str = Field(..., description="Action: create_event, list_events, update_event, delete_event")
    title: Optional[str] = Field(None, description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_time: Optional[datetime] = Field(None, description="Event start time")
    end_time: Optional[datetime] = Field(None, description="Event end time")
    location: Optional[str] = Field(None, description="Event location")
    event_id: Optional[int] = Field(None, description="Event ID for update/delete")
    days_ahead: Optional[int] = Field(7, description="Days ahead to query for list_events")


class CalendarMCP(BaseMCP):
    """MCP for Google Calendar integration."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize Calendar MCP.
        
        Args:
            db: Database session
        """
        super().__init__()
        self.db = db
        self.memory = LongTermMemory(db)
        # TODO: Initialize Google Calendar API client
        self.google_calendar = None
    
    async def execute(self, input_data: CalendarInput, user_id: int, **kwargs) -> MCPOutput:
        """
        Execute calendar operation.
        
        Args:
            input_data: Calendar operation parameters
            user_id: User ID
            **kwargs: Additional context (including telegram_id)
            
        Returns:
            MCPOutput with operation results
        """
        try:
            if input_data.action == "create_event":
                return await self._create_event(input_data, user_id, **kwargs)
            elif input_data.action == "list_events":
                return await self._list_events(input_data, user_id)
            elif input_data.action == "update_event":
                return await self._update_event(input_data, user_id)
            elif input_data.action == "delete_event":
                return await self._delete_event(input_data, user_id)
            else:
                return MCPOutput(
                    status=MCPStatus.FAILURE,
                    message=f"Unknown action: {input_data.action}",
                    error="Invalid action"
                )
        
        except Exception as e:
            logger.error("calendar_mcp_error", error=str(e), action=input_data.action)
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to execute calendar operation",
                error=str(e)
            )
    
    async def _create_event(self, input_data: CalendarInput, user_id: int, **kwargs) -> MCPOutput:
        """Create a new calendar event."""
        if not input_data.title or not input_data.start_time:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Title and start_time are required for creating events",
                error="Missing required fields"
            )
        
        # Default end time to 1 hour after start if not provided
        end_time = input_data.end_time or (input_data.start_time + timedelta(hours=1))
        
        # Create event in database
        event = await self.memory.create_event(
            user_id=user_id,
            title=input_data.title,
            start_time=input_data.start_time,
            end_time=end_time,
            description=input_data.description,
            location=input_data.location
        )
        
        # Sync with Google Calendar
        google_event_id = None
        google_sync_status = "not_synced"
        
        # Extract telegram_id from kwargs (passed by executor)
        telegram_id = kwargs.get('telegram_id', user_id)
        
        try:
            google_client = get_google_calendar_client(telegram_id)
            
            # Check if user is authenticated
            if google_client.is_authenticated():
                google_event = google_client.create_event(
                    title=input_data.title,
                    start_time=input_data.start_time,
                    end_time=end_time,
                    description=input_data.description,
                    location=input_data.location
                )
                
                if google_event:
                    google_event_id = google_event.get('id')
                    google_sync_status = "synced"
                    logger.info(
                        "event_synced_to_google",
                        event_id=event.id,
                        google_event_id=google_event_id,
                        telegram_id=telegram_id
                    )
                else:
                    google_sync_status = "sync_failed"
                    logger.warning("google_event_creation_failed", event_id=event.id, telegram_id=telegram_id)
            else:
                # User needs to authenticate first
                google_sync_status = "auth_required"
                logger.info("google_auth_required", telegram_id=telegram_id)
                
        except Exception as e:
            google_sync_status = "sync_error"
            logger.warning(
                "google_sync_exception",
                error=str(e),
                event_id=event.id,
                telegram_id=telegram_id
            )
        
        # Prepare response message
        message = f"Created event: {input_data.title}"
        if google_sync_status == "synced":
            message += " (synced to Google Calendar)"
        elif google_sync_status == "auth_required":
            message += " (Google Calendar sync requires authentication - run authentication flow)"
        elif google_sync_status in ["sync_failed", "sync_error"]:
            message += " (saved locally, Google Calendar sync failed)"
        
        return MCPOutput(
            status=MCPStatus.SUCCESS,
            message=message,
            data={
                'event_id': event.id,
                'title': event.title,
                'start_time': event.start_time.isoformat(),
                'end_time': event.end_time.isoformat(),
                'google_event_id': google_event_id,
                'google_sync_status': google_sync_status
            }
        )
    
    async def _list_events(self, input_data: CalendarInput, user_id: int) -> MCPOutput:
        """List upcoming events."""
        events = await self.memory.get_upcoming_events(user_id, limit=10)
        
        event_list = [
            {
                'id': e.id,
                'title': e.title,
                'start_time': e.start_time.isoformat(),
                'end_time': e.end_time.isoformat() if e.end_time else None,
                'location': e.location
            }
            for e in events
        ]
        
        return MCPOutput(
            status=MCPStatus.SUCCESS,
            message=f"Found {len(events)} upcoming events",
            data={'events': event_list}
        )
    
    async def _update_event(self, input_data: CalendarInput, user_id: int) -> MCPOutput:
        """Update an existing event."""
        # TODO: Implement event update logic
        return MCPOutput(
            status=MCPStatus.FAILURE,
            message="Event update not yet implemented",
            error="Not implemented"
        )
    
    async def _delete_event(self, input_data: CalendarInput, user_id: int) -> MCPOutput:
        """Delete an event."""
        # TODO: Implement event deletion logic
        return MCPOutput(
            status=MCPStatus.FAILURE,
            message="Event deletion not yet implemented",
            error="Not implemented"
        )
    
    def get_capabilities(self) -> List[MCPCapability]:
        """Get calendar MCP capabilities."""
        return [
            MCPCapability(
                name="create_event",
                description="Create a new calendar event",
                parameters={
                    "title": "string (required)",
                    "start_time": "datetime (required)",
                    "end_time": "datetime (optional)",
                    "description": "string (optional)",
                    "location": "string (optional)"
                },
                examples=[
                    "Schedule a dentist appointment on March 1st at 8 AM",
                    "Create a meeting with John tomorrow at 3 PM",
                    "Book a 2-hour workshop on Friday at 10 AM"
                ]
            ),
            MCPCapability(
                name="list_events",
                description="List upcoming calendar events",
                parameters={"days_ahead": "integer (optional, default 7)"},
                examples=[
                    "What's on my calendar?",
                    "Show my upcoming events",
                    "What do I have scheduled this week?"
                ]
            ),
            MCPCapability(
                name="update_event",
                description="Update an existing calendar event",
                parameters={
                    "event_id": "integer (required)",
                    "title": "string (optional)",
                    "start_time": "datetime (optional)",
                    "end_time": "datetime (optional)"
                },
                examples=["Reschedule my dentist appointment to 9 AM"]
            ),
            MCPCapability(
                name="delete_event",
                description="Delete a calendar event",
                parameters={"event_id": "integer (required)"},
                examples=["Cancel my 3 PM meeting", "Delete tomorrow's appointment"]
            )
        ]
    
    def get_description(self) -> str:
        """Get MCP description."""
        return "Manages calendar events with Google Calendar integration. Supports creating, listing, updating, and deleting events."
