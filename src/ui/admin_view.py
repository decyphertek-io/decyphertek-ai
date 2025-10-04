
import flet as ft
from pathlib import Path
import subprocess
import sys
from utils.logger import setup_logger

logger = setup_logger()


class AdminView:
    """Admin panel for launching and managing sub-applications"""
    
    def __init__(self, page: ft.Page, on_back=None):
        self.page = page
        self.on_back = on_back
        self.apps = self._get_available_apps()
        self.running_apps = {}  # Track running app processes
        
    def _get_available_apps(self):
        """Get list of available Flet applications"""
        base_path = Path.home() / "Documents" / "git" / "flet"
        
        return [
            {
                "name": "Ansible Manager",
                "description": "Infrastructure automation and management",
                "path": base_path / "ansible" / "src" / "main.py",
                "icon": ft.icons.SETTINGS_APPLICATIONS,
                "color": ft.colors.BLUE_400,
                "enabled": True,
                "requires_config": True,
            },
            {
                "name": "LangTek",
                "description": "Language learning and translation tools",
                "path": base_path / "langtek" / "src" / "main.py",
                "icon": ft.icons.TRANSLATE,
                "color": ft.colors.GREEN_400,
                "enabled": True,
                "requires_config": False,
            },
            {
                "name": "Netrunner",
                "description": "Cyberpunk card game",
                "path": base_path / "netrunner" / "NetRunner-Python" / "main.py",
                "icon": ft.icons.GAMES,
                "color": ft.colors.PURPLE_400,
                "enabled": True,
                "requires_config": False,
            },
        ]
    
    def build(self):
        """Build admin view"""
        return ft.Container(
            content=ft.Column(
                [
                    # Header
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(
                                            ft.icons.APPS,  # Apps icon (grid of squares)
                                            size=28,
                                            color=ft.colors.BLUE_600,
                                        ),
                                        ft.Text(
                                            "Apps",
                                            size=24,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.colors.WHITE,
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                ft.IconButton(
                                    icon=ft.icons.SETTINGS,
                                    on_click=lambda _: self._show_settings(),
                                    visible=self.on_back is not None,  # Only show in standalone mode
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=10,
                        bgcolor=ft.colors.SURFACE_VARIANT,
                    ),
                    
                    # App Grid
                    ft.Container(
                        content=ft.Column(
                            [
                                self._build_app_card(app)
                                for app in self.apps
                            ],
                            spacing=10,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        padding=20,
                        expand=True,
                    ),
                    
                    # Status Bar
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(
                                    ft.icons.APPS,
                                    size=16,
                                    color=ft.colors.BLUE_600,
                                ),
                                ft.Text(
                                    f"Apps Control Center - Enabled Apps: {sum(1 for app in self.apps if app.get('enabled', False))}",
                                    size=12,
                                    color=ft.colors.ON_SURFACE_VARIANT,
                                ),
                            ],
                            spacing=6,
                        ),
                        padding=10,
                        bgcolor=ft.colors.SURFACE_VARIANT,
                    ),
                ],
                spacing=0,
            ),
            expand=True,
        )
    
    def _build_app_card(self, app):
        """Build individual app card"""
        is_running = app["name"] in self.running_apps
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    name=app["icon"],
                                    color=app["color"],
                                    size=40,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            app["name"],
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(
                                            app["description"],
                                            size=12,
                                            color=ft.colors.ON_SURFACE_VARIANT,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Switch(
                                    value=app["enabled"],
                                    on_change=lambda e, a=app: self._toggle_app(a, e.control.value),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        
                        # Configuration button (only if needed)
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.icons.SETTINGS,
                                    on_click=lambda _, a=app: self._configure_app(a),
                                    disabled=not app["requires_config"],
                                    visible=app["requires_config"],
                                ),
                            ],
                            spacing=10,
                        ),
                        
                        # Status indicator
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        name=ft.icons.CIRCLE,
                                        color=ft.colors.GREEN if app["enabled"] else ft.colors.GREY,
                                        size=12,
                                    ),
                                    ft.Text(
                                        "Enabled" if app["enabled"] else "Disabled",
                                        size=12,
                                    ),
                                ],
                                spacing=5,
                            ),
                            padding=ft.padding.only(top=10),
                        ),
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
        )
    
    def _launch_app(self, app):
        """Launch a Flet application as subprocess"""
        try:
            if not app["path"].exists():
                self._show_error(f"App not found: {app['path']}")
                return
            
            logger.info(f"Launching {app['name']}")
            
            # Launch app in new window using Poetry
            process = subprocess.Popen(
                ["poetry", "run", "python", str(app["path"])],
                cwd=app["path"].parent.parent,  # Go to project root
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            self.running_apps[app["name"]] = process
            self._show_success(f"{app['name']} launched successfully")
            self.page.update()
            
        except Exception as e:
            logger.error(f"Failed to launch {app['name']}: {e}")
            self._show_error(f"Failed to launch: {e}")
    
    def _stop_app(self, app):
        """Stop a running application"""
        try:
            if app["name"] in self.running_apps:
                process = self.running_apps[app["name"]]
                process.terminate()
                process.wait(timeout=5)
                del self.running_apps[app["name"]]
                
                logger.info(f"Stopped {app['name']}")
                self._show_success(f"{app['name']} stopped")
                self.page.update()
                
        except Exception as e:
            logger.error(f"Failed to stop {app['name']}: {e}")
            self._show_error(f"Failed to stop: {e}")
    
    def _toggle_app(self, app, enabled):
        """Enable/disable an application"""
        app["enabled"] = enabled
        logger.info(f"{app['name']} {'enabled' if enabled else 'disabled'}")
        self.page.update()
    
    def _configure_app(self, app):
        """Open app configuration dialog"""
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Configure {app['name']}"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.TextField(
                            label="API Key",
                            password=True,
                            hint_text="Enter API key if required",
                        ),
                        ft.TextField(
                            label="Configuration Path",
                            value=str(app["path"].parent / "config.json"),
                        ),
                        ft.Checkbox(
                            label="Auto-start on launch",
                            value=False,
                        ),
                    ],
                    spacing=10,
                    tight=True,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Save", on_click=close_dialog),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_settings(self):
        """Show admin settings dialog"""
        try:
            def close_dialog(e):
                dialog.open = False
                self.page.update()
            
            dialog = ft.AlertDialog(
            title=ft.Text("Admin Settings"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Global Settings", weight=ft.FontWeight.BOLD),
                        ft.Checkbox(
                            label="Enable MCP Server Integration",
                            value=True,
                        ),
                        ft.Checkbox(
                            label="Allow background app execution",
                            value=True,
                        ),
                        ft.Checkbox(
                            label="Auto-restart crashed apps",
                            value=False,
                        ),
                        ft.Divider(),
                        ft.Text("Security", weight=ft.FontWeight.BOLD),
                        ft.Checkbox(
                            label="Require authentication for app launch",
                            value=False,
                        ),
                        ft.TextField(
                            label="Max concurrent apps",
                            value="3",
                            keyboard_type=ft.KeyboardType.NUMBER,
                        ),
                    ],
                    spacing=10,
                    tight=True,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Save", on_click=close_dialog),
            ],
        )
        
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            
        except Exception as e:
            logger.error(f"Error showing admin settings: {e}")
            self._show_error(f"Failed to show settings: {str(e)}")
    
    def _show_error(self, message):
        """Show error snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.colors.RED_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _show_success(self, message):
        """Show success snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.colors.GREEN_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def cleanup(self):
        """Cleanup running apps on exit"""
        for app_name, process in self.running_apps.items():
            try:
                process.terminate()
                logger.info(f"Terminated {app_name}")
            except:
                pass
