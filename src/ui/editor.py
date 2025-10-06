"""
Integrated Text Editor for Chat Interface
Launches within the chat window for seamless editing experience
"""
import flet as ft
from pathlib import Path
import os

def launch_editor(chat_view):
    """Launch integrated text editor within the chat window"""
    
    # Create admin.txt content (now just a placeholder)
    admin_content = """# 📝 Quick Notes Reference

This is your personal notes editor. Use the Admin Guide for system diagnostic commands.

## Quick Tips:
- Type your notes here
- Use the toolbar buttons to save, open files, or create folders
- Adminotaur can read and write to these notes
- All notes are saved automatically when you use the SAVE button

---
**Note:** For system diagnostic commands, use the Admin Guide from the Docs Menu."""

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
    
    # Create vim-style text fields with Tron cyberpunk theme
    admin_field = ft.TextField(
        value=admin_content,
        read_only=True,
        multiline=True,
        min_lines=12,
        max_lines=12,
        border_color=ft.colors.CYAN_400,
        bgcolor=ft.colors.BLACK,
        color=ft.colors.CYAN_300,
        text_style=ft.TextStyle(
            font_family="monospace",
            size=11,
            color=ft.colors.CYAN_300
        )
    )
    
    quicknotes_field = ft.TextField(
        value=quicknotes_content,
        multiline=True,
        min_lines=20,
        max_lines=20,
        hint_text="Type your notes here... Modern Tron-style editor",
        border_color=ft.colors.CYAN_400,
        bgcolor=ft.colors.BLACK,
        color=ft.colors.CYAN_300,
        text_style=ft.TextStyle(
            font_family="monospace",
            size=11,
            color=ft.colors.CYAN_300
        )
    )
    
    # Visual mode indicator (just for looks)
    mode_indicator = ft.Text(
        "-- TRON MODE --",
        size=12,
        weight=ft.FontWeight.BOLD,
        color=ft.colors.CYAN_400,
        font_family="monospace"
    )
    
    # Modern Tron-style editor (visual only, no vim keybindings)
    
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
            border_color=ft.colors.CYAN_400,
            bgcolor=ft.colors.GREY_800,
            color=ft.colors.WHITE,
            text_style=ft.TextStyle(color=ft.colors.WHITE)
        )
        
        folder_dialog = ft.AlertDialog(
            title=ft.Text("📁 Create New Folder", color=ft.colors.WHITE),
            bgcolor=ft.colors.GREY_900,
            content=ft.Container(
                content=folder_input,
                padding=10
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: chat_view.page.close(folder_dialog), 
                             style=ft.ButtonStyle(color=ft.colors.WHITE)),
                ft.TextButton("Create", on_click=create_folder_dialog,
                             style=ft.ButtonStyle(color=ft.colors.CYAN_300)),
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
                # Vim-style editor header with Tron theme
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("⚡ TRON EDITOR ⚡", 
                                           size=16, weight=ft.FontWeight.BOLD, color=ft.colors.CYAN_400,
                                           font_family="monospace"),
                                    ft.Container(expand=True),  # Spacer
                                    ft.IconButton(
                                        icon=ft.icons.CLOSE,
                                        icon_color=ft.colors.RED_400,
                                        tooltip="Close Editor (:q)",
                                        on_click=close_editor
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Row(
                                controls=[
                                    mode_indicator,
                                    ft.Container(expand=True),
                                    ft.Text("Modern Tron-style text editor", 
                                           size=10, color=ft.colors.CYAN_300, font_family="monospace")
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            )
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
                            ft.Text("📄 admin.txt (Read-Only Reference)", 
                                   weight=ft.FontWeight.BOLD, size=12, color=ft.colors.CYAN_400,
                                   font_family="monospace"),
                            admin_field,
                        ],
                        spacing=5
                    ),
                    padding=10,
                    bgcolor=ft.colors.BLACK,
                    border=ft.border.all(1, ft.colors.CYAN_400)
                ),
                
                # Tron-style divider
                ft.Container(
                    content=ft.Text("═══════════════════════════════════════════════════════════════", 
                                   color=ft.colors.CYAN_400, font_family="monospace", size=10),
                    alignment=ft.alignment.center,
                    padding=5,
                    bgcolor=ft.colors.BLACK
                ),
                
                # Modern Tron-style text editor section
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("✏️ TRON EDITOR (Modern Text Editor)", 
                                   weight=ft.FontWeight.BOLD, size=12, color=ft.colors.CYAN_400,
                                   font_family="monospace"),
                            quicknotes_field,
                        ],
                        spacing=5
                    ),
                    padding=10,
                    bgcolor=ft.colors.BLACK,
                    border=ft.border.all(1, ft.colors.CYAN_400)
                ),
                
                # Editor toolbar
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "📂 OPEN",
                                icon=ft.icons.FOLDER_OPEN,
                                on_click=open_file,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.BLACK,
                                    color=ft.colors.CYAN_400,
                                    side=ft.BorderSide(1, ft.colors.CYAN_400)
                                )
                            ),
                            ft.ElevatedButton(
                                "💾 SAVE",
                                icon=ft.icons.SAVE,
                                on_click=save_quicknotes,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.BLACK,
                                    color=ft.colors.GREEN_400,
                                    side=ft.BorderSide(1, ft.colors.GREEN_400)
                                )
                            ),
                            ft.ElevatedButton(
                                "💾 SAVE AS",
                                icon=ft.icons.SAVE_AS,
                                on_click=save_as_file,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.BLACK,
                                    color=ft.colors.ORANGE_400,
                                    side=ft.BorderSide(1, ft.colors.ORANGE_400)
                                )
                            ),
                            ft.ElevatedButton(
                                "📁 NEW FOLDER",
                                icon=ft.icons.CREATE_NEW_FOLDER,
                                on_click=create_folder,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.BLACK,
                                    color=ft.colors.PURPLE_400,
                                    side=ft.BorderSide(1, ft.colors.PURPLE_400)
                                )
                            ),
                        ],
                        spacing=10
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
        height=600,  # Fixed height to fit within chat window
        bgcolor=ft.colors.BLACK,
        border=ft.border.all(2, ft.colors.CYAN_400),
        border_radius=10,
        # Remove margins and shadows for static framing
        margin=ft.margin.all(5),  # Minimal margin
        # Add subtle glow effect with shadow
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.colors.with_opacity(0.3, ft.colors.CYAN_400),
            offset=ft.Offset(0, 0)
        )
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