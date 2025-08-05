"""
Core state management for the LangGraph agent.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AgentRole(str, Enum):
    """Agent roles for different types of operations."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(BaseModel):
    """Message structure for the agent conversation."""
    role: AgentRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


class ToolResult(BaseModel):
    """Result from tool execution."""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0


class AgentState(BaseModel):
    """Main state for the LangGraph agent."""
    # Conversation history
    messages: List[Message] = Field(default_factory=list)
    
    # Current user input
    user_input: str = ""
    
    # Tool execution results
    tool_results: List[ToolResult] = Field(default_factory=list)
    
    # Agent configuration
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # Current iteration count
    iteration: int = 0
    
    # Maximum iterations allowed
    max_iterations: int = 10
    
    # Agent memory/context
    memory: Dict[str, Any] = Field(default_factory=dict)
    
    # Current task or goal
    current_task: Optional[str] = None
    
    # Execution status
    is_complete: bool = False
    error: Optional[str] = None
    
    # Performance metrics
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Tool and MCP extension status
    enabled_tools: List[str] = Field(default_factory=list)
    enabled_mcp_servers: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


def create_initial_state(config: Dict[str, Any]) -> AgentState:
    """Create initial agent state from configuration."""
    return AgentState(
        config=config,
        max_iterations=config.get("behavior", {}).get("max_iterations", 10),
        enabled_tools=[],
        enabled_mcp_servers=[],
        start_time=datetime.now()
    )


def add_message(state: AgentState, role: AgentRole, content: str, metadata: Optional[Dict[str, Any]] = None) -> AgentState:
    """Add a message to the conversation history."""
    message = Message(role=role, content=content, metadata=metadata)
    state.messages.append(message)
    return state


def add_tool_result(state: AgentState, tool_result: ToolResult) -> AgentState:
    """Add a tool execution result to the state."""
    state.tool_results.append(tool_result)
    return state


def update_iteration(state: AgentState) -> AgentState:
    """Update the iteration count."""
    state.iteration += 1
    return state


def mark_complete(state: AgentState, error: Optional[str] = None) -> AgentState:
    """Mark the agent execution as complete."""
    state.is_complete = True
    state.end_time = datetime.now()
    if error:
        state.error = error
    return state 