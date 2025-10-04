"""
Ollama Local AI Client
Provides local LLM access without API keys or internet
"""

from typing import List, Dict, Optional, AsyncIterator
import ollama
from ollama import AsyncClient


class OllamaClient:
    """Client for local Ollama AI models"""

    def __init__(self, model: str = "gemma2:2b", host: str = "http://localhost:11434"):
        """
        Initialize Ollama client
        
        Args:
            model: Model to use (default: gemma2:2b - lightweight)
            host: Ollama server host
        """
        self.model = model
        self.host = host
        self.client = AsyncClient(host=host)
        
        print(f"[Ollama] Initialized with model: {model}")
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test connection to Ollama server"""
        try:
            # Try to list models to verify connection
            models = await self.client.list()
            
            if not models.get('models'):
                return False, "No models found. Run: ollama pull gemma2:2b"
            
            # Check if our model is available
            model_names = [m['name'] for m in models['models']]
            if self.model not in model_names:
                available = ", ".join(model_names[:3])
                return False, f"Model '{self.model}' not found. Available: {available}"
            
            return True, f"✓ Connected to Ollama ({len(model_names)} models)"
            
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    async def send_message(self, messages: List[Dict[str, str]], 
                          stream: bool = False) -> Optional[str]:
        """
        Send chat message
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream response (not used for now)
            
        Returns:
            Response text or None on error
        """
        try:
            print(f"[Ollama] Sending request to {self.model} with {len(messages)} messages")
            
            response = await self.client.chat(
                model=self.model,
                messages=messages
            )
            
            content = response['message']['content']
            print(f"[Ollama] Success! Response length: {len(content)} chars")
            return content
            
        except Exception as e:
            print(f"[Ollama] Error: {type(e).__name__}: {e}")
            return None
    
    async def stream_message(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """
        Stream chat message response
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Yields:
            Chunks of response text
        """
        try:
            stream = await self.client.chat(
                model=self.model,
                messages=messages,
                stream=True
            )
            
            async for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
                    
        except Exception as e:
            print(f"[Ollama] Stream error: {e}")
    
    async def get_available_models(self) -> List[str]:
        """Get list of locally available Ollama models"""
        try:
            models = await self.client.list()
            return [m['name'] for m in models.get('models', [])]
        except Exception as e:
            print(f"[Ollama] Error listing models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> tuple[bool, str]:
        """
        Pull a model from Ollama registry
        
        Args:
            model_name: Name of model to pull
            
        Returns:
            (success, message)
        """
        try:
            print(f"[Ollama] Pulling model: {model_name}")
            await self.client.pull(model_name)
            return True, f"✓ Model '{model_name}' pulled successfully"
        except Exception as e:
            return False, f"Failed to pull model: {str(e)}"
    
    def get_ollama_library(self) -> List[Dict[str, str]]:
        """
        Get curated list of Ollama models from https://ollama.com/library
        Organized by category and use case
        """
        return [
            # Ultra Lightweight (Mobile Optimized)
            {
                "name": "qwen2.5:0.5b",
                "display_name": "Qwen 2.5 0.5B",
                "size": "400 MB",
                "category": "Ultra Lightweight",
                "description": "Smallest model, very fast - perfect for mobile",
                "tags": ["mobile", "fast", "multilingual"],
                "command": "ollama pull qwen2.5:0.5b"
            },
            {
                "name": "tinyllama",
                "display_name": "TinyLlama 1.1B",
                "size": "637 MB",
                "category": "Ultra Lightweight",
                "description": "Compact 1.1B model, great for resource-constrained devices",
                "tags": ["mobile", "fast", "lightweight"],
                "command": "ollama pull tinyllama"
            },
            {
                "name": "qwen3:0.6b",
                "display_name": "Qwen 3 0.6B",
                "size": "600 MB",
                "category": "Ultra Lightweight",
                "description": "Latest generation Qwen, excellent for mobile",
                "tags": ["mobile", "fast", "latest"],
                "command": "ollama pull qwen3:0.6b"
            },
            
            # Lightweight (1-2GB)
            {
                "name": "llama3.2:1b",
                "display_name": "Llama 3.2 1B",
                "size": "1.3 GB",
                "category": "Lightweight",
                "description": "Meta's compact Llama 3.2 - balanced performance",
                "tags": ["mobile", "balanced", "meta"],
                "command": "ollama pull llama3.2:1b"
            },
            {
                "name": "gemma2:2b",
                "display_name": "Gemma 2 2B",
                "size": "1.6 GB",
                "category": "Lightweight",
                "description": "Google's efficient model - best quality for size",
                "tags": ["mobile", "quality", "google"],
                "command": "ollama pull gemma2:2b"
            },
            {
                "name": "qwen2.5:1.5b",
                "display_name": "Qwen 2.5 1.5B",
                "size": "1.5 GB",
                "category": "Lightweight",
                "description": "High-quality 1.5B model with multilingual support",
                "tags": ["mobile", "multilingual", "quality"],
                "command": "ollama pull qwen2.5:1.5b"
            },
            
            # Small (3-7GB)
            {
                "name": "phi3:mini",
                "display_name": "Phi 3 Mini",
                "size": "2.3 GB",
                "category": "Small",
                "description": "Microsoft's Phi-3 - excellent quality/size ratio",
                "tags": ["quality", "efficient", "microsoft"],
                "command": "ollama pull phi3:mini"
            },
            {
                "name": "llama3.2:3b",
                "display_name": "Llama 3.2 3B",
                "size": "3 GB",
                "category": "Small",
                "description": "Meta's 3B model - great for desktop",
                "tags": ["quality", "balanced", "meta"],
                "command": "ollama pull llama3.2:3b"
            },
            {
                "name": "mistral:7b",
                "display_name": "Mistral 7B",
                "size": "4 GB",
                "category": "Small",
                "description": "Mistral AI's flagship 7B - high performance",
                "tags": ["quality", "popular", "tools"],
                "command": "ollama pull mistral:7b"
            },
            {
                "name": "qwen2.5:7b",
                "display_name": "Qwen 2.5 7B",
                "size": "4.7 GB",
                "category": "Small",
                "description": "Powerful 7B model with 128K context",
                "tags": ["quality", "multilingual", "long-context"],
                "command": "ollama pull qwen2.5:7b"
            },
            
            # Medium (8-14GB)
            {
                "name": "llama3.1:8b",
                "display_name": "Llama 3.1 8B",
                "size": "8 GB",
                "category": "Medium",
                "description": "Meta's powerful 8B model with tool calling",
                "tags": ["quality", "tools", "popular"],
                "command": "ollama pull llama3.1:8b"
            },
            {
                "name": "gemma2:9b",
                "display_name": "Gemma 2 9B",
                "size": "9 GB",
                "category": "Medium",
                "description": "Google's 9B model - high performance",
                "tags": ["quality", "google", "efficient"],
                "command": "ollama pull gemma2:9b"
            },
            {
                "name": "phi4:14b",
                "display_name": "Phi 4 14B",
                "size": "14 GB",
                "category": "Medium",
                "description": "Microsoft's state-of-the-art 14B model",
                "tags": ["quality", "latest", "microsoft"],
                "command": "ollama pull phi4:14b"
            },
            
            # Large (Requires Powerful Hardware)
            {
                "name": "llama3.1:70b",
                "display_name": "Llama 3.1 70B",
                "size": "70 GB",
                "category": "Large",
                "description": "Meta's most capable open model",
                "tags": ["quality", "powerful", "tools"],
                "command": "ollama pull llama3.1:70b"
            },
            {
                "name": "qwen2.5:72b",
                "display_name": "Qwen 2.5 72B",
                "size": "72 GB",
                "category": "Large",
                "description": "Massive 72B model for demanding tasks",
                "tags": ["quality", "powerful", "multilingual"],
                "command": "ollama pull qwen2.5:72b"
            },
            
            # Specialized Models
            {
                "name": "qwen2.5-coder:7b",
                "display_name": "Qwen 2.5 Coder 7B",
                "size": "4.7 GB",
                "category": "Specialized",
                "description": "Optimized for code generation and reasoning",
                "tags": ["coding", "quality", "tools"],
                "command": "ollama pull qwen2.5-coder:7b"
            },
            {
                "name": "deepseek-r1:7b",
                "display_name": "DeepSeek R1 7B",
                "size": "7 GB",
                "category": "Specialized",
                "description": "Advanced reasoning model by DeepSeek",
                "tags": ["reasoning", "thinking", "quality"],
                "command": "ollama pull deepseek-r1:7b"
            },
            {
                "name": "nomic-embed-text",
                "display_name": "Nomic Embed Text",
                "size": "274 MB",
                "category": "Embeddings",
                "description": "High-performing embedding model for RAG",
                "tags": ["embeddings", "rag", "fast"],
                "command": "ollama pull nomic-embed-text"
            },
        ]
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text (for RAG)
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        try:
            # Use nomic-embed-text for embeddings (lightweight)
            response = await self.client.embed(
                model="nomic-embed-text",
                input=text
            )
            return response.get('embeddings', [None])[0]
        except Exception as e:
            print(f"[Ollama] Embedding error: {e}")
            return None

