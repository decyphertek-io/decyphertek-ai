"""
Login screen for returning users
"""

import flet as ft
from typing import Callable


class LoginView:
    """Login screen"""
    
    def __init__(self, page: ft.Page, credential_manager, on_success: Callable):
        """
        Initialize login view
        
        Args:
            page: Flet page
            credential_manager: Credential manager instance
            on_success: Callback when login succeeds (receives username)
        """
        self.page = page
        self.credential_manager = credential_manager
        self.on_success = on_success
        
        # Form fields
        self.username_field = None
        self.password_field = None
        self.error_text = None
        self.login_button = None
    
    def build(self) -> ft.View:
        """Build the login view"""
        
        # Username field
        self.username_field = ft.TextField(
            label="Username",
            prefix_icon=ft.icons.PERSON,
            autofocus=True,
            on_change=self._on_input_change
        )
        
        # Password field
        self.password_field = ft.TextField(
            label="Password",
            prefix_icon=ft.icons.LOCK,
            password=True,
            can_reveal_password=True,
            on_change=self._on_input_change,
            on_submit=self._on_login
        )
        
        # Error text
        self.error_text = ft.Text(
            "",
            color=ft.colors.RED_400,
            size=14,
            visible=False
        )
        
        # Login button
        self.login_button = ft.ElevatedButton(
            "Login",
            icon=ft.icons.LOGIN,
            on_click=self._on_login,
            disabled=True
        )
        
        # Build view
        return ft.View(
            route="/login",
            padding=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(height=60),
                
                # Logo/Icon
                ft.Container(
                    content=ft.Icon(
                        ft.icons.CHAT_BUBBLE,
                        size=100,
                        color=ft.colors.BLUE_400
                    ),
                    alignment=ft.alignment.center
                ),
                
                ft.Container(height=30),
                
                # Welcome back text
                ft.Text(
                    "Welcome Back",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                
                ft.Container(height=10),
                
                ft.Text(
                    "Sign in to continue",
                    size=16,
                    color=ft.colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                ),
                
                ft.Container(height=50),
                
                # Login form
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self.username_field,
                            ft.Container(height=20),
                            self.password_field,
                            ft.Container(height=10),
                            self.error_text,
                            ft.Container(height=30),
                            self.login_button,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                    ),
                    padding=20
                ),
                
                ft.Container(height=20),
                
                # Forgot password hint
                ft.Container(
                    content=ft.Column([
                        ft.Divider(),
                        ft.Container(height=10),
                        ft.Text(
                            "Forgot your password?",
                            size=12,
                            color=ft.colors.GREY_600,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            "You'll need to reset the app data and create a new account.",
                            size=10,
                            color=ft.colors.GREY_500,
                            text_align=ft.TextAlign.CENTER,
                            italic=True
                        ),
                    ]),
                    padding=20
                ),
            ]
        )
    
    def _on_input_change(self, e):
        """Handle input field changes"""
        has_username = bool(self.username_field.value)
        has_password = bool(self.password_field.value)
        
        self.login_button.disabled = not (has_username and has_password)
        self.page.update()
    
    def _on_login(self, e):
        """Handle login submission"""
        username = self.username_field.value.strip()
        password = self.password_field.value
        
        if not username or not password:
            self._show_error("Please enter both username and password")
            return
        
        # Disable button during processing
        self.login_button.disabled = True
        self.login_button.text = "Logging in..."
        self.error_text.visible = False
        self.page.update()
        
        # Verify credentials
        if self.credential_manager.verify_credentials(username, password):
            # Store password temporarily for this session
            session_password = password
            
            # Clear password field
            self.password_field.value = ""
            
            # Call success callback with password
            self.on_success(username, session_password)
        else:
            self._show_error("Invalid username or password")
            self.login_button.disabled = False
            self.login_button.text = "Login"
            self.password_field.value = ""
            self.page.update()
    
    def _show_error(self, message: str):
        """Show error message"""
        self.error_text.value = message
        self.error_text.visible = True
        self.page.update()

