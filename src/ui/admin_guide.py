import flet as ft
from pathlib import Path

def launch_admin_guide(chat_view):
    """Launches the admin diagnostic guide within the chat window."""
    
    # Admin diagnostic commands content
    admin_content = """# 🔧 Admin Diagnostic Commands

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

## Note Management (Adminotaur)
- `search notes for "keyword"` - Search through all notes
- `read notes` - Show all available notes
- `write note: content` - Add a new note
- `find notes about "topic"` - Find notes containing specific topic

## Quick Tips
- All normal chat goes through adminotaur.py when agent is enabled
- Use `health-check` for comprehensive system diagnostics
- Use `verbose` for detailed troubleshooting information
- MCP servers provide tools for the agent (web search, etc.)
- Store Manager handles downloads and installations
- Chat Manager routes messages and manages sessions
- Adminotaur can read/write notes and organize research in folders

---
**Note:** This is a read-only reference guide. Use the Editor for your own notes."""
    
    def close_admin_guide(e):
        """Close the admin guide and return to chat"""
        # Remove admin guide from chat list
        chat_view.chat_list.controls = [control for control in chat_view.chat_list.controls 
                                      if not hasattr(control, 'admin_guide_container')]
        chat_view.page.update()
        print("[Admin Guide] Closed")
    
    # Create admin guide container with Tron theme
    admin_guide_container = ft.Container(
        content=ft.Column(
            controls=[
                # Admin guide header with Tron theme
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("🔧 ADMIN DIAGNOSTIC GUIDE", 
                                           size=16, weight=ft.FontWeight.BOLD, color=ft.colors.CYAN_400,
                                           font_family="monospace"),
                                    ft.Container(expand=True),  # Spacer
                                    ft.IconButton(
                                        icon=ft.icons.CLOSE,
                                        icon_color=ft.colors.RED_400,
                                        tooltip="Close Admin Guide",
                                        on_click=close_admin_guide
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Text("System diagnostic commands and troubleshooting guide", 
                                   size=10, color=ft.colors.CYAN_300, font_family="monospace")
                        ],
                        spacing=5
                    ),
                    bgcolor=ft.colors.BLACK,
                    padding=10,
                    border=ft.border.all(1, ft.colors.CYAN_400),
                    border_radius=ft.border_radius.only(
                        top_left=10, top_right=10
                    )
                ),
                
                # Admin commands section with Tron theme
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("📄 Diagnostic Commands (Read-Only)", 
                                   weight=ft.FontWeight.BOLD, size=12, color=ft.colors.CYAN_400,
                                   font_family="monospace"),
                            ft.TextField(
                                value=admin_content,
                                read_only=True,
                                multiline=True,
                                min_lines=25,
                                max_lines=25,
                                border_color=ft.colors.CYAN_400,
                                bgcolor=ft.colors.BLACK,
                                color=ft.colors.CYAN_300,
                                text_style=ft.TextStyle(
                                    font_family="monospace",
                                    size=11,
                                    color=ft.colors.CYAN_300
                                )
                            ),
                        ],
                        spacing=5
                    ),
                    padding=10,
                    bgcolor=ft.colors.BLACK,
                    border=ft.border.all(1, ft.colors.CYAN_400),
                    border_radius=ft.border_radius.only(
                        bottom_left=10, bottom_right=10
                    )
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0
        ),
        # Static framing within chat window with Tron theme
        width=chat_view.chat_list.width if hasattr(chat_view.chat_list, 'width') else None,
        height=500,  # Fixed height to fit within chat window
        bgcolor=ft.colors.BLACK,
        border=ft.border.all(2, ft.colors.CYAN_400),
        border_radius=10,
        margin=ft.margin.all(5),  # Minimal margin
        # Add subtle glow effect with shadow
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.colors.with_opacity(0.3, ft.colors.CYAN_400),
            offset=ft.Offset(0, 0)
        )
    )
    
    # Mark this container as the admin guide for easy removal
    admin_guide_container.admin_guide_container = True
    
    # Add admin guide to chat list as a static, contained element
    chat_view.chat_list.controls.append(admin_guide_container)
    
    # Update the page to render the admin guide
    chat_view.page.update()
    
    # Scroll to the admin guide smoothly
    chat_view.chat_list.scroll_to(
        offset=-1,
        duration=500,
        curve=ft.AnimationCurve.EASE_OUT
    )
    
    return admin_guide_container
