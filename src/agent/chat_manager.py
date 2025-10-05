"""
Chat Manager - Handles LLM interaction with agents, MCP servers, and apps in Chaquopy environment.

This module manages the proper environment setup and execution of:
- Agent personalities (from agent-store)
- MCP servers (from mcp-store) 
- Flet apps (from app-store)

All components run in their own virtual environments with proper Chaquopy integration.
"""

import json
import os
import subprocess
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import importlib.util


class ChatManager:
    """Manages chat interactions with agents, MCP servers, and apps in proper environments."""
    
    def __init__(self, page=None):
        self.page = page
        self.base_path = Path(__file__).resolve().parents[2]  # src/agent -> src/
        self.store_root = self.base_path / "store"
        
        # Ensure store directories exist
        (self.store_root / "agent").mkdir(parents=True, exist_ok=True)
        (self.store_root / "mcp").mkdir(parents=True, exist_ok=True)
        (self.store_root / "app").mkdir(parents=True, exist_ok=True)
        
        print(f"[ChatManager] Initialized with base_path: {self.base_path}")
        print(f"[ChatManager] Store root: {self.store_root}")
    
    def get_enabled_agent(self) -> Optional[Dict[str, Any]]:
        """Get the currently enabled agent from cache."""
        try:
            cache_path = self.store_root / "agent" / "cache.json"
            if not cache_path.exists():
                print("[ChatManager] No agent cache found")
                return None
                
            cache_data = json.loads(cache_path.read_text(encoding="utf-8"))
            for agent_id, info in cache_data.items():
                if isinstance(info, dict) and info.get("installed") and info.get("enabled"):
                    print(f"[ChatManager] Found enabled agent: {agent_id}")
                    return {"id": agent_id, **info}
                    
            print("[ChatManager] No enabled agent found")
            return None
        except Exception as e:
            print(f"[ChatManager] Error reading agent cache: {e}")
            return None
    
    def get_agent_environment(self, agent_id: str) -> Dict[str, str]:
        """Get the proper environment setup for an agent."""
        agent_dir = self.store_root / "agent" / agent_id
        
        # Determine Python executable
        if os.name == "nt":  # Windows
            venv_python = agent_dir / ".venv" / "Scripts" / "python.exe"
        else:  # Linux/macOS
            venv_python = agent_dir / ".venv" / "bin" / "python"
        
        # Fallback to system Python if venv doesn't exist
        if not venv_python.exists():
            venv_python = Path(sys.executable)
            print(f"[ChatManager] Using system Python: {venv_python}")
        else:
            print(f"[ChatManager] Using venv Python: {venv_python}")
        
        return {
            "python_exec": str(venv_python),
            "agent_dir": str(agent_dir),
            "cwd": str(agent_dir),
            "PYTHONPATH": str(agent_dir),
            "PATH": str(venv_python.parent) + os.pathsep + os.environ.get("PATH", "")
        }
    
    def invoke_agent(self, agent_id: str, message: str, context: str = "", history: List[Dict] = None) -> str:
        """Invoke an agent personality in its proper environment."""
        try:
            agent_info = self.get_enabled_agent()
            if not agent_info or agent_info["id"] != agent_id:
                return f"Agent '{agent_id}' not found or not enabled"
            
            env = self.get_agent_environment(agent_id)
            agent_dir = Path(env["agent_dir"])
            
            # Look for the main agent script
            script_candidates = ["adminotaur.py", f"{agent_id}.py", "main.py", "agent.py"]
            script_path = None
            
            for candidate in script_candidates:
                candidate_path = agent_dir / candidate
                if candidate_path.exists():
                    script_path = candidate_path
                    break
            
            if not script_path:
                return f"Agent script not found in {agent_dir}. Tried: {script_candidates}"
            
            print(f"[ChatManager] Invoking agent script: {script_path}")
            
            # Prepare input payload
            payload = {
                "message": message,
                "context": context,
                "history": history or [],
                "env": {
                    "cwd": env["cwd"],
                    "pythonpath": env["PYTHONPATH"]
                }
            }
            
            # Set up environment variables
            env_vars = os.environ.copy()
            env_vars.update({
                "PYTHONPATH": env["PYTHONPATH"],
                "PATH": env["PATH"]
            })
            
            # Execute agent script
            process = subprocess.run(
                [env["python_exec"], str(script_path)],
                input=json.dumps(payload).encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=env["cwd"],
                env=env_vars,
                timeout=120  # 2 minute timeout
            )
            
            if process.returncode != 0:
                error_output = process.stderr.decode("utf-8", errors="ignore")
                print(f"[ChatManager] Agent execution failed (code {process.returncode}): {error_output}")
                return f"Agent execution failed: {error_output.strip() or f'Exit code {process.returncode}'}"
            
            # Parse response
            output = process.stdout.decode("utf-8", errors="ignore").strip()
            try:
                response_data = json.loads(output)
                if isinstance(response_data, dict):
                    return response_data.get("text", response_data.get("response", str(response_data)))
                else:
                    return str(response_data)
            except json.JSONDecodeError:
                # If not JSON, return raw output
                return output
                
        except subprocess.TimeoutExpired:
            return "Agent execution timed out (2 minutes)"
        except Exception as e:
            print(f"[ChatManager] Error invoking agent: {e}")
            return f"Agent invocation error: {e}"
    
    def get_enabled_mcp_servers(self) -> List[Dict[str, Any]]:
        """Get all enabled MCP servers from cache."""
        try:
            cache_path = self.store_root / "mcp" / "cache.json"
            if not cache_path.exists():
                return []
                
            cache_data = json.loads(cache_path.read_text(encoding="utf-8"))
            enabled_servers = []
            
            for server_id, info in cache_data.items():
                if isinstance(info, dict) and info.get("installed") and info.get("enabled"):
                    enabled_servers.append({"id": server_id, **info})
                    
            return enabled_servers
        except Exception as e:
            print(f"[ChatManager] Error reading MCP cache: {e}")
            return []
    
    def invoke_mcp_server(self, server_id: str, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Invoke an MCP server tool in its proper environment."""
        try:
            server_dir = self.store_root / "mcp" / server_id
            
            # Determine Python executable
            if os.name == "nt":  # Windows
                venv_python = server_dir / ".venv" / "Scripts" / "python.exe"
            else:  # Linux/macOS
                venv_python = server_dir / ".venv" / "bin" / "python"
            
            # Fallback to system Python if venv doesn't exist
            if not venv_python.exists():
                venv_python = Path(sys.executable)
            
            # Look for the main server script
            script_candidates = [f"{server_id}.py", "server.py", "main.py", "web.py", "rag.py"]
            script_path = None
            
            for candidate in script_candidates:
                candidate_path = server_dir / candidate
                if candidate_path.exists():
                    script_path = candidate_path
                    break
            
            if not script_path:
                return f"MCP server script not found in {server_dir}"
            
            print(f"[ChatManager] Invoking MCP server: {script_path}")
            
            # Prepare input payload
            payload = {
                "tool": tool_name,
                "parameters": parameters,
                "env": {
                    "cwd": str(server_dir),
                    "server_id": server_id
                }
            }
            
            # Set up environment variables
            env_vars = os.environ.copy()
            env_vars.update({
                "PYTHONPATH": str(server_dir),
                "PATH": str(venv_python.parent) + os.pathsep + os.environ.get("PATH", "")
            })
            
            # Execute MCP server script
            process = subprocess.run(
                [str(venv_python), str(script_path)],
                input=json.dumps(payload).encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(server_dir),
                env=env_vars,
                timeout=60  # 1 minute timeout
            )
            
            if process.returncode != 0:
                error_output = process.stderr.decode("utf-8", errors="ignore")
                return f"MCP server execution failed: {error_output.strip()}"
            
            # Parse response
            output = process.stdout.decode("utf-8", errors="ignore").strip()
            try:
                response_data = json.loads(output)
                if isinstance(response_data, dict):
                    return response_data.get("result", response_data.get("text", str(response_data)))
                else:
                    return str(response_data)
            except json.JSONDecodeError:
                return output
                
        except subprocess.TimeoutExpired:
            return "MCP server execution timed out"
        except Exception as e:
            return f"MCP server invocation error: {e}"
    
    def get_available_tools(self) -> Dict[str, List[str]]:
        """Get available tools from enabled MCP servers."""
        tools = {}
        enabled_servers = self.get_enabled_mcp_servers()
        
        for server in enabled_servers:
            server_id = server["id"]
            # Common tool names for known servers
            if server_id == "web-search":
                tools[server_id] = ["search", "search_videos", "search_images"]
            elif server_id == "rag":
                tools[server_id] = ["query_documents", "add_document", "list_documents"]
            elif server_id == "github":
                tools[server_id] = ["get_repo", "create_issue", "list_issues"]
            else:
                tools[server_id] = ["execute"]  # Generic tool
        
        return tools
    
    def process_agent_command(self, command: str, context: str = "", history: List[Dict] = None) -> str:
        """Process an agent command and return the response."""
        agent_info = self.get_enabled_agent()
        if not agent_info:
            return "No agent is currently enabled. Please install and enable an agent from the Agents tab."
        
        agent_id = agent_info["id"]
        print(f"[ChatManager] Processing agent command for {agent_id}: {command[:50]}...")
        
        return self.invoke_agent(agent_id, command, context, history)
    
    def process_tool_command(self, tool_spec: str, parameters: Dict[str, Any]) -> str:
        """Process a tool command and return the response."""
        # Parse tool specification (e.g., "web-search:search" or "rag:query_documents")
        if ":" not in tool_spec:
            return f"Invalid tool specification: {tool_spec}. Expected format: 'server:tool'"
        
        server_id, tool_name = tool_spec.split(":", 1)
        print(f"[ChatManager] Processing tool command: {server_id}:{tool_name}")
        
        return self.invoke_mcp_server(server_id, tool_name, parameters)
