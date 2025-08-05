"""
Encryption manager for securing sensitive data.
Handles encryption and decryption of credentials and session data.
"""

import base64
import os
import sys
from typing import Optional
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Add project root to path for config import
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key or settings.encryption_key
        self.fernet = self._create_fernet()
    
    def _create_fernet(self) -> Fernet:
        """Create Fernet cipher from encryption key."""
        try:
            # Generate a key from the encryption key using PBKDF2
            salt = b'db_agent_salt_2024'  # Fixed salt for consistency
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key.encode()))
            return Fernet(key)
            
        except Exception as e:
            logger.error(f"Error creating Fernet cipher: {str(e)}")
            raise
    
    def encrypt(self, data: str) -> str:
        """Encrypt data string."""
        try:
            if not data:
                return ""
            
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data string."""
        try:
            if not encrypted_data:
                return ""
            
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Decrypt
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
            raise
    
    def encrypt_dict(self, data: dict) -> str:
        """Encrypt dictionary data."""
        try:
            import json
            json_data = json.dumps(data)
            return self.encrypt(json_data)
            
        except Exception as e:
            logger.error(f"Error encrypting dict: {str(e)}")
            raise
    
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """Decrypt data to dictionary."""
        try:
            import json
            json_data = self.decrypt(encrypted_data)
            return json.loads(json_data)
            
        except Exception as e:
            logger.error(f"Error decrypting dict: {str(e)}")
            raise
    
    def encrypt_credentials(self, credentials: dict) -> str:
        """Encrypt database credentials specifically."""
        try:
            # Create a copy to avoid modifying original
            creds_copy = credentials.copy()
            
            # Ensure password is encrypted
            if 'password' in creds_copy:
                creds_copy['password'] = self.encrypt(creds_copy['password'])
            
            return self.encrypt_dict(creds_copy)
            
        except Exception as e:
            logger.error(f"Error encrypting credentials: {str(e)}")
            raise
    
    def decrypt_credentials(self, encrypted_credentials: str) -> dict:
        """Decrypt database credentials specifically."""
        try:
            creds = self.decrypt_dict(encrypted_credentials)
            
            # Decrypt password if it exists
            if 'password' in creds:
                creds['password'] = self.decrypt(creds['password'])
            
            return creds
            
        except Exception as e:
            logger.error(f"Error decrypting credentials: {str(e)}")
            raise
    
    def generate_encryption_key(self) -> str:
        """Generate a new encryption key."""
        try:
            return Fernet.generate_key().decode()
            
        except Exception as e:
            logger.error(f"Error generating encryption key: {str(e)}")
            raise
    
    def validate_encryption_key(self, key: str) -> bool:
        """Validate if an encryption key is valid."""
        try:
            # Try to create a Fernet instance with the key
            test_fernet = Fernet(key.encode())
            
            # Test encryption/decryption
            test_data = "test_encryption"
            encrypted = test_fernet.encrypt(test_data.encode())
            decrypted = test_fernet.decrypt(encrypted).decode()
            
            return decrypted == test_data
            
        except Exception:
            return False


class SecureStorage:
    """Secure storage wrapper for sensitive data."""
    
    def __init__(self, encryption_manager: Optional[EncryptionManager] = None):
        self.encryption_manager = encryption_manager or EncryptionManager()
    
    def store_secure_data(self, key: str, data: dict) -> str:
        """Store data securely with encryption."""
        try:
            encrypted_data = self.encryption_manager.encrypt_dict(data)
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Error storing secure data for key {key}: {str(e)}")
            raise
    
    def retrieve_secure_data(self, key: str, encrypted_data: str) -> dict:
        """Retrieve and decrypt data."""
        try:
            return self.encryption_manager.decrypt_dict(encrypted_data)
            
        except Exception as e:
            logger.error(f"Error retrieving secure data for key {key}: {str(e)}")
            raise
    
    def store_credentials(self, key: str, credentials: dict) -> str:
        """Store database credentials securely."""
        try:
            return self.encryption_manager.encrypt_credentials(credentials)
            
        except Exception as e:
            logger.error(f"Error storing credentials for key {key}: {str(e)}")
            raise
    
    def retrieve_credentials(self, key: str, encrypted_credentials: str) -> dict:
        """Retrieve and decrypt database credentials."""
        try:
            return self.encryption_manager.decrypt_credentials(encrypted_credentials)
            
        except Exception as e:
            logger.error(f"Error retrieving credentials for key {key}: {str(e)}")
            raise


# Global encryption manager instance
encryption_manager = EncryptionManager()


def get_encryption_manager() -> EncryptionManager:
    """Get the global encryption manager instance."""
    return encryption_manager


def get_secure_storage() -> SecureStorage:
    """Get a secure storage instance."""
    return SecureStorage(encryption_manager) 