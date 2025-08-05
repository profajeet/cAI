"""
MCP registry for managing MCP server extensions.
"""
import importlib
import inspect
from typing import Dict, List, Type, Any
from pathlib import Path
import logging
import asyncio
from .base_mcp import BaseMCPServer, MCPRequest, MCPResponse


class MCPRegistry:
    """Registry for managing MCP server extensions."""
    
    def __init__(self):
        self.servers: Dict[str, Type[BaseMCPServer]] = {}
        self.server_instances: Dict[str, BaseMCPServer] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_server(self, server_class: Type[BaseMCPServer]) -> None:
        """Register an MCP server class."""
        if not issubclass(server_class, BaseMCPServer):
            raise ValueError(f"MCP server class must inherit from BaseMCPServer: {server_class}")
        
        server_name = server_class.__name__
        self.servers[server_name] = server_class
        self.logger.info(f"Registered MCP server: {server_name}")
    
    def create_server_instance(self, server_name: str, config: Dict[str, Any]) -> BaseMCPServer:
        """Create an instance of an MCP server."""
        if server_name not in self.servers:
            raise ValueError(f"MCP server not found: {server_name}")
        
        server_class = self.servers[server_name]
        instance = server_class(config)
        self.server_instances[server_name] = instance
        return instance
    
    def get_server(self, server_name: str) -> BaseMCPServer:
        """Get an MCP server instance."""
        if server_name not in self.server_instances:
            raise ValueError(f"MCP server instance not found: {server_name}")
        return self.server_instances[server_name]
    
    def get_all_servers(self) -> Dict[str, BaseMCPServer]:
        """Get all registered MCP server instances."""
        return self.server_instances.copy()
    
    def get_enabled_servers(self) -> Dict[str, BaseMCPServer]:
        """Get all enabled MCP server instances."""
        return {
            name: server for name, server in self.server_instances.items()
            if server.is_enabled()
        }
    
    def load_servers_from_directory(self, directory: str, config_manager) -> None:
        """Load MCP servers from a directory."""
        servers_dir = Path(directory)
        if not servers_dir.exists():
            self.logger.warning(f"MCP servers directory does not exist: {directory}")
            return
        
        # Find all Python files in the directory
        for py_file in servers_dir.glob("*.py"):
            if py_file.name.startswith("__") or py_file.name.startswith("base_"):
                continue
            
            try:
                # Import the module
                module_name = f"src.mcp_extensions.{py_file.stem}"
                module = importlib.import_module(module_name)
                
                # Find server classes in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseMCPServer) and 
                        obj != BaseMCPServer):
                        
                        # Check if server is enabled in config
                        server_config = config_manager.get_mcp_config(name)
                        if server_config and server_config.get("enabled", False):
                            self.register_server(obj)
                            # Create instance with config
                            self.create_server_instance(name, server_config)
                        else:
                            self.logger.info(f"MCP server {name} is disabled in configuration")
                
            except Exception as e:
                self.logger.error(f"Failed to load MCP server from {py_file}: {e}")
    
    async def initialize_all_servers(self) -> Dict[str, bool]:
        """Initialize all enabled MCP servers."""
        results = {}
        enabled_servers = self.get_enabled_servers()
        
        for name, server in enabled_servers.items():
            try:
                success = await server.initialize()
                results[name] = success
                if success:
                    self.logger.info(f"MCP server {name} initialized successfully")
                else:
                    self.logger.error(f"Failed to initialize MCP server {name}")
            except Exception as e:
                self.logger.error(f"Error initializing MCP server {name}: {e}")
                results[name] = False
        
        return results
    
    async def cleanup_all_servers(self) -> Dict[str, bool]:
        """Cleanup all MCP servers."""
        results = {}
        
        for name, server in self.server_instances.items():
            try:
                success = await server.cleanup()
                results[name] = success
                if success:
                    self.logger.info(f"MCP server {name} cleaned up successfully")
                else:
                    self.logger.error(f"Failed to cleanup MCP server {name}")
            except Exception as e:
                self.logger.error(f"Error cleaning up MCP server {name}: {e}")
                results[name] = False
        
        return results
    
    async def handle_request(self, server_name: str, request: MCPRequest) -> MCPResponse:
        """Handle an MCP request for a specific server."""
        server = self.get_server(server_name)
        return await server.handle_request(request)
    
    def get_server_schemas(self) -> Dict[str, Any]:
        """Get schemas for all registered MCP servers."""
        return {
            name: server.get_schema().dict() 
            for name, server in self.server_instances.items()
        }
    
    def list_servers(self) -> List[str]:
        """List all registered MCP server names."""
        return list(self.servers.keys())
    
    def list_enabled_servers(self) -> List[str]:
        """List all enabled MCP server names."""
        return list(self.get_enabled_servers().keys())
    
    def get_server_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all MCP servers."""
        return {
            name: server.get_status() 
            for name, server in self.server_instances.items()
        }


# Global MCP registry instance
mcp_registry = MCPRegistry() 