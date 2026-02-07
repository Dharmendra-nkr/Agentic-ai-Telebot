"""
Google Calendar API Helper
Handles authentication and API interactions with Google Calendar.
"""

import os
import pickle
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarClient:
    """Client for interacting with Google Calendar API."""
    
    def __init__(self, user_id: int):
        """
        Initialize Google Calendar client for a specific user.
        
        Args:
            user_id: User ID for token storage
        """
        self.user_id = user_id
        self.service = None
        self.credentials = None
        self.token_path = Path(f"credentials/token_user_{user_id}.pickle")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Load existing credentials
            if self.token_path.exists():
                with open(self.token_path, 'rb') as token:
                    self.credentials = pickle.load(token)
            
            # Refresh or get new credentials
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.info("refreshing_google_token", user_id=self.user_id)
                    self.credentials.refresh(Request())
                else:
                    logger.info("starting_oauth_flow", user_id=self.user_id)
                    flow = InstalledAppFlow.from_client_secrets_file(
                        settings.google_credentials_file, SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0)
                
                # Save credentials for future use
                self.token_path.parent.mkdir(exist_ok=True)
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.credentials, token)
                
                logger.info("google_auth_successful", user_id=self.user_id)
            
            # Build service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return True
            
        except Exception as e:
            logger.error("google_auth_failed", user_id=self.user_id, error=str(e))
            return False
    
    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone: str = "Asia/Kolkata"
    ) -> Optional[Dict[str, Any]]:
        """
        Create an event in Google Calendar.
        
        Args:
            title: Event title
            start_time: Event start time
            end_time: Event end time
            description: Event description (optional)
            location: Event location (optional)
            timezone: Timezone for the event
            
        Returns:
            Created event data or None if failed
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            event = {
                'summary': title,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': timezone,
                },
            }
            
            if description:
                event['description'] = description
            
            if location:
                event['location'] = location
            
            result = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            logger.info(
                "google_event_created",
                user_id=self.user_id,
                event_id=result.get('id'),
                title=title
            )
            
            return result
            
        except HttpError as e:
            logger.error(
                "google_event_creation_failed",
                user_id=self.user_id,
                error=str(e)
            )
            return None
    
    def list_events(
        self,
        max_results: int = 10,
        time_min: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        List upcoming events from Google Calendar.
        
        Args:
            max_results: Maximum number of events to return
            time_min: Minimum start time for events (defaults to now)
            
        Returns:
            List of event dictionaries
        """
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            if not time_min:
                time_min = datetime.utcnow()
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            logger.info(
                "google_events_listed",
                user_id=self.user_id,
                count=len(events)
            )
            
            return events
            
        except HttpError as e:
            logger.error(
                "google_events_list_failed",
                user_id=self.user_id,
                error=str(e)
            )
            return []
    
    def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone: str = "Asia/Kolkata"
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing event in Google Calendar.
        
        Args:
            event_id: Google Calendar event ID
            title: New event title (optional)
            start_time: New start time (optional)
            end_time: New end time (optional)
            description: New description (optional)
            location: New location (optional)
            timezone: Timezone for the event
            
        Returns:
            Updated event data or None if failed
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            # Get existing event
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Update fields
            if title:
                event['summary'] = title
            if start_time:
                event['start'] = {
                    'dateTime': start_time.isoformat(),
                    'timeZone': timezone,
                }
            if end_time:
                event['end'] = {
                    'dateTime': end_time.isoformat(),
                    'timeZone': timezone,
                }
            if description:
                event['description'] = description
            if location:
                event['location'] = location
            
            # Update event
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(
                "google_event_updated",
                user_id=self.user_id,
                event_id=event_id
            )
            
            return updated_event
            
        except HttpError as e:
            logger.error(
                "google_event_update_failed",
                user_id=self.user_id,
                event_id=event_id,
                error=str(e)
            )
            return None
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event from Google Calendar.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not self.service:
            if not self.authenticate():
                return False
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            logger.info(
                "google_event_deleted",
                user_id=self.user_id,
                event_id=event_id
            )
            
            return True
            
        except HttpError as e:
            logger.error(
                "google_event_deletion_failed",
                user_id=self.user_id,
                event_id=event_id,
                error=str(e)
            )
            return False
    
    def is_authenticated(self) -> bool:
        """
        Check if user has valid Google Calendar credentials.
        
        Returns:
            True if authenticated, False otherwise
        """
        if not self.token_path.exists():
            return False
        
        try:
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
                return creds and creds.valid
        except Exception:
            return False


# Convenience function for quick access
def get_google_calendar_client(user_id: int) -> GoogleCalendarClient:
    """
    Get a Google Calendar client for a specific user.
    
    Args:
        user_id: User ID
        
    Returns:
        GoogleCalendarClient instance
    """
    return GoogleCalendarClient(user_id)
