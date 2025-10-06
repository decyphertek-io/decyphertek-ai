import flet as ft

def launch_docs_menu(chat_view):
    """Launches the docs menu with icon-based options within the chat window."""
    
    def close_docs_menu(e):
        """Close the docs menu and return to chat"""
        # Remove docs menu from chat list
        chat_view.chat_list.controls = [control for control in chat_view.chat_list.controls 
                                      if not hasattr(control, 'docs_menu_container')]
        chat_view.page.update()
        print("[Docs Menu] Closed")
    
    def open_admin_guide(e):
        """Open the admin diagnostic guide"""
        try:
            # Close the menu first
            close_docs_menu(e)
            # Launch admin guide
            from ui.admin_guide import launch_admin_guide
            launch_admin_guide(chat_view)
        except Exception as ex:
            print(f"[Docs Menu] Error opening admin guide: {ex}")
            chat_view.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Error opening admin guide: {ex}"),
                    bgcolor=ft.colors.RED
                )
            )
    
    def open_editor(e):
        """Open the Tron-style text editor"""
        try:
            # Close the menu first
            close_docs_menu(e)
            # Launch editor
            from ui.editor import launch_editor
            launch_editor(chat_view)
        except Exception as ex:
            print(f"[Docs Menu] Error opening editor: {ex}")
            chat_view.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Error opening editor: {ex}"),
                    bgcolor=ft.colors.RED
                )
            )
    
    def open_rag_docs(e):
        """Open the RAG documents viewer"""
        try:
            # Close the menu first
            close_docs_menu(e)
            # Launch docs viewer
            from ui.docs import launch_docs_viewer
            launch_docs_viewer(chat_view)
        except Exception as ex:
            print(f"[Docs Menu] Error opening RAG docs: {ex}")
            chat_view.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Error opening RAG docs: {ex}"),
                    bgcolor=ft.colors.RED
                )
            )
    
    # Create docs menu container with Tron theme
    docs_menu_container = ft.Container(
        content=ft.Column(
            controls=[
                # Docs menu header with Tron theme
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("📋 DOCS MENU", 
                                           size=16, weight=ft.FontWeight.BOLD, color=ft.colors.CYAN_400,
                                           font_family="monospace"),
                                    ft.Container(expand=True),  # Spacer
                                    ft.IconButton(
                                        icon=ft.icons.CLOSE,
                                        icon_color=ft.colors.RED_400,
                                        tooltip="Close Menu",
                                        on_click=close_docs_menu
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Text("Choose your documentation tool", 
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
                
                # Menu options with Tron theme
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Select Documentation Tool:", 
                                   weight=ft.FontWeight.BOLD, size=12, color=ft.colors.CYAN_400,
                                   font_family="monospace"),
                            
                            # Admin Guide Option
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.icons.BUILD,
                                            size=40,
                                            color=ft.colors.ORANGE_400
                                        ),
                                        ft.Column(
                                            controls=[
                                                ft.Text(
                                                    "Admin Guide",
                                                    weight=ft.FontWeight.BOLD,
                                                    size=14,
                                                    color=ft.colors.CYAN_300,
                                                    font_family="monospace"
                                                ),
                                                ft.Text(
                                                    "System diagnostic commands and troubleshooting guide",
                                                    size=10,
                                                    color=ft.colors.CYAN_200,
                                                    font_family="monospace"
                                                )
                                            ],
                                            spacing=2
                                        ),
                                        ft.Container(expand=True),
                                        ft.ElevatedButton(
                                            "OPEN",
                                            on_click=open_admin_guide,
                                            style=ft.ButtonStyle(
                                                bgcolor=ft.colors.BLACK,
                                                color=ft.colors.ORANGE_400,
                                                side=ft.BorderSide(1, ft.colors.ORANGE_400)
                                            )
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.START
                                ),
                                bgcolor=ft.colors.BLACK,
                                border=ft.border.all(1, ft.colors.ORANGE_400),
                                border_radius=5,
                                padding=15,
                                margin=ft.margin.symmetric(vertical=5)
                            ),
                            
                            # Editor Option
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.icons.EDIT,
                                            size=40,
                                            color=ft.colors.GREEN_400
                                        ),
                                        ft.Column(
                                            controls=[
                                                ft.Text(
                                                    "Tron Editor",
                                                    weight=ft.FontWeight.BOLD,
                                                    size=14,
                                                    color=ft.colors.CYAN_300,
                                                    font_family="monospace"
                                                ),
                                                ft.Text(
                                                    "Modern Tron-style text editor for notes and documents",
                                                    size=10,
                                                    color=ft.colors.CYAN_200,
                                                    font_family="monospace"
                                                )
                                            ],
                                            spacing=2
                                        ),
                                        ft.Container(expand=True),
                                        ft.ElevatedButton(
                                            "OPEN",
                                            on_click=open_editor,
                                            style=ft.ButtonStyle(
                                                bgcolor=ft.colors.BLACK,
                                                color=ft.colors.GREEN_400,
                                                side=ft.BorderSide(1, ft.colors.GREEN_400)
                                            )
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.START
                                ),
                                bgcolor=ft.colors.BLACK,
                                border=ft.border.all(1, ft.colors.GREEN_400),
                                border_radius=5,
                                padding=15,
                                margin=ft.margin.symmetric(vertical=5)
                            ),
                            
                            # RAG Documents Option
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.icons.DESCRIPTION,
                                            size=40,
                                            color=ft.colors.PURPLE_400
                                        ),
                                        ft.Column(
                                            controls=[
                                                ft.Text(
                                                    "RAG Documents",
                                                    weight=ft.FontWeight.BOLD,
                                                    size=14,
                                                    color=ft.colors.CYAN_300,
                                                    font_family="monospace"
                                                ),
                                                ft.Text(
                                                    "View and read documents stored in the RAG system",
                                                    size=10,
                                                    color=ft.colors.CYAN_200,
                                                    font_family="monospace"
                                                )
                                            ],
                                            spacing=2
                                        ),
                                        ft.Container(expand=True),
                                        ft.ElevatedButton(
                                            "OPEN",
                                            on_click=open_rag_docs,
                                            style=ft.ButtonStyle(
                                                bgcolor=ft.colors.BLACK,
                                                color=ft.colors.PURPLE_400,
                                                side=ft.BorderSide(1, ft.colors.PURPLE_400)
                                            )
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.START
                                ),
                                bgcolor=ft.colors.BLACK,
                                border=ft.border.all(1, ft.colors.PURPLE_400),
                                border_radius=5,
                                padding=15,
                                margin=ft.margin.symmetric(vertical=5)
                            )
                        ],
                        spacing=10
                    ),
                    padding=15,
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
        height=400,  # Fixed height to fit within chat window
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
    
    # Mark this container as the docs menu for easy removal
    docs_menu_container.docs_menu_container = True
    
    # Add docs menu to chat list as a static, contained element
    chat_view.chat_list.controls.append(docs_menu_container)
    
    # Update the page to render the docs menu
    chat_view.page.update()
    
    # Scroll to the docs menu smoothly
    chat_view.chat_list.scroll_to(
        offset=-1,
        duration=500,
        curve=ft.AnimationCurve.EASE_OUT
    )
    
    return docs_menu_container
