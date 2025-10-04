"""
Encryption utilities for secure credential storage
"""

import base64
import hashlib
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionManager:
    """Manages encryption/decryption of sensitive data"""
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password using PBKDF2
        
        Args:
            password: User password
            salt: Random salt bytes
            
        Returns:
            Derived key bytes
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    @staticmethod
    def generate_salt() -> bytes:
        """Generate random salt for key derivation"""
        return os.urandom(16)
    
    @staticmethod
    def hash_password(password: str, salt: bytes = None) -> tuple[str, bytes]:
        """
        Hash password using SHA-256
        
        Args:
            password: Password to hash
            salt: Optional salt (generated if not provided)
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = os.urandom(32)
        
        # Use PBKDF2 for password hashing
        pwdhash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        
        return base64.b64encode(pwdhash).decode('utf-8'), salt
    
    @staticmethod
    def verify_password(password: str, hashed: str, salt: bytes) -> bool:
        """
        Verify password against hash
        
        Args:
            password: Password to verify
            hashed: Stored password hash
            salt: Salt used for hashing
            
        Returns:
            True if password matches
        """
        new_hash, _ = EncryptionManager.hash_password(password, salt)
        return new_hash == hashed
    
    @staticmethod
    def encrypt(data: str, key: bytes) -> bytes:
        """
        Encrypt data using Fernet
        
        Args:
            data: String data to encrypt
            key: Encryption key
            
        Returns:
            Encrypted bytes
        """
        f = Fernet(key)
        return f.encrypt(data.encode())
    
    @staticmethod
    def decrypt(encrypted_data: bytes, key: bytes) -> str:
        """
        Decrypt data using Fernet
        
        Args:
            encrypted_data: Encrypted bytes
            key: Encryption key
            
        Returns:
            Decrypted string
        """
        f = Fernet(key)
        return f.decrypt(encrypted_data).decode()
    
    @staticmethod
    def generate_master_key() -> bytes:
        """Generate a random master encryption key"""
        return Fernet.generate_key()

