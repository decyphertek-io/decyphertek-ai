"""
Embedding model management
"""

from sentence_transformers import SentenceTransformer
from typing import List, Union
import os


class EmbeddingManager:
    """Manages text embedding generation"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: str = None):
        """
        Initialize embedding manager
        
        Args:
            model_name: Name of the sentence-transformers model
            cache_dir: Directory to cache the model
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or os.path.expanduser("~/.decyphertek-ai/models")
        
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load model (will download if not cached)
        self.model = SentenceTransformer(
            model_name,
            cache_folder=self.cache_dir
        )
        
        # Get embedding dimensions
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
    
    def encode(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text
        
        Args:
            text: Single text string or list of text strings
            
        Returns:
            Embedding(s) as list(s) of floats
        """
        embeddings = self.model.encode(text)
        
        # Convert numpy array to list
        if isinstance(text, str):
            return embeddings.tolist()
        else:
            return [emb.tolist() for emb in embeddings]
    
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for batch of texts
        
        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
            
        Returns:
            List of embeddings
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False
        )
        return [emb.tolist() for emb in embeddings]
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self.embedding_dim

