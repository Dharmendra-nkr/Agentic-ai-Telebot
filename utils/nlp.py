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
    
    # Intent keywords mapping
    INTENT_KEYWORDS = {
        'create_event': ['schedule', 'appointment', 'meeting', 'event', 'save the date', 'book'],
        'create_reminder': ['remind', 'reminder', 'alert', 'notify'],
        'create_note': ['note', 'write down', 'remember', 'jot down'],
        'create_task': ['task', 'todo', 'to-do', 'need to do'],
        'query_events': ['what', 'when', 'show', 'list', 'upcoming'],
        'cancel': ['cancel', 'delete', 'remove'],
        'update': ['change', 'update', 'modify', 'reschedule'],
    }
    
    def extract_intent(self, text: str) -> str:
        """
        Extract primary intent from user message.
        
        Args:
            text: User message
            
        Returns:
            Intent string (e.g., 'create_event', 'create_reminder')
        """
        text_lower = text.lower()
        
        # Check for intent keywords
        for intent, keywords in self.INTENT_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                logger.info("extracted_intent", text=text, intent=intent)
                return intent
        
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
