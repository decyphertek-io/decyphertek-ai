"""
API Settings view for configuring OpenRouter
"""

import flet as ft
from typing import Callable
import asyncio


class APISettingsView:
    """View for managing OpenRouter API configuration"""
    
    def __init__(self, page: ft.Page, api_key_manager, on_save: Callable, on_back: Callable):
        """
        Initialize API settings view
        
        Args:
            page: Flet page
            api_key_manager: APIKeyManager instance
            on_save: Callback when settings are saved
            on_back: Callback for back button
        """
        self.page = page
        self.api_key_manager = api_key_manager
        self.on_save = on_save
        self.on_back = on_back
        
        # UI elements
        self.api_key_field = None
        self.model_dropdown = None
        self.test_button = None
        self.save_button = None
        self.status_text = None
    
    def build(self) -> ft.Column:
        """Build API settings interface"""
        
        # Get existing config
        config = self.api_key_manager.get_openrouter_config()
        has_key = config is not None
        
        # API Key field
        self.api_key_field = ft.TextField(
            label="OpenRouter API Key",
            hint_text="sk-or-v1-...",
            password=True,
            can_reveal_password=True,
            value=config['api_key'] if has_key else "",
            expand=True,
            border_color=ft.colors.BLUE_200,
        )
        
        # Model dropdown
        self.model_dropdown = ft.Dropdown(
            label="Model",
            hint_text="Select AI model",
            value=config['model'] if has_key else "qwen/qwen-2.5-coder-32b-instruct",
            options=[
                ft.dropdown.Option("qwen/qwen-2.5-coder-32b-instruct", "Qwen 2.5 Coder 32B (Free)"),
                ft.dropdown.Option("openai/gpt-4-turbo", "GPT-4 Turbo"),
                ft.dropdown.Option("openai/gpt-4", "GPT-4"),
                ft.dropdown.Option("openai/gpt-3.5-turbo", "GPT-3.5 Turbo"),
                ft.dropdown.Option("anthropic/claude-3-opus", "Claude 3 Opus"),
                ft.dropdown.Option("anthropic/claude-3-sonnet", "Claude 3 Sonnet"),
                ft.dropdown.Option("anthropic/claude-3-haiku", "Claude 3 Haiku"),
                ft.dropdown.Option("google/gemini-pro", "Gemini Pro"),
                ft.dropdown.Option("meta-llama/llama-3-70b-instruct", "Llama 3 70B"),
                ft.dropdown.Option("mistralai/mixtral-8x7b-instruct", "Mixtral 8x7B"),
            ],
            expand=True,
            border_color=ft.colors.BLUE_200,
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
            expand=True
        )
        
        # Save button
        self.save_button = ft.ElevatedButton(
            "Save Settings",
            icon=ft.icons.SAVE,
            on_click=self._save_settings,
            expand=True,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.BLUE,
                color=ft.colors.WHITE
            )
        )
        
        return ft.Column(
            controls=[
                # App bar
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.ARROW_BACK,
                                on_click=lambda e: self.on_back(),
                                tooltip="Back"
                            ),
                            ft.Text(
                                "OpenRouter API",
                                size=22,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Container(expand=True),
                        ]
                    ),
                    padding=15,
                    bgcolor=ft.colors.SURFACE_VARIANT
                ),
                
                # Settings content
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(height=20),
                            
                            # Info card
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.icons.INFO_OUTLINE, color=ft.colors.BLUE),
                                        ft.Text(
                                            "OpenRouter Configuration",
                                            size=16,
                                            weight=ft.FontWeight.BOLD
                                        ),
                                    ]),
                                    ft.Container(height=10),
                                    ft.Text(
                                        "Get your API key from openrouter.ai",
                                        size=13,
                                        color=ft.colors.GREY_700
                                    ),
                                    ft.TextButton(
                                        "Get API Key →",
                                        on_click=lambda e: self.page.launch_url("https://openrouter.ai/keys"),
                                        style=ft.ButtonStyle(
                                            color=ft.colors.BLUE
                                        )
                                    ),
                                ]),
                                bgcolor=ft.colors.BLUE_50,
                                border_radius=10,
                                padding=15,
                            ),
                            
                            ft.Container(height=30),
                            
                            # API Key input
                            self.api_key_field,
                            
                            ft.Container(height=20),
                            
                            # Model selection
                            self.model_dropdown,
                            
                            ft.Container(height=30),
                            
                            # Status
                            self.status_text,
                            
                            ft.Container(height=10),
                            
                            # Buttons
                            ft.Row(
                                controls=[
                                    self.test_button,
                                    self.save_button,
                                ],
                                spacing=15
                            ),
                            
                            ft.Container(height=20),
                            
                            # Delete key option
                            ft.Container(
                                content=ft.TextButton(
                                    "Delete API Key",
                                    icon=ft.icons.DELETE_OUTLINE,
                                    on_click=self._delete_key,
                                    style=ft.ButtonStyle(
                                        color=ft.colors.RED
                                    )
                                ),
                                alignment=ft.alignment.center,
                            ) if has_key else ft.Container(),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True
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
        import threading
        
        def test_in_thread():
            import asyncio
            asyncio.run(self._test_connection())
        
        threading.Thread(target=test_in_thread, daemon=True).start()
    
    async def _test_connection(self):
        """Test API connection"""
        if not self.api_key_field.value or not self.api_key_field.value.strip():
            self._show_status("⚠️ Please enter an API key", ft.colors.ORANGE)
            return
        
        self.test_button.disabled = True
        self._show_status("Testing connection...", ft.colors.BLUE)
        self.page.update()
        
        try:
            # Import here to avoid circular dependency
            from chat.openrouter_client import OpenRouterClient
            
            client = OpenRouterClient(
                api_key=self.api_key_field.value.strip(),
                model=self.model_dropdown.value
            )
            
            success, message = await client.test_connection()
            
            if success:
                self._show_status(f"✓ {message}", ft.colors.GREEN)
            else:
                self._show_status(f"✗ {message}", ft.colors.RED)
                
        except Exception as e:
            self._show_status(f"✗ Error: {str(e)}", ft.colors.RED)
        
        finally:
            self.test_button.disabled = False
            self.page.update()
    
    def _save_settings(self, e):
        """Save API settings"""
        if not self.api_key_field.value or not self.api_key_field.value.strip():
            self._show_status("⚠️ Please enter an API key", ft.colors.ORANGE)
            return
        
        success = self.api_key_manager.store_openrouter_key(
            api_key=self.api_key_field.value.strip(),
            model=self.model_dropdown.value
        )
        
        if success:
            self._show_status("✓ Settings saved!", ft.colors.GREEN)
            self.page.update()
            # Call save callback directly
            import time
            time.sleep(0.5)  # Brief pause to show success message
            self.on_save()
        else:
            self._show_status("✗ Failed to save settings", ft.colors.RED)
            self.page.update()
    
    def _delete_key(self, e):
        """Delete API key"""
        dialog = ft.AlertDialog(
            title=ft.Text("Delete API Key?"),
            content=ft.Text("This will remove your OpenRouter API key. You can add it again later."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.TextButton(
                    "Delete",
                    on_click=lambda e: self._confirm_delete(dialog),
                    style=ft.ButtonStyle(color=ft.colors.RED)
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _confirm_delete(self, dialog):
        """Confirm and execute delete"""
        self.api_key_manager.delete_openrouter_key()
        self.page.close(dialog)
        self._show_status("✓ API key deleted", ft.colors.ORANGE)
        self.api_key_field.value = ""
        self.page.update()
    
    def _show_status(self, message: str, color):
        """Show status message"""
        self.status_text.value = message
        self.status_text.color = color
        self.page.update()

