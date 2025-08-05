"""
Database-specific configuration and connection parameters.
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DatabaseType(str, Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    # Extensible for future database types
    # ORACLE = "oracle"
    # SQLSERVER = "sqlserver"


class DatabaseConnectionConfig(BaseModel):
    """Database connection configuration."""
    
    database_type: DatabaseType
    host: str
    port: int
    username: str
    password: str
    database_name: Optional[str] = None
    ssl_mode: Optional[str] = None
    connection_timeout: Optional[int] = None
    max_connections: Optional[int] = None
    
    class Config:
        extra = "forbid"  # Prevent additional fields


class DatabaseDefaults:
    """Default configuration values for different database types."""
    
    POSTGRESQL_DEFAULTS = {
        "port": 5432,
        "ssl_mode": "prefer",
        "connection_timeout": 5,
        "max_connections": 10
    }
    
    MYSQL_DEFAULTS = {
        "port": 3306,
        "ssl_mode": "required",
        "connection_timeout": 5,
        "max_connections": 10
    }
    
    @classmethod
    def get_defaults(cls, database_type: DatabaseType) -> Dict[str, Any]:
        """Get default configuration for a database type."""
        defaults_map = {
            DatabaseType.POSTGRESQL: cls.POSTGRESQL_DEFAULTS,
            DatabaseType.MYSQL: cls.MYSQL_DEFAULTS,
        }
        return defaults_map.get(database_type, {})


class ConnectionStringBuilder:
    """Build database connection strings."""
    
    @staticmethod
    def build_postgresql_connection_string(config: DatabaseConnectionConfig) -> str:
        """Build PostgreSQL connection string."""
        params = []
        
        if config.ssl_mode:
            params.append(f"sslmode={config.ssl_mode}")
        
        if config.connection_timeout:
            params.append(f"connect_timeout={config.connection_timeout}")
        
        if config.max_connections:
            params.append(f"max_connections={config.max_connections}")
        
        param_string = "&".join(params) if params else ""
        
        if config.database_name:
            base_url = f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database_name}"
        else:
            base_url = f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}"
        
        if param_string:
            return f"{base_url}?{param_string}"
        
        return base_url
    
    @staticmethod
    def build_mysql_connection_string(config: DatabaseConnectionConfig) -> str:
        """Build MySQL connection string."""
        params = []
        
        if config.ssl_mode:
            params.append(f"ssl_mode={config.ssl_mode}")
        
        if config.connection_timeout:
            params.append(f"connection_timeout={config.connection_timeout}")
        
        if config.max_connections:
            params.append(f"max_connections={config.max_connections}")
        
        param_string = "&".join(params) if params else ""
        
        if config.database_name:
            base_url = f"mysql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database_name}"
        else:
            base_url = f"mysql://{config.username}:{config.password}@{config.host}:{config.port}"
        
        if param_string:
            return f"{base_url}?{param_string}"
        
        return base_url
    
    @classmethod
    def build_connection_string(cls, config: DatabaseConnectionConfig) -> str:
        """Build connection string based on database type."""
        builders = {
            DatabaseType.POSTGRESQL: cls.build_postgresql_connection_string,
            DatabaseType.MYSQL: cls.build_mysql_connection_string,
        }
        
        builder = builders.get(config.database_type)
        if not builder:
            raise ValueError(f"Unsupported database type: {config.database_type}")
        
        return builder(config)


class DatabaseValidationRules:
    """Validation rules for database connections."""
    
    @staticmethod
    def validate_postgresql_config(config: DatabaseConnectionConfig) -> None:
        """Validate PostgreSQL configuration."""
        if not (1024 <= config.port <= 65535):
            raise ValueError("PostgreSQL port must be between 1024 and 65535")
        
        if config.ssl_mode and config.ssl_mode not in ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]:
            raise ValueError("Invalid SSL mode for PostgreSQL")
    
    @staticmethod
    def validate_mysql_config(config: DatabaseConnectionConfig) -> None:
        """Validate MySQL configuration."""
        if not (1024 <= config.port <= 65535):
            raise ValueError("MySQL port must be between 1024 and 65535")
        
        if config.ssl_mode and config.ssl_mode not in ["disabled", "preferred", "required", "verify_ca", "verify_identity"]:
            raise ValueError("Invalid SSL mode for MySQL")
    
    @classmethod
    def validate_config(cls, config: DatabaseConnectionConfig) -> None:
        """Validate database configuration based on type."""
        validators = {
            DatabaseType.POSTGRESQL: cls.validate_postgresql_config,
            DatabaseType.MYSQL: cls.validate_mysql_config,
        }
        
        validator = validators.get(config.database_type)
        if validator:
            validator(config) 