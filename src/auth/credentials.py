"""
Credential management for local authentication
"""

import json
import os
from pathlib import Path
from typing import Optional
import base64

from .encryption import EncryptionManager


class CredentialManager:
    """Manages user credentials with encryption"""
    
    def __init__(self, storage_dir: str):
        """
        Initialize credential manager
        
        Args:
            storage_dir: Directory to store encrypted credentials
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.credentials_file = self.storage_dir / "credentials.enc"
        self.config_file = self.storage_dir / "config.json"
        
        self.encryption_manager = EncryptionManager()
    
    def has_credentials(self) -> bool:
        """Check if credentials file exists"""
        return self.credentials_file.exists()
    
    def create_credentials(self, username: str, password: str) -> bool:
        """
        Create and store new credentials
        
        Args:
            username: Username
            password: Password
            
        Returns:
            True if successful
        """
        try:
            # Validate input
            if not self._validate_username(username):
                raise ValueError("Invalid username")
            if not self._validate_password(password):
                raise ValueError("Invalid password")
            
            # Generate salt and hash password
            password_hash, salt = self.encryption_manager.hash_password(password)
            
            # Create credentials data
            credentials_data = {
                "username": username,
                "password_hash": password_hash,
                "salt": base64.b64encode(salt).decode('utf-8'),
                "version": "1.0"
            }
            
            # Generate master key for encrypting other data
            master_key = self.encryption_manager.generate_master_key()
            
            # Encrypt credentials
            credentials_json = json.dumps(credentials_data)
            encrypted = self.encryption_manager.encrypt(credentials_json, master_key)
            
            # Store encrypted credentials
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted)
            
            # Store master key encrypted with password
            self._store_master_key(master_key, password, salt)
            
            # Create initial config
            self._create_initial_config(username)
            
            return True
            
        except Exception as e:
            print(f"Error creating credentials: {e}")
            return False
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """
        Verify credentials
        
        Args:
            username: Username to verify
            password: Password to verify
            
        Returns:
            True if credentials are valid
        """
        try:
            if not self.has_credentials():
                return False
            
            # Load and decrypt credentials
            credentials = self._load_credentials(password)
            if not credentials:
                return False
            
            # Verify username and password
            stored_username = credentials.get('username')
            stored_hash = credentials.get('password_hash')
            salt = base64.b64decode(credentials.get('salt'))
            
            if stored_username != username:
                return False
            
            return self.encryption_manager.verify_password(password, stored_hash, salt)
            
        except Exception as e:
            print(f"Error verifying credentials: {e}")
            return False
    
    def get_username(self, password: str) -> Optional[str]:
        """
        Get stored username (requires password to decrypt)
        
        Args:
            password: Password to decrypt credentials
            
        Returns:
            Username if successful, None otherwise
        """
        credentials = self._load_credentials(password)
        return credentials.get('username') if credentials else None
    
    def get_master_key(self, password: str) -> Optional[bytes]:
        """
        Get master key for encrypting other data (like API keys)
        
        Args:
            password: Password to decrypt master key
            
        Returns:
            Master key bytes or None
        """
        print(f"Getting master key with password length: {len(password)}")
        return self._load_master_key(password)
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            username: Username
            old_password: Current password
            new_password: New password
            
        Returns:
            True if successful
        """
        try:
            # Verify old credentials
            if not self.verify_credentials(username, old_password):
                return False
            
            # Delete old credentials
            self.delete_credentials()
            
            # Create new credentials
            return self.create_credentials(username, new_password)
            
        except Exception as e:
            print(f"Error changing password: {e}")
            return False
    
    def delete_credentials(self) -> bool:
        """
        Delete stored credentials
        
        Returns:
            True if successful
        """
        try:
            if self.credentials_file.exists():
                self.credentials_file.unlink()
            
            master_key_file = self.storage_dir / "master.key"
            if master_key_file.exists():
                master_key_file.unlink()
            
            return True
            
        except Exception as e:
            print(f"Error deleting credentials: {e}")
            return False
    
    def _load_credentials(self, password: str) -> Optional[dict]:
        """Load and decrypt credentials"""
        try:
            # Load master key
            master_key = self._load_master_key(password)
            if not master_key:
                return None
            
            # Load and decrypt credentials
            with open(self.credentials_file, 'rb') as f:
                encrypted = f.read()
            
            decrypted = self.encryption_manager.decrypt(encrypted, master_key)
            return json.loads(decrypted)
            
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None
    
    def _store_master_key(self, master_key: bytes, password: str, salt: bytes):
        """Store master key encrypted with password (with salt prepended)"""
        key = self.encryption_manager.derive_key(password, salt)
        encrypted_master_key = self.encryption_manager.encrypt(
            base64.b64encode(master_key).decode('utf-8'),
            key
        )
        
        master_key_file = self.storage_dir / "master.key"
        with open(master_key_file, 'wb') as f:
            # Write salt first (16 bytes), then encrypted master key
            f.write(salt)
            f.write(encrypted_master_key)
        
        print(f"Master key stored at: {master_key_file} (salt: {len(salt)} bytes, encrypted: {len(encrypted_master_key)} bytes)")
    
    def _load_master_key(self, password: str) -> Optional[bytes]:
        """Load master key using password (salt is stored with the key)"""
        try:
            master_key_file = self.storage_dir / "master.key"
            if not master_key_file.exists():
                print(f"Master key file not found at: {master_key_file}")
                return None
            
            with open(master_key_file, 'rb') as f:
                # Read salt (first 32 bytes - from hash_password which uses os.urandom(32))
                salt = f.read(32)
                if len(salt) != 32:
                    print(f"Invalid salt length: {len(salt)}, expected 32")
                    return None
                # Read encrypted master key (rest of file)
                encrypted_master_key = f.read()
                if not encrypted_master_key:
                    print("Empty encrypted master key")
                    return None
            
            # Derive key from password and salt
            key = self.encryption_manager.derive_key(password, salt)
            
            # Decrypt master key
            decrypted = self.encryption_manager.decrypt(encrypted_master_key, key)
            return base64.b64decode(decrypted)
            
        except Exception as e:
            import traceback
            print(f"Error loading master key: {type(e).__name__}: {e}")
            traceback.print_exc()
            return None
    
    def _create_initial_config(self, username: str):
        """Create initial configuration file"""
        config = {
            "username": username,
            "version": "1.0.0",
            "theme": "system",
            "first_launch": True,
            "features": {
                "biometric_enabled": False,
                "auto_logout_minutes": 30
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _validate_username(self, username: str) -> bool:
        """Validate username format"""
        if not username or len(username) < 3 or len(username) > 32:
            return False
        if not username.replace('_', '').replace('-', '').isalnum():
            return False
        return True
    
    def _validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if not password or len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        return has_upper and has_lower and has_digit

