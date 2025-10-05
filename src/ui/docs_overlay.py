"""
Simple docs overlay implementation for testing
"""
import flet as ft
from pathlib import Path

def create_docs_overlay(page):
    """Create a simple docs overlay for testing"""
    
    # Create admin.txt content
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
**Note:** Commands above are read-only. Use the text editor below for your notes."""

    # Set up file paths
    notes_dir = Path.home() / ".decyphertek-ai" / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    
    admin_file = notes_dir / "admin.txt"
    quicknotes_file = notes_dir / "quicknotes.md"
    
    # Create admin.txt if it doesn't exist
    if not admin_file.exists():
        admin_file.write_text(admin_content, encoding="utf-8")
    
    # Load quicknotes content
    quicknotes_content = ""
    if quicknotes_file.exists():
        try:
            quicknotes_content = quicknotes_file.read_text(encoding="utf-8")
        except Exception:
            quicknotes_content = ""
    
    # Create text fields
    admin_field = ft.TextField(
        value=admin_content,
        read_only=True,
        multiline=True,
        min_lines=15,
        max_lines=15,
        border_color=ft.colors.GREY_300,
        bgcolor=ft.colors.GREY_50,
        text_style=ft.TextStyle(
            font_family="monospace",
            size=11
        )
    )
    
    quicknotes_field = ft.TextField(
        value=quicknotes_content,
        multiline=True,
        min_lines=15,
        max_lines=15,
        hint_text="Type your notes here... Supports markdown, python, txt, etc.",
        border_color=ft.colors.BLUE_300,
        text_style=ft.TextStyle(
            font_family="monospace",
            size=11
        )
    )
    
    def save_quicknotes(e):
        """Save quicknotes to file"""
        try:
            quicknotes_file.write_text(quicknotes_field.value, encoding="utf-8")
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Quicknotes saved successfully!"),
                    bgcolor=ft.colors.GREEN
                )
            )
        except Exception as ex:
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Error saving quicknotes: {ex}"),
                    bgcolor=ft.colors.RED
                )
            )
    
    def create_folder(e):
        """Create a new folder for organizing notes"""
        def create_folder_dialog(e):
            folder_name = folder_input.value.strip()
            if folder_name:
                folder_path = notes_dir / folder_name
                folder_path.mkdir(exist_ok=True)
                page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Folder '{folder_name}' created!"),
                        bgcolor=ft.colors.GREEN
                    )
                )
            page.close(folder_dialog)
        
        folder_input = ft.TextField(
            hint_text="Enter folder name",
            border_color=ft.colors.BLUE_300
        )
        
        folder_dialog = ft.AlertDialog(
            title=ft.Text("📁 Create New Folder"),
            content=ft.Container(
                content=folder_input,
                padding=10
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.close(folder_dialog)),
                ft.TextButton("Create", on_click=create_folder_dialog),
            ]
        )
        
        page.add(folder_dialog)
        folder_dialog.open = True
        page.update()
    
    def close_dialog(e):
        page.close(dialog)
    
    # Create dialog
    dialog = ft.AlertDialog(
        title=ft.Text("📋 Admin Commands & Text Editor"),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("📄 admin.txt (Read-Only):", weight=ft.FontWeight.BOLD),
                    admin_field,
                    ft.Divider(),
                    ft.Text("✏️ quicknotes.md (Editable):", weight=ft.FontWeight.BOLD),
                    quicknotes_field,
                ],
                scroll=ft.ScrollMode.AUTO,
                height=700,
                width=900
            ),
            padding=10
        ),
        actions=[
            ft.TextButton("📁 New Folder", on_click=create_folder),
            ft.TextButton("💾 Save Notes", on_click=save_quicknotes),
            ft.TextButton("❌ Close", on_click=close_dialog),
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    page.add(dialog)
    dialog.open = True
    page.update()
    
    return dialog
