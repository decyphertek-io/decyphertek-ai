"""
Main dashboard view with OpenRouter chat integration
"""

import flet as ft
from typing import Callable
from pathlib import Path

from auth.api_keys import APIKeyManager
from chat.openrouter_client import OpenRouterClient
from chat.ollama_client import OllamaClient
from chat.duckduckgo_client import DuckDuckGoClient
from ui.chat import ChatView
from ui.api_settings import APISettingsView
from ui.ollama_settings import OllamaSettingsView
from ui.rag_view import RAGView
from rag.document_manager import DocumentManager
from agent.store_manager import DecypherTekAgent, StoreManager
from ui.mcp_store import MCPStoreView


class DashboardView:
    """Dashboard with OpenRouter AI chat, RAG, and MCP"""
    
    def __init__(self, page: ft.Page, credential_manager, username: str, password: str, on_logout: Callable, on_admin: Callable = None):
        """
        Initialize dashboard view
        
        Args:
            page: Flet page
            credential_manager: Credential manager instance
            username: Current username
            password: Current password (for API key encryption)
            on_logout: Callback when user logs out
            on_admin: Optional callback for admin panel
        """
        self.page = page
        self.credential_manager = credential_manager
        self.username = username
        self.password = password
        self.on_logout = on_logout
        self.on_admin = on_admin
        
        # Get master key for API key encryption
        self.master_key = credential_manager.get_master_key(password)
        if not self.master_key:
            raise Exception("Failed to load master key")
        
        # Get storage directory (same as credentials)
        storage_dir = credential_manager.storage_dir
        
        # Initialize API key manager
        self.api_key_manager = APIKeyManager(str(storage_dir), self.master_key)
        
        # Get API key for embeddings
        config = self.api_key_manager.get_openrouter_config()
        api_key = config['api_key'] if config else None
        
        # Initialize document manager for RAG (with error handling for Qdrant locks)
        try:
            self.document_manager = DocumentManager(str(storage_dir), openrouter_api_key=api_key)
        except Exception as e:
            print(f"[Dashboard] Warning: Could not initialize document manager: {e}")
            print("[Dashboard] RAG features will be disabled")
            self.document_manager = None
        
        # Initialize AI client/agent lazily (after UI renders)
        self.ai_client = None
        self.agent = None
        self.adminotaur_agent = None  # Adminotaur agent for RAG integration
        self._ai_init_started = False
        
        # UI state
        self.current_index = 0
        self.content_area = None
        self.navigation_bar = None
        self.chat_view = None
        self.rag_view = None
        self._rag_tab_content = None
        # Store manager (for Agent Store personalities)
        self.store_manager = StoreManager()
        self._agents_init_started = False
        self._agents_tab_content = None
        self._mcp_tab_content = None
        self._apps_tab_content = None
        
        # Chat manager for MCP server integration
        self.chat_manager = None
        
        # View mode
        self.showing_api_settings = False
    
    def _init_chat_manager(self):
        """Initialize chat manager for MCP server integration"""
        try:
            if not self.chat_manager:
                from agent.chat_manager import ChatManager
                self.chat_manager = ChatManager(
                    page=self.page,
                    ai_client=self.ai_client,
                    document_manager=self.document_manager
                )
                print("[Dashboard] Chat manager initialized for MCP integration")
        except Exception as e:
            print(f"[Dashboard] Warning: Could not initialize chat manager: {e}")
            self.chat_manager = None
    
    def _init_adminotaur_agent(self):
        """Initialize Adminotaur agent for RAG integration"""
        try:
            if not self.adminotaur_agent:
                # Initialize chat manager first
                self._init_chat_manager()
                
                # Import AdminotaurAgent from the store
                from store.agent.adminotaur.adminotaur import AdminotaurAgent
                self.adminotaur_agent = AdminotaurAgent(self)
                print("[Dashboard] Adminotaur agent initialized for RAG integration")
        except Exception as e:
            print(f"[Dashboard] Warning: Could not initialize Adminotaur agent: {e}")
            self.adminotaur_agent = None
    
    def _init_ai_client(self):
        """Initialize AI client and agent based on selected provider"""
        provider = self.api_key_manager.get_ai_provider()
        
        if provider == 'ollama':
            # Initialize Ollama client
            ollama_config = self.api_key_manager.get_ollama_config()
            if ollama_config:
                self.ai_client = OllamaClient(
                    model=ollama_config.get('model', 'gemma2:2b'),
                    host=ollama_config.get('host', 'http://localhost:11434')
                )
                print(f"[Dashboard] Ollama client initialized with model: {ollama_config.get('model')}")
                
                # Initialize agent with Ollama
                self.agent = DecypherTekAgent(
                    ai_client=self.ai_client,
                    provider='ollama',
                    enable_tools=True,
                    doc_manager=self.document_manager,
                    page=self.page
                )
                print(f"[Dashboard] Agent initialized with Ollama")
            else:
                print("[Dashboard] Ollama selected but not configured")
                
        elif provider == 'duckduckgo':
            # Initialize DuckDuckGo client (FREE!)
            duckduckgo_config = self.api_key_manager.get_duckduckgo_config()
            model = duckduckgo_config.get('model', 'gpt-4o-mini') if duckduckgo_config else 'gpt-4o-mini'
            
            self.ai_client = DuckDuckGoClient(model=model)
            print(f"[Dashboard] DuckDuckGo client initialized with model: {model}")
            
            # Initialize agent with DuckDuckGo
            self.agent = DecypherTekAgent(
                ai_client=self.ai_client,
                provider='duckduckgo',
                enable_tools=True,
                doc_manager=self.document_manager,
                page=self.page
            )
            print(f"[Dashboard] Agent initialized with DuckDuckGo")
            
        else:
            # Initialize OpenRouter client (default)
            config = self.api_key_manager.get_openrouter_config()
            if config:
                self.ai_client = OpenRouterClient(
                    api_key=config['api_key'],
                    model=config['model'],
                    base_url=config['base_url']
                )
                print(f"[Dashboard] OpenRouter client initialized with model: {config['model']}")
                
                # Initialize agent with OpenRouter
                self.agent = DecypherTekAgent(
                    ai_client=self.ai_client,
                    provider='openrouter',
                    enable_tools=True,
                    doc_manager=self.document_manager,
                    page=self.page
                )
                print(f"[Dashboard] Agent initialized with OpenRouter")
            else:
                print("[Dashboard] OpenRouter not configured")
    
    def build(self) -> ft.View:
        """Build the dashboard view"""
        
        # Start AI init in background on first build
        if not self._ai_init_started:
            self._ai_init_started = True
            import threading
            def _bg_init():
                try:
                    self._init_ai_client()
                    # If chat view already built, refresh it to bind agent
                    if self.chat_view:
                        self.chat_view.agent = self.agent
                    self.page.update()
                except Exception as e:
                    print(f"[Dashboard] Background AI init error: {e}")
            threading.Thread(target=_bg_init, daemon=True).start()
        
        # Content area
        self.content_area = ft.Container(
            content=self._build_chat_tab(),
            expand=True
        )
        
        # Build navigation destinations
        destinations = [
            ft.NavigationBarDestination(
                icon=ft.icons.CHAT_BUBBLE_OUTLINE,
                selected_icon=ft.icons.CHAT_BUBBLE,
                label="Chat"
            ),
            ft.NavigationBarDestination(
                icon=ft.icons.STORAGE_OUTLINED,
                selected_icon=ft.icons.STORAGE,
                label="RAG"
            ),
            ft.NavigationBarDestination(
                icon=ft.icons.CLOUD_OUTLINED,
                selected_icon=ft.icons.CLOUD,
                label="MCP"
            ),
            ft.NavigationBarDestination(
                icon=ft.icons.SMART_TOY_OUTLINED,
                selected_icon=ft.icons.SMART_TOY,
                label="Agents"
            ),
        ]
        
        # Add apps destination (always show apps tab)
        destinations.append(
            ft.NavigationBarDestination(
                icon=ft.icons.APPS_OUTLINED,
                selected_icon=ft.icons.APPS,
                label="Apps"
            )
        )
        
        # Settings is always the rightmost icon
        destinations.append(
            ft.NavigationBarDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon=ft.icons.SETTINGS,
                label="Settings"
            )
        )
        
        # Bottom navigation
        self.navigation_bar = ft.NavigationBar(
            selected_index=0,
            on_change=self._on_nav_change,
            destinations=destinations
        )
        
        return ft.View(
            route="/dashboard",
            padding=0,
            controls=[
                self.content_area,
                self.navigation_bar
            ]
        )
    
    def _on_nav_change(self, e):
        """Handle navigation bar selection"""
        if self.showing_api_settings:
            return  # Don't change tab while in settings
        
        self.current_index = e.control.selected_index
        
        # Update content based on selection
        if self.current_index == 0:
            self.content_area.content = self._build_chat_tab()
        elif self.current_index == 1:
            self.content_area.content = self._build_rag_tab()
        elif self.current_index == 2:
            self.content_area.content = self._build_mcp_tab()
        elif self.current_index == 3:
            self.content_area.content = self._build_agents_tab()
        elif self.current_index == 4:
            # Admin tab - build admin content within dashboard
            self.content_area.content = self._build_admin_tab()
        elif self.current_index == 5:
            # Settings tab (always at index 5 now)
            self.content_area.content = self._build_settings_tab()
        
        self.page.update()
    
    def _build_chat_tab(self) -> ft.Control:
        """Build chat tab"""
        
        # Check if API key is configured
        if not self.api_key_manager.has_openrouter_key():
            return self._build_api_setup_prompt()
        
        # Proceed to build full chat view; agent binds when background init completes
        
        # Build chat view
        if not self.chat_view:
            # Initialize Adminotaur agent for RAG integration
            self._init_adminotaur_agent()
            
            self.chat_view = ChatView(
                self.page,
                self.ai_client,
                self.document_manager,
                on_settings_click=lambda e, open_ollama=False: self._show_api_settings(open_ollama=open_ollama),
                api_key_manager=self.api_key_manager,
                agent=self.adminotaur_agent,  # Pass Adminotaur agent for RAG integration
                on_document_uploaded=self._refresh_rag_view,  # Callback to refresh RAG view
                storage_dir=str(self.credential_manager.storage_dir),  # Pass storage directory for sessions
                chat_manager=self.chat_manager  # Pass chat manager for document uploads
            )
        
        return self.chat_view.build()
    
    def _build_api_setup_prompt(self) -> ft.Control:
        """Build prompt to set up API key"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(height=100),
                    ft.Icon(ft.icons.KEY, size=80, color=ft.colors.BLUE_300),
                    ft.Container(height=30),
                    ft.Text(
                        "Configure OpenRouter API",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=15),
                    ft.Text(
                        "To start chatting, add your OpenRouter API key",
                        size=16,
                        color=ft.colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=40),
                    ft.ElevatedButton(
                        "Configure API Key",
                        icon=ft.icons.SETTINGS,
                        on_click=lambda e: self._show_api_settings(),
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE,
                            color=ft.colors.WHITE,
                            padding=20
                        )
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            ),
            expand=True,
            alignment=ft.alignment.center
        )
    
    def _on_provider_change(self, e):
        """Handle AI provider selection change"""
        provider = e.control.value
        print(f"[Dashboard] Provider changed to: {provider}")
        
        # Save provider selection
        self.api_key_manager.set_ai_provider(provider)
        
        # Show notification
        provider_name = "Cloud AI (OpenRouter)" if provider == "openrouter" else "Local AI (Ollama)"
        snackbar = ft.SnackBar(
            content=ft.Text(f"✓ Switched to {provider_name}"),
            bgcolor=ft.colors.BLUE if provider == "openrouter" else ft.colors.PURPLE
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
        
        # Reinitialize AI client if needed
        # (Chat view will pick up the new provider on next message)
    
    def _show_api_settings(self, open_ollama=False):
        """Show OpenRouter API settings view or Ollama settings"""
        if open_ollama:
            self._show_ollama_settings()
            return
            
        self.showing_api_settings = True
        settings_view = APISettingsView(
            self.page,
            self.api_key_manager,
            on_save=self._on_api_settings_saved,
            on_back=self._on_api_settings_back
        )
        self.content_area.content = settings_view.build()
        self.page.update()
    
    def _show_ollama_settings(self):
        """Show Ollama configuration view with model browser"""
        self.showing_api_settings = True
        ollama_view = OllamaSettingsView(
            self.page,
            self.api_key_manager,
            on_save=self._on_ollama_settings_saved,
            on_back=self._on_api_settings_back
        )
        self.content_area.content = ollama_view.build()
        self.page.update()
    
    def _on_api_settings_saved(self):
        """Handle API settings saved"""
        # Reinitialize client
        self._init_ai_client()
        self.chat_view = None  # Reset chat view
        
        # Update document manager with new API key
        config = self.api_key_manager.get_openrouter_config()
        if config:
            self.document_manager.set_api_key(config['api_key'])
        
        # Return to chat
        self.showing_api_settings = False
        self.content_area.content = self._build_chat_tab()
        self.page.update()
    
    def _on_ollama_settings_saved(self):
        """Handle Ollama settings saved"""
        # Reinitialize client with new Ollama config
        self._init_ai_client()
        self.chat_view = None  # Reset chat view to pick up new client
        
        # Set provider to Ollama
        self.api_key_manager.set_ai_provider('ollama')
        
        # Return to chat view
        self.showing_api_settings = False
        self.content_area.content = self._build_chat_tab()
        self.page.update()

    def _on_api_settings_back(self):
        """Handle back from API settings"""
        self.showing_api_settings = False
        self.content_area.content = self._build_chat_tab()
        self.page.update()
    
    def _build_rag_tab(self) -> ft.Control:
        """Build RAG management tab"""
        if self._rag_tab_content is not None:
            return self._rag_tab_content
        if not self.rag_view:
            self.rag_view = RAGView(
                self.page,
                self.document_manager,
                on_install_mcp=self._show_mcp_installer
            )
        self._rag_tab_content = self.rag_view.build()
        return self._rag_tab_content
    
    def _refresh_rag_view(self):
        """Refresh RAG view when documents are uploaded via chat"""
        if self.rag_view and hasattr(self.rag_view, '_refresh_docs_list'):
            print("[Dashboard] Refreshing RAG view after document upload")
            self.rag_view._refresh_docs_list()
    
    def _build_mcp_tab(self) -> ft.Control:
        """Delegate MCP tab to isolated view."""
        if self._mcp_tab_content is not None:
            return self._mcp_tab_content
        self._mcp_tab_content = MCPStoreView(self.page).build()
        return self._mcp_tab_content
    
    def _create_mcp_server_card(self, title: str, description: str, icon, color, server_id: str, connected: bool = False):
        """Create an MCP server card with connection status"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=24, color=color),
                ft.Column([
                    ft.Row([
                        ft.Text(title, size=14, weight=ft.FontWeight.W_500),
                        ft.Icon(
                            ft.icons.CHECK_CIRCLE if connected else ft.icons.CIRCLE_OUTLINED,
                            size=14,
                            color=ft.colors.GREEN if connected else ft.colors.GREY_400
                        ),
                    ], spacing=5),
                    ft.Text(description, size=11, color=ft.colors.GREY_600),
                ], spacing=2, expand=True),
                ft.Row([
                    ft.IconButton(
                        icon=ft.icons.SETTINGS if connected else ft.icons.ADD,
                        tooltip="Configure" if connected else "Connect",
                        icon_color=ft.colors.BLUE if connected else ft.colors.GREEN,
                        on_click=lambda e: self._show_mcp_installer(server_id)
                    ),
                ]),
            ]),
            bgcolor=ft.colors.GREEN_50 if connected else ft.colors.SURFACE_VARIANT,
            border_radius=8,
            padding=10
        )
    
    def _get_available_servers(self):
        """Get available MCP servers from store"""
        # This will load from your mcp-store directory
        return [
            {
                "id": "web-search",
                "name": "Web Search",
                "description": "Search the web using Python",
                "icon": ft.icons.SEARCH,
                "color": ft.colors.GREEN
            },
            {
                "id": "nextcloud",
                "name": "Nextcloud",
                "description": "Access Nextcloud files and folders",
                "icon": ft.icons.CLOUD,
                "color": ft.colors.BLUE
            },
            {
                "id": "google-drive",
                "name": "Google Drive",
                "description": "Import documents from Google Drive",
                "icon": ft.icons.FOLDER,
                "color": ft.colors.GREEN
            },
            {
                "id": "google-voice",
                "name": "Google Voice",
                "description": "Send and receive messages via Google Voice",
                "icon": ft.icons.PHONE,
                "color": ft.colors.ORANGE
            },
            {
                "id": "whatsapp",
                "name": "WhatsApp",
                "description": "Send messages via WhatsApp",
                "icon": ft.icons.MESSAGE,
                "color": ft.colors.GREEN
            },
        ]
    
    def _get_connected_servers(self):
        """Get list of connected server IDs"""
        # TODO: Load from config file
        # For now, return empty list
        return []
    
    def _is_smithery_configured(self):
        """Check if Smithery is configured"""
        # TODO: Check for API key in config
        return False
    
    def _show_smithery_config(self):
        """Show Smithery API configuration dialog"""
        api_key_field = ft.TextField(
            label="Smithery API Key",
            hint_text="sk-smithery-...",
            password=True,
            can_reveal_password=True,
        )
        
        server_url_field = ft.TextField(
            label="Server URL (optional)",
            hint_text="http://localhost:8000",
        )
        
        def save_config(e):
            if not api_key_field.value:
                # Show warning
                return
            
            # TODO: Save to config
            self.page.close(dialog)
            snackbar = ft.SnackBar(
                content=ft.Text("✓ Smithery configured!"),
                bgcolor=ft.colors.GREEN
            )
            self.page.overlay.append(snackbar)
            snackbar.open = True
            self._refresh_mcp_tab()
        
        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.ROCKET_LAUNCH, color=ft.colors.PURPLE),
                ft.Text("Configure Smithery"),
            ]),
            content=ft.Column([
                ft.Text("Enter your Smithery API credentials", size=12, color=ft.colors.GREY_600),
                ft.Container(height=15),
                api_key_field,
                ft.Container(height=10),
                server_url_field,
                ft.Container(height=15),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Quick Start:", size=11, weight=ft.FontWeight.BOLD),
                        ft.Text("• Get your API key from smithery.ai", size=10),
                        ft.Text("• Or run locally: uv run smithery dev", size=10),
                    ]),
                    bgcolor=ft.colors.GREY_100,
                    border_radius=5,
                    padding=10
                ),
            ], tight=True, height=350),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Save",
                    icon=ft.icons.SAVE,
                    on_click=save_config,
                    style=ft.ButtonStyle(bgcolor=ft.colors.PURPLE, color=ft.colors.WHITE)
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_custom_store_browser(self):
        """Show custom MCP store browser"""
        dialog = ft.AlertDialog(
            title=ft.Text("🔍 Browse Custom MCP Store"),
            content=ft.Column([
                ft.Text("Enter your GitHub repository URL:", size=12, color=ft.colors.GREY_600),
                ft.Container(height=10),
                ft.TextField(
                    label="GitHub URL",
                    hint_text="https://github.com/decyphertek-io/mcp-server",
                    value="https://github.com/decyphertek-io/mcp-server",
                ),
                ft.Container(height=15),
                ft.Text("This will fetch available MCP servers from your repository", 
                        size=11, italic=True, color=ft.colors.GREY_600),
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Fetch Servers",
                    icon=ft.icons.DOWNLOAD,
                    on_click=lambda e: self._fetch_custom_servers(dialog),
                    style=ft.ButtonStyle(bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _load_default_mcp_store(self):
        """Load default MCP store"""
        snackbar = ft.SnackBar(
            content=ft.Text("✓ Loaded default MCP store: github.com/decyphertek-io/mcp-server"),
            bgcolor=ft.colors.GREEN
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def _fetch_custom_servers(self, dialog):
        """Fetch servers from custom store"""
        self.page.close(dialog)
        snackbar = ft.SnackBar(
            content=ft.Text("⏳ Fetching MCP servers... (Coming soon)"),
            bgcolor=ft.colors.BLUE
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def _refresh_mcp_tab(self):
        """Refresh MCP tab"""
        self.content_area.content = self._build_mcp_tab()
        self.page.update()
    
    def _build_agents_tab(self) -> ft.Control:
        """Delegate Agents tab to AgentStoreView to avoid blocking and isolate logic."""
        if self._agents_tab_content is not None:
            return self._agents_tab_content
        from ui.agent_store import AgentStoreView
        self._agents_tab_content = AgentStoreView(self.page, self.store_manager).build()
        return self._agents_tab_content

    def _agents_add_custom_store(self):
        url_field = ft.TextField(
            label="Raw personality.json URL",
            hint_text="https://raw.githubusercontent.com/your-org/agent-store/main/personality.json",
            value="",
            expand=True
        )

        def apply_url(_):
            url = url_field.value.strip()
            if url:
                self.store_manager.set_registry_url(url)
                self.store_manager.fetch_registry()
                self.page.close(dialog)
                self._refresh_agents_tab()

        dialog = ft.AlertDialog(
            title=ft.Text("Add custom Agent Store"),
            content=url_field,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton("Apply", icon=ft.icons.CHECK, on_click=apply_url),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _create_agent_card(self, title: str, description: str, icon, color, agent_id: str, active: bool = False):
        """Create an agent card with activation status"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=24, color=color),
                ft.Column([
                    ft.Row([
                        ft.Text(title, size=14, weight=ft.FontWeight.W_500),
                        ft.Icon(
                            ft.icons.PLAY_CIRCLE if active else ft.icons.CIRCLE_OUTLINED,
                            size=14,
                            color=ft.colors.GREEN if active else ft.colors.GREY_400
                        ),
                    ], spacing=5),
                    ft.Text(description, size=11, color=ft.colors.GREY_600),
                ], spacing=2, expand=True),
                ft.Row([
                    ft.IconButton(
                        icon=ft.icons.STOP if active else ft.icons.PLAY_ARROW,
                        tooltip="Stop" if active else "Start",
                        icon_color=ft.colors.RED if active else ft.colors.GREEN,
                        on_click=lambda e: self._toggle_agent(agent_id)
                    ),
                    ft.IconButton(
                        icon=ft.icons.SETTINGS,
                        tooltip="Configure",
                        on_click=lambda e: self._show_agent_config(agent_id)
                    ),
                ]),
            ]),
            bgcolor=ft.colors.GREEN_50 if active else ft.colors.SURFACE_VARIANT,
            border_radius=8,
            padding=10,
            margin=ft.margin.only(bottom=10)
        )
    
    def _get_agent_templates(self):
        """Get available agent templates"""
        return [
            {
                "id": "rag-qa",
                "name": "RAG Q&A Agent",
                "description": "Question answering with document retrieval",
                "icon": ft.icons.QUESTION_ANSWER,
                "color": ft.colors.BLUE
            },
            {
                "id": "tool-calling",
                "name": "Tool Calling Agent",
                "description": "Agent that can use external tools",
                "icon": ft.icons.BUILD,
                "color": ft.colors.ORANGE
            },
            {
                "id": "conversational",
                "name": "Conversational Agent",
                "description": "Chat agent with memory and context",
                "icon": ft.icons.CHAT,
                "color": ft.colors.GREEN
            },
            {
                "id": "sql-query",
                "name": "SQL Query Agent",
                "description": "Natural language to SQL queries",
                "icon": ft.icons.TABLE_CHART,
                "color": ft.colors.PURPLE
            },
        ]
    
    def _get_active_agents(self):
        """Get list of active agent IDs"""
        # TODO: Load from config
        return []
    
    def _is_langchain_configured(self):
        """Check if LangChain is configured (needs OpenRouter API)"""
        return self.api_key_manager.has_openrouter_key()
    
    def _show_agent_store_browser(self):
        """Show agent store browser"""
        snackbar = ft.SnackBar(
            content=ft.Text("⏳ Loading agents from ./agent-store... (Coming soon)"),
            bgcolor=ft.colors.BLUE
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def _show_create_agent_dialog(self):
        """Show create new agent dialog"""
        dialog = ft.AlertDialog(
            title=ft.Text("📝 Create New Agent"),
            content=ft.Column([
                ft.Text("Create a custom LangChain agent", size=12, color=ft.colors.GREY_600),
                ft.Container(height=10),
                ft.TextField(label="Agent Name", hint_text="My Custom Agent"),
                ft.Container(height=10),
                ft.TextField(
                    label="Description",
                    hint_text="What does this agent do?",
                    multiline=True,
                    min_lines=2
                ),
                ft.Container(height=10),
                ft.Dropdown(
                    label="Template",
                    options=[
                        ft.dropdown.Option("rag", "RAG Q&A"),
                        ft.dropdown.Option("tools", "Tool Calling"),
                        ft.dropdown.Option("conversational", "Conversational"),
                        ft.dropdown.Option("custom", "Custom"),
                    ],
                    value="conversational"
                ),
            ], tight=True, height=350),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Create",
                    icon=ft.icons.ADD,
                    on_click=lambda e: self._create_agent(dialog),
                    style=ft.ButtonStyle(bgcolor=ft.colors.GREEN, color=ft.colors.WHITE)
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _toggle_agent(self, agent_id: str):
        """Toggle agent active/inactive"""
        snackbar = ft.SnackBar(
            content=ft.Text(f"⏳ Toggling agent {agent_id}... (Coming soon)"),
            bgcolor=ft.colors.BLUE
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def _show_agent_config(self, agent_id: str):
        """Show agent configuration"""
        snackbar = ft.SnackBar(
            content=ft.Text(f"⚙️ Configuring agent {agent_id}... (Coming soon)"),
            bgcolor=ft.colors.BLUE
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def _create_agent(self, dialog):
        """Create new agent"""
        self.page.close(dialog)
        snackbar = ft.SnackBar(
            content=ft.Text("✓ Agent created! (Coming soon)"),
            bgcolor=ft.colors.GREEN
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def _refresh_agents_tab(self):
        """Refresh agents tab"""
        self.content_area.content = self._build_agents_tab()
        self.page.update()
    
    def _build_admin_tab(self) -> ft.Control:
        """Build Apps tab content via app_store view"""
        if self._apps_tab_content is not None:
            return self._apps_tab_content
        from ui.app_store import AdminView
        admin_view = AdminView(self.page, lambda: None, self.store_manager)
        admin_content = admin_view.build()
        self._apps_tab_content = ft.Container(
            content=admin_content.content,
            expand=True,
            padding=0
        )
        return self._apps_tab_content
    
    def _build_settings_tab(self) -> ft.Control:
        """Build settings tab"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    # AppBar
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.SETTINGS, size=28),
                                ft.Text(
                                    "Settings",
                                    size=22,
                                    weight=ft.FontWeight.BOLD
                                ),
                            ]
                        ),
                        padding=15,
                        bgcolor=ft.colors.SURFACE_VARIANT
                    ),
                    
                    # Settings list
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=20),
                                
                                # Account section
                                ft.Text(
                                    "Account",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.GREY_600
                                ),
                                ft.ListTile(
                                    leading=ft.Icon(ft.icons.PERSON),
                                    title=ft.Text("Username"),
                                    subtitle=ft.Text(self.username),
                                ),
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.LOCK),
                                title=ft.Text("Change Password"),
                                trailing=ft.Icon(ft.icons.CHEVRON_RIGHT),
                                on_click=lambda e: None  # TODO: Implement
                            ),
                            
                            ft.Divider(height=30),
                            
                            # AI Provider section
                            ft.Text(
                                "AI Provider",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.GREY_600
                            ),
                            ft.Container(
                                content=ft.Column([
                                    ft.RadioGroup(
                                        content=ft.Column([
                                            ft.Radio(
                                                value="openrouter",
                                                label="Cloud AI (OpenRouter)",
                                            ),
                                            ft.Text(
                                                "100+ models • Best for battery • Internet required",
                                                size=11,
                                                color=ft.colors.GREY_600,
                                                italic=True
                                            ),
                                            ft.Container(height=10),
                                            ft.Radio(
                                                value="duckduckgo",
                                                label="DuckDuckGo AI (FREE!)",
                                            ),
                                            ft.Text(
                                                "Free • No API key • 5 models • Internet required",
                                                size=11,
                                                color=ft.colors.GREY_600,
                                                italic=True
                                            ),
                                            ft.Container(height=10),
                                            ft.Radio(
                                                value="ollama",
                                                label="Local AI (Ollama)",
                                            ),
                                            ft.Text(
                                                "Privacy focused • Works offline • Higher battery usage",
                                                size=11,
                                                color=ft.colors.GREY_600,
                                                italic=True
                                            ),
                                        ]),
                                        value=self.api_key_manager.get_ai_provider(),
                                        on_change=self._on_provider_change
                                    ),
                                ]),
                                bgcolor=ft.colors.SURFACE_VARIANT,
                                border_radius=10,
                                padding=15
                            ),
                            
                            ft.Divider(height=30),
                            
                            # API Configuration section
                            ft.Text(
                                "API Configuration",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.GREY_600
                            ),
                            ft.ListTile(
                                leading=ft.Icon(
                                    ft.icons.CHECK_CIRCLE if self.api_key_manager.has_openrouter_key() 
                                    else ft.icons.WARNING,
                                    color=ft.colors.GREEN if self.api_key_manager.has_openrouter_key() 
                                    else ft.colors.ORANGE
                                ),
                                title=ft.Text("OpenRouter API Key"),
                                subtitle=ft.Text(
                                    "Configured" if self.api_key_manager.has_openrouter_key() 
                                    else "Not configured"
                                ),
                                trailing=ft.Icon(ft.icons.CHEVRON_RIGHT),
                                on_click=lambda e: self._show_api_settings()
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.COMPUTER, color=ft.colors.PURPLE),
                                title=ft.Text("Ollama Configuration"),
                                subtitle=ft.Text("Host, model selection & browser"),
                                trailing=ft.Icon(ft.icons.CHEVRON_RIGHT),
                                on_click=lambda e: self._show_ollama_settings()
                            ),
                            
                            ft.Divider(height=30),
                            
                            # About section
                            ft.Text(
                                "About",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.GREY_600
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.INFO),
                                title=ft.Text("Version"),
                                subtitle=ft.Text("1.0.0"),
                            ),
                            
                            ft.Container(height=30),
                            
                            # Logout button
                                ft.Container(
                                    content=ft.ElevatedButton(
                                        "Logout",
                                        icon=ft.icons.LOGOUT,
                                        on_click=self._on_logout_click,
                                        style=ft.ButtonStyle(
                                            color=ft.colors.RED_400
                                        )
                                    ),
                                    alignment=ft.alignment.center
                                ),
                            ],
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        padding=20,
                        expand=True,
                    ),
                ],
                expand=True
            ),
            expand=True
        )
    
    def _on_logout_click(self, e):
        """Handle logout"""
        # Show confirmation dialog
        dialog = ft.AlertDialog(
            title=ft.Text("Logout"),
            content=ft.Text("Are you sure you want to logout?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.TextButton(
                    "Logout",
                    on_click=lambda e: self._confirm_logout(dialog)
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _confirm_logout(self, dialog):
        """Confirm and execute logout"""
        self.page.close(dialog)
        self.on_logout()
    
    def _show_mcp_installer(self, server_name: str):
        """Show MCP server installation dialog"""
        # MCP server info
        mcp_info = {
            "nextcloud": {
                "title": "Nextcloud MCP Server",
                "description": "Connect to your Nextcloud instance to import files and folders",
                "github": "https://github.com/decyphertek-io/mcp-server/tree/main/mcp/nextcloud",
                "icon": ft.icons.CLOUD,
                "color": ft.colors.BLUE
            },
            "google-drive": {
                "title": "Google Drive MCP Server",
                "description": "Connect to Google Drive to import documents",
                "github": "https://github.com/modelcontextprotocol/servers/tree/main/src/gdrive",
                "icon": ft.icons.FOLDER,
                "color": ft.colors.GREEN
            }
        }
        
        info = mcp_info.get(server_name, {})
        if not info:
            return
        
        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(info["icon"], color=info["color"]),
                ft.Text(info["title"]),
            ]),
            content=ft.Column([
                ft.Text(info["description"]),
                ft.Container(height=10),
                ft.Text("This feature is coming soon!", size=12, italic=True, color=ft.colors.GREY_600),
                ft.Container(height=10),
                ft.Text("GitHub Repository:", size=12, weight=ft.FontWeight.BOLD),
                ft.TextButton(
                    info["github"],
                    on_click=lambda e: self.page.launch_url(info["github"]),
                    style=ft.ButtonStyle(color=ft.colors.BLUE)
                ),
            ], tight=True),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.page.close(dialog)),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
