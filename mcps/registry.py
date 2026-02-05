"""
MCP Registry for plug-and-play tool management.
Handles registration, discovery, and retrieval of MCPs.
"""

from typing import Dict, List, Optional, Type
from mcps.base import BaseMCP, MCPCapability
from utils.logger import get_logger

logger = get_logger(__name__)


class MCPRegistry:
    """
    Registry for managing available MCPs.
    Provides plug-and-play architecture for tool discovery and selection.
    """
    
    def __init__(self):
        """Initialize the MCP registry."""
        self._mcps: Dict[str, BaseMCP] = {}
        self._capabilities_cache: Optional[List[MCPCapability]] = None
        logger.info("mcp_registry_initialized")
    
    def register(self, mcp: BaseMCP, name: Optional[str] = None) -> None:
        """
        Register an MCP with the registry.
        
        Args:
            mcp: MCP instance to register
            name: Optional custom name (defaults to class name)
        """
        mcp_name = name or mcp.__class__.__name__
        self._mcps[mcp_name] = mcp
        self._capabilities_cache = None  # Invalidate cache
        logger.info("mcp_registered", mcp_name=mcp_name)
    
    def unregister(self, name: str) -> bool:
        """
        Unregister an MCP from the registry.
        
        Args:
            name: Name of MCP to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        if name in self._mcps:
            del self._mcps[name]
            self._capabilities_cache = None  # Invalidate cache
            logger.info("mcp_unregistered", mcp_name=name)
            return True
        return False
    
    def get(self, name: str) -> Optional[BaseMCP]:
        """
        Get an MCP by name.
        
        Args:
            name: Name of the MCP
            
        Returns:
            MCP instance or None if not found
        """
        return self._mcps.get(name)
    
    def list_mcps(self) -> List[str]:
        """
        List all registered MCP names.
        
        Returns:
            List of MCP names
        """
        return list(self._mcps.keys())
    
    def get_all_capabilities(self) -> List[MCPCapability]:
        """
        Get capabilities of all registered MCPs.
        
        Returns:
            List of all capabilities
        """
        if self._capabilities_cache is not None:
            return self._capabilities_cache
        
        capabilities = []
        for mcp_name, mcp in self._mcps.items():
            mcp_capabilities = mcp.get_capabilities()
            capabilities.extend(mcp_capabilities)
        
        self._capabilities_cache = capabilities
        return capabilities
    
    def find_mcp_for_capability(self, capability_name: str) -> Optional[BaseMCP]:
        """
        Find an MCP that provides a specific capability.
        
        Args:
            capability_name: Name of the capability
            
        Returns:
            MCP instance or None if not found
        """
        for mcp in self._mcps.values():
            capabilities = mcp.get_capabilities()
            if any(cap.name == capability_name for cap in capabilities):
                return mcp
        return None
    
    def get_mcp_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions of all registered MCPs.
        
        Returns:
            Dictionary mapping MCP names to descriptions
        """
        return {name: mcp.get_description() for name, mcp in self._mcps.items()}
    
    def search_mcps(self, query: str) -> List[str]:
        """
        Search for MCPs by name or description.
        
        Args:
            query: Search query
            
        Returns:
            List of matching MCP names
        """
        query_lower = query.lower()
        matches = []
        
        for name, mcp in self._mcps.items():
            if query_lower in name.lower() or query_lower in mcp.get_description().lower():
                matches.append(name)
        
        return matches
    
    def __len__(self) -> int:
        """Get number of registered MCPs."""
        return len(self._mcps)
    
    def __repr__(self):
        return f"<MCPRegistry(mcps={len(self._mcps)})>"


# Global registry instance
_global_registry = MCPRegistry()


def get_registry() -> MCPRegistry:
    """Get the global MCP registry instance."""
    return _global_registry


def register_mcp(mcp: BaseMCP, name: Optional[str] = None) -> None:
    """
    Register an MCP with the global registry.
    
    Args:
        mcp: MCP instance to register
        name: Optional custom name
    """
    _global_registry.register(mcp, name)


def get_mcp(name: str) -> Optional[BaseMCP]:
    """
    Get an MCP from the global registry.
    
    Args:
        name: Name of the MCP
        
    Returns:
        MCP instance or None
    """
    return _global_registry.get(name)
