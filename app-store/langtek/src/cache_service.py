import json
import os
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

class CacheService:
    FEED_CACHE_KEY = 'cached_feeds'
    TRANSLATION_CACHE_TABLE = 'translation_cache'
    CACHE_EXPIRY_DAYS = 3  # Cache expiry in days
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheService, cls).__new__(cls)
            cls._instance._is_initialized = False
            cls._instance._db = None
        return cls._instance
    
    def __init__(self):
        if not self._is_initialized:
            self._init_database()
            self._is_initialized = True
    
    def _init_database(self):
        # Create cache directory if it doesn't exist
        cache_dir = Path.home() / '.langtek' / 'cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        db_path = cache_dir / 'cache.db'
        self._db = sqlite3.connect(str(db_path))
        
        # Create tables if they don't exist
        cursor = self._db.cursor()
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {self.TRANSLATION_CACHE_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_text TEXT,
            translated_text TEXT,
            language_from TEXT,
            language_to TEXT,
            translation_type TEXT,
            timestamp INTEGER
        )
        ''')
        self._db.commit()
    
    def cache_feeds(self, feeds):
        """Cache RSS feeds"""
        cache_dir = Path.home() / '.langtek' / 'cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_file = cache_dir / f"{self.FEED_CACHE_KEY}.json"
        
        cache_data = {
            'feeds': feeds,
            'timestamp': int(time.time() * 1000)  # Current time in milliseconds
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
    
    def get_cached_feeds(self):
        """Get cached feeds"""
        cache_file = Path.home() / '.langtek' / 'cache' / f"{self.FEED_CACHE_KEY}.json"
        
        if not cache_file.exists():
            return None
        
        with open(cache_file, 'r') as f:
            try:
                cache_map = json.load(f)
            except json.JSONDecodeError:
                return None
        
        timestamp = cache_map.get('timestamp', 0)
        cache_time = datetime.fromtimestamp(timestamp / 1000)  # Convert from milliseconds
        now = datetime.now()
        
        # Check if cache is expired
        if (now - cache_time).days > self.CACHE_EXPIRY_DAYS:
            return None
        
        return cache_map.get('feeds')
    
    def cache_translation(self, source_text, translated_text, language_from, language_to, translation_type):
        """Cache a translation"""
        cursor = self._db.cursor()
        
        # Check if translation already exists
        cursor.execute(
            f"SELECT id FROM {self.TRANSLATION_CACHE_TABLE} "
            f"WHERE source_text = ? AND language_from = ? AND language_to = ? AND translation_type = ?",
            (source_text, language_from, language_to, translation_type)
        )
        existing = cursor.fetchone()
        
        timestamp = int(time.time() * 1000)  # Current time in milliseconds
        
        if existing:
            # Update existing translation
            cursor.execute(
                f"UPDATE {self.TRANSLATION_CACHE_TABLE} "
                f"SET translated_text = ?, timestamp = ? "
                f"WHERE id = ?",
                (translated_text, timestamp, existing[0])
            )
        else:
            # Insert new translation
            cursor.execute(
                f"INSERT INTO {self.TRANSLATION_CACHE_TABLE} "
                f"(source_text, translated_text, language_from, language_to, translation_type, timestamp) "
                f"VALUES (?, ?, ?, ?, ?, ?)",
                (source_text, translated_text, language_from, language_to, translation_type, timestamp)
            )
        
        self._db.commit()
    
    def get_cached_translation(self, source_text, language_from, language_to, translation_type):
        """Get cached translation"""
        cursor = self._db.cursor()
        
        cursor.execute(
            f"SELECT translated_text, timestamp FROM {self.TRANSLATION_CACHE_TABLE} "
            f"WHERE source_text = ? AND language_from = ? AND language_to = ? AND translation_type = ?",
            (source_text, language_from, language_to, translation_type)
        )
        result = cursor.fetchone()
        
        if not result:
            return None
        
        translated_text, timestamp = result
        cache_time = datetime.fromtimestamp(timestamp / 1000)  # Convert from milliseconds
        now = datetime.now()
        
        # Check if cache is expired
        if (now - cache_time).days > self.CACHE_EXPIRY_DAYS:
            return None
        
        return translated_text
    
    def clear_expired_cache(self):
        """Clear expired cache entries"""
        cursor = self._db.cursor()
        
        expiry_timestamp = int((datetime.now() - timedelta(days=self.CACHE_EXPIRY_DAYS)).timestamp() * 1000)
        
        cursor.execute(
            f"DELETE FROM {self.TRANSLATION_CACHE_TABLE} WHERE timestamp < ?",
            (expiry_timestamp,)
        )
        
        self._db.commit()
    
    def close(self):
        """Close the database connection"""
        if self._is_initialized and self._db:
            self._db.close()
            self._is_initialized = False
