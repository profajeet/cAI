"""
Structured logging system for Database Interface Agent.
Provides JSON formatting and proper configuration.
"""

import sys
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

import structlog
from structlog.stdlib import LoggerFactory

# Add project root to path for config import
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import settings

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None
) -> None:
    """Setup logging configuration."""
    
    # Use settings if not provided
    log_level = log_level or settings.log_level
    log_format = log_format or settings.log_format
    
    # Convert log level string to logging constant
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    log_level_constant = level_map.get(log_level.upper(), logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level_constant
    )
    
    # Set log level for all loggers
    logging.getLogger().setLevel(log_level_constant)
    
    # Configure specific loggers
    loggers_to_configure = [
        "src",
        "config",
        "langgraph",
        "langchain",
        "mcp",
        "redis",
        "psycopg2",
        "mysql.connector"
    ]
    
    for logger_name in loggers_to_configure:
        logging.getLogger(logger_name).setLevel(log_level_constant)


class AgentLogger:
    """Specialized logger for agent operations."""
    
    def __init__(self, agent_id: str, session_id: Optional[str] = None):
        self.agent_id = agent_id
        self.session_id = session_id
        self.logger = get_logger(f"agent.{agent_id}")
    
    def _get_context(self, **kwargs) -> dict:
        """Get logging context."""
        context = {
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.session_id:
            context["session_id"] = self.session_id
        
        context.update(kwargs)
        return context
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        context = self._get_context(**kwargs)
        self.logger.info(message, **context)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        context = self._get_context(**kwargs)
        self.logger.warning(message, **context)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        context = self._get_context(**kwargs)
        self.logger.error(message, **context)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        context = self._get_context(**kwargs)
        self.logger.debug(message, **context)
    
    def connection_test(self, database_type: str, host: str, port: int, success: bool, **kwargs) -> None:
        """Log connection test result."""
        context = self._get_context(
            database_type=database_type,
            host=host,
            port=port,
            success=success,
            **kwargs
        )
        
        if success:
            self.logger.info("Database connection test successful", **context)
        else:
            self.logger.error("Database connection test failed", **context)
    
    def session_created(self, reference_id: str, ttl: int) -> None:
        """Log session creation."""
        context = self._get_context(
            reference_id=reference_id,
            ttl=ttl,
            action="session_created"
        )
        self.logger.info("Session created", **context)
    
    def session_accessed(self, reference_id: str) -> None:
        """Log session access."""
        context = self._get_context(
            reference_id=reference_id,
            action="session_accessed"
        )
        self.logger.info("Session accessed", **context)
    
    def session_expired(self, reference_id: str) -> None:
        """Log session expiration."""
        context = self._get_context(
            reference_id=reference_id,
            action="session_expired"
        )
        self.logger.warning("Session expired", **context)
    
    def mcp_server_started(self, server_id: str, server_type: str) -> None:
        """Log MCP server start."""
        context = self._get_context(
            server_id=server_id,
            server_type=server_type,
            action="mcp_server_started"
        )
        self.logger.info("MCP server started", **context)
    
    def mcp_server_stopped(self, server_id: str) -> None:
        """Log MCP server stop."""
        context = self._get_context(
            server_id=server_id,
            action="mcp_server_stopped"
        )
        self.logger.info("MCP server stopped", **context)
    
    def tool_executed(self, tool_name: str, success: bool, **kwargs) -> None:
        """Log tool execution."""
        context = self._get_context(
            tool_name=tool_name,
            success=success,
            action="tool_executed",
            **kwargs
        )
        
        if success:
            self.logger.info("Tool executed successfully", **context)
        else:
            self.logger.error("Tool execution failed", **context)
    
    def security_event(self, event_type: str, details: dict) -> None:
        """Log security-related events."""
        context = self._get_context(
            event_type=event_type,
            details=details,
            action="security_event"
        )
        self.logger.warning("Security event detected", **context)


# Initialize logging on module import
setup_logging() 