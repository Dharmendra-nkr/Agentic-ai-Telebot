"""
Short-term memory management for conversation context.
Maintains recent conversation history in memory for quick access.
"""

from typing import List, Dict, Any, Optional
from collections import deque
from datetime import datetime
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class Message:
    """Represents a single message in conversation."""
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None, metadata: Optional[Dict[str, Any]] = None):
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    def __repr__(self):
        return f"Message(role={self.role}, content={self.content[:50]}...)"


class ShortTermMemory:
    """
    Short-term memory for maintaining conversation context.
    Uses a fixed-size buffer to store recent messages.
    """
    
    def __init__(self, max_size: int = None):
        """
        Initialize short-term memory.
        
        Args:
            max_size: Maximum number of messages to keep (defaults to config setting)
        """
        self.max_size = max_size or settings.short_term_memory_size
        self._buffer: deque = deque(maxlen=self.max_size)
        self._session_start = datetime.now()
        logger.info("short_term_memory_initialized", max_size=self.max_size)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a message to short-term memory.
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata (intent, entities, etc.)
        """
        message = Message(role=role, content=content, metadata=metadata)
        self._buffer.append(message)
        logger.debug("message_added_to_stm", role=role, buffer_size=len(self._buffer))
    
    def get_recent_messages(self, n: Optional[int] = None) -> List[Message]:
        """
        Get recent messages from memory.
        
        Args:
            n: Number of recent messages to retrieve (None for all)
            
        Returns:
            List of recent messages
        """
        if n is None:
            return list(self._buffer)
        return list(self._buffer)[-n:]
    
    def get_context_for_llm(self, n: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get conversation context formatted for LLM.
        
        Args:
            n: Number of recent messages to include
            
        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        messages = self.get_recent_messages(n)
        return [{'role': msg.role, 'content': msg.content} for msg in messages]
    
    def get_last_user_message(self) -> Optional[Message]:
        """Get the most recent user message."""
        for message in reversed(self._buffer):
            if message.role == 'user':
                return message
        return None
    
    def get_last_assistant_message(self) -> Optional[Message]:
        """Get the most recent assistant message."""
        for message in reversed(self._buffer):
            if message.role == 'assistant':
                return message
        return None
    
    def clear(self) -> None:
        """Clear all messages from short-term memory."""
        self._buffer.clear()
        self._session_start = datetime.now()
        logger.info("short_term_memory_cleared")
    
    def get_session_duration(self) -> float:
        """Get session duration in seconds."""
        return (datetime.now() - self._session_start).total_seconds()
    
    def __len__(self) -> int:
        """Get number of messages in memory."""
        return len(self._buffer)
    
    def __repr__(self):
        return f"ShortTermMemory(size={len(self._buffer)}/{self.max_size})"


# Global short-term memory instances per user
_user_memories: Dict[int, ShortTermMemory] = {}


def get_user_memory(user_id: int) -> ShortTermMemory:
    """
    Get or create short-term memory for a user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        ShortTermMemory instance for the user
    """
    if user_id not in _user_memories:
        _user_memories[user_id] = ShortTermMemory()
        logger.info("created_user_memory", user_id=user_id)
    return _user_memories[user_id]


def clear_user_memory(user_id: int) -> None:
    """
    Clear short-term memory for a user.
    
    Args:
        user_id: Telegram user ID
    """
    if user_id in _user_memories:
        _user_memories[user_id].clear()
        logger.info("cleared_user_memory", user_id=user_id)
