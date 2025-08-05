"""
LangGraph workflows for Database Interface Agent.
Defines the stateful workflows for agent interactions.
"""

from typing import Dict, Any, List
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.agent.state import AgentState, AgentStatus, ConnectionStatus, StateManager
from src.tools.connection_tools import get_connection_tools
from src.mcp.client import mcp_client
from src.storage.session_store import get_session_store
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseAgentWorkflows:
    """Workflow definitions for Database Interface Agent."""
    
    def __init__(self):
        self.tools = get_connection_tools()
        self.tool_node = ToolNode(self.tools)
    
    def create_workflow(self) -> StateGraph:
        """Create the main agent workflow."""
        
        # Create workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("initialize", self.initialize_agent)
        workflow.add_node("collect_credentials", self.collect_credentials)
        workflow.add_node("validate_credentials", self.validate_credentials)
        workflow.add_node("test_connection", self.test_connection)
        workflow.add_node("connection_success", self.connection_success)
        workflow.add_node("connection_failed", self.connection_failed)
        workflow.add_node("ready_state", self.ready_state)
        workflow.add_node("error_handling", self.error_handling)
        workflow.add_node("cleanup", self.cleanup)
        
        # Add tool node
        workflow.add_node("tools", self.tool_node)
        
        # Define edges
        workflow.set_entry_point("initialize")
        
        # Initialize -> Collect Credentials or Error
        workflow.add_conditional_edges(
            "initialize",
            self.should_collect_credentials,
            {
                "collect_credentials": "collect_credentials",
                "error": "error_handling"
            }
        )
        
        # Collect Credentials -> Validate or Error
        workflow.add_conditional_edges(
            "collect_credentials",
            self.should_validate_credentials,
            {
                "validate": "validate_credentials",
                "error": "error_handling"
            }
        )
        
        # Validate Credentials -> Test Connection or Error
        workflow.add_conditional_edges(
            "validate_credentials",
            self.should_test_connection,
            {
                "test": "test_connection",
                "error": "error_handling"
            }
        )
        
        # Test Connection -> Success or Failed
        workflow.add_conditional_edges(
            "test_connection",
            self.connection_test_result,
            {
                "success": "connection_success",
                "failed": "connection_failed"
            }
        )
        
        # Connection Success -> Ready State
        workflow.add_edge("connection_success", "ready_state")
        
        # Connection Failed -> Error Handling
        workflow.add_edge("connection_failed", "error_handling")
        
        # Ready State -> End (with continue flag)
        workflow.add_conditional_edges(
            "ready_state",
            self.should_continue,
            {
                "continue": "ready_state",
                "end": END
            }
        )
        
        # Error Handling -> Cleanup
        workflow.add_edge("error_handling", "cleanup")
        
        # Cleanup -> End
        workflow.add_edge("cleanup", END)
        
        return workflow
    
    async def initialize_agent(self, state: AgentState) -> AgentState:
        """Initialize the agent."""
        try:
            logger.info(f"Initializing agent for reference ID: {state.reference_id}")
            
            # Get or create session
            session_store = await get_session_store()
            
            if state.reference_id:
                # Try to retrieve existing session
                session = await session_store.get_session_by_reference_id(state.reference_id)
                if session:
                    state.update_session(session)
                    state.agent_status = AgentStatus.COLLECTING_CREDENTIALS
                    state.current_step = "collect_credentials"
                    state.response_message = f"Session {state.reference_id} retrieved. Ready to continue."
                else:
                    # Create new session
                    session = await session_store.create_session()
                    state.update_session(session)
                    state.agent_status = AgentStatus.COLLECTING_CREDENTIALS
                    state.current_step = "collect_credentials"
                    state.response_message = f"New session created: {session.reference_id}. Please provide database credentials."
            else:
                # Create new session
                session = await session_store.create_session()
                state.update_session(session)
                state.agent_status = AgentStatus.COLLECTING_CREDENTIALS
                state.current_step = "collect_credentials"
                state.response_message = f"New session created: {session.reference_id}. Please provide database credentials."
            
            # Add action log
            state.add_action_log("agent_initialized", {
                "reference_id": state.reference_id,
                "session_id": session.session_id if session else None
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error initializing agent: {str(e)}")
            state.agent_status = AgentStatus.ERROR
            state.error_message = f"Initialization failed: {str(e)}"
            state.current_step = "error_handling"
            return state
    
    async def collect_credentials(self, state: AgentState) -> AgentState:
        """Collect database credentials."""
        try:
            logger.info(f"Collecting credentials for session: {state.reference_id}")
            
            if state.structured_input:
                # Use structured input
                credentials = state.structured_input
                state.agent_status = AgentStatus.TESTING_CONNECTION
                state.current_step = "validate_credentials"
                state.response_message = "Credentials received from structured input. Validating..."
            else:
                # Interactive mode - ask for credentials
                state.agent_status = AgentStatus.COLLECTING_CREDENTIALS
                state.current_step = "collect_credentials"
                state.response_message = (
                    "Please provide database credentials:\n"
                    "- Database type (postgresql/mysql)\n"
                    "- Host\n"
                    "- Port\n"
                    "- Username\n"
                    "- Password\n"
                    "- Database name (optional)"
                )
            
            # Add action log
            state.add_action_log("credentials_collection_started", {
                "interactive": state.is_interactive,
                "has_structured_input": bool(state.structured_input)
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error collecting credentials: {str(e)}")
            state.agent_status = AgentStatus.ERROR
            state.error_message = f"Credential collection failed: {str(e)}"
            state.current_step = "error_handling"
            return state
    
    async def validate_credentials(self, state: AgentState) -> AgentState:
        """Validate collected credentials."""
        try:
            logger.info(f"Validating credentials for session: {state.reference_id}")
            
            # Use validation tool
            validation_result = await self.tool_node.invoke({
                "name": "validate_credentials",
                "arguments": {"credentials": state.structured_input or {}}
            })
            
            if validation_result.get("valid", False):
                state.agent_status = AgentStatus.TESTING_CONNECTION
                state.current_step = "test_connection"
                state.response_message = "Credentials validated successfully. Testing connection..."
            else:
                state.agent_status = AgentStatus.ERROR
                state.error_message = f"Credential validation failed: {validation_result.get('errors', [])}"
                state.current_step = "error_handling"
            
            # Add action log
            state.add_action_log("credentials_validated", {
                "valid": validation_result.get("valid", False),
                "errors": validation_result.get("errors", [])
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error validating credentials: {str(e)}")
            state.agent_status = AgentStatus.ERROR
            state.error_message = f"Credential validation failed: {str(e)}"
            state.current_step = "error_handling"
            return state
    
    async def test_connection(self, state: AgentState) -> AgentState:
        """Test database connection."""
        try:
            logger.info(f"Testing connection for session: {state.reference_id}")
            
            # Use connection testing tool
            test_result = await self.tool_node.invoke({
                "name": "test_connection",
                "arguments": {"connection_config": state.structured_input or {}}
            })
            
            if test_result.get("success", False):
                state.connection_status = ConnectionStatus.SUCCESS
                state.connection_test_result = test_result
                state.agent_status = AgentStatus.CONNECTED
                state.current_step = "connection_success"
                state.response_message = f"Connection successful! {test_result.get('message', '')}"
            else:
                state.connection_status = ConnectionStatus.FAILED
                state.connection_error = test_result.get("message", "Unknown error")
                state.agent_status = AgentStatus.ERROR
                state.current_step = "connection_failed"
                state.response_message = f"Connection failed: {test_result.get('message', '')}"
            
            # Add action log
            state.add_action_log("connection_tested", {
                "success": test_result.get("success", False),
                "database_type": test_result.get("database_type"),
                "host": test_result.get("host"),
                "port": test_result.get("port")
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            state.connection_status = ConnectionStatus.FAILED
            state.connection_error = str(e)
            state.agent_status = AgentStatus.ERROR
            state.current_step = "connection_failed"
            state.response_message = f"Connection test failed: {str(e)}"
            return state
    
    async def connection_success(self, state: AgentState) -> AgentState:
        """Handle successful connection."""
        try:
            logger.info(f"Connection successful for session: {state.reference_id}")
            
            # Update session with connection info
            if state.session:
                state.session.connection_status = ConnectionStatus.SUCCESS
                state.session.connection_tested_at = datetime.now()
                state.session.agent_status = AgentStatus.CONNECTED
                
                # Update session in store
                session_store = await get_session_store()
                await session_store.update_session(state.session)
            
            state.agent_status = AgentStatus.READY
            state.current_step = "ready_state"
            state.response_message = (
                f"Database connection established successfully!\n"
                f"Session: {state.reference_id}\n"
                f"Status: Ready for database operations"
            )
            
            # Add action log
            state.add_action_log("connection_established", {
                "reference_id": state.reference_id,
                "database_type": state.connection_test_result.get("database_type") if state.connection_test_result else None
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error handling connection success: {str(e)}")
            state.agent_status = AgentStatus.ERROR
            state.error_message = f"Error handling connection success: {str(e)}"
            state.current_step = "error_handling"
            return state
    
    async def connection_failed(self, state: AgentState) -> AgentState:
        """Handle failed connection."""
        try:
            logger.error(f"Connection failed for session: {state.reference_id}")
            
            # Update session with error info
            if state.session:
                state.session.connection_status = ConnectionStatus.FAILED
                state.session.connection_error = state.connection_error
                state.session.agent_status = AgentStatus.ERROR
                
                # Update session in store
                session_store = await get_session_store()
                await session_store.update_session(state.session)
            
            state.agent_status = AgentStatus.ERROR
            state.current_step = "error_handling"
            state.response_message = f"Connection failed: {state.connection_error}"
            
            # Add action log
            state.add_action_log("connection_failed", {
                "reference_id": state.reference_id,
                "error": state.connection_error
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error handling connection failure: {str(e)}")
            state.agent_status = AgentStatus.ERROR
            state.error_message = f"Error handling connection failure: {str(e)}"
            state.current_step = "error_handling"
            return state
    
    async def ready_state(self, state: AgentState) -> AgentState:
        """Handle ready state for database operations."""
        try:
            logger.info(f"Agent ready for session: {state.reference_id}")
            
            # Update session status
            if state.session:
                state.session.agent_status = AgentStatus.READY
                session_store = await get_session_store()
                await session_store.update_session(state.session)
            
            state.agent_status = AgentStatus.READY
            state.current_step = "ready_state"
            state.response_message = (
                f"Agent is ready for database operations!\n"
                f"Session: {state.reference_id}\n"
                f"Available operations:\n"
                f"- Execute queries\n"
                f"- List tables\n"
                f"- Get schema information\n"
                f"- Test connection"
            )
            
            # Add action log
            state.add_action_log("agent_ready", {
                "reference_id": state.reference_id
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in ready state: {str(e)}")
            state.agent_status = AgentStatus.ERROR
            state.error_message = f"Error in ready state: {str(e)}"
            state.current_step = "error_handling"
            return state
    
    async def error_handling(self, state: AgentState) -> AgentState:
        """Handle errors in the workflow."""
        try:
            logger.error(f"Error handling for session: {state.reference_id}")
            
            # Update session with error info
            if state.session:
                state.session.agent_status = AgentStatus.ERROR
                state.session.connection_error = state.error_message
                
                # Update session in store
                session_store = await get_session_store()
                await session_store.update_session(state.session)
            
            state.agent_status = AgentStatus.ERROR
            state.current_step = "error_handling"
            state.response_message = f"An error occurred: {state.error_message}"
            
            # Add action log
            state.add_action_log("error_handled", {
                "reference_id": state.reference_id,
                "error": state.error_message
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in error handling: {str(e)}")
            state.agent_status = AgentStatus.ERROR
            state.error_message = f"Error in error handling: {str(e)}"
            state.current_step = "cleanup"
            return state
    
    async def cleanup(self, state: AgentState) -> AgentState:
        """Clean up resources."""
        try:
            logger.info(f"Cleaning up session: {state.reference_id}")
            
            # Stop MCP servers if active
            if state.mcp_server_active and state.mcp_server_id:
                await mcp_client.stop_server(state.mcp_server_id)
                state.mcp_server_active = False
                state.mcp_server_id = None
            
            # Update session status
            if state.session:
                state.session.is_active = False
                state.session.agent_status = AgentStatus.DISCONNECTED
                
                # Update session in store
                session_store = await get_session_store()
                await session_store.update_session(state.session)
            
            state.agent_status = AgentStatus.DISCONNECTED
            state.current_step = "cleanup"
            state.response_message = "Session cleaned up successfully."
            state.should_continue = False
            
            # Add action log
            state.add_action_log("cleanup_completed", {
                "reference_id": state.reference_id
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in cleanup: {str(e)}")
            state.agent_status = AgentStatus.ERROR
            state.error_message = f"Error in cleanup: {str(e)}"
            state.should_continue = False
            return state
    
    # Conditional edge functions
    def should_collect_credentials(self, state: AgentState) -> str:
        """Determine if should collect credentials."""
        if state.agent_status == AgentStatus.ERROR:
            return "error"
        return "collect_credentials"
    
    def should_validate_credentials(self, state: AgentState) -> str:
        """Determine if should validate credentials."""
        if state.agent_status == AgentStatus.ERROR:
            return "error"
        if state.structured_input:
            return "validate"
        return "collect_credentials"
    
    def should_test_connection(self, state: AgentState) -> str:
        """Determine if should test connection."""
        if state.agent_status == AgentStatus.ERROR:
            return "error"
        return "test"
    
    def connection_test_result(self, state: AgentState) -> str:
        """Determine connection test result."""
        if state.connection_status == ConnectionStatus.SUCCESS:
            return "success"
        return "failed"
    
    def should_continue(self, state: AgentState) -> str:
        """Determine if should continue."""
        if state.should_continue:
            return "continue"
        return "end"


# Global workflow instance
workflows = DatabaseAgentWorkflows()


def get_workflow() -> StateGraph:
    """Get the main agent workflow."""
    return workflows.create_workflow() 