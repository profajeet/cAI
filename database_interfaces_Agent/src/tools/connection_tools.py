"""
Connection-related tools for the Database Interface Agent.
Handles credential collection, validation, and connection testing.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from config.database_config import (
    DatabaseConnectionConfig, 
    DatabaseType, 
    DatabaseDefaults, 
    ConnectionStringBuilder,
    DatabaseValidationRules
)
from src.agent.state import AgentState, AgentStatus, ConnectionStatus
from src.utils.validators import InputValidator
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CollectCredentialsInput(BaseModel):
    """Input for credential collection tool."""
    database_type: Optional[str] = Field(None, description="Database type (postgresql, mysql)")
    host: Optional[str] = Field(None, description="Database hostname or IP address")
    port: Optional[int] = Field(None, description="Database port number")
    username: Optional[str] = Field(None, description="Database username")
    password: Optional[str] = Field(None, description="Database password")
    database_name: Optional[str] = Field(None, description="Database name (optional)")


class CollectCredentialsTool(BaseTool):
    """Tool for collecting database credentials interactively or from structured input."""
    
    name: str = "collect_credentials"
    description: str = "Collect database connection credentials from user input"
    args_schema: type = CollectCredentialsInput
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """Collect credentials from structured input."""
        return self._collect_credentials(kwargs)
    
    async def _arun(self, **kwargs) -> Dict[str, Any]:
        """Async version of credential collection."""
        return self._collect_credentials(kwargs)
    
    def _collect_credentials(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect and validate database credentials."""
        try:
            # Extract and validate input
            database_type = input_data.get("database_type")
            host = input_data.get("host")
            port = input_data.get("port")
            username = input_data.get("username")
            password = input_data.get("password")
            database_name = input_data.get("database_name")
            
            # Validate required fields
            missing_fields = []
            if not database_type:
                missing_fields.append("database_type")
            if not host:
                missing_fields.append("host")
            if not username:
                missing_fields.append("username")
            if not password:
                missing_fields.append("password")
            
            if missing_fields:
                return {
                    "success": False,
                    "missing_fields": missing_fields,
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Validate database type
            try:
                db_type = DatabaseType(database_type.lower())
            except ValueError:
                return {
                    "success": False,
                    "message": f"Unsupported database type: {database_type}. Supported types: {[t.value for t in DatabaseType]}"
                }
            
            # Apply defaults if port not provided
            if not port:
                defaults = DatabaseDefaults.get_defaults(db_type)
                port = defaults.get("port", 5432 if db_type == DatabaseType.POSTGRESQL else 3306)
            
            # Create connection config
            config = DatabaseConnectionConfig(
                database_type=db_type,
                host=host,
                port=port,
                username=username,
                password=password,
                database_name=database_name
            )
            
            # Validate configuration
            try:
                DatabaseValidationRules.validate_config(config)
            except ValueError as e:
                return {
                    "success": False,
                    "message": f"Configuration validation failed: {str(e)}"
                }
            
            # Validate host format
            if not InputValidator.is_valid_host(host):
                return {
                    "success": False,
                    "message": f"Invalid host format: {host}"
                }
            
            # Validate port range
            if not InputValidator.is_valid_port(port):
                return {
                    "success": False,
                    "message": f"Invalid port number: {port}. Must be between 1024 and 65535"
                }
            
            logger.info(f"Credentials collected successfully for {db_type.value} database at {host}:{port}")
            
            return {
                "success": True,
                "connection_config": config,
                "message": f"Credentials collected successfully for {db_type.value} database"
            }
            
        except Exception as e:
            logger.error(f"Error collecting credentials: {str(e)}")
            return {
                "success": False,
                "message": f"Error collecting credentials: {str(e)}"
            }


class TestConnectionInput(BaseModel):
    """Input for connection testing tool."""
    connection_config: Dict[str, Any] = Field(..., description="Database connection configuration")


class TestConnectionTool(BaseTool):
    """Tool for testing database connections."""
    
    name: str = "test_connection"
    description: str = "Test database connection using provided credentials"
    args_schema: type = TestConnectionInput
    
    def _run(self, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test database connection."""
        return asyncio.run(self._test_connection(connection_config))
    
    async def _arun(self, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Async version of connection testing."""
        return await self._test_connection(connection_config)
    
    async def _test_connection(self, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test database connection asynchronously."""
        try:
            # Convert dict back to DatabaseConnectionConfig
            config = DatabaseConnectionConfig(**connection_config)
            
            logger.info(f"Testing connection to {config.database_type.value} at {config.host}:{config.port}")
            
            # Build connection string
            connection_string = ConnectionStringBuilder.build_connection_string(config)
            
            # Test connection based on database type
            if config.database_type == DatabaseType.POSTGRESQL:
                result = await self._test_postgresql_connection(config)
            elif config.database_type == DatabaseType.MYSQL:
                result = await self._test_mysql_connection(config)
            else:
                return {
                    "success": False,
                    "message": f"Unsupported database type: {config.database_type}"
                }
            
            # Add metadata to result
            result.update({
                "database_type": config.database_type.value,
                "host": config.host,
                "port": config.port,
                "database_name": config.database_name,
                "tested_at": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "error_type": type(e).__name__
            }
    
    async def _test_postgresql_connection(self, config: DatabaseConnectionConfig) -> Dict[str, Any]:
        """Test PostgreSQL connection."""
        try:
            import psycopg2
            import psycopg2.extras
            
            # Test connection
            conn = psycopg2.connect(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                database=config.database_name or "postgres",
                connect_timeout=5
            )
            
            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            # Get database info
            cursor.execute("SELECT current_database(), current_user")
            db_info = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "message": "PostgreSQL connection successful",
                "version": version,
                "database": db_info[0],
                "user": db_info[1],
                "connection_time": "~5ms"
            }
            
        except psycopg2.OperationalError as e:
            return {
                "success": False,
                "message": f"PostgreSQL connection failed: {str(e)}",
                "error_code": getattr(e, 'pgcode', None)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"PostgreSQL connection error: {str(e)}"
            }
    
    async def _test_mysql_connection(self, config: DatabaseConnectionConfig) -> Dict[str, Any]:
        """Test MySQL connection."""
        try:
            import mysql.connector
            from mysql.connector import Error
            
            # Test connection
            conn = mysql.connector.connect(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                database=config.database_name,
                connection_timeout=5
            )
            
            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            
            # Get database info
            cursor.execute("SELECT DATABASE(), USER()")
            db_info = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "message": "MySQL connection successful",
                "version": version,
                "database": db_info[0],
                "user": db_info[1],
                "connection_time": "~5ms"
            }
            
        except Error as e:
            return {
                "success": False,
                "message": f"MySQL connection failed: {str(e)}",
                "error_code": e.errno
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"MySQL connection error: {str(e)}"
            }


class ValidateCredentialsInput(BaseModel):
    """Input for credential validation tool."""
    credentials: Dict[str, Any] = Field(..., description="Credentials to validate")


class ValidateCredentialsTool(BaseTool):
    """Tool for validating database credentials format and completeness."""
    
    name: str = "validate_credentials"
    description: str = "Validate database credentials format and completeness"
    args_schema: type = ValidateCredentialsInput
    
    def _run(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Validate credentials."""
        return self._validate_credentials(credentials)
    
    async def _arun(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Async version of credential validation."""
        return self._validate_credentials(credentials)
    
    def _validate_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Validate credential format and completeness."""
        try:
            validation_errors = []
            
            # Check required fields
            required_fields = ["database_type", "host", "username", "password"]
            for field in required_fields:
                if field not in credentials or not credentials[field]:
                    validation_errors.append(f"Missing required field: {field}")
            
            if validation_errors:
                return {
                    "valid": False,
                    "errors": validation_errors,
                    "message": "Credential validation failed"
                }
            
            # Validate database type
            try:
                db_type = DatabaseType(credentials["database_type"].lower())
            except ValueError:
                validation_errors.append(f"Unsupported database type: {credentials['database_type']}")
            
            # Validate host format
            if not InputValidator.is_valid_host(credentials["host"]):
                validation_errors.append(f"Invalid host format: {credentials['host']}")
            
            # Validate port if provided
            if "port" in credentials and credentials["port"]:
                if not InputValidator.is_valid_port(credentials["port"]):
                    validation_errors.append(f"Invalid port number: {credentials['port']}")
            
            # Validate username format
            if not InputValidator.is_valid_username(credentials["username"]):
                validation_errors.append(f"Invalid username format: {credentials['username']}")
            
            if validation_errors:
                return {
                    "valid": False,
                    "errors": validation_errors,
                    "message": "Credential validation failed"
                }
            
            return {
                "valid": True,
                "message": "Credentials are valid",
                "database_type": credentials["database_type"]
            }
            
        except Exception as e:
            logger.error(f"Error validating credentials: {str(e)}")
            return {
                "valid": False,
                "errors": [str(e)],
                "message": "Credential validation error"
            }


# Tool registry
def get_connection_tools() -> List[BaseTool]:
    """Get all connection-related tools."""
    return [
        CollectCredentialsTool(),
        TestConnectionTool(),
        ValidateCredentialsTool()
    ] 