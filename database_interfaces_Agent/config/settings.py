"""
Configuration settings for the Database Interface Agent.
Uses Pydantic settings for environment variable management.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Main application settings."""
    
    # Application settings
    app_name: str = "Database Interface Agent"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Session management
    session_ttl: int = Field(default=3600, env="SESSION_TTL")  # 1 hour default
    max_sessions: int = Field(default=100, env="MAX_SESSIONS")
    
    # Security - provide defaults for development
    encryption_key: str = Field(default="dev-encryption-key-32-chars-long", env="ENCRYPTION_KEY")
    secret_key: str = Field(default="dev-secret-key-32-chars-long", env="SECRET_KEY")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # MCP settings
    mcp_timeout: int = Field(default=30, env="MCP_TIMEOUT")
    mcp_retry_attempts: int = Field(default=3, env="MCP_RETRY_ATTEMPTS")
    
    # Database connection settings
    default_postgres_port: int = Field(default=5432, env="DEFAULT_POSTGRES_PORT")
    default_mysql_port: int = Field(default=3306, env="DEFAULT_MYSQL_PORT")
    
    # Redis settings (for session storage)
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    
    # Connection testing
    connection_timeout: int = Field(default=5, env="CONNECTION_TIMEOUT")
    max_connection_pool_size: int = Field(default=10, env="MAX_CONNECTION_POOL_SIZE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def validate_settings() -> None:
    """Validate critical settings."""
    if not settings.encryption_key or settings.encryption_key.startswith("dev-"):
        print("⚠️  Warning: Using development encryption key. Set ENCRYPTION_KEY in production.")
    
    if not settings.secret_key or settings.secret_key.startswith("dev-"):
        print("⚠️  Warning: Using development secret key. Set SECRET_KEY in production.")
    
    if settings.session_ttl <= 0:
        raise ValueError("SESSION_TTL must be greater than 0")
    
    if settings.mcp_timeout <= 0:
        raise ValueError("MCP_TIMEOUT must be greater than 0") 