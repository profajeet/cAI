"""
State management for the Database Interface Agent.
Defines the state structure used by LangGraph workflows.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field

from config.database_config import DatabaseConnectionConfig, DatabaseType


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    INITIALIZING = "initializing"
    COLLECTING_CREDENTIALS = "collecting_credentials"
    TESTING_CONNECTION = "testing_connection"
    CONNECTED = "connected"
    ERROR = "error"
    READY = "ready"
    DISCONNECTED = "disconnected"


class ConnectionStatus(str, Enum):
    """Connection status enumeration."""
    PENDING = "pending"
    TESTING = "testing"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class SessionState(BaseModel):
    """Session state for tracking user interactions."""
    
    session_id: str
    reference_id: str
    created_at: datetime
    last_accessed: datetime
    ttl: int  # Time to live in seconds
    is_active: bool = True
    
    # User interaction state
    current_step: str = "initialization"
    collected_data: Dict[str, Any] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    
    # Connection state
    connection_config: Optional[DatabaseConnectionConfig] = None
    connection_status: ConnectionStatus = ConnectionStatus.PENDING
    connection_error: Optional[str] = None
    connection_tested_at: Optional[datetime] = None
    
    # Agent state
    agent_status: AgentStatus = AgentStatus.INITIALIZING
    agent_messages: List[str] = Field(default_factory=list)
    
    # MCP state
    mcp_server_active: bool = False
    mcp_server_id: Optional[str] = None
    mcp_last_activity: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True


class AgentState(BaseModel):
    """Main agent state for LangGraph workflows."""
    
    # Session management
    session: Optional[SessionState] = None
    reference_id: Optional[str] = None
    
    # Current interaction state
    user_input: Optional[str] = None
    structured_input: Optional[Dict[str, Any]] = None
    is_interactive: bool = True
    
    # Database connection state
    database_type: Optional[DatabaseType] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database_name: Optional[str] = None
    
    # Connection testing state
    connection_config: Optional[DatabaseConnectionConfig] = None
    connection_status: ConnectionStatus = ConnectionStatus.PENDING
    connection_error: Optional[str] = None
    connection_test_result: Optional[Dict[str, Any]] = None
    
    # Agent workflow state
    current_step: str = "initialization"
    next_step: Optional[str] = None
    agent_status: AgentStatus = AgentStatus.INITIALIZING
    error_message: Optional[str] = None
    
    # MCP integration state
    mcp_client_ready: bool = False
    mcp_server_active: bool = False
    mcp_server_id: Optional[str] = None
    
    # Output and response state
    response_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    should_continue: bool = True
    
    # Audit and logging
    timestamp: datetime = Field(default_factory=datetime.now)
    action_log: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True
    
    def update_session(self, session: SessionState) -> None:
        """Update the session state."""
        self.session = session
        self.reference_id = session.reference_id
    
    def add_action_log(self, action: str, details: Dict[str, Any]) -> None:
        """Add an action to the audit log."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "step": self.current_step,
            "status": self.agent_status
        }
        self.action_log.append(log_entry)
    
    def set_connection_config(self, config: DatabaseConnectionConfig) -> None:
        """Set the database connection configuration."""
        self.connection_config = config
        self.database_type = config.database_type
        self.host = config.host
        self.port = config.port
        self.username = config.username
        self.password = config.password
        self.database_name = config.database_name
    
    def get_connection_summary(self) -> Dict[str, Any]:
        """Get a summary of the connection configuration (without sensitive data)."""
        if not self.connection_config:
            return {}
        
        return {
            "database_type": self.connection_config.database_type.value,
            "host": self.connection_config.host,
            "port": self.connection_config.port,
            "database_name": self.connection_config.database_name,
            "ssl_mode": self.connection_config.ssl_mode,
            "connection_status": self.connection_status.value,
            "connection_tested_at": self.connection_tested_at.isoformat() if self.connection_tested_at else None
        }
    
    def is_connection_ready(self) -> bool:
        """Check if the connection is ready for use."""
        return (
            self.connection_config is not None and
            self.connection_status == ConnectionStatus.SUCCESS and
            self.agent_status in [AgentStatus.CONNECTED, AgentStatus.READY]
        )
    
    def reset_connection_state(self) -> None:
        """Reset connection-related state."""
        self.connection_config = None
        self.connection_status = ConnectionStatus.PENDING
        self.connection_error = None
        self.connection_test_result = None
        self.agent_status = AgentStatus.INITIALIZING
        self.mcp_server_active = False
        self.mcp_server_id = None


class StateManager:
    """Manages state transitions and validation."""
    
    @staticmethod
    def create_initial_state(reference_id: Optional[str] = None, is_interactive: bool = True) -> AgentState:
        """Create initial agent state."""
        return AgentState(
            reference_id=reference_id,
            is_interactive=is_interactive,
            current_step="initialization",
            agent_status=AgentStatus.INITIALIZING
        )
    
    @staticmethod
    def validate_state_transition(current_state: AgentState, new_status: AgentStatus) -> bool:
        """Validate if a state transition is allowed."""
        valid_transitions = {
            AgentStatus.INITIALIZING: [AgentStatus.COLLECTING_CREDENTIALS, AgentStatus.ERROR],
            AgentStatus.COLLECTING_CREDENTIALS: [AgentStatus.TESTING_CONNECTION, AgentStatus.ERROR],
            AgentStatus.TESTING_CONNECTION: [AgentStatus.CONNECTED, AgentStatus.ERROR, AgentStatus.TIMEOUT],
            AgentStatus.CONNECTED: [AgentStatus.READY, AgentStatus.DISCONNECTED, AgentStatus.ERROR],
            AgentStatus.READY: [AgentStatus.DISCONNECTED, AgentStatus.ERROR],
            AgentStatus.ERROR: [AgentStatus.INITIALIZING, AgentStatus.DISCONNECTED],
            AgentStatus.DISCONNECTED: [AgentStatus.INITIALIZING]
        }
        
        allowed_transitions = valid_transitions.get(current_state.agent_status, [])
        return new_status in allowed_transitions
    
    @staticmethod
    def get_next_step(current_step: str, status: AgentStatus) -> str:
        """Determine the next step based on current state."""
        step_mapping = {
            "initialization": "collect_credentials" if status == AgentStatus.COLLECTING_CREDENTIALS else "error_handling",
            "collect_credentials": "test_connection" if status == AgentStatus.TESTING_CONNECTION else "error_handling",
            "test_connection": "connection_success" if status == AgentStatus.CONNECTED else "connection_failed",
            "connection_success": "ready_state",
            "connection_failed": "error_handling",
            "ready_state": "wait_for_commands",
            "error_handling": "cleanup"
        }
        
        return step_mapping.get(current_step, "error_handling") 