"""
DecypherTek AI Mobile - Credential-Free Version
Users must configure their own API keys and credentials
"""

import flet as ft
import os
import json
from pathlib import Path

class CredentialFreeApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "DecypherTek AI Mobile"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = ft.colors.BACKGROUND
        
        # Check if credentials are configured
        self.credentials_configured = self._check_credentials()
        
        if self.credentials_configured:
            self._build_main_app()
        else:
            self._build_setup_screen()
    
    def _check_credentials(self):
        """Check if user has configured credentials"""
        try:
            # Look for credentials in app data directory
            app_data_dir = Path.home() / ".decyphertek-ai-mobile"
            app_data_dir.mkdir(exist_ok=True)
            
            config_file = app_data_dir / "config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return bool(config.get('openrouter_api_key'))
            return False
        except:
            return False
    
    def _build_setup_screen(self):
        """Build the initial setup screen"""
        self.api_key_field = ft.TextField(
            label="OpenRouter API Key",
            password=True,
            can_reveal_password=True,
            hint_text="Enter your OpenRouter API key",
            border_color=ft.colors.BLUE_200,
        )
        
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(
                        ft.icons.SMART_TOY,
                        size=80,
                        color=ft.colors.BLUE,
                    ),
                    ft.Text(
                        "DecypherTek AI Mobile",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE,
                    ),
                    ft.Text(
                        "Welcome! Please configure your API key to get started.",
                        size=16,
                        color=ft.colors.GREY_400,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=30),
                    self.api_key_field,
                    ft.ElevatedButton(
                        "Save Configuration",
                        on_click=self._save_credentials,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE,
                            color=ft.colors.WHITE,
                        )
                    ),
                    ft.Text(
                        "Get your API key from: https://openrouter.ai/",
                        size=12,
                        color=ft.colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20),
                padding=40,
                alignment=ft.alignment.center
            )
        )
    
    def _build_main_app(self):
        """Build the main app interface"""
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(
                        ft.icons.SMART_TOY,
                        size=80,
                        color=ft.colors.BLUE,
                    ),
                    ft.Text(
                        "DecypherTek AI Mobile",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE,
                    ),
                    ft.Text(
                        "✅ Credentials configured successfully!",
                        size=16,
                        color=ft.colors.GREEN,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Mobile features coming soon!",
                        size=14,
                        color=ft.colors.GREY_400,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=30),
                    ft.ElevatedButton(
                        "Test Connection",
                        on_click=self._test_connection,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE,
                            color=ft.colors.WHITE,
                        )
                    ),
                    ft.ElevatedButton(
                        "Reset Configuration",
                        on_click=self._reset_credentials,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.RED,
                            color=ft.colors.WHITE,
                        )
                    ),
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20),
                padding=40,
                alignment=ft.alignment.center
            )
        )
    
    def _save_credentials(self, e):
        """Save user credentials"""
        if not self.api_key_field.value.strip():
            self._show_snackbar("Please enter your API key", ft.colors.RED)
            return
        
        try:
            # Save to app data directory
            app_data_dir = Path.home() / ".decyphertek-ai-mobile"
            app_data_dir.mkdir(exist_ok=True)
            
            config = {
                "openrouter_api_key": self.api_key_field.value.strip(),
                "configured": True
            }
            
            config_file = app_data_dir / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self._show_snackbar("✅ Configuration saved successfully!", ft.colors.GREEN)
            
            # Refresh the app
            self.page.clean()
            self.credentials_configured = True
            self._build_main_app()
            
        except Exception as ex:
            self._show_snackbar(f"Error saving configuration: {str(ex)}", ft.colors.RED)
    
    def _test_connection(self, e):
        """Test API connection"""
        self._show_snackbar("🔗 Testing connection... (Feature coming soon)", ft.colors.BLUE)
    
    def _reset_credentials(self, e):
        """Reset user credentials"""
        try:
            app_data_dir = Path.home() / ".decyphertek-ai-mobile"
            config_file = app_data_dir / "config.json"
            if config_file.exists():
                config_file.unlink()
            
            self._show_snackbar("Configuration reset", ft.colors.ORANGE)
            
            # Refresh the app
            self.page.clean()
            self.credentials_configured = False
            self._build_setup_screen()
            
        except Exception as ex:
            self._show_snackbar(f"Error resetting configuration: {str(ex)}", ft.colors.RED)
    
    def _show_snackbar(self, message: str, color: ft.colors):
        """Show a snackbar message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color,
        )
        self.page.snack_bar.open = True
        self.page.update()

def main(page: ft.Page):
    """Main entry point - completely credential-free"""
    app = CredentialFreeApp(page)

if __name__ == "__main__":
    ft.app(target=main)
