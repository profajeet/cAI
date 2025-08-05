"""
Filesystem MCP server for file system operations.
"""
import os
from pathlib import Path
from typing import Dict, Any, List
from .base_mcp import BaseMCPServer, MCPServerSchema, MCPRequest, MCPResponse


class FilesystemServer(BaseMCPServer):
    """Filesystem MCP server for file system operations."""
    
    description = "Provides filesystem operations through MCP"
    version = "1.0.0"
    
    def _create_schema(self) -> MCPServerSchema:
        return MCPServerSchema(
            name="FilesystemServer",
            description=self.description,
            version=self.version,
            capabilities={
                "methods": [
                    "read_file",
                    "write_file", 
                    "list_directory",
                    "file_exists",
                    "get_file_info"
                ],
                "resources": [
                    {
                        "uri": "file://",
                        "name": "filesystem",
                        "description": "Local filesystem access"
                    }
                ]
            },
            resources=[
                {
                    "uri": "file://",
                    "name": "filesystem",
                    "description": "Local filesystem access"
                }
            ]
        )
    
    async def connect(self) -> bool:
        """Connect to the filesystem (always available)."""
        try:
            # Verify we can access the configured path
            base_path = self.config.get("path", "./workspace")
            Path(base_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to filesystem: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from the filesystem."""
        return True
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle filesystem MCP requests."""
        try:
            method = request.method
            params = request.params
            
            if method == "read_file":
                result = await self._read_file(params)
            elif method == "write_file":
                result = await self._write_file(params)
            elif method == "list_directory":
                result = await self._list_directory(params)
            elif method == "file_exists":
                result = await self._file_exists(params)
            elif method == "get_file_info":
                result = await self._get_file_info(params)
            else:
                return MCPResponse(
                    result=None,
                    error=f"Unknown method: {method}",
                    id=request.id
                )
            
            return MCPResponse(
                result=result,
                id=request.id
            )
            
        except Exception as e:
            return MCPResponse(
                result=None,
                error=str(e),
                id=request.id
            )
    
    async def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read file content."""
        path = params.get("path")
        if not path:
            raise ValueError("Path parameter is required")
        
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "content": content,
            "path": str(file_path.absolute()),
            "size": file_path.stat().st_size
        }
    
    async def _write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to file."""
        path = params.get("path")
        content = params.get("content", "")
        
        if not path:
            raise ValueError("Path parameter is required")
        
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "path": str(file_path.absolute()),
            "size": len(content.encode('utf-8')),
            "written": True
        }
    
    async def _list_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List directory contents."""
        path = params.get("path", ".")
        
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
                "size": item.stat().st_size if item.is_file() else None
            }
            items.append(item_info)
        
        return {
            "path": str(dir_path.absolute()),
            "items": items,
            "total": len(items)
        }
    
    async def _file_exists(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check if file exists."""
        path = params.get("path")
        if not path:
            raise ValueError("Path parameter is required")
        
        file_path = Path(path)
        
        return {
            "path": str(file_path.absolute()),
            "exists": file_path.exists(),
            "is_file": file_path.is_file() if file_path.exists() else False,
            "is_dir": file_path.is_dir() if file_path.exists() else False
        }
    
    async def _get_file_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed file information."""
        path = params.get("path")
        if not path:
            raise ValueError("Path parameter is required")
        
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        stat = file_path.stat()
        
        return {
            "path": str(file_path.absolute()),
            "name": file_path.name,
            "size": stat.st_size,
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:]
        } 