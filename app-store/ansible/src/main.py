import flet as ft
import importlib
import os

# Decyphertek UI color scheme
DECYPHERTEK_DARK_BG = "#212529"
DECYPHERTEK_SIDEBAR_BG = "#343a40"
DECYPHERTEK_PRIMARY = "#007bff"
DECYPHERTEK_SUCCESS = "#28a745"
DECYPHERTEK_WARNING = "#ffc107"
DECYPHERTEK_DANGER = "#dc3545"
DECYPHERTEK_TEXT_PRIMARY = "#ffffff"
DECYPHERTEK_TEXT_SECONDARY = "#adb5bd"

class DecyphertekMainUI(ft.Container):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.current_view = "Dashboard"
        self.setup_page()
        self.content = self.build()

    def setup_page(self):
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window_width = 1400
        self.page.window_height = 900
        self.page.title = "Decyphertek Sysadmin UI"
        self.page.padding = 0
        self.page.bgcolor = DECYPHERTEK_DARK_BG

    def build(self):
        # Left sidebar navigation
        sidebar = ft.Container(
            width=200,
            bgcolor=DECYPHERTEK_SIDEBAR_BG,
            content=ft.Column([
                # Decyphertek Logo/Header
                ft.Container(
                    padding=ft.padding.all(15),
                    content=ft.Row([
                        ft.Icon(ft.Icons.BUSINESS, color=DECYPHERTEK_PRIMARY, size=24),
                        ft.Text("Decyphertek", size=16, weight="bold", color=DECYPHERTEK_TEXT_PRIMARY)
                    ])
                ),
                ft.Divider(color=DECYPHERTEK_TEXT_SECONDARY, height=1),
                
                # Navigation Menu
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8),
                    expand=True,
                    content=ft.Column([
                        self.create_nav_item("Dashboard", ft.Icons.DASHBOARD, True),
                        self.create_nav_item("Projects", ft.Icons.FOLDER_OPEN, False),
                        self.create_nav_item("Schedule", ft.Icons.SCHEDULE, False),
                        self.create_nav_item("Ansible", ft.Icons.TERMINAL, False),
                        self.create_nav_item("Bash Scripts", ft.Icons.LAYERS, False),
                        self.create_nav_item("Networking", ft.Icons.ROUTER, False),
                        self.create_nav_item("Text Editor", ft.Icons.EDIT, False),
                        self.create_nav_item("Terminal", ft.Icons.TERMINAL, False),
                        self.create_nav_item("Settings", ft.Icons.SETTINGS, False),
                    ], spacing=3)
                )
            ], expand=True)
        )

        # Top header bar
        header = ft.Container(
            height=60,
            bgcolor=DECYPHERTEK_SIDEBAR_BG,
            padding=ft.padding.symmetric(horizontal=20),
            content=ft.Row([
                ft.Text(self.current_view, size=24, weight="bold", color=DECYPHERTEK_TEXT_PRIMARY),
                ft.Container(expand=True),
                ft.IconButton(ft.Icons.SEARCH, icon_color=DECYPHERTEK_TEXT_SECONDARY),
                ft.IconButton(ft.Icons.NOTIFICATIONS, icon_color=DECYPHERTEK_TEXT_SECONDARY),
                ft.IconButton(ft.Icons.PERSON, icon_color=DECYPHERTEK_TEXT_SECONDARY),
            ])
        )

        # Main content area
        self.main_content = ft.Container(
            expand=True,
            padding=ft.padding.all(20),
            bgcolor=DECYPHERTEK_DARK_BG,
            content=self.get_dashboard_content()
        )

        # Main layout
        return ft.Container(
            expand=True,
            content=ft.Row([
                sidebar,
                ft.VerticalDivider(width=1, color=DECYPHERTEK_TEXT_SECONDARY),
                ft.Column([
                    header,
                    ft.Divider(height=1, color=DECYPHERTEK_TEXT_SECONDARY),
                    self.main_content
                ], expand=True, spacing=0)
            ], expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
        )

    def create_nav_item(self, label, icon, is_selected):
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=DECYPHERTEK_PRIMARY if is_selected else "#495057",
            border_radius=5,
            content=ft.Row([
                ft.Icon(icon, color=DECYPHERTEK_TEXT_PRIMARY, size=18),
                ft.Text(label, color=DECYPHERTEK_TEXT_PRIMARY, size=14)
            ]),
            on_click=lambda e, view=label: self.switch_view(view)
        )

    def get_dashboard_content(self):
        return ft.Column([
            # Stat cards
            ft.Column([
                ft.Row([
                    self.create_stat_card("-", "Projects", DECYPHERTEK_PRIMARY),
                    self.create_stat_card("-", "Schedule", DECYPHERTEK_PRIMARY),
                    self.create_stat_card("-", "Ansible", DECYPHERTEK_PRIMARY),
                    self.create_stat_card("-", "Bash Scripts", DECYPHERTEK_PRIMARY),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Container(height=20),
                ft.Row([
                    self.create_stat_card("-", "Networking", DECYPHERTEK_PRIMARY),
                    self.create_stat_card("-", "Text Editor", DECYPHERTEK_PRIMARY),
                    self.create_stat_card("-", "Terminal", DECYPHERTEK_PRIMARY),
                    self.create_stat_card("-", "Settings", DECYPHERTEK_PRIMARY),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ]),
        ])

    def create_stat_card(self, value, label, color):
        return ft.Container(
            width=200,
            height=130,
            bgcolor=DECYPHERTEK_SIDEBAR_BG,
            border_radius=10,
            padding=ft.padding.all(15),
            content=ft.Column([
                ft.Text(value, size=32, weight="bold", color=color),
                ft.Text(label, size=16, color=DECYPHERTEK_TEXT_SECONDARY, text_align=ft.TextAlign.CENTER)
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            alignment=ft.MainAxisAlignment.CENTER, 
            spacing=10)
        )

    def switch_view(self, view_name):
        self.current_view = view_name
        
        # Update navigation selection
        sidebar_column = self.content.content.controls[0].content
        nav_menu_container = sidebar_column.controls[2]
        nav_menu_column = nav_menu_container.content
        
        # Update all nav items
        for nav_item in nav_menu_column.controls:
            nav_text = nav_item.content.controls[1]
            if nav_text.value == view_name:
                nav_item.bgcolor = DECYPHERTEK_PRIMARY
            else:
                nav_item.bgcolor = "#495057"
            
        # Update header title
        header_container = self.content.content.controls[2].controls[0]
        header_container.content.controls[0].value = view_name
        
        # Clear and switch content based on view
        self.main_content.content = None
        if view_name == "Dashboard":
            self.main_content.content = self.get_dashboard_content()
        else:
            try:
                module_name = view_name.lower().replace(" ", "_")
                spec = importlib.util.spec_from_file_location(module_name, f"./{module_name}.py")
                module = importlib.util.module_from_spec(spec)
                spec.module = module
                importlib.util.exec_spec(spec, module)
                
                if hasattr(module, 'build_tab_content'):
                    self.main_content.content = module.build_tab_content(self.page)
                else:
                    self.main_content.content = ft.Column([
                        ft.Text(f"{view_name} functionality will be implemented here", 
                                size=16, 
                                color=DECYPHERTEK_TEXT_SECONDARY)
                    ])
            except Exception as e:
                self.main_content.content = ft.Column([
                    ft.Text(f"Error loading {view_name} tab: {str(e)}", 
                            size=16, 
                            color=DECYPHERTEK_DANGER)
                ])
        
        # Update the entire page to reflect changes
        self.page.update()

def main(page: ft.Page):
    app = DecyphertekMainUI(page)
    page.add(app)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
