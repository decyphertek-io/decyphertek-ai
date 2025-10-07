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
        Process a message - handle systemctl commands, route to agent if enabled, otherwise use API
        
        Args:
            user_message: The user's message
            message_history: Previous chat messages
            use_rag: Ignored (kept for compatibility)
        
        Returns:
            Response string
        """
        print(f"[ChatManager] Processing message: {user_message[:50]}...")
        
        # Check for systemctl commands first - these bypass agent/API routing
        if user_message.startswith("sudo systemctl"):
            response = self.handle_systemctl_command(user_message)
            if response:
                return response
            # If not a recognized systemctl command, fall through to normal processing
        
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
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get detailed status of all agents for troubleshooting"""
        status = {
            "enabled_agent": None,
            "available_agents": [],
            "agent_cache_exists": False,
            "store_root_exists": False,
            "errors": []
        }
        
        try:
            # Check store root
            status["store_root_exists"] = self.store_root.exists()
            if not status["store_root_exists"]:
                status["errors"].append(f"Store root not found: {self.store_root}")
                return status
            
            # Check agent cache
            status["agent_cache_exists"] = self.agent_cache_path.exists()
            if not status["agent_cache_exists"]:
                status["errors"].append(f"Agent cache not found: {self.agent_cache_path}")
                return status
            
            # Read agent cache
            try:
                cache_data = json.loads(self.agent_cache_path.read_text(encoding="utf-8"))
                
                for agent_id, info in cache_data.items():
                    if isinstance(info, dict):
                        agent_status = {
                            "id": agent_id,
                            "installed": info.get("installed", False),
                            "enabled": info.get("enabled", False),
                            "binary_exists": False,
                            "binary_executable": False
                        }
                        
                        # Check agent directory
                        agent_dir = self.store_root / "agent" / agent_id
                        if agent_dir.exists():
                            # Check for binary
                            agent_binary = agent_dir / f"{agent_id}.agent"
                            agent_status["binary_exists"] = agent_binary.exists()
                            if agent_status["binary_exists"]:
                                agent_status["binary_executable"] = agent_binary.stat().st_mode & 0o111 != 0
                        
                        status["available_agents"].append(agent_status)
                        
                        if agent_status["enabled"]:
                            status["enabled_agent"] = agent_status
                            
            except Exception as e:
                status["errors"].append(f"Error reading agent cache: {e}")
                
        except Exception as e:
            status["errors"].append(f"Error checking agent status: {e}")
        
        return status
    
    def test_agent_connection(self, agent_id: str = None) -> Dict[str, Any]:
        """Test connection to a specific agent or the enabled agent"""
        if not agent_id:
            enabled_agent = self.get_enabled_agent()
            if not enabled_agent:
                return {"success": False, "error": "No agent enabled"}
            agent_id = enabled_agent["id"]
        
        test_result = {
            "agent_id": agent_id,
            "success": False,
            "response": None,
            "error": None,
            "execution_time": 0
        }
        
        try:
            import time
            start_time = time.time()
            
            # Test payload
            test_payload = {
                "message": "Hello, this is a connection test.",
                "context": "",
                "history": []
            }
            
            agent_dir = self.store_root / "agent" / agent_id
            agent_binary = agent_dir / f"{agent_id}.agent"
            venv_python = agent_dir / ".venv" / "bin" / "python"
            agent_script = agent_dir / f"{agent_id}.py"
            
            # Determine execution method
            if agent_binary.exists():
                cmd = [str(agent_binary)]
                method = "binary"
            elif venv_python.exists() and agent_script.exists():
                cmd = [str(venv_python), str(agent_script)]
                method = "venv_script"
            else:
                test_result["error"] = f"Agent {agent_id} not properly installed (no binary or venv+script found)"
                return test_result
            
            # Execute test
            process = subprocess.run(
                cmd,
                input=json.dumps(test_payload).encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(agent_dir),
                timeout=30
            )
            
            test_result["execution_time"] = time.time() - start_time
            test_result["method"] = method
            test_result["return_code"] = process.returncode
            
            if process.returncode == 0:
                output = process.stdout.decode("utf-8", errors="ignore").strip()
                test_result["success"] = True
                test_result["response"] = output
            else:
                error = process.stderr.decode("utf-8", errors="ignore")
                test_result["error"] = f"Agent execution failed: {error}"
                
        except subprocess.TimeoutExpired:
            test_result["error"] = "Agent test timed out (30 seconds)"
        except Exception as e:
            test_result["error"] = f"Test error: {e}"
        
        return test_result


    def handle_systemctl_command(self, command: str) -> str:
        """Handle systemctl-like commands for troubleshooting"""
        if command == "sudo systemctl status agent":
            return self._get_agent_status_text()
            
        elif command == "sudo systemctl test agent":
            result = self.test_agent_connection()
            
            if result["success"]:
                return f"✅ Agent '{result['agent_id']}' connection successful\n   Method: {result['method']}\n   Execution time: {result['execution_time']:.2f}s\n   Response: {result['response'][:100]}..."
            else:
                return f"❌ Agent connection failed: {result['error']}"
                
        elif command == "sudo systemctl list agents":
            status = self.get_agent_status()
            result = "=== Available Agents ===\n"
            for agent in status["available_agents"]:
                result += f"  - {agent['id']} (enabled: {'✅' if agent['enabled'] else '❌'})\n"
            return result
            
        elif command == "sudo systemctl status mcp":
            return self._get_mcp_status_text()
            
        elif command == "sudo systemctl list mcp":
            return self._get_mcp_list_text()
            
        elif command == "sudo systemctl status app":
            return self._get_app_status_text()
            
        elif command == "sudo systemctl list app":
            return self._get_app_list_text()
            
        return None  # Not a recognized systemctl command
    
    def _get_agent_status_text(self) -> str:
        """Get formatted agent status text"""
        status = self.get_agent_status()
        
        if status["errors"]:
            error_text = "❌ ERRORS:\n"
            for error in status["errors"]:
                error_text += f"  - {error}\n"
            error_text += "\n"
        else:
            error_text = ""
        
        result = f"=== Agent Status ===\n{error_text}"
        result += f"Store Root: {'✅' if status['store_root_exists'] else '❌'} {self.store_root}\n"
        result += f"Agent Cache: {'✅' if status['agent_cache_exists'] else '❌'} {self.agent_cache_path}\n\n"
        
        if status["enabled_agent"]:
            agent = status["enabled_agent"]
            result += f"Enabled Agent: {agent['id']}\n"
            result += f"  Installed: {'✅' if agent['installed'] else '❌'}\n"
            result += f"  Binary: {'✅' if agent['binary_exists'] else '❌'} (executable: {'✅' if agent['binary_executable'] else '❌'})\n"
        else:
            result += "No agent enabled\n"
        
        result += "\nAll Available Agents:\n"
        for agent in status["available_agents"]:
            status_icon = "🟢" if agent["enabled"] else "⚪"
            result += f"  {status_icon} {agent['id']} (installed: {'✅' if agent['installed'] else '❌'})\n"
        
        return result
    
    def _get_mcp_status_text(self) -> str:
        """Get formatted MCP server status text"""
        mcp_dir = self.store_root / "mcp"
        
        if not mcp_dir.exists():
            return "=== MCP Status ===\n❌ MCP directory not found"
        
        result = "=== MCP Status ===\n"
        result += f"MCP Directory: {'✅' if mcp_dir.exists() else '❌'} {mcp_dir}\n\n"
        
        mcp_servers = []
        for server_dir in mcp_dir.iterdir():
            if server_dir.is_dir():
                server_name = server_dir.name
                binary_name = f"{server_name}.mcp" if server_name != "web-search" else "web.mcp"
                binary_path = server_dir / binary_name
                script_path = server_dir / f"{server_name}.py"
                
                mcp_servers.append({
                    "name": server_name,
                    "binary_exists": binary_path.exists(),
                    "script_exists": script_path.exists(),
                    "binary_executable": binary_path.exists() and binary_path.stat().st_mode & 0o111 != 0
                })
        
        if mcp_servers:
            result += "Available MCP Servers:\n"
            for server in mcp_servers:
                result += f"  - {server['name']}\n"
                result += f"    Binary: {'✅' if server['binary_exists'] else '❌'} (executable: {'✅' if server['binary_executable'] else '❌'})\n"
                result += f"    Script: {'✅' if server['script_exists'] else '❌'}\n"
        else:
            result += "No MCP servers found\n"
        
        return result
    
    def _get_mcp_list_text(self) -> str:
        """Get formatted MCP server list text"""
        mcp_dir = self.store_root / "mcp"
        
        if not mcp_dir.exists():
            return "=== Available MCP Servers ===\n❌ MCP directory not found"
        
        result = "=== Available MCP Servers ===\n"
        for server_dir in mcp_dir.iterdir():
            if server_dir.is_dir():
                result += f"  - {server_dir.name}\n"
        
        return result
    
    def _get_app_status_text(self) -> str:
        """Get formatted app status text"""
        app_dir = self.store_root / "app"
        
        if not app_dir.exists():
            return "=== App Status ===\n❌ App directory not found"
        
        result = "=== App Status ===\n"
        result += f"App Directory: {'✅' if app_dir.exists() else '❌'} {app_dir}\n\n"
        
        apps = []
        for app_subdir in app_dir.iterdir():
            if app_subdir.is_dir():
                main_py = app_subdir / "main.py"
                apps.append({
                    "name": app_subdir.name,
                    "main_exists": main_py.exists()
                })
        
        if apps:
            result += "Available Apps:\n"
            for app in apps:
                result += f"  - {app['name']} (main.py: {'✅' if app['main_exists'] else '❌'})\n"
        else:
            result += "No apps found\n"
        
        return result
    
    def _get_app_list_text(self) -> str:
        """Get formatted app list text"""
        app_dir = self.store_root / "app"
        
        if not app_dir.exists():
            return "=== Available Apps ===\n❌ App directory not found"
        
        result = "=== Available Apps ===\n"
        for app_subdir in app_dir.iterdir():
            if app_subdir.is_dir():
                result += f"  - {app_subdir.name}\n"
        
        return result


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

