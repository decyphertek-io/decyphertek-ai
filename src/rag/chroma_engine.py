"""
ChromaDB-based RAG engine for conversation context retrieval
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import time
import hashlib
import os

from .embeddings import EmbeddingManager
from utils.logger import setup_logger

logger = setup_logger()


class ChromaRAGEngine:
    """RAG engine using ChromaDB for vector storage and retrieval"""
    
    def __init__(self, storage_dir: str, collection_name: str = "chat_rag"):
        """
        Initialize ChromaDB RAG engine
        
        Args:
            storage_dir: Directory to store ChromaDB data
            collection_name: Name of the ChromaDB collection
        """
        self.storage_dir = storage_dir
        self.collection_name = collection_name
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=storage_dir,
            anonymized_telemetry=False
        ))
        
        # Initialize embedding manager
        self.embedding_manager = EmbeddingManager()
        
        # Create or get collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"ChromaDB collection '{collection_name}' initialized")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB collection: {e}")
            raise
    
    def add_message(
        self,
        text: str,
        user_id: str,
        conversation_id: str,
        message_type: str = "user",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add a message to the RAG store
        
        Args:
            text: Message text
            user_id: User ID
            conversation_id: Conversation ID
            message_type: Type of message ("user", "assistant", "system")
            metadata: Additional metadata
            
        Returns:
            Message ID
        """
        try:
            # Generate message ID
            timestamp = int(time.time() * 1000)
            message_id = hashlib.md5(
                f"{text}{user_id}{conversation_id}{timestamp}".encode()
            ).hexdigest()
            
            # Generate embedding
            embedding = self.embedding_manager.encode(text)
            
            # Prepare metadata
            msg_metadata = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "timestamp": timestamp,
                "type": message_type
            }
            
            if metadata:
                msg_metadata.update(metadata)
            
            # Add to ChromaDB
            self.collection.add(
                ids=[message_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[msg_metadata]
            )
            
            logger.debug(f"Added message {message_id} to RAG store")
            return message_id
            
        except Exception as e:
            logger.error(f"Error adding message to RAG store: {e}")
            raise
    
    def search_context(
        self,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        limit: int = 5,
        include_keywords: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search for relevant context using hybrid search
        
        Args:
            query: Search query
            user_id: User ID to filter by
            conversation_id: Optional conversation ID to filter by
            limit: Maximum number of results
            include_keywords: Optional keywords for full-text search
            
        Returns:
            List of context items with text, metadata, and scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_manager.encode(query)
            
            # Build metadata filter
            where_filter = {"user_id": user_id}
            if conversation_id:
                where_filter["conversation_id"] = conversation_id
            
            # Build document filter for full-text search
            where_document = None
            if include_keywords:
                where_document = {
                    "$or": [
                        {"$contains": keyword}
                        for keyword in include_keywords
                    ]
                }
            
            # Perform hybrid search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter,
                where_document=where_document
            )
            
            # Format results
            context_items = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    context_items.append({
                        "id": results['ids'][0][i],
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "score": 1 - results['distances'][0][i]  # Convert distance to similarity
                    })
            
            logger.debug(f"Found {len(context_items)} context items for query")
            return context_items
            
        except Exception as e:
            logger.error(f"Error searching context: {e}")
            return []
    
    def build_rag_prompt(self, query: str, context: List[Dict]) -> str:
        """
        Build a prompt with retrieved context
        
        Args:
            query: User query
            context: List of context items from search
            
        Returns:
            Formatted prompt with context
        """
        if not context:
            return query
        
        # Build context string
        context_parts = []
        for i, item in enumerate(context, 1):
            msg_type = item['metadata'].get('type', 'unknown')
            text = item['text']
            context_parts.append(f"[{msg_type.capitalize()} Message {i}]\n{text}")
        
        context_str = "\n\n".join(context_parts)
        
        # Build full prompt
        prompt = f"""You are a helpful AI assistant. Use the following context from our previous conversation to provide a relevant and informed response.

Previous Context:
{context_str}

Current Question: {query}

Please provide a helpful response based on both the context above and your knowledge."""
        
        return prompt
    
    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get conversation history
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages
            
        Returns:
            List of messages sorted by timestamp
        """
        try:
            results = self.collection.get(
                where={"conversation_id": conversation_id},
                limit=limit
            )
            
            if not results['ids']:
                return []
            
            # Format and sort messages
            messages = []
            for i in range(len(results['ids'])):
                messages.append({
                    "id": results['ids'][i],
                    "text": results['documents'][i],
                    "metadata": results['metadatas'][i]
                })
            
            # Sort by timestamp
            messages.sort(key=lambda x: x['metadata'].get('timestamp', 0))
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete all messages from a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if successful
        """
        try:
            self.collection.delete(
                where={"conversation_id": conversation_id}
            )
            logger.info(f"Deleted conversation {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False
    
    def cleanup_old_messages(self, days_old: int = 30) -> int:
        """
        Delete messages older than specified days
        
        Args:
            days_old: Age threshold in days
            
        Returns:
            Number of messages deleted
        """
        try:
            cutoff_timestamp = int(time.time() * 1000) - (days_old * 24 * 60 * 60 * 1000)
            
            # Get count before deletion
            old_count = self.collection.count()
            
            # Delete old messages
            self.collection.delete(
                where={"timestamp": {"$lt": cutoff_timestamp}}
            )
            
            # Get count after deletion
            new_count = self.collection.count()
            deleted = old_count - new_count
            
            logger.info(f"Cleaned up {deleted} old messages")
            return deleted
            
        except Exception as e:
            logger.error(f"Error cleaning up old messages: {e}")
            return 0
    
    def get_stats(self) -> Dict:
        """
        Get RAG store statistics
        
        Returns:
            Dictionary with statistics
        """
        try:
            collection_info = self.collection.count()
            
            # Calculate storage size
            storage_size = self._get_storage_size()
            
            return {
                "total_messages": collection_info,
                "storage_size_mb": storage_size / (1024 * 1024),
                "embedding_dimension": self.embedding_manager.get_embedding_dimension(),
                "model_name": self.embedding_manager.model_name
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def _get_storage_size(self) -> int:
        """Calculate total storage size in bytes"""
        total = 0
        for dirpath, dirnames, filenames in os.walk(self.storage_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total += os.path.getsize(filepath)
        return total
    
    def export_conversation(self, conversation_id: str) -> Dict:
        """
        Export a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dictionary with conversation data
        """
        messages = self.get_conversation_history(conversation_id)
        
        return {
            "conversation_id": conversation_id,
            "message_count": len(messages),
            "messages": messages,
            "exported_at": int(time.time() * 1000)
        }

