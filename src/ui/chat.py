
"""
Chat interface for OpenRouter AI with session management
"""

import flet as ft
from typing import List, Dict
import inspect
import subprocess
import json
import os
from pathlib import Path
import asyncio
from chat.chat_sessions import ChatSessionManager


class ChatView:
    """Clean, professional chat interface"""
    
    def __init__(self, page: ft.Page, openrouter_client, document_manager, on_settings_click, api_key_manager=None, agent=None, storage_dir=None, on_document_uploaded=None):
        """
        Initialize chat view
        
        Args:
            page: Flet page
            openrouter_client: OpenRouter client instance
            document_manager: Document manager for RAG
            on_settings_click: Callback for settings button
            api_key_manager: API key manager for provider switching
            agent: DecypherTekAgent for tool use (optional)
            storage_dir: Storage directory for chat sessions
            on_document_uploaded: Callback when document is uploaded (for RAG view refresh)
        """
        self.page = page
        self.client = openrouter_client
        self.doc_manager = document_manager
        self.on_settings_click = on_settings_click
        self.api_key_manager = api_key_manager
        self.agent = agent
        self.on_document_uploaded = on_document_uploaded
        
        # Initialize session manager
        self.session_manager = ChatSessionManager(storage_dir or "/tmp")
        
        # AI Provider state - Default to OpenRouter
        self.current_provider = 'openrouter'
        if api_key_manager:
            provider = api_key_manager.get_ai_provider()
            self.current_provider = provider if provider in ['openrouter', 'ollama', 'duckduckgo'] else 'openrouter'
        
        print(f"[Chat] AI Provider initialized: {self.current_provider}")
        
        # Chat state
        self.messages: List[Dict[str, str]] = []
        self.chat_list = None
        self.input_field = None
        self.send_button = None
        self.docs_button = None
        self.rag_toggle = None
        self.ollama_toggle = None
        self.use_rag = True  # RAG enabled by default
        self.editor_open = False  # Track editor state
        self.show_thinking = True  # Show thinking by default
        
        # Sidebar state
        self.sidebar_visible = False
        self.sidebar = None
        self.sessions_list = None
        
        # File picker for document upload
        self.file_picker = ft.FilePicker(
            on_result=self._on_file_picked
        )
        self.page.overlay.append(self.file_picker)
    
    def build(self) -> ft.Row:
        """Build chat interface with sidebar"""
        
        # Chat messages list
        self.chat_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            auto_scroll=True
        )
        
        # Input field
        self.input_field = ft.TextField(
            hint_text="Type your message...",
            multiline=True,
            min_lines=1,
            max_lines=4,
            shift_enter=True,
            expand=True,
            on_submit=self._on_send_click,
            border_color=ft.colors.BLUE_200,
            color=ft.colors.WHITE,
            hint_style=ft.TextStyle(color=ft.colors.GREY_400),
        )
        
        # Send button
        self.send_button = ft.IconButton(
            icon=ft.icons.SEND,
            icon_color=ft.colors.BLUE,
            tooltip="Send message",
            on_click=self._on_send_click
        )
        
        # Docs button (paper icon for troubleshooting notes)
        self.docs_button = ft.IconButton(
            icon=ft.icons.DESCRIPTION,
            icon_color=ft.colors.ORANGE,
            tooltip="Troubleshooting Notes & Commands",
            on_click=self._on_docs_click
        )
        
        # Terminal button (terminal icon for command line access)
        self.terminal_button = ft.IconButton(
            icon=ft.icons.TERMINAL,
            icon_color=ft.colors.GREEN,
            tooltip="Terminal Emulator",
            on_click=self._on_terminal_click
        )
        
        # Build sidebar
        self.sidebar = self._build_sidebar()
        
        # Main chat column
        chat_column = ft.Column(
            controls=[
                # App bar
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.MENU,
                                icon_size=24,
                                tooltip="Chat History",
                                on_click=self._toggle_sidebar
                            ),
                            ft.Container(expand=True),
                            # New chat button
                            ft.IconButton(
                                icon=ft.icons.ADD,
                                icon_size=24,
                                tooltip="New Chat",
                                on_click=self._on_new_chat
                            ),
                            # Provider selector (3 providers)
                            ft.PopupMenuButton(
                                items=[
                                    ft.PopupMenuItem(
                                        text="OpenRouter (Cloud)",
                                        icon=ft.icons.CLOUD,
                                        checked=self.current_provider == 'openrouter',
                                        on_click=lambda e: self._switch_provider('openrouter')
                                    ),
                                    ft.PopupMenuItem(
                                        text="DuckDuckGo (FREE!)",
                                        icon=ft.icons.PETS,
                                        checked=self.current_provider == 'duckduckgo',
                                        on_click=lambda e: self._switch_provider('duckduckgo')
                                    ),
                                    ft.PopupMenuItem(
                                        text="Ollama (Local)",
                                        icon=ft.icons.COMPUTER,
                                        checked=self.current_provider == 'ollama',
                                        on_click=lambda e: self._switch_provider('ollama')
                                    ),
                                ],
                                icon=ft.icons.CLOUD if self.current_provider == 'openrouter' 
                                     else ft.icons.PETS if self.current_provider == 'duckduckgo'
                                     else ft.icons.COMPUTER,
                                tooltip=f"AI Provider: {self.current_provider.capitalize()}"
                            ),
                            ft.IconButton(
                                icon=ft.icons.SETTINGS,
                                icon_size=24,
                                tooltip="Settings",
                                on_click=self.on_settings_click
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    padding=15,
                    bgcolor=ft.colors.SURFACE_VARIANT
                ),
                
                # Chat area
                ft.Container(
                    content=self.chat_list,
                    expand=True,
                    bgcolor=ft.colors.SURFACE
                ),
                
                # Input area
                ft.Container(
                    content=ft.Column(
                        controls=[
                            # Thinking toggle and settings row
                            ft.Row(
                                controls=[
                                    # Thinking toggle
                                    ft.Row(
                                        controls=[
                                            ft.Icon(
                                                ft.icons.PSYCHOLOGY,
                                                size=16,
                                                color=ft.colors.BLUE_600 if self.show_thinking else ft.colors.GREY_400
                                            ),
                                            ft.Text(
                                                "Show thinking",
                                                size=12,
                                                color=ft.colors.BLUE_600 if self.show_thinking else ft.colors.GREY_400
                                            ),
                                            ft.Switch(
                                                value=self.show_thinking,
                                                on_change=self._toggle_thinking,
                                                active_color=ft.colors.BLUE_400,
                                            )
                                        ],
                                        spacing=8,
                                        alignment=ft.MainAxisAlignment.START
                                    ),
                                    ft.Container(expand=True),
                                    # Quick settings gear
                                    ft.IconButton(
                                        icon=ft.icons.SETTINGS,
                                        icon_size=20,
                                        tooltip="Quick Model Settings",
                                        on_click=self._show_quick_settings
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            # Input row
                            ft.Row(
                                controls=[
                                    # Upload button (paper clip)
                                    ft.IconButton(
                                        icon=ft.icons.ATTACH_FILE,
                                        icon_color=ft.colors.BLUE_600,
                                        tooltip="Upload Document to RAG",
                                        on_click=self._on_upload_click
                                    ),
                                    # Docs button (paper icon for troubleshooting notes)
                                    self.docs_button,
                                    # Terminal button (terminal icon for command line access)
                                    self.terminal_button,
                                    self.input_field,
                                    self.send_button
                                ],
                                spacing=10,
                            )
                        ],
                        spacing=8
                    ),
                    padding=15,
                    bgcolor=ft.colors.SURFACE_VARIANT
                ),
            ],
            spacing=0,
            expand=True
        )
        
        # Return row with sidebar and chat
        return ft.Row(
            controls=[
                self.sidebar,
                chat_column
            ],
            spacing=0,
            expand=True
        )
    
    def _on_upload_click(self, e):
        """Handle upload button click"""
        # Open file picker for document upload
        self.file_picker.pick_files(
            dialog_title="Select Document to Upload to RAG",
            allowed_extensions=["txt", "md", "json", "csv", "py", "js", "html", "css", "xml", "yaml", "yml"],
            allow_multiple=False
        )
    
    def _on_docs_click(self, e):
        """Handle docs button click - launch docs menu"""
        print("[Chat] Docs button clicked - launching docs menu!")
        try:
            if self.editor_open:
                # Close any open docs if already open
                print("[Chat] Docs already open, closing them")
                self._close_editor()
                return
            
            # Launch docs menu
            from ui.docs_menu import launch_docs_menu
            launch_docs_menu(self)
            self.editor_open = True
            
        except Exception as ex:
            print(f"[Chat] Error launching docs menu: {ex}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Error opening docs menu: {ex}"),
                    bgcolor=ft.colors.RED
                )
            )
    
    def _on_terminal_click(self, e):
        """Handle terminal button click - launch terminal emulator"""
        print("[Chat] Terminal button clicked - launching terminal!")
        try:
            if self.editor_open:
                # Close any open docs if already open
                print("[Chat] Terminal already open, closing it")
                self._close_editor()
                return
            
            # Launch terminal
            from ui.terminal import launch_terminal
            launch_terminal(self)
            self.editor_open = True
            
        except Exception as ex:
            print(f"[Chat] Error launching terminal: {ex}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Error opening terminal: {ex}"),
                    bgcolor=ft.colors.RED
                )
            )
    
    def _close_editor(self):
        """Close any open docs (editor, admin guide, docs viewer, or menu)"""
        try:
            # Remove any docs containers from chat list
            self.chat_list.controls = [control for control in self.chat_list.controls 
                                      if not (hasattr(control, 'editor_container') or 
                                             hasattr(control, 'admin_guide_container') or
                                             hasattr(control, 'docs_viewer_container') or
                                             hasattr(control, 'docs_menu_container') or
                                             hasattr(control, 'terminal_container'))]
            self.editor_open = False
            self.page.update()
            print("[Chat] Docs closed")
        except Exception as ex:
            print(f"[Chat] Error closing docs: {ex}")
    
    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file picker result"""
        if e.files:
            file = e.files[0]
            print(f"[Chat] File selected for upload: {file.name}")
            
            # Show upload message in chat
            self._add_message("system", f"📎 Uploading document: {file.name}")
            
            # Start upload in background thread
            import threading
            thread = threading.Thread(
                target=self._upload_document,
                args=(file,),
                daemon=True
            )
            thread.start()
    
    def _upload_document(self, file):
        """Upload document using RAG MCP server"""
        try:
            import asyncio
            asyncio.run(self._upload_document_async(file))
        except Exception as e:
            print(f"[Chat] Upload error: {e}")
            self._add_message("system", f"❌ Upload failed: {str(e)}")
    
    async def _upload_document_async(self, file):
        """Async document upload using RAG MCP server"""
        try:
            # Read file content
            with open(file.path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            print(f"[Chat] Uploading {file.name} ({len(content)} chars) to RAG")
            
            # Use RAG MCP server to upload document
            if self.agent and hasattr(self.agent, 'doc_manager') and self.agent.doc_manager:
                # Use built-in document manager
                success = await self.agent.doc_manager.add_document(
                    content=content,
                    filename=file.name,
                    source="chat_upload"
                )
                
                if success:
                    self._add_message("system", f"✅ Document '{file.name}' uploaded to RAG successfully!")
                    print(f"[Chat] Document {file.name} uploaded successfully")
                    
                    # Notify RAG view to refresh
                    if self.on_document_uploaded:
                        self.on_document_uploaded()
                else:
                    self._add_message("system", f"⚠️ Document '{file.name}' already exists in RAG database")
                    print(f"[Chat] Document {file.name} already exists")
                    
                    # Even if document already exists, refresh RAG view to show it
                    if self.on_document_uploaded:
                        self.on_document_uploaded()
            else:
                # Fallback: try to use RAG MCP server directly
                self._add_message("system", f"⚠️ RAG system not available - cannot upload document")
                print("[Chat] RAG system not available")
                
        except Exception as e:
            print(f"[Chat] Upload error: {e}")
            self._add_message("system", f"❌ Upload failed: {str(e)}")
    
    def _on_send_click(self, e):
        """Handle send button click"""
        import threading
        
        def send_in_thread():
            import asyncio
            asyncio.run(self._send_message())
        
        threading.Thread(target=send_in_thread, daemon=True).start()
    
    async def _send_message(self):
        """Send message to AI"""
        if not self.input_field.value or not self.input_field.value.strip():
            return
        
        user_message = self.input_field.value.strip()
        self.input_field.value = ""
        self.input_field.disabled = True
        self.send_button.disabled = True
        self.page.update()
        
        print(f"[Chat] Sending message: {user_message[:50]}...")
        
        # Add user message to chat
        self._add_message("user", user_message)
        
        # Add messages to history
        self.messages.append({"role": "user", "content": user_message})
        
        # Create AI message bubble with "thinking" indicator (if enabled)
        ai_bubble = None
        ai_bubble_index = -1
        if self.show_thinking:
            ai_bubble = self._create_message_bubble("assistant", "🤔 Thinking...")
            self.chat_list.controls.append(ai_bubble)
            ai_bubble_index = len(self.chat_list.controls) - 1  # Track position
            self.page.update()
        
        try:
            # Use ChatManager to process the message
            from agent.chat_manager import ChatManager
            chat_manager = ChatManager(
                page=self.page,
                ai_client=self.client,
                document_manager=self.doc_manager
            )
            
            print(f"[Chat] Processing message with ChatManager...")
            response = await chat_manager.process_message(
                user_message=user_message,
                message_history=self.messages,
                use_rag=self.use_rag
            )
            
            print(f"[Chat] Got response: {response[:100] if response else 'None'}...")
            
            if response:
                if self.show_thinking and ai_bubble_index >= 0:
                    # REPLACE the thinking bubble with the actual response
                    new_bubble = self._create_message_bubble("assistant", response)
                    self.chat_list.controls[ai_bubble_index] = new_bubble
                else:
                    # Add new message bubble (thinking was disabled)
                    self._add_message("assistant", response)
                self.messages.append({"role": "assistant", "content": response})
            else:
                if self.show_thinking and ai_bubble_index >= 0:
                    # Update thinking bubble with error
                    error_bubble = self._create_message_bubble("assistant", "⚠️ Error: Could not get response")
                    error_bubble.bgcolor = ft.colors.RED_100
                    self.chat_list.controls[ai_bubble_index] = error_bubble
                else:
                    # Add error message (thinking was disabled)
                    self._add_message("assistant", "⚠️ Error: Could not get response")
                
        except Exception as e:
            import traceback
            print(f"[Chat] An exception occurred: {type(e).__name__}: {e}")
            traceback.print_exc()  # Print the full traceback for debugging
            if self.show_thinking and ai_bubble_index >= 0:
                # Update thinking bubble with error
                error_bubble = self._create_message_bubble("assistant", f"⚠️ Error: {type(e).__name__}")
                error_bubble.bgcolor = ft.colors.RED_100
                self.chat_list.controls[ai_bubble_index] = error_bubble
            else:
                # Add error message (thinking was disabled)
                self._add_message("assistant", f"⚠️ Error: {type(e).__name__}")
        
        finally:
            self.input_field.disabled = False
            self.send_button.disabled = False
            self.page.update()
            print("[Chat] Message complete, UI re-enabled")

    
    def _add_message(self, role: str, content: str, save_to_session: bool = True):
        """Add message to chat display and optionally save to session"""
        bubble = self._create_message_bubble(role, content)
        self.chat_list.controls.append(bubble)
        
        # Save to session manager only if requested (not when loading history)
        if save_to_session:
            self.session_manager.add_message(role, content)
        
        self.page.update()
    
    def _create_message_bubble(self, role: str, content: str) -> ft.Container:
        """Create a message bubble with embedded YouTube videos"""
        import re
        
        # Define colors based on role
        is_user = role == "user"
        bg_color = ft.colors.GREY_700 if is_user else ft.colors.WHITE
        text_color = ft.colors.WHITE if is_user else ft.colors.BLACK
        
        # Detect YouTube URLs
        youtube_pattern = r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})'
        youtube_matches = list(re.finditer(youtube_pattern, content))
        
        bubble_controls = []
        
        # Add text content with dynamic color
        bubble_controls.append(
            ft.Text(
                content,
                size=14,
                selectable=True,
                color=text_color,
            )
        )
        
        # Add embedded YouTube players for each video found
        for match in youtube_matches:
            video_id = match.group(1)
            bubble_controls.append(
                ft.Container(
                    content=ft.Video(
                        playlist=[ft.VideoMedia(f"https://www.youtube.com/watch?v={video_id}")],
                        aspect_ratio=16/9,
                        volume=100,
                        autoplay=False,
                        show_controls=True,
                    ),
                    width=400,
                    height=225,
                    margin=ft.margin.only(top=10),
                )
            )
        
        # Return bubble with dynamic styling
        return ft.Container(
            content=ft.Column(
                controls=bubble_controls,
                spacing=5,
            ),
            bgcolor=bg_color,
            border_radius=12,
            padding=12,
            margin=ft.margin.only(bottom=8),
            alignment=ft.alignment.center_left,
        )
    
    def _open_url(self, url: str):
        """Open URL in browser"""
        import webbrowser
        print(f"[Chat] Opening URL: {url}")
        webbrowser.open(url)
    
    def _switch_provider(self, provider: str):
        """Switch between AI providers (openrouter, duckduckgo, ollama)"""
        
        # Check if Ollama needs configuration
        if provider == 'ollama':
            ollama_config = None
            if self.api_key_manager:
                ollama_config = self.api_key_manager.get_ollama_config()
            
            if not ollama_config:
                self._show_ollama_setup_dialog()
                return
        
        # Update provider
        self.current_provider = provider
        if self.api_key_manager:
            self.api_key_manager.set_ai_provider(provider)
        
        # Show notification
        provider_names = {
            'openrouter': ('OpenRouter (Cloud)', ft.colors.BLUE),
            'duckduckgo': ('DuckDuckGo AI (FREE!)', ft.colors.GREEN),
            'ollama': ('Ollama (Local)', ft.colors.PURPLE)
        }
        
        name, color = provider_names.get(provider, ('Unknown', ft.colors.GREY))
        
        snackbar = ft.SnackBar(
            content=ft.Text(f"✓ Switched to {name}"),
            bgcolor=color
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
        
        print(f"[Chat] Switched to {provider}")
    
    def _show_ollama_setup_dialog(self):
        """Navigate directly to Ollama model browser (no dialog - just go there)"""
        # Trigger settings click callback with 'ollama' flag
        if self.on_settings_click:
            self.on_settings_click(None, open_ollama=True)
    
    def _go_to_ollama_settings(self):
        """Navigate to Ollama settings"""
        # Trigger settings click callback with 'ollama' flag
        if self.on_settings_click:
            self.on_settings_click(None, open_ollama=True)
    
    def _toggle_rag(self, e):
        """Toggle RAG on/off"""
        self.use_rag = not self.use_rag
        
        # Update icon
        e.control.icon = ft.icons.STORAGE if self.use_rag else ft.icons.STORAGE_OUTLINED
        e.control.icon_color = ft.colors.GREEN if self.use_rag else ft.colors.GREY
        e.control.tooltip = "RAG: ON" if self.use_rag else "RAG: OFF"
        
        # Show notification
        snackbar = ft.SnackBar(
            content=ft.Text(f"RAG {'enabled' if self.use_rag else 'disabled'}"),
            bgcolor=ft.colors.GREEN if self.use_rag else ft.colors.GREY
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
        
        print(f"[Chat] RAG {'enabled' if self.use_rag else 'disabled'}")
    
    def _toggle_thinking(self, e):
        """Toggle thinking visibility on/off"""
        self.show_thinking = not self.show_thinking
        
        # Show notification
        snackbar = ft.SnackBar(
            content=ft.Text(f"Thinking {'enabled' if self.show_thinking else 'disabled'}"),
            bgcolor=ft.colors.BLUE if self.show_thinking else ft.colors.GREY
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
        
        print(f"[Chat] Thinking {'enabled' if self.show_thinking else 'disabled'}")
    
    def _show_quick_settings(self, e):
        """Show quick model settings dialog"""
        # Get current provider and available models
        current_provider = self.current_provider
        
        # Create provider selection
        provider_radio_group = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(value="openrouter", label="OpenRouter (Cloud)", active_color=ft.colors.BLUE),
                ft.Radio(value="duckduckgo", label="DuckDuckGo AI (FREE!)", active_color=ft.colors.GREEN),
                ft.Radio(value="ollama", label="Ollama (Local)", active_color=ft.colors.PURPLE),
            ]),
            value=current_provider,
            on_change=self._on_provider_change
        )
        
        # Create model selection based on current provider
        model_dropdown = self._create_model_dropdown(current_provider)
        
        def close_dialog(e):
            self.page.close(dialog)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Quick Model Settings"),
            content=ft.Column([
                ft.Text("AI Provider:", weight=ft.FontWeight.BOLD),
                provider_radio_group,
                ft.Divider(),
                ft.Text("Model:", weight=ft.FontWeight.BOLD),
                model_dropdown,
            ], spacing=10, height=300),
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_docs_overlay(self):
        """Show troubleshooting notes overlay with read-only commands and editable user notes"""
        
        # Read-only troubleshooting commands
        troubleshooting_notes = """# 🔧 Troubleshooting Commands & Notes

## System Health Checks
- `health-check` - Comprehensive system health check via adminotaur.py
- `verbose` - Detailed verbose system status from Chat Manager
- `!debug` - Debug information from Chat Manager

## Component Status Commands
- `sudo systemctl status chat_manager` - Chat Manager health check
- `sudo systemctl status agent` - Agent status report
- `sudo systemctl status mcp` - MCP servers status report
- `sudo systemctl status app` - Apps status report
- `sudo systemctl status agent-adminotaur` - Test adminotaur agent
- `sudo systemctl status mcp-web-search` - Test web-search MCP server

## MCP Server Management
- `sudo apt install mcp-web-search` - Install web-search MCP server
- `sudo apt reinstall mcp-web-search` - Reinstall web-search MCP server
- `!enable mcp web-search` - Enable web-search MCP server
- `!disable mcp web-search` - Disable web-search MCP server

## Agent Management
- `!enable agent adminotaur` - Enable adminotaur agent
- `!disable agent adminotaur` - Disable adminotaur agent
- `!list` - List all available components

## Quick Tips
- All normal chat goes through adminotaur.py when agent is enabled
- Use `health-check` for comprehensive system diagnostics
- Use `verbose` for detailed troubleshooting information
- MCP servers provide tools for the agent (web search, etc.)
- Store Manager handles downloads and installations
- Chat Manager routes messages and manages sessions

---
**Note:** Commands above are read-only. Add your own notes below."""

        # Load user notes from file
        user_notes_path = Path.home() / ".decyphertek-ai" / "user_notes.txt"
        user_notes_path.parent.mkdir(parents=True, exist_ok=True)
        
        user_notes = ""
        if user_notes_path.exists():
            try:
                user_notes = user_notes_path.read_text(encoding="utf-8")
            except Exception:
                user_notes = ""
        
        # Create text fields
        read_only_field = ft.TextField(
            value=troubleshooting_notes,
            read_only=True,
            multiline=True,
            min_lines=20,
            max_lines=20,
            border_color=ft.colors.GREY_300,
            bgcolor=ft.colors.GREY_50,
            text_style=ft.TextStyle(
                font_family="monospace",
                size=12
            )
        )
        
        user_notes_field = ft.TextField(
            value=user_notes,
            multiline=True,
            min_lines=10,
            max_lines=10,
            hint_text="Add your own troubleshooting notes here...",
            border_color=ft.colors.BLUE_300,
            text_style=ft.TextStyle(
                font_family="monospace",
                size=12
            )
        )
        
        def save_notes(e):
            """Save user notes to file"""
            try:
                user_notes_path.write_text(user_notes_field.value, encoding="utf-8")
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Notes saved successfully!"),
                        bgcolor=ft.colors.GREEN
                    )
                )
            except Exception as ex:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Error saving notes: {ex}"),
                        bgcolor=ft.colors.RED
                    )
                )
        
        def close_dialog(e):
            self.page.close(dialog)
        
        # Create dialog
        dialog = ft.AlertDialog(
            title=ft.Text("📋 Troubleshooting Notes & Commands"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Read-Only Commands:", weight=ft.FontWeight.BOLD),
                        read_only_field,
                        ft.Divider(),
                        ft.Text("Your Notes:", weight=ft.FontWeight.BOLD),
                        user_notes_field,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    height=600,
                    width=800
                ),
                padding=10
            ),
            actions=[
                ft.TextButton("Save Notes", on_click=save_notes),
                ft.TextButton("Close", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.add(dialog)
        self.page.update()
    
    def _create_model_dropdown(self, provider: str) -> ft.Dropdown:
        """Create model dropdown based on provider"""
        if provider == 'openrouter':
            models = [
                "qwen/qwen-2.5-coder-32b-instruct",
                "meta-llama/llama-3.1-405b-instruct",
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4o",
                "google/gemini-pro-1.5"
            ]
        elif provider == 'duckduckgo':
            models = [
                "gpt-4o-mini",
                "gpt-4o",
                "claude-3.5-sonnet",
                "llama-3.1-405b-instruct"
            ]
        else:  # ollama
            models = [
                "gemma2:2b",
                "gemma2:9b",
                "llama3.1:8b",
                "llama3.1:70b",
                "qwen2.5:7b",
                "qwen2.5:32b"
            ]
        
        # Get current model
        current_model = "qwen/qwen-2.5-coder-32b-instruct"  # Default
        if self.api_key_manager:
            if provider == 'openrouter':
                config = self.api_key_manager.get_openrouter_config()
                current_model = config.get('model', current_model) if config else current_model
            elif provider == 'duckduckgo':
                config = self.api_key_manager.get_duckduckgo_config()
                current_model = config.get('model', current_model) if config else current_model
            elif provider == 'ollama':
                config = self.api_key_manager.get_ollama_config()
                current_model = config.get('model', current_model) if config else current_model
        
        return ft.Dropdown(
            options=[ft.dropdown.Option(model) for model in models],
            value=current_model,
            on_change=lambda e: self._on_model_change(provider, e.control.value),
            expand=True
        )
    
    def _on_provider_change(self, e):
        """Handle provider change in quick settings"""
        new_provider = e.control.value
        if new_provider != self.current_provider:
            self._switch_provider(new_provider)
    
    def _on_model_change(self, provider: str, model: str):
        """Handle model change in quick settings"""
        if self.api_key_manager:
            if provider == 'openrouter':
                config = self.api_key_manager.get_openrouter_config()
                if config:
                    config['model'] = model
                    self.api_key_manager.save_openrouter_config(config)
            elif provider == 'duckduckgo':
                config = self.api_key_manager.get_duckduckgo_config()
                if config:
                    config['model'] = model
                    self.api_key_manager.save_duckduckgo_config(config)
            elif provider == 'ollama':
                config = self.api_key_manager.get_ollama_config()
                if config:
                    config['model'] = model
                    self.api_key_manager.save_ollama_config(config)
        
        # Show notification
        snackbar = ft.SnackBar(
            content=ft.Text(f"✓ Model changed to {model}"),
            bgcolor=ft.colors.BLUE
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
        
        print(f"[Chat] Model changed to {model} for {provider}")
    
    def clear_chat(self):
        """Clear chat history"""
        self.messages = []
        self.chat_list.controls.clear()
        self.page.update()
    
    def _build_sidebar(self) -> ft.Container:
        """Build chat history sidebar"""
        self.sessions_list = ft.ListView(
            spacing=5,
            padding=10,
            expand=True
        )
        
        # Load sessions
        self._refresh_sessions_list()
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Sidebar header
                    ft.Container(
                        content=ft.Text(
                            "Chat History",
                            size=16,
                            weight=ft.FontWeight.BOLD
                        ),
                        padding=15,
                        bgcolor=ft.colors.SURFACE_VARIANT
                    ),
                    # Sessions list
                    self.sessions_list,
                ],
                spacing=0
            ),
            width=250,
            bgcolor=ft.colors.SURFACE,
            border=ft.border.only(right=ft.BorderSide(1, ft.colors.OUTLINE_VARIANT)),
            visible=False  # Hidden by default
        )
    
    def _refresh_sessions_list(self):
        """Refresh the sessions list"""
        if not self.sessions_list:
            return
        
        self.sessions_list.controls.clear()
        sessions = self.session_manager.list_sessions()
        
        for session in sessions:
            self.sessions_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        session['title'],
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS
                                    ),
                                    ft.Text(
                                        f"{session['message_count']} messages",
                                        size=11,
                                        color=ft.colors.GREY_600
                                    ),
                                ],
                                spacing=2,
                                expand=True
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE,
                                icon_size=18,
                                tooltip="Delete",
                                on_click=lambda e, sid=session['id']: self._delete_session(sid)
                            )
                        ],
                        spacing=5
                    ),
                    padding=10,
                    border_radius=8,
                    bgcolor=ft.colors.BLUE_50 if session['id'] == self.session_manager.current_session_id else None,
                    on_click=lambda e, sid=session['id']: self._load_session(sid),
                    ink=True
                )
            )
        
        self.page.update()
    
    def _toggle_sidebar(self, e):
        """Toggle sidebar visibility"""
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar.visible = self.sidebar_visible
        self.page.update()
    
    def _on_new_chat(self, e):
        """Start a new chat"""
        # Clear current chat
        self.clear_chat()
        
        # Create new session
        self.session_manager.create_new_session()
        
        # Refresh sidebar
        self._refresh_sessions_list()
        
        print("[Chat] Started new chat session")
    
    def _load_session(self, session_id: str):
        """Load a chat session (display only, no API calls or re-saving)"""
        # Prevent loading if already current
        if session_id == self.session_manager.current_session_id and len(self.messages) > 0:
            print(f"[Chat] Session {session_id} already loaded, skipping")
            self.sidebar_visible = False
            self.sidebar.visible = False
            self.page.update()
            return
        
        # Load messages from file
        messages = self.session_manager.load_session(session_id)
        
        if not messages:
            print(f"[Chat] No messages in session {session_id}")
            return
        
        print(f"[Chat] Loading {len(messages)} messages from session {session_id}...")
        
        # Clear current chat UI and message list completely
        self.chat_list.controls.clear()
        self.messages = []
        self.page.update()
        
        # Rebuild chat UI from loaded messages (DISPLAY ONLY - no saving, no API calls)
        for i, msg in enumerate(messages):
            # Display message without saving (save_to_session=False)
            self._add_message(msg['role'], msg['content'], save_to_session=False)
            # Add to context for future AI messages (so AI can read conversation history)
            self.messages.append({"role": msg['role'], "content": msg['content']})
            print(f"[Chat] Loaded message {i+1}/{len(messages)}: {msg['role']}")
        
        # Refresh sidebar to highlight current session
        self._refresh_sessions_list()
        
        print(f"[Chat] ✓ Session loaded: {len(self.messages)} messages in context (no API calls made)")
        
        # Close sidebar after loading
        self.sidebar_visible = False
        self.sidebar.visible = False
        
        # Show success notification
        snackbar = ft.SnackBar(
            content=ft.Text(f"✓ Loaded {len(messages)} messages"),
            bgcolor=ft.colors.GREEN,
            duration=2000
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def _delete_session(self, session_id: str):
        """Delete a chat session"""
        # Show confirmation dialog
        def confirm_delete(e):
            if self.session_manager.delete_session(session_id):
                # If deleting current session, start new one
                if session_id == self.session_manager.current_session_id:
                    self._on_new_chat(None)
                else:
                    self._refresh_sessions_list()
            self.page.close(dialog)
        
        def cancel_delete(e):
            self.page.close(dialog)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Delete Chat?"),
            content=ft.Text("This action cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.colors.RED)),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_docs_overlay(self):
        """Show troubleshooting notes overlay with read-only commands and editable user notes"""
        
        # Read-only troubleshooting commands
        troubleshooting_notes = """# 🔧 Troubleshooting Commands & Notes

## System Health Checks
- `health-check` - Comprehensive system health check via adminotaur.py
- `verbose` - Detailed verbose system status from Chat Manager
- `!debug` - Debug information from Chat Manager

## Component Status Commands
- `sudo systemctl status chat_manager` - Chat Manager health check
- `sudo systemctl status agent` - Agent status report
- `sudo systemctl status mcp` - MCP servers status report
- `sudo systemctl status app` - Apps status report
- `sudo systemctl status agent-adminotaur` - Test adminotaur agent
- `sudo systemctl status mcp-web-search` - Test web-search MCP server

## MCP Server Management
- `sudo apt install mcp-web-search` - Install web-search MCP server
- `sudo apt reinstall mcp-web-search` - Reinstall web-search MCP server
- `!enable mcp web-search` - Enable web-search MCP server
- `!disable mcp web-search` - Disable web-search MCP server

## Agent Management
- `!enable agent adminotaur` - Enable adminotaur agent
- `!disable agent adminotaur` - Disable adminotaur agent
- `!list` - List all available components

## Quick Tips
- All normal chat goes through adminotaur.py when agent is enabled
- Use `health-check` for comprehensive system diagnostics
- Use `verbose` for detailed troubleshooting information
- MCP servers provide tools for the agent (web search, etc.)
- Store Manager handles downloads and installations
- Chat Manager routes messages and manages sessions

---
**Note:** Commands above are read-only. Add your own notes below."""

        # Load user notes from file
        user_notes_path = Path.home() / ".decyphertek-ai" / "user_notes.txt"
        user_notes_path.parent.mkdir(parents=True, exist_ok=True)
        
        user_notes = ""
        if user_notes_path.exists():
            try:
                user_notes = user_notes_path.read_text(encoding="utf-8")
            except Exception:
                user_notes = ""
        
        # Create text fields
        read_only_field = ft.TextField(
            value=troubleshooting_notes,
            read_only=True,
            multiline=True,
            min_lines=20,
            max_lines=20,
            border_color=ft.colors.GREY_300,
            bgcolor=ft.colors.GREY_50,
            text_style=ft.TextStyle(
                font_family="monospace",
                size=12
            )
        )
        
        user_notes_field = ft.TextField(
            value=user_notes,
            multiline=True,
            min_lines=10,
            max_lines=10,
            hint_text="Add your own troubleshooting notes here...",
            border_color=ft.colors.BLUE_300,
            text_style=ft.TextStyle(
                font_family="monospace",
                size=12
            )
        )
        
        def save_notes(e):
            """Save user notes to file"""
            try:
                user_notes_path.write_text(user_notes_field.value, encoding="utf-8")
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Notes saved successfully!"),
                        bgcolor=ft.colors.GREEN
                    )
                )
            except Exception as ex:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Error saving notes: {ex}"),
                        bgcolor=ft.colors.RED
                    )
                )
        
        def close_dialog(e):
            self.page.close(dialog)
        
        # Create dialog
        dialog = ft.AlertDialog(
            title=ft.Text("📋 Troubleshooting Notes & Commands"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Read-Only Commands:", weight=ft.FontWeight.BOLD),
                        read_only_field,
                        ft.Divider(),
                        ft.Text("Your Notes:", weight=ft.FontWeight.BOLD),
                        user_notes_field,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    height=600,
                    width=800
                ),
                padding=10
            ),
            actions=[
                ft.TextButton("Save Notes", on_click=save_notes),
                ft.TextButton("Close", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.add(dialog)
        self.page.update()

