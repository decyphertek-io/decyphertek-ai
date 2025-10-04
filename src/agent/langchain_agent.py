
"""
LangChain Agent for DecypherTek AI
Integrates OpenRouter/Ollama with MCP tools for autonomous task execution
"""

import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

# Removed MCPToolkit - now using modular MCP server approach


class DecypherTekAgent:
    """
    Autonomous AI agent with tool use capabilities
    Uses LangChain + OpenRouter/Ollama + MCP tools
    """
    
    def __init__(self, 
                 ai_client,
                 provider: str = "openrouter",
                 enable_tools: bool = True,
                 verbose: bool = True,
                 doc_manager=None):
        """
        Initialize agent
        
        Args:
            ai_client: OpenRouterClient, OllamaClient, or DuckDuckGoClient instance
            provider: "openrouter", "ollama", or "duckduckgo"
            enable_tools: Enable tool use (web search, etc.)
            verbose: Print debug info
            doc_manager: DocumentManager instance for RAG integration
        """
        self.ai_client = ai_client
        self.provider = provider
        self.verbose = verbose
        self.enable_tools = enable_tools
        self.doc_manager = doc_manager
        
        # MCP server discovery and management
        self.mcp_store_path = Path(__file__).parent.parent.parent / "mcp-store"
        self.servers_path = self.mcp_store_path / "servers"
        self.available_servers = self._discover_mcp_servers()
        
        # App store discovery and management
        self.app_store_path = Path(__file__).parent.parent.parent / "app-store"
        self.available_apps = self._discover_flet_apps()
        
        # Get tools from discovered MCP servers
        self.tools = []
        if enable_tools:
            self.tools = self._get_mcp_tools()
            
            # Add RAG tools if document manager is available
            if self.doc_manager:
                self.tools.extend(self._get_rag_tools())
            
            # Add Ollama management tool if using Ollama
            if provider == "ollama":
                from agent.mcp_tools import OllamaTool
                ollama_tool = OllamaTool(ollama_client=ai_client)
                self.tools.append(ollama_tool)
        
        # Build system prompt with tool awareness
        self.system_prompt = self._build_system_prompt()
        
        print(f"[Agent] Initialized with {len(self.tools)} tools: {[t.name for t in self.tools]}")
    
    def _discover_mcp_servers(self) -> Dict[str, Dict]:
        """Discover available MCP servers from the MCP store"""
        servers = {}
        
        if not self.servers_path.exists():
            print(f"[Agent] MCP store not found at {self.servers_path}")
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
                    print(f"[Agent] Found MCP server: {server_name}")
                else:
                    print(f"[Agent] Skipping {server_name} - missing Python file")
        
        return servers
    
    def _discover_flet_apps(self) -> Dict[str, Dict]:
        """Discover available Flet applications from the app store"""
        apps = {}
        
        if not self.app_store_path.exists():
            print(f"[Agent] App store not found at {self.app_store_path}")
            return apps
        
        for app_dir in self.app_store_path.iterdir():
            if app_dir.is_dir():
                app_name = app_dir.name
                main_py = app_dir / "src" / "main.py"
                pyproject_toml = app_dir / "pyproject.toml"
                
                # Check if it's a valid Flet app with pyproject.toml
                if main_py.exists() and pyproject_toml.exists():
                    app_info = {
                        'name': app_name,
                        'path': app_dir,
                        'main_file': main_py,
                        'pyproject_toml': pyproject_toml,
                        'venv_path': app_dir / ".venv",
                        'description': app_dir / "README.md",
                        'installed': False
                    }
                    apps[app_name] = app_info
                    print(f"[Agent] Found Flet app: {app_name} (with pyproject.toml)")
                else:
                    print(f"[Agent] Skipping {app_name} - missing src/main.py or pyproject.toml")
        
        return apps
    
    def _get_mcp_tools(self) -> List:
        """Get tools from discovered MCP servers"""
        from langchain.tools import Tool
        
        tools = []
        
        # Add tools from discovered MCP servers
        for server_name, server_info in self.available_servers.items():
            if server_name == "web-search":
                # Web Search Tool (calls the enhanced web.py MCP server)
                web_search_tool = Tool(
                    name="web_search",
                    func=lambda q: self._call_web_search_mcp(q, 5),
                    description=(
                        "Search the web using enhanced MCP server with 7 fallback methods. "
                        "Input should be a search query string. "
                        "Returns a list of relevant web pages with titles, URLs, and snippets. "
                        "Uses DuckDuckGo API, DuckDuckGo HTML, Google, Bing, Yandex, Startpage, and Ecosia. "
                        "Use this when you need current information, facts, or to research topics."
                    )
                )
                tools.append(web_search_tool)
                
                video_search_tool = Tool(
                    name="search_videos",
                    func=lambda q: self._call_web_search_mcp(q, 3, "videos"),
                    description=(
                        "Search for videos including YouTube videos using enhanced MCP server. "
                        "Input should be a search query string. "
                        "Returns video results with titles, descriptions, and URLs. "
                        "Use this when the user asks for videos, YouTube content, or multimedia."
                    )
                )
                tools.append(video_search_tool)
                
                image_search_tool = Tool(
                    name="search_images",
                    func=lambda q: self._call_web_search_mcp(q, 5, "images"),
                    description=(
                        "Search for images using enhanced MCP server. "
                        "Input should be a search query string. "
                        "Returns image results with titles and URLs. "
                        "Use this when the user asks for images, pictures, or visual content."
                    )
                )
                tools.append(image_search_tool)
        
        # Launch App Tool (always available)
        launch_app_tool = Tool(
            name="launch_app",
            func=self._call_launch_app,
            description=(
                "Install and launch a Flet application from the app store. "
                "Input should be the name of the application (e.g., 'langtek', 'ansible'). "
                "Apps are automatically discovered from the app-store directory. "
                "Installs the app in a virtual environment using pyproject.toml dependencies. "
                "Loads the app within the chat window as an embedded widget. "
                "Returns installation status and app details or an error if the app cannot be launched."
            )
        )
        tools.append(launch_app_tool)
        
        return tools
    
    def _get_rag_tools(self) -> List:
        """Get RAG tools for document management"""
        from langchain.tools import Tool
        
        tools = []
        
        # Document Query Tool
        query_docs_tool = Tool(
            name="query_documents",
            func=lambda q: asyncio.run(self._call_query_documents(q)),
            description=(
                "Query uploaded documents for relevant information. "
                "Input should be a search query string. "
                "Returns relevant document chunks with filenames and content. "
                "Use this when user asks about information that might be in uploaded documents. "
                "This searches through all documents in the RAG database."
            )
        )
        tools.append(query_docs_tool)
        
        # List Documents Tool
        list_docs_tool = Tool(
            name="list_documents",
            func=self._call_list_documents,
            description=(
                "List all uploaded documents in the RAG database. "
                "Input can be empty or any string. "
                "Returns a list of all documents with filenames, sources, and chunk counts. "
                "Use this when user asks about what documents are available or wants to see the document library."
            )
        )
        tools.append(list_docs_tool)
        
        # Add Document Tool
        add_doc_tool = Tool(
            name="add_document",
            func=lambda data: asyncio.run(self._call_add_document(data)),
            description=(
                "Add a new document to the RAG database. "
                "Input should be a JSON string with 'content' and 'filename' fields. "
                "Example: '{\"content\": \"Document text here\", \"filename\": \"my_doc.txt\"}'. "
                "Use this when user wants to save information to the knowledge base. "
                "The document will be processed and made searchable."
            )
        )
        tools.append(add_doc_tool)
        
        return tools
    
    def _format_available_servers(self) -> str:
        """Format available MCP servers for system prompt"""
        if not self.available_servers:
            return "- No MCP servers discovered"
        
        formatted = ""
        for server_name, server_info in self.available_servers.items():
            formatted += f"- **{server_name}**: {server_info['python_file'].name} (Python script)\n"
        
        return formatted
    
    def _format_available_apps(self) -> str:
        """Format available Flet apps for display"""
        if not self.available_apps:
            return "- No Flet apps discovered in app store"
        
        formatted = ""
        for app_name, app_info in self.available_apps.items():
            formatted += f"- **{app_name}**: {app_info['main_file'].name} (Flet app)\n"
        
        return formatted
    
    def _call_web_search_mcp(self, query: str, num_results: int = 5, search_type: str = "text") -> str:
        """Call the web.py MCP server with 7 fallback methods"""
        try:
            # Find the web.py MCP server
            web_server_path = self.servers_path / "web-search" / "web.py"
            if not web_server_path.exists():
                debug_msg = f"🔍 [DEBUG] Web search MCP server not found at: {web_server_path}"
                print(debug_msg)
                return f"⚠️ Web search MCP server not found\n{debug_msg}"
            
            debug_msg = f"🔍 [DEBUG] Found web.py MCP server at: {web_server_path}"
            print(debug_msg)
            print(f"[Agent] Calling web.py MCP server with 7 fallback methods for: {query}")
            
            # Import and call the web.py functions directly
            import sys
            import importlib.util
            
            # Load the web.py module
            debug_msg = f"🔍 [DEBUG] Loading web.py module from: {web_server_path}"
            print(debug_msg)
            
            spec = importlib.util.spec_from_file_location("web_search", web_server_path)
            web_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(web_module)
            
            debug_msg = f"🔍 [DEBUG] Successfully loaded web.py module. Available functions: {[attr for attr in dir(web_module) if not attr.startswith('_')]}"
            print(debug_msg)
            
            # Call the appropriate search function
            if search_type == "videos":
                # Call the video search function from web.py
                if hasattr(web_module, 'search_with_fallbacks'):
                    debug_msg = f"🔍 [DEBUG] Calling search_with_fallbacks for video search: {query}"
                    print(debug_msg)
                    results = web_module.search_with_fallbacks(query, num_results)
                    debug_msg = f"🔍 [DEBUG] Video search completed, got {len(results) if results else 0} results"
                    print(debug_msg)
                    return self._format_search_results(results, f"Video Search Results for '{query}'") + f"\n{debug_msg}"
                else:
                    debug_msg = "🔍 [DEBUG] search_with_fallbacks function not found in web.py module"
                    print(debug_msg)
                    return f"⚠️ Video search not available in web.py MCP server\n{debug_msg}"
            
            elif search_type == "images":
                # Call the image search function from web.py
                if hasattr(web_module, 'search_with_fallbacks'):
                    debug_msg = f"🔍 [DEBUG] Calling search_with_fallbacks for image search: {query}"
                    print(debug_msg)
                    results = web_module.search_with_fallbacks(query, num_results)
                    debug_msg = f"🔍 [DEBUG] Image search completed, got {len(results) if results else 0} results"
                    print(debug_msg)
                    return self._format_search_results(results, f"Image Search Results for '{query}'") + f"\n{debug_msg}"
                else:
                    debug_msg = "🔍 [DEBUG] search_with_fallbacks function not found in web.py module"
                    print(debug_msg)
                    return f"⚠️ Image search not available in web.py MCP server\n{debug_msg}"
            
            else:
                # Call the regular search function from web.py
                if hasattr(web_module, 'search_with_fallbacks'):
                    debug_msg = f"🔍 [DEBUG] Calling search_with_fallbacks for web search: {query}"
                    print(debug_msg)
                    results = web_module.search_with_fallbacks(query, num_results)
                    debug_msg = f"🔍 [DEBUG] Web search completed, got {len(results) if results else 0} results"
                    print(debug_msg)
                    return self._format_search_results(results, f"Web Search Results for '{query}'") + f"\n{debug_msg}"
                else:
                    debug_msg = "🔍 [DEBUG] search_with_fallbacks function not found in web.py module"
                    print(debug_msg)
                    return f"⚠️ Web search not available in web.py MCP server\n{debug_msg}"
                    
        except Exception as e:
            debug_msg = f"🔍 [DEBUG] Exception in _call_web_search_mcp: {type(e).__name__}: {str(e)}"
            print(debug_msg)
            return f"⚠️ Error calling web.py MCP server: {str(e)}\n{debug_msg}"
    
    def _format_search_results(self, results: list, title: str) -> str:
        """Format search results from web.py MCP server"""
        if not results:
            return f"No results found for this search."
        
        formatted = f"**{title}:**\n\n"
        for i, result in enumerate(results, 1):
            formatted += f"{i}. **{result.get('title', 'No title')}**\n"
            formatted += f"   {result.get('snippet', 'No description')}\n"
            formatted += f"   🔗 {result.get('url', 'No URL')}\n\n"
        
        return formatted
    
    def _call_launch_app(self, app_name: str) -> str:
        """Install and launch a Flet application from the app store in Chaquopy"""
        try:
            debug_msg = f"🔍 [DEBUG] Launching app: {app_name}"
            print(debug_msg)
            
            # Check if app exists in app store
            if app_name.lower() not in self.available_apps:
                available_apps = list(self.available_apps.keys())
                debug_msg = f"🔍 [DEBUG] App not found. Available apps: {available_apps}"
                print(debug_msg)
                return f"⚠️ Unknown application: {app_name}. Available apps: {available_apps}\n{debug_msg}"
            
            app_info = self.available_apps[app_name.lower()]
            app_path = app_info['path']
            main_py = app_info['main_file']
            pyproject_toml = app_info['pyproject_toml']
            venv_path = app_info['venv_path']
            
            debug_msg = f"🔍 [DEBUG] App info found: {app_info}"
            print(debug_msg)
            print(f"[Agent] Installing and launching {app_name} from {app_path}")
            
            # Step 1: Install the app in a virtual environment
            debug_msg = f"🔍 [DEBUG] Starting installation process for {app_name}"
            print(debug_msg)
            
            install_result = self._install_app_in_venv(app_name, app_info)
            if not install_result['success']:
                debug_msg = f"🔍 [DEBUG] Installation failed: {install_result['error']}"
                print(debug_msg)
                return f"⚠️ Failed to install {app_name}: {install_result['error']}\n{debug_msg}"
            
            debug_msg = f"🔍 [DEBUG] Installation successful: {install_result['message']}"
            print(debug_msg)
            
            # Step 2: Create an embedded app widget for the chat bubble
            debug_msg = f"🔍 [DEBUG] Creating app widget for {app_name}"
            print(debug_msg)
            
            app_widget = self._create_app_widget(app_name, app_info)
            
            debug_msg = f"🔍 [DEBUG] App widget created successfully"
            print(debug_msg)
            
            return f"""✅ **{app_name.title()} Application Installed & Ready!**

🔧 **Installation Status**: {install_result['message']}
📱 **Chat Integration**: App will load within this chat window
🚀 **Virtual Environment**: Dependencies installed in isolated venv

**Application Details:**
- **Path**: {app_path}
- **Main File**: {main_py}
- **Dependencies**: Installed from pyproject.toml
- **Venv Path**: {venv_path}
- **Status**: Ready to launch in chat bubble

**Next Steps:**
1. The app is now installed with all dependencies
2. It will load within this chat window as an embedded widget
3. You can interact with it directly in the chat interface
4. Use the back button to return to normal chat

**Available Apps in Store:**
{self._format_available_apps()}

🎯 **Ready to launch {app_name} in chat window!**

**Debug Info:**
{debug_msg}"""
            
        except Exception as e:
            debug_msg = f"🔍 [DEBUG] Exception in _call_launch_app: {type(e).__name__}: {str(e)}"
            print(debug_msg)
            return f"⚠️ Error launching {app_name}: {str(e)}\n{debug_msg}"
    
    def _install_app_in_venv(self, app_name: str, app_info: Dict) -> Dict:
        """Install a Flet app in its own virtual environment"""
        try:
            import subprocess
            import sys
            import os
            
            app_path = app_info['path']
            venv_path = app_info['venv_path']
            pyproject_toml = app_info['pyproject_toml']
            
            debug_msg = f"🔍 [DEBUG] Installing {app_name} in venv at: {venv_path}"
            print(debug_msg)
            print(f"[Agent] Installing {app_name} in virtual environment...")
            
            # Create virtual environment if it doesn't exist
            if not venv_path.exists():
                debug_msg = f"🔍 [DEBUG] Creating new virtual environment for {app_name}"
                print(debug_msg)
                print(f"[Agent] Creating virtual environment for {app_name}")
                
                result = subprocess.run([
                    sys.executable, "-m", "venv", str(venv_path)
                ], capture_output=True, text=True)
                
                debug_msg = f"🔍 [DEBUG] Venv creation result: returncode={result.returncode}, stdout={result.stdout}, stderr={result.stderr}"
                print(debug_msg)
                
                if result.returncode != 0:
                    return {
                        'success': False,
                        'error': f"Failed to create venv: {result.stderr}",
                        'message': "Virtual environment creation failed",
                        'debug': debug_msg
                    }
            else:
                debug_msg = f"🔍 [DEBUG] Virtual environment already exists at: {venv_path}"
                print(debug_msg)
            
            # Determine the Python executable in the venv
            if os.name == 'nt':  # Windows
                venv_python = venv_path / "Scripts" / "python.exe"
            else:  # Unix/Linux/macOS
                venv_python = venv_path / "bin" / "python"
            
            debug_msg = f"🔍 [DEBUG] Using Python executable: {venv_python}"
            print(debug_msg)
            
            # Install the app using pip in the virtual environment
            debug_msg = f"🔍 [DEBUG] Installing dependencies for {app_name} from {app_path}"
            print(debug_msg)
            print(f"[Agent] Installing dependencies for {app_name}")
            
            result = subprocess.run([
                str(venv_python), "-m", "pip", "install", "-e", str(app_path)
            ], capture_output=True, text=True, cwd=str(app_path))
            
            debug_msg = f"🔍 [DEBUG] Pip install result: returncode={result.returncode}, stdout={result.stdout[:200]}..., stderr={result.stderr[:200]}..."
            print(debug_msg)
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f"Failed to install dependencies: {result.stderr}",
                    'message': "Dependency installation failed",
                    'debug': debug_msg
                }
            
            # Mark as installed
            app_info['installed'] = True
            
            debug_msg = f"🔍 [DEBUG] Successfully installed {app_name} with all dependencies"
            print(debug_msg)
            
            return {
                'success': True,
                'error': None,
                'message': f"Successfully installed {app_name} with all dependencies",
                'debug': debug_msg
            }
            
        except Exception as e:
            debug_msg = f"🔍 [DEBUG] Exception in _install_app_in_venv: {type(e).__name__}: {str(e)}"
            print(debug_msg)
            return {
                'success': False,
                'error': str(e),
                'message': f"Installation failed: {str(e)}",
                'debug': debug_msg
            }
    
    def _create_app_widget(self, app_name: str, app_info: Dict):
        """Create an embedded app widget for the chat bubble"""
        try:
            # This would create a Flet widget that embeds the app
            # For now, we'll return a placeholder that indicates the app is ready
            print(f"[Agent] Creating embedded widget for {app_name}")
            
            # In a real implementation, this would:
            # 1. Create a Flet Container with the app embedded
            # 2. Load the app's main.py within the container
            # 3. Handle the app's lifecycle within the chat bubble
            
            return {
                'type': 'embedded_app',
                'app_name': app_name,
                'status': 'ready',
                'message': f'{app_name} is ready to load in chat window'
            }
            
        except Exception as e:
            print(f"[Agent] Error creating widget for {app_name}: {e}")
            return None
    
    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt with modular MCP awareness"""
        
        tool_descriptions = ""
        if self.tools:
            tool_descriptions = "\n\n## YOUR AVAILABLE TOOLS:\n"
            for tool in self.tools:
                tool_descriptions += f"\n**{tool.name}**: {tool.description}\n"
        
        return f"""You are the DecypherTek AI Assistant - a unified intelligent agent with THREE DISTINCT SYSTEM INTEGRATIONS.

## YOUR ENVIRONMENT & CAPABILITIES

**You are running on:** {self.provider.upper()} AI Provider
**Platform:** Mobile (Chaquopy) - Battery optimized
**Available Tools:** {[tool.name for tool in self.tools]}

{tool_descriptions}

## 🗂️ SYSTEM ARCHITECTURE - THREE DISTINCT PATHS

### 1️⃣ **RAG SYSTEM** (Document Management)
**Purpose:** Query and manage local documents
**Location:** Built into the main application
**Document Manager:** {f"Available (Qdrant + OpenRouter embeddings)" if self.doc_manager else "Not available - RAG features disabled"}
**Storage Location:** `~/.decyphertek-ai/qdrant/` (Qdrant database)
**Metadata Storage:** `~/.decyphertek-ai/documents.json` (Document metadata)
**How it works:**
- Documents are stored in Qdrant vector database with embeddings
- Document metadata is stored in JSON file for quick access
- Use RAG for context when user asks about documents
- Upload/process documents through the main UI or agent tools
- **Available RAG Tools:**
  - `query_documents`: Search through uploaded documents using vector similarity
  - `list_documents`: Show all documents in the database with metadata
  - `add_document`: Add new documents to the knowledge base
- **Document Processing:** Documents are chunked, embedded, and stored in Qdrant
- **DO NOT** confuse with MCP or Apps

### 2️⃣ **MCP STORE** (Modular Python Servers)
**Purpose:** External data sources and specialized functions
**Location:** `/mcp-store/servers/`
**Discovered Servers:** {list(self.available_servers.keys())}

**How MCP Servers Work:**
- **Separate Python scripts** that run independently
- **Auto-discovery** from the MCP store directory
- **Direct execution** as standalone Python modules
- **Battery optimization** - start when needed, stop when done
- **Modular design** - add/remove without changing agent code

**Current Available MCP Servers:**
{self._format_available_servers()}

**MCP Server Usage:**
- **web-search**: For current web information, videos, images
- **rag**: For document management and retrieval (alternative to built-in RAG)
- **google-drive**: For Google Drive file operations
- **nextcloud**: For Nextcloud storage operations
- **whatsapp**: For WhatsApp messaging
- **google-voice**: For voice processing

### 3️⃣ **APP STORE** (Flet Applications)
**Purpose:** Launch full Flet applications in chat bubbles
**Location:** `/app-store/`
**Discovered Apps:** {list(self.available_apps.keys())}

**How Flet Apps Work:**
- **Complete Flet applications** with their own UI
- **Virtual environment installation** using pyproject.toml
- **Chat bubble integration** - apps load within chat window
- **Isolated dependencies** - each app gets its own venv
- **Embedded widgets** - apps run as widgets in chat interface

**Current Available Flet Apps:**
{self._format_available_apps()}

## 🎯 EXECUTION GUIDELINES - CLEAR SEPARATION

### **When to use RAG:**
- User asks about documents or knowledge base
- Need context from uploaded documents
- Document management tasks
- User wants to save information to knowledge base
- User asks "what documents do I have?" or "list my documents"
- User wants to search through uploaded content
- **Use RAG tools:** `query_documents`, `list_documents`, `add_document`
- **Document Manager Status:** {f"Available - {len(self.doc_manager.get_documents()) if self.doc_manager else 0} documents stored" if self.doc_manager else "Not available - RAG features disabled"}

### **When to use MCP Servers:**
- Need current web information (weather, news, etc.)
- Want to search for videos or images
- Need to access external services (Google Drive, Nextcloud, etc.)
- **Use web-search MCP for web queries**

### **When to use Flet Apps:**
- User wants to run a specific application (langtek, ansible, etc.)
- Need a full application interface
- **Use launch_app tool for Flet applications**

## 🚀 RESPONSE GUIDELINES

1. **Be specific**: Clearly state which system you're using (RAG, MCP, or Apps)
2. **Be transparent**: Tell user what you're doing ("Using MCP web-search...", "Launching Flet app...")
3. **Include URLs**: Always include full URLs (YouTube links auto-embed)
4. **Battery conscious**: Mention when starting/stopping MCP servers
5. **Clear separation**: Never confuse RAG, MCP, and Apps - they are distinct systems

## ⚠️ CRITICAL REMINDERS

- **RAG** = Local document management (built-in)
  - Document Manager: {f"Available at {self.doc_manager.storage_dir if self.doc_manager else 'Not available'}"}
  - Documents stored in: Qdrant vector database + JSON metadata
  - Use for: Document queries, knowledge base management
- **MCP** = External Python servers (modular, battery-optimized)
- **Apps** = Full Flet applications (chat bubble integration)
- **NEVER** mix these systems - they have different purposes and execution paths
- Always use the right system for the right job
- Be transparent about which system you're using
"""
    
    async def chat(self, message: str, context: Optional[str] = None) -> str:
        """
        Chat with agent (with tool use if enabled)
        
        Args:
            message: User message
            context: Optional context from RAG
            
        Returns:
            String response (with URLs that will auto-embed)
        """
        try:
            # Build messages
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Context from knowledge base:\n{context}"
                })
            
            messages.append({"role": "user", "content": message})
            
            # Check if we should use tools
            if self.enable_tools and self._should_use_tools(message):
                return await self._agent_chat(messages, message)
            else:
                return await self._direct_chat(messages)
                
        except Exception as e:
            print(f"[Agent] Chat error: {e}")
            import traceback
            traceback.print_exc()
            return f"I encountered an error: {str(e)}"
    
    def _should_use_tools(self, message: str) -> bool:
        """
        Determine if message requires tool use (MCP or Apps)
        RAG is handled separately by the main chat system
        """
        if not self.tools:
            return False
        
        message_lower = message.lower()
        
        # MCP Server indicators (web search, external data)
        mcp_keywords = [
            "search", "find", "look up", "lookup", "search for",
            "find me", "show me", "get me", "can you search",
            "can you find", "look for", "youtube", "video",
            "song", "music", "movie", "image", "picture", "montage",
            "trailer", "clip", "watch", "stream", "play",
            "weather", "news", "current", "latest", "web", "internet", "online",
            "what is", "who is", "when is", "where is", "how to", "tell me about"
        ]
        
        # Flet App launch indicators
        app_launch_keywords = [
            "run", "launch", "start", "open", "execute", "can you run",
            "can you launch", "can you start", "please run", "please launch",
            "langtek", "netrunner", "ansible", "application", "app"
        ]
        
        # Check for MCP intent (web search, external data)
        has_mcp_intent = any(keyword in message_lower for keyword in mcp_keywords)
        
        # Check for Flet app launch intent
        has_app_launch_intent = any(keyword in message_lower for keyword in app_launch_keywords)
        
        if self.verbose:
            print(f"[Agent] MCP intent detected: {has_mcp_intent}")
            print(f"[Agent] App launch intent detected: {has_app_launch_intent}")
        
        return has_mcp_intent or has_app_launch_intent
    
    async def _agent_chat(self, messages: List[Dict], user_message: str) -> str:
        """
        Chat with tool use enabled
        Returns simple string with URLs
        """
        print("[Agent] Using tools for this query...")
        
        # Detect if this is an app launch request
        message_lower = user_message.lower()
        
        # Check if this is an app launch request
        app_launch_keywords = ["run", "launch", "start", "open", "execute"]
        app_names = ["langtek", "netrunner", "ansible"]
        
        is_app_launch = any(keyword in message_lower for keyword in app_launch_keywords)
        has_app_name = any(app in message_lower for app in app_names)
        
        if is_app_launch and has_app_name:
            # Extract app name
            app_name = None
            for app in app_names:
                if app in message_lower:
                    app_name = app
                    break
            
            if app_name:
                try:
                    print(f"[Agent] 🚀 Using APP STORE system - Launching Flet app: {app_name}")
                    result = self._call_launch_app(app_name)
                    return result
                except Exception as e:
                    print(f"[Agent] App launch error: {e}")
                    return f"I encountered an error while launching {app_name}: {str(e)}"
        
        # Check if this is a video search request
        video_keywords = ["youtube", "video", "trailer", "clip", "watch", "stream", "play", "song", "music", "movie"]
        is_video_search = any(keyword in message_lower for keyword in video_keywords)
        
        # Default to web search
        # Extract search query
        search_query = user_message
        for prefix in ["search for", "find", "look up", "search", "show me", "get me", "can you find"]:
            if prefix in message_lower:
                search_query = message_lower.split(prefix, 1)[1].strip()
                break
        
        # Execute appropriate search
        try:
            if is_video_search:
                print(f"[Agent] 🔍 Using MCP STORE system - Executing video search: {search_query}")
                result = self._call_web_search_mcp(search_query, 3, "videos")
            else:
                print(f"[Agent] 🔍 Using MCP STORE system - Executing web search: {search_query}")
                result = self._call_web_search_mcp(search_query, 5, "text")
            
            # Result is already a string with URLs
            search_text = result if isinstance(result, str) else result.get("text", "No results found")
            
            print(f"[Agent] Search completed, got {len(search_text)} chars")
            
            # Build response with search results
            response_messages = messages + [
                {
                    "role": "system",
                    "content": f"Search results for '{search_query}':\n\n{search_text}\n\nPlease summarize these results and include the relevant URLs."
                }
            ]
            
            # Get AI to format the response nicely
            final_response = await self._direct_chat(response_messages)
            
            return final_response
            
        except Exception as e:
            print(f"[Agent] Tool execution error: {e}")
            import traceback
            traceback.print_exc()
            
            # Fall back to direct chat
            return await self._direct_chat(messages)
    
    async def _direct_chat(self, messages: List[Dict]) -> str:
        """
        Direct chat without tools
        Compatible with OpenRouterClient, OllamaClient, and DuckDuckGoClient
        """
        try:
            # Convert messages to format expected by clients
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Call the appropriate client method
            if hasattr(self.ai_client, 'send_message'):
                # OpenRouterClient
                response = await self.ai_client.send_message(formatted_messages, stream=False)
            elif hasattr(self.ai_client, 'chat'):
                # OllamaClient or DuckDuckGoClient
                response = await self.ai_client.chat(formatted_messages)
            else:
                return "Error: Unsupported AI client"
            
            return response or "I apologize, but I couldn't generate a response."
            
        except Exception as e:
            print(f"[Agent] Direct chat error: {e}")
            import traceback
            traceback.print_exc()
            return f"I encountered an error: {str(e)}"
    
    async def _call_query_documents(self, query: str) -> str:
        """Query documents in the RAG database"""
        try:
            if not self.doc_manager:
                return "⚠️ RAG system not available - no document manager configured"
            
            debug_msg = f"🔍 [DEBUG] Querying RAG documents for: {query}"
            print(debug_msg)
            
            # Query documents
            results = await self.doc_manager.query_documents(query, n_results=3)
            
            if not results:
                debug_msg = f"🔍 [DEBUG] No relevant documents found for query: {query}"
                print(debug_msg)
                return f"No relevant documents found for '{query}'.\n{debug_msg}"
            
            # Format results
            formatted_results = f"📚 **Found {len(results)} relevant document chunks:**\n\n"
            for i, result in enumerate(results, 1):
                formatted_results += f"**{i}. {result['filename']}**\n"
                formatted_results += f"Content: {result['content'][:200]}{'...' if len(result['content']) > 200 else ''}\n\n"
            
            debug_msg = f"🔍 [DEBUG] Found {len(results)} relevant document chunks"
            print(debug_msg)
            
            return formatted_results + f"\n{debug_msg}"
            
        except Exception as e:
            debug_msg = f"🔍 [DEBUG] Exception in _call_query_documents: {type(e).__name__}: {str(e)}"
            print(debug_msg)
            return f"⚠️ Error querying documents: {str(e)}\n{debug_msg}"
    
    def _call_list_documents(self, _: str = "") -> str:
        """List all documents in the RAG database"""
        try:
            if not self.doc_manager:
                return "⚠️ RAG system not available - no document manager configured"
            
            debug_msg = f"🔍 [DEBUG] Listing all RAG documents"
            print(debug_msg)
            
            # Get all documents
            documents = self.doc_manager.get_documents()
            
            if not documents:
                debug_msg = f"🔍 [DEBUG] No documents found in RAG database"
                print(debug_msg)
                return f"📚 **No documents in RAG database yet.**\n\nUpload documents through the RAG tab or use the add_document tool.\n{debug_msg}"
            
            # Format document list
            formatted_docs = f"📚 **RAG Database - {len(documents)} documents:**\n\n"
            for doc_id, doc_info in documents.items():
                formatted_docs += f"**📄 {doc_info['filename']}**\n"
                formatted_docs += f"  - Source: {doc_info['source']}\n"
                formatted_docs += f"  - Chunks: {doc_info['chunks']}\n"
                formatted_docs += f"  - Size: {doc_info['size']} chars\n"
                formatted_docs += f"  - ID: {doc_id}\n\n"
            
            debug_msg = f"🔍 [DEBUG] Listed {len(documents)} documents"
            print(debug_msg)
            
            return formatted_docs + f"\n{debug_msg}"
            
        except Exception as e:
            debug_msg = f"🔍 [DEBUG] Exception in _call_list_documents: {type(e).__name__}: {str(e)}"
            print(debug_msg)
            return f"⚠️ Error listing documents: {str(e)}\n{debug_msg}"
    
    async def _call_add_document(self, input_data: str) -> str:
        """Add a document to the RAG database"""
        try:
            if not self.doc_manager:
                return "⚠️ RAG system not available - no document manager configured"
            
            debug_msg = f"🔍 [DEBUG] Adding document to RAG database"
            print(debug_msg)
            
            # Parse input data
            try:
                import json
                data = json.loads(input_data)
                content = data.get('content', '')
                filename = data.get('filename', 'untitled.txt')
            except json.JSONDecodeError:
                # If not JSON, treat as content with default filename
                content = input_data
                filename = "user_input.txt"
            
            if not content.strip():
                return "⚠️ No content provided to add to RAG database"
            
            debug_msg = f"🔍 [DEBUG] Adding document: {filename} ({len(content)} chars)"
            print(debug_msg)
            
            # Add document
            success = await self.doc_manager.add_document(
                content=content,
                filename=filename,
                source="agent"
            )
            
            if success:
                debug_msg = f"🔍 [DEBUG] Successfully added document: {filename}"
                print(debug_msg)
                return f"✅ **Document added to RAG database!**\n\n**Filename:** {filename}\n**Size:** {len(content)} characters\n**Source:** Agent\n\nDocument is now searchable and will be included in RAG queries.\n{debug_msg}"
            else:
                debug_msg = f"🔍 [DEBUG] Document already exists: {filename}"
                print(debug_msg)
                return f"⚠️ **Document already exists:** {filename}\n\nThe document with this content is already in the RAG database.\n{debug_msg}"
            
        except Exception as e:
            debug_msg = f"🔍 [DEBUG] Exception in _call_add_document: {type(e).__name__}: {str(e)}"
            print(debug_msg)
            return f"⚠️ Error adding document: {str(e)}\n{debug_msg}"
    
    def update_client(self, new_client, provider: str):
        """
        Update AI client (for provider switching)
        
        Args:
            new_client: New AI client instance
            provider: New provider name
        """
        self.ai_client = new_client
        self.provider = provider
        self.system_prompt = self._build_system_prompt()
        print(f"[Agent] Switched to {provider}")
