
"""
MCP Server manager for installing and running servers
"""

import importlib.util
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional

from .models import MCPServer
from .github_store import MCPGitHubStore
from utils.logger import setup_logger

logger = setup_logger()


class MCPServerManager:
    """Manages MCP server installation and execution"""
    
    def __init__(self, data_dir: str, store_url: str):
        """
        Initialize MCP server manager
        
        Args:
            data_dir: Application data directory
            store_url: GitHub store URL
        """
        self.data_dir = Path(data_dir)
        self.servers_dir = self.data_dir / "mcp_servers"
        self.cache_dir = self.data_dir / "mcp_cache"
        
        # Create directories
        self.servers_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize GitHub store
        self.github_store = MCPGitHubStore(store_url, str(self.cache_dir))
        
        # Load installed servers
        self.installed_servers: Dict[str, MCPServer] = {}
        self._load_installed_servers()
        
        logger.info("MCP Server Manager initialized")
    
    async def fetch_available_servers(self) -> List[MCPServer]:
        """
        Fetch available servers from GitHub store
        
        Returns:
            List of available MCP servers
        """
        servers = await self.github_store.fetch_index()
        
        # Update installation status
        for server in servers:
            if server.id in self.installed_servers:
                server.installed = True
                server.enabled = self.installed_servers[server.id].enabled
        
        return servers
    
    async def install_server(self, server: MCPServer) -> bool:
        """
        Install an MCP server
        
        Args:
            server: MCP server to install
            
        Returns:
            True if successful
        """
        try:
            # Download server code
            success = await self.github_store.download_server(server, self.servers_dir)
            
            if not success:
                return False
            
            # Install requirements (if any)
            if server.requirements:
                await self._install_requirements(server)
            
            # Mark as installed
            server.installed = True
            self.installed_servers[server.id] = server
            self._save_installed_servers()
            
            logger.info(f"Installed MCP server: {server.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error installing server {server.name}: {e}")
            return False
    
    async def uninstall_server(self, server_id: str) -> bool:
        """
        Uninstall an MCP server
        
        Args:
            server_id: Server ID to uninstall
            
        Returns:
            True if successful
        """
        try:
            if server_id not in self.installed_servers:
                return False
            
            # Remove server directory
            server_dir = self.servers_dir / server_id
            if server_dir.exists():
                import shutil
                shutil.rmtree(server_dir)
            
            # Remove from installed list
            del self.installed_servers[server_id]
            self._save_installed_servers()
            
            logger.info(f"Uninstalled MCP server: {server_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error uninstalling server {server_id}: {e}")
            return False
    
    def enable_server(self, server_id: str) -> bool:
        """
        Enable an installed server
        
        Args:
            server_id: Server ID to enable
            
        Returns:
            True if successful
        """
        if server_id in self.installed_servers:
            self.installed_servers[server_id].enabled = True
            self._save_installed_servers()
            logger.info(f"Enabled MCP server: {server_id}")
            return True
        return False
    
    def disable_server(self, server_id: str) -> bool:
        """
        Disable an installed server
        
        Args:
            server_id: Server ID to disable
            
        Returns:
            True if successful
        """
        if server_id in self.installed_servers:
            self.installed_servers[server_id].enabled = False
            self._save_installed_servers()
            logger.info(f"Disabled MCP server: {server_id}")
            return True
        return False
    
    def get_installed_servers(self) -> List[MCPServer]:
        """Get list of installed servers"""
        return list(self.installed_servers.values())
    
    def get_enabled_servers(self) -> List[MCPServer]:
        """Get list of enabled servers"""
        return [
            server for server in self.installed_servers.values()
            if server.enabled
        ]
    
    async def execute_server(
        self,
        server_id: str,
        method: str,
        params: Dict = None
    ) -> Optional[Dict]:
        """
        Execute a method on an MCP server
        
        Args:
            server_id: Server ID
            method: Method name to execute
            params: Method parameters
            
        Returns:
            Result dictionary or None
        """
        try:
            if server_id not in self.installed_servers:
                logger.error(f"Server {server_id} not installed")
                return None
            
            server = self.installed_servers[server_id]
            
            if not server.enabled:
                logger.error(f"Server {server_id} not enabled")
                return None
            
            # Get server Python file
            server_dir = self.servers_dir / server_id
            python_file = server_dir / Path(server.python_file).name
            
            if not python_file.exists():
                logger.error(f"Server file not found: {python_file}")
                return None
            
            # Dynamically load the module
            spec = importlib.util.spec_from_file_location(server_id, python_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the method to execute
            func = getattr(module, method, None)
            if not func or not callable(func):
                logger.error(f"Method '{method}' not found or not callable in {server_id}")
                return None
                
            logger.info(f"Executing {method} on server {server_id} with params: {params}")
            
            # Execute the method (handle both sync and async)
            if inspect.iscoroutinefunction(func):
                result = await func(params or {})
            else:
                result = func(params or {})
                
            return {
                "success": True,
                "server_id": server_id,
                "method": method,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error executing server method: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _install_requirements(self, server: MCPServer):
        """
        Install Python requirements for server
        
        Args:
            server: MCP server
        """
        try:
            if not server.requirements:
                return
            
            logger.info(f"Installing requirements for {server.name}")
            
            # On Android with Chaquopy, pip is available
            for requirement in server.requirements:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", requirement],
                    check=True,
                    capture_output=True
                )
            
            logger.info(f"Requirements installed for {server.name}")
            
        except Exception as e:
            logger.error(f"Error installing requirements: {e}")
            # Don't fail installation if requirements fail
    
    def _load_installed_servers(self):
        """Load installed servers from disk"""
        try:
            for server_dir in self.servers_dir.iterdir():
                if not server_dir.is_dir():
                    continue
                
                metadata_file = server_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        server_data = json.load(f)
                    
                    server = MCPServer.from_dict(server_data)
                    server.installed = True
                    self.installed_servers[server.id] = server
            
            logger.info(f"Loaded {len(self.installed_servers)} installed servers")
            
        except Exception as e:
            logger.error(f"Error loading installed servers: {e}")
    
    def _save_installed_servers(self):
        """Save installed servers list"""
        try:
            for server_id, server in self.installed_servers.items():
                server_dir = self.servers_dir / server_id
                metadata_file = server_dir / "metadata.json"
                
                with open(metadata_file, 'w') as f:
                    f.write(server.to_json())
            
        except Exception as e:
            logger.error(f"Error saving installed servers: {e}")
    
    async def close(self):
        """Cleanup resources"""
        await self.github_store.close()

