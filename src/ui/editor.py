"""
Integrated Text Editor for Chat Interface
Launches within the chat window for seamless editing experience
"""
import flet as ft
from pathlib import Path
import os

def launch_editor(chat_view):
    """Launch integrated text editor within the chat window"""
    
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
    
    # Create editor components
    admin_field = ft.TextField(
        value=admin_content,
        read_only=True,
        multiline=True,
        min_lines=12,
        max_lines=12,
        border_color=ft.colors.GREY_600,
        bgcolor=ft.colors.GREY_900,
        color=ft.colors.WHITE,
        text_style=ft.TextStyle(
            font_family="monospace",
            size=10,
            color=ft.colors.WHITE
        )
    )
    
    quicknotes_field = ft.TextField(
        value=quicknotes_content,
        multiline=True,
        min_lines=20,
        max_lines=20,
        hint_text="Type your notes here... Supports markdown, python, txt, etc.",
        border_color=ft.colors.BLUE_400,
        bgcolor=ft.colors.GREY_800,
        color=ft.colors.WHITE,
        text_style=ft.TextStyle(
            font_family="monospace",
            size=10,
            color=ft.colors.WHITE
        )
    )
    
    # File picker for opening files
    file_picker = ft.FilePicker()
    chat_view.page.overlay.append(file_picker)
    
    def save_quicknotes(e):
        """Save quicknotes to file"""
        try:
            quicknotes_file.write_text(quicknotes_field.value, encoding="utf-8")
            chat_view.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("💾 Quicknotes saved successfully!"),
                    bgcolor=ft.colors.GREEN
                )
            )
        except Exception as ex:
            chat_view.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"❌ Error saving quicknotes: {ex}"),
                    bgcolor=ft.colors.RED
                )
            )
    
    def open_file(e):
        """Open a file in the editor"""
        def on_file_picked(e: ft.FilePickerResultEvent):
            if e.files:
                file_path = Path(e.files[0].path)
                try:
                    content = file_path.read_text(encoding="utf-8")
                    quicknotes_field.value = content
                    quicknotes_field.update()
                    chat_view.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text(f"📂 Opened: {file_path.name}"),
                            bgcolor=ft.colors.BLUE
                        )
                    )
                except Exception as ex:
                    chat_view.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text(f"❌ Error opening file: {ex}"),
                            bgcolor=ft.colors.RED
                        )
                    )
        
        file_picker.on_result = on_file_picked
        file_picker.pick_files(
            dialog_title="Open File in Editor",
            allowed_extensions=["txt", "md", "py", "js", "html", "css", "json", "yaml", "yml", "xml"]
        )
    
    def save_as_file(e):
        """Save current content as a new file"""
        def on_save_picked(e: ft.FilePickerResultEvent):
            if e.path:
                file_path = Path(e.path)
                try:
                    file_path.write_text(quicknotes_field.value, encoding="utf-8")
                    chat_view.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text(f"💾 Saved as: {file_path.name}"),
                            bgcolor=ft.colors.GREEN
                        )
                    )
                except Exception as ex:
                    chat_view.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text(f"❌ Error saving file: {ex}"),
                            bgcolor=ft.colors.RED
                        )
                    )
        
        file_picker.on_result = on_save_picked
        file_picker.save_file(
            dialog_title="Save File As",
            file_name="notes.md",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["md", "txt", "py", "js", "html", "css", "json", "yaml", "yml"]
        )
    
    def create_folder(e):
        """Create a new folder for organizing notes"""
        def create_folder_dialog(e):
            folder_name = folder_input.value.strip()
            if folder_name:
                folder_path = notes_dir / folder_name
                folder_path.mkdir(exist_ok=True)
                chat_view.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"📁 Folder '{folder_name}' created!"),
                        bgcolor=ft.colors.GREEN
                    )
                )
            chat_view.page.close(folder_dialog)
        
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
                ft.TextButton("Cancel", on_click=lambda e: chat_view.page.close(folder_dialog)),
                ft.TextButton("Create", on_click=create_folder_dialog),
            ]
        )
        
        chat_view.page.add(folder_dialog)
        folder_dialog.open = True
        chat_view.page.update()
    
    def close_editor(e):
        """Close the editor and return to chat"""
        # Use chat view's close method for proper state management
        if hasattr(chat_view, '_close_editor'):
            chat_view._close_editor()
        else:
            # Fallback: remove editor from chat list
            chat_view.chat_list.controls = [control for control in chat_view.chat_list.controls 
                                          if not hasattr(control, 'editor_container')]
            chat_view.page.update()
    
    # Create editor container - statically framed within chat window
    editor_container = ft.Container(
        content=ft.Column(
            controls=[
                # Editor header
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text("📝 Integrated Text Editor", 
                                   size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE),
                            ft.Container(expand=True),  # Spacer
                            ft.IconButton(
                                icon=ft.icons.CLOSE,
                                icon_color=ft.colors.RED,
                                tooltip="Close Editor",
                                on_click=close_editor
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    bgcolor=ft.colors.BLUE_50,
                    padding=10,
                    border_radius=ft.border_radius.only(
                        top_left=10, top_right=10
                    )
                ),
                
                # Admin commands section
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("📄 admin.txt (Read-Only Reference)", 
                                   weight=ft.FontWeight.BOLD, size=12),
                            admin_field,
                        ],
                        spacing=5
                    ),
                    padding=10,
                    bgcolor=ft.colors.GREY_100
                ),
                
                # Divider
                ft.Divider(height=2, color=ft.colors.BLUE_200),
                
                # Text editor section
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("✏️ Text Editor (Editable)", 
                                   weight=ft.FontWeight.BOLD, size=12),
                            quicknotes_field,
                        ],
                        spacing=5
                    ),
                    padding=10,
                    bgcolor=ft.colors.WHITE
                ),
                
                # Editor toolbar
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "📂 Open File",
                                icon=ft.icons.FOLDER_OPEN,
                                on_click=open_file,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.BLUE_100,
                                    color=ft.colors.BLUE_800
                                )
                            ),
                            ft.ElevatedButton(
                                "💾 Save Notes",
                                icon=ft.icons.SAVE,
                                on_click=save_quicknotes,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.GREEN_100,
                                    color=ft.colors.GREEN_800
                                )
                            ),
                            ft.ElevatedButton(
                                "💾 Save As",
                                icon=ft.icons.SAVE_AS,
                                on_click=save_as_file,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.ORANGE_100,
                                    color=ft.colors.ORANGE_800
                                )
                            ),
                            ft.ElevatedButton(
                                "📁 New Folder",
                                icon=ft.icons.CREATE_NEW_FOLDER,
                                on_click=create_folder,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.PURPLE_100,
                                    color=ft.colors.PURPLE_800
                                )
                            ),
                        ],
                        spacing=10
                    ),
                    padding=10,
                    bgcolor=ft.colors.GREY_50,
                    border_radius=ft.border_radius.only(
                        bottom_left=10, bottom_right=10
                    )
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0
        ),
        # Static framing within chat window - no margins, full width
        width=chat_view.chat_list.width if hasattr(chat_view.chat_list, 'width') else None,
        height=600,  # Fixed height to fit within chat window
        bgcolor=ft.colors.WHITE,
        border=ft.border.all(2, ft.colors.BLUE_200),
        border_radius=10,
        # Remove margins and shadows for static framing
        margin=ft.margin.all(5),  # Minimal margin
        # Remove shadow for cleaner integration
    )
    
    # Mark this container as the editor for easy removal
    editor_container.editor_container = True
    
    # Add editor to chat list as a static, contained element
    chat_view.chat_list.controls.append(editor_container)
    
    # Update the page to render the editor
    chat_view.page.update()
    
    # Scroll to the editor smoothly
    chat_view.chat_list.scroll_to(
        offset=-1,
        duration=500,
        curve=ft.AnimationCurve.EASE_OUT
    )
    
    # Ensure editor stays within chat window bounds
    def ensure_editor_bounds():
        """Ensure editor stays properly framed within chat window"""
        try:
            # Get chat list dimensions
            if hasattr(chat_view.chat_list, 'width') and chat_view.chat_list.width:
                editor_container.width = min(editor_container.width or 800, chat_view.chat_list.width - 20)
            
            # Ensure height fits within chat window
            editor_container.height = min(600, chat_view.page.height - 200)
            chat_view.page.update()
        except Exception as ex:
            print(f"[Editor] Error adjusting bounds: {ex}")
    
    # Adjust bounds after a short delay to ensure proper rendering
    import threading
    import time
    def delayed_bounds_adjust():
        time.sleep(0.1)
        ensure_editor_bounds()
    
    threading.Thread(target=delayed_bounds_adjust, daemon=True).start()
    
    return editor_container