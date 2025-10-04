"""
RAG (Retrieval Augmented Generation) view
"""

import flet as ft
from typing import Callable
from pathlib import Path
import platform
import os


class RAGView:
    """RAG document management interface"""
    
    def __init__(self, page: ft.Page, document_manager, on_install_mcp: Callable):
        """
        Initialize RAG view
        
        Args:
            page: Flet page
            document_manager: DocumentManager instance
            on_install_mcp: Callback for MCP server installation
        """
        self.page = page
        self.doc_manager = document_manager
        self.on_install_mcp = on_install_mcp
        
        # Detect platform
        self.is_mobile = self._detect_mobile()
        self.platform_name = platform.system()
        print(f"[RAG] Platform: {self.platform_name} | Mobile: {self.is_mobile}")
        
        # UI elements
        self.file_picker = None
        self.docs_list = None
        self.stats_text = None
    
    def _detect_mobile(self) -> bool:
        """Detect if running on mobile platform"""
        try:
            # Check if running in Chaquopy (Android)
            import sys
            if 'com.chaquo.python' in sys.modules:
                return True
            
            # Check environment variables
            if os.getenv('ANDROID_ROOT') or os.getenv('ANDROID_DATA'):
                return True
            
            # Check platform
            system = platform.system().lower()
            if system == 'android':
                return True
            
            return False
        except:
            return False
    
    def build(self) -> ft.Column:
        """Build RAG interface"""
        
        # File picker for document upload - Create fresh each time
        print("[RAG] Creating file picker...")
        
        # Remove old file picker if exists
        if self.file_picker is not None:
            try:
                if self.file_picker in self.page.overlay:
                    self.page.overlay.remove(self.file_picker)
                print("[RAG] Removed old file picker")
            except:
                pass
        
        # Create new file picker
        self.file_picker = ft.FilePicker(on_result=self._on_file_picked)
        self.page.overlay.append(self.file_picker)
        self.page.update()
        
        print(f"[RAG] ✓ File picker created and registered (overlay count: {len(self.page.overlay)})")
        print(f"[RAG] File picker callback: {self.file_picker.on_result}")
        print(f"[RAG] File picker in overlay: {self.file_picker in self.page.overlay}")
        
        # Documents list
        self.docs_list = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=10
        )
        
        # Stats text
        stats = self.doc_manager.get_stats()
        self.stats_text = ft.Text(
            f"{stats['documents']} documents • {stats['chunks']} chunks • {stats['size_mb']} MB",
            size=13,
            color=ft.colors.GREY_600
        )
        
        # Refresh document list
        self._refresh_docs_list()
        
        return ft.Column(
            controls=[
                # App bar
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.icons.STORAGE, size=28),
                            ft.Text(
                                "RAG Documents",
                                size=22,
                                weight=ft.FontWeight.BOLD
                            ),
                        ]
                    ),
                    padding=15,
                    bgcolor=ft.colors.SURFACE_VARIANT
                ),
                
                # Content
                ft.Container(
                    content=ft.Column([
                        ft.Container(height=20),
                        
                        # Stats
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.INFO_OUTLINE, size=20, color=ft.colors.BLUE),
                                    ft.Text("ChromaDB Status", size=16, weight=ft.FontWeight.BOLD),
                                ]),
                                ft.Container(height=5),
                                self.stats_text,
                            ]),
                            bgcolor=ft.colors.BLUE_50,
                            border_radius=10,
                            padding=15
                        ),
                        
                        ft.Container(height=20),
                        
                        # Add Document section
                        ft.Text("Add Documents", size=14, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        
                        # Mobile-friendly options
                        ft.Row([
                            ft.ElevatedButton(
                                "📝 Paste Text",
                                icon=ft.icons.TEXT_FIELDS,
                                on_click=lambda e: self._show_text_input_dialog(),
                                expand=True,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.BLUE,
                                    color=ft.colors.WHITE
                                )
                            ),
                            ft.ElevatedButton(
                                "🔗 From URL",
                                icon=ft.icons.LINK,
                                on_click=lambda e: self._show_url_input_dialog(),
                                expand=True,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.GREEN,
                                    color=ft.colors.WHITE
                                )
                            ),
                        ], spacing=10),
                        
                        ft.Container(height=10),
                        
                        # File picker button
                        ft.ElevatedButton(
                            "📄 Upload Docs",
                            icon=ft.icons.UPLOAD_FILE,
                            on_click=self._on_upload_click,
                            expand=True,
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.PURPLE,
                                color=ft.colors.WHITE
                            )
                        ),
                        
                        ft.Container(height=20),
                        ft.Divider(),
                        ft.Container(height=10),
                        
                        # MCP Integration section
                        ft.Text("MCP Server Integration", size=14, weight=ft.FontWeight.BOLD),
                        ft.Container(height=5),
                        ft.Text(
                            "Connect cloud storage MCP servers to import documents",
                            size=12,
                            color=ft.colors.GREY_600
                        ),
                        ft.Container(height=15),
                        
                        ft.Row([
                            ft.ElevatedButton(
                                "☁️ Nextcloud",
                                icon=ft.icons.CLOUD,
                                on_click=lambda e: self.on_install_mcp("nextcloud"),
                                expand=True
                            ),
                            ft.ElevatedButton(
                                "📁 Google Drive",
                                icon=ft.icons.FOLDER,
                                on_click=lambda e: self.on_install_mcp("google-drive"),
                                expand=True
                            ),
                        ], spacing=10),
                        
                        ft.Container(height=20),
                        ft.Divider(),
                        ft.Container(height=10),
                        
                        # Documents list
                        ft.Row([
                            ft.Text("Your Documents", size=14, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.icons.REFRESH,
                                tooltip="Refresh",
                                on_click=lambda e: self._refresh_docs_list()
                            ),
                        ]),
                        ft.Container(height=10),
                        
                        self.docs_list,
                        
                    ], scroll=ft.ScrollMode.AUTO, expand=True),
                    padding=20,
                    expand=True
                ),
            ],
            expand=True,
            spacing=0
        )
    
    def _on_upload_click(self, e):
        """Handle upload button click with platform-specific paths"""
        print("\n" + "="*70)
        print("[RAG] ⬆️  UPLOAD BUTTON CLICKED!")
        print("="*70)
        
        # Check file picker exists
        if self.file_picker is None:
            error_msg = "File picker not initialized!"
            print(f"[RAG] ❌ ERROR: {error_msg}")
            self._show_snackbar(f"Error: {error_msg}", ft.colors.RED)
            return
        
        print(f"[RAG] ✓ File picker exists: {self.file_picker}")
        print(f"[RAG] ✓ File picker callback: {self.file_picker.on_result}")
        print(f"[RAG] ✓ File picker in overlay: {self.file_picker in self.page.overlay}")
        
        try:
            # Get initial directory based on platform
            initial_dir = self._get_initial_directory()
            print(f"[RAG] Platform: {self.platform_name}")
            print(f"[RAG] Is Mobile: {self.is_mobile}")
            print(f"[RAG] Initial directory: {initial_dir}")
            print(f"[RAG] Calling file_picker.pick_files()...")
            
            # Show notification that picker is opening
            self._show_snackbar("📂 Opening file picker...", ft.colors.BLUE)
            
            # Platform-specific file picker configuration
            if self.is_mobile:
                # Android - use storage paths
                print("[RAG] Using MOBILE configuration (no initial_directory)")
                self.file_picker.pick_files(
                    allowed_extensions=["txt", "md", "json", "csv", "py", "js", "html", "css", "xml", "yaml", "yml"],
                    allow_multiple=True,
                    dialog_title="Select Documents to Upload"
                )
            else:
                # Linux/Desktop - set initial directory
                print(f"[RAG] Using DESKTOP configuration (initial_directory={initial_dir})")
                self.file_picker.pick_files(
                    allowed_extensions=["txt", "md", "json", "csv", "py", "js", "html", "css", "xml", "yaml", "yml"],
                    allow_multiple=True,
                    dialog_title="Select Documents to Upload",
                    initial_directory=initial_dir
                )
            
            print("[RAG] ✓ pick_files() called successfully")
            print("[RAG] ⏳ Waiting for user to select files...")
            print("="*70 + "\n")
            
        except Exception as ex:
            print(f"[RAG] ❌ ERROR opening file picker: {ex}")
            import traceback
            traceback.print_exc()
            self._show_snackbar(f"Error: {str(ex)}", ft.colors.RED)
    
    def _get_initial_directory(self) -> str:
        """Get initial directory for file picker based on platform"""
        try:
            if self.is_mobile:
                # Android paths
                if os.path.exists("/storage/emulated/0/Documents"):
                    return "/storage/emulated/0/Documents"
                elif os.path.exists("/storage/emulated/0/Download"):
                    return "/storage/emulated/0/Download"
                else:
                    return "/storage/emulated/0"
            else:
                # Linux/Desktop paths
                home = os.path.expanduser("~")
                
                # Try common document locations
                documents = os.path.join(home, "Documents")
                downloads = os.path.join(home, "Downloads")
                desktop = os.path.join(home, "Desktop")
                
                if os.path.exists(documents):
                    print(f"[RAG] Using Documents folder: {documents}")
                    return documents
                elif os.path.exists(downloads):
                    print(f"[RAG] Using Downloads folder: {downloads}")
                    return downloads
                elif os.path.exists(desktop):
                    print(f"[RAG] Using Desktop folder: {desktop}")
                    return desktop
                else:
                    print(f"[RAG] Using home directory: {home}")
                    return home
        except Exception as ex:
            print(f"[RAG] Error getting initial directory: {ex}")
            return os.path.expanduser("~")
    
    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file selection"""
        print(f"\n{'='*60}")
        print(f"[RAG] FILE PICKER CALLBACK TRIGGERED!")
        print(f"{'='*60}")
        print(f"[RAG] Event type: {type(e)}")
        print(f"[RAG] Event object: {e}")
        print(f"[RAG] Has files attr: {hasattr(e, 'files')}")
        
        if hasattr(e, 'files'):
            print(f"[RAG] Files value: {e.files}")
            print(f"[RAG] Files type: {type(e.files)}")
        
        if not e.files:
            print("[RAG] WARNING: No files in event (user canceled or error)")
            self._show_snackbar("⚠️ No files selected", ft.colors.ORANGE)
            return
        
        print(f"[RAG] SUCCESS: Selected {len(e.files)} file(s):")
        for idx, f in enumerate(e.files, 1):
            print(f"  [{idx}] Name: {f.name}")
            print(f"      Path: {f.path}")
            print(f"      Size: {getattr(f, 'size', 'unknown')}")
        
        self._show_snackbar(f"📤 Uploading {len(e.files)} file(s)...", ft.colors.BLUE)
        
        import threading
        
        def upload_in_thread():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._upload_files(e.files))
            finally:
                loop.close()
        
        print("[RAG] Starting upload thread...")
        thread = threading.Thread(target=upload_in_thread, daemon=True)
        thread.start()
        print("[RAG] Upload thread started")
    
    async def _upload_files(self, files):
        """Upload files asynchronously"""
        print(f"[RAG] ===== Starting upload of {len(files)} files =====")
        
        for idx, file in enumerate(files, 1):
            try:
                # Read file content
                file_path = Path(file.path)
                
                print(f"[RAG] [{idx}/{len(files)}] Processing file: {file.name}")
                print(f"[RAG] Path: {file.path}")
                print(f"[RAG] Size: {file.size if hasattr(file, 'size') else 'unknown'}")
                
                self._show_snackbar(f"⏳ [{idx}/{len(files)}] Processing {file.name}...", ft.colors.BLUE)
                
                # Read file based on extension
                supported_text_extensions = ['.txt', '.md', '.json', '.csv', '.py', '.js', '.html', '.css', '.xml', '.yaml', '.yml']
                
                if file_path.suffix.lower() in supported_text_extensions:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # For JSON, pretty print
                    if file_path.suffix == '.json':
                        try:
                            import json
                            data = json.loads(content)
                            content = json.dumps(data, indent=2)
                        except:
                            pass  # Use raw content if JSON parsing fails
                else:
                    self._show_snackbar(f"Unsupported file type: {file_path.suffix}", ft.colors.ORANGE)
                    continue
                
                print(f"[RAG] File content length: {len(content)} chars")
                
                # Add to document manager (generates embeddings via API)
                success = await self.doc_manager.add_document(
                    content=content,
                    filename=file.name,
                    source="upload"
                )
                
                if success:
                    self._show_snackbar(f"✓ Added: {file.name}", ft.colors.GREEN)
                    self._refresh_docs_list()
                else:
                    self._show_snackbar(f"Document already exists: {file.name}", ft.colors.ORANGE)
                    
            except Exception as ex:
                self._show_snackbar(f"Error: {str(ex)}", ft.colors.RED)
    
    def _refresh_docs_list(self):
        """Refresh documents list"""
        print(f"[RAG View] Refreshing documents list...")
        self.docs_list.controls.clear()
        
        documents = self.doc_manager.get_documents()
        print(f"[RAG View] Retrieved {len(documents)} documents from DocumentManager")
        
        if not documents:
            self.docs_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.FOLDER_OPEN, size=60, color=ft.colors.GREY_400),
                        ft.Container(height=10),
                        ft.Text(
                            "No documents yet",
                            size=16,
                            color=ft.colors.GREY_600
                        ),
                        ft.Text(
                            "Upload documents or connect MCP servers",
                            size=12,
                            color=ft.colors.GREY_500
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=40,
                    alignment=ft.alignment.center
                )
            )
        else:
            for doc_id, doc_info in documents.items():
                # Source icon
                if doc_info['source'] == 'upload':
                    source_icon = ft.icons.UPLOAD_FILE
                elif doc_info['source'] == 'text-input':
                    source_icon = ft.icons.TEXT_FIELDS
                elif doc_info['source'] == 'url':
                    source_icon = ft.icons.LINK
                elif doc_info['source'] == 'nextcloud':
                    source_icon = ft.icons.CLOUD
                elif doc_info['source'] == 'google-drive':
                    source_icon = ft.icons.FOLDER
                else:
                    source_icon = ft.icons.DESCRIPTION
                
                self.docs_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(source_icon, size=20, color=ft.colors.BLUE),
                            ft.Column([
                                ft.Text(doc_info['filename'], size=14, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    f"{doc_info['chunks']} chunks • {round(doc_info['size'] / 1024, 1)} KB",
                                    size=11,
                                    color=ft.colors.GREY_600
                                ),
                            ], spacing=2, expand=True),
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE,
                                icon_color=ft.colors.RED,
                                tooltip="Delete",
                                on_click=lambda e, d=doc_id: self._delete_document(d)
                            ),
                        ]),
                        bgcolor=ft.colors.SURFACE_VARIANT,
                        border_radius=8,
                        padding=10
                    )
                )
        
        # Update stats
        stats = self.doc_manager.get_stats()
        self.stats_text.value = f"{stats['documents']} documents • {stats['chunks']} chunks • {stats['size_mb']} MB"
        
        self.page.update()
    
    def _delete_document(self, doc_id: str):
        """Delete a document"""
        success = self.doc_manager.delete_document(doc_id)
        if success:
            self._show_snackbar("✓ Document deleted", ft.colors.GREEN)
            self._refresh_docs_list()
        else:
            self._show_snackbar("Failed to delete document", ft.colors.RED)
    
    def _show_text_input_dialog(self):
        """Show dialog for pasting/typing text"""
        text_field = ft.TextField(
            label="Document Title",
            hint_text="My Document",
        )
        
        content_field = ft.TextField(
            label="Content",
            hint_text="Paste or type your text here...",
            multiline=True,
            min_lines=10,
            max_lines=20,
        )
        
        def save_text(e):
            if not text_field.value or not content_field.value:
                self._show_snackbar("⚠️ Please provide both title and content", ft.colors.ORANGE)
                return
            
            self.page.close(dialog)
            
            # Process in background
            import threading
            
            def process_text():
                import asyncio
                asyncio.run(self._add_text_document(text_field.value, content_field.value))
            
            threading.Thread(target=process_text, daemon=True).start()
        
        dialog = ft.AlertDialog(
            title=ft.Text("📝 Add Text Document"),
            content=ft.Column([
                text_field,
                ft.Container(height=10),
                content_field,
            ], tight=True, height=400),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Save",
                    icon=ft.icons.SAVE,
                    on_click=save_text,
                    style=ft.ButtonStyle(bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_url_input_dialog(self):
        """Show dialog for importing from URL"""
        url_field = ft.TextField(
            label="URL",
            hint_text="https://example.com/document.txt",
        )
        
        def fetch_url(e):
            if not url_field.value:
                self._show_snackbar("⚠️ Please enter a URL", ft.colors.ORANGE)
                return
            
            self.page.close(dialog)
            
            # Fetch in background
            import threading
            
            def fetch_and_process():
                import asyncio
                asyncio.run(self._fetch_url_document(url_field.value))
            
            threading.Thread(target=fetch_and_process, daemon=True).start()
        
        dialog = ft.AlertDialog(
            title=ft.Text("🔗 Import from URL"),
            content=ft.Column([
                ft.Text("Fetch a document from a URL", size=12, color=ft.colors.GREY_600),
                ft.Container(height=10),
                url_field,
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton(
                    "Fetch",
                    icon=ft.icons.DOWNLOAD,
                    on_click=fetch_url,
                    style=ft.ButtonStyle(bgcolor=ft.colors.GREEN, color=ft.colors.WHITE)
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    async def _add_text_document(self, title: str, content: str):
        """Add text document"""
        try:
            self._show_snackbar(f"⏳ Processing {title}...", ft.colors.BLUE)
            
            filename = title if title.endswith('.txt') else f"{title}.txt"
            
            success = await self.doc_manager.add_document(
                content=content,
                filename=filename,
                source="text-input"
            )
            
            if success:
                self._show_snackbar(f"✓ Added: {filename}", ft.colors.GREEN)
                self._refresh_docs_list()
            else:
                self._show_snackbar(f"Document already exists", ft.colors.ORANGE)
                
        except Exception as ex:
            self._show_snackbar(f"Error: {str(ex)}", ft.colors.RED)
    
    async def _fetch_url_document(self, url: str):
        """Fetch document from URL"""
        try:
            self._show_snackbar(f"⏳ Fetching from URL...", ft.colors.BLUE)
            
            import httpx
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Extract filename from URL
                    from urllib.parse import urlparse
                    filename = urlparse(url).path.split('/')[-1] or "url-document.txt"
                    
                    success = await self.doc_manager.add_document(
                        content=content,
                        filename=filename,
                        source="url"
                    )
                    
                    if success:
                        self._show_snackbar(f"✓ Added: {filename}", ft.colors.GREEN)
                        self._refresh_docs_list()
                    else:
                        self._show_snackbar(f"Document already exists", ft.colors.ORANGE)
                else:
                    self._show_snackbar(f"Failed to fetch: HTTP {response.status_code}", ft.colors.RED)
                    
        except Exception as ex:
            self._show_snackbar(f"Error: {str(ex)}", ft.colors.RED)
    
    def _show_snackbar(self, message: str, color):
        """Show snackbar notification"""
        snackbar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

