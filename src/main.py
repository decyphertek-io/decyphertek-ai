
"""
DecypherTek AI - Mobile App
Main entry point for the Flet application
"""

import flet as ft
import os
import sys
from pathlib import Path

# Add the python directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from auth.credentials import CredentialManager
from ui.setup import SetupView
from ui.login import LoginView
from ui.dashboard import DashboardView
from utils.config import AppConfig
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger()


class DecypherTekAI:
    """Main application class"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.config = AppConfig()
        self.credential_manager = None
        self.current_user = None
        self.current_password = None  # Store password for API key encryption
        self.dashboard_view = None  # Cache dashboard view to avoid Qdrant lock issues
        
        # Configure page
        self._configure_page()
        
        # Initialize app
        self._initialize()
    
    def _configure_page(self):
        """Configure the main page settings"""
        self.page.title = ""  # Remove title bar text
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.padding = 0
        
        # Set theme colors
        self.page.theme = ft.Theme(
            color_scheme_seed=ft.colors.BLUE,
            use_material3=True,
        )
        
        # Handle window events
        self.page.on_route_change = self._route_change
        self.page.on_view_pop = self._view_pop
    
    def _initialize(self):
        """Initialize the application"""
        try:
            # Get app data directory from Android context
            if hasattr(self.page, 'platform_brightness'):
                # Running on Android
                app_data_dir = os.path.join(
                    os.getenv('HOME', '/data/data/io.decyphertek.ai'),
                    '.decyphertek-ai'
                )
            else:
                # Development mode
                app_data_dir = os.path.expanduser('~/.decyphertek-ai')
            
            # Ensure directory exists
            os.makedirs(app_data_dir, exist_ok=True)
            
            # Initialize credential manager
            self.credential_manager = CredentialManager(app_data_dir)
            
            # Check if first launch
            if self.credential_manager.has_credentials():
                logger.info("Credentials found, showing login screen")
                self.show_login()
            else:
                logger.info("First launch, showing setup screen")
                self.show_setup()
                
        except Exception as e:
            logger.error(f"Error initializing app: {e}")
            self._show_error(f"Initialization error: {e}")
    
    def show_setup(self):
        """Show the setup screen for first-time users"""
        self.page.views.clear()
        setup_view = SetupView(self.page, self.credential_manager, self.on_setup_complete)
        self.page.views.append(setup_view.build())
        self.page.update()
    
    def show_login(self):
        """Show the login screen"""
        self.page.views.clear()
        login_view = LoginView(self.page, self.credential_manager, self.on_login_success)
        self.page.views.append(login_view.build())
        self.page.update()
    
    def show_dashboard(self):
        """Show the main dashboard"""
        self.page.views.clear()
        
        # Reuse dashboard view if it exists to avoid Qdrant lock issues
        if self.dashboard_view is None:
            self.dashboard_view = DashboardView(
                self.page, 
                self.credential_manager,
                self.current_user,
                self.current_password,
                self.on_logout,
                None  # No admin callback needed - admin is now a tab
            )
        
        self.page.views.append(self.dashboard_view.build())
        self.page.update()
    
    def on_setup_complete(self, username: str, password: str):
        """Callback when setup is complete"""
        logger.info(f"Setup complete for user: {username}")
        self.current_user = username
        self.current_password = password
        self.show_dashboard()
    
    def on_login_success(self, username: str, password: str):
        """Callback when login is successful"""
        logger.info(f"Login successful for user: {username}")
        self.current_user = username
        self.current_password = password
        self.show_dashboard()
    
    def on_logout(self):
        """Callback when user logs out"""
        logger.info("User logged out")
        self.current_user = None
        self.current_password = None
        self.show_login()
    
    def _route_change(self, e):
        """Handle route changes"""
        logger.info(f"Route changed to: {e.route}")
    
    def _view_pop(self, e):
        """Handle back button"""
        self.page.views.pop()
        top_view = self.page.views[-1] if self.page.views else None
        self.page.go(top_view.route if top_view else "/")
    
    def _show_error(self, message: str):
        """Show error dialog"""
        dialog = ft.AlertDialog(
            title=ft.Text("Error"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=lambda e: self.page.close(dialog))
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()


def main(page: ft.Page):
    """Main entry point for Flet app"""
    try:
        app = DecypherTekAI(page)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        # Show error on page
        page.add(ft.Text(f"Fatal error: {e}", color=ft.colors.RED))


if __name__ == "__main__":
    # For development testing
    ft.app(target=main)
