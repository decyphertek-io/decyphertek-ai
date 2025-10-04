"""
Ollama Settings View - Model browser and configuration
"""

import flet as ft
from typing import Callable, Optional
import asyncio
import threading

from auth.api_keys import APIKeyManager
from chat.ollama_client import OllamaClient


class OllamaSettingsView:
    """View for configuring Ollama and browsing/installing models"""
    
    def __init__(self, page: ft.Page, api_key_manager: APIKeyManager, on_save: Callable, on_back: Callable):
        """
        Initialize Ollama settings view
        
        Args:
            page: Flet page
            api_key_manager: APIKeyManager instance
            on_save: Callback when settings are saved
            on_back: Callback when back button is pressed
        """
        self.page = page
        self.api_key_manager = api_key_manager
        self.on_save = on_save
        self.on_back = on_back
        
        # Get current config
        self.config = api_key_manager.get_ollama_config()
        self.host = self.config['host'] if self.config else "http://localhost:11434"
        self.current_model = self.config['model'] if self.config else None
        
        # UI elements
        self.host_field = None
        self.status_text = None
        self.models_list = None
        self.installed_models = []
        self.test_button = None
        
    def build(self) -> ft.Column:
        """Build the Ollama settings view"""
        
        # Host field
        self.host_field = ft.TextField(
            label="Ollama Server Host",
            hint_text="http://localhost:11434",
            value=self.host,
            border_color=ft.colors.PURPLE_200,
        )
        
        # Status text
        self.status_text = ft.Text(
            "",
            size=14,
            text_align=ft.TextAlign.CENTER,
        )
        
        # Test button
        self.test_button = ft.ElevatedButton(
            "Test Connection",
            icon=ft.icons.WIFI_FIND,
            on_click=self._on_test_click,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.PURPLE,
                color=ft.colors.WHITE
            )
        )
        
        # Models list
        self.models_list = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=10
        )
        
        return ft.Column(
            controls=[
                # App bar
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.ARROW_BACK,
                                on_click=lambda e: self.on_back()
                            ),
                            ft.Icon(ft.icons.COMPUTER, size=28, color=ft.colors.PURPLE),
                            ft.Text(
                                "Ollama Configuration",
                                size=22,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Container(expand=True),
                        ],
                        alignment=ft.MainAxisAlignment.START
                    ),
                    padding=15,
                    bgcolor=ft.colors.SURFACE_VARIANT
                ),
                
                # Settings form
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "Configure Ollama server and download models",
                                size=14,
                                color=ft.colors.GREY_600,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Container(height=20),
                            
                            self.host_field,
                            ft.Container(height=10),
                            self.test_button,
                            ft.Container(height=10),
                            self.status_text,
                            
                            ft.Container(height=20),
                            ft.Divider(),
                            ft.Container(height=10),
                            
                            # Models section
                            ft.Row([
                                ft.Text(
                                    "Available Models",
                                    size=18,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.Container(expand=True),
                                ft.IconButton(
                                    icon=ft.icons.REFRESH,
                                    tooltip="Refresh",
                                    on_click=self._refresh_models
                                ),
                            ]),
                            ft.Text(
                                "Download models to use with Ollama",
                                size=12,
                                color=ft.colors.GREY_600
                            ),
                            ft.Container(height=10),
                            
                            self.models_list,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    padding=20,
                    expand=True
                ),
            ],
            spacing=0,
            expand=True
        )
    
    def _on_test_click(self, e):
        """Handle test connection button click"""
        threading.Thread(target=lambda: asyncio.run(self._test_connection()), daemon=True).start()
    
    async def _test_connection(self):
        """Test Ollama connection and load models"""
        self.test_button.disabled = True
        self._show_status("Testing connection...", ft.colors.BLUE)
        
        try:
            # Create Ollama client
            client = OllamaClient(host=self.host_field.value.strip())
            
            # Test connection
            success, message = await client.test_connection()
            
            if success:
                self._show_status(f"✓ {message}", ft.colors.GREEN)
                
                # Load installed models
                self.installed_models = await client.get_available_models()
                
                # Save host
                self.host = self.host_field.value.strip()
                
                # Load model library
                self._load_model_library(client)
            else:
                self._show_status(f"✗ {message}", ft.colors.RED)
                
        except Exception as e:
            self._show_status(f"✗ Error: {str(e)}", ft.colors.RED)
        
        finally:
            self.test_button.disabled = False
            self.page.update()
    
    def _load_model_library(self, client: OllamaClient):
        """Load and display model library"""
        self.models_list.controls.clear()
        
        # Get curated models from library
        library = client.get_ollama_library()
        
        # Group by category
        categories = {}
        for model in library:
            category = model['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(model)
        
        # Display by category
        for category, models in categories.items():
            # Category header
            self.models_list.controls.append(
                ft.Text(
                    category,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.PURPLE
                )
            )
            
            # Models in this category
            for model in models:
                self.models_list.controls.append(
                    self._create_model_card(model)
                )
            
            self.models_list.controls.append(ft.Container(height=10))
        
        self.page.update()
    
    def _create_model_card(self, model: dict) -> ft.Container:
        """Create a model card with download button"""
        is_installed = model['name'] in self.installed_models
        is_current = model['name'] == self.current_model
        
        # Status indicator
        if is_current:
            status = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=20)
            status_text = "Active"
        elif is_installed:
            status = ft.Icon(ft.icons.DOWNLOAD_DONE, color=ft.colors.BLUE, size=20)
            status_text = "Installed"
        else:
            status = ft.Icon(ft.icons.CLOUD_DOWNLOAD, color=ft.colors.GREY, size=20)
            status_text = "Not installed"
        
        # Action button
        if is_current:
            action_btn = ft.Container()  # Already active
        elif is_installed:
            action_btn = ft.ElevatedButton(
                "Set Active",
                icon=ft.icons.PLAY_ARROW,
                on_click=lambda e, m=model: self._set_active_model(m),
                style=ft.ButtonStyle(
                    bgcolor=ft.colors.GREEN,
                    color=ft.colors.WHITE
                )
            )
        else:
            action_btn = ft.ElevatedButton(
                "Download",
                icon=ft.icons.DOWNLOAD,
                on_click=lambda e, m=model: self._download_model(m),
                style=ft.ButtonStyle(
                    bgcolor=ft.colors.PURPLE,
                    color=ft.colors.WHITE
                )
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(model['display_name'], size=14, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{model['size']} • {status_text}", size=11, color=ft.colors.GREY_600),
                    ], expand=True, spacing=2),
                    status,
                    ft.Container(width=10),
                    action_btn,
                ]),
                ft.Text(
                    model['description'],
                    size=12,
                    color=ft.colors.GREY_700,
                ),
                ft.Row([
                    ft.Container(
                        content=ft.Text(tag, size=10),
                        bgcolor=ft.colors.PURPLE_100,
                        border_radius=5,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2)
                    )
                    for tag in model['tags'][:3]
                ], spacing=5),
            ], spacing=5),
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=10,
            padding=15,
            border=ft.border.all(2, ft.colors.GREEN) if is_current else None
        )
    
    def _download_model(self, model: dict):
        """Download a model"""
        threading.Thread(
            target=lambda: asyncio.run(self._download_model_async(model)),
            daemon=True
        ).start()
    
    async def _download_model_async(self, model: dict):
        """Download model asynchronously"""
        model_name = model['name']
        
        # Show progress
        self._show_status(f"⏳ Downloading {model['display_name']}... This may take a few minutes", ft.colors.BLUE)
        
        try:
            client = OllamaClient(host=self.host)
            success, message = await client.pull_model(model_name)
            
            if success:
                self._show_status(message, ft.colors.GREEN)
                
                # Refresh installed models
                self.installed_models = await client.get_available_models()
                
                # Reload library to update UI
                self._load_model_library(client)
            else:
                self._show_status(f"✗ {message}", ft.colors.RED)
                
        except Exception as e:
            self._show_status(f"✗ Error downloading: {str(e)}", ft.colors.RED)
    
    def _set_active_model(self, model: dict):
        """Set a model as active"""
        model_name = model['name']
        
        # Save configuration
        success = self.api_key_manager.store_ollama_config(
            model=model_name,
            host=self.host
        )
        
        if success:
            self.current_model = model_name
            self._show_status(f"✓ {model['display_name']} is now active!", ft.colors.GREEN)
            
            # Reload library to update UI
            client = OllamaClient(host=self.host)
            self._load_model_library(client)
            
            # Call save callback
            self.page.run_task(lambda: self.on_save())
        else:
            self._show_status("✗ Failed to save configuration", ft.colors.RED)
    
    def _refresh_models(self, e):
        """Refresh models list"""
        threading.Thread(target=lambda: asyncio.run(self._test_connection()), daemon=True).start()
    
    def _show_status(self, message: str, color):
        """Show status message"""
        self.status_text.value = message
        self.status_text.color = color
        self.page.update()

