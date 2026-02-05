"""MCPs package initialization."""

from .base import BaseMCP, MCPInput, MCPOutput, MCPStatus, MCPCapability
from .registry import MCPRegistry, get_registry, register_mcp, get_mcp
from .reminder_mcp import ReminderMCP, ReminderInput
from .calendar_mcp import CalendarMCP, CalendarInput

__all__ = [
    # Base classes
    'BaseMCP', 'MCPInput', 'MCPOutput', 'MCPStatus', 'MCPCapability',
    # Registry
    'MCPRegistry', 'get_registry', 'register_mcp', 'get_mcp',
    # MCPs
    'ReminderMCP', 'ReminderInput',
    'CalendarMCP', 'CalendarInput',
]
