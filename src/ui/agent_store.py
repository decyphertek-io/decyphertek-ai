import flet as ft
from agent.store_manager import StoreManager


class AgentStoreView:
    """Minimal Agents tab driven by StoreManager and personality.json.

    - Renders instantly from local state (no network on render path)
    - Kicks off background registry fetch and refreshes when done
    - Shows default Adminotaur card with Install or Enable/Disable
    - Provides a + button to set custom personality.json URL
    """

    def __init__(self, page: ft.Page, store_manager: StoreManager | None = None):
        self.page = page
        self.store_manager = store_manager or StoreManager()
        self._init_started = False

    def build(self) -> ft.Control:
        # Background registry fetch once; never block UI
        if not self._init_started:
            self._init_started = True
            import threading

            def _bg_fetch():
                try:
                    self.store_manager.fetch_registry()
                except Exception as e:
                    print(f"[AgentStore] Registry fetch error: {e}")
                # Trigger UI refresh if this view is still visible
                try:
                    self.page.update()
                except Exception:
                    pass

            threading.Thread(target=_bg_fetch, daemon=True).start()

        # Render from local state only
        default_id = "adminotaur"
        try:
            installed = self.store_manager.is_installed(default_id)
            enabled = self.store_manager.is_enabled(default_id)
        except Exception:
            installed = False
            enabled = False

        def install_default(_):
            res = self.store_manager.install_agent(default_id)
            self._refresh()

        def toggle_enabled(agent_id: str, enabled_val: bool):
            self.store_manager.set_enabled(agent_id, enabled_val)
            self._refresh()

        # Build action controls per state
        if installed:
            action = ft.Switch(
                value=enabled,
                on_change=lambda e: toggle_enabled(default_id, e.control.value),
                tooltip="Enable/Disable",
            )
        else:
            action = ft.IconButton(
                icon=ft.icons.DOWNLOAD,
                tooltip="Install",
                on_click=install_default,
            )

        # + button bottom-left to add custom store URL
        add_store_fab = ft.IconButton(
            icon=ft.icons.ADD_CIRCLE,
            icon_color=ft.colors.BLUE,
            tooltip="Add Store",
            on_click=lambda e: self._add_custom_store(),
        )

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.SMART_TOY, size=28),
                    ft.Text("Agents", size=22, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.icons.ADD,
                        tooltip="Add Store",
                        on_click=lambda e: self._add_custom_store(),
                    ),
                    ft.IconButton(
                        icon=ft.icons.REFRESH,
                        tooltip="Refresh",
                        on_click=lambda e: self._refresh(),
                    ),
                ]
            ),
            padding=15,
            bgcolor=ft.colors.SURFACE_VARIANT,
        )

        card = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.SMART_TOY, size=22, color=ft.colors.BLUE),
                    ft.Column(
                        [
                            ft.Text("Adminotaur", size=14, weight=ft.FontWeight.W_600),
                            ft.Text(
                                "Default personality from Agent Store",
                                size=11,
                                color=ft.colors.GREY_600,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    action,
                ]
            ),
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=8,
            padding=10,
        )

        return ft.Container(
            content=ft.Column(
                [
                    header,
                    ft.Container(height=10),
                    card,
                    ft.Row([add_store_fab], alignment=ft.MainAxisAlignment.START),
                ],
                expand=True,
                spacing=10,
            ),
            expand=True,
        )

    def _add_custom_store(self):
        url_field = ft.TextField(
            label="Raw personality.json URL",
            hint_text=
            "https://raw.githubusercontent.com/your-org/agent-store/main/personality.json",
            value="",
            expand=True,
        )

        def apply_url(_):
            url = url_field.value.strip()
            if url:
                self.store_manager.set_registry_url(url)
                self.store_manager.fetch_registry()
                self.page.close(dialog)
                self._refresh()

        dialog = ft.AlertDialog(
            title=ft.Text("Add custom Agent Store"),
            content=url_field,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton("Apply", icon=ft.icons.CHECK, on_click=apply_url),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _refresh(self):
        # Rebuild this view in-place
        try:
            parent = self.page
            parent.update()
        except Exception:
            pass


