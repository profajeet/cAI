"""
Main Database Interface Agent class.
Orchestrates all components and provides the main interface.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

from src.agent.state import AgentState, StateManager, AgentStatus
from src.agent.workflows import get_workflow
from src.mcp.client import mcp_client
from src.storage.session_store import get_session_store
from src.utils.logger import get_logger, AgentLogger

logger = get_logger(__name__)


class DatabaseInterfaceAgent:
    """Main Database Interface Agent class."""
    
    def __init__(self):
        self.workflow: Optional[StateGraph] = None
        self.memory_saver = MemorySaver()
        self.agent_logger: Optional[AgentLogger] = None
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the agent."""
        try:
            logger.info("Initializing Database Interface Agent")
            
            # Initialize session store
            session_store = await get_session_store()
            if not session_store.redis_client:
                await session_store.initialize()
            
            # Initialize MCP client
            # (MCP client is initialized on import)
            
            # Create workflow
            self.workflow = get_workflow()
            
            # Compile workflow
            self.app = self.workflow.compile(checkpointer=self.memory_saver)
            
            self.is_initialized = True
            logger.info("Database Interface Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            return False
    
    async def create_session(self, ttl: Optional[int] = None) -> Dict[str, Any]:
        """Create a new agent session."""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Create session in store
            session_store = await get_session_store()
            session = await session_store.create_session(ttl)
            
            # Create initial state
            initial_state = StateManager.create_initial_state(
                reference_id=session.reference_id,
                is_interactive=True
            )
            
            # Initialize agent logger
            self.agent_logger = AgentLogger(
                agent_id=f"agent_{session.reference_id}",
                session_id=session.session_id
            )
            
            self.agent_logger.session_created(session.reference_id, session.ttl)
            
            return {
                "success": True,
                "reference_id": session.reference_id,
                "session_id": session.session_id,
                "ttl": session.ttl,
                "created_at": session.created_at.isoformat(),
                "message": f"Session created successfully: {session.reference_id}"
            }
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create session"
            }
    
    async def connect_database(
        self,
        reference_id: str,
        credentials: Dict[str, Any],
        is_interactive: bool = False
    ) -> Dict[str, Any]:
        """Connect to database using provided credentials."""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Create initial state
            initial_state = StateManager.create_initial_state(
                reference_id=reference_id,
                is_interactive=is_interactive
            )
            
            # Set structured input if provided
            if credentials:
                initial_state.structured_input = credentials
            
            # Initialize agent logger
            self.agent_logger = AgentLogger(
                agent_id=f"agent_{reference_id}",
                session_id=reference_id
            )
            
            # Run workflow
            config = {"configurable": {"thread_id": reference_id}}
            result = await self.app.ainvoke(initial_state, config)
            
            # Extract final state
            final_state = result.get("__end__", initial_state)
            
            # Log connection attempt
            if final_state.connection_status.value == "success":
                self.agent_logger.connection_test(
                    credentials.get("database_type", "unknown"),
                    credentials.get("host", "unknown"),
                    credentials.get("port", 0),
                    True
                )
            else:
                self.agent_logger.connection_test(
                    credentials.get("database_type", "unknown"),
                    credentials.get("host", "unknown"),
                    credentials.get("port", 0),
                    False,
                    error=final_state.connection_error
                )
            
            return {
                "success": final_state.connection_status.value == "success",
                "reference_id": reference_id,
                "status": final_state.agent_status.value,
                "message": final_state.response_message,
                "connection_status": final_state.connection_status.value,
                "error": final_state.connection_error,
                "connection_test_result": final_state.connection_test_result
            }
            
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            return {
                "success": False,
                "reference_id": reference_id,
                "error": str(e),
                "message": "Failed to connect to database"
            }
    
    async def execute_query(
        self,
        reference_id: str,
        query: str
    ) -> Dict[str, Any]:
        """Execute a database query."""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Get session
            session_store = await get_session_store()
            session = await session_store.get_session_by_reference_id(reference_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found",
                    "message": f"Session {reference_id} not found or expired"
                }
            
            if not session.connection_config:
                return {
                    "success": False,
                    "error": "No connection configuration",
                    "message": "No database connection configured for this session"
                }
            
            # Execute query using MCP
            result = await mcp_client.execute_database_query(
                session.connection_config,
                query
            )
            
            # Log query execution
            if self.agent_logger:
                self.agent_logger.tool_executed(
                    "execute_query",
                    result.get("success", False),
                    query=query,
                    row_count=result.get("data", {}).get("row_count", 0)
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute query"
            }
    
    async def list_tables(self, reference_id: str) -> Dict[str, Any]:
        """List tables in the database."""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Get session
            session_store = await get_session_store()
            session = await session_store.get_session_by_reference_id(reference_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found",
                    "message": f"Session {reference_id} not found or expired"
                }
            
            if not session.connection_config:
                return {
                    "success": False,
                    "error": "No connection configuration",
                    "message": "No database connection configured for this session"
                }
            
            # List tables using MCP
            result = await mcp_client.call_tool(
                session.mcp_server_id or "temp",
                "list_tables",
                {
                    "host": session.connection_config.host,
                    "port": session.connection_config.port,
                    "username": session.connection_config.username,
                    "password": session.connection_config.password,
                    "database_name": session.connection_config.database_name
                }
            )
            
            # Log table listing
            if self.agent_logger:
                self.agent_logger.tool_executed(
                    "list_tables",
                    True,
                    table_count=len(result.get("tables", []))
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing tables: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to list tables"
            }
    
    async def get_schema(
        self,
        reference_id: str,
        table_name: str
    ) -> Dict[str, Any]:
        """Get schema information for a table."""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Get session
            session_store = await get_session_store()
            session = await session_store.get_session_by_reference_id(reference_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found",
                    "message": f"Session {reference_id} not found or expired"
                }
            
            if not session.connection_config:
                return {
                    "success": False,
                    "error": "No connection configuration",
                    "message": "No database connection configured for this session"
                }
            
            # Get schema using MCP
            result = await mcp_client.call_tool(
                session.mcp_server_id or "temp",
                "get_schema",
                {
                    "host": session.connection_config.host,
                    "port": session.connection_config.port,
                    "username": session.connection_config.username,
                    "password": session.connection_config.password,
                    "database_name": session.connection_config.database_name,
                    "table_name": table_name
                }
            )
            
            # Log schema retrieval
            if self.agent_logger:
                self.agent_logger.tool_executed(
                    "get_schema",
                    True,
                    table_name=table_name,
                    column_count=len(result.get("columns", []))
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting schema: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get schema"
            }
    
    async def get_session_info(self, reference_id: str) -> Dict[str, Any]:
        """Get information about a session."""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Get session
            session_store = await get_session_store()
            session = await session_store.get_session_by_reference_id(reference_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found",
                    "message": f"Session {reference_id} not found or expired"
                }
            
            return {
                "success": True,
                "session": {
                    "reference_id": session.reference_id,
                    "session_id": session.session_id,
                    "created_at": session.created_at.isoformat(),
                    "last_accessed": session.last_accessed.isoformat(),
                    "ttl": session.ttl,
                    "is_active": session.is_active,
                    "agent_status": session.agent_status.value,
                    "connection_status": session.connection_status.value,
                    "connection_tested_at": session.connection_tested_at.isoformat() if session.connection_tested_at else None,
                    "mcp_server_active": session.mcp_server_active,
                    "mcp_server_id": session.mcp_server_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting session info: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get session information"
            }
    
    async def list_sessions(self) -> Dict[str, Any]:
        """List all active sessions."""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Get sessions from store
            session_store = await get_session_store()
            sessions = await session_store.list_active_sessions()
            
            return {
                "success": True,
                "sessions": sessions,
                "count": len(sessions)
            }
            
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to list sessions"
            }
    
    async def delete_session(self, reference_id: str) -> Dict[str, Any]:
        """Delete a session."""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Delete session from store
            session_store = await get_session_store()
            success = await session_store.delete_session(reference_id)
            
            if success:
                # Log session deletion
                if self.agent_logger:
                    self.agent_logger.info(f"Session {reference_id} deleted")
                
                return {
                    "success": True,
                    "message": f"Session {reference_id} deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Session not found",
                    "message": f"Session {reference_id} not found"
                }
            
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to delete session"
            }
    
    async def cleanup(self) -> None:
        """Clean up agent resources."""
        try:
            logger.info("Cleaning up Database Interface Agent")
            
            # Clean up MCP servers
            await mcp_client.cleanup_inactive_servers()
            
            # Clean up session store
            session_store = await get_session_store()
            await session_store.close()
            
            logger.info("Database Interface Agent cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


# Global agent instance
agent = DatabaseInterfaceAgent()


async def get_agent() -> DatabaseInterfaceAgent:
    """Get the global agent instance."""
    if not agent.is_initialized:
        await agent.initialize()
    return agent 