"""
File operations tool extension.
"""
import os
from pathlib import Path
from typing import Dict, Any, List
from .base_tool import BaseTool, ToolSchema, ToolResult


class FileOperations(BaseTool):
    """File operations tool for reading and writing files."""
    
    description = "Performs file operations like reading, writing, and listing files"
    
    def _create_schema(self) -> ToolSchema:
        return ToolSchema(
            name="FileOperations",
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "write", "list", "exists"],
                        "description": "File operation to perform"
                    },
                    "path": {
                        "type": "string",
                        "description": "File or directory path"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write (for write operation)"
                    }
                },
                "required": ["operation", "path"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "result": {"type": "object"},
                    "error": {"type": "string"}
                }
            },
            required_params=["operation", "path"]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        operation = kwargs["operation"]
        path = kwargs["path"]
        content = kwargs.get("content", "")
        
        try:
            # Validate file extension if writing
            if operation == "write":
                self._validate_file_extension(path)
            
            # Perform operation
            if operation == "read":
                result = self._read_file(path)
            elif operation == "write":
                result = self._write_file(path, content)
            elif operation == "list":
                result = self._list_directory(path)
            elif operation == "exists":
                result = self._file_exists(path)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
            return ToolResult(
                success=True,
                result=result
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )
    
    def _validate_file_extension(self, path: str) -> None:
        """Validate file extension against allowed extensions."""
        allowed_extensions = self.config.get("allowed_extensions", [])
        if allowed_extensions:
            file_ext = Path(path).suffix.lower()
            if file_ext not in allowed_extensions:
                raise ValueError(f"File extension {file_ext} not allowed. Allowed: {allowed_extensions}")
    
    def _read_file(self, path: str) -> Dict[str, Any]:
        """Read file content."""
        file_path = Path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        # Check file size limit
        max_size_mb = self.config.get("max_file_size_mb", 10)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            raise ValueError(f"File too large: {file_size_mb:.2f}MB > {max_size_mb}MB")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "content": content,
            "size_bytes": file_path.stat().st_size,
            "path": str(file_path.absolute())
        }
    
    def _write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to file."""
        file_path = Path(path)
        
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "path": str(file_path.absolute()),
            "size_bytes": len(content.encode('utf-8')),
            "written": True
        }
    
    def _list_directory(self, path: str) -> Dict[str, Any]:
        """List directory contents."""
        dir_path = Path(path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        items = []
        for item in dir_path.iterdir():
            item_info = {
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size_bytes": item.stat().st_size if item.is_file() else None
            }
            items.append(item_info)
        
        return {
            "path": str(dir_path.absolute()),
            "items": items,
            "total_items": len(items)
        }
    
    def _file_exists(self, path: str) -> Dict[str, Any]:
        """Check if file or directory exists."""
        path_obj = Path(path)
        
        return {
            "path": str(path_obj.absolute()),
            "exists": path_obj.exists(),
            "is_file": path_obj.is_file() if path_obj.exists() else False,
            "is_dir": path_obj.is_dir() if path_obj.exists() else False
        } 