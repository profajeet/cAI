"""
Tests for Database Interface Agent.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from src.agent.database_agent import DatabaseInterfaceAgent
from src.agent.state import AgentState, AgentStatus, ConnectionStatus
from src.utils.validators import InputValidator, ConnectionValidator


class TestDatabaseInterfaceAgent:
    """Test cases for DatabaseInterfaceAgent."""
    
    @pytest.fixture
    async def agent(self):
        """Create a test agent instance."""
        agent = DatabaseInterfaceAgent()
        # Mock the initialization to avoid external dependencies
        with patch.object(agent, 'initialize', return_value=True):
            agent.is_initialized = True
            yield agent
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization."""
        agent = DatabaseInterfaceAgent()
        assert agent.is_initialized == False
        assert agent.workflow is None
    
    @pytest.mark.asyncio
    async def test_create_session(self, agent):
        """Test session creation."""
        with patch('src.storage.session_store.get_session_store') as mock_get_store:
            mock_store = AsyncMock()
            mock_get_store.return_value = mock_store
            
            # Mock session creation
            mock_session = Mock()
            mock_session.reference_id = "test_ref_123"
            mock_session.session_id = "test_session_456"
            mock_session.ttl = 3600
            mock_session.created_at.isoformat.return_value = "2024-01-01T00:00:00"
            mock_store.create_session.return_value = mock_session
            
            result = await agent.create_session()
            
            assert result["success"] == True
            assert result["reference_id"] == "test_ref_123"
            assert result["session_id"] == "test_session_456"
            assert result["ttl"] == 3600
    
    @pytest.mark.asyncio
    async def test_connect_database_success(self, agent):
        """Test successful database connection."""
        with patch('src.storage.session_store.get_session_store') as mock_get_store, \
             patch.object(agent, 'app') as mock_app:
            
            mock_store = AsyncMock()
            mock_get_store.return_value = mock_store
            
            # Mock workflow result
            mock_state = Mock()
            mock_state.connection_status.value = "success"
            mock_state.agent_status.value = "ready"
            mock_state.response_message = "Connection successful"
            mock_state.connection_error = None
            mock_state.connection_test_result = {"version": "test"}
            
            mock_app.ainvoke.return_value = {"__end__": mock_state}
            
            credentials = {
                "database_type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "username": "test",
                "password": "test"
            }
            
            result = await agent.connect_database("test_ref", credentials)
            
            assert result["success"] == True
            assert result["status"] == "ready"
            assert "Connection successful" in result["message"]
    
    @pytest.mark.asyncio
    async def test_connect_database_failure(self, agent):
        """Test failed database connection."""
        with patch('src.storage.session_store.get_session_store') as mock_get_store, \
             patch.object(agent, 'app') as mock_app:
            
            mock_store = AsyncMock()
            mock_get_store.return_value = mock_store
            
            # Mock workflow result with failure
            mock_state = Mock()
            mock_state.connection_status.value = "failed"
            mock_state.agent_status.value = "error"
            mock_state.response_message = "Connection failed"
            mock_state.connection_error = "Authentication failed"
            mock_state.connection_test_result = None
            
            mock_app.ainvoke.return_value = {"__end__": mock_state}
            
            credentials = {
                "database_type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "username": "wrong",
                "password": "wrong"
            }
            
            result = await agent.connect_database("test_ref", credentials)
            
            assert result["success"] == False
            assert result["status"] == "error"
            assert "Connection failed" in result["message"]
            assert result["error"] == "Authentication failed"


class TestInputValidator:
    """Test cases for InputValidator."""
    
    def test_valid_host_ip(self):
        """Test valid IP address."""
        assert InputValidator.is_valid_host("192.168.1.1") == True
        assert InputValidator.is_valid_host("127.0.0.1") == True
        assert InputValidator.is_valid_host("::1") == True
    
    def test_valid_host_hostname(self):
        """Test valid hostname."""
        assert InputValidator.is_valid_host("localhost") == True
        assert InputValidator.is_valid_host("example.com") == True
        assert InputValidator.is_valid_host("db-server-01") == True
    
    def test_invalid_host(self):
        """Test invalid host."""
        assert InputValidator.is_valid_host("") == False
        assert InputValidator.is_valid_host("invalid@host") == False
        assert InputValidator.is_valid_host("a" * 300) == False  # Too long
    
    def test_valid_port(self):
        """Test valid port numbers."""
        assert InputValidator.is_valid_port(1024) == True
        assert InputValidator.is_valid_port(5432) == True
        assert InputValidator.is_valid_port(65535) == True
    
    def test_invalid_port(self):
        """Test invalid port numbers."""
        assert InputValidator.is_valid_port(0) == False
        assert InputValidator.is_valid_port(1023) == False
        assert InputValidator.is_valid_port(65536) == False
    
    def test_valid_username(self):
        """Test valid usernames."""
        assert InputValidator.is_valid_username("user123") == True
        assert InputValidator.is_valid_username("test_user") == True
        assert InputValidator.is_valid_username("admin") == True
    
    def test_invalid_username(self):
        """Test invalid usernames."""
        assert InputValidator.is_valid_username("") == False
        assert InputValidator.is_valid_username("user@name") == False
        assert InputValidator.is_valid_username("a" * 100) == False  # Too long
    
    def test_valid_password(self):
        """Test valid passwords."""
        assert InputValidator.is_valid_password("password123") == True
        assert InputValidator.is_valid_password("p@ssw0rd") == True
        assert InputValidator.is_valid_password("a" * 255) == True  # Max length
    
    def test_invalid_password(self):
        """Test invalid passwords."""
        assert InputValidator.is_valid_password("") == False
        assert InputValidator.is_valid_password("a" * 256) == False  # Too long
    
    def test_validate_credentials_success(self):
        """Test successful credential validation."""
        credentials = {
            "database_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "username": "testuser",
            "password": "testpass"
        }
        
        errors = InputValidator.validate_credentials(credentials)
        assert len(errors) == 0
    
    def test_validate_credentials_missing_fields(self):
        """Test credential validation with missing fields."""
        credentials = {
            "database_type": "postgresql",
            "host": "localhost"
            # Missing username, password, port
        }
        
        errors = InputValidator.validate_credentials(credentials)
        assert "missing_fields" in errors
        assert "username" in errors["missing_fields"]
        assert "password" in errors["missing_fields"]
    
    def test_validate_credentials_invalid_values(self):
        """Test credential validation with invalid values."""
        credentials = {
            "database_type": "postgresql",
            "host": "invalid@host",
            "port": 99999,  # Invalid port
            "username": "user@name",  # Invalid username
            "password": "testpass"
        }
        
        errors = InputValidator.validate_credentials(credentials)
        assert "host" in errors
        assert "port" in errors
        assert "username" in errors


class TestConnectionValidator:
    """Test cases for ConnectionValidator."""
    
    def test_validate_postgresql_connection_success(self):
        """Test successful PostgreSQL connection validation."""
        credentials = {
            "database_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "username": "postgres",
            "password": "password",
            "ssl_mode": "prefer"
        }
        
        errors = ConnectionValidator.validate_postgresql_connection(credentials)
        assert len(errors) == 0
    
    def test_validate_postgresql_connection_wrong_type(self):
        """Test PostgreSQL validation with wrong database type."""
        credentials = {
            "database_type": "mysql",  # Wrong type
            "host": "localhost",
            "port": 5432,
            "username": "postgres",
            "password": "password"
        }
        
        errors = ConnectionValidator.validate_postgresql_connection(credentials)
        assert "database_type" in errors
    
    def test_validate_mysql_connection_success(self):
        """Test successful MySQL connection validation."""
        credentials = {
            "database_type": "mysql",
            "host": "localhost",
            "port": 3306,
            "username": "root",
            "password": "password",
            "ssl_mode": "required"
        }
        
        errors = ConnectionValidator.validate_mysql_connection(credentials)
        assert len(errors) == 0
    
    def test_get_default_port(self):
        """Test default port retrieval."""
        assert ConnectionValidator.get_default_port("postgresql") == 5432
        assert ConnectionValidator.get_default_port("mysql") == 3306
        assert ConnectionValidator.get_default_port("unknown") == 5432  # Default
    
    def test_get_default_ssl_mode(self):
        """Test default SSL mode retrieval."""
        assert ConnectionValidator.get_default_ssl_mode("postgresql") == "prefer"
        assert ConnectionValidator.get_default_ssl_mode("mysql") == "required"
        assert ConnectionValidator.get_default_ssl_mode("unknown") == "prefer"  # Default


if __name__ == "__main__":
    pytest.main([__file__]) 