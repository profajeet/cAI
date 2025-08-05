"""
Base MCP server class for all MCP extensions.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import logging
import asyncio
from datetime import datetime


class MCPServerSchema(BaseModel):
    """Schema for MCP server capabilities."""
    name: str
    description: str
    version: str
    capabilities: Dict[str, Any]
    resources: List[Dict[str, Any]] = Field(default_factory=list)


class MCPRequest(BaseModel):
    """MCP request structure."""
    method: str
    params: Dict[str, Any]
    id: Optional[str] = None


class MCPResponse(BaseModel):
    """MCP response structure."""
    result: Any
    error: Optional[str] = None
    id: Optional[str] = None


class BaseMCPServer(ABC):
    """Base class for all MCP server extensions."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.name = self.__class__.__name__
        self.description = getattr(self, 'description', 'No description provided')
        self.version = getattr(self, 'version', '1.0.0')
        self.schema = self._create_schema()
        self.is_connected = False
    
    @abstractmethod
    def _create_schema(self) -> MCPServerSchema:
        """Create the MCP server schema."""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the MCP server."""
        pass
    
    @abstractmethod
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle an MCP request."""
        pass
    
    async def initialize(self) -> bool:
        """Initialize the MCP server."""
        try:
            success = await self.connect()
            if success:
                self.is_connected = True
                self.logger.info(f"MCP server {self.name} initialized successfully")
            return success
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP server {self.name}: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup the MCP server."""
        try:
            success = await self.disconnect()
            if success:
                self.is_connected = False
                self.logger.info(f"MCP server {self.name} cleaned up successfully")
            return success
        except Exception as e:
            self.logger.error(f"Failed to cleanup MCP server {self.name}: {e}")
            return False
    
    def get_schema(self) -> MCPServerSchema:
        """Get the MCP server schema."""
        return self.schema
    
    def is_enabled(self) -> bool:
        """Check if the MCP server is enabled based on configuration."""
        return self.config.get("enabled", False)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status."""
        return {
            "name": self.name,
            "connected": self.is_connected,
            "enabled": self.is_enabled(),
            "version": self.version
        } 