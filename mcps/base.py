"""
Base MCP (Model Context Protocol) interface.
Defines the standard interface that all MCPs must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from enum import Enum
from utils.logger import get_logger

logger = get_logger(__name__)


class MCPStatus(str, Enum):
    """MCP execution status."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class MCPInput(BaseModel):
    """Base class for MCP input parameters."""
    pass


class MCPOutput(BaseModel):
    """Standard MCP output format."""
    status: MCPStatus
    data: Optional[Any] = None
    message: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MCPCapability(BaseModel):
    """Describes an MCP's capabilities."""
    name: str
    description: str
    parameters: Dict[str, Any]
    examples: List[str] = Field(default_factory=list)


class BaseMCP(ABC):
    """
    Abstract base class for all MCPs.
    All tool implementations must inherit from this class.
    """
    
    def __init__(self):
        """Initialize the MCP."""
        self.name = self.__class__.__name__
        logger.info("mcp_initialized", mcp_name=self.name)
    
    @abstractmethod
    async def execute(self, input_data: MCPInput, **kwargs) -> MCPOutput:
        """
        Execute the MCP with given input.
        
        Args:
            input_data: Input parameters for the MCP
            **kwargs: Additional execution context
            
        Returns:
            MCPOutput with execution results
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[MCPCapability]:
        """
        Get the capabilities of this MCP.
        
        Returns:
            List of capabilities this MCP provides
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        Get a human-readable description of this MCP.
        
        Returns:
            Description string
        """
        pass
    
    def validate_input(self, input_data: MCPInput) -> bool:
        """
        Validate input data before execution.
        
        Args:
            input_data: Input to validate
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        try:
            # Pydantic will validate on instantiation
            return True
        except Exception as e:
            logger.error("mcp_input_validation_failed", mcp_name=self.name, error=str(e))
            raise ValueError(f"Invalid input for {self.name}: {str(e)}")
    
    async def execute_with_retry(self, input_data: MCPInput, max_retries: int = 3, **kwargs) -> MCPOutput:
        """
        Execute MCP with automatic retry on failure.
        
        Args:
            input_data: Input parameters
            max_retries: Maximum number of retry attempts
            **kwargs: Additional execution context
            
        Returns:
            MCPOutput with execution results
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info("mcp_execute_attempt", mcp_name=self.name, attempt=attempt + 1)
                result = await self.execute(input_data, **kwargs)
                
                if result.status == MCPStatus.SUCCESS:
                    return result
                
                last_error = result.error
                logger.warning("mcp_execute_failed", 
                             mcp_name=self.name, 
                             attempt=attempt + 1, 
                             error=result.error)
                
            except Exception as e:
                last_error = str(e)
                logger.error("mcp_execute_exception", 
                           mcp_name=self.name, 
                           attempt=attempt + 1, 
                           error=str(e))
        
        # All retries failed
        return MCPOutput(
            status=MCPStatus.FAILURE,
            message=f"Failed after {max_retries} attempts",
            error=last_error
        )
    
    def __repr__(self):
        return f"<{self.name}>"
