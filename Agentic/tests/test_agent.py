"""
Tests for the AgenticAgent class.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from core.agent import AgenticAgent
from config.settings import Settings, AIConfig, DatabaseConfig, LoggingConfig, SecurityConfig


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        ai=AIConfig(provider="openai", api_key="test-key"),
        database=DatabaseConfig(url="sqlite:///test.db"),
        logging=LoggingConfig(level="INFO"),
        security=SecurityConfig(secret_key="test-secret"),
        mcp_servers={},
        tools={},
        session_storage="sqlite",
        workflow_storage="sqlite",
        validation_enabled=True,
        verification_enabled=True,
        max_concurrent_requests=10,
        request_timeout=300
    )


@pytest.fixture
def agent(settings):
    """Create test agent."""
    return AgenticAgent(settings)


@pytest.mark.asyncio
async def test_agent_initialization(agent):
    """Test agent initialization."""
    assert agent is not None
    assert agent.settings is not None
    assert agent.session_manager is not None
    assert agent.workflow_manager is not None
    assert agent.context_manager is not None
    assert agent.mcp_manager is not None
    assert agent.memory_manager is not None
    assert agent.verification_manager is not None


@pytest.mark.asyncio
async def test_process_input_basic(agent):
    """Test basic input processing."""
    response = await agent.process_input("Hello, how are you?")
    
    assert response is not None
    assert "response" in response
    assert "session_id" in response
    assert "status" in response
    assert response["status"] in ["success", "error", "validation_error", "verification_error"]


@pytest.mark.asyncio
async def test_process_input_with_session_id(agent):
    """Test input processing with existing session ID."""
    # Create initial session
    response1 = await agent.process_input("First message")
    session_id = response1["session_id"]
    
    # Process with same session ID
    response2 = await agent.process_input("Second message", session_id=session_id)
    
    assert response2["session_id"] == session_id
    assert response2["status"] in ["success", "error", "validation_error", "verification_error"]


@pytest.mark.asyncio
async def test_session_management(agent):
    """Test session management."""
    # Create session
    response = await agent.process_input("Test message")
    session_id = response["session_id"]
    
    # Get session history
    history = await agent.get_session_history(session_id)
    assert len(history) >= 2  # User message + agent response
    
    # List sessions
    sessions = await agent.list_sessions()
    assert len(sessions) >= 1
    
    # Delete session
    success = await agent.delete_session(session_id)
    assert success is True


@pytest.mark.asyncio
async def test_workflow_tracing(agent):
    """Test workflow tracing."""
    # Process input to create workflow
    response = await agent.process_input("Test workflow")
    session_id = response["session_id"]
    
    # Get workflow trace
    workflow = await agent.get_workflow_trace(session_id)
    assert workflow is not None
    assert len(workflow) >= 1


@pytest.mark.asyncio
async def test_memory_management(agent):
    """Test memory management."""
    # Store memory
    success = await agent.memory_manager.store_memory("test_key", "test_value")
    assert success is True
    
    # Retrieve memory
    value = await agent.memory_manager.retrieve_memory("test_key")
    assert value == "test_value"
    
    # Get memory stats
    stats = await agent.memory_manager.get_memory_stats()
    assert stats is not None
    assert "total_memory_entries" in stats


@pytest.mark.asyncio
async def test_context_analysis(agent):
    """Test context analysis."""
    # Test with file operation intent
    response = await agent.process_input("Load the file /data/test.csv")
    
    assert response is not None
    assert "metadata" in response
    assert "context_analysis" in response["metadata"]
    
    context_analysis = response["metadata"]["context_analysis"]
    assert "intent" in context_analysis
    assert "entities" in context_analysis


@pytest.mark.asyncio
async def test_validation(agent):
    """Test input validation."""
    # Test with validation enabled
    response = await agent.process_input("Valid input")
    assert response["status"] in ["success", "error", "validation_error", "verification_error"]
    
    # Test with empty input
    response = await agent.process_input("")
    assert response["status"] in ["success", "error", "validation_error", "verification_error"]


@pytest.mark.asyncio
async def test_service_verification(agent):
    """Test service verification."""
    # Test with verification enabled
    response = await agent.process_input("Test service verification")
    assert response["status"] in ["success", "error", "validation_error", "verification_error"]


@pytest.mark.asyncio
async def test_mcp_server_management(agent):
    """Test MCP server management."""
    # List servers
    servers = await agent.mcp_manager.list_servers()
    assert isinstance(servers, list)
    
    # Test server health check (should handle missing servers gracefully)
    if agent.settings.mcp_servers:
        server_name = list(agent.settings.mcp_servers.keys())[0]
        health = await agent.mcp_manager.check_server_health(server_name)
        assert isinstance(health, dict)


@pytest.mark.asyncio
async def test_agent_shutdown(agent):
    """Test agent shutdown."""
    await agent.shutdown()
    # Should complete without errors


@pytest.mark.asyncio
async def test_error_handling(agent):
    """Test error handling."""
    # Test with invalid input that might cause errors
    response = await agent.process_input("Invalid input that might cause errors")
    assert response is not None
    assert "status" in response


@pytest.mark.asyncio
async def test_session_persistence(agent):
    """Test session persistence."""
    # Create session
    response = await agent.process_input("Test persistence")
    session_id = response["session_id"]
    
    # Verify session was saved
    session = await agent.session_manager.get_session(session_id)
    assert session is not None
    assert session["session_id"] == session_id
    
    # Test session export
    export_data = await agent.session_manager.export_session(session_id)
    assert export_data is not None
    assert export_data["session_id"] == session_id


@pytest.mark.asyncio
async def test_workflow_persistence(agent):
    """Test workflow persistence."""
    # Process input to create workflow
    response = await agent.process_input("Test workflow persistence")
    session_id = response["session_id"]
    
    # Get workflow trace
    workflow = await agent.get_workflow_trace(session_id)
    assert workflow is not None
    
    # Test workflow export
    if workflow:
        workflow_id = workflow[0].get("workflow_id")
        if workflow_id:
            export_data = await agent.workflow_manager.export_workflow(workflow_id)
            assert export_data is not None 