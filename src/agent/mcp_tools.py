
"""
MCP Tools wrapped as LangChain tools
Direct execution for Chaquopy compatibility (no subprocess needed)
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from pydantic import BaseModel, Field

# Lightweight local Tool replacement (to avoid LangChain dependency)
from typing import Callable


class Tool:
    """Minimal tool wrapper compatible with current app usage."""

    def __init__(self, name: str, func: Callable, description: str):
        self.name = name
        self.func = func
        self.description = description

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class WebSearchInput(BaseModel):
    """Input for web search tool"""
    query: str = Field(description="The search query to look up")
    num_results: Optional[int] = Field(default=5, description="Number of results to return")


class URLScrapeInput(BaseModel):
    """Input for URL scraping tool"""
    url: str = Field(description="The URL to scrape content from")


class LaunchAppInput(BaseModel):
    """Input for launching applications"""
    app_name: str = Field(description="The name of the application to launch (e.g., 'langtek', 'netrunner', 'ansible')")


# Direct web search implementation (no MCP server dependency)
try:
    from duckduckgo_search import DDGS
    ddgs_available = True
    print("[MCPToolkit] DuckDuckGo search available")
except ImportError as e:
    print(f"Warning: Could not import DuckDuckGo search: {e}")
    ddgs_available = False


class MCPToolkit:
    """
    Modular MCP Toolkit for DecypherTek AI
    Discovers and manages MCP servers dynamically from the MCP store
    """
    
    def __init__(self):
        """Initialize MCP toolkit"""
        # Get MCP store path
        self.mcp_store_path = Path(__file__).parent.parent.parent.parent.parent / "mcp-store"
        self.servers_path = self.mcp_store_path / "servers"
        
        # Initialize DuckDuckGo for fallback
        self.ddgs = DDGS() if ddgs_available else None
        
        # Discover available MCP servers
        self.available_servers = self._discover_mcp_servers()
        print(f"[MCPToolkit] Discovered {len(self.available_servers)} MCP servers: {list(self.available_servers.keys())}")
        
        # Rate limiting for DuckDuckGo fallback only
        self._ddg_timestamps = []
        self._ddg_rate_limit = {'max_requests': 5, 'window_seconds': 60}
        
        # Initialize event loop
        self.loop = None
    
    def _discover_mcp_servers(self) -> Dict[str, Dict]:
        """Discover available MCP servers from the MCP store"""
        servers = {}
        
        if not self.servers_path.exists():
            print(f"[MCPToolkit] MCP store not found at {self.servers_path}")
            return servers
        
        for server_dir in self.servers_path.iterdir():
            if server_dir.is_dir():
                server_name = server_dir.name
                server_info = {
                    'name': server_name,
                    'path': server_dir,
                    'python_file': server_dir / f"{server_name.split('-')[0]}.py",  # e.g., web.py
                    'requirements': server_dir / "requirements.txt",
                    'config': server_dir / f"{server_name.split('-')[0]}.json",  # e.g., web.json
                    'description': server_dir / f"{server_name.split('-')[0]}.md"  # e.g., web.md
                }
                
                # Check if server is properly configured
                if server_info['python_file'].exists():
                    servers[server_name] = server_info
                    print(f"[MCPToolkit] Found MCP server: {server_name}")
                else:
                    print(f"[MCPToolkit] Skipping {server_name} - missing Python file")
        
        return servers
    
    def _get_loop(self):
        """Get or create event loop"""
        if self.loop is None:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
        return self.loop
    
    def _load_config(self) -> Dict[str, Any]:
        """Load MCP servers configuration from JSON"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    print(f"[MCPToolkit] Loaded config for {len(config.get('servers', {}))} MCP servers")
                    return config
            else:
                print(f"[MCPToolkit] Warning: Config not found at {self.config_path}")
                return {"servers": {}}
        except Exception as e:
            print(f"[MCPToolkit] Error loading config: {e}")
            return {"servers": {}}
    
    def _check_ddg_rate_limit(self) -> bool:
        """Check if we're within DuckDuckGo rate limits"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self._ddg_rate_limit['window_seconds'])
        
        # Clean old timestamps
        self._ddg_timestamps = [ts for ts in self._ddg_timestamps if ts > cutoff]
        
        # Check if we're under the limit
        return len(self._ddg_timestamps) < self._ddg_rate_limit['max_requests']
    
    def _record_ddg_search(self):
        """Record a DuckDuckGo search request timestamp"""
        self._ddg_timestamps.append(datetime.now())
    
    def _run_async(self, coro):
        """Run async function in sync context"""
        loop = self._get_loop()
        if loop.is_running():
            future = asyncio.ensure_future(coro, loop=loop)
            return future
        else:
            return loop.run_until_complete(coro)
    
    async def _call_web_search_tool(self, tool_name: str, arguments: dict) -> str:
        """
        Call web search tool using enhanced MCP server with 7 fallback methods
        
        Uses the robust web.py MCP server with comprehensive fallback system.
        """
        print("[MCPToolkit] Starting enhanced web-search MCP server with 7 fallback methods")
        return await self._call_enhanced_web_search(tool_name, arguments)
    
    async def _ddg_fallback_search(self, tool_name: str, arguments: dict) -> str:
        """Simple DuckDuckGo fallback with basic rate limiting"""
        if not self.ddgs:
            return "⚠️ Web search unavailable - MCP server not running and DuckDuckGo not installed"
        
        # Check rate limit
        if not self._check_ddg_rate_limit():
            return "⚠️ Rate limit reached. Please try again in a moment."
        
        # Record search
        self._record_ddg_search()
        
        query = arguments.get("query", "")
        num_results = arguments.get("num_results", 5)
        
        try:
            if tool_name == "search":
                results = list(self.ddgs.text(query, max_results=num_results))
                return self._format_search_results(results, "Web Search (Fallback)")
            elif tool_name == "search_videos":
                results = list(self.ddgs.videos(query, max_results=num_results))
                return self._format_video_results(results, "Video Search (Fallback)")
            elif tool_name == "search_images":
                results = list(self.ddgs.images(query, max_results=num_results))
                return self._format_image_results(results, "Image Search (Fallback)")
            else:
                return f"Unknown search type: {tool_name}"
        except Exception as e:
            return f"⚠️ Search error: {str(e)}"
    
    def _format_mcp_result(self, result: Any) -> str:
        """Format result from MCP server"""
        if isinstance(result, dict) and 'content' in result:
            # MCP server returns structured content
            return result['content']
        elif isinstance(result, str):
            return result
        else:
            return str(result)
    
    def _format_search_results(self, results: list, title: str) -> str:
        """Format web search results"""
        if not results:
            return f"No {title.lower()} results found"
        
        formatted = f"**{title} Results:**\n\n"
        for i, result in enumerate(results, 1):
            formatted += f"{i}. **{result.get('title', 'No title')}**\n"
            formatted += f"   {result.get('body', 'No description')}\n"
            formatted += f"   🔗 {result.get('href', 'No URL')}\n\n"
        
        return formatted
    
    def _format_video_results(self, results: list, title: str) -> str:
        """Format video search results"""
        if not results:
            return f"No {title.lower()} results found"
        
        formatted = f"**{title} Results:**\n\n"
        for i, result in enumerate(results, 1):
            formatted += f"{i}. **{result.get('title', 'No title')}**\n"
            formatted += f"   📺 {result.get('content', 'No description')}\n"
            formatted += f"   🔗 {result.get('url', 'No URL')}\n"
            if result.get('duration'):
                formatted += f"   ⏱️ Duration: {result.get('duration')}\n"
            formatted += "\n"
        
        return formatted
    
    def _format_image_results(self, results: list, title: str) -> str:
        """Format image search results"""
        if not results:
            return f"No {title.lower()} results found"
        
        formatted = f"**{title} Results:**\n\n"
        for i, result in enumerate(results, 1):
            formatted += f"{i}. **{result.get('title', 'No title')}**\n"
            formatted += f"   🖼️ {result.get('url', 'No URL')}\n"
            if result.get('thumbnail'):
                formatted += f"   🖼️ Thumbnail: {result.get('thumbnail')}\n"
            formatted += "\n"
        
        return formatted
    
    async def _call_launch_app_tool(self, app_name: str) -> str:
        """Launch an enabled application"""
        try:
            base_path = Path.home() / "Documents" / "git" / "flet"
            
            app_paths = {
                "langtek": base_path / "langtek" / "src" / "main.py",
                "netrunner": base_path / "netrunner" / "NetRunner-Python" / "main.py", 
                "ansible": base_path / "ansible" / "src" / "main.py"
            }
            
            app_name_lower = app_name.lower()
            
            if app_name_lower not in app_paths:
                return f"Unknown application: {app_name}. Available apps: {', '.join(app_paths.keys())}"
            
            app_path = app_paths[app_name_lower]
            
            if not app_path.exists():
                return f"Application {app_name} not found at {app_path}"
            
            return f"🚀 Launching {app_name}...\n\nNote: App launching via Chaquopy is ready for implementation. The {app_name} application is available at {app_path} and can be launched when enabled in the admin panel."
            
        except Exception as e:
            return f"Error launching {app_name}: {str(e)}"
    
    def web_search_sync(self, query: str, num_results: int = 5) -> str:
        """Synchronous wrapper for web search"""
        return self._run_async(self._call_web_search_tool("search", {"query": query, "num_results": num_results}))
    
    def video_search_sync(self, query: str, num_results: int = 3) -> str:
        """Synchronous wrapper for video search"""
        return self._run_async(self._call_web_search_tool("search_videos", {"query": query, "num_results": num_results}))
    
    def image_search_sync(self, query: str, num_results: int = 5) -> str:
        """Synchronous wrapper for image search"""
        return self._run_async(self._call_web_search_tool("search_images", {"query": query, "num_results": num_results}))
    
    def launch_app_sync(self, app_name: str) -> str:
        """Synchronous wrapper for launching applications"""
        return self._run_async(self._call_launch_app_tool(app_name))
    
    def get_tools(self) -> List[Tool]:
        """
        Get all MCP tools as LangChain tools
        Dynamically discovers tools from available MCP servers
        
        Returns:
            List of LangChain Tool objects
        """
        tools = []
        
        # Add tools from discovered MCP servers
        for server_name, _server_info in self.available_servers.items():
            if server_name == "web-search" and self.ddgs:
                tools.append(
                    Tool(
                        name="web_search",
                        func=lambda q: self.web_search_sync(q, 5),
                        description=(
                            "Search the web using DuckDuckGo. "
                            "Input should be a search query string. "
                            "Returns a list of relevant web pages with titles, URLs, and snippets. "
                            "Use this when you need current information, facts, or to research topics."
                        ),
                    )
                )
                tools.append(
                    Tool(
                        name="search_videos",
                        func=lambda q: self.video_search_sync(q, 3),
                        description=(
                            "Search for videos including YouTube videos. "
                            "Input should be a search query string. "
                            "Returns video results with titles, descriptions, and URLs. "
                            "Use this when the user asks for videos, YouTube content, or multimedia."
                        ),
                    )
                )
                tools.append(
                    Tool(
                        name="search_images",
                        func=lambda q: self.image_search_sync(q, 5),
                        description=(
                            "Search for images. "
                            "Input should be a search query string. "
                            "Returns image results with titles and URLs. "
                            "Use this when the user asks for images, pictures, or visual content."
                        ),
                    )
                )
        
        # Launch App Tool
        launch_app_tool = Tool(
            name="launch_app",
            func=self.launch_app_sync,
            description=(
                "Launch an enabled application from the admin panel. "
                "Input should be the name of the application (e.g., 'langtek', 'netrunner', 'ansible'). "
                "Only works if the application is enabled in the admin panel. "
                "Use this when the user asks to run, launch, or start a specific application."
            )
        )
        tools.append(launch_app_tool)
        
        return tools
    
    async def scrape_ollama_models(self) -> List[Dict[str, Any]]:
        """
        Scrape Ollama model library from ollama.com
        Uses web scraping to get live model data
        
        Returns:
            List of model dictionaries with name, size, description, etc.
        """
        url = "https://ollama.com/library?sort=popular"
        
        try:
            content = await self._scrape_url(url)
            
            # Parse the content for model information
            # This is a simplified parser - a real implementation would use BeautifulSoup
            models = []
            
            # For now, return a notice that we scraped the page
            # In production, you'd parse the HTML properly
            return {
                'success': True,
                'content': content,
                'message': 'Scraped Ollama library page - parse the content for model names'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to scrape Ollama models'
            }


class OllamaManagementInput(BaseModel):
    """Input for Ollama management tool"""
    action: str = Field(description="Action to perform: 'list', 'pull', 'search'")
    model: Optional[str] = Field(default=None, description="Model name for pull action")


class OllamaTool:
    """
    Tool for managing Ollama models
    Allows agent to pull models, list installed, etc.
    """
    name: str = "ollama_manager"
    description: str = (
        "Manage Ollama models. "
        "Actions: 'list' (show installed models), 'pull MODEL_NAME' (download a model), "
        "'search' (find available models online). "
        "Use this when user wants to install or manage local AI models."
    )
    args_schema: type[BaseModel] = OllamaManagementInput
    
    ollama_client: Any = None
    
    def _run(self, action: str, model: Optional[str] = None) -> str:
        """Execute Ollama management action"""
        if not self.ollama_client:
            return "Error: Ollama client not configured"
        
        try:
            if action == "list":
                # List installed models
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                models = loop.run_until_complete(self.ollama_client.get_available_models())
                
                if not models:
                    return "No Ollama models installed. Use 'pull' to download one."
                
                return f"Installed models: {', '.join(models)}"
            
            elif action == "pull" and model:
                # Pull a model
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success, message = loop.run_until_complete(self.ollama_client.pull_model(model))
                
                return f"Pull {model}: {message}"
            
            elif action == "search":
                # Search available models
                return (
                    "Popular Ollama models:\n"
                    "- gemma2:2b (1.6GB) - Best quality for size\n"
                    "- qwen2.5:0.5b (400MB) - Ultra lightweight\n"
                    "- llama3.2:1b (1.3GB) - Good balance\n"
                    "- tinyllama (637MB) - Very fast\n"
                    "- phi3:mini (2.3GB) - Excellent quality\n"
                    "Use 'pull MODEL_NAME' to download."
                )
            
            else:
                return f"Unknown action: {action}"
                
        except Exception as e:
            return f"Ollama error: {str(e)}"
    
    async def _arun(self, action: str, model: Optional[str] = None) -> str:
        """Async version"""
        return self._run(action, model)


# MCP server integration removed - using direct DuckDuckGo integration instead
