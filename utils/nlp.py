"""
NLP utilities for parsing natural language inputs.
Handles date/time extraction, entity recognition, and text normalization.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import dateparser
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
import re
from utils.logger import get_logger

logger = get_logger(__name__)


class DateTimeParser:
    """Parse natural language date and time expressions."""
    
    def __init__(self, timezone: str = "Asia/Kolkata"):
        self.timezone = timezone
        self.settings = {
            'TIMEZONE': timezone,
            'RETURN_AS_TIMEZONE_AWARE': True,
            'PREFER_DATES_FROM': 'future',
        }
    
    def parse(self, text: str, reference_date: Optional[datetime] = None) -> Optional[datetime]:
        """
        Parse a natural language date/time string.
        
        Args:
            text: Natural language date/time string (e.g., "tomorrow at 3 PM", "March 1st at 8 AM")
            reference_date: Reference date for relative parsing (defaults to now)
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        try:
            # Use dateparser for flexible parsing
            parsed = dateparser.parse(
                text,
                settings=self.settings,
                languages=['en']
            )
            
            if parsed:
                logger.info("parsed_datetime", input=text, result=parsed.isoformat())
                return parsed
            
            # Fallback to dateutil parser
            parsed = date_parser.parse(text, fuzzy=True)
            logger.info("parsed_datetime_fallback", input=text, result=parsed.isoformat())
            return parsed
            
        except Exception as e:
            logger.warning("datetime_parse_failed", input=text, error=str(e))
            return None
    
    def extract_duration(self, text: str) -> Optional[timedelta]:
        """
        Extract duration from text (e.g., "30 minutes", "2 hours", "1 day").
        
        Args:
            text: Text containing duration
            
        Returns:
            timedelta object or None
        """
        patterns = [
            (r'(\d+)\s*(?:minute|min|minutes|mins)', lambda m: timedelta(minutes=int(m.group(1)))),
            (r'(\d+)\s*(?:hour|hr|hours|hrs)', lambda m: timedelta(hours=int(m.group(1)))),
            (r'(\d+)\s*(?:day|days)', lambda m: timedelta(days=int(m.group(1)))),
            (r'(\d+)\s*(?:week|weeks)', lambda m: timedelta(weeks=int(m.group(1)))),
        ]
        
        text_lower = text.lower()
        for pattern, converter in patterns:
            match = re.search(pattern, text_lower)
            if match:
                duration = converter(match)
                logger.info("extracted_duration", input=text, duration=str(duration))
                return duration
        
        return None


class IntentExtractor:
    """Extract intent and entities from user messages."""
    
    # High-priority intents checked first (order matters)
    # More specific patterns are checked before generic ones
    INTENT_RULES = [
        # --- File Storage (checked first — most specific) ---
        ('file_list', [
            'files in drive', 'my files', 'drive files', 'list files',
            'show files', 'list my files', 'files on drive',
            'what files', 'show my drive', 'whats in my drive', 'whats in drive'
        ]),
        ('file_link', [
            'drive link', 'file link', 'shareable link', 'share link',
            'get link', 'get the link', 'link for', 'link of',
            'send me the link', 'give me the link', 'send link'
        ]),
        ('file_share', [
            'share file', 'share document', 'share with', 'share this file',
            'share it with', 'send file to', 'give access', 'share this'
        ]),
        ('file_delete', [
            'delete file', 'delete from drive', 'remove file', 'remove from drive',
            'trash file', 'delete the file', 'delete this file',
            'remove this file', 'delete it from drive'
        ]),
        ('file_upload', [
            'upload', 'store in drive', 'save to drive', 'upload to drive',
            'put in drive', 'save in drive', 'store file', 'store document'
        ]),

        # --- Reminder queries (BEFORE create_reminder so "my reminders" matches here) ---
        ('query_reminders', [
            'my reminders', 'show reminders', 'list reminders',
            'pending reminders', 'active reminders', 'view reminders',
            'what reminders', 'check reminders'
        ]),

        # --- Calendar queries (BEFORE create_event so "my calendar" matches here) ---
        ('query_events', [
            'my calendar', 'on my calendar', 'calendar for',
            'whats on', "what's on", 'upcoming events', 'events today',
            'events tomorrow', 'show calendar', 'check calendar',
            'any events', 'any meetings', 'show my calendar'
        ]),

        # --- Calendar create ---
        ('create_event', [
            'schedule', 'appointment', 'meeting', 'event',
            'save the date', 'book', 'calendar event', 'add to calendar'
        ]),

        # --- Reminder create ---
        ('create_reminder', [
            'remind', 'reminder', 'alert me', 'notify me',
            'remind me', 'set a reminder', 'set reminder', 'don\'t forget'
        ]),

        # --- Meta actions (use specific phrases to avoid clashing with file_delete) ---
        ('cancel', [
            'cancel', 'cancel event', 'cancel meeting', 'cancel reminder',
            'cancel appointment', 'delete event', 'delete meeting',
            'delete reminder', 'delete appointment', 'remove event',
            'remove meeting', 'remove reminder', 'remove appointment'
        ]),
        ('update', ['change', 'update', 'modify', 'reschedule', 'edit']),
    ]
    
    def extract_intent(self, text: str) -> str:
        """
        Extract primary intent from user message.
        Uses ordered rules so specific intents match before generic ones.
        
        Args:
            text: User message
            
        Returns:
            Intent string (e.g., 'create_event', 'file_list')
        """
        text_lower = text.lower()
        
        # Check rules in priority order
        for intent, keywords in self.INTENT_RULES:
            if any(keyword in text_lower for keyword in keywords):
                logger.info("extracted_intent", text=text, intent=intent)
                return intent
        
        # Regex fallbacks for patterns that keyword matching can't catch
        import re
        # "delete/remove <filename> from drive" — file has words between verb and "from drive"
        if re.search(r'\b(?:delete|remove|trash)\b.+\b(?:from\s+(?:my\s+)?drive|in\s+drive)\b', text_lower):
            logger.info("extracted_intent", text=text, intent='file_delete')
            return 'file_delete'
        
        # "delete <something>" / "remove <something>" — likely file delete when no calendar/reminder context
        calendar_words = {'event', 'meeting', 'appointment', 'reminder', 'schedule', 'calendar'}
        if re.search(r'\b(?:delete|remove|trash)\b\s+\S+', text_lower):
            # Only route to file_delete if no calendar/reminder words present
            if not any(w in text_lower for w in calendar_words):
                logger.info("extracted_intent", text=text, intent='file_delete')
                return 'file_delete'
        
        # Default to general query
        return 'general_query'
    
    def extract_event_info(self, text: str) -> Dict[str, Any]:
        """
        Extract event information from text.
        
        Args:
            text: User message
            
        Returns:
            Dictionary with extracted event details
        """
        parser = DateTimeParser()
        
        info = {
            'raw_text': text,
            'datetime': None,
            'title': None,
            'duration': None,
            'reminder_before': None,
        }
        
        # Extract datetime
        info['datetime'] = parser.parse(text)
        
        # Extract duration
        info['duration'] = parser.extract_duration(text)
        
        # Extract reminder preference
        reminder_patterns = [
            r'remind.*?(\d+)\s*(?:minute|min|hour|hr|day)s?\s*before',
            r'(\d+)\s*(?:minute|min|hour|hr|day)s?\s*before',
        ]
        
        for pattern in reminder_patterns:
            match = re.search(pattern, text.lower())
            if match:
                info['reminder_before'] = parser.extract_duration(match.group(0))
                break
        
        # Extract title (simple heuristic: text between quotes or after "for")
        title_match = re.search(r'"([^"]+)"', text)
        if title_match:
            info['title'] = title_match.group(1)
        else:
            # Try to extract from context
            for keyword in ['appointment', 'meeting', 'event']:
                if keyword in text.lower():
                    # Get words around the keyword
                    pattern = rf'(\w+\s+)?{keyword}(\s+\w+)?'
                    match = re.search(pattern, text.lower())
                    if match:
                        info['title'] = match.group(0).strip()
                        break
        
        logger.info("extracted_event_info", info=info)
        return info


class TextNormalizer:
    """Normalize and clean text inputs."""
    
    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize text by removing extra whitespace and standardizing format.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """
        Extract important keywords from text.
        
        Args:
            text: Input text
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction (can be enhanced with NLP)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        words = text.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords


# Convenience functions
def parse_datetime(text: str) -> Optional[datetime]:
    """Parse datetime from natural language text."""
    parser = DateTimeParser()
    return parser.parse(text)


def extract_intent(text: str) -> str:
    """Extract intent from user message."""
    extractor = IntentExtractor()
    return extractor.extract_intent(text)


def extract_event_info(text: str) -> Dict[str, Any]:
    """Extract event information from text."""
    extractor = IntentExtractor()
    return extractor.extract_event_info(text)
