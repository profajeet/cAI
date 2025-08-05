"""
Input validation utilities for Database Interface Agent.
Validates database credentials and connection parameters.
"""

import re
import ipaddress
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from src.utils.logger import get_logger

logger = get_logger(__name__)


class InputValidator:
    """Input validation utilities."""
    
    @staticmethod
    def is_valid_host(host: str) -> bool:
        """Validate host format (IP address or hostname)."""
        try:
            # Check if it's a valid IP address
            ipaddress.ip_address(host)
            return True
        except ValueError:
            # Check if it's a valid hostname
            if not host or len(host) > 253:
                return False
            
            # Hostname regex pattern
            hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
            return bool(re.match(hostname_pattern, host))
    
    @staticmethod
    def is_valid_port(port: int) -> bool:
        """Validate port number."""
        return 1024 <= port <= 65535
    
    @staticmethod
    def is_valid_username(username: str) -> bool:
        """Validate database username."""
        if not username or len(username) > 63:
            return False
        
        # Username regex pattern (alphanumeric, underscore, hyphen)
        username_pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(username_pattern, username))
    
    @staticmethod
    def is_valid_password(password: str) -> bool:
        """Validate database password."""
        # Basic password validation
        if not password:
            return False
        
        # Check for minimum length
        if len(password) < 1:
            return False
        
        # Check for maximum length (reasonable limit)
        if len(password) > 255:
            return False
        
        return True
    
    @staticmethod
    def is_valid_database_name(db_name: str) -> bool:
        """Validate database name."""
        if not db_name:
            return True  # Optional field
        
        if len(db_name) > 63:
            return False
        
        # Database name regex pattern
        db_name_pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(db_name_pattern, db_name))
    
    @staticmethod
    def is_valid_connection_string(connection_string: str) -> bool:
        """Validate database connection string format."""
        try:
            parsed = urlparse(connection_string)
            
            # Check scheme
            if parsed.scheme not in ['postgresql', 'mysql', 'postgres']:
                return False
            
            # Check host
            if not parsed.hostname:
                return False
            
            # Check port
            if parsed.port and not InputValidator.is_valid_port(parsed.port):
                return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Sanitize input string to prevent injection attacks."""
        if not input_str:
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', input_str)
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    @staticmethod
    def validate_ssl_mode(ssl_mode: str, database_type: str) -> bool:
        """Validate SSL mode for database type."""
        if not ssl_mode:
            return True  # Optional field
        
        valid_modes = {
            'postgresql': ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full'],
            'mysql': ['disabled', 'preferred', 'required', 'verify_ca', 'verify_identity']
        }
        
        return ssl_mode.lower() in valid_modes.get(database_type.lower(), [])
    
    @staticmethod
    def validate_credentials(credentials: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate database credentials and return validation errors."""
        errors = {}
        
        # Required fields
        required_fields = ['database_type', 'host', 'username', 'password']
        for field in required_fields:
            if field not in credentials or not credentials[field]:
                if 'missing_fields' not in errors:
                    errors['missing_fields'] = []
                errors['missing_fields'].append(field)
        
        # Validate host
        if 'host' in credentials and credentials['host']:
            if not InputValidator.is_valid_host(credentials['host']):
                if 'host' not in errors:
                    errors['host'] = []
                errors['host'].append("Invalid host format")
        
        # Validate port
        if 'port' in credentials and credentials['port']:
            try:
                port = int(credentials['port'])
                if not InputValidator.is_valid_port(port):
                    if 'port' not in errors:
                        errors['port'] = []
                    errors['port'].append("Port must be between 1024 and 65535")
            except (ValueError, TypeError):
                if 'port' not in errors:
                    errors['port'] = []
                errors['port'].append("Port must be a valid integer")
        
        # Validate username
        if 'username' in credentials and credentials['username']:
            if not InputValidator.is_valid_username(credentials['username']):
                if 'username' not in errors:
                    errors['username'] = []
                errors['username'].append("Invalid username format")
        
        # Validate password
        if 'password' in credentials and credentials['password']:
            if not InputValidator.is_valid_password(credentials['password']):
                if 'password' not in errors:
                    errors['password'] = []
                errors['password'].append("Invalid password format")
        
        # Validate database name
        if 'database_name' in credentials and credentials['database_name']:
            if not InputValidator.is_valid_database_name(credentials['database_name']):
                if 'database_name' not in errors:
                    errors['database_name'] = []
                errors['database_name'].append("Invalid database name format")
        
        # Validate SSL mode
        if 'ssl_mode' in credentials and credentials['ssl_mode']:
            if 'database_type' in credentials:
                if not InputValidator.validate_ssl_mode(credentials['ssl_mode'], credentials['database_type']):
                    if 'ssl_mode' not in errors:
                        errors['ssl_mode'] = []
                    errors['ssl_mode'].append("Invalid SSL mode for database type")
        
        return errors
    
    @staticmethod
    def validate_query(query: str) -> Dict[str, List[str]]:
        """Validate SQL query for potential security issues."""
        errors = {}
        
        if not query or not query.strip():
            if 'query' not in errors:
                errors['query'] = []
            errors['query'].append("Query cannot be empty")
            return errors
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            (r'DROP\s+DATABASE', 'DROP DATABASE is not allowed'),
            (r'CREATE\s+DATABASE', 'CREATE DATABASE is not allowed'),
            (r'ALTER\s+DATABASE', 'ALTER DATABASE is not allowed'),
            (r'DROP\s+USER', 'DROP USER is not allowed'),
            (r'CREATE\s+USER', 'CREATE USER is not allowed'),
            (r'GRANT\s+ALL', 'GRANT ALL is not allowed'),
            (r'REVOKE\s+ALL', 'REVOKE ALL is not allowed'),
            (r'SHUTDOWN', 'SHUTDOWN is not allowed'),
            (r'KILL', 'KILL is not allowed'),
        ]
        
        query_upper = query.upper()
        for pattern, message in dangerous_patterns:
            if re.search(pattern, query_upper):
                if 'security' not in errors:
                    errors['security'] = []
                errors['security'].append(message)
        
        # Check for multiple statements (potential injection)
        if ';' in query and query.count(';') > 1:
            if 'security' not in errors:
                errors['security'] = []
            errors['security'].append("Multiple statements not allowed")
        
        return errors
    
    @staticmethod
    def sanitize_credentials(credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize credential values."""
        sanitized = {}
        
        for key, value in credentials.items():
            if isinstance(value, str):
                sanitized[key] = InputValidator.sanitize_input(value)
            else:
                sanitized[key] = value
        
        return sanitized


class ConnectionValidator:
    """Connection-specific validation utilities."""
    
    @staticmethod
    def validate_postgresql_connection(credentials: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate PostgreSQL connection parameters."""
        errors = InputValidator.validate_credentials(credentials)
        
        # PostgreSQL-specific validations
        if 'database_type' in credentials and credentials['database_type'].lower() != 'postgresql':
            if 'database_type' not in errors:
                errors['database_type'] = []
            errors['database_type'].append("Database type must be 'postgresql'")
        
        # Validate SSL mode
        if 'ssl_mode' in credentials and credentials['ssl_mode']:
            valid_ssl_modes = ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']
            if credentials['ssl_mode'].lower() not in valid_ssl_modes:
                if 'ssl_mode' not in errors:
                    errors['ssl_mode'] = []
                errors['ssl_mode'].append(f"Invalid SSL mode. Valid modes: {', '.join(valid_ssl_modes)}")
        
        return errors
    
    @staticmethod
    def validate_mysql_connection(credentials: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate MySQL connection parameters."""
        errors = InputValidator.validate_credentials(credentials)
        
        # MySQL-specific validations
        if 'database_type' in credentials and credentials['database_type'].lower() != 'mysql':
            if 'database_type' not in errors:
                errors['database_type'] = []
            errors['database_type'].append("Database type must be 'mysql'")
        
        # Validate SSL mode
        if 'ssl_mode' in credentials and credentials['ssl_mode']:
            valid_ssl_modes = ['disabled', 'preferred', 'required', 'verify_ca', 'verify_identity']
            if credentials['ssl_mode'].lower() not in valid_ssl_modes:
                if 'ssl_mode' not in errors:
                    errors['ssl_mode'] = []
                errors['ssl_mode'].append(f"Invalid SSL mode. Valid modes: {', '.join(valid_ssl_modes)}")
        
        return errors
    
    @staticmethod
    def get_default_port(database_type: str) -> int:
        """Get default port for database type."""
        default_ports = {
            'postgresql': 5432,
            'mysql': 3306
        }
        return default_ports.get(database_type.lower(), 5432)
    
    @staticmethod
    def get_default_ssl_mode(database_type: str) -> str:
        """Get default SSL mode for database type."""
        default_ssl_modes = {
            'postgresql': 'prefer',
            'mysql': 'required'
        }
        return default_ssl_modes.get(database_type.lower(), 'prefer') 