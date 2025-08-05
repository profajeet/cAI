"""
MCP (Multi-Component Processor) server integration.

This package provides MCP server management and integration:
- MCPServerManager: MCP server management
- Tool adapters for various MCP servers
"""

from .manager import MCPServerManager

__all__ = ["MCPServerManager"] 