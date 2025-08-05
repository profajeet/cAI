"""
Service verification and validation for the Agentic AI Orchestration system.

This module provides the VerificationManager class that handles service
verification, credential validation, and input verification.
"""

import asyncio
import aiohttp
from typing import Any, Dict, List, Optional

from rich.console import Console

from config.settings import Settings

console = Console()


class VerificationManager:
    """
    Manages service verification and validation.
    
    This class provides:
    - Service verification
    - Credential validation
    - Input verification
    - Security checks
    """
    
    def __init__(self, settings: Settings):
        """Initialize the verification manager."""
        self.settings = settings
        
        # HTTP session for verification requests
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Verification cache
        self.verification_cache: Dict[str, Dict[str, Any]] = {}
        
        console.log("🔒 VerificationManager initialized")
    
    async def initialize(self):
        """Initialize the verification manager."""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        console.log("🔒 VerificationManager initialized successfully")
    
    async def verify_service(self, service_name: str) -> Dict[str, Any]:
        """
        Verify a service is available and accessible.
        
        Args:
            service_name: Name of the service to verify
            
        Returns:
            Verification result
        """
        try:
            # Check cache first
            if service_name in self.verification_cache:
                cached_result = self.verification_cache[service_name]
                if self._is_cache_valid(cached_result):
                    return cached_result
            
            # Perform verification based on service type
            if service_name.startswith("mcp_"):
                result = await self._verify_mcp_service(service_name)
            elif service_name == "filesystem":
                result = await self._verify_filesystem_service()
            elif service_name == "database":
                result = await self._verify_database_service()
            elif service_name == "api_client":
                result = await self._verify_api_client_service()
            else:
                result = await self._verify_generic_service(service_name)
            
            # Cache result
            self.verification_cache[service_name] = result
            
            return result
            
        except Exception as e:
            console.log(f"❌ Error verifying service {service_name}: {e}")
            return {
                "verified": False,
                "error": str(e),
                "service": service_name
            }
    
    async def verify_credentials(
        self, 
        service_name: str, 
        credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify credentials for a service.
        
        Args:
            service_name: Name of the service
            credentials: Credentials to verify
            
        Returns:
            Credential verification result
        """
        try:
            if service_name.startswith("database_"):
                return await self._verify_database_credentials(credentials)
            elif service_name.startswith("api_"):
                return await self._verify_api_credentials(credentials)
            elif service_name.startswith("mcp_"):
                return await self._verify_mcp_credentials(service_name, credentials)
            else:
                return await self._verify_generic_credentials(service_name, credentials)
                
        except Exception as e:
            console.log(f"❌ Error verifying credentials for {service_name}: {e}")
            return {
                "verified": False,
                "error": str(e),
                "service": service_name
            }
    
    async def verify_input(
        self, 
        input_data: Any, 
        input_type: str,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verify input data.
        
        Args:
            input_data: Input data to verify
            input_type: Type of input
            validation_rules: Optional validation rules
            
        Returns:
            Input verification result
        """
        try:
            if input_type == "file_path":
                return await self._verify_file_path(input_data)
            elif input_type == "url":
                return await self._verify_url(input_data)
            elif input_type == "database_query":
                return await self._verify_database_query(input_data)
            elif input_type == "api_request":
                return await self._verify_api_request(input_data)
            else:
                return await self._verify_generic_input(input_data, validation_rules)
                
        except Exception as e:
            console.log(f"❌ Error verifying input: {e}")
            return {
                "verified": False,
                "error": str(e),
                "input_type": input_type
            }
    
    async def _verify_mcp_service(self, service_name: str) -> Dict[str, Any]:
        """Verify an MCP service."""
        try:
            # Extract server name from service name
            server_name = service_name.replace("mcp_", "")
            
            # Get server configuration
            server_config = self.settings.get_mcp_server(server_name)
            
            if not server_config:
                return {
                    "verified": False,
                    "error": f"MCP server not found: {server_name}",
                    "service": service_name
                }
            
            if not server_config.enabled:
                return {
                    "verified": False,
                    "error": f"MCP server disabled: {server_name}",
                    "service": service_name
                }
            
            # Test connection
            health_url = f"{server_config.url}/health"
            
            async with self.session.get(health_url) as response:
                if response.status == 200:
                    return {
                        "verified": True,
                        "service": service_name,
                        "server": server_name,
                        "url": server_config.url
                    }
                else:
                    return {
                        "verified": False,
                        "error": f"Health check failed: HTTP {response.status}",
                        "service": service_name
                    }
                    
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "service": service_name
            }
    
    async def _verify_filesystem_service(self) -> Dict[str, Any]:
        """Verify filesystem service."""
        try:
            import os
            
            # Test basic filesystem operations
            test_dir = "/tmp/agentic_test"
            
            # Create test directory
            os.makedirs(test_dir, exist_ok=True)
            
            # Test file creation
            test_file = os.path.join(test_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            
            # Test file reading
            with open(test_file, "r") as f:
                content = f.read()
            
            # Cleanup
            os.remove(test_file)
            os.rmdir(test_dir)
            
            return {
                "verified": True,
                "service": "filesystem",
                "capabilities": ["read", "write", "create", "delete"]
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "service": "filesystem"
            }
    
    async def _verify_database_service(self) -> Dict[str, Any]:
        """Verify database service."""
        try:
            # Check if database configuration exists
            db_config = self.settings.database
            
            if not db_config.url:
                return {
                    "verified": False,
                    "error": "No database configuration found",
                    "service": "database"
                }
            
            # Test database connection
            # This would be implemented based on the database type
            return {
                "verified": True,
                "service": "database",
                "url": db_config.url,
                "capabilities": ["connect", "query", "transaction"]
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "service": "database"
            }
    
    async def _verify_api_client_service(self) -> Dict[str, Any]:
        """Verify API client service."""
        try:
            # Test basic HTTP capabilities
            test_url = "https://httpbin.org/get"
            
            async with self.session.get(test_url) as response:
                if response.status == 200:
                    return {
                        "verified": True,
                        "service": "api_client",
                        "capabilities": ["get", "post", "put", "delete"]
                    }
                else:
                    return {
                        "verified": False,
                        "error": f"HTTP test failed: {response.status}",
                        "service": "api_client"
                    }
                    
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "service": "api_client"
            }
    
    async def _verify_generic_service(self, service_name: str) -> Dict[str, Any]:
        """Verify a generic service."""
        # For now, assume generic services are available
        # This could be enhanced with service-specific verification
        return {
            "verified": True,
            "service": service_name,
            "note": "Generic service verification"
        }
    
    async def _verify_database_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Verify database credentials."""
        try:
            # Basic credential validation
            required_fields = ["host", "port", "database"]
            
            for field in required_fields:
                if field not in credentials:
                    return {
                        "verified": False,
                        "error": f"Missing required field: {field}",
                        "credentials": "database"
                    }
            
            # Test connection (would be implemented based on database type)
            return {
                "verified": True,
                "credentials": "database",
                "host": credentials.get("host"),
                "database": credentials.get("database")
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "credentials": "database"
            }
    
    async def _verify_api_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Verify API credentials."""
        try:
            # Check for API key
            if "api_key" not in credentials:
                return {
                    "verified": False,
                    "error": "Missing API key",
                    "credentials": "api"
                }
            
            # Test API key (would be implemented based on API type)
            return {
                "verified": True,
                "credentials": "api",
                "has_api_key": True
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "credentials": "api"
            }
    
    async def _verify_mcp_credentials(
        self, 
        service_name: str, 
        credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify MCP credentials."""
        try:
            # Extract server name
            server_name = service_name.replace("mcp_", "")
            
            # Get server configuration
            server_config = self.settings.get_mcp_server(server_name)
            
            if not server_config:
                return {
                    "verified": False,
                    "error": f"MCP server not found: {server_name}",
                    "credentials": "mcp"
                }
            
            # Check if auth token is required and provided
            if server_config.auth_token and "auth_token" not in credentials:
                return {
                    "verified": False,
                    "error": "Missing authentication token",
                    "credentials": "mcp"
                }
            
            return {
                "verified": True,
                "credentials": "mcp",
                "server": server_name
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "credentials": "mcp"
            }
    
    async def _verify_generic_credentials(
        self, 
        service_name: str, 
        credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify generic credentials."""
        # Basic credential validation
        if not credentials:
            return {
                "verified": False,
                "error": "No credentials provided",
                "credentials": service_name
            }
        
        return {
            "verified": True,
            "credentials": service_name,
            "note": "Generic credential verification"
        }
    
    async def _verify_file_path(self, file_path: str) -> Dict[str, Any]:
        """Verify file path."""
        try:
            import os
            
            # Check for unsafe patterns
            unsafe_patterns = ["..", "~", "/etc", "/var", "/usr"]
            for pattern in unsafe_patterns:
                if pattern in file_path:
                    return {
                        "verified": False,
                        "error": f"Unsafe file path pattern: {pattern}",
                        "input_type": "file_path"
                    }
            
            # Check if path is absolute and within allowed directories
            if os.path.isabs(file_path):
                # Add additional security checks here
                pass
            
            return {
                "verified": True,
                "input_type": "file_path",
                "path": file_path
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "input_type": "file_path"
            }
    
    async def _verify_url(self, url: str) -> Dict[str, Any]:
        """Verify URL."""
        try:
            from urllib.parse import urlparse
            
            # Parse URL
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ["http", "https"]:
                return {
                    "verified": False,
                    "error": "Invalid URL scheme",
                    "input_type": "url"
                }
            
            # Check for localhost or private IPs (security concern)
            if parsed.hostname in ["localhost", "127.0.0.1"]:
                return {
                    "verified": False,
                    "error": "Localhost URLs not allowed",
                    "input_type": "url"
                }
            
            return {
                "verified": True,
                "input_type": "url",
                "url": url,
                "scheme": parsed.scheme,
                "hostname": parsed.hostname
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "input_type": "url"
            }
    
    async def _verify_database_query(self, query: str) -> Dict[str, Any]:
        """Verify database query."""
        try:
            # Basic SQL injection prevention
            dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "EXEC"]
            
            query_upper = query.upper()
            for keyword in dangerous_keywords:
                if keyword in query_upper:
                    return {
                        "verified": False,
                        "error": f"Dangerous SQL keyword detected: {keyword}",
                        "input_type": "database_query"
                    }
            
            return {
                "verified": True,
                "input_type": "database_query",
                "query": query
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "input_type": "database_query"
            }
    
    async def _verify_api_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify API request."""
        try:
            # Check for required fields
            if "url" not in request_data:
                return {
                    "verified": False,
                    "error": "Missing URL in API request",
                    "input_type": "api_request"
                }
            
            # Verify URL
            url_result = await self._verify_url(request_data["url"])
            if not url_result["verified"]:
                return url_result
            
            return {
                "verified": True,
                "input_type": "api_request",
                "request": request_data
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "input_type": "api_request"
            }
    
    async def _verify_generic_input(
        self, 
        input_data: Any, 
        validation_rules: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Verify generic input."""
        try:
            if validation_rules:
                # Apply validation rules
                # This would be enhanced with a proper validation library
                pass
            
            return {
                "verified": True,
                "input_type": "generic",
                "data": input_data
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "input_type": "generic"
            }
    
    def _is_cache_valid(self, cached_result: Dict[str, Any]) -> bool:
        """Check if cached verification result is still valid."""
        # Cache validity could be based on timestamp
        # For now, assume cache is always valid
        return True
    
    async def shutdown(self):
        """Shutdown the verification manager."""
        console.log("🔄 Shutting down VerificationManager...")
        
        if self.session:
            await self.session.close()
        
        console.log("✅ VerificationManager shutdown complete") 