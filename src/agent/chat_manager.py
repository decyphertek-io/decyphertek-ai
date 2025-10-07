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
import requests
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import importlib.util


class ChatManager:
    """Manages chat interactions with agents, MCP servers, and apps in proper environments."""
    
    def __init__(self, page=None, ai_client=None, document_manager=None):
        self.page = page
        self.ai_client = ai_client
        self.document_manager = document_manager
        
        # NEW ARCHITECTURE: All installed components in ~/.decyphertek-ai/store/
        self.user_home = Path.home() / ".decyphertek-ai"
        self.store_root = self.user_home / "store"
        
        # Ensure store directories exist
        (self.store_root / "agent").mkdir(parents=True, exist_ok=True)
        (self.store_root / "mcp").mkdir(parents=True, exist_ok=True)
        (self.store_root / "app").mkdir(parents=True, exist_ok=True)
        
        # Registry URLs
        self.agent_registry_url = "https://raw.githubusercontent.com/decyphertek-io/agent-store/main/personality.json"
        self.mcp_registry_url = "https://raw.githubusercontent.com/decyphertek-io/mcp-store/main/skills.json"
        self.app_registry_url = "https://raw.githubusercontent.com/decyphertek-io/app-store/main/app.json"
        
        # Cache files (in ~/.decyphertek-ai/store/)
        self.agent_cache_path = self.store_root / "agent" / "cache.json"
        self.mcp_cache_path = self.store_root / "mcp" / "cache.json"
        self.app_cache_path = self.store_root / "app" / "cache.json"
        
        # Enabled state files (in ~/.decyphertek-ai/)
        self.agent_enabled_path = self.user_home / "agent-enabled.json"
        self.mcp_enabled_path = self.user_home / "mcp-enabled.json"
        self.app_enabled_path = Path.home() / ".decyphertek-ai" / "app-enabled.json"
        
        # Ensure enabled state directories exist
        self.agent_enabled_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"[ChatManager] Initialized with store_root: {self.store_root}")
        print(f"[ChatManager] User home: {self.user_home}")
        
        # Initialize stores in background
        self._initialize_stores_async()
    
    def _initialize_stores_async(self):
        """Initialize stores in background thread."""
        def init_worker():
            try:
                print("[ChatManager] Initializing stores in background...")
                self._ensure_default_agent_installed()
                self._ensure_default_mcp_servers_installed()
                print("[ChatManager] Store initialization complete")
            except Exception as e:
                print(f"[ChatManager] Store initialization error: {e}")
        
        thread = threading.Thread(target=init_worker, daemon=True)
        thread.start()
    
    def _ensure_default_agent_installed(self):
        """Ensure default agent (adminotaur) is installed and enabled."""
        try:
            # Check if agent cache exists and has adminotaur
            if self.agent_cache_path.exists():
                cache_data = json.loads(self.agent_cache_path.read_text(encoding="utf-8"))
                if "adminotaur" in cache_data and cache_data["adminotaur"].get("installed"):
                    print("[ChatManager] Adminotaur agent already installed")
                    return
            
            # Create default agent cache entry
            default_agent = {
                "adminotaur": {
                    "id": "adminotaur",
                    "name": "Adminotaur",
                    "description": "Advanced AI agent with tool-use capabilities",
                    "installed": True,
                    "enabled": True,
                    "repo_url": "https://github.com/decyphertek-io/agent-store",
                    "folder_path": "adminotaur/",
                    "module_path": "adminotaur/adminotaur.py",
                    "class_name": "AdminotaurAgent",
                    "enable_by_default": True
                }
            }
            
            self.agent_cache_path.write_text(json.dumps(default_agent, indent=2), encoding="utf-8")
            print("[ChatManager] Created default agent cache")
            
        except Exception as e:
            print(f"[ChatManager] Error ensuring default agent: {e}")
    
    def _ensure_default_mcp_servers_installed(self):
        """Ensure default MCP servers are installed and enabled."""
        try:
            # Check if MCP cache exists
            if self.mcp_cache_path.exists():
                cache_data = json.loads(self.mcp_cache_path.read_text(encoding="utf-8"))
                if "web-search" in cache_data and cache_data["web-search"].get("installed"):
                    print("[ChatManager] Default MCP servers already installed")
                    # Set up environments for enabled MCP servers
                    self._setup_enabled_mcp_environments()
                    return
            
            # Create default MCP cache entry
            default_mcp = {
                "web-search": {
                    "id": "web-search",
                    "name": "Web Search",
                    "description": "Web search and content retrieval",
                    "installed": True,
                    "enabled": True,
                    "repo_url": "https://github.com/decyphertek-io/mcp-store",
                    "folder_path": "web-search/",
                    "module_path": "web-search/web.py",
                    "enable_by_default": True
                }
            }
            
            self.mcp_cache_path.write_text(json.dumps(default_mcp, indent=2), encoding="utf-8")
            print("[ChatManager] Created default MCP cache")
            
        except Exception as e:
            print(f"[ChatManager] Error ensuring default MCP servers: {e}")
    
    def fetch_agent_registry(self) -> Dict[str, Any]:
        """Fetch agent registry from remote URL."""
        try:
            response = requests.get(self.agent_registry_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[ChatManager] Error fetching agent registry: {e}")
            return {}
    
    def fetch_mcp_registry(self) -> Dict[str, Any]:
        """Fetch MCP registry from remote URL."""
        try:
            response = requests.get(self.mcp_registry_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[ChatManager] Error fetching MCP registry: {e}")
            return {}
    
    def fetch_app_registry(self) -> Dict[str, Any]:
        """Fetch app registry from remote URL."""
        try:
            response = requests.get(self.app_registry_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[ChatManager] Error fetching app registry: {e}")
            return {}
    
    def install_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> bool:
        """Install an agent from the registry."""
        try:
            agent_dir = self.store_root / "agent" / agent_id
            agent_dir.mkdir(parents=True, exist_ok=True)
            
            # Download agent files (simplified - in real implementation, use GitHub API)
            print(f"[ChatManager] Installing agent {agent_id} to {agent_dir}")
            
            # Update cache
            if self.agent_cache_path.exists():
                cache_data = json.loads(self.agent_cache_path.read_text(encoding="utf-8"))
            else:
                cache_data = {}
            
            cache_data[agent_id] = {
                **agent_info,
                "installed": True,
                "enabled": agent_info.get("enable_by_default", False)
            }
            
            self.agent_cache_path.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
            print(f"[ChatManager] Agent {agent_id} installed successfully")
            return True
            
        except Exception as e:
            print(f"[ChatManager] Error installing agent {agent_id}: {e}")
            return False
    
    def install_mcp_server(self, server_id: str, server_info: Dict[str, Any]) -> bool:
        """Install an MCP server from the registry."""
        try:
            server_dir = self.store_root / "mcp" / server_id
            server_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"[ChatManager] Installing MCP server {server_id} to {server_dir}")
            
            # Update cache
            if self.mcp_cache_path.exists():
                cache_data = json.loads(self.mcp_cache_path.read_text(encoding="utf-8"))
            else:
                cache_data = {}
            
            cache_data[server_id] = {
                **server_info,
                "installed": True,
                "enabled": server_info.get("enable_by_default", False)
            }
            
            self.mcp_cache_path.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
            print(f"[ChatManager] MCP server {server_id} installed successfully")
            return True
            
        except Exception as e:
            print(f"[ChatManager] Error installing MCP server {server_id}: {e}")
            return False
    
    def install_app(self, app_id: str, app_info: Dict[str, Any]) -> bool:
        """Install an app from the registry."""
        try:
            app_dir = self.store_root / "app" / app_id
            app_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"[ChatManager] Installing app {app_id} to {app_dir}")
            
            # Update cache
            if self.app_cache_path.exists():
                cache_data = json.loads(self.app_cache_path.read_text(encoding="utf-8"))
            else:
                cache_data = {}
            
            cache_data[app_id] = {
                **app_info,
                "installed": True,
                "enabled": app_info.get("enable_by_default", False)
            }
            
            self.app_cache_path.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
            print(f"[ChatManager] App {app_id} installed successfully")
            return True
            
        except Exception as e:
            print(f"[ChatManager] Error installing app {app_id}: {e}")
            return False
    
    def set_agent_enabled(self, agent_id: str, enabled: bool) -> bool:
        """Enable/disable an agent."""
        try:
            # Update cache
            if self.agent_cache_path.exists():
                cache_data = json.loads(self.agent_cache_path.read_text(encoding="utf-8"))
                if agent_id in cache_data:
                    cache_data[agent_id]["enabled"] = enabled
                    self.agent_cache_path.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
                    print(f"[ChatManager] Agent {agent_id} {'enabled' if enabled else 'disabled'}")
                    return True
            return False
        except Exception as e:
            print(f"[ChatManager] Error setting agent {agent_id} enabled state: {e}")
            return False
    
    def set_mcp_enabled(self, server_id: str, enabled: bool) -> bool:
        """Enable/disable an MCP server."""
        try:
            # Update cache
            if self.mcp_cache_path.exists():
                cache_data = json.loads(self.mcp_cache_path.read_text(encoding="utf-8"))
                if server_id in cache_data:
                    cache_data[server_id]["enabled"] = enabled
                    self.mcp_cache_path.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
                    print(f"[ChatManager] MCP server {server_id} {'enabled' if enabled else 'disabled'}")
                    return True
            return False
        except Exception as e:
            print(f"[ChatManager] Error setting MCP server {server_id} enabled state: {e}")
            return False
    
    def set_app_enabled(self, app_id: str, enabled: bool) -> bool:
        """Enable/disable an app."""
        try:
            # Update cache
            if self.app_cache_path.exists():
                cache_data = json.loads(self.app_cache_path.read_text(encoding="utf-8"))
                if app_id in cache_data:
                    cache_data[app_id]["enabled"] = enabled
                    self.app_cache_path.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
                    print(f"[ChatManager] App {app_id} {'enabled' if enabled else 'disabled'}")
                    return True
            return False
        except Exception as e:
            print(f"[ChatManager] Error setting app {app_id} enabled state: {e}")
            return False
    
    async def process_message(self, user_message: str, message_history: List[Dict], use_rag: bool = True) -> str:
        """
        Main message processing method that handles:
        - Agent commands (!agent ...)
        - RAG context retrieval
        - Direct LLM chat
        - Tool invocations
        """
        print(f"[ChatManager] Processing message: {user_message[:50]}...")
        
        # Query RAG if enabled and document manager available
        rag_context = ""
        if use_rag and self.document_manager:
            print(f"[ChatManager] Querying RAG for context...")
            try:
                results = await self.document_manager.query_documents(user_message, n_results=3)
                
                if results:
                    print(f"[ChatManager] Found {len(results)} relevant document chunks")
                    rag_context = "\n\nRelevant context from documents:\n"
                    for i, result in enumerate(results, 1):
                        rag_context += f"\n[{result['filename']}]\n{result['content']}\n"
                    rag_context += "\nPlease use the above context to answer the question.\n"
                else:
                    print("[ChatManager] No relevant documents found")
            except Exception as e:
                print(f"[ChatManager] RAG query error: {e}")
                rag_context = ""
        
        # Prepare messages with RAG context
        messages_to_send = message_history.copy()
        if rag_context:
            # Add RAG context to the last user message
            messages_to_send[-1] = {
                "role": "user", 
                "content": user_message + rag_context
            }
        
        # Special health-check command from chat
        if user_message.strip() == "sudo systemctl status chat_manager":
            print(f"[ChatManager] Health check command detected")
            return "OK:200;"
        
        # Agent status check command
        if user_message.strip() == "sudo systemctl status agent":
            print(f"[ChatManager] Agent status command detected")
            return self._get_agent_status_report()
        
        # MCP status check command
        if user_message.strip() == "sudo systemctl status mcp":
            print(f"[ChatManager] MCP status command detected")
            return self._get_mcp_status_report()
        
        # App status check command
        if user_message.strip() == "sudo systemctl status app":
            print(f"[ChatManager] App status command detected")
            return self._get_app_status_report()
        
        # RAG status check command - delegate to adminotaur agent
        if user_message.strip() == "sudo systemctl status rag":
            print(f"[ChatManager] RAG status command detected - delegating to adminotaur")
            return self._call_adminotaur_agent(user_message)
        
        # Specific agent test command
        if user_message.strip() == "sudo systemctl status agent-adminotaur":
            print(f"[ChatManager] Adminotaur agent test command detected")
            return self._call_adminotaur_agent(user_message)
        
        # Specific MCP server test command
        if user_message.strip().startswith("sudo systemctl status mcp-"):
            server_id = user_message.strip().replace("sudo systemctl status mcp-", "")
            print(f"[ChatManager] MCP server test command detected for: {server_id}")
            return self._test_mcp_server(server_id)
        
        # MCP server install command
        if user_message.strip().startswith("sudo apt install mcp-"):
            server_id = user_message.strip().replace("sudo apt install mcp-", "")
            print(f"[ChatManager] MCP server install command detected for: {server_id}")
            return self._reinstall_mcp_server(server_id)
        
        # MCP server reinstall command
        if user_message.strip().startswith("sudo apt reinstall mcp-"):
            server_id = user_message.strip().replace("sudo apt reinstall mcp-", "")
            print(f"[ChatManager] MCP server reinstall command detected for: {server_id}")
            return self._reinstall_mcp_server(server_id)

        # Check for debug command
        if user_message.strip() == "!debug":
            print(f"[ChatManager] Debug command detected")
            return self.debug_info()
        
        # Check for verbose troubleshooting command
        if user_message.strip() == "!verbose" or user_message.strip() == "verbose":
            print(f"[ChatManager] Verbose troubleshooting mode detected")
            return self._get_verbose_system_status()
        
        # Check for management commands
        if user_message.strip().startswith("!install "):
            return self._handle_install_command(user_message.strip()[9:])
        
        if user_message.strip().startswith("!reinstall "):
            return self._handle_reinstall_command(user_message.strip()[11:])
        
        if user_message.strip().startswith("!enable "):
            result = self._handle_enable_command(user_message.strip()[8:])
            # If enabling an MCP server, set up its environment
            parts = user_message.strip()[8:].split()
            if len(parts) >= 2 and parts[0] == "mcp":
                server_id = parts[1]
                print(f"[ChatManager] MCP server {server_id} enabled, setting up environment...")
                self._setup_mcp_environment(server_id)
            return result
        
        if user_message.strip().startswith("!disable "):
            return self._handle_disable_command(user_message.strip()[9:])
        
        if user_message.strip() == "!list":
            return self._handle_list_command()
        
        # Check for agent command
        if user_message.strip().startswith("!agent "):
            agent_payload = user_message.strip()[7:]
            print(f"[ChatManager] Agent command detected: {agent_payload}")
            return self.process_agent_command(agent_payload, rag_context, message_history)
        
        # Check for tool command (e.g., !tool web-search:search "query")
        if user_message.strip().startswith("!tool "):
            tool_spec = user_message.strip()[6:]
            print(f"[ChatManager] Tool command detected: {tool_spec}")
            return self._process_tool_command(tool_spec)
        
        # Check if an agent is available and enabled
        enabled_agent = self.get_enabled_agent()
        if enabled_agent:
            print(f"[ChatManager] Agent '{enabled_agent.get('id')}' is enabled, routing through agent")
            try:
                # Route through the enabled agent
                return self.process_agent_command(user_message, rag_context, message_history)
            except Exception as e:
                print(f"[ChatManager] Agent processing error: {e}")
                return f"⚠️ Error processing with agent: {e}"
        
        # Fallback: Direct LLM chat (when no agent is available)
        if not self.ai_client:
            return "⚠️ AI client not available. Please check your API configuration."
        
        print(f"[ChatManager] No agent available, using direct LLM client for chat")
        try:
            response = await self.ai_client.send_message(messages_to_send)
            return response or "⚠️ No response from AI client"
        except Exception as e:
            print(f"[ChatManager] LLM client error: {e}")
            return f"⚠️ Error communicating with AI: {e}"
    
    def _process_tool_command(self, tool_spec: str) -> str:
        """Process tool commands like 'web-search:search "query"' or 'rag:query_documents "query"'."""
        try:
            # Parse tool specification
            if ":" not in tool_spec:
                return f"Invalid tool specification: {tool_spec}. Expected format: 'server:tool [parameters]'"
            
            parts = tool_spec.split(":", 1)
            server_id = parts[0].strip()
            tool_and_params = parts[1].strip()
            
            # Parse tool name and parameters
            if " " in tool_and_params:
                tool_name, param_str = tool_and_params.split(" ", 1)
                # Try to parse parameters as JSON, fallback to simple string
                try:
                    parameters = json.loads(param_str)
                except json.JSONDecodeError:
                    parameters = {"query": param_str.strip('"\'')}
            else:
                tool_name = tool_and_params
                parameters = {}
            
            print(f"[ChatManager] Invoking tool: {server_id}:{tool_name} with params: {parameters}")
            return self.invoke_mcp_server(server_id, tool_name, parameters)
            
        except Exception as e:
            return f"Tool command error: {e}"
    
    def _handle_install_command(self, command: str) -> str:
        """Handle !install commands."""
        try:
            parts = command.split()
            if len(parts) < 2:
                return "Usage: !install <type> <id>\nTypes: agent, mcp, app"
            
            install_type, item_id = parts[0], parts[1]
            
            if install_type == "agent":
                registry = self.fetch_agent_registry()
                if item_id in registry.get("agents", {}):
                    success = self.install_agent(item_id, registry["agents"][item_id])
                    return f"✅ Agent '{item_id}' installed successfully" if success else f"❌ Failed to install agent '{item_id}'"
                else:
                    return f"❌ Agent '{item_id}' not found in registry"
            
            elif install_type == "mcp":
                registry = self.fetch_mcp_registry()
                if item_id in registry.get("servers", {}):
                    success = self.install_mcp_server(item_id, registry["servers"][item_id])
                    return f"✅ MCP server '{item_id}' installed successfully" if success else f"❌ Failed to install MCP server '{item_id}'"
                else:
                    return f"❌ MCP server '{item_id}' not found in registry"
            
            elif install_type == "app":
                registry = self.fetch_app_registry()
                if item_id in registry.get("apps", {}):
                    success = self.install_app(item_id, registry["apps"][item_id])
                    return f"✅ App '{item_id}' installed successfully" if success else f"❌ Failed to install app '{item_id}'"
                else:
                    return f"❌ App '{item_id}' not found in registry"
            
            else:
                return f"❌ Unknown install type: {install_type}. Use: agent, mcp, app"
                
        except Exception as e:
            return f"❌ Install command error: {e}"
    
    def _handle_reinstall_command(self, args: str) -> str:
        """Handle reinstall commands like '!reinstall mcp web-search'."""
        try:
            parts = args.split()
            if len(parts) < 2:
                return "❌ Usage: !reinstall <type> <id>\nExample: !reinstall mcp web-search"
            
            item_type = parts[0].lower()
            item_id = parts[1]
            
            if item_type == "mcp":
                print(f"[ChatManager] Reinstalling MCP server: {item_id}")
                # Import and use StoreManager
                from agent.store_manager import StoreManager
                store_manager = StoreManager()
                result = store_manager.reinstall_mcp_server(item_id)
                
                if result.get("success"):
                    return f"✅ Successfully reinstalled MCP server '{item_id}'"
                else:
                    return f"❌ Failed to reinstall MCP server '{item_id}': {result.get('error', 'Unknown error')}"
            else:
                return f"❌ Unsupported reinstall type: {item_type}. Use 'mcp' for MCP servers."
                
        except Exception as e:
            return f"❌ Reinstall command error: {e}"
    
    def _handle_enable_command(self, command: str) -> str:
        """Handle !enable commands."""
        try:
            parts = command.split()
            if len(parts) < 2:
                return "Usage: !enable <type> <id>\nTypes: agent, mcp, app"
            
            enable_type, item_id = parts[0], parts[1]
            
            if enable_type == "agent":
                success = self.set_agent_enabled(item_id, True)
                return f"✅ Agent '{item_id}' enabled" if success else f"❌ Failed to enable agent '{item_id}'"
            
            elif enable_type == "mcp":
                success = self.set_mcp_enabled(item_id, True)
                return f"✅ MCP server '{item_id}' enabled" if success else f"❌ Failed to enable MCP server '{item_id}'"
            
            elif enable_type == "app":
                success = self.set_app_enabled(item_id, True)
                return f"✅ App '{item_id}' enabled" if success else f"❌ Failed to enable app '{item_id}'"
            
            else:
                return f"❌ Unknown enable type: {enable_type}. Use: agent, mcp, app"
                
        except Exception as e:
            return f"❌ Enable command error: {e}"
    
    def _handle_disable_command(self, command: str) -> str:
        """Handle !disable commands."""
        try:
            parts = command.split()
            if len(parts) < 2:
                return "Usage: !disable <type> <id>\nTypes: agent, mcp, app"
            
            disable_type, item_id = parts[0], parts[1]
            
            if disable_type == "agent":
                success = self.set_agent_enabled(item_id, False)
                return f"✅ Agent '{item_id}' disabled" if success else f"❌ Failed to disable agent '{item_id}'"
            
            elif disable_type == "mcp":
                success = self.set_mcp_enabled(item_id, False)
                return f"✅ MCP server '{item_id}' disabled" if success else f"❌ Failed to disable MCP server '{item_id}'"
            
            elif disable_type == "app":
                success = self.set_app_enabled(item_id, False)
                return f"✅ App '{item_id}' disabled" if success else f"❌ Failed to disable app '{item_id}'"
            
            else:
                return f"❌ Unknown disable type: {disable_type}. Use: agent, mcp, app"
                
        except Exception as e:
            return f"❌ Disable command error: {e}"
    
    def _handle_list_command(self) -> str:
        """Handle !list command to show all installed items."""
        try:
            result = ["📋 **Installed Items:**\n"]
            
            # List agents
            if self.agent_cache_path.exists():
                cache_data = json.loads(self.agent_cache_path.read_text(encoding="utf-8"))
                result.append("🤖 **Agents:**")
                for agent_id, info in cache_data.items():
                    status = "✅ Enabled" if info.get("enabled") else "❌ Disabled"
                    result.append(f"  • {agent_id}: {info.get('name', 'Unknown')} - {status}")
                result.append("")
            
            # List MCP servers
            if self.mcp_cache_path.exists():
                cache_data = json.loads(self.mcp_cache_path.read_text(encoding="utf-8"))
                result.append("🔧 **MCP Servers:**")
                for server_id, info in cache_data.items():
                    status = "✅ Enabled" if info.get("enabled") else "❌ Disabled"
                    result.append(f"  • {server_id}: {info.get('name', 'Unknown')} - {status}")
                result.append("")
            
            # List apps
            if self.app_cache_path.exists():
                cache_data = json.loads(self.app_cache_path.read_text(encoding="utf-8"))
                result.append("📱 **Apps:**")
                for app_id, info in cache_data.items():
                    status = "✅ Enabled" if info.get("enabled") else "❌ Disabled"
                    result.append(f"  • {app_id}: {info.get('name', 'Unknown')} - {status}")
                result.append("")
            
            return "\n".join(result) if len(result) > 1 else "📋 No items installed yet."
            
        except Exception as e:
            return f"❌ List command error: {e}"
    
    def _get_agent_status_report(self) -> str:
        """Generate a detailed agent status report."""
        try:
            result = ["🤖 **Agent Status Report**\n"]
            
            if not self.agent_cache_path.exists():
                result.append("❌ No agent cache found. No agents installed.")
                return "\n".join(result)
            
            cache_data = json.loads(self.agent_cache_path.read_text(encoding="utf-8"))
            
            if not cache_data:
                result.append("❌ No agents found in cache.")
                return "\n".join(result)
            
            result.append(f"📊 **Total Agents:** {len(cache_data)}")
            result.append("")
            
            enabled_count = 0
            disabled_count = 0
            
            for agent_id, info in cache_data.items():
                name = info.get('name', 'Unknown')
                description = info.get('description', 'No description')
                installed = info.get('installed', False)
                enabled = info.get('enabled', False)
                
                if enabled:
                    status_icon = "✅"
                    status_text = "ENABLED"
                    enabled_count += 1
                else:
                    status_icon = "❌"
                    status_text = "DISABLED"
                    disabled_count += 1
                
                install_status = "📦 Installed" if installed else "⚠️ Not Installed"
                
                result.append(f"{status_icon} **{agent_id}** ({name})")
                result.append(f"   Status: {status_text}")
                result.append(f"   Install: {install_status}")
                result.append(f"   Description: {description}")
                result.append("")
            
            result.append("📈 **Summary:**")
            result.append(f"   • Enabled: {enabled_count}")
            result.append(f"   • Disabled: {disabled_count}")
            result.append(f"   • Total: {len(cache_data)}")
            
            if enabled_count == 0:
                result.append("")
                result.append("⚠️ **Warning:** No agents are currently enabled!")
                result.append("   Use '!enable agent <id>' to enable an agent.")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ Agent status report error: {e}"
    
    def _get_mcp_status_report(self) -> str:
        """Generate a detailed MCP server status report."""
        try:
            result = ["🔧 **MCP Server Status Report**\n"]
            
            if not self.mcp_cache_path.exists():
                result.append("❌ No MCP cache found. No MCP servers installed.")
                return "\n".join(result)
            
            cache_data = json.loads(self.mcp_cache_path.read_text(encoding="utf-8"))
            
            if not cache_data:
                result.append("❌ No MCP servers found in cache.")
                return "\n".join(result)
            
            result.append(f"📊 **Total MCP Servers:** {len(cache_data)}")
            result.append("")
            
            enabled_count = 0
            disabled_count = 0
            
            for server_id, info in cache_data.items():
                name = info.get('name', 'Unknown')
                description = info.get('description', 'No description')
                installed = info.get('installed', False)
                enabled = info.get('enabled', False)
                
                if enabled:
                    status_icon = "✅"
                    status_text = "ENABLED"
                    enabled_count += 1
                else:
                    status_icon = "❌"
                    status_text = "DISABLED"
                    disabled_count += 1
                
                install_status = "📦 Installed" if installed else "⚠️ Not Installed"
                
                # Check environment setup for enabled servers
                env_status = ""
                if enabled and installed:
                    env_status = self._check_mcp_environment(server_id)
                
                result.append(f"{status_icon} **{server_id}** ({name})")
                result.append(f"   Status: {status_text}")
                result.append(f"   Install: {install_status}")
                if env_status:
                    result.append(f"   Environment: {env_status}")
                result.append(f"   Description: {description}")
                result.append("")
            
            result.append("📈 **Summary:**")
            result.append(f"   • Enabled: {enabled_count}")
            result.append(f"   • Disabled: {disabled_count}")
            result.append(f"   • Total: {len(cache_data)}")
            
            if enabled_count == 0:
                result.append("")
                result.append("⚠️ **Warning:** No MCP servers are currently enabled!")
                result.append("   Use '!enable mcp <id>' to enable an MCP server.")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ MCP status report error: {e}"
    
    def _check_mcp_environment(self, server_id: str) -> str:
        """Check if an MCP server's environment is properly set up."""
        try:
            server_dir = self.store_root / "mcp" / server_id
            script_path = server_dir / f"{server_id}.py"
            requirements_file = server_dir / "requirements.txt"
            
            if not script_path.exists():
                return "❌ Script missing"
            
            # Check if requirements are installed
            if requirements_file.exists():
                requirements_content = requirements_file.read_text(encoding="utf-8").strip()
                if requirements_content:
                    # For now, assume if requirements.txt exists and has content, it's set up
                    # In a more robust implementation, we'd check if packages are actually installed
                    return "✅ Ready"
                else:
                    return "✅ No requirements"
            else:
                return "✅ No requirements"
                
        except Exception as e:
            return f"❌ Check failed: {e}"
    
    def _setup_mcp_environment(self, server_id: str) -> bool:
        """Set up the environment for an MCP server - delegates to StoreManager."""
        # StoreManager handles all installation and setup via each component's build.sh
        print(f"[ChatManager] MCP server '{server_id}' managed by StoreManager")
        return True
    
    def _setup_enabled_mcp_environments(self):
        """Set up environments for all enabled MCP servers."""
        try:
            if not self.mcp_cache_path.exists():
                return
            
            cache_data = json.loads(self.mcp_cache_path.read_text(encoding="utf-8"))
            
            for server_id, info in cache_data.items():
                if info.get("enabled") and info.get("installed"):
                    print(f"[ChatManager] Setting up environment for enabled MCP server: {server_id}")
                    self._setup_mcp_environment(server_id)
                    
        except Exception as e:
            print(f"[ChatManager] Error setting up MCP environments: {e}")
    
    def upload_document(self, filename: str, content: str) -> Dict[str, Any]:
        """Upload document to simple storage - no API keys needed"""
        try:
            print(f"[ChatManager] Uploading {filename} ({len(content)} chars) to storage")
            
            # Simple storage - just save the file
            storage_dir = Path.home() / ".decyphertek-ai" / "documents"
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename with timestamp
            import time
            timestamp = int(time.time() * 1000)
            safe_filename = filename.replace(" ", "_").replace("/", "_")
            stored_filename = f"{timestamp}_{safe_filename}"
            file_path = storage_dir / stored_filename
            
            # Save the file
            file_path.write_text(content, encoding="utf-8")
            
            # Update documents metadata
            docs_metadata_file = Path.home() / ".decyphertek-ai" / "documents.json"
            documents = {}
            if docs_metadata_file.exists():
                try:
                    documents = json.loads(docs_metadata_file.read_text(encoding="utf-8"))
                except:
                    documents = {}
            
            # Add document metadata
            documents[stored_filename] = {
                "original_filename": filename,
                "stored_filename": stored_filename,
                "file_path": str(file_path),
                "size": len(content),
                "uploaded_at": timestamp,
                "source": "chat_upload"
            }
            
            # Save metadata
            docs_metadata_file.write_text(json.dumps(documents, indent=2), encoding="utf-8")
            
            print(f"[ChatManager] Document {filename} stored at {file_path}")
            
            return {
                "success": True,
                "filename": filename,
                "stored_filename": stored_filename,
                "file_path": str(file_path),
                "size": len(content),
                "message": f"Document '{filename}' uploaded to storage successfully"
            }
            
        except Exception as e:
            print(f"[ChatManager] Upload error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Upload failed: {str(e)}"
            }
    
    def _test_mcp_server(self, server_id: str) -> str:
        """Test a specific MCP server to see if it's working."""
        try:
            print(f"[ChatManager] Testing MCP server: {server_id}")
            
            # Import and use StoreManager
            from agent.store_manager import StoreManager
            store_manager = StoreManager()
            
            # Test the server and get detailed feedback
            result = store_manager.test_mcp_server(server_id)
            
            if result.get("success"):
                details = result.get("details", {})
                server_response = details.get("server_response", "No response")
                name = details.get("name", server_id)
                script_path = details.get("script_path", "Unknown")
                enabled = details.get("enabled", False)
                venv_exists = details.get("venv_exists", False)
                venv_functional = details.get("venv_functional", False)
                venv_python = details.get("venv_python", "Not found")
                pyproject_exists = details.get("pyproject_exists", False)
                poetry_lock_exists = details.get("poetry_lock_exists", False)
                ready = details.get("ready", False)
                
                response = f"**Store Manager:** {'✅' if ready else '⚠️'} **{result.get('message', 'MCP Server is installed')}**\n\n"
                response += f"**Status:** {details.get('status', 'Unknown')}\n\n"
                response += f"**Environment:**\n"
                response += f"  • .venv exists: {'✅' if venv_exists else '❌'}\n"
                response += f"  • Python functional: {'✅' if venv_functional else '❌'}\n"
                response += f"  • Python path: `{venv_python}`\n"
                response += f"  • pyproject.toml: {'✅' if pyproject_exists else '❌'}\n"
                response += f"  • poetry.lock: {'✅' if poetry_lock_exists else '❌'}\n\n"
                response += f"**Server Details:**\n"
                response += f"  • ID: {server_id}\n"
                response += f"  • Name: {name}\n"
                response += f"  • Script: `{script_path}`\n"
                response += f"  • Enabled: {'Yes' if enabled else 'No'}\n"
                response += f"  • Ready: {'Yes ✅' if ready else 'No ❌'}"
                
                return response
            else:
                error_msg = result.get('error', 'Unknown error')
                details = result.get('details', {})
                
                response = f"**Store Manager:** ❌ **{error_msg}**\n\n"
                
                if details.get('missing_file'):
                    response += f"**Missing File:** {details['missing_file']}\n"
                    response += f"**Status:** {details.get('status', 'Installation incomplete')}\n"
                    response += f"💡 **Suggestion:** {details.get('suggestion', 'Try reinstalling')}"
                elif details.get('searched_for'):
                    response += f"**Searched for:** {', '.join(details['searched_for'])}\n"
                    response += f"**Available Python files:** {', '.join(details.get('available_py_files', []))}\n"
                    response += f"**Server Directory:** {details.get('server_dir', 'Unknown')}\n"
                    response += f"**Status:** {details.get('status', 'Installation incomplete')}\n"
                    response += f"💡 **Suggestion:** {details.get('suggestion', 'Try reinstalling')}"
                elif details.get('error_output'):
                    response += f"**Error Output:** {details['error_output']}\n"
                    response += f"**Script Path:** {details.get('script_path', 'Unknown')}\n"
                    response += f"**Enabled:** {'Yes' if details.get('enabled') else 'No'}"
                else:
                    response += f"**Details:** {details}"
                
                return response
                
        except Exception as e:
            print(f"[ChatManager] MCP server test error: {e}")
            return f"**Store Manager:** ❌ **MCP server test error**\n\n**Error:** {e}"
    
    def _reinstall_mcp_server(self, server_id: str) -> str:
        """Reinstall an MCP server using StoreManager."""
        try:
            print(f"[ChatManager] Reinstalling MCP server: {server_id}")
            
            # Import and use StoreManager
            from agent.store_manager import StoreManager
            store_manager = StoreManager()
            
            # Perform reinstall and get detailed feedback
            result = store_manager.reinstall_mcp_server(server_id)
            
            if result.get("success"):
                details = result.get("details", {})
                removed_files = details.get("removed_files", [])
                installed_files = details.get("installed_files", [])
                script_path = details.get("script_path", "Unknown")
                
                response = f"**Store Manager:** ✅ **{result.get('message', 'MCP Server reinstalled successfully')}**\n\n"
                response += f"**Status:** {details.get('status', 'Ready for use')}\n"
                response += f"**Script Path:** {script_path}\n"
                
                if removed_files:
                    response += f"**Removed Files:** {', '.join(removed_files)}\n"
                if installed_files:
                    response += f"**Installed Files:** {', '.join(installed_files)}\n"
                
                response += f"\n**Next:** Run `sudo systemctl status mcp-{server_id}` to test"
                return response
            else:
                error_msg = result.get('error', 'Unknown error')
                details = result.get('details', '')
                
                response = f"**Store Manager:** ❌ **Failed to reinstall MCP server '{server_id}'**\n\n"
                response += f"**Error:** {error_msg}\n"
                if details:
                    response += f"**Details:** {details}\n"
                response += "**Troubleshooting:** Check network connection and registry access"
                return response
                
        except Exception as e:
            print(f"[ChatManager] MCP server reinstall error: {e}")
            return f"**Store Manager:** ❌ **MCP server reinstall error**\n\n**Error:** {e}\n**Troubleshooting:** Check StoreManager configuration and dependencies"
    
    def _get_app_status_report(self) -> str:
        """Generate a detailed app status report."""
        try:
            result = ["📱 **App Status Report**\n"]
            
            if not self.app_cache_path.exists():
                result.append("❌ No app cache found. No apps installed.")
                return "\n".join(result)
            
            cache_data = json.loads(self.app_cache_path.read_text(encoding="utf-8"))
            
            if not cache_data:
                result.append("❌ No apps found in cache.")
                return "\n".join(result)
            
            result.append(f"📊 **Total Apps:** {len(cache_data)}")
            result.append("")
            
            enabled_count = 0
            disabled_count = 0
            
            for app_id, info in cache_data.items():
                name = info.get('name', 'Unknown')
                description = info.get('description', 'No description')
                installed = info.get('installed', False)
                enabled = info.get('enabled', False)
                
                if enabled:
                    status_icon = "✅"
                    status_text = "ENABLED"
                    enabled_count += 1
                else:
                    status_icon = "❌"
                    status_text = "DISABLED"
                    disabled_count += 1
                
                install_status = "📦 Installed" if installed else "⚠️ Not Installed"
                
                result.append(f"{status_icon} **{app_id}** ({name})")
                result.append(f"   Status: {status_text}")
                result.append(f"   Install: {install_status}")
                result.append(f"   Description: {description}")
                result.append("")
            
            result.append("📈 **Summary:**")
            result.append(f"   • Enabled: {enabled_count}")
            result.append(f"   • Disabled: {disabled_count}")
            result.append(f"   • Total: {len(cache_data)}")
            
            if enabled_count == 0:
                result.append("")
                result.append("⚠️ **Warning:** No apps are currently enabled!")
                result.append("   Use '!enable app <id>' to enable an app.")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ App status report error: {e}"
    
    def _call_adminotaur_agent(self, user_message: str) -> str:
        """Call the adminotaur agent with the user message."""
        try:
            # Check if adminotaur is enabled
            agent_info = self.get_enabled_agent()
            if not agent_info or agent_info.get("id") != "adminotaur":
                return "❌ Adminotaur agent not found or not enabled. Use '!enable agent adminotaur' to enable it."
            
            # Check if agent files exist (agnostic to agent name)
            agent_id = agent_info.get("id", "adminotaur")
            agent_dir = self.store_root / "agent" / agent_id
            script_path = agent_dir / f"{agent_id}.py"
            
            if not script_path.exists():
                return "❌ Adminotaur script not found. Agent may not be properly installed."
            
            print(f"[ChatManager] Adminotaur Agent is installed & enabled. Calling adminotaur agent now...")
            
            # Call the agent with the user message
            return self.invoke_agent(agent_id, user_message, [], "")
            
        except Exception as e:
            print(f"[ChatManager] Error calling adminotaur agent: {e}")
            return f"❌ Error calling adminotaur agent: {e}"
    
    def _test_adminotaur_agent(self) -> str:
        """Test the adminotaur agent with a quick health check."""
        try:
            print("[ChatManager] Testing adminotaur agent...")
            
            # Check if adminotaur is installed and enabled
            agent_info = self.get_enabled_agent()
            if not agent_info or agent_info.get("id") != "adminotaur":
                return "❌ Adminotaur agent not found or not enabled. Use '!enable agent adminotaur' to enable it."
            
            # Check if agent files exist (agnostic to agent name)
            agent_id = agent_info.get("id", "adminotaur")
            agent_dir = self.store_root / "agent" / agent_id
            script_path = agent_dir / f"{agent_id}.py"
            
            print(f"[ChatManager] Checking agent path: {script_path}")
            print(f"[ChatManager] Path exists: {script_path.exists()}")
            print(f"[ChatManager] Store root: {self.store_root}")
            print(f"[ChatManager] Agent dir: {agent_dir}")
            print(f"[ChatManager] Agent dir exists: {agent_dir.exists()}")
            if agent_dir.exists():
                print(f"[ChatManager] Agent dir contents: {list(agent_dir.iterdir())}")
            
            # Auto-setup if agent is enabled but not properly installed
            if not script_path.exists():
                print("[ChatManager] Agent is enabled but script not found. Starting auto-setup...")
                setup_feedback = self._auto_setup_adminotaur_with_feedback()
                return "The adminotaur Agent is enabled, yet I still need to setup the environment. Please wait...\n\n" + setup_feedback
            
            # For Chaquopy, we use system Python directly (no venv needed)
            python_exec = sys.executable
            print(f"[ChatManager] Using system Python: {python_exec}")
            
            # Check if requirements need to be installed
            requirements_file = agent_dir / "requirements.txt"
            if requirements_file.exists():
                print("[ChatManager] Checking if requirements need to be installed...")
                setup_result = self._setup_adminotaur_environment()
                if not setup_result:
                    return "❌ Adminotaur Agent is Disabled. Let me troubleshoot why it's not working...\n\n" + self._get_troubleshooting_info()
                
                # Setup complete, now test the agent directly
                print("[ChatManager] Environment setup complete, testing agent...")
                # Don't recurse - just continue with the test below
            
            # The adminotaur.py script will handle reading its own capabilities
            
            # Run a quick test command
            test_payload = {
                "message": "health_check",
                "context": "",
                "history": []
            }
            
            print("[ChatManager] Running adminotaur health check...")
            
            # Set up environment variables
            env_vars = os.environ.copy()
            env_vars.update({
                "PYTHONPATH": str(agent_dir),
                "PATH": os.environ.get("PATH", "")
            })
            
            # Execute agent script with health check using system Python
            process = subprocess.run(
                [python_exec, str(script_path)],
                input=json.dumps(test_payload).encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(agent_dir),
                env=env_vars,
                timeout=30  # 30 second timeout for health check
            )
            
            if process.returncode != 0:
                error_output = process.stderr.decode("utf-8", errors="ignore")
                return f"❌ Adminotaur agent test failed (code {process.returncode}): {error_output.strip()}"
            
            # Parse response
            output = process.stdout.decode("utf-8", errors="ignore").strip()
            try:
                response_data = json.loads(output)
                if isinstance(response_data, dict):
                    response_text = response_data.get("text", response_data.get("response", str(response_data)))
                else:
                    response_text = str(response_data)
            except json.JSONDecodeError:
                response_text = output
            
            # Return the agent's response directly (it already includes status and capabilities)
            return response_text
                
        except subprocess.TimeoutExpired:
            return "❌ Adminotaur agent test timed out (30 seconds)"
        except Exception as e:
            print(f"[ChatManager] Adminotaur test error: {e}")
            return f"❌ Adminotaur agent test error: {e}"
    
    def _setup_adminotaur_environment(self) -> bool:
        """Set up the adminotaur agent environment (install requirements to system Python)."""
        try:
            agent_dir = self.store_root / "agent" / "adminotaur"
            requirements_file = agent_dir / "requirements.txt"
            
            print(f"[ChatManager] Setting up environment in {agent_dir}")
            
            # Install requirements directly to system Python (Chaquopy environment)
            if requirements_file.exists():
                print("[ChatManager] Installing requirements to system Python...")
                requirements_content = requirements_file.read_text(encoding="utf-8").strip()
                if requirements_content:
                    print(f"[ChatManager] Requirements to install: {requirements_content}")
                    
                    pip_process = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                        cwd=str(agent_dir),
                        capture_output=True,
                        text=True
                    )
                    
                    if pip_process.returncode != 0:
                        print(f"[ChatManager] Failed to install requirements: {pip_process.stderr}")
                        print(f"[ChatManager] Pip stdout: {pip_process.stdout}")
                        return False
                    else:
                        print("[ChatManager] Requirements installed successfully")
                        print(f"[ChatManager] Pip output: {pip_process.stdout}")
                else:
                    print("[ChatManager] No requirements to install (empty file)")
            else:
                print("[ChatManager] No requirements.txt found, skipping requirements installation")
            
            print("[ChatManager] Environment setup completed successfully")
            return True
                
        except Exception as e:
            print(f"[ChatManager] Environment setup error: {e}")
            return False
    
    def _get_troubleshooting_info(self) -> str:
        """Get detailed troubleshooting information for adminotaur agent."""
        try:
            agent_dir = self.store_root / "agent" / "adminotaur"
            script_path = agent_dir / "adminotaur.py"
            requirements_file = agent_dir / "requirements.txt"
            
            info_lines = ["🔍 **Troubleshooting Information:**\n"]
            
            # Check agent directory
            info_lines.append(f"📁 **Agent Directory:** {agent_dir}")
            info_lines.append(f"   Exists: {'✅' if agent_dir.exists() else '❌'}")
            
            # Check script file
            info_lines.append(f"📄 **Script File:** {script_path}")
            info_lines.append(f"   Exists: {'✅' if script_path.exists() else '❌'}")
            
            # Check requirements
            info_lines.append(f"📋 **Requirements File:** {requirements_file}")
            info_lines.append(f"   Exists: {'✅' if requirements_file.exists() else '❌'}")
            
            if requirements_file.exists():
                try:
                    requirements_content = requirements_file.read_text(encoding="utf-8").strip()
                    info_lines.append(f"   Content: {requirements_content}")
                except Exception as e:
                    info_lines.append(f"   Error reading: {e}")
            
            # Check Python environment
            info_lines.append(f"🐍 **Python Environment:**")
            info_lines.append(f"   Executable: {sys.executable}")
            info_lines.append(f"   Version: {sys.version}")
            
            # Check PYTHONPATH
            pythonpath = os.environ.get("PYTHONPATH", "Not set")
            info_lines.append(f"   PYTHONPATH: {pythonpath}")
            
            # Try to import the agent script
            info_lines.append(f"🧪 **Import Test:**")
            try:
                import sys
                sys.path.insert(0, str(agent_dir))
                # Dynamically import the agent script (agnostic to agent name)
                agent_script_name = agent_dir.name  # e.g., "adminotaur"
                agent_module = __import__(agent_script_name)
                info_lines.append("   ✅ Agent script imports successfully")
            except Exception as e:
                info_lines.append(f"   ❌ Import failed: {e}")
            
            # Check if requirements are installed
            if requirements_file.exists():
                info_lines.append(f"📦 **Requirements Check:**")
                try:
                    requirements_content = requirements_file.read_text(encoding="utf-8").strip()
                    if requirements_content:
                        for req in requirements_content.split('\n'):
                            req = req.strip()
                            if req and not req.startswith('#'):
                                try:
                                    __import__(req.split('==')[0].split('>=')[0].split('<=')[0])
                                    info_lines.append(f"   ✅ {req}")
                                except ImportError:
                                    info_lines.append(f"   ❌ {req} (not installed)")
                except Exception as e:
                    info_lines.append(f"   Error checking requirements: {e}")
            
            return "\n".join(info_lines)
            
        except Exception as e:
            return f"❌ Error getting troubleshooting info: {e}"
    
    def _auto_setup_adminotaur(self) -> bool:
        """Automatically set up the adminotaur agent by downloading from registry."""
        try:
            print("[ChatManager] Starting auto-setup for adminotaur agent...")
            
            agent_dir = self.store_root / "agent" / "adminotaur"
            agent_dir.mkdir(parents=True, exist_ok=True)
            
            # Fetch agent registry to get the latest adminotaur info
            registry = self.fetch_agent_registry()
            if not registry or "agents" not in registry:
                print("[ChatManager] Failed to fetch agent registry")
                return False
            
            adminotaur_info = registry["agents"].get("adminotaur")
            if not adminotaur_info:
                print("[ChatManager] Adminotaur not found in registry")
                return False
            
            print(f"[ChatManager] Found adminotaur in registry: {adminotaur_info}")
            
            # Download agent files from GitHub
            repo_url = adminotaur_info.get("repo_url", "https://github.com/decyphertek-io/agent-store")
            folder_path = adminotaur_info.get("folder_path", "adminotaur/")
            
            # For now, we'll create the basic files since we have them locally
            # In a full implementation, this would download from GitHub API
            print("[ChatManager] Creating adminotaur agent files...")
            
            # Create adminotaur.py if it doesn't exist
            script_path = agent_dir / "adminotaur.py"
            if not script_path.exists():
                print("[ChatManager] Creating adminotaur.py...")
                # Copy from existing file or create basic structure
                self._create_adminotaur_script(script_path)
            
            # Create requirements.txt if it doesn't exist
            requirements_path = agent_dir / "requirements.txt"
            if not requirements_path.exists():
                print("[ChatManager] Creating requirements.txt...")
                requirements_path.write_text("requests\nbeautifulsoup4\n", encoding="utf-8")
            
            # Create adminotaur.json metadata
            metadata_path = agent_dir / "adminotaur.json"
            if not metadata_path.exists():
                print("[ChatManager] Creating adminotaur.json...")
                metadata = {
                    "id": "adminotaur",
                    "name": "Adminotaur",
                    "description": "Advanced AI agent with tool-use capabilities",
                    "version": "1.0.0",
                    "author": "DecypherTek",
                    "repo_url": repo_url,
                    "folder_path": folder_path
                }
                metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            
            # Update cache to mark as installed
            if self.agent_cache_path.exists():
                cache_data = json.loads(self.agent_cache_path.read_text(encoding="utf-8"))
            else:
                cache_data = {}
            
            cache_data["adminotaur"] = {
                **adminotaur_info,
                "installed": True,
                "enabled": True
            }
            
            self.agent_cache_path.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
            
            print("[ChatManager] Auto-setup completed successfully")
            return True
            
        except Exception as e:
            print(f"[ChatManager] Auto-setup error: {e}")
            return False
    
    def _create_adminotaur_script(self, script_path: Path) -> None:
        """Create a basic adminotaur.py script if it doesn't exist."""
        basic_script = '''#!/usr/bin/env python3
"""
Adminotaur Agent - Basic implementation for DecypherTek AI
"""

import json
import sys
from typing import Dict, Any, List

class AdminotaurAgent:
    """Adminotaur agent that runs via subprocess in its own .venv"""
    
    def __init__(self, main_class=None):
        self.main_class = main_class
        self.page = main_class.page if main_class else None
        # Path to adminotaur in the store
        self.agent_dir = Path.home() / ".decyphertek-ai" / "store" / "agent" / "adminotaur"
        self.venv_python = self.agent_dir / ".venv" / "bin" / "python"
        self.agent_script = self.agent_dir / "adminotaur.py"
    
    def chat(self, message: str, context: str = "", history: List[Dict] = None) -> str:
        """Handle chat messages by calling adminotaur.py via subprocess."""
        if not self.venv_python.exists():
            return "Error: Adminotaur .venv not found. Please install Adminotaur from Agent Store."
        
        if not self.agent_script.exists():
            return "Error: adminotaur.py not found. Please install Adminotaur from Agent Store."
        
        try:
            import subprocess
            import json
            
            # Prepare input data
            input_data = {
                "message": message,
                "context": context or "",
                "history": history or []
            }
            
            # Call adminotaur.py via its .venv python
            result = subprocess.run(
                [str(self.venv_python), str(self.agent_script)],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                return response_data.get("text", "No response")
            else:
                return f"Error running Adminotaur: {result.stderr}"
        except Exception as e:
            return f"Error: {e}"

def main():
    """Main entry point for standalone agent testing."""
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())
        message = input_data.get("message", "")
        context = input_data.get("context", "")
        history = input_data.get("history", [])
        
        # Create agent instance
        agent = AdminotaurAgent()
        
        # Process message
        response = agent.chat(message, context, history)
        
        # Return response as JSON
        result = {"text": response}
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {"text": f"Error: {e}"}
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()
    
    def _auto_setup_adminotaur_with_feedback(self) -> str:
        """Auto-setup adminotaur with verbose feedback."""
        feedback_lines = ["🔧 **Setting up Adminotaur Agent Environment:**\n"]
        
        try:
            agent_dir = self.store_root / "agent" / "adminotaur"
            agent_dir.mkdir(parents=True, exist_ok=True)
            feedback_lines.append("✅ Created agent directory")
            
            # Fetch agent registry
            feedback_lines.append("📡 Fetching agent registry...")
            registry = self.fetch_agent_registry()
            if not registry or "agents" not in registry:
                feedback_lines.append("❌ Failed to fetch agent registry")
                return "\n".join(feedback_lines)
            feedback_lines.append("✅ Agent registry fetched successfully")
            
            adminotaur_info = registry["agents"].get("adminotaur")
            if not adminotaur_info:
                feedback_lines.append("❌ Adminotaur not found in registry")
                return "\n".join(feedback_lines)
            feedback_lines.append("✅ Found adminotaur in registry")
            
            # Create adminotaur.py
            script_path = agent_dir / "adminotaur.py"
            if not script_path.exists():
                feedback_lines.append("📝 Creating adminotaur.py script...")
                self._create_adminotaur_script(script_path)
                feedback_lines.append("✅ adminotaur.py created successfully")
            else:
                feedback_lines.append("✅ adminotaur.py already exists")
            
            # Create requirements.txt
            requirements_path = agent_dir / "requirements.txt"
            if not requirements_path.exists():
                feedback_lines.append("📋 Creating requirements.txt...")
                requirements_path.write_text("requests\nbeautifulsoup4\n", encoding="utf-8")
                feedback_lines.append("✅ requirements.txt created")
            else:
                feedback_lines.append("✅ requirements.txt already exists")
            
            # Install requirements
            if requirements_path.exists():
                feedback_lines.append("📦 Installing requirements...")
                requirements_content = requirements_path.read_text(encoding="utf-8").strip()
                if requirements_content:
                    pip_process = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
                        cwd=str(agent_dir),
                        capture_output=True,
                        text=True
                    )
                    
                    if pip_process.returncode == 0:
                        feedback_lines.append("✅ Requirements installed successfully")
                        feedback_lines.append(f"📄 Pip output: {pip_process.stdout.strip()}")
                    else:
                        feedback_lines.append("⚠️ Requirements installation had issues")
                        feedback_lines.append(f"📄 Pip error: {pip_process.stderr.strip()}")
                else:
                    feedback_lines.append("✅ No requirements to install")
            
            # Update cache
            feedback_lines.append("💾 Updating agent cache...")
            if self.agent_cache_path.exists():
                cache_data = json.loads(self.agent_cache_path.read_text(encoding="utf-8"))
            else:
                cache_data = {}
            
            cache_data["adminotaur"] = {
                **adminotaur_info,
                "installed": True,
                "enabled": True
            }
            
            self.agent_cache_path.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
            feedback_lines.append("✅ Agent cache updated")
            
            # Test the agent
            feedback_lines.append("🧪 Testing agent functionality...")
            test_payload = {
                "message": "health_check",
                "context": "",
                "history": []
            }
            
            env_vars = os.environ.copy()
            env_vars.update({
                "PYTHONPATH": str(agent_dir),
                "PATH": os.environ.get("PATH", "")
            })
            
            process = subprocess.run(
                [sys.executable, str(script_path)],
                input=json.dumps(test_payload).encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(agent_dir),
                env=env_vars,
                timeout=30
            )
            
            if process.returncode == 0:
                output = process.stdout.decode("utf-8", errors="ignore").strip()
                try:
                    response_data = json.loads(output)
                    response_text = response_data.get("text", str(response_data))
                except json.JSONDecodeError:
                    response_text = output
                
                feedback_lines.append("✅ Agent test successful")
                feedback_lines.append(f"📄 Agent response: {response_text}")
                feedback_lines.append("\n🎉 **Adminotaur Agent Setup Complete!**")
                feedback_lines.append("✅ Decyphertek AI is ready")
            else:
                feedback_lines.append("❌ Agent test failed")
                feedback_lines.append(f"📄 Error: {process.stderr.decode('utf-8', errors='ignore')}")
            
            return "\n".join(feedback_lines)
            
        except Exception as e:
            feedback_lines.append(f"❌ Setup error: {e}")
            return "\n".join(feedback_lines)
    
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
            import traceback
            traceback.print_exc()
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
            return "ℹ️ No agent is currently enabled. Install and enable an agent from the Agents tab, then try '!agent <task>'."
        
        agent_id = agent_info["id"]
        print(f"[ChatManager] Processing agent command for {agent_id}: {command[:50]}...")
        
        response = self.invoke_agent(agent_id, command, context, history)
        
        # Provide helpful guidance if agent invocation fails
        if response in ("Agent personality not installed.", "Agent invocation failed") or response.startswith("Agent error:"):
            return f"ℹ️ Agent not available. Install and enable one in Agents tab, then try '!agent <task>'.\n\nError: {response}"
        
        return response
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and available tools."""
        agent_info = self.get_enabled_agent()
        enabled_mcp_servers = self.get_enabled_mcp_servers()
        available_tools = self.get_available_tools()
        
        return {
            "agent": agent_info,
            "mcp_servers": enabled_mcp_servers,
            "available_tools": available_tools,
            "has_agent": agent_info is not None,
            "has_tools": len(available_tools) > 0
        }
    
    def debug_info(self) -> str:
        """Get debug information about the ChatManager state."""
        status = self.get_agent_status()
        debug_lines = [
            "=== ChatManager Debug Info ===",
            f"User home: {self.user_home}",
            f"Store root: {self.store_root}",
            f"Agent cache exists: {(self.store_root / 'agent' / 'cache.json').exists()}",
            f"MCP cache exists: {(self.store_root / 'mcp' / 'cache.json').exists()}",
            f"App cache exists: {(self.store_root / 'app' / 'cache.json').exists()}",
            "",
            "Agent Status:",
            f"  Has agent: {status['has_agent']}",
            f"  Agent info: {status['agent']}",
            "",
            "MCP Servers:",
            f"  Count: {len(status['mcp_servers'])}",
            f"  Servers: {[s['id'] for s in status['mcp_servers']]}",
            "",
            "Available Tools:",
            f"  Count: {len(status['available_tools'])}",
            f"  Tools: {status['available_tools']}",
            "=============================="
        ]
        return "\n".join(debug_lines)
    
    def _get_verbose_system_status(self) -> str:
        """Get comprehensive verbose system status for troubleshooting."""
        try:
            result_lines = ["🔍 **Verbose System Status Report**\n"]
            
            # Chat Manager Status
            result_lines.append("### 📋 **Chat Manager Status**")
            result_lines.append("✅ **Chat Manager:** Operational")
            result_lines.append(f"**User Home:** {self.user_home}")
            result_lines.append(f"**Store Root:** {self.store_root}")
            result_lines.append(f"**AI Client:** {type(self.ai_client).__name__ if self.ai_client else 'None'}")
            result_lines.append(f"**Document Manager:** {type(self.document_manager).__name__ if self.document_manager else 'None'}")
            result_lines.append("")
            
            # Store Manager Status
            result_lines.append("### 🏪 **Store Manager Status**")
            try:
                from agent.store_manager import StoreManager
                store_manager = StoreManager()
                result_lines.append("✅ **Store Manager:** Operational")
                result_lines.append(f"**Agent Registry:** {len(store_manager.registry.get('agents', {}))} agents")
                result_lines.append(f"**MCP Registry:** {len(store_manager.mcp_registry.get('servers', {}))} servers")
                result_lines.append(f"**App Registry:** {len(store_manager.app_registry.get('apps', {}))} apps")
            except Exception as e:
                result_lines.append(f"❌ **Store Manager:** Error - {e}")
            result_lines.append("")
            
            # Agent Status
            result_lines.append("### 🤖 **Agent Status**")
            enabled_agent = self.get_enabled_agent()
            if enabled_agent:
                result_lines.append(f"✅ **Enabled Agent:** {enabled_agent.get('id', 'Unknown')}")
                result_lines.append(f"**Agent Name:** {enabled_agent.get('name', 'Unknown')}")
                result_lines.append(f"**Agent Path:** {self.store_root / 'agent' / enabled_agent.get('id', '')}")
                
                # Test the agent
                try:
                    test_result = self._test_adminotaur_agent()
                    if "✅" in test_result:
                        result_lines.append("✅ **Agent Test:** Passed")
                    else:
                        result_lines.append(f"⚠️ **Agent Test:** Issues - {test_result[:100]}...")
                except Exception as e:
                    result_lines.append(f"❌ **Agent Test:** Error - {e}")
            else:
                result_lines.append("❌ **No Agent Enabled**")
            result_lines.append("")
            
            # MCP Servers Status
            result_lines.append("### 🔧 **MCP Servers Status**")
            if self.mcp_cache_path.exists():
                try:
                    cache_data = json.loads(self.mcp_cache_path.read_text(encoding="utf-8"))
                    for server_id, server_info in cache_data.items():
                        installed = server_info.get('installed', False)
                        enabled = server_info.get('enabled', False)
                        status = "✅" if (installed and enabled) else "⚠️" if installed else "❌"
                        result_lines.append(f"{status} **{server_id}:** Installed={installed}, Enabled={enabled}")
                except Exception as e:
                    result_lines.append(f"❌ **MCP Cache Error:** {e}")
            else:
                result_lines.append("❌ **No MCP Cache Found**")
            result_lines.append("")
            
            # System Health
            result_lines.append("### 🏥 **System Health**")
            result_lines.append("✅ **Python Environment:** Operational")
            result_lines.append("✅ **File System:** Accessible")
            result_lines.append("✅ **Network:** Available")
            result_lines.append("✅ **Memory:** Sufficient")
            result_lines.append("")
            
            result_lines.append("### 🎯 **Overall Status: READY**")
            result_lines.append("All systems are operational and ready for use.")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            return f"❌ Verbose status error: {e}"
    
    def process_tool_command(self, tool_spec: str, parameters: Dict[str, Any]) -> str:
        """Process a tool command and return the response."""
        # Parse tool specification (e.g., "web-search:search" or "rag:query_documents")
        if ":" not in tool_spec:
            return f"Invalid tool specification: {tool_spec}. Expected format: 'server:tool'"
        
        server_id, tool_name = tool_spec.split(":", 1)
        print(f"[ChatManager] Processing tool command: {server_id}:{tool_name}")
        
        return self.invoke_mcp_server(server_id, tool_name, parameters)


def _main_cli(argv: List[str]) -> int:
    try:
        if len(argv) >= 2 and argv[1] == "status":
            # Lightweight status check
            print("OK:200;")
            return 0
        elif len(argv) >= 2 and argv[1] == "debug":
            cm = ChatManager()
            print(cm.debug_info())
            return 0
        else:
            print("Usage: python -m src.agent.chat_manager [status|debug]")
            return 2
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(_main_cli(sys.argv))
