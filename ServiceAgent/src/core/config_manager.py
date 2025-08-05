"""
Configuration manager for the agent.
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import logging


class ConfigManager:
    """Manages agent configuration loading and validation."""
    
    def __init__(self, config_path: str = "config/agent_config.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as file:
                self.config = yaml.safe_load(file)
            
            # Resolve environment variables
            self._resolve_env_vars()
            
            # Validate configuration
            self._validate_config()
            
            self.logger.info(f"Configuration loaded successfully from {self.config_path}")
            return self.config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _resolve_env_vars(self):
        """Resolve environment variables in configuration values."""
        def resolve_value(value):
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                return os.getenv(env_var, "")
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(v) for v in value]
            else:
                return value
        
        self.config = resolve_value(self.config)
    
    def _validate_config(self):
        """Validate the loaded configuration."""
        required_sections = ["agent", "tool_extensions", "mcp_extensions", "behavior"]
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate agent configuration
        agent_config = self.config.get("agent", {})
        if not agent_config.get("model"):
            raise ValueError("Agent model is required")
        
        # Validate tool extensions
        tool_config = self.config.get("tool_extensions", {})
        if tool_config.get("enabled", False):
            tools = tool_config.get("tools", {})
            for tool_name, tool_config in tools.items():
                if tool_config.get("enabled", False):
                    # Check for required API keys
                    if "api_key" in tool_config and not tool_config["api_key"]:
                        self.logger.warning(f"API key not found for tool: {tool_name}")
    
    def get_tool_config(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific tool."""
        tools = self.config.get("tool_extensions", {}).get("tools", {})
        return tools.get(tool_name, {})
    
    def get_mcp_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific MCP server."""
        servers = self.config.get("mcp_extensions", {}).get("servers", {})
        return servers.get(server_name, {})
    
    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a tool is enabled."""
        tool_config = self.get_tool_config(tool_name)
        return tool_config.get("enabled", False)
    
    def is_mcp_enabled(self, server_name: str) -> bool:
        """Check if an MCP server is enabled."""
        mcp_config = self.get_mcp_config(server_name)
        return mcp_config.get("enabled", False)
    
    def get_enabled_tools(self) -> list[str]:
        """Get list of enabled tools."""
        tools = self.config.get("tool_extensions", {}).get("tools", {})
        return [name for name, config in tools.items() if config.get("enabled", False)]
    
    def get_enabled_mcp_servers(self) -> list[str]:
        """Get list of enabled MCP servers."""
        servers = self.config.get("mcp_extensions", {}).get("servers", {})
        return [name for name, config in servers.items() if config.get("enabled", False)]
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return self.config.get("agent", {})
    
    def get_behavior_config(self) -> Dict[str, Any]:
        """Get behavior configuration."""
        return self.config.get("behavior", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.config.get("logging", {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        return self.config.get("api", {})
    
    def reload_config(self) -> Dict[str, Any]:
        """Reload configuration from file."""
        return self.load_config() 