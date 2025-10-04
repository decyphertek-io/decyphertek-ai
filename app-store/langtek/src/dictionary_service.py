import os
import sqlite3
import shutil
import aiohttp
import asyncio
from pathlib import Path

class DictionaryService:
    _db_name = "es-en.sqlite3"
    _table_name = "translations"
    _column_spanish = "spanish"
    _column_english = "english"
    
    def __init__(self):
        self.db_path = os.path.join(Path.home(), self._db_name)
        self.connection = None
    
    async def initialize(self):
        if self.connection:
            return self.connection
        
        self.connection = await self._init_database()
        return self.connection
    
    async def _init_database(self):
        # Check if database exists in home directory
        db_exists = os.path.exists(self.db_path)
        
        if not db_exists:
            print(f"Copying database '{self._db_name}' from assets to {self.db_path}")
            try:
                # Ensure the assets directory exists
                assets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', self._db_name)
                
                if os.path.exists(assets_path):
                    shutil.copy(assets_path, self.db_path)
                    print(f"Database '{self._db_name}' copied successfully.")
                else:
                    print(f"Error: Database file not found at {assets_path}")
                    print("Please ensure 'assets/dictionaries/es-en.sqlite3' exists.")
                    raise FileNotFoundError(f"Database file not found at {assets_path}")
            except Exception as e:
                print(f"Error copying database '{self._db_name}': {str(e)}")
                raise
        
        print(f"Opening database at {self.db_path}")
        return sqlite3.connect(self.db_path)
    
    async def translate(self, word):
        """Translate a word from Spanish to English, using local DB first then API as fallback"""
        if not word or not word.strip():
            return word
        
        word = word.strip().lower()
        
        # Try local database first
        local_translation = await self.get_local_translation(word)
        if local_translation:
            return local_translation
        
        # Skip API translation entirely to avoid connection errors
        # Return the original word as fallback
        return word
    
    async def get_local_translation(self, spanish_word):
        if not self.connection:
            await self.initialize()
        
        search_word = spanish_word.lower()
        print(f"[DEBUG_TRANSLATE] Starting translation for: {search_word}")
        
        local_translation = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                f"SELECT {self._column_english} FROM {self._table_name} "
                f"WHERE LOWER({self._column_spanish}) = ? LIMIT 1",
                (search_word,)
            )
            result = cursor.fetchone()
            
            if result:
                local_translation = result[0]
                if local_translation:
                    print(f"Found '{search_word}' in local DB: {local_translation}")
                    return local_translation
        except Exception as e:
            print(f"Error querying local DB for '{search_word}': {str(e)}")
        
        print(f"No translation found for '{search_word}' in local DB.")
        return None
    
    async def add_word(self, spanish_word, english_translation):
        if not self.connection:
            await self.initialize()
        
        store_spanish_word = spanish_word.lower()
        print(f"[DEBUG_ADDWORD] Attempting to add/update: {store_spanish_word} -> {english_translation}")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                f"SELECT 1 FROM {self._table_name} "
                f"WHERE LOWER({self._column_spanish}) = ? LIMIT 1",
                (store_spanish_word,)
            )
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute(
                    f"UPDATE {self._table_name} SET {self._column_english} = ? "
                    f"WHERE LOWER({self._column_spanish}) = ?",
                    (english_translation, store_spanish_word)
                )
                self.connection.commit()
                print(f"Updated: {store_spanish_word} -> {english_translation}")
            else:
                cursor.execute(
                    f"INSERT INTO {self._table_name} ({self._column_spanish}, {self._column_english}) "
                    f"VALUES (?, ?)",
                    (store_spanish_word, english_translation)
                )
                self.connection.commit()
                print(f"Added: {store_spanish_word} -> {english_translation}")
        except Exception as e:
            print(f"Error adding/updating word ('{store_spanish_word}', '{english_translation}'): {str(e)}")
    
    async def update_translation(self, spanish_word, new_english_translation):
        if not self.connection:
            await self.initialize()
        
        store_spanish_word = spanish_word.lower()
        count = 0
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                f"UPDATE {self._table_name} SET {self._column_english} = ? "
                f"WHERE LOWER({self._column_spanish}) = ?",
                (new_english_translation, store_spanish_word)
            )
            self.connection.commit()
            count = cursor.rowcount
            
            if count > 0:
                print(f"Updated translation for '{store_spanish_word}' to '{new_english_translation}' ({count} rows affected)")
            else:
                print(f"No entry found for '{store_spanish_word}' to update.")
        except Exception as e:
            print(f"Error updating translation for '{store_spanish_word}': {str(e)}")
        
        return count
    
    async def translate_multiple(self, spanish_words):
        translations = {}
        try:
            for word in spanish_words:
                translations[word] = await self.translate(word)
        except Exception as e:
            print(f"Error translating multiple words: {str(e)}")
        
        return translations
    
    async def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            print("Database closed.")
