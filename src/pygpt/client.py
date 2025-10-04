"""
PyGPT API client for mobile
"""

import httpx
from typing import Optional, AsyncIterator, Dict, List
import json

from .models import Message, Conversation
from utils.logger import setup_logger

logger = setup_logger()


class PyGPTClient:
    """
    PyGPT API client
    
    This client can connect to:
    1. A remote PyGPT API endpoint
    2. OpenAI API directly
    3. Other compatible LLM APIs
    """
    
    def __init__(
        self,
        api_endpoint: str,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        timeout: int = 60
    ):
        """
        Initialize PyGPT client
        
        Args:
            api_endpoint: API endpoint URL (e.g., "https://api.openai.com/v1" or your PyGPT server)
            api_key: API key for authentication
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.api_endpoint = api_endpoint.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        
        # Create httpx client
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.api_endpoint,
            headers=headers,
            timeout=timeout
        )
        
        logger.info(f"PyGPT client initialized with model: {model}")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        """
        Send chat request
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            
        Returns:
            Generated response text
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream
            }
            
            response = await self.client.post(
                "/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract response text
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise ValueError("Invalid response format from API")
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in chat request: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in chat request: {e}")
            raise
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        """
        Send chat request with streaming response
        
        Args:
            messages: List of message dicts
            temperature: Temperature for generation
            max_tokens: Maximum tokens
            
        Yields:
            Response chunks as they arrive
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True
            }
            
            async with self.client.stream(
                "POST",
                "/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    if line.startswith("data: "):
                        line = line[6:]  # Remove "data: " prefix
                    
                    if line == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(line)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
                        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in streaming chat: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            raise
    
    async def send_message(
        self,
        conversation: Conversation,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Message:
        """
        Send a message in a conversation
        
        Args:
            conversation: Conversation object
            user_message: User's message text
            temperature: Temperature for generation
            max_tokens: Maximum tokens
            
        Returns:
            Assistant's response message
        """
        # Add user message to conversation
        user_msg = Message(role="user", content=user_message)
        conversation.add_message(user_msg)
        
        # Prepare messages for API
        api_messages = conversation.get_messages_for_api()
        
        # Get response
        response_text = await self.chat(
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Create assistant message
        assistant_msg = Message(role="assistant", content=response_text)
        conversation.add_message(assistant_msg)
        
        return assistant_msg
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            import asyncio
            asyncio.create_task(self.close())
        except:
            pass

