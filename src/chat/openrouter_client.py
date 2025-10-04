"""
OpenRouter AI client for chat
"""

import httpx
from typing import List, Dict, Optional, AsyncIterator
import json


class OpenRouterClient:
    """Client for OpenRouter AI API"""
    
    def __init__(self, api_key: str, model: str = "qwen/qwen-2.5-coder-32b-instruct", 
                 base_url: str = "https://openrouter.ai/api/v1"):
        """
        Initialize OpenRouter client
        
        Args:
            api_key: OpenRouter API key
            model: Model to use
            base_url: API base URL
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://decyphertek.io",  # Optional, for rankings
            "X-Title": "DecypherTek AI",  # Optional, shows in rankings
        }
    
    async def test_connection(self) -> tuple[bool, str]:
        """
        Test API connection
        
        Returns:
            Tuple of (success, message)
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 5
                    }
                )
                
                if response.status_code == 200:
                    return True, "Connection successful!"
                elif response.status_code == 401:
                    return False, "Invalid API key"
                elif response.status_code == 402:
                    return False, "Insufficient credits"
                else:
                    return False, f"Error: {response.status_code} - {response.text}"
                    
        except httpx.TimeoutException:
            return False, "Connection timeout"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    async def send_message(self, messages: List[Dict[str, str]], 
                          stream: bool = False) -> Optional[str]:
        """
        Send chat message
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream response
            
        Returns:
            Response text or None on error
        """
        try:
            print(f"[OpenRouter] Sending request to {self.model} with {len(messages)} messages")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": stream
                    }
                )
                
                print(f"[OpenRouter] Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content']
                    print(f"[OpenRouter] Success! Response length: {len(content)} chars")
                    return content
                else:
                    error_text = response.text[:200]
                    print(f"[OpenRouter] API error: {response.status_code} - {error_text}")
                    return None
                    
        except httpx.TimeoutException:
            print(f"[OpenRouter] Request timeout (30s)")
            return None
        except Exception as e:
            print(f"[OpenRouter] Error: {type(e).__name__}: {e}")
            return None
    
    async def stream_message(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """
        Stream chat message response
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Yields:
            Response text chunks
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": True
                    }
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]
                                if data == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data)
                                    if 'choices' in chunk and len(chunk['choices']) > 0:
                                        delta = chunk['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            yield delta['content']
                                except json.JSONDecodeError:
                                    continue
                    else:
                        print(f"Stream error: {response.status_code}")
                        
        except Exception as e:
            print(f"Error streaming message: {e}")
    
    def get_available_models(self) -> List[str]:
        """Get list of popular OpenRouter models"""
        return [
            "qwen/qwen-2.5-coder-32b-instruct",
            "openai/gpt-4-turbo",
            "openai/gpt-4",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "google/gemini-pro",
            "meta-llama/llama-3-70b-instruct",
            "mistralai/mixtral-8x7b-instruct",
        ]

