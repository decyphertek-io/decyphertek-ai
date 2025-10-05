import flet as ft


class MCPStoreView:
    """MCP Store tab UI isolated from dashboard logic.

    - Renders instantly
    - Purely UI; no blocking network calls
    """

    def __init__(self, page: ft.Page):
        self.page = page

    def build(self) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    # AppBar
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.CLOUD, size=28),
                                ft.Text(
                                    "MCP Servers",
                                    size=22,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.Container(expand=True),
                                ft.IconButton(
                                    icon=ft.icons.REFRESH,
                                    tooltip="Refresh",
                                    on_click=lambda e: self._refresh()
                                ),
                            ]
                        ),
                        padding=15,
                        bgcolor=ft.colors.SURFACE_VARIANT
                    ),

                    # MCP content
                    ft.Container(
                        content=ft.Column([
                            ft.Container(height=20),

                            # Smithery AI
                            ft.Row([
                                ft.Text("Smithery AI", size=14, weight=ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                                ft.Icon(
                                    ft.icons.CHECK_CIRCLE if False else ft.icons.WARNING,
                                    size=20,
                                    color=ft.colors.GREEN if False else ft.colors.ORANGE
                                ),
                            ]),
                            ft.Container(height=5),
                            ft.Text(
                                "Build FastMCP servers with session-scoped configuration",
                                size=12,
                                color=ft.colors.GREY_600
                            ),
                            ft.Container(height=10),
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.icons.ROCKET_LAUNCH, size=20, color=ft.colors.PURPLE),
                                        ft.Text("Status: ", size=12, color=ft.colors.GREY_700),
                                        ft.Text(
                                            "Not Configured",
                                            size=12,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.colors.ORANGE
                                        ),
                                    ]),
                                    ft.Container(height=10),
                                    ft.Row([
                                        ft.ElevatedButton(
                                            "🔑 Configure API",
                                            on_click=lambda e: self._show_smithery_config(),
                                            expand=True,
                                            style=ft.ButtonStyle(
                                                bgcolor=ft.colors.PURPLE,
                                                color=ft.colors.WHITE
                                            )
                                        ),
                                        ft.TextButton(
                                            "📖 Docs",
                                            on_click=lambda e: self.page.launch_url("https://pypi.org/project/smithery/"),
                                            style=ft.ButtonStyle(color=ft.colors.PURPLE)
                                        ),
                                    ]),
                                ]),
                                bgcolor=ft.colors.PURPLE_50,
                                border_radius=10,
                                padding=15
                            ),

                            ft.Container(height=20),
                            ft.Divider(),
                            ft.Container(height=20),

                            # Custom MCP Store
                            ft.Text("Custom MCP Store", size=14, weight=ft.FontWeight.BOLD),
                            ft.Container(height=5),
                            ft.Text(
                                "Connect to your custom MCP server repository",
                                size=12,
                                color=ft.colors.GREY_600
                            ),
                            ft.Container(height=10),
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.icons.STORAGE, size=20, color=ft.colors.BLUE),
                                        ft.Text("GitHub Repository", weight=ft.FontWeight.W_500),
                                    ]),
                                    ft.Container(height=10),
                                    ft.TextField(
                                        label="Repository URL",
                                        hint_text="https://github.com/username/mcp-store",
                                        border_color=ft.colors.BLUE_200,
                                        expand=True
                                    ),
                                    ft.Container(height=10),
                                    ft.Row([
                                        ft.ElevatedButton(
                                            "🔍 Browse Servers",
                                            on_click=lambda e: self._show_custom_store_browser(),
                                            expand=True,
                                            style=ft.ButtonStyle(
                                                bgcolor=ft.colors.BLUE,
                                                color=ft.colors.WHITE
                                            )
                                        ),
                                        ft.TextButton(
                                            "Default Store",
                                            on_click=lambda e: self._load_default_mcp_store(),
                                            style=ft.ButtonStyle(color=ft.colors.BLUE)
                                        ),
                                    ]),
                                ]),
                                bgcolor=ft.colors.BLUE_50,
                                border_radius=10,
                                padding=15
                            ),

                            ft.Container(height=20),
                            ft.Divider(),
                            ft.Container(height=20),

                            # Available Servers from Store (static placeholders; wire to real list later)
                            ft.Row([
                                ft.Text("Available Servers", size=14, weight=ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                            ]),
                            ft.Container(height=10),

                            ft.Column([
                                self._create_mcp_server_card("Web Search", "Search the web using Python", ft.icons.SEARCH, ft.colors.GREEN, "web-search"),
                                self._create_mcp_server_card("Nextcloud", "Access Nextcloud files and folders", ft.icons.CLOUD, ft.colors.BLUE, "nextcloud"),
                                self._create_mcp_server_card("Google Drive", "Import documents from Google Drive", ft.icons.FOLDER, ft.colors.GREEN, "google-drive"),
                            ], scroll=ft.ScrollMode.AUTO, expand=True),

                        ], scroll=ft.ScrollMode.AUTO, expand=True),
                        padding=20,
                        expand=True
                    ),
                ],
                expand=True
            ),
            expand=True
        )

    def _create_mcp_server_card(self, title: str, description: str, icon, color, server_id: str, connected: bool = False):
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=24, color=color),
                ft.Column([
                    ft.Row([
                        ft.Text(title, size=14, weight=ft.FontWeight.W_500),
                        ft.Icon(
                            ft.icons.CHECK_CIRCLE if connected else ft.icons.CIRCLE_OUTLINED,
                            size=14,
                            color=ft.colors.GREEN if connected else ft.colors.GREY_400
                        ),
                    ], spacing=5),
                    ft.Text(description, size=11, color=ft.colors.GREY_600),
                ], spacing=2, expand=True),
                ft.Row([
                    ft.IconButton(
                        icon=ft.icons.SETTINGS if connected else ft.icons.ADD,
                        tooltip="Configure" if connected else "Connect",
                        icon_color=ft.colors.BLUE if connected else ft.colors.GREEN,
                        on_click=lambda e: self._show_mcp_installer(server_id)
                    ),
                ]),
            ]),
            bgcolor=ft.colors.GREEN_50 if connected else ft.colors.SURFACE_VARIANT,
            border_radius=8,
            padding=10
        )

    def _show_mcp_installer(self, server_name: str):
        info_map = {
            "nextcloud": {
                "title": "Nextcloud MCP Server",
                "description": "Connect to your Nextcloud instance to import files and folders",
                "github": "https://github.com/decyphertek-io/mcp-store/tree/main/servers/nextcloud",
                "icon": ft.icons.CLOUD,
                "color": ft.colors.BLUE
            }
        }
        info = info_map.get(server_name, {
            "title": f"{server_name} MCP Server",
            "description": "Installation coming soon",
            "github": "https://github.com/decyphertek-io/mcp-store/tree/main/servers",
            "icon": ft.icons.CLOUD,
            "color": ft.colors.BLUE
        })

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(info["icon"], color=info["color"]),
                ft.Text(info["title"]),
            ]),
            content=ft.Column([
                ft.Text(info["description"]),
                ft.Container(height=10),
                ft.Text("GitHub Repository:", size=12, weight=ft.FontWeight.BOLD),
                ft.TextButton(
                    info["github"],
                    on_click=lambda e: self.page.launch_url(info["github"]),
                    style=ft.ButtonStyle(color=ft.colors.BLUE)
                ),
            ], tight=True),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.page.close(dialog)),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _show_smithery_config(self):
        api_key_field = ft.TextField(label="Smithery API Key", hint_text="sk-smithery-...", password=True, can_reveal_password=True)
        server_url_field = ft.TextField(label="Server URL (optional)", hint_text="http://localhost:8000")

        def save_config(e):
            self.page.close(dialog)
            snackbar = ft.SnackBar(content=ft.Text("✓ Smithery configured!"), bgcolor=ft.colors.GREEN)
            self.page.overlay.append(snackbar)
            snackbar.open = True
            self._refresh()

        dialog = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.icons.ROCKET_LAUNCH, color=ft.colors.PURPLE), ft.Text("Configure Smithery")]),
            content=ft.Column([
                ft.Text("Enter your Smithery API credentials", size=12, color=ft.colors.GREY_600),
                ft.Container(height=15),
                api_key_field,
                ft.Container(height=10),
                server_url_field,
            ], tight=True, height=220),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton("Save", icon=ft.icons.SAVE, on_click=save_config, style=ft.ButtonStyle(bgcolor=ft.colors.PURPLE, color=ft.colors.WHITE))
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _show_custom_store_browser(self):
        dialog = ft.AlertDialog(
            title=ft.Text("🔍 Browse Custom MCP Store"),
            content=ft.Column([
                ft.Text("Enter your GitHub repository URL:", size=12, color=ft.colors.GREY_600),
                ft.Container(height=10),
                ft.TextField(label="GitHub URL", hint_text="https://github.com/decyphertek-io/mcp-store"),
            ], tight=True),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.page.close(dialog)),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _load_default_mcp_store(self):
        snackbar = ft.SnackBar(content=ft.Text("✓ Loaded default MCP store: github.com/decyphertek-io/mcp-store"), bgcolor=ft.colors.GREEN)
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

    def _refresh(self):
        self.page.update()

