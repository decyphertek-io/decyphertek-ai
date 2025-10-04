"""
Mobile-compatible version of DecypherTek AI
Excludes RAG, MCP, and other non-mobile-compatible features
"""


import flet as ft
from typing import Optional
import json
import os
from pathlib import Path

class MobileDecypherTekAI:
    """Simplified mobile version of DecypherTek AI"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "DecypherTek AI Mobile"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = ft.colors.BACKGROUND
        
        # Simple chat state
        self.messages = []
        self.chat_list = None
        self.input_field = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the mobile UI"""
        
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
        send_button = ft.IconButton(
            icon=ft.icons.SEND,
            icon_color=ft.colors.BLUE,
            tooltip="Send message",
            on_click=self._on_send_click
        )
        
        # Main UI
        self.page.add(
            ft.Container(
                content=ft.Column([
                    # Header
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.SMART_TOY, size=28, color=ft.colors.BLUE),
                            ft.Text(
                                "DecypherTek AI Mobile",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.WHITE,
                            ),
                        ], spacing=10),
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
                        content=ft.Row([
                            self.input_field,
                            send_button
                        ], spacing=10),
                        padding=15,
                        bgcolor=ft.colors.SURFACE_VARIANT
                    ),
                ], spacing=0, expand=True),
                expand=True
            )
        )
        
        # Add welcome message
        self._add_message("system", "🤖 Welcome to DecypherTek AI Mobile!\n\nThis is a simplified mobile version. Full features are available in the desktop version.")
    
    def _add_message(self, role: str, content: str):
        """Add a message to the chat"""
        color = ft.colors.BLUE_100 if role == "user" else ft.colors.WHITE
        bgcolor = ft.colors.BLUE_900 if role == "user" else ft.colors.SURFACE_VARIANT
        
        self.chat_list.controls.append(
            ft.Container(
                content=ft.Text(
                    content,
                    color=color,
                    size=14,
                    selectable=True
                ),
                bgcolor=bgcolor,
                border_radius=8,
                padding=12,
                margin=ft.margin.only(
                    left=50 if role == "user" else 0,
                    right=0 if role == "user" else 50
                )
            )
        )
        self.page.update()
    
    def _on_send_click(self, e):
        """Handle send button click"""
        if not self.input_field.value.strip():
            return
        
        user_message = self.input_field.value.strip()
        self.input_field.value = ""
        self.page.update()
        
        # Add user message
        self._add_message("user", user_message)
        
        # Add simple AI response
        self._add_message("assistant", f"🤖 Mobile AI Response:\n\nI received your message: '{user_message}'\n\nThis is a simplified mobile version of DecypherTek AI. For full features including RAG, MCP servers, and advanced AI capabilities, please use the desktop version.\n\nMobile features coming soon! 🚀")

def main(page: ft.Page):
    """Main entry point for mobile app"""
    app = MobileDecypherTekAI(page)

if __name__ == "__main__":
    ft.app(target=main)
