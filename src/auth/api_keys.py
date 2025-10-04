"""
API Key management with encryption
"""

import json
from pathlib import Path
from typing import Optional
import base64

from .encryption import EncryptionManager


class APIKeyManager:
    """Manages API keys with encryption"""
    
    def __init__(self, storage_dir: str, master_key: bytes):
        """
        Initialize API key manager
        
        Args:
            storage_dir: Directory to store encrypted API keys
            master_key: Master encryption key
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.api_keys_file = self.storage_dir / "api_keys.enc"
        self.master_key = master_key
        self.encryption_manager = EncryptionManager()
        
        # Cache for decrypted keys (in-memory only)
        self._keys_cache = None
    
    def has_openrouter_key(self) -> bool:
        """Check if OpenRouter API key exists"""
        keys = self._load_keys()
        return keys and 'openrouter' in keys and keys['openrouter'].get('api_key')
    
    def store_openrouter_key(self, api_key: str, model: str = "qwen/qwen-2.5-coder-32b-instruct") -> bool:
        """
        Store OpenRouter API key
        
        Args:
            api_key: OpenRouter API key
            model: Default model to use
            
        Returns:
            True if successful
        """
        try:
            # Load existing keys or create new dict
            keys = self._load_keys() or {}
            
            # Store OpenRouter configuration
            keys['openrouter'] = {
                'api_key': api_key,
                'model': model,
                'base_url': 'https://openrouter.ai/api/v1'
            }
            
            # Save encrypted
            self._save_keys(keys)
            
            # Update cache
            self._keys_cache = keys
            
            return True
            
        except Exception as e:
            print(f"Error storing OpenRouter key: {e}")
            return False
    
    def get_openrouter_config(self) -> Optional[dict]:
        """
        Get OpenRouter configuration
        
        Returns:
            Dict with api_key, model, and base_url, or None
        """
        keys = self._load_keys()
        return keys.get('openrouter') if keys else None
    
    def delete_openrouter_key(self) -> bool:
        """
        Delete OpenRouter API key
        
        Returns:
            True if successful
        """
        try:
            keys = self._load_keys()
            if keys and 'openrouter' in keys:
                del keys['openrouter']
                self._save_keys(keys)
                self._keys_cache = keys
            
            return True
            
        except Exception as e:
            print(f"Error deleting OpenRouter key: {e}")
            return False
    
    # Ollama Configuration Methods
    
    def get_ollama_config(self) -> Optional[dict]:
        """Get Ollama configuration"""
        keys = self._load_keys()
        return keys.get('ollama') if keys else None
    
    def store_ollama_config(self, model: str = "gemma2:2b", host: str = "http://localhost:11434") -> bool:
        """
        Store Ollama configuration
        
        Args:
            model: Ollama model name
            host: Ollama server host
        Returns:
            True if successful
        """
        try:
            keys = self._load_keys() or {}
            keys['ollama'] = {
                "model": model,
                "host": host
            }
            self._save_keys(keys)
            self._keys_cache = keys
            return True
        except Exception as e:
            print(f"Error storing Ollama config: {e}")
            return False
    
    def get_duckduckgo_config(self) -> Optional[dict]:
        """Get DuckDuckGo AI configuration"""
        keys = self._load_keys()
        return keys.get('duckduckgo') if keys else None
    
    def store_duckduckgo_config(self, model: str = "gpt-4o-mini") -> bool:
        """
        Store DuckDuckGo AI configuration
        
        Args:
            model: DuckDuckGo model name
        Returns:
            True if successful
        """
        try:
            keys = self._load_keys() or {}
            keys['duckduckgo'] = {
                "model": model
            }
            self._save_keys(keys)
            self._keys_cache = keys
            return True
        except Exception as e:
            print(f"Error storing DuckDuckGo config: {e}")
            return False
    
    # AI Provider Selection
    
    def get_ai_provider(self) -> str:
        """Get currently selected AI provider (openrouter, ollama, or duckduckgo)"""
        keys = self._load_keys()
        return keys.get('ai_provider', 'openrouter') if keys else 'openrouter'
    
    def set_ai_provider(self, provider: str) -> bool:
        """
        Set AI provider
        
        Args:
            provider: 'openrouter', 'ollama', or 'duckduckgo'
        Returns:
            True if successful
        """
        if provider not in ['openrouter', 'ollama', 'duckduckgo']:
            return False
        
        try:
            keys = self._load_keys() or {}
            keys['ai_provider'] = provider
            self._save_keys(keys)
            self._keys_cache = keys
            return True
        except Exception as e:
            print(f"Error setting AI provider: {e}")
            return False
    
    def update_openrouter_model(self, model: str) -> bool:
        """
        Update default OpenRouter model
        
        Args:
            model: Model identifier
            
        Returns:
            True if successful
        """
        try:
            keys = self._load_keys()
            if keys and 'openrouter' in keys:
                keys['openrouter']['model'] = model
                self._save_keys(keys)
                self._keys_cache = keys
                return True
            
            return False
            
        except Exception as e:
            print(f"Error updating model: {e}")
            return False
    
    def _load_keys(self) -> Optional[dict]:
        """Load and decrypt API keys"""
        # Check cache first
        if self._keys_cache is not None:
            return self._keys_cache
        
        try:
            if not self.api_keys_file.exists():
                return None
            
            # Load and decrypt
            with open(self.api_keys_file, 'rb') as f:
                encrypted = f.read()
            
            decrypted = self.encryption_manager.decrypt(encrypted, self.master_key)
            keys = json.loads(decrypted)
            
            # Cache it
            self._keys_cache = keys
            
            return keys
            
        except Exception as e:
            print(f"Error loading API keys: {e}")
            return None
    
    def _save_keys(self, keys: dict):
        """Encrypt and save API keys"""
        try:
            # Encrypt
            keys_json = json.dumps(keys)
            encrypted = self.encryption_manager.encrypt(keys_json, self.master_key)
            
            # Save
            with open(self.api_keys_file, 'wb') as f:
                f.write(encrypted)
                
        except Exception as e:
            print(f"Error saving API keys: {e}")
            raise

