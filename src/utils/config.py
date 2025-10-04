"""
Application configuration management
"""

import json
import os
from pathlib import Path
from typing import Any, Optional


class AppConfig:
    """Manages application configuration"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory for config file (default: ~/.decyphertek-ai)
        """
        if config_dir is None:
            config_dir = os.path.join(
                os.getenv('HOME', '/data/data/io.decyphertek.ai'),
                '.decyphertek-ai'
            )
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        
        self._config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from file"""
        if not self.config_file.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Get default configuration"""
        return {
            "version": "1.0.0",
            "app": {
                "name": "DecypherTek AI",
                "theme": "system",
                "language": "en"
            },
            "security": {
                "session_timeout_minutes": 30,
                "require_auth_on_launch": True,
                "biometric_enabled": False
            },
            "chromadb": {
                "collection_name": "chat_rag",
                "embedding_model": "all-MiniLM-L6-v2",
                "max_results": 5
            },
            "pygpt": {
                "api_endpoint": "",
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "mcp": {
                "github_store_url": "https://github.com/decyphertek/mcp-store",
                "enabled_servers": []
            },
            "storage": {
                "max_conversations": 100,
                "cleanup_days": 30
            }
        }
    
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'app.theme')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save()
    
    def get_data_dir(self) -> Path:
        """Get application data directory"""
        return self.config_dir

