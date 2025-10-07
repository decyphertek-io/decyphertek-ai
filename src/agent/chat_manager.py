"""
Simplified Chat Manager - Routes messages to agent or API

This module does ONLY two things:
1. If agent is enabled: Route ALL messages to the agent
2. If no agent: Use direct OpenRouter API calls
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List


class ChatManager:
    """Simplified chat manager that routes to agent or API"""
    
    def __init__(self, page=None, ai_client=None):
        self.page = page
        self.ai_client = ai_client
        
        # Store paths
        self.user_home = Path.home() / ".decyphertek-ai"
        self.store_root = self.user_home / "store"
        
        # Agent cache path
        self.agent_cache_path = self.store_root / "agent" / "cache.json"
        
        # Ensure directories exist
        (self.store_root / "agent").mkdir(parents=True, exist_ok=True)
        
    def get_enabled_agent(self) -> Optional[Dict[str, Any]]:
        """Get the currently enabled agent from cache."""
        try:
            if not self.agent_cache_path.exists():
                return None
                
            cache_data = json.loads(self.agent_cache_path.read_text(encoding="utf-8"))
            
            for agent_id, info in cache_data.items():
                if isinstance(info, dict) and info.get("installed") and info.get("enabled"):
                    return {"id": agent_id, **info}
                    
            return None
        except Exception as e:
            print(f"[ChatManager] Error reading agent cache: {e}")
            return None
    
    async def process_message(self, user_message: str, message_history: List[Dict], use_rag: bool = True) -> str:
        """
        Process a message - route to agent if enabled, otherwise use API
        
        Args:
            user_message: The user's message
            message_history: Previous chat messages
            use_rag: Ignored (kept for compatibility)
        
        Returns:
            Response string
        """
        print(f"[ChatManager] Processing message: {user_message[:50]}...")
        
        # Check if an agent is enabled
        enabled_agent = self.get_enabled_agent()
        
        if enabled_agent:
            # ROUTE TO AGENT
            print(f"[ChatManager] Agent '{enabled_agent.get('id')}' is enabled, routing to agent")
            return self._call_agent(enabled_agent, user_message, message_history)
        else:
            # NO AGENT - USE DIRECT API
            print(f"[ChatManager] No agent enabled, using direct API")
            return await self._call_api(user_message, message_history)
    
    def _call_agent(self, agent_info: Dict[str, Any], user_message: str, message_history: List[Dict]) -> str:
        """Call the agent via subprocess"""
        try:
            agent_id = agent_info["id"]
            agent_dir = self.store_root / "agent" / agent_id
            agent_binary = agent_dir / f"{agent_id}.agent"
            venv_python = agent_dir / ".venv" / "bin" / "python"
            agent_script = agent_dir / f"{agent_id}.py"
            
            # Prefer compiled binary if present; fallback to venv + script
            use_binary = agent_binary.exists()
            if not use_binary and (not venv_python.exists() or not agent_script.exists()):
                return f"⚠️ Agent not ready. Please reinstall {agent_id} from the Agents tab."
            
            # Prepare input
            payload = {
                "message": user_message,
                "context": "",
                "history": message_history
            }
            
            # Execute agent
            if use_binary:
                print(f"[ChatManager] Calling {agent_id} binary at {agent_binary}")
                cmd = [str(agent_binary)]
            else:
                print(f"[ChatManager] Calling {agent_id} script via venv at {agent_script}")
                cmd = [str(venv_python), str(agent_script)]

            process = subprocess.run(
                cmd,
                input=json.dumps(payload).encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(agent_dir),
                timeout=120
            )
            
            if process.returncode != 0:
                error = process.stderr.decode("utf-8", errors="ignore")
                print(f"[ChatManager] Agent error: {error}")
                return f"⚠️ Agent error: {error[:200]}"
            
            # Parse response
            output = process.stdout.decode("utf-8", errors="ignore").strip()
            try:
                response_data = json.loads(output)
                if isinstance(response_data, dict):
                    return response_data.get("text", response_data.get("response", str(response_data)))
                return str(response_data)
            except json.JSONDecodeError:
                return output
                
        except subprocess.TimeoutExpired:
            return "⚠️ Agent timed out (2 minutes)"
        except Exception as e:
            print(f"[ChatManager] Agent error: {e}")
            return f"⚠️ Agent error: {e}"
    
    async def _call_api(self, user_message: str, message_history: List[Dict]) -> str:
        """Call OpenRouter API directly (no RAG - agents handle that)"""
        try:
            # Check if API client is available
            if not self.ai_client:
                return "⚠️ No AI client configured and no agent enabled. Please configure an API key in Settings or enable an agent."
            
            # Call API
            print(f"[ChatManager] Calling OpenRouter API")
            response = await self.ai_client.send_message(message_history)
            return response or "⚠️ No response from API"
            
        except Exception as e:
            print(f"[ChatManager] API error: {e}")
            return f"⚠️ API error: {e}"


if __name__ == "__main__":
    # Simple test mode
    import asyncio
    
    async def test():
        cm = ChatManager()
        agent = cm.get_enabled_agent()
        if agent:
            print(f"Agent enabled: {agent['id']}")
        else:
            print("No agent enabled")
    
    asyncio.run(test())

