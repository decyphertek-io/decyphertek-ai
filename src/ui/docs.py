import flet as ft
from pathlib import Path
import os

def launch_docs_viewer(chat_view):
    """Launches the RAG documents viewer within the chat window."""
    
    # Get the document manager from the main class
    doc_manager = None
    if hasattr(chat_view, 'main_class') and hasattr(chat_view.main_class, 'document_manager'):
        doc_manager = chat_view.main_class.document_manager
    
    def close_docs_viewer(e):
        """Close the docs viewer and return to chat"""
        # Remove docs viewer from chat list
        chat_view.chat_list.controls = [control for control in chat_view.chat_list.controls 
                                      if not hasattr(control, 'docs_viewer_container')]
        chat_view.page.update()
        print("[Docs Viewer] Closed")
    
    def refresh_docs(e):
        """Refresh the documents list"""
        try:
            if doc_manager:
                # Get all documents from the document manager
                docs = doc_manager.get_all_documents()
                docs_list.controls.clear()
                
                if docs:
                    for doc in docs:
                        doc_item = ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.icons.DESCRIPTION, color=ft.colors.CYAN_400),
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                doc.get('title', 'Untitled Document'),
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.colors.CYAN_300,
                                                font_family="monospace"
                                            ),
                                            ft.Text(
                                                f"ID: {doc.get('id', 'Unknown')}",
                                                size=10,
                                                color=ft.colors.CYAN_200,
                                                font_family="monospace"
                                            ),
                                            ft.Text(
                                                f"Size: {len(doc.get('content', ''))} chars",
                                                size=10,
                                                color=ft.colors.CYAN_200,
                                                font_family="monospace"
                                            )
                                        ],
                                        spacing=2
                                    ),
                                    ft.Container(expand=True),
                                    ft.IconButton(
                                        icon=ft.icons.VISIBILITY,
                                        icon_color=ft.colors.GREEN_400,
                                        tooltip="View Document",
                                        on_click=lambda e, doc_id=doc.get('id'): view_document(doc_id)
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.START
                            ),
                            bgcolor=ft.colors.BLACK,
                            border=ft.border.all(1, ft.colors.CYAN_400),
                            border_radius=5,
                            padding=10,
                            margin=ft.margin.symmetric(vertical=2)
                        )
                        docs_list.controls.append(doc_item)
                else:
                    docs_list.controls.append(
                        ft.Container(
                            content=ft.Text(
                                "No documents found. Upload documents through the RAG tab.",
                                color=ft.colors.ORANGE_400,
                                font_family="monospace"
                            ),
                            padding=20,
                            alignment=ft.alignment.center
                        )
                    )
                
                docs_list.update()
                chat_view.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Documents refreshed!"),
                        bgcolor=ft.colors.GREEN
                    )
                )
            else:
                chat_view.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Document manager not available"),
                        bgcolor=ft.colors.RED
                    )
                )
        except Exception as ex:
            print(f"[Docs Viewer] Error refreshing docs: {ex}")
            chat_view.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Error refreshing documents: {ex}"),
                    bgcolor=ft.colors.RED
                )
            )
    
    def view_document(doc_id):
        """View a specific document"""
        try:
            if doc_manager:
                # Get document content
                doc = doc_manager.get_document(doc_id)
                if doc:
                    # Create document viewer dialog
                    doc_content = ft.TextField(
                        value=doc.get('content', 'No content available'),
                        read_only=True,
                        multiline=True,
                        min_lines=20,
                        max_lines=20,
                        border_color=ft.colors.CYAN_400,
                        bgcolor=ft.colors.BLACK,
                        color=ft.colors.CYAN_300,
                        text_style=ft.TextStyle(
                            font_family="monospace",
                            size=11,
                            color=ft.colors.CYAN_300
                        )
                    )
                    
                    doc_dialog = ft.AlertDialog(
                        title=ft.Text(f"📄 {doc.get('title', 'Document')}", 
                                     color=ft.colors.CYAN_400, font_family="monospace"),
                        bgcolor=ft.colors.BLACK,
                        content=ft.Container(
                            content=doc_content,
                            width=600,
                            height=400
                        ),
                        actions=[
                            ft.TextButton(
                                "Close",
                                on_click=lambda e: chat_view.page.close(doc_dialog),
                                style=ft.ButtonStyle(color=ft.colors.CYAN_400)
                            )
                        ]
                    )
                    
                    chat_view.page.add(doc_dialog)
                    doc_dialog.open = True
                    chat_view.page.update()
                else:
                    chat_view.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("Document not found"),
                            bgcolor=ft.colors.RED
                        )
                    )
        except Exception as ex:
            print(f"[Docs Viewer] Error viewing document: {ex}")
            chat_view.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Error viewing document: {ex}"),
                    bgcolor=ft.colors.RED
                )
            )
    
    # Create docs list
    docs_list = ft.Column(
        controls=[],
        scroll=ft.ScrollMode.AUTO,
        spacing=5
    )
    
    # Create docs viewer container with Tron theme
    docs_viewer_container = ft.Container(
        content=ft.Column(
            controls=[
                # Docs viewer header with Tron theme
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("📚 RAG DOCUMENTS VIEWER", 
                                           size=16, weight=ft.FontWeight.BOLD, color=ft.colors.CYAN_400,
                                           font_family="monospace"),
                                    ft.Container(expand=True),  # Spacer
                                    ft.IconButton(
                                        icon=ft.icons.REFRESH,
                                        icon_color=ft.colors.GREEN_400,
                                        tooltip="Refresh Documents",
                                        on_click=refresh_docs
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.CLOSE,
                                        icon_color=ft.colors.RED_400,
                                        tooltip="Close Docs Viewer",
                                        on_click=close_docs_viewer
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Text("View and read RAG documents stored in the system", 
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
                
                # Documents list section
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("📄 Available Documents", 
                                   weight=ft.FontWeight.BOLD, size=12, color=ft.colors.CYAN_400,
                                   font_family="monospace"),
                            docs_list,
                        ],
                        spacing=5
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
        height=500,  # Fixed height to fit within chat window
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
    
    # Mark this container as the docs viewer for easy removal
    docs_viewer_container.docs_viewer_container = True
    
    # Add docs viewer to chat list as a static, contained element
    chat_view.chat_list.controls.append(docs_viewer_container)
    
    # Update the page to render the docs viewer
    chat_view.page.update()
    
    # Scroll to the docs viewer smoothly
    chat_view.chat_list.scroll_to(
        offset=-1,
        duration=500,
        curve=ft.AnimationCurve.EASE_OUT
    )
    
    # Auto-refresh documents on launch
    refresh_docs(None)
    
    return docs_viewer_container
