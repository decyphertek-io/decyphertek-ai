"""
Document management for RAG using Qdrant + OpenRouter embeddings
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from pathlib import Path
from typing import List, Optional, Dict
import hashlib
import json
import httpx


class DocumentManager:
    """Manages documents for RAG with Qdrant (mobile-friendly)"""
    
    def __init__(self, storage_dir: str, openrouter_api_key: Optional[str] = None):
        """
        Initialize document manager
        
        Args:
            storage_dir: Directory for Qdrant storage
            openrouter_api_key: OpenRouter API key for embeddings
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Qdrant client (local/embedded mode)
        self.client = QdrantClient(path=str(self.storage_dir / "qdrant"))
        
        # OpenRouter API settings
        self.api_key = openrouter_api_key
        self.embedding_model = "openai/text-embedding-3-small"  # Fast, cheap
        self.embedding_dim = 1536
        
        # Create collection if it doesn't exist
        self._init_collection()
        
        # Document metadata storage
        self.docs_file = self.storage_dir / "documents.json"
        self.documents = self._load_documents()
        
        # Document content storage directory
        self.docs_storage_dir = self.storage_dir / "documents"
        self.docs_storage_dir.mkdir(exist_ok=True)
    
    def _init_collection(self):
        """Initialize Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            if not any(c.name == "documents" for c in collections):
                # Create collection
                self.client.create_collection(
                    collection_name="documents",
                    vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE)
                )
                print("[DocumentManager] Created Qdrant collection")
        except Exception as e:
            print(f"[DocumentManager] Error initializing collection: {e}")
    
    def _load_documents(self) -> dict:
        """Load document metadata from documents.json"""
        try:
            if self.docs_file.exists():
                with open(self.docs_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            print(f"[DocumentManager] Error loading documents: {e}")
            return {}
    
    def get_documents(self) -> dict:
        """Get all document metadata"""
        return self.documents
    
    def set_api_key(self, api_key: str):
        """Update OpenRouter API key"""
        self.api_key = api_key
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding using OpenRouter API
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        if not self.api_key:
            print("[DocumentManager] No API key set for embeddings")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.embedding_model,
                        "input": text
                    }
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return data['data'][0]['embedding']
                    except Exception as json_error:
                        print(f"[DocumentManager] JSON parsing error: {json_error}")
                        print(f"[DocumentManager] Response content: {response.text[:200]}")
                        return None
                else:
                    print(f"[DocumentManager] Embedding API error: {response.status_code}")
                    print(f"[DocumentManager] Response content: {response.text[:200]}")
                    return None
                    
        except Exception as e:
            print(f"[DocumentManager] Error generating embedding: {e}")
            return None
    
    async def add_document(self, content: str, filename: str, source: str = "upload") -> bool:
        """
        Add document to RAG store
        
        Args:
            content: Document text content
            filename: Original filename
            source: Source of document (upload, nextcloud, google-drive)
            
        Returns:
            True if successful
        """
        try:
            # Use original filename as doc_id, but handle conflicts
            import time
            timestamp = int(time.time() * 1000)
            doc_id = filename
            
            # Check if filename already exists and handle conflicts
            if doc_id in self.documents:
                # Check if it's the same content by comparing file sizes and content
                existing_doc = self.documents[doc_id]
                existing_file_path = Path(existing_doc.get("file_path", ""))
                
                if existing_file_path.exists():
                    existing_size = existing_file_path.stat().st_size
                    if existing_size == len(content):
                        # Same size, check if content is identical
                        existing_content = existing_file_path.read_text(encoding="utf-8")
                        if existing_content == content:
                            print(f"[DocumentManager] Document {filename} already exists with identical content")
                            return False
                
                # Different content, create unique filename
                name_parts = filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    base_name, extension = name_parts
                    doc_id = f"{base_name}_{timestamp}.{extension}"
                else:
                    doc_id = f"{filename}_{timestamp}"
                
                print(f"[DocumentManager] Filename conflict detected, using: {doc_id}")
            
            print(f"[DocumentManager] Using doc_id: {doc_id}")
            print(f"[DocumentManager] Current documents count: {len(self.documents)}")
            print(f"[DocumentManager] Current document IDs: {list(self.documents.keys())}")
            
            # Split content into chunks
            chunks = self._chunk_text(content)
            print(f"[DocumentManager] Split {filename} into {len(chunks)} chunks")
            
            # Check if we have API key for embeddings
            if not self.api_key:
                print(f"[DocumentManager] No OpenRouter API key available - cannot generate embeddings")
                print(f"[DocumentManager] Document {filename} will be stored but not indexed for search")
                # Store document without embeddings
                doc_file_path = self.docs_storage_dir / filename
                doc_file_path.write_text(content, encoding="utf-8")
                
                # Store document metadata
                self.documents[doc_id] = {
                    "filename": filename,
                    "source": source,
                    "chunks": len(chunks),
                    "size": len(content),
                    "file_path": str(doc_file_path),
                    "created_at": timestamp,
                    "indexed": False,
                    "reason": "No API key for embeddings"
                }
                self._save_documents()
                
                print(f"[DocumentManager] Added {filename} without embeddings (ID: {doc_id})")
                return True
            
            # Generate embeddings for all chunks
            points = []
            for i, chunk in enumerate(chunks):
                embedding = await self.generate_embedding(chunk)
                if not embedding:
                    print(f"[DocumentManager] Failed to generate embedding for chunk {i}")
                    continue
                
                point = PointStruct(
                    id=f"{doc_id}_{i}",
                    vector=embedding,
                    payload={
                        "text": chunk,
                        "filename": filename,
                        "source": source,
                        "doc_id": doc_id,
                        "chunk_index": i
                    }
                )
                points.append(point)
            
            # Add to Qdrant
            # Store document content to file with original filename
            doc_file_path = self.docs_storage_dir / filename
            doc_file_path.write_text(content, encoding="utf-8")
            
            if points:
                self.client.upsert(
                    collection_name="documents",
                    points=points
                )
                
                # Store document metadata with embeddings
                self.documents[doc_id] = {
                    "filename": filename,
                    "source": source,
                    "chunks": len(chunks),
                    "size": len(content),
                    "file_path": str(doc_file_path),
                    "created_at": timestamp,
                    "indexed": True,
                    "embedded_chunks": len(points)
                }
                
                print(f"[DocumentManager] Added {filename} with {len(points)} chunks (ID: {doc_id})")
            else:
                # Store document metadata without embeddings
                self.documents[doc_id] = {
                    "filename": filename,
                    "source": source,
                    "chunks": len(chunks),
                    "size": len(content),
                    "file_path": str(doc_file_path),
                    "created_at": timestamp,
                    "indexed": False,
                    "reason": "Embedding generation failed"
                }
                
                print(f"[DocumentManager] Added {filename} without embeddings (ID: {doc_id})")
            
            self._save_documents()
            print(f"[DocumentManager] Total documents now: {len(self.documents)}")
            print(f"[DocumentManager] Document metadata: {self.documents[doc_id]}")
            return True
            
        except Exception as e:
            print(f"[DocumentManager] Error adding document: {e}")
            return False
    
    async def query_documents(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Query documents for relevant context
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of relevant document chunks
        """
        try:
            # Generate embedding for query
            query_embedding = await self.generate_embedding(query)
            if not query_embedding:
                return []
            
            # Search in Qdrant
            results = self.client.search(
                collection_name="documents",
                query_vector=query_embedding,
                limit=n_results
            )
            
            # Format results
            formatted = []
            for result in results:
                formatted.append({
                    "content": result.payload.get("text", ""),
                    "filename": result.payload.get("filename", ""),
                    "source": result.payload.get("source", ""),
                    "score": result.score
                })
            
            return formatted
            
        except Exception as e:
            print(f"[DocumentManager] Error querying documents: {e}")
            return []
    
    def get_documents(self) -> Dict[str, Dict]:
        """Get all documents metadata"""
        print(f"[DocumentManager] get_documents() called - returning {len(self.documents)} documents")
        print(f"[DocumentManager] Document IDs: {list(self.documents.keys())}")
        return self.documents
    
    def get_document_content(self, doc_id: str) -> Optional[str]:
        """Get document content from storage"""
        try:
            if doc_id not in self.documents:
                return None
            
            doc_info = self.documents[doc_id]
            file_path = doc_info.get("file_path")
            
            if file_path and Path(file_path).exists():
                return Path(file_path).read_text(encoding="utf-8")
            else:
                # Fallback: try to read from docs storage directory
                doc_file_path = self.docs_storage_dir / f"{doc_id}.txt"
                if doc_file_path.exists():
                    return doc_file_path.read_text(encoding="utf-8")
                else:
                    return None
                    
        except Exception as e:
            print(f"[DocumentManager] Error reading document {doc_id}: {e}")
            return None
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document from RAG store
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful
        """
        try:
            if doc_id not in self.documents:
                return False
            
            # Delete all points with this doc_id
            self.client.delete(
                collection_name="documents",
                points_selector={
                    "filter": {
                        "must": [
                            {"key": "doc_id", "match": {"value": doc_id}}
                        ]
                    }
                }
            )
            
            # Remove stored document file
            doc_info = self.documents[doc_id]
            file_path = doc_info.get("file_path")
            if file_path and Path(file_path).exists():
                Path(file_path).unlink()
            
            # Remove from metadata
            del self.documents[doc_id]
            self._save_documents()
            
            print(f"[DocumentManager] Deleted document {doc_id}")
            return True
            
        except Exception as e:
            print(f"[DocumentManager] Error deleting document: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            collection_info = self.client.get_collection("documents")
            total_chunks = collection_info.points_count
            total_docs = len(self.documents)
            total_size = sum(doc['size'] for doc in self.documents.values())
            
            return {
                "documents": total_docs,
                "chunks": total_chunks,
                "size_bytes": total_size,
                "size_mb": round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            print(f"[DocumentManager] Error getting stats: {e}")
            return {"documents": 0, "chunks": 0, "size_bytes": 0, "size_mb": 0}
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks if chunks else [text]
    
    def _load_documents(self) -> Dict:
        """Load document metadata from file"""
        if self.docs_file.exists():
            try:
                with open(self.docs_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[DocumentManager] Error loading documents: {e}")
        return {}
    
    def _save_documents(self):
        """Save document metadata to file"""
        try:
            with open(self.docs_file, 'w') as f:
                json.dump(self.documents, f, indent=2)
        except Exception as e:
            print(f"[DocumentManager] Error saving documents: {e}")
