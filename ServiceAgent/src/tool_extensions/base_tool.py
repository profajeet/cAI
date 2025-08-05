"""
Base tool class for all tool extensions.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import logging
import time
from datetime import datetime


class ToolSchema(BaseModel):
    """Schema for tool input/output."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_params: List[str] = Field(default_factory=list)


class ToolResult(BaseModel):
    """Result from tool execution."""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """Base class for all tool extensions."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.name = self.__class__.__name__
        self.description = getattr(self, 'description', 'No description provided')
        self.schema = self._create_schema()
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    @abstractmethod
    def _create_schema(self) -> ToolSchema:
        """Create the tool schema."""
        pass
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        required_params = self.schema.required_params
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"Required parameter '{param}' is missing")
        return True
    
    def execute_with_timing(self, **kwargs) -> ToolResult:
        """Execute tool with timing information."""
        start_time = time.time()
        
        try:
            # Validate input
            self.validate_input(**kwargs)
            
            # Execute tool
            result = self.execute(**kwargs)
            
            # Add timing information
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            self.logger.info(f"Tool {self.name} executed successfully in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Tool {self.name} failed: {str(e)}")
            
            return ToolResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    def get_schema(self) -> ToolSchema:
        """Get the tool schema."""
        return self.schema
    
    def is_enabled(self) -> bool:
        """Check if the tool is enabled based on configuration."""
        return self.config.get("enabled", False)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default) 