import flet as ft
import subprocess
import threading
import queue
import os
from pathlib import Path

def launch_terminal(chat_view):
    """Launches the terminal emulator within the chat window."""
    
    # Terminal state
    terminal_output = []
    command_queue = queue.Queue()
    current_directory = str(Path.home())
    
    def close_terminal(e):
        """Close the terminal and return to chat"""
        # Remove terminal from chat list
        chat_view.chat_list.controls = [control for control in chat_view.chat_list.controls 
                                      if not hasattr(control, 'terminal_container')]
        chat_view.page.update()
        print("[Terminal] Closed")
    
    def execute_command(command):
        """Execute a command using pyterminal-emulator"""
        try:
            # Use pyterminal-emulator to execute the command
            result = subprocess.run(
                ['python', '-c', f'import pyterminal_emulator; pyterminal_emulator.run_command("{command}")'],
                capture_output=True,
                text=True,
                cwd=current_directory,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def run_command(e):
        """Handle command execution"""
        command = command_input.value.strip()
        if not command:
            return
        
        # Add command to output
        terminal_output.append(f"$ {command}")
        
        # Execute command
        result = execute_command(command)
        if result:
            terminal_output.append(result)
        
        # Update display
        update_terminal_display()
        
        # Clear input
        command_input.value = ""
        command_input.update()
    
    def update_terminal_display():
        """Update the terminal output display"""
        output_text = "\n".join(terminal_output[-50:])  # Show last 50 lines
        terminal_display.value = output_text
        terminal_display.update()
        
        # Auto-scroll to bottom
        terminal_display.scroll_to(
            offset=-1,
            duration=100,
            curve=ft.AnimationCurve.EASE_OUT
        )
    
    def clear_terminal(e):
        """Clear the terminal output"""
        terminal_output.clear()
        update_terminal_display()
    
    def show_help(e):
        """Show available commands"""
        help_text = """Available Commands:
ls          - List directory contents
cd <dir>    - Change directory
pwd         - Show current path
mkdir <dir> - Make directory
rm <file>   - Remove file/folder
whoami      - Show current user
cp <src> <dst> - Copy files
mv <src> <dst> - Move/rename files
touch <file> - Create empty files
cat <file>  - Display file content
head <file> - Show top lines of a file
tail <file> - Show last lines of a file
find <pattern> - Search files
chmod <mode> <file> - Change permissions
git <cmd>   - Git commands
python <script> - Run Python scripts
curl <url>  - Fetch from URL
wget <url>  - Download from URL
clear       - Clear terminal
help        - Show this help
exit        - Close terminal"""
        
        terminal_output.append("$ help")
        terminal_output.append(help_text)
        update_terminal_display()
    
    # Initialize terminal with welcome message
    terminal_output.extend([
        "╔══════════════════════════════════════════════════════════════╗",
        "║                    TERMINAL EMULATOR                         ║",
        "║              Powered by pyterminal-emulator                  ║",
        "╚══════════════════════════════════════════════════════════════╝",
        "",
        f"Current directory: {current_directory}",
        "Type 'help' for available commands or 'exit' to close terminal.",
        ""
    ])
    
    # Create terminal display
    terminal_display = ft.TextField(
        value="\n".join(terminal_output),
        read_only=True,
        multiline=True,
        min_lines=25,
        max_lines=25,
        border_color=ft.colors.GREEN_400,
        bgcolor=ft.colors.BLACK,
        color=ft.colors.GREEN_300,
        text_style=ft.TextStyle(
            font_family="monospace",
            size=12,
            color=ft.colors.GREEN_300
        )
    )
    
    # Create command input
    command_input = ft.TextField(
        value="",
        hint_text="Enter command...",
        border_color=ft.colors.GREEN_400,
        bgcolor=ft.colors.BLACK,
        color=ft.colors.GREEN_300,
        text_style=ft.TextStyle(
            font_family="monospace",
            size=12,
            color=ft.colors.GREEN_300
        ),
        on_submit=run_command
    )
    
    # Create terminal container with Tron theme
    terminal_container = ft.Container(
        content=ft.Column(
            controls=[
                # Terminal header with Tron theme
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("💻 TERMINAL EMULATOR", 
                                           size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_400,
                                           font_family="monospace"),
                                    ft.Container(expand=True),  # Spacer
                                    ft.IconButton(
                                        icon=ft.icons.HELP,
                                        icon_color=ft.colors.BLUE_400,
                                        tooltip="Show Help",
                                        on_click=show_help
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.CLEAR,
                                        icon_color=ft.colors.ORANGE_400,
                                        tooltip="Clear Terminal",
                                        on_click=clear_terminal
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.CLOSE,
                                        icon_color=ft.colors.RED_400,
                                        tooltip="Close Terminal",
                                        on_click=close_terminal
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Text("Linux terminal emulator with pyterminal-emulator", 
                                   size=10, color=ft.colors.GREEN_300, font_family="monospace")
                        ],
                        spacing=5
                    ),
                    bgcolor=ft.colors.BLACK,
                    padding=10,
                    border=ft.border.all(1, ft.colors.GREEN_400),
                    border_radius=ft.border_radius.only(
                        top_left=10, top_right=10
                    )
                ),
                
                # Terminal output section
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("📺 Terminal Output", 
                                   weight=ft.FontWeight.BOLD, size=12, color=ft.colors.GREEN_400,
                                   font_family="monospace"),
                            terminal_display,
                        ],
                        spacing=5
                    ),
                    padding=10,
                    bgcolor=ft.colors.BLACK,
                    border=ft.border.all(1, ft.colors.GREEN_400)
                ),
                
                # Command input section
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("⌨️ Command Input", 
                                   weight=ft.FontWeight.BOLD, size=12, color=ft.colors.GREEN_400,
                                   font_family="monospace"),
                            ft.Row(
                                controls=[
                                    command_input,
                                    ft.ElevatedButton(
                                        "EXECUTE",
                                        on_click=run_command,
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.colors.BLACK,
                                            color=ft.colors.GREEN_400,
                                            side=ft.BorderSide(1, ft.colors.GREEN_400)
                                        )
                                    )
                                ],
                                spacing=10
                            )
                        ],
                        spacing=5
                    ),
                    padding=10,
                    bgcolor=ft.colors.BLACK,
                    border=ft.border.all(1, ft.colors.GREEN_400),
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
        height=min(600, chat_view.page.height - 200) if hasattr(chat_view.page, 'height') and chat_view.page.height else 500,  # Dynamic height based on available space
        bgcolor=ft.colors.BLACK,
        border=ft.border.all(2, ft.colors.GREEN_400),
        border_radius=10,
        margin=ft.margin.all(5),  # Minimal margin
        # Add subtle glow effect with shadow
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.colors.with_opacity(0.3, ft.colors.GREEN_400),
            offset=ft.Offset(0, 0)
        )
    )
    
    # Mark this container as the terminal for easy removal
    terminal_container.terminal_container = True
    
    # Add terminal to chat list as a static, contained element
    chat_view.chat_list.controls.append(terminal_container)
    
    # Update the page to render the terminal
    chat_view.page.update()
    
    # Scroll to the terminal smoothly
    chat_view.chat_list.scroll_to(
        offset=-1,
        duration=500,
        curve=ft.AnimationCurve.EASE_OUT
    )
    
    return terminal_container
