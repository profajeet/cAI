"""
MCP (Multi-Component Processor) server management.

This module provides the MCPServerManager class that handles MCP server
connections, activation, and operation execution.
"""

import asyncio
import aiohttp
import json
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console

from config.settings import Settings, MCPServerConfig

console = Console()


class MCPServerManager:
    """
    Manages MCP server connections and operations.
    
    This class provides:
    - MCP server connection management
    - Server activation and health checks
    - Operation execution
    - Load balancing and optimization
    """
    
    def __init__(self, settings: Settings):
        """Initialize the MCP server manager."""
        self.settings = settings
        
        # Active connections
        self.connections: Dict[str, aiohttp.ClientSession] = {}
        
        # Server status cache
        self.server_status: Dict[str, Dict[str, Any]] = {}
        
        # Connection pool
        self.session: Optional[aiohttp.ClientSession] = None
        
        console.log("🔌 MCPServerManager initialized")
    
    async def initialize(self):
        """Initialize the MCP server manager."""
        # Create HTTP session
        connector = aiohttp.TCPConnector(
            limit=self.settings.max_concurrent_requests,
            limit_per_host=5,
            ttl_dns_cache=300
        )
        
        timeout = aiohttp.ClientTimeout(total=self.settings.request_timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        # Initialize server status
        await self._initialize_server_status()
        
        console.log("🔌 MCPServerManager initialized successfully")
    
    async def get_server(self, server_name: str) -> Optional[MCPServerConfig]:
        """
        Get MCP server configuration.
        
        Args:
            server_name: Name of the server
            
        Returns:
            Server configuration or None if not found
        """
        return self.settings.get_mcp_server(server_name)
    
    async def connect_to_server(self, server_name: str) -> bool:
        """
        Connect to an MCP server.
        
        Args:
            server_name: Name of the server to connect to
            
        Returns:
            True if connection successful, False otherwise
        """
        server_config = await self.get_server(server_name)
        
        if not server_config:
            console.log(f"❌ MCP server not found: {server_name}")
            return False
        
        if not server_config.enabled:
            console.log(f"⚠️ MCP server disabled: {server_name}")
            return False
        
        try:
            # Check if already connected
            if server_name in self.connections:
                console.log(f"🔌 Already connected to {server_name}")
                return True
            
            # Test connection
            if await self._test_connection(server_config):
                # Store connection info
                self.connections[server_name] = {
                    "config": server_config,
                    "connected_at": asyncio.get_event_loop().time(),
                    "last_used": asyncio.get_event_loop().time(),
                    "request_count": 0
                }
                
                console.log(f"🔌 Connected to MCP server: {server_name}")
                return True
            else:
                console.log(f"❌ Failed to connect to MCP server: {server_name}")
                return False
                
        except Exception as e:
            console.log(f"❌ Error connecting to MCP server {server_name}: {e}")
            return False
    
    async def execute_operation(
        self, 
        server_name: str, 
        intent: Dict[str, Any],
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an operation on an MCP server.
        
        Args:
            server_name: Name of the MCP server
            intent: Operation intent
            entities: Operation entities
            
        Returns:
            Operation result
        """
        try:
            # Ensure connection
            if not await self.connect_to_server(server_name):
                return {
                    "success": False,
                    "error": f"Failed to connect to MCP server: {server_name}"
                }
            
            # Get server configuration
            server_config = await self.get_server(server_name)
            if not server_config:
                return {
                    "success": False,
                    "error": f"MCP server not found: {server_name}"
                }
            
            # Prepare operation request
            operation_request = await self._prepare_operation_request(
                server_name, intent, entities
            )
            
            # Execute operation
            result = await self._execute_mcp_request(
                server_config, operation_request
            )
            
            # Update connection stats
            if server_name in self.connections:
                self.connections[server_name]["last_used"] = asyncio.get_event_loop().time()
                self.connections[server_name]["request_count"] += 1
            
            return result
            
        except Exception as e:
            console.log(f"❌ Error executing operation on {server_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_server_health(self, server_name: str) -> Dict[str, Any]:
        """
        Check the health of an MCP server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            Health status
        """
        server_config = await self.get_server(server_name)
        
        if not server_config:
            return {
                "healthy": False,
                "error": "Server not found"
            }
        
        try:
            # Test basic connectivity
            health_url = f"{server_config.url}/health"
            
            async with self.session.get(health_url) as response:
                if response.status == 200:
                    health_data = await response.json()
                    return {
                        "healthy": True,
                        "status": health_data,
                        "response_time": response.headers.get("X-Response-Time", "unknown")
                    }
                else:
                    return {
                        "healthy": False,
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def get_optimal_server(self, server_type: str) -> Optional[str]:
        """
        Get the optimal server for a given type.
        
        Args:
            server_type: Type of server needed
            
        Returns:
            Optimal server name or None
        """
        available_servers = []
        
        for server_name, server_config in self.settings.mcp_servers.items():
            if (server_config.enabled and 
                server_type in server_name.lower()):
                
                # Check health
                health = await self.check_server_health(server_name)
                
                if health["healthy"]:
                    available_servers.append({
                        "name": server_name,
                        "config": server_config,
                        "health": health
                    })
        
        if not available_servers:
            return None
        
        # Select optimal server based on criteria
        # For now, select the first available
        # Could be enhanced with load balancing logic
        return available_servers[0]["name"]
    
    async def list_servers(self) -> List[Dict[str, Any]]:
        """
        List all MCP servers and their status.
        
        Returns:
            List of server information
        """
        servers = []
        
        for server_name, server_config in self.settings.mcp_servers.items():
            health = await self.check_server_health(server_name)
            
            server_info = {
                "name": server_name,
                "config": {
                    "host": server_config.host,
                    "port": server_config.port,
                    "protocol": server_config.protocol,
                    "enabled": server_config.enabled
                },
                "health": health,
                "connected": server_name in self.connections
            }
            
            servers.append(server_info)
        
        return servers
    
    async def _initialize_server_status(self):
        """Initialize server status cache."""
        for server_name in self.settings.mcp_servers:
            self.server_status[server_name] = {
                "last_check": None,
                "healthy": False,
                "response_time": None,
                "error": None
            }
    
    async def _test_connection(self, server_config: MCPServerConfig) -> bool:
        """Test connection to an MCP server."""
        try:
            # Test basic connectivity
            test_url = f"{server_config.url}/ping"
            
            async with self.session.get(test_url) as response:
                return response.status == 200
                
        except Exception as e:
            console.log(f"❌ Connection test failed for {server_config.name}: {e}")
            return False
    
    async def _prepare_operation_request(
        self, 
        server_name: str, 
        intent: Dict[str, Any],
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare operation request for MCP server."""
        operation_type = intent.get("type", "unknown")
        
        request = {
            "operation": operation_type,
            "intent": intent,
            "entities": entities,
            "server": server_name,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Add operation-specific data
        if operation_type == "file_operation":
            request["file_paths"] = entities.get("file_paths", [])
            request["operations"] = entities.get("operations", [])
            
        elif operation_type == "database_operation":
            request["database"] = entities.get("database", {})
            request["operations"] = entities.get("operations", [])
            
        elif operation_type == "api_operation":
            request["api_endpoints"] = entities.get("api_endpoints", [])
            request["operations"] = entities.get("operations", [])
        
        return request
    
    async def _execute_mcp_request(
        self, 
        server_config: MCPServerConfig,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute request on MCP server."""
        try:
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            if server_config.auth_token:
                headers["Authorization"] = f"Bearer {server_config.auth_token}"
            
            # Execute request
            operation_url = f"{server_config.url}/execute"
            
            async with self.session.post(
                operation_url,
                json=request_data,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "result": result,
                        "response_time": response.headers.get("X-Response-Time", "unknown")
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_server_status(self, server_name: str, status: Dict[str, Any]):
        """Update server status cache."""
        self.server_status[server_name] = {
            "last_check": asyncio.get_event_loop().time(),
            "healthy": status.get("healthy", False),
            "response_time": status.get("response_time"),
            "error": status.get("error")
        }
    
    async def shutdown(self):
        """Shutdown the MCP server manager."""
        console.log("🔄 Shutting down MCPServerManager...")
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        # Clear connections
        self.connections.clear()
        
        console.log("✅ MCPServerManager shutdown complete") 