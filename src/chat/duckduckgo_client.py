"""
DuckDuckGo AI Chat Client
Free AI chat service with multiple models - no API key needed!
"""

import httpx
from typing import List, Dict, Optional
import json
import uuid


class DuckDuckGoClient:
    """Client for DuckDuckGo AI Chat (FREE, no API key!)"""
    
    # Available models
    MODELS = {
        "gpt-4o-mini": {
            "name": "GPT-4o mini",
            "description": "Fast - Quick, simple tasks",
            "performance": "⚡⚡⚡",
            "provider": "OpenAI"
        },
        "claude-3-haiku-20240307": {
            "name": "Claude 3 Haiku",
            "description": "Balanced - Technical discussions",
            "performance": "⚡⚡",
            "provider": "Anthropic"
        },
        "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo": {
            "name": "Llama 3.1 70B",
            "description": "Code optimized - Programming tasks",
            "performance": "⚡⚡",
            "provider": "Meta"
        },
        "mistralai/Mistral-Small-24B-Instruct-2501": {
            "name": "Mistral Small 3",
            "description": "Knowledge focused - Complex topics",
            "performance": "⚡⚡",
            "provider": "Mistral AI"
        },
        "o3-mini": {
            "name": "o3-mini",
            "description": "Very fast - Simple queries",
            "performance": "⚡⚡⚡⚡",
            "provider": "OpenAI"
        }
    }
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize DuckDuckGo AI client
        
        Args:
            model: Model to use (default: gpt-4o-mini)
        """
        self.model = model
        self.base_url = "https://duckduckgo.com/duckchat/v1/chat"
        self.status_url = "https://duckduckgo.com/duckchat/v1/status"
        
        # Session state
        self.vqd = None
        self.conversation_id = None
        
        print(f"[DuckDuckGo] Initialized with model: {model}")
    
    async def _get_vqd(self) -> Optional[str]:
        """Get VQD token for authentication"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.status_url,
                    headers={
                        "x-vqd-accept": "1",
                        "User-Agent": "Mozilla/5.0"
                    }
                )
                
                if response.status_code == 200:
                    vqd = response.headers.get("x-vqd-4")
                    print(f"[DuckDuckGo] Got VQD token")
                    return vqd
                else:
                    print(f"[DuckDuckGo] Failed to get VQD: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"[DuckDuckGo] Error getting VQD: {e}")
            return None
    
    async def test_connection(self) -> tuple[bool, str]:
        """
        Test DuckDuckGo AI connection
        
        Returns:
            Tuple of (success, message)
        """
        try:
            vqd = await self._get_vqd()
            if vqd:
                return True, f"Connected! Using {self.MODELS[self.model]['name']}"
            else:
                return False, "Failed to connect to DuckDuckGo AI"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    async def send_message(self, messages: List[Dict[str, str]], 
                          stream: bool = False) -> Optional[str]:
        """
        Send chat message to DuckDuckGo AI
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream response (not supported)
            
        Returns:
            Response text or None on error
        """
        try:
            # Get VQD token if we don't have one
            if not self.vqd:
                self.vqd = await self._get_vqd()
                if not self.vqd:
                    return "Error: Could not authenticate with DuckDuckGo AI"
            
            # Prepare request
            last_message = messages[-1]['content'] if messages else ""
            
            payload = {
                "model": self.model,
                "messages": messages
            }
            
            print(f"[DuckDuckGo] Sending request to {self.model}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "x-vqd-4": self.vqd,
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0"
                    },
                    json=payload
                )
                
                print(f"[DuckDuckGo] Response status: {response.status_code}")
                
                if response.status_code == 200:
                    # Update VQD for next request
                    new_vqd = response.headers.get("x-vqd-4")
                    if new_vqd:
                        self.vqd = new_vqd
                    
                    # Parse response
                    lines = response.text.strip().split('\n')
                    full_response = ""
                    
                    for line in lines:
                        if line.startswith('data: '):
                            data = line[6:]  # Remove 'data: ' prefix
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if 'message' in chunk:
                                    full_response += chunk['message']
                            except json.JSONDecodeError:
                                continue
                    
                    print(f"[DuckDuckGo] Success! Response length: {len(full_response)} chars")
                    return full_response if full_response else "No response from model"
                    
                else:
                    error_text = response.text[:200]
                    print(f"[DuckDuckGo] API error: {response.status_code} - {error_text}")
                    
                    # Reset VQD on auth errors
                    if response.status_code in [401, 403]:
                        self.vqd = None
                    
                    return f"Error: DuckDuckGo AI returned status {response.status_code}"
                    
        except httpx.TimeoutException:
            print("[DuckDuckGo] Request timeout")
            return "Error: Request timeout"
        except Exception as e:
            print(f"[DuckDuckGo] Error: {e}")
            return f"Error: {str(e)}"
    
    @classmethod
    def get_available_models(cls) -> List[Dict[str, str]]:
        """Get list of available models"""
        return [
            {
                "id": model_id,
                "name": info["name"],
                "description": info["description"],
                "performance": info["performance"],
                "provider": info["provider"]
            }
            for model_id, info in cls.MODELS.items()
        ]
    
    def set_model(self, model: str):
        """Change the model"""
        if model in self.MODELS:
            self.model = model
            # Reset session for new model
            self.vqd = None
            self.conversation_id = None
            print(f"[DuckDuckGo] Switched to model: {model}")
        else:
            print(f"[DuckDuckGo] Unknown model: {model}")

