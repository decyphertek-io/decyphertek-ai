
from typing import List, Dict, Any, Optional
import subprocess
import sys
import os
import io
import json
from pathlib import Path
from urllib.parse import urlparse
import zipfile
import tempfile
import urllib.request

class AdminotaurAgent:
    """
    The core agent for interacting with the DecypherTek AI environment.
    It can discover and launch Flet applications from the agent-store.
    """
    def __init__(self, main_class: Any):
        """
        Initializes the Adminotaur agent.
        :param main_class: A reference to the main application class that holds the UI (page) and other state.
        """
        self.main_class = main_class
        self.page = getattr(main_class, "page", None)

        # Flet app discovery (existing behavior)
        self.app_store_path = Path("./apps")  # Assuming apps are in an 'apps' directory relative to the main app
        self.available_apps = self._discover_flet_apps()

        # MCP store paths and settings
        self.project_root = Path(__file__).resolve().parents[2]
        self.mcp_root = self.project_root / "mcp-store"
        self.mcp_servers_dir = self.mcp_root / "servers"
        self.enabled_state_path = Path.home() / ".decyphertek-ai" / "mcp-enabled.json"
        self.registry_url = (
            "https://raw.githubusercontent.com/decyphertek-io/mcp-store/main/mcp-skills.json"
        )
        self.registry_cache: Dict[str, Any] = {}
        self.enabled_state: Dict[str, bool] = self._load_enabled_state()

        print(
            f"[Adminotaur] Initialized. Discovered apps: {list(self.available_apps.keys())}. MCP root: {self.mcp_root}"
        )

    def _discover_flet_apps(self) -> Dict[str, Dict]:
        """Discover available Flet applications from the app store"""
        apps = {}
        if not self.app_store_path.exists():
            print(f"[Adminotaur] App store not found at {self.app_store_path}")
            return apps
        
        for app_dir in self.app_store_path.iterdir():
            if app_dir.is_dir():
                app_name = app_dir.name
                main_py = app_dir / "src" / "main.py"
                
                if main_py.exists():
                    apps[app_name.lower()] = {
                        'name': app_name,
                        'path': app_dir,
                        'main_file': main_py,
                    }
        return apps

    # =========================
    # MCP Registry & Installer
    # =========================

    def fetch_registry(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Fetch MCP registry JSON (minimal, no extra deps). Caches in memory."""
        registry_url = url or self.registry_url
        try:
            print(f"[Adminotaur:MCP] Fetching registry from: {registry_url}")
            with urllib.request.urlopen(registry_url, timeout=15) as resp:
                data = resp.read()
            registry = json.loads(data.decode("utf-8"))
            # Basic validation
            if not isinstance(registry, dict) or "servers" not in registry:
                raise ValueError("Invalid registry schema: missing 'servers'")
            self.registry_cache = registry
            return registry
        except Exception as e:
            print(f"[Adminotaur:MCP] Registry fetch error: {e}")
            # Fallback: try local registry if exists
            local_registry = self.mcp_root / "mcp-skills.json"
            if local_registry.exists():
                try:
                    registry = json.loads(local_registry.read_text(encoding="utf-8"))
                    self.registry_cache = registry
                    print("[Adminotaur:MCP] Loaded local registry fallback")
                    return registry
                except Exception as e2:
                    print(f"[Adminotaur:MCP] Local registry load error: {e2}")
            return {}

    def get_registry_servers(self) -> Dict[str, Dict[str, Any]]:
        """Return servers map from cached registry; fetch if empty."""
        if not self.registry_cache:
            self.fetch_registry()
        return self.registry_cache.get("servers", {})

    def get_install_path(self, server_id: str) -> Path:
        """Local installation path for a server."""
        return self.mcp_servers_dir / server_id

    def is_installed(self, server_id: str) -> bool:
        """Check if server folder exists locally."""
        return self.get_install_path(server_id).exists()

    def _load_enabled_state(self) -> Dict[str, bool]:
        try:
            self.enabled_state_path.parent.mkdir(parents=True, exist_ok=True)
            if self.enabled_state_path.exists():
                return json.loads(self.enabled_state_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[Adminotaur:MCP] Failed to load enabled state: {e}")
        return {}

    def _save_enabled_state(self) -> None:
        try:
            self.enabled_state_path.parent.mkdir(parents=True, exist_ok=True)
            self.enabled_state_path.write_text(json.dumps(self.enabled_state, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[Adminotaur:MCP] Failed to save enabled state: {e}")

    def is_enabled(self, server_id: str) -> bool:
        return bool(self.enabled_state.get(server_id, False))

    def set_enabled(self, server_id: str, enabled: bool) -> None:
        self.enabled_state[server_id] = bool(enabled)
        self._save_enabled_state()
        print(f"[Adminotaur:MCP] Server '{server_id}' enabled={enabled}")

    def install_server(self, server_id: str, registry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Install a server by downloading only its folder from the GitHub repo ZIP.
        Steps:
          1) Download repo ZIP (main branch)
          2) Extract only the specified server folder (servers/<server_id>/)
          3) Create venv inside that server folder (.venv)
          4) pip install -r requirements.txt (if present)
          5) Mark enabled by default
        Returns dict with success/message/error.
        """
        try:
            servers = registry.get("servers") if registry else self.get_registry_servers()
            if server_id not in servers:
                return {"success": False, "error": f"Unknown server_id: {server_id}"}

            server_info = servers[server_id]
            # Expected fields; keep minimal and robust
            repo_url = server_info.get("repo_url", "https://github.com/decyphertek-io/mcp-store")
            server_path = server_info.get("server_path", f"servers/{server_id}/")

            # Translate repo to codeload ZIP
            # e.g., https://codeload.github.com/decyphertek-io/mcp-store/zip/refs/heads/main
            try:
                parsed = urlparse(repo_url)
                parts = parsed.path.strip("/").split("/")
                owner, repo = parts[0], parts[1]
            except Exception:
                owner, repo = "decyphertek-io", "mcp-store"
            zip_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/main"

            print(f"[Adminotaur:MCP] Downloading ZIP from: {zip_url}")
            with urllib.request.urlopen(zip_url, timeout=30) as resp:
                zip_bytes = resp.read()

            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                # Find top-level folder name inside ZIP (e.g., mcp-store-main)
                top_prefix = None
                for n in zf.namelist():
                    if n.endswith("/") and n.count("/") == 1:
                        top_prefix = n
                        break
                if not top_prefix:
                    # Fallback: first entry's prefix
                    top_prefix = zf.namelist()[0].split("/")[0] + "/"

                target_prefix = top_prefix + server_path.strip("/") + "/"
                print(f"[Adminotaur:MCP] Extracting prefix: {target_prefix}")

                # Ensure destination
                dest_dir = self.get_install_path(server_id)
                if dest_dir.exists():
                    print(f"[Adminotaur:MCP] Removing existing install at {dest_dir}")
                    import shutil
                    shutil.rmtree(dest_dir)
                dest_dir.mkdir(parents=True, exist_ok=True)

                # Extract only files under target_prefix
                for member in zf.namelist():
                    if member.startswith(target_prefix) and not member.endswith("/"):
                        relative = member[len(target_prefix):]
                        out_path = dest_dir / relative
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(out_path, "wb") as dst:
                            dst.write(src.read())

            # Create venv
            venv_dir = dest_dir / ".venv"
            print(f"[Adminotaur:MCP] Creating venv at {venv_dir}")
            result = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], capture_output=True, text=True)
            if result.returncode != 0:
                return {"success": False, "error": f"venv failed: {result.stderr}"}

            # Determine venv python
            venv_python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

            # Install requirements if present
            req_path = dest_dir / "requirements.txt"
            if req_path.exists():
                print(f"[Adminotaur:MCP] Installing requirements from {req_path}")
                result = subprocess.run([str(venv_python), "-m", "pip", "install", "-r", str(req_path)], capture_output=True, text=True, cwd=str(dest_dir))
                if result.returncode != 0:
                    return {"success": False, "error": f"pip install failed: {result.stderr[:200]}"}
            else:
                print("[Adminotaur:MCP] No requirements.txt found; skipping pip install")

            # Enable by default
            self.set_enabled(server_id, True)

            return {"success": True, "message": f"Installed and enabled '{server_id}'"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # Convenience helpers for UI layer
    def mcp_list_for_ui(self) -> List[Dict[str, Any]]:
        """Return list suitable for UI: id, name, installed, enabled, description."""
        servers = self.get_registry_servers()
        items: List[Dict[str, Any]] = []
        for sid, info in servers.items():
            items.append({
                "id": sid,
                "name": info.get("name", sid),
                "description": info.get("description", ""),
                "installed": self.is_installed(sid),
                "enabled": self.is_enabled(sid),
            })
        return items

    async def chat(self, messages: List[Dict], user_message: str) -> str:
        """
        Main chat method for the Adminotaur agent.
        Determines if a tool needs to be used, like launching an app.
        """
        print("[Adminotaur] Thinking...")
        
        message_lower = user_message.lower()
        app_launch_keywords = ["run", "launch", "start", "open", "execute"]
        
        # Check for app launch intent
        triggered_keyword = next((word for word in app_launch_keywords if word in message_lower), None)
        
        if triggered_keyword:
            # Find which app is being requested
            app_to_launch = None
            for app_name in self.available_apps.keys():
                if app_name in message_lower:
                    app_to_launch = app_name
                    break
            
            if app_to_launch:
                print(f"[Adminotaur] Detected request to launch '{app_to_launch}'")
                # The main_class should have a generic launch method
                if hasattr(self.main_class, "launch_app_by_name"):
                    self.main_class.launch_app_by_name(app_to_launch)
                    return f"I have launched the {self.available_apps[app_to_launch]['name']} application for you."
                else:
                    return f"Sorry, I can't launch applications right now. The main application is missing the 'launch_app_by_name' method."
            
        # Default response if no specific action is taken
        return "I can help with launching applications. What would you like to do?"
