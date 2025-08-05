"""
Tool registry for managing tool extensions.
"""
import importlib
import inspect
from typing import Dict, List, Type, Any
from pathlib import Path
import logging
from .base_tool import BaseTool


class ToolRegistry:
    """Registry for managing tool extensions."""
    
    def __init__(self):
        self.tools: Dict[str, Type[BaseTool]] = {}
        self.tool_instances: Dict[str, BaseTool] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_tool(self, tool_class: Type[BaseTool]) -> None:
        """Register a tool class."""
        if not issubclass(tool_class, BaseTool):
            raise ValueError(f"Tool class must inherit from BaseTool: {tool_class}")
        
        tool_name = tool_class.__name__
        self.tools[tool_name] = tool_class
        self.logger.info(f"Registered tool: {tool_name}")
    
    def create_tool_instance(self, tool_name: str, config: Dict[str, Any]) -> BaseTool:
        """Create an instance of a tool."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        tool_class = self.tools[tool_name]
        instance = tool_class(config)
        self.tool_instances[tool_name] = instance
        return instance
    
    def get_tool(self, tool_name: str) -> BaseTool:
        """Get a tool instance."""
        if tool_name not in self.tool_instances:
            raise ValueError(f"Tool instance not found: {tool_name}")
        return self.tool_instances[tool_name]
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tool instances."""
        return self.tool_instances.copy()
    
    def get_enabled_tools(self) -> Dict[str, BaseTool]:
        """Get all enabled tool instances."""
        return {
            name: tool for name, tool in self.tool_instances.items()
            if tool.is_enabled()
        }
    
    def load_tools_from_directory(self, directory: str, config_manager) -> None:
        """Load tools from a directory."""
        tools_dir = Path(directory)
        if not tools_dir.exists():
            self.logger.warning(f"Tools directory does not exist: {directory}")
            return
        
        # Find all Python files in the directory
        for py_file in tools_dir.glob("*.py"):
            if py_file.name.startswith("__") or py_file.name.startswith("base_"):
                continue
            
            try:
                # Import the module
                module_name = f"src.tool_extensions.{py_file.stem}"
                module = importlib.import_module(module_name)
                
                # Find tool classes in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseTool) and 
                        obj != BaseTool):
                        
                        # Check if tool is enabled in config
                        tool_config = config_manager.get_tool_config(name)
                        if tool_config and tool_config.get("enabled", False):
                            self.register_tool(obj)
                            # Create instance with config
                            self.create_tool_instance(name, tool_config)
                        else:
                            self.logger.info(f"Tool {name} is disabled in configuration")
                
            except Exception as e:
                self.logger.error(f"Failed to load tool from {py_file}: {e}")
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool by name."""
        tool = self.get_tool(tool_name)
        return tool.execute_with_timing(**kwargs)
    
    def get_tool_schemas(self) -> Dict[str, Any]:
        """Get schemas for all registered tools."""
        return {
            name: tool.get_schema().dict() 
            for name, tool in self.tool_instances.items()
        }
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())
    
    def list_enabled_tools(self) -> List[str]:
        """List all enabled tool names."""
        return list(self.get_enabled_tools().keys())


# Global tool registry instance
tool_registry = ToolRegistry() 