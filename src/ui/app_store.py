
import flet as ft
from pathlib import Path
import json
import threading
import subprocess
import sys
import os
from utils.logger import setup_logger
from agent.store_manager import StoreManager

logger = setup_logger()


class AdminView:
    """Apps store: download/enable apps from remote registry"""

    def __init__(self, page: ft.Page, on_back=None, store_manager: StoreManager | None = None):
        self.page = page
        self.on_back = on_back
        self.store = store_manager or StoreManager()
        self.registry_url = "https://raw.githubusercontent.com/decyphertek-io/app-store/main/app.json"
        self.cache_path = Path("src/store/app/cache.json")
        self.local_root = Path("src/store/app")
        self.apps = self._load_cache()
        self.running_apps = {}  # Track running app processes
        self._ensure_background_sync()

    def _load_cache(self):
        try:
            if self.cache_path.exists():
                data = json.loads(self.cache_path.read_text(encoding="utf-8"))
                apps = []
                for aid, info in (data.get("apps") or {}).items():
                    apps.append(self._normalize_app(aid, info))
                return apps
        except Exception as e:
            logger.error(f"[AppStore] cache load error: {e}")
        return []

    def _write_cache(self, registry: dict) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"[AppStore] cache write error: {e}")

    def _normalize_app(self, app_id: str, info: dict) -> dict:
        installed = self.store.is_app_installed(app_id) if hasattr(self.store, "is_app_installed") else False
        ready = self.store.is_app_ready(app_id) if hasattr(self.store, "is_app_ready") else False
        enabled = self.store.is_app_enabled(app_id) if hasattr(self.store, "is_app_enabled") else False
        
        return {
            "id": app_id,
            "name": info.get("name") or app_id,
            "description": info.get("description") or "",
            "icon": ft.icons.APPS,
            "color": ft.colors.BLUE_400,
            "installed": installed,
            "ready": ready,
            "enabled": enabled,
        }

    def _ensure_background_sync(self):
        def _bg():
            try:
                if hasattr(self.store, "set_app_registry_url"):
                    self.store.set_app_registry_url(self.registry_url)
                registry = self.store.fetch_app_registry() if hasattr(self.store, "fetch_app_registry") else {}
                if registry:
                    self._write_cache(registry)
                    new_apps = []
                    for aid, info in (registry.get("apps") or {}).items():
                        new_apps.append(self._normalize_app(aid, info))
                    self.apps = new_apps
                    self._refresh_view()
            except Exception as e:
                logger.error(f"[AppStore] registry sync error: {e}")

        threading.Thread(target=_bg, daemon=True).start()

    def _refresh_view(self):
        try:
            if hasattr(self, "_app_list_column") and self._app_list_column is not None:
                self._app_list_column.controls = [self._build_app_card(app) for app in self.apps]
                self._app_list_column.update()
            self.page.update()
        except Exception:
            pass
    
    def build(self):
        """Build admin view"""
        return ft.Container(
            content=ft.Column(
                [
                    # Header (match Agent/MCP layout with Add/Refresh)
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.icons.APPS, size=28, color=ft.colors.BLUE_600),
                                        ft.Text("Apps", size=22, weight=ft.FontWeight.BOLD),
                                    ],
                                    spacing=8,
                                ),
                                ft.Container(expand=True),
                                ft.IconButton(
                                    icon=ft.icons.ADD,
                                    tooltip="Add Store",
                                    on_click=lambda e: self._add_custom_store(),
                                ),
                                ft.IconButton(
                                    icon=ft.icons.REFRESH,
                                    tooltip="Refresh",
                                    on_click=lambda e: self._ensure_background_sync(),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=10,
                        bgcolor=ft.colors.SURFACE_VARIANT,
                    ),
                    
                    # App Grid (renders instantly from cache)
                    ft.Container(
                        content=self._init_app_list(),
                        padding=20,
                        expand=True,
                    ),
                    
                    # Status bar removed to match Agent/MCP minimal layout
                ],
                spacing=0,
            ),
            expand=True,
        )

    def _init_app_list(self) -> ft.Column:
        # Create and keep a reference so we can update in-place after background sync
        self._app_list_column = ft.Column(
            [self._build_app_card(app) for app in self.apps],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
        return self._app_list_column
    
    def _build_app_card(self, app):
        """Build individual app card (download/enable)"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    name=app.get("icon", ft.icons.APPS),
                                    color=app.get("color", ft.colors.BLUE_400),
                                    size=40,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            app.get("name") or app.get("id"),
                                            size=14,
                                            weight=ft.FontWeight.W_600,
                                        ),
                                        ft.Text(
                                            app.get("description", ""),
                                            size=11,
                                            color=ft.colors.GREY_600,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Row([
                                    # Download button - show when not installed
                                    ft.IconButton(
                                        icon=ft.icons.DOWNLOAD,
                                        tooltip="Download & Setup",
                                        on_click=lambda _, a=app: self._on_download(a),
                                        visible=not app.get("installed", False),
                                    ),
                                    # Play button - show when installed, ready, and enabled
                                    ft.IconButton(
                                        icon=ft.icons.PLAY_ARROW,
                                        tooltip="Launch App",
                                        on_click=lambda _, a=app: self._on_launch(a),
                                        visible=app.get("installed", False) and app.get("ready", False) and app.get("enabled", False),
                                        icon_color=ft.colors.GREEN_600,
                                    ),
                                    # Enable/Disable switch - show when installed and ready
                                    ft.Switch(
                                        value=app.get("enabled", False),
                                        on_change=lambda e, a=app: self._on_toggle_enabled(a, e.control.value),
                                        visible=app.get("installed", False) and app.get("ready", False),
                                    ),
                                ], spacing=6),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        # Status indicator removed to match Agent/MCP layout
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
        )

    def _on_download(self, app: dict):
        app_id = app.get("id") or app.get("name")
        if not app_id:
            return
        self._show_success(f"Downloading and setting up {app_id}...")

        def _bg():
            try:
                res = self.store.install_app(app_id) if hasattr(self.store, "install_app") else {"success": False, "error": "installer missing"}
                if res.get("success"):
                    # Update app state
                    for a in self.apps:
                        if a.get("id") == app_id:
                            a["installed"] = True
                            a["ready"] = res.get("ready_to_run", False)
                            a["enabled"] = res.get("ready_to_run", False)  # Auto-enable if ready
                            break
                    
                    if res.get("ready_to_run"):
                        self._show_success(f"✅ {app_id} installed and ready to run!")
                    else:
                        self._show_success(f"✅ {app_id} installed successfully")
                else:
                    self._show_error(f"❌ Install failed: {res.get('error')}")
            except Exception as e:
                self._show_error(f"❌ Install error: {e}")
            finally:
                self._refresh_view()

        threading.Thread(target=_bg, daemon=True).start()

    def _on_toggle_enabled(self, app: dict, enabled: bool):
        app_id = app.get("id") or app.get("name")
        if not app_id:
            return
        try:
            if hasattr(self.store, "set_app_enabled"):
                self.store.set_app_enabled(app_id, bool(enabled))
            app["enabled"] = bool(enabled)
            self.page.update()
        except Exception as e:
            self._show_error(f"Toggle failed: {e}")
    
    def _on_launch(self, app: dict):
        """Launch a Flet app within the app window"""
        app_id = app.get("id") or app.get("name")
        if not app_id:
            return
        
        self._show_success(f"Launching {app_id}...")
        
        def _launch_app():
            try:
                # Get launch info from store manager
                launch_info = self.store.get_app_launch_info(app_id) if hasattr(self.store, "get_app_launch_info") else None
                
                if not launch_info or not launch_info.get("success"):
                    error_msg = launch_info.get("error", "Unknown error") if launch_info else "Store manager not available"
                    self._show_error(f"❌ Cannot launch {app_id}: {error_msg}")
                    return
                
                main_script = Path(launch_info["main_script"])
                if not main_script.exists():
                    self._show_error(f"❌ Main script not found: {main_script}")
                    return
                
                # Launch the app in a new window
                self._launch_flet_app(app_id, main_script)
                
            except Exception as e:
                self._show_error(f"❌ Launch failed: {e}")
        
        threading.Thread(target=_launch_app, daemon=True).start()
    
    def _launch_flet_app(self, app_id: str, main_py_path: Path):
        """Launch a Flet app within the chat window"""
        try:
            # Check if app is already running
            if app_id in self.running_apps:
                self._show_error(f"❌ {app_id} is already running")
                return
            
            # For now, launch in external window
            # TODO: Integrate with chat window for Flet-in-Flet experience
            app_window = FletAppWindow(app_id, main_py_path, self.page, self)
            app_window.show()
            
            # Track the running app
            self.running_apps[app_id] = app_window
            self._show_success(f"✅ {app_id} launched successfully!")
            
        except Exception as e:
            self._show_error(f"❌ Failed to launch {app_id}: {e}")


class FletAppWindow:
    """Container for running Flet apps within the main application"""
    
    def __init__(self, app_id: str, main_py_path: Path, parent_page: ft.Page, parent_view=None):
        self.app_id = app_id
        self.main_py_path = main_py_path
        self.parent_page = parent_page
        self.parent_view = parent_view  # Reference to AdminView for cleanup
        self.app_process = None
        self.app_page = None
        
    def show(self):
        """Show the app in a new window or embedded view"""
        try:
            # For now, launch in a new process
            # In the future, this could be embedded in the main UI
            self._launch_external()
            
        except Exception as e:
            print(f"Error launching {self.app_id}: {e}")
    
    def _launch_external(self):
        """Launch the app in a separate process"""
        try:
            # Change to the app directory
            app_dir = self.main_py_path.parent
            
            # Launch the Flet app
            cmd = [sys.executable, "-m", "flet", "run", str(self.main_py_path)]
            
            self.app_process = subprocess.Popen(
                cmd,
                cwd=app_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"Launched {self.app_id} with PID {self.app_process.pid}")
            
        except Exception as e:
            print(f"Failed to launch {self.app_id}: {e}")
    
    def close(self):
        """Close the app"""
        if self.app_process:
            try:
                self.app_process.terminate()
                self.app_process.wait(timeout=5)
            except:
                self.app_process.kill()
            self.app_process = None
        
        # Remove from parent view tracking
        if self.parent_view and self.app_id in self.parent_view.running_apps:
            del self.parent_view.running_apps[self.app_id]
    
    # Removed per remote-registry design; configuration handled by apps themselves
    
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
