"""
Configuration settings for the Agentic AI Orchestration system.

This module provides type-safe configuration management using Pydantic.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not available, try to load manually
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


class MCPServerConfig(BaseSettings):
    """Configuration for an MCP server."""
    
    name: str = Field(..., description="Server name")
    host: str = Field("localhost", description="Server host")
    port: int = Field(..., description="Server port")
    protocol: str = Field("http", description="Protocol (http/https)")
    auth_token: Optional[str] = Field(None, description="Authentication token")
    timeout: int = Field(30, description="Connection timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    enabled: bool = Field(True, description="Whether this server is enabled")
    
    @property
    def url(self) -> str:
        """Get the full server URL."""
        return f"{self.protocol}://{self.host}:{self.port}"


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    
    url: str = Field("sqlite:///./agentic.db", description="Database URL")
    echo: bool = Field(False, description="Enable SQL echo")
    pool_size: int = Field(10, description="Connection pool size")
    max_overflow: int = Field(20, description="Maximum overflow connections")


class LoggingConfig(BaseSettings):
    """Logging configuration."""
    
    level: str = Field("INFO", description="Log level")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    file: Optional[str] = Field(None, description="Log file path")
    max_size: int = Field(10 * 1024 * 1024, description="Max log file size in bytes")
    backup_count: int = Field(5, description="Number of backup log files")


class AIConfig(BaseSettings):
    """AI model configuration."""
    
    provider: str = Field("openai", description="AI provider")
    model: str = Field("gpt-4", description="Model name")
    api_key: Optional[str] = Field(None, description="API key")
    temperature: float = Field(0.7, description="Model temperature")
    max_tokens: int = Field(4000, description="Maximum tokens")
    timeout: int = Field(60, description="API timeout in seconds")
    
    @field_validator("api_key", mode="before")
    @classmethod
    def get_api_key(cls, v):
        """Get API key from environment if not provided."""
        if v is None:
            return os.getenv("OPENAI_API_KEY")
        return v


class SecurityConfig(BaseSettings):
    """Security configuration."""
    
    secret_key: Optional[str] = Field(None, description="Secret key for encryption")
    algorithm: str = Field("HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(30, description="Access token expiry")
    session_timeout: int = Field(3600, description="Session timeout in seconds")
    
    @field_validator("secret_key", mode="before")
    @classmethod
    def get_secret_key(cls, v):
        """Generate secret key if not provided."""
        if v is None:
            import secrets
            return secrets.token_urlsafe(32)
        return v


class Settings(BaseSettings):
    """Main application settings."""
    
    # Application
    app_name: str = Field("Agentic AI Orchestration", description="Application name")
    version: str = Field("1.0.0", description="Application version")
    debug: bool = Field(False, description="Debug mode")
    
    # AI Configuration
    ai: AIConfig = Field(default_factory=AIConfig, description="AI configuration")
    
    # Database Configuration
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig, 
        description="Database configuration"
    )
    
    # Logging Configuration
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration"
    )
    
    # Security Configuration
    security: SecurityConfig = Field(
        default_factory=SecurityConfig,
        description="Security configuration"
    )
    
    # MCP Servers
    mcp_servers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict,
        description="MCP server configurations"
    )
    
    # Tool configurations
    tools: Dict[str, Dict] = Field(
        default_factory=dict,
        description="Tool-specific configurations"
    )
    
    # Session configuration
    session_storage: str = Field("sqlite", description="Session storage backend")
    session_cleanup_interval: int = Field(3600, description="Session cleanup interval")
    
    # Workflow configuration
    workflow_storage: str = Field("sqlite", description="Workflow storage backend")
    workflow_retention_days: int = Field(30, description="Workflow retention period")
    
    # Validation configuration
    validation_enabled: bool = Field(True, description="Enable input validation")
    verification_enabled: bool = Field(True, description="Enable service verification")
    
    # Performance configuration
    max_concurrent_requests: int = Field(10, description="Max concurrent requests")
    request_timeout: int = Field(300, description="Request timeout in seconds")
    
    model_config = ConfigDict(
        env_file=".env" if os.path.exists(".env") else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Allow extra fields from environment
    )
    
    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path]) -> "Settings":
        """Load settings from a YAML file."""
        yaml_path = Path(yaml_path)
        
        if not yaml_path.exists():
            # Create default settings
            settings = cls()
            settings.save_yaml(yaml_path)
            return settings
        
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        # Create settings instance which will load from .env file
        settings = cls()
        
        # Update with YAML data, but preserve environment-loaded values
        for key, value in data.items():
            if hasattr(settings, key):
                if key == "ai" and isinstance(value, dict):
                    # Handle nested AI config
                    ai_config = settings.ai
                    for ai_key, ai_value in value.items():
                        if hasattr(ai_config, ai_key) and ai_value is not None:
                            setattr(ai_config, ai_key, ai_value)
                elif key == "database" and isinstance(value, dict):
                    # Handle nested database config
                    db_config = settings.database
                    for db_key, db_value in value.items():
                        if hasattr(db_config, db_key) and db_value is not None:
                            setattr(db_config, db_key, db_value)
                elif key == "logging" and isinstance(value, dict):
                    # Handle nested logging config
                    log_config = settings.logging
                    for log_key, log_value in value.items():
                        if hasattr(log_config, log_key) and log_value is not None:
                            setattr(log_config, log_key, log_value)
                elif key == "security" and isinstance(value, dict):
                    # Handle nested security config
                    sec_config = settings.security
                    for sec_key, sec_value in value.items():
                        if hasattr(sec_config, sec_key) and sec_value is not None:
                            setattr(sec_config, sec_key, sec_value)
                elif key == "mcp_servers" and isinstance(value, dict):
                    # Handle MCP servers config
                    for server_name, server_data in value.items():
                        if isinstance(server_data, dict):
                            server_config = MCPServerConfig(**server_data)
                            settings.mcp_servers[server_name] = server_config
                elif key == "tools" and isinstance(value, dict):
                    # Handle tools config
                    settings.tools.update(value)
                elif value is not None:
                    setattr(settings, key, value)
        
        return settings
    
    def save_yaml(self, yaml_path: Union[str, Path]) -> None:
        """Save settings to a YAML file."""
        yaml_path = Path(yaml_path)
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and handle nested objects
        data = self.model_dump()
        
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
    
    def get_mcp_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get MCP server configuration by name."""
        return self.mcp_servers.get(name)
    
    def get_enabled_mcp_servers(self) -> List[MCPServerConfig]:
        """Get all enabled MCP servers."""
        return [
            server for server in self.mcp_servers.values()
            if server.enabled
        ]
    
    def validate_configuration(self) -> List[str]:
        """Validate the configuration and return any errors."""
        errors = []
        
        # Validate AI configuration
        if not self.ai.api_key:
            errors.append("AI API key is required")
        
        # Validate MCP servers
        for name, server in self.mcp_servers.items():
            if server.enabled and not server.host:
                errors.append(f"MCP server '{name}' must have a host")
        
        # Validate database URL
        if not self.database.url:
            errors.append("Database URL is required")
        
        return errors 