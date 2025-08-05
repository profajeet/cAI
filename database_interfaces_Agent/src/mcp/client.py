"""
MCP (Model Context Protocol) client for Database Interface Agent.
Handles communication with database servers and manages server lifecycle.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource
)

from config.database_config import DatabaseConnectionConfig, DatabaseType
from src.agent.state import AgentState, AgentStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MCPClient:
    """MCP client for database operations."""
    
    def __init__(self):
        self.active_servers: Dict[str, Dict[str, Any]] = {}
        self.server_registry: Dict[str, Callable] = {}
        self.default_timeout: int = 30
        
    async def register_server(self, server_id: str, server_path: str, server_type: str) -> bool:
        """Register a new MCP server."""
        try:
            server_info = {
                "id": server_id,
                "path": server_path,
                "type": server_type,
                "registered_at": datetime.now(),
                "last_activity": datetime.now(),
                "is_active": False
            }
            
            self.active_servers[server_id] = server_info
            logger.info(f"Registered MCP server: {server_id} ({server_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error registering MCP server {server_id}: {str(e)}")
            return False
    
    async def start_server(self, server_id: str) -> bool:
        """Start an MCP server."""
        try:
            if server_id not in self.active_servers:
                logger.error(f"Server {server_id} not registered")
                return False
            
            server_info = self.active_servers[server_id]
            
            # Create server parameters
            params = StdioServerParameters(
                command=server_info["path"],
                args=[],
                env={}
            )
            
            # Start server session
            async with stdio_client(params) as (read, write):
                session = ClientSession(read, write)
                
                # Initialize session
                await session.initialize()
                
                # Store session info
                server_info.update({
                    "session": session,
                    "is_active": True,
                    "started_at": datetime.now(),
                    "last_activity": datetime.now()
                })
                
                logger.info(f"Started MCP server: {server_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error starting MCP server {server_id}: {str(e)}")
            return False
    
    async def stop_server(self, server_id: str) -> bool:
        """Stop an MCP server."""
        try:
            if server_id not in self.active_servers:
                return True  # Already stopped
            
            server_info = self.active_servers[server_id]
            
            if server_info.get("is_active") and "session" in server_info:
                # Close session
                await server_info["session"].close()
                
                server_info.update({
                    "is_active": False,
                    "stopped_at": datetime.now(),
                    "session": None
                })
                
                logger.info(f"Stopped MCP server: {server_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping MCP server {server_id}: {str(e)}")
            return False
    
    async def call_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any]) -> Optional[CallToolResult]:
        """Call a tool on an MCP server."""
        try:
            if server_id not in self.active_servers:
                logger.error(f"Server {server_id} not found")
                return None
            
            server_info = self.active_servers[server_id]
            
            if not server_info.get("is_active"):
                logger.error(f"Server {server_id} is not active")
                return None
            
            session = server_info["session"]
            
            # Create tool call request
            request = CallToolRequest(
                name=tool_name,
                arguments=arguments
            )
            
            # Call tool
            result = await session.call_tool(request)
            
            # Update last activity
            server_info["last_activity"] = datetime.now()
            
            logger.info(f"Called tool {tool_name} on server {server_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on server {server_id}: {str(e)}")
            return None
    
    async def list_tools(self, server_id: str) -> Optional[List[Tool]]:
        """List available tools on an MCP server."""
        try:
            if server_id not in self.active_servers:
                logger.error(f"Server {server_id} not found")
                return None
            
            server_info = self.active_servers[server_id]
            
            if not server_info.get("is_active"):
                logger.error(f"Server {server_id} is not active")
                return None
            
            session = server_info["session"]
            
            # Create list tools request
            request = ListToolsRequest()
            
            # Get tools
            result = await session.list_tools(request)
            
            # Update last activity
            server_info["last_activity"] = datetime.now()
            
            logger.info(f"Listed {len(result.tools)} tools from server {server_id}")
            return result.tools
            
        except Exception as e:
            logger.error(f"Error listing tools from server {server_id}: {str(e)}")
            return None
    
    async def get_server_status(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an MCP server."""
        try:
            if server_id not in self.active_servers:
                return None
            
            server_info = self.active_servers[server_id]
            
            return {
                "id": server_info["id"],
                "type": server_info["type"],
                "is_active": server_info.get("is_active", False),
                "registered_at": server_info["registered_at"].isoformat(),
                "last_activity": server_info["last_activity"].isoformat(),
                "started_at": server_info.get("started_at", "").isoformat() if server_info.get("started_at") else None
            }
            
        except Exception as e:
            logger.error(f"Error getting status for server {server_id}: {str(e)}")
            return None
    
    async def cleanup_inactive_servers(self, timeout_minutes: int = 30) -> int:
        """Clean up inactive servers."""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
            servers_to_remove = []
            
            for server_id, server_info in self.active_servers.items():
                if (server_info["last_activity"] < cutoff_time and 
                    not server_info.get("is_active")):
                    servers_to_remove.append(server_id)
            
            for server_id in servers_to_remove:
                await self.stop_server(server_id)
                del self.active_servers[server_id]
            
            logger.info(f"Cleaned up {len(servers_to_remove)} inactive servers")
            return len(servers_to_remove)
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive servers: {str(e)}")
            return 0


class DatabaseMCPClient(MCPClient):
    """Specialized MCP client for database operations."""
    
    def __init__(self):
        super().__init__()
        self.database_servers = {
            DatabaseType.POSTGRESQL: "postgres_server",
            DatabaseType.MYSQL: "mysql_server"
        }
    
    async def get_database_server_id(self, database_type: DatabaseType) -> str:
        """Get or create server ID for database type."""
        server_type = self.database_servers.get(database_type)
        if not server_type:
            raise ValueError(f"Unsupported database type: {database_type}")
        
        # Check if server already exists
        for server_id, server_info in self.active_servers.items():
            if server_info["type"] == server_type and server_info.get("is_active"):
                return server_id
        
        # Create new server ID
        server_id = f"{server_type}_{uuid.uuid4().hex[:8]}"
        return server_id
    
    async def start_database_server(self, database_type: DatabaseType) -> Optional[str]:
        """Start database-specific MCP server."""
        try:
            server_type = self.database_servers.get(database_type)
            if not server_type:
                raise ValueError(f"Unsupported database type: {database_type}")
            
            server_id = await self.get_database_server_id(database_type)
            
            # Register server
            server_path = f"src/mcp/servers/{server_type}.py"
            await self.register_server(server_id, server_path, server_type)
            
            # Start server
            success = await self.start_server(server_id)
            if success:
                logger.info(f"Started database server for {database_type.value}")
                return server_id
            else:
                logger.error(f"Failed to start database server for {database_type.value}")
                return None
                
        except Exception as e:
            logger.error(f"Error starting database server for {database_type.value}: {str(e)}")
            return None
    
    async def test_database_connection(self, config: DatabaseConnectionConfig) -> Dict[str, Any]:
        """Test database connection using MCP server."""
        try:
            # Start database server
            server_id = await self.start_database_server(config.database_type)
            if not server_id:
                return {
                    "success": False,
                    "message": f"Failed to start {config.database_type.value} server"
                }
            
            # Call test connection tool
            arguments = {
                "host": config.host,
                "port": config.port,
                "username": config.username,
                "password": config.password,
                "database_name": config.database_name
            }
            
            result = await self.call_tool(server_id, "test_connection", arguments)
            
            if result and result.content:
                # Parse result content
                content = result.content[0]
                if isinstance(content, TextContent):
                    try:
                        return json.loads(content.text)
                    except json.JSONDecodeError:
                        return {
                            "success": False,
                            "message": f"Invalid response from {config.database_type.value} server"
                        }
            
            return {
                "success": False,
                "message": f"No response from {config.database_type.value} server"
            }
            
        except Exception as e:
            logger.error(f"Error testing database connection: {str(e)}")
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}"
            }
        finally:
            # Stop server after test
            if server_id:
                await self.stop_server(server_id)
    
    async def execute_database_query(self, config: DatabaseConnectionConfig, query: str) -> Dict[str, Any]:
        """Execute database query using MCP server."""
        try:
            # Start database server
            server_id = await self.start_database_server(config.database_type)
            if not server_id:
                return {
                    "success": False,
                    "message": f"Failed to start {config.database_type.value} server"
                }
            
            # Call execute query tool
            arguments = {
                "host": config.host,
                "port": config.port,
                "username": config.username,
                "password": config.password,
                "database_name": config.database_name,
                "query": query
            }
            
            result = await self.call_tool(server_id, "execute_query", arguments)
            
            if result and result.content:
                content = result.content[0]
                if isinstance(content, TextContent):
                    try:
                        return json.loads(content.text)
                    except json.JSONDecodeError:
                        return {
                            "success": False,
                            "message": f"Invalid response from {config.database_type.value} server"
                        }
            
            return {
                "success": False,
                "message": f"No response from {config.database_type.value} server"
            }
            
        except Exception as e:
            logger.error(f"Error executing database query: {str(e)}")
            return {
                "success": False,
                "message": f"Query execution failed: {str(e)}"
            }
        finally:
            # Stop server after query
            if server_id:
                await self.stop_server(server_id)


# Global MCP client instance
mcp_client = DatabaseMCPClient()


@asynccontextmanager
async def get_mcp_client():
    """Context manager for MCP client."""
    try:
        yield mcp_client
    finally:
        # Cleanup inactive servers
        await mcp_client.cleanup_inactive_servers() 