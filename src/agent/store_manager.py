from __future__ import annotations

"""
Store Manager for Agent Store (personalities)

Responsibilities (minimal):
- Fetch personality registry (JSON) from remote
- Download only the specified personality folder via GitHub Contents API
- Install locally under agent-store/
- Persist enabled/disabled state
- Dynamically load the personality module/class

UI can call:
- fetch_registry()
- get_default_agent_id()
- list_agents_for_ui()
- is_installed(agent_id)
- install_agent(agent_id)
- is_enabled(agent_id), set_enabled(agent_id, enabled)
- load_agent(agent_id)

Source of truth registry:
- https://github.com/decyphertek-io/agent-store/blob/main/personality.json
  (Use raw: https://raw.githubusercontent.com/decyphertek-io/agent-store/main/personality.json)
"""

import json
import os
import time
import urllib.request
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional
import importlib.util
import subprocess
import sys


class StoreManager:
    def __init__(self, registry_url: Optional[str] = None) -> None:
        self.project_root = Path(__file__).resolve().parents[2]
        
        # NEW ARCHITECTURE: All installed components go to ~/.decyphertek-ai/store/
        # Bundled templates stay in ./src/store/
        self.user_home = Path.home() / ".decyphertek-ai"
        self.user_store_root = self.user_home / "store"
        
        # Installed stores (in user home)
        self.local_store_root = self.user_store_root / "agent"
        self.mcp_store_root = self.user_store_root / "mcp"
        self.app_local_root = self.user_store_root / "app"
        
        # Bundled stores (in project, read-only templates)
        self.bundled_agent_root = self.project_root / "src" / "store" / "agent"
        self.bundled_mcp_root = self.project_root / "src" / "store" / "mcp"
        self.bundled_app_root = self.project_root / "src" / "store" / "app"
        
        # State files
        self.enabled_state_path = self.user_home / "agent-enabled.json"
        self.mcp_enabled_state_path = self.user_home / "mcp-enabled.json"
        self.app_enabled_state_path = self.user_home / "app-enabled.json"

        # Registries
        self.registry_url = (
            registry_url
            or "https://raw.githubusercontent.com/decyphertek-io/agent-store/main/personality.json"
        )
        self.mcp_registry_url = "https://raw.githubusercontent.com/decyphertek-io/mcp-store/main/skills.json"
        self.app_registry_url = "https://raw.githubusercontent.com/decyphertek-io/app-store/main/app.json"
        
        self.registry: Dict[str, Any] = {}
        self.mcp_registry: Dict[str, Any] = {}
        self.app_registry: Dict[str, Any] = {}
        
        self.enabled_state: Dict[str, bool] = self._load_enabled_state()
        self.mcp_enabled_state: Dict[str, bool] = self._load_mcp_enabled_state()
        self.app_enabled_state: Dict[str, bool] = self._load_enabled_state_generic(self.app_enabled_state_path)
        
        # Ensure store directories exist
        self.local_store_root.mkdir(parents=True, exist_ok=True)
        self.mcp_store_root.mkdir(parents=True, exist_ok=True)
        self.app_local_root.mkdir(parents=True, exist_ok=True)
        
        # Auto-install components with enable_by_default: true
        self._start_agent_background_sync()
        self._start_mcp_background_sync()

    # -------------------
    # Registry management
    # -------------------
    def fetch_registry(self) -> Dict[str, Any]:
        try:
            with urllib.request.urlopen(self.registry_url, timeout=20) as resp:
                data = resp.read()
            reg = json.loads(data.decode("utf-8"))
            if not isinstance(reg, dict) or "agents" not in reg:
                raise ValueError("Invalid personality registry")
            self.registry = reg
            return reg
        except Exception as e:
            print(f"[StoreManager] Registry fetch error: {e}")
            # Attempt local fallback
            local_json = self.local_store_root / "personality.json"
    
    def fetch_mcp_registry(self) -> Dict[str, Any]:
        try:
            with urllib.request.urlopen(self.mcp_registry_url, timeout=20) as resp:
                data = resp.read()
            reg = json.loads(data.decode("utf-8"))
            if not isinstance(reg, dict) or "servers" not in reg:
                raise ValueError("Invalid MCP registry")
            self.mcp_registry = reg
            return reg
        except Exception as e:
            print(f"[StoreManager] MCP registry fetch error: {e}")
            # Attempt local fallback
            local_json = self.mcp_store_root / "skills.json"
            if local_json.exists():
                try:
                    self.registry = json.loads(local_json.read_text(encoding="utf-8"))
                    return self.registry
                except Exception:
                    pass
            return {}

    def set_registry_url(self, url: str) -> None:
        """Override registry URL (for custom stores)."""
        if url and isinstance(url, str):
            self.registry_url = url

    def get_default_agent_id(self) -> Optional[str]:
        if not self.registry:
            self.fetch_registry()
        return self.registry.get("default_agent")

    def list_agents_for_ui(self) -> List[Dict[str, Any]]:
        if not self.registry:
            self.fetch_registry()
        agents = self.registry.get("agents", {})
        items: List[Dict[str, Any]] = []
        for agent_id, info in agents.items():
            items.append(
                {
                    "id": agent_id,
                    "name": info.get("name", agent_id),
                    "description": info.get("description", ""),
                    "installed": self.is_installed(agent_id),
                    "enabled": self.is_enabled(agent_id),
                }
            )
        return items

    # -----------------
    # Install management
    # -----------------
    def _agent_info(self, agent_id: str) -> Dict[str, Any]:
        if not self.registry:
            self.fetch_registry()
        agents = self.registry.get("agents", {})
        return agents.get(agent_id, {})


    def _raw_url(self, repo_url: str, path: str, ref: str = "main") -> str:
        try:
            parts = repo_url.rstrip("/").split("/")
            owner, repo = parts[-2], parts[-1]
        except Exception:
            owner, repo = "decyphertek-io", "agent-store"
        p = path.strip("/")
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{p}"

    def is_installed(self, agent_id: str) -> bool:
        info = self._agent_info(agent_id)
        folder_path = info.get("folder_path", f"{agent_id}/")
        # Install root is always ./store/agent
        dest_dir = self.local_store_root / Path(folder_path).name
        return dest_dir.exists() and any(dest_dir.iterdir())

    def install_agent(self, agent_id: str) -> Dict[str, Any]:
        info = self._agent_info(agent_id)
        if not info:
            return {"success": False, "error": f"Unknown agent: {agent_id}"}

        repo_url = info.get("repo_url", "https://github.com/decyphertek-io/agent-store")
        folder_path = info.get("folder_path", f"{agent_id}/")
        contents_url = self._contents_api_url(repo_url, folder_path)
        
        # Install under ~/.decyphertek-ai/store/agent/
        dest_root = self.local_store_root
        dest_root.mkdir(parents=True, exist_ok=True)
        dest_dir = dest_root / Path(folder_path).name
        dest_dir.mkdir(parents=True, exist_ok=True)

        try:
            # List directory items via GitHub Contents API
            with urllib.request.urlopen(contents_url, timeout=20) as resp:
                listing = json.loads(resp.read().decode("utf-8"))
            if isinstance(listing, dict) and listing.get("message"):
                raise RuntimeError(listing.get("message"))
            self._download_contents_recursive(repo_url, folder_path, dest_dir)

            # Use Poetry to manage dependencies
            try:
                print(f"[StoreManager] Setting up Poetry environment for agent '{agent_id}'...")
                
                # Check if requirements.txt exists (convert to Poetry if needed)
                req = dest_dir / "requirements.txt"
                pyproject = dest_dir / "pyproject.toml"
                
                if req.exists() and not pyproject.exists():
                    print(f"[StoreManager] Converting requirements.txt to Poetry format...")
                    # Create basic pyproject.toml
                    pyproject_content = f"""[tool.poetry]
name = "{agent_id}"
version = "1.0.0"
description = "Agent: {agent_id}"
authors = ["DecypherTek <decyphertek@proton.me>"]

[tool.poetry.dependencies]
python = "^3.10"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
                    pyproject.write_text(pyproject_content)
                    print(f"[StoreManager] Created pyproject.toml")
                
                # Use bash script to set up Poetry environment (same approach as launch.sh)
                print(f"[StoreManager] Setting up Poetry environment for agent '{agent_id}'...")
                script_path = Path(__file__).resolve().parents[2] / "scripts" / "store-manager.sh"
                
                result = subprocess.run(
                    [str(script_path), str(dest_dir)],
                    check=False,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"[StoreManager] Poetry install output:")
                    print(f"  STDOUT: {result.stdout}")
                    print(f"  STDERR: {result.stderr}")
                
                if result.returncode == 0:
                    print(f"[StoreManager] ✅ Poetry environment set up successfully for agent '{agent_id}'")
                    # Verify .venv exists
                    venv_dir = dest_dir / ".venv"
                    if venv_dir.exists():
                        print(f"[StoreManager] ✅ .venv directory created at {venv_dir}")
                    else:
                        print(f"[StoreManager] ⚠️ .venv not found, Poetry may be using global cache")
                else:
                    print(f"[StoreManager] ⚠️ Poetry install had issues:")
                    print(f"[StoreManager] STDERR: {result.stderr}")
                    if result.stdout:
                        print(f"[StoreManager] STDOUT: {result.stdout}")
                    
            except Exception as ve:
                print(f"[StoreManager] ❌ Poetry setup error for agent '{agent_id}': {ve}")
                import traceback
                traceback.print_exc()

            # Enable by default if requested
            enable_by_default = info.get("enable_by_default", False)
            
            # Mark installed in local cache for chat to detect
            self._write_agent_cache_entry(agent_id, installed=True, enabled=enable_by_default)
            
            # Also set enabled state
            if enable_by_default:
                self.enabled_state[agent_id] = True
                self._save_enabled_state()
                print(f"[StoreManager] ✅ Agent '{agent_id}' enabled by default")

            return {"success": True, "message": f"Installed '{agent_id}' to ~/.decyphertek-ai/store/agent/{agent_id}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def install_mcp_server(self, server_id: str) -> Dict[str, Any]:
        """Install an MCP server from the registry."""
        if not self.mcp_registry:
            self.fetch_mcp_registry()
        
        servers = self.mcp_registry.get("servers", {})
        info = servers.get(server_id)
        if not info:
            return {"success": False, "error": f"Unknown MCP server: {server_id}"}

        repo_url = info.get("repo_url", "https://github.com/decyphertek-io/mcp-store")
        folder_path = info.get("folder_path", f"servers/{server_id}/")
        contents_url = self._contents_api_url(repo_url, folder_path)
        
        # Install under ./store/mcp
        dest_root = self.mcp_store_root
        dest_root.mkdir(parents=True, exist_ok=True)
        dest_dir = dest_root / server_id
        dest_dir.mkdir(parents=True, exist_ok=True)

        try:
            # List directory items via GitHub Contents API
            with urllib.request.urlopen(contents_url, timeout=20) as resp:
                listing = json.loads(resp.read().decode("utf-8"))
            if isinstance(listing, dict) and listing.get("message"):
                raise RuntimeError(listing.get("message"))
            self._download_contents_recursive(repo_url, folder_path, dest_dir)

            # Use Poetry to manage dependencies
            try:
                print(f"[StoreManager] Setting up Poetry environment for MCP server '{server_id}'...")
                
                # Check if requirements.txt exists (convert to Poetry if needed)
                req = dest_dir / "requirements.txt"
                pyproject = dest_dir / "pyproject.toml"
                
                if req.exists() and not pyproject.exists():
                    print(f"[StoreManager] Converting requirements.txt to Poetry format...")
                    # Parse requirements.txt
                    requirements = []
                    for line in req.read_text().splitlines():
                        line = line.strip()
                        if line and not line.startswith('#'):
                            requirements.append(line)
                    
                    # Build dependencies section
                    deps_lines = ['python = "^3.10"']
                    for req_line in requirements:
                        # Convert pip format to poetry format
                        # e.g., "duckduckgo-search>=8.1.1" -> 'duckduckgo-search = ">=8.1.1"'
                        if '>=' in req_line:
                            pkg, ver = req_line.split('>=')
                            deps_lines.append(f'{pkg.strip()} = ">={ver.strip()}"')
                        elif '==' in req_line:
                            pkg, ver = req_line.split('==')
                            deps_lines.append(f'{pkg.strip()} = "{ver.strip()}"')
                        else:
                            deps_lines.append(f'{req_line} = "*"')
                    
                    deps_section = '\n'.join(deps_lines)
                    
                    # Create pyproject.toml with actual dependencies
                    pyproject_content = f"""[tool.poetry]
name = "mcp-{server_id}"
version = "1.0.0"
description = "MCP Server: {server_id}"
authors = ["DecypherTek <decyphertek@proton.me>"]

[tool.poetry.dependencies]
{deps_section}

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
                    pyproject.write_text(pyproject_content)
                    print(f"[StoreManager] Created pyproject.toml with dependencies from requirements.txt")
                
                # Use bash script to set up Poetry environment (same approach as launch.sh)
                print(f"[StoreManager] Setting up Poetry environment for MCP server '{server_id}'...")
                script_path = Path(__file__).resolve().parents[2] / "scripts" / "store-manager.sh"
                
                result = subprocess.run(
                    [str(script_path), str(dest_dir)],
                    check=False,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"[StoreManager] Poetry install output:")
                    print(f"  STDOUT: {result.stdout}")
                    print(f"  STDERR: {result.stderr}")
                
                if result.returncode == 0:
                    print(f"[StoreManager] ✅ Poetry environment set up successfully for MCP '{server_id}'")
                    # Verify .venv exists
                    venv_dir = dest_dir / ".venv"
                    if venv_dir.exists():
                        print(f"[StoreManager] ✅ .venv directory created at {venv_dir}")
                        
                        # Verify key packages if this is web-search
                        if server_id == "web-search":
                            poetry_show = subprocess.run(
                                ["poetry", "show"],
                                cwd=str(dest_dir),
                                check=False,
                                capture_output=True,
                                text=True
                            )
                            if poetry_show.returncode == 0:
                                installed = poetry_show.stdout.lower()
                                if "duckduckgo" in installed:
                                    print(f"[StoreManager] ✅ Verified: duckduckgo-search")
                                if "requests" in installed:
                                    print(f"[StoreManager] ✅ Verified: requests")
                                if "mcp" in installed:
                                    print(f"[StoreManager] ✅ Verified: mcp")
                    else:
                        print(f"[StoreManager] ⚠️ .venv not found, Poetry may be using global cache")
                else:
                    print(f"[StoreManager] ⚠️ Poetry install had issues:")
                    print(f"[StoreManager] STDERR: {result.stderr}")
                    if result.stdout:
                        print(f"[StoreManager] STDOUT: {result.stdout}")
                    
            except Exception as ve:
                print(f"[StoreManager] ❌ Poetry setup error for MCP '{server_id}': {ve}")
                import traceback
                traceback.print_exc()

            # Enable by default if specified
            enable_by_default = info.get("enable_by_default", False)
            
            # Mark installed in local cache
            self._write_mcp_cache_entry(server_id, installed=True, enabled=enable_by_default)
            
            # Also set enabled state
            if enable_by_default:
                self.mcp_enabled_state[server_id] = True
                self._save_mcp_enabled_state()
                print(f"[StoreManager] ✅ MCP server '{server_id}' enabled by default")

            return {"success": True, "message": f"Installed MCP server '{server_id}'"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_mcp_enabled(self, server_id: str, enabled: bool) -> None:
        """Set MCP server enabled state."""
        self.mcp_enabled_state[server_id] = enabled
        self._save_mcp_enabled_state()
    
    def is_mcp_enabled(self, server_id: str) -> bool:
        """Check if MCP server is enabled."""
        return self.mcp_enabled_state.get(server_id, False)
    
    def _save_mcp_enabled_state(self) -> None:
        try:
            self.mcp_enabled_state_path.parent.mkdir(parents=True, exist_ok=True)
            self.mcp_enabled_state_path.write_text(json.dumps(self.mcp_enabled_state, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[StoreManager] MCP enabled state save error: {e}")
    
    def _write_mcp_cache_entry(self, server_id: str, installed: bool = None, enabled: bool = None) -> None:
        """Write MCP cache entry."""
        try:
            cache_path = self.mcp_store_root / "cache.json"
            if cache_path.exists():
                cache_data = json.loads(cache_path.read_text(encoding="utf-8"))
            else:
                cache_data = {}
            
            if server_id not in cache_data:
                cache_data[server_id] = {}
            
            if installed is not None:
                cache_data[server_id]["installed"] = installed
            if enabled is not None:
                cache_data[server_id]["enabled"] = enabled
            
            cache_path.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[StoreManager] MCP cache write error: {e}")
    
    def reinstall_mcp_server(self, server_id: str) -> Dict[str, Any]:
        """Reinstall an MCP server (useful for fixing broken installations)."""
        try:
            # Check if server exists in registry first
            if not self.mcp_registry:
                self.fetch_mcp_registry()
            
            servers = self.mcp_registry.get("servers", {})
            if server_id not in servers:
                available_servers = list(servers.keys())
                return {
                    "success": False, 
                    "error": f"MCP Server '{server_id}' not found in registry",
                    "details": f"Available servers: {', '.join(available_servers) if available_servers else 'None'}"
                }
            
            # Remove existing installation (including .venv)
            server_dir = self.mcp_store_root / server_id
            removed_files = []
            if server_dir.exists():
                import shutil
                # List files before removal for feedback
                removed_files = [f.name for f in server_dir.iterdir() if f.is_file()]
                # Also remove .venv if it exists
                venv_dir = server_dir / ".venv"
                if venv_dir.exists():
                    removed_files.append(".venv")
                shutil.rmtree(server_dir)
                print(f"[StoreManager] Removed existing {server_id} installation (including .venv)")
            
            # Reinstall
            install_result = self.install_mcp_server(server_id)
            
            if install_result.get("success"):
                # Check what was actually installed
                installed_files = []
                if server_dir.exists():
                    installed_files = [f.name for f in server_dir.iterdir() if f.is_file()]
                # Verify venv rebuilt
                venv_dir = server_dir / ".venv"
                venv_rebuilt = venv_dir.exists()
                
                # Find the actual script file for feedback
                script_path = None
                possible_names = [
                    f"{server_id}.py",  # web-search.py
                    "main.py",          # main.py
                    "web.py",           # web.py (for web-search)
                    "server.py",        # server.py
                    "app.py"            # app.py
                ]
                
                for script_name in possible_names:
                    potential_path = server_dir / script_name
                    if potential_path.exists():
                        script_path = potential_path
                        break
                
                return {
                    "success": True,
                    "message": (
                        f"MCP Server '{server_id}' reinstalled successfully. "
                        f"Old .venv deleted and new .venv {'created' if venv_rebuilt else 'not found'}"
                    ),
                    "details": {
                        "removed_files": removed_files,
                        "installed_files": installed_files,
                        "server_id": server_id,
                        "script_path": str(script_path) if script_path else "Script not found",
                        "venv_rebuilt": venv_rebuilt,
                        "status": "Ready for use"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": install_result.get("error", "Unknown installation error"),
                    "details": f"Failed to reinstall MCP server '{server_id}'"
                }
                
        except Exception as e:
            return {
                "success": False, 
                "error": str(e),
                "details": f"Exception during reinstall of MCP server '{server_id}'"
            }


    # --------------------
    # Enabled state persist
    # --------------------
    def _load_enabled_state(self) -> Dict[str, bool]:
        try:
            self.enabled_state_path.parent.mkdir(parents=True, exist_ok=True)
            if self.enabled_state_path.exists():
                return json.loads(self.enabled_state_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[StoreManager] Enabled state load error: {e}")
        return {}
    
    def _load_mcp_enabled_state(self) -> Dict[str, bool]:
        try:
            self.mcp_enabled_state_path.parent.mkdir(parents=True, exist_ok=True)
            if self.mcp_enabled_state_path.exists():
                return json.loads(self.mcp_enabled_state_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[StoreManager] MCP enabled state load error: {e}")
        return {}

    def _save_enabled_state(self) -> None:
        try:
            self.enabled_state_path.parent.mkdir(parents=True, exist_ok=True)
            self.enabled_state_path.write_text(json.dumps(self.enabled_state, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[StoreManager] Enabled state save error: {e}")

    def is_enabled(self, agent_id: str) -> bool:
        return bool(self.enabled_state.get(agent_id, False))

    def set_enabled(self, agent_id: str, enabled: bool) -> None:
        self.enabled_state[agent_id] = bool(enabled)
        self._save_enabled_state()
        # Mirror enabled state into src/store/agent/cache.json for UI/chat discovery
        self._write_agent_cache_entry(agent_id, enabled=bool(enabled))

    # ----------------
    # Dynamic loading
    # ----------------
    def load_agent(self, agent_id: Optional[str] = None) -> Any:
        if not self.registry:
            self.fetch_registry()
        agent_id = agent_id or self.get_default_agent_id()
        if not agent_id:
            raise RuntimeError("No agent id provided and no default configured")

        info = self._agent_info(agent_id)
        # Module path under ./store/agent/<module_path>
        module_rel = info.get("module_path") or f"{agent_id}/{agent_id}.py"
        mod_path = self.local_store_root / module_rel
        if not mod_path.exists():
            raise FileNotFoundError(f"Agent module not found at {mod_path}")

        spec = importlib.util.spec_from_file_location(agent_id, str(mod_path))
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        class_name = info.get("class_name", "AdminotaurAgent")
        if not hasattr(module, class_name):
            raise AttributeError(f"Class {class_name} not found in {mod_path}")

        AgentClass = getattr(module, class_name)
        return AgentClass  # caller may instantiate with its own parameters

    # --------------------
    # Agent cache for UI/chat
    # --------------------
    def _write_agent_cache_entry(self, aid: str, installed: bool | None = None, enabled: bool | None = None) -> None:
        """Write to ~/.decyphertek-ai/store/agent/cache.json"""
        cache_path = self.local_store_root / "cache.json"
        try:
            self.local_store_root.mkdir(parents=True, exist_ok=True)
            data: Dict[str, Any] = {}
            if cache_path.exists():
                data = json.loads(cache_path.read_text(encoding="utf-8"))
            entry = data.get(aid, {})
            if installed is not None:
                entry["installed"] = bool(installed)
            if enabled is not None:
                entry["enabled"] = bool(enabled)
            data[aid] = entry
            cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[StoreManager] Agent cache write error: {e}")

    # -----------------
    # MCP Store methods
    # -----------------
    def set_mcp_registry_url(self, url: str) -> None:
        if url and isinstance(url, str):
            self.mcp_registry_url = url

    def fetch_mcp_registry(self) -> Dict[str, Any]:
        try:
            with urllib.request.urlopen(self.mcp_registry_url, timeout=20) as resp:
                data = resp.read()
            reg = json.loads(data.decode("utf-8"))
            if not isinstance(reg, dict) or "servers" not in reg:
                raise ValueError("Invalid MCP skills registry")
            self.mcp_registry = reg
            return reg
        except Exception as e:
            print(f"[StoreManager] MCP registry fetch error: {e}")
            return {}

    def is_mcp_installed(self, server_id: str) -> bool:
        dest_dir = self.mcp_store_root / server_id
        return dest_dir.exists() and any(dest_dir.iterdir())

    def is_mcp_enabled(self, server_id: str) -> bool:
        return bool(self.mcp_enabled_state.get(server_id, False))

    def set_mcp_enabled(self, server_id: str, enabled: bool) -> None:
        self.mcp_enabled_state[server_id] = bool(enabled)
        self._save_enabled_state_generic(self.mcp_enabled_state_path, self.mcp_enabled_state)


    def _start_agent_background_sync(self) -> None:
        """Auto-install and enable default agents."""
        def _bg():
            try:
                print("[StoreManager] Fetching agent registry...")
                registry = self.fetch_registry()
                
                # Save registry locally
                registry_path = self.local_store_root / "personality.json"
                registry_path.parent.mkdir(parents=True, exist_ok=True)
                registry_path.write_text(json.dumps(registry, indent=2))
                print(f"[StoreManager] Saved personality.json to {registry_path}")
                
                agents = (registry.get("agents") or {}) if isinstance(registry, dict) else {}
                for aid, info in agents.items():
                    if info.get("enable_by_default", False):
                        try:
                            print(f"[StoreManager] Checking agent '{aid}' (enable_by_default: true)")
                            if not self.is_installed(aid):
                                print(f"[StoreManager] Installing agent '{aid}'...")
                                res = self.install_agent(aid)
                                if not res.get("success"):
                                    print(f"[StoreManager] Failed to install '{aid}': {res.get('error')}")
                                    continue
                                print(f"[StoreManager] ✅ Agent '{aid}' installed and enabled")
                            else:
                                print(f"[StoreManager] Agent '{aid}' already installed")
                                # Ensure it's enabled
                                if not self.is_enabled(aid):
                                    self.set_enabled(aid, True)
                                    print(f"[StoreManager] ✅ Agent '{aid}' enabled")
                        except Exception as e:
                            print(f"[StoreManager] Error with agent '{aid}': {e}")
                            continue
            except Exception as e:
                print(f"[StoreManager] Agent sync error: {e}")

        threading.Thread(target=_bg, daemon=True).start()

    def _start_mcp_background_sync(self) -> None:
        """Auto-install and enable default MCP servers."""
        def _bg():
            try:
                print("[StoreManager] Fetching MCP registry...")
                registry = self.fetch_mcp_registry()
                
                # Save registry locally
                registry_path = self.mcp_store_root / "skills.json"
                registry_path.parent.mkdir(parents=True, exist_ok=True)
                registry_path.write_text(json.dumps(registry, indent=2))
                print(f"[StoreManager] Saved skills.json to {registry_path}")
                
                servers = (registry.get("servers") or {}) if isinstance(registry, dict) else {}
                for sid, info in servers.items():
                    if info.get("enable_by_default", False):
                        try:
                            print(f"[StoreManager] Checking MCP server '{sid}' (enable_by_default: true)")
                            if not self.is_mcp_installed(sid):
                                print(f"[StoreManager] Installing MCP server '{sid}'...")
                                res = self.install_mcp_server(sid)
                                if not res.get("success"):
                                    print(f"[StoreManager] Failed to install '{sid}': {res.get('error')}")
                                    continue
                                print(f"[StoreManager] ✅ MCP server '{sid}' installed and enabled")
                            else:
                                print(f"[StoreManager] MCP server '{sid}' already installed")
                                # Ensure it's enabled
                                if not self.is_mcp_enabled(sid):
                                    self.set_mcp_enabled(sid, True)
                                    print(f"[StoreManager] ✅ MCP server '{sid}' enabled")
                        except Exception as e:
                            print(f"[StoreManager] Error with MCP server '{sid}': {e}")
                            continue
            except Exception as e:
                print(f"[StoreManager] MCP sync error: {e}")

        threading.Thread(target=_bg, daemon=True).start()

    def test_mcp_server(self, server_id: str) -> Dict[str, Any]:
        """Test an MCP server installation status (diagnostic only)."""
        try:
            # Check if server is installed
            server_dir = self.mcp_store_root / server_id
            
            # Find the actual script file
            script_path = None
            possible_names = [
                f"{server_id}.py",  # web-search.py
                "main.py",          # main.py
                "web.py",           # web.py (for web-search)
                "server.py",        # server.py
                "app.py"            # app.py
            ]
            
            for script_name in possible_names:
                potential_path = server_dir / script_name
                if potential_path.exists():
                    script_path = potential_path
                    break
            
            if not script_path:
                available_files = [f.name for f in server_dir.iterdir() if f.is_file() and f.suffix == '.py']
                return {
                    "success": False,
                    "error": f"MCP Server script not found",
                    "details": {
                        "searched_for": possible_names,
                        "available_py_files": available_files,
                        "server_dir": str(server_dir),
                        "status": "Installation incomplete"
                    }
                }
            
            # Check if server is enabled
            is_enabled = self.is_mcp_enabled(server_id)
            
            # Get server info from registry
            server_info = {}
            if self.mcp_registry:
                server_info = self.mcp_registry.get("servers", {}).get(server_id, {})
            
            # Check if venv exists and is functional
            venv_dir = server_dir / ".venv"
            venv_python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            venv_exists = venv_dir.exists()
            venv_functional = venv_python.exists()
            
            # Check if pyproject.toml and poetry.lock exist
            pyproject_exists = (server_dir / "pyproject.toml").exists()
            poetry_lock_exists = (server_dir / "poetry.lock").exists()
            
            # Determine status
            if not venv_exists:
                status = "❌ No .venv - Poetry install failed"
                ready = False
            elif not venv_functional:
                status = "⚠️ .venv exists but Python not found"
                ready = False
            else:
                status = "✅ Ready (venv configured)"
                ready = True
            
            return {
                "success": True,
                "message": f"MCP Server {server_id} is installed",
                "details": {
                    "server_id": server_id,
                    "script_path": str(script_path),
                    "enabled": is_enabled,
                    "venv_exists": venv_exists,
                    "venv_functional": venv_functional,
                    "venv_python": str(venv_python) if venv_functional else "Not found",
                    "pyproject_exists": pyproject_exists,
                    "poetry_lock_exists": poetry_lock_exists,
                    "name": server_info.get("name", server_id),
                    "status": status,
                    "ready": ready
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"MCP Server check error: {e}",
                "details": {
                    "server_id": server_id,
                    "exception": str(e)
                }
            }

    # ------------------
    # Shared utilities
    # ------------------
    def _load_enabled_state_generic(self, path: Path) -> Dict[str, bool]:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_enabled_state_generic(self, path: Path, data: Dict[str, bool]) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _contents_api_url(self, repo_url: str, folder_path: str, ref: str = "main") -> str:
        try:
            parts = repo_url.rstrip("/").split("/")
            owner, repo = parts[-2], parts[-1]
        except Exception:
            owner, repo = "decyphertek-io", "mcp-store"
        folder = folder_path.strip("/")
        return f"https://api.github.com/repos/{owner}/{repo}/contents/{folder}?ref={ref}"

    def _download_contents_recursive(self, repo_url: str, folder_path: str, dest_dir: Path, ref: str = "main") -> None:
        dest_dir.mkdir(parents=True, exist_ok=True)
        url = self._contents_api_url(repo_url, folder_path, ref)
        with urllib.request.urlopen(url, timeout=20) as resp:
            items = json.loads(resp.read().decode("utf-8"))
        if isinstance(items, dict) and items.get("message"):
            raise RuntimeError(items.get("message"))
        for item in items:
            itype = item.get("type")
            name = item.get("name")
            path = item.get("path")
            download_url = item.get("download_url")
            if itype == "file" and download_url:
                target = dest_dir / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with urllib.request.urlopen(download_url, timeout=20) as fsrc, open(target, "wb") as fdst:
                    fdst.write(fsrc.read())
            elif itype == "dir":
                self._download_contents_recursive(repo_url, path, dest_dir / name, ref)

    # ---------------
    # App Store methods
    # ---------------
    def set_app_registry_url(self, url: str) -> None:
        if url and isinstance(url, str):
            self.app_registry_url = url

    def fetch_app_registry(self) -> Dict[str, Any]:
        try:
            with urllib.request.urlopen(self.app_registry_url, timeout=20) as resp:
                data = resp.read()
            reg = json.loads(data.decode("utf-8"))
            if not isinstance(reg, dict) or "apps" not in reg:
                raise ValueError("Invalid Apps registry")
            self.app_registry = reg
            return reg
        except Exception as e:
            print(f"[StoreManager] App registry fetch error: {e}")
            return {}

    def is_app_installed(self, app_id: str) -> bool:
        dest_dir = self.app_local_root / app_id
        return dest_dir.exists() and any(dest_dir.iterdir())

    def is_app_enabled(self, app_id: str) -> bool:
        return bool(self.app_enabled_state.get(app_id, False))

    def set_app_enabled(self, app_id: str, enabled: bool) -> None:
        self.app_enabled_state[app_id] = bool(enabled)
        self._save_enabled_state_generic(self.app_enabled_state_path, self.app_enabled_state)

    def install_app(self, app_id: str) -> Dict[str, Any]:
        """Download, install, and setup a Flet app from the app store"""
        print(f"[StoreManager] Installing app: {app_id}")
        if not self.app_registry:
            print(f"[StoreManager] Fetching app registry from: {self.app_registry_url}")
            self.fetch_app_registry()
        
        print(f"[StoreManager] App registry: {self.app_registry}")
        info = self.app_registry.get("apps", {}).get(app_id)
        print(f"[StoreManager] App info for {app_id}: {info}")
        
        if not info:
            return {"success": False, "error": f"Unknown app: {app_id}"}
        repo_url = info.get("repo_url")
        folder_path = info.get("folder_path")
        if not repo_url or not folder_path:
            return {"success": False, "error": "Missing repo_url or folder_path"}

        dest_root = self.app_local_root
        dest_root.mkdir(parents=True, exist_ok=True)
        dest_dir = dest_root / app_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            print(f"[StoreManager] Downloading {app_id} from {repo_url}/{folder_path}")
            self._download_contents_recursive(repo_url, folder_path, dest_dir)
            
            # Setup environment and dependencies
            print(f"[StoreManager] Setting up environment for {app_id}")
            setup_result = self._setup_app_environment(app_id, dest_dir)
            if not setup_result["success"]:
                return setup_result
            
            # Mark app as ready to run
            self._mark_app_ready(app_id, dest_dir)
            
            if info.get("enable_by_default", False):
                self.set_app_enabled(app_id, True)
                
            return {
                "success": True, 
                "message": f"Installed and setup '{app_id}' successfully",
                "app_path": str(dest_dir),
                "main_script": setup_result.get("main_script", ""),
                "ready_to_run": True
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _setup_app_environment(self, app_id: str, dest_dir: Path) -> Dict[str, Any]:
        """Setup the app environment including dependencies"""
        try:
            # For Chaquopy compatibility, install directly to system Python
            # instead of creating virtual environments
            req_file = dest_dir / "requirements.txt"
            if req_file.exists():
                print(f"[StoreManager] Installing requirements for {app_id}")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                    cwd=str(dest_dir),
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"[StoreManager] Requirements install warning for {app_id}: {result.stderr}")
            
            # Find the main script
            main_script = self._find_main_script(dest_dir)
            if not main_script:
                return {"success": False, "error": "No main.py or main script found"}
            
            return {
                "success": True,
                "main_script": str(main_script),
                "message": f"Environment setup complete for {app_id}"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Environment setup failed: {e}"}
    
    def _find_main_script(self, dest_dir: Path) -> Path | None:
        """Find the main script for the Flet app"""
        # Common patterns for Flet app main scripts
        possible_paths = [
            dest_dir / "src" / "main.py",
            dest_dir / "main.py",
            dest_dir / "app.py",
            dest_dir / "src" / "app.py"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def _mark_app_ready(self, app_id: str, dest_dir: Path) -> None:
        """Mark an app as ready to run by creating a ready state file"""
        try:
            ready_file = dest_dir / ".ready"
            ready_file.write_text(f"ready_at={int(time.time())}\napp_id={app_id}\npath={dest_dir}")
            print(f"[StoreManager] Marked {app_id} as ready to run")
        except Exception as e:
            print(f"[StoreManager] Warning: Could not mark {app_id} as ready: {e}")
    
    def is_app_ready(self, app_id: str) -> bool:
        """Check if an app is ready to run"""
        try:
            app_dir = self.app_local_root / app_id
            ready_file = app_dir / ".ready"
            return ready_file.exists()
        except:
            return False
    
    def get_app_launch_info(self, app_id: str) -> Dict[str, Any]:
        """Get information needed to launch an app"""
        try:
            app_dir = self.app_local_root / app_id
            if not app_dir.exists():
                return {"success": False, "error": f"App {app_id} not installed"}
            
            if not self.is_app_ready(app_id):
                return {"success": False, "error": f"App {app_id} not ready to run"}
            
            main_script = self._find_main_script(app_dir)
            if not main_script:
                return {"success": False, "error": f"No main script found for {app_id}"}
            
            return {
                "success": True,
                "app_id": app_id,
                "app_dir": str(app_dir),
                "main_script": str(main_script),
                "ready": True
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


class DecypherTekAgent:
    """
    Default lightweight agent that uses StoreManager to ensure the default
    personality (Adminotaur) is installed and enabled, then delegates chat to it.
    """

    def __init__(self, ai_client, provider: str = "openrouter", enable_tools: bool = False, verbose: bool = True, doc_manager=None, page=None):
        self.ai_client = ai_client
        self.provider = provider
        self.verbose = verbose
        self.doc_manager = doc_manager
        # Expose page for personalities expecting main_class.page
        self.page = page

        self._store = StoreManager()
        self.personality = None

        # Bootstrap store and choose active personality
        self._store.fetch_registry()

        # Prefer first enabled agent; otherwise ensure default installed/enabled
        enabled_ids = [aid for aid, enabled in self._store.enabled_state.items() if enabled]
        active_id = enabled_ids[0] if enabled_ids else self._store.get_default_agent_id()

        if active_id and not self._store.is_installed(active_id):
            install_res = self._store.install_agent(active_id)
            if self.verbose:
                print(f"[DecypherTekAgent] Install '{active_id}': {install_res}")
        if active_id and not self._store.is_enabled(active_id):
            self._store.set_enabled(active_id, True)

        # Load class and instantiate selected personality
        try:
            AgentClass = self._store.load_agent(active_id)
            # Prefer positional main_class to match AdminotaurAgent signature
            try:
                self.personality = AgentClass(self)
            except TypeError:
                # Fallbacks for alternative constructors
                try:
                    self.personality = AgentClass(main_class=self)
                except Exception:
                    try:
                        self.personality = AgentClass(ai_client=self.ai_client, provider=self.provider, doc_manager=self.doc_manager)
                    except Exception:
                        self.personality = AgentClass()

            # Propagate useful references if personality supports them
            for attr, val in ("ai_client", self.ai_client), ("provider", self.provider), ("doc_manager", self.doc_manager):
                if hasattr(self.personality, attr):
                    setattr(self.personality, attr, val)
            if self.verbose:
                print(f"[DecypherTekAgent] Personality '{active_id}' loaded and ready")
        except Exception as e:
            print(f"[DecypherTekAgent] Failed to load personality: {e}")

    async def chat(self, message: str, context: Optional[str] = None) -> str:
        if self.personality and hasattr(self.personality, "chat"):
            return await self.personality.chat(message, context=context)
        # Fallback minimal behavior
        return "Personality not available yet. Please try again after installation completes."


