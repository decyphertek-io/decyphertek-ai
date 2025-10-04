"""
Setup screen for first-time users
"""

import flet as ft
from typing import Callable


class SetupView:
    """First-time setup screen"""
    
    def __init__(self, page: ft.Page, credential_manager, on_complete: Callable):
        """
        Initialize setup view
        
        Args:
            page: Flet page
            credential_manager: Credential manager instance
            on_complete: Callback when setup is complete (receives username)
        """
        self.page = page
        self.credential_manager = credential_manager
        self.on_complete = on_complete
        
        # Form fields
        self.username_field = None
        self.password_field = None
        self.confirm_password_field = None
        self.error_text = None
        self.submit_button = None
    
    def build(self) -> ft.View:
        """Build the setup view"""
        
        # Username field
        self.username_field = ft.TextField(
            label="Username",
            hint_text="3-32 characters, alphanumeric",
            prefix_icon=ft.icons.PERSON,
            autofocus=True,
            on_change=self._on_input_change
        )
        
        # Password field
        self.password_field = ft.TextField(
            label="Password",
            hint_text="Min 8 characters, include uppercase, lowercase, number",
            prefix_icon=ft.icons.LOCK,
            password=True,
            can_reveal_password=True,
            on_change=self._on_input_change
        )
        
        # Confirm password field
        self.confirm_password_field = ft.TextField(
            label="Confirm Password",
            prefix_icon=ft.icons.LOCK_CLOCK,
            password=True,
            can_reveal_password=True,
            on_change=self._on_input_change,
            on_submit=self._on_submit
        )
        
        # Error text
        self.error_text = ft.Text(
            "",
            color=ft.colors.RED_400,
            size=14,
            visible=False
        )
        
        # Submit button
        self.submit_button = ft.ElevatedButton(
            "Create Account",
            icon=ft.icons.CHECK_CIRCLE,
            on_click=self._on_submit,
            disabled=True
        )
        
        # Build view
        return ft.View(
            route="/setup",
            padding=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(height=40),
                
                # Logo/Icon
                ft.Container(
                    content=ft.Icon(
                        ft.icons.SECURITY,
                        size=80,
                        color=ft.colors.BLUE_400
                    ),
                    alignment=ft.alignment.center
                ),
                
                ft.Container(height=20),
                
                # Welcome text
                ft.Text(
                    "Welcome to DecypherTek AI",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                
                ft.Container(height=10),
                
                ft.Text(
                    "Let's set up your account",
                    size=16,
                    color=ft.colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                ),
                
                ft.Container(height=40),
                
                # Form
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self.username_field,
                            ft.Container(height=20),
                            self.password_field,
                            ft.Container(height=20),
                            self.confirm_password_field,
                            ft.Container(height=10),
                            self.error_text,
                            ft.Container(height=20),
                            self.submit_button,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                    ),
                    padding=20
                ),
                
                ft.Container(height=20),
                
                # Info text
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Password Requirements:",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.GREY_700
                        ),
                        ft.Text(
                            "• At least 8 characters",
                            size=12,
                            color=ft.colors.GREY_600
                        ),
                        ft.Text(
                            "• Include uppercase letter",
                            size=12,
                            color=ft.colors.GREY_600
                        ),
                        ft.Text(
                            "• Include lowercase letter",
                            size=12,
                            color=ft.colors.GREY_600
                        ),
                        ft.Text(
                            "• Include number",
                            size=12,
                            color=ft.colors.GREY_600
                        ),
                    ]),
                    padding=ft.padding.only(left=20, right=20)
                ),
            ]
        )
    
    def _on_input_change(self, e):
        """Handle input field changes"""
        # Enable submit button if all fields have values
        has_username = bool(self.username_field.value)
        has_password = bool(self.password_field.value)
        has_confirm = bool(self.confirm_password_field.value)
        
        self.submit_button.disabled = not (has_username and has_password and has_confirm)
        self.page.update()
    
    def _on_submit(self, e):
        """Handle form submission"""
        username = self.username_field.value.strip()
        password = self.password_field.value
        confirm_password = self.confirm_password_field.value
        
        # Validate inputs
        error = self._validate_inputs(username, password, confirm_password)
        if error:
            self._show_error(error)
            return
        
        # Disable button during processing
        self.submit_button.disabled = True
        self.submit_button.text = "Creating account..."
        self.page.update()
        
        # Create credentials
        success = self.credential_manager.create_credentials(username, password)
        
        if success:
            # Store password temporarily for this session
            session_password = password
            
            # Clear sensitive data from fields
            self.password_field.value = ""
            self.confirm_password_field.value = ""
            
            # Call completion callback with password
            self.on_complete(username, session_password)
        else:
            self._show_error("Failed to create account. Please try again.")
            self.submit_button.disabled = False
            self.submit_button.text = "Create Account"
            self.page.update()
    
    def _validate_inputs(self, username: str, password: str, confirm_password: str) -> str:
        """
        Validate form inputs
        
        Returns:
            Error message if validation fails, empty string otherwise
        """
        # Username validation
        if not username:
            return "Username is required"
        if len(username) < 3:
            return "Username must be at least 3 characters"
        if len(username) > 32:
            return "Username must be less than 32 characters"
        if not username.replace('_', '').replace('-', '').isalnum():
            return "Username can only contain letters, numbers, _ and -"
        
        # Password validation
        if not password:
            return "Password is required"
        if len(password) < 8:
            return "Password must be at least 8 characters"
        if not any(c.isupper() for c in password):
            return "Password must include at least one uppercase letter"
        if not any(c.islower() for c in password):
            return "Password must include at least one lowercase letter"
        if not any(c.isdigit() for c in password):
            return "Password must include at least one number"
        
        # Confirm password validation
        if password != confirm_password:
            return "Passwords do not match"
        
        return ""
    
    def _show_error(self, message: str):
        """Show error message"""
        self.error_text.value = message
        self.error_text.visible = True
        self.page.update()

