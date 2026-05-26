"""
Sentrix Browser Security Module
Handles encryption, secure storage, and security utilities
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pathlib import Path
import hashlib


class SecurityManager:
    """Manages encryption and secure storage for Sentrix Browser"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key or self._get_or_create_key()
        self.fernet = Fernet(self.encryption_key.encode())
        
    def _get_or_create_key(self) -> str:
        """Get encryption key from environment or create a new one"""
        key_file = Path("~/.sentrix/master.key").expanduser()
        
        if key_file.exists():
            with open(key_file, 'r') as f:
                return f.read().strip()
        else:
            # Generate a new key
            key = Fernet.generate_key().decode()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'w') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple:
        """Hash a password with salt"""
        if salt is None:
            salt = os.urandom(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return (key.decode(), salt)
    
    def verify_password(self, password: str, hashed: str, salt: bytes) -> bool:
        """Verify a password against a hash"""
        key, _ = self.hash_password(password, salt)
        return key == hashed
    
    def secure_delete(self, file_path: str):
        """Securely delete a file by overwriting before deletion"""
        path = Path(file_path)
        if path.exists():
            # Overwrite with random data
            file_size = path.stat().st_size
            with open(path, 'wb') as f:
                f.write(os.urandom(file_size))
            # Delete the file
            path.unlink()
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a secure random token"""
        return base64.urlsafe_b64encode(os.urandom(length)).decode()
    
    def validate_url(self, url: str) -> bool:
        """Validate URL to prevent malicious URLs"""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            
            # Check for valid scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check for valid domain
            if not parsed.netloc:
                return False
            
            # Prevent common attack patterns
            dangerous_patterns = ['@', '..', 'javascript:', 'data:', 'file:']
            for pattern in dangerous_patterns:
                if pattern in url:
                    return False
            
            return True
        except Exception:
            return False


def get_security_manager(encryption_key: Optional[str] = None) -> SecurityManager:
    """Get a SecurityManager instance"""
    return SecurityManager(encryption_key)
