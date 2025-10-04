"""
GitHub-based MCP server store
"""

import httpx
import json
from typing import List, Dict, Optional
from pathlib import Path
import base64

from .models import MCPServer
from utils.logger import setup_logger

logger = setup_logger()


class MCPGitHubStore:
    """
    Fetch and manage MCP servers from GitHub repositories
    
    Supports two formats:
    1. Direct GitHub repo with mcp-store structure
    2. API endpoint that serves MCP server index
    """
    
    def __init__(self, store_url: str, cache_dir: str):
        """
        Initialize GitHub MCP store
        
        Args:
            store_url: GitHub repository URL or API endpoint
            cache_dir: Directory to cache server definitions
        """
        self.store_url = store_url
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Determine if it's a GitHub repo or API endpoint
        self.is_github_repo = "github.com" in store_url
        
        logger.info(f"MCP Store initialized: {store_url}")
    
    async def fetch_index(self) -> List[MCPServer]:
        """
        Fetch the index of available MCP servers
        
        Returns:
            List of MCP server definitions
        """
        try:
            if self.is_github_repo:
                servers = await self._fetch_from_github()
            else:
                servers = await self._fetch_from_api()
            
            # Cache the index
            self._cache_index(servers)
            
            logger.info(f"Fetched {len(servers)} MCP servers from store")
            return servers
            
        except Exception as e:
            logger.error(f"Error fetching MCP index: {e}")
            # Try to load from cache
            return self._load_cached_index()
    
    async def _fetch_from_github(self) -> List[MCPServer]:
        """
        Fetch MCP servers from GitHub repository
        
        Expected structure:
        repo/
          ├── index.json
          └── servers/
              ├── server1/
              │   ├── server.py
              │   └── config.json
              └── server2/
                  ├── server.py
                  └── config.json
        """
        # Convert GitHub URL to API URL
        # https://github.com/user/repo -> https://api.github.com/repos/user/repo
        api_url = self.store_url.replace(
            "https://github.com/",
            "https://api.github.com/repos/"
        )
        
        # Fetch index.json from the repo
        index_url = f"{api_url}/contents/index.json"
        
        response = await self.client.get(index_url)
        response.raise_for_status()
        
        # GitHub API returns base64-encoded content
        content_data = response.json()
        content = base64.b64decode(content_data['content']).decode('utf-8')
        index_data = json.loads(content)
        
        # Parse servers
        servers = [
            MCPServer.from_dict(server_data)
            for server_data in index_data.get('servers', [])
        ]
        
        return servers
    
    async def _fetch_from_api(self) -> List[MCPServer]:
        """
        Fetch MCP servers from API endpoint
        
        Expected response:
        {
          "servers": [
            {
              "id": "server1",
              "name": "Server 1",
              ...
            }
          ]
        }
        """
        response = await self.client.get(f"{self.store_url}/index.json")
        response.raise_for_status()
        
        data = response.json()
        
        servers = [
            MCPServer.from_dict(server_data)
            for server_data in data.get('servers', [])
        ]
        
        return servers
    
    async def download_server(self, server: MCPServer, install_dir: Path) -> bool:
        """
        Download MCP server Python code from GitHub
        
        Args:
            server: MCP server definition
            install_dir: Directory to install the server
            
        Returns:
            True if successful
        """
        try:
            install_path = install_dir / server.id
            install_path.mkdir(parents=True, exist_ok=True)
            
            # Download the Python file
            if server.github_url.startswith("https://github.com/"):
                # Convert to raw GitHub URL
                raw_url = server.github_url.replace(
                    "https://github.com/",
                    "https://raw.githubusercontent.com/"
                ).replace("/blob/", "/")
                
                # Construct full URL to Python file
                python_url = f"{raw_url}/{server.python_file}"
                
                response = await self.client.get(python_url)
                response.raise_for_status()
                
                # Save Python file
                python_path = install_path / Path(server.python_file).name
                with open(python_path, 'w') as f:
                    f.write(response.text)
                
                # Save server metadata
                metadata_path = install_path / "metadata.json"
                with open(metadata_path, 'w') as f:
                    f.write(server.to_json())
                
                logger.info(f"Downloaded MCP server: {server.name}")
                return True
            else:
                logger.error(f"Invalid GitHub URL: {server.github_url}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading server {server.name}: {e}")
            return False
    
    async def fetch_server_config(self, server: MCPServer) -> Optional[Dict]:
        """
        Fetch configuration schema for a server
        
        Args:
            server: MCP server definition
            
        Returns:
            Configuration schema dictionary
        """
        try:
            # Try to fetch config.json from GitHub
            if server.github_url.startswith("https://github.com/"):
                raw_url = server.github_url.replace(
                    "https://github.com/",
                    "https://raw.githubusercontent.com/"
                ).replace("/blob/", "/")
                
                config_url = f"{raw_url}/config.json"
                
                response = await self.client.get(config_url)
                response.raise_for_status()
                
                return response.json()
            
            return server.config_schema
            
        except Exception as e:
            logger.debug(f"No config schema found for {server.name}: {e}")
            return server.config_schema
    
    def _cache_index(self, servers: List[MCPServer]):
        """Cache server index locally"""
        try:
            cache_file = self.cache_dir / "index.json"
            
            data = {
                "servers": [server.to_dict() for server in servers]
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error caching index: {e}")
    
    def _load_cached_index(self) -> List[MCPServer]:
        """Load cached server index"""
        try:
            cache_file = self.cache_dir / "index.json"
            
            if not cache_file.exists():
                return []
            
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            servers = [
                MCPServer.from_dict(server_data)
                for server_data in data.get('servers', [])
            ]
            
            logger.info(f"Loaded {len(servers)} servers from cache")
            return servers
            
        except Exception as e:
            logger.error(f"Error loading cached index: {e}")
            return []
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

