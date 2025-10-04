import flet as ft
import asyncio
import aiohttp
import json
import os
import platform
import subprocess

class InteractiveTranslatorWidget(ft.Column):
    def __init__(self, text=""):
        super().__init__()
        self.initial_text = text
        
        # Language codes
        self.source_language_code = 'es-US'  # Default: Spanish (United States)
        self.target_language_code = 'en-US'  # Default: English (United States)
        
        # List of possible language codes to try
        self.spanish_codes = ['es-US', 'es-ES', 'es', 'spa', 'es-419']
        self.english_codes = ['en-US', 'en-GB', 'en', 'eng']
        
        # Text controllers and state
        self.text_to_translate = ft.TextField(
            hint_text="Enter Spanish text...",
            border=ft.InputBorder.OUTLINE,
            multiline=True,
            min_lines=3,
            max_lines=5,
            suffix=ft.IconButton(
                icon=ft.Icons.CLEAR,
                on_click=self.clear_text
            )
        )
        self.translated_text = ""
        self.is_loading = False
        
        # UI elements
        self.translation_container = ft.Container(
            content=ft.Text(
                "Translation will appear here...",
                color='#757575',
                italic=True
            ),
            padding=12,
            border=ft.border.all(color='#bdbdbd'),
            border_radius=4,
            bgcolor='#424242',
            min_height=80
        )
        
        # Progress indicator
        self.progress_ring = ft.ProgressRing(
            width=20, 
            height=20, 
            stroke_width=2,
            color='#ffffff'
        )
        
        # Translate button
        self.translate_button = ft.ElevatedButton(
            text="Translate",
            on_click=self.translate_text
        )
        
        # Copy button row
        self.copy_row = ft.Row(
            [
                ft.TextButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.COPY, size=18),
                        ft.Text("Copy")
                    ]),
                    on_click=self.copy_to_clipboard
                )
            ],
            alignment=ft.MainAxisAlignment.END,
            visible=False
        )
        
    def did_mount(self):
        # Initialize with passed text
        self.text_to_translate.value = self.initial_text
        
        # Initialize TTS
        asyncio.create_task(self.init_tts())
        
        # Translate immediately if text is present
        if self.initial_text:
            asyncio.create_task(self.translate_text(None))
            
        self.update()
        
    async def init_tts(self):
        """Initialize text-to-speech functionality"""
        # In Python, we'll use a different TTS approach
        # For now, let's check if we have a system TTS available
        
        self.tts_available = False
        
        # Check platform and available TTS options
        system = platform.system()
        
        if system == "Windows":
            # Windows typically has SAPI available
            self.tts_available = True
            self.tts_engine = "windows"
        elif system == "Darwin":  # macOS
            # macOS has say command
            self.tts_available = True
            self.tts_engine = "macos"
        elif system == "Linux":
            # Check for espeak
            try:
                result = subprocess.run(["which", "espeak"], capture_output=True, text=True)
                if result.returncode == 0:
                    self.tts_available = True
                    self.tts_engine = "espeak"
            except:
                pass
                
            # Check for pyttsx3 as fallback
            if not self.tts_available:
                try:
                    import pyttsx3
                    self.tts_available = True
                    self.tts_engine = "pyttsx3"
                except:
                    pass
        
        if not self.tts_available and self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("TTS not available. Install espeak or pyttsx3 for speech functionality.")
                )
            )
    
    async def speak(self, text, is_spanish):
        """Speak the provided text in the appropriate language"""
        if not text or not self.tts_available:
            return
            
        language = "es" if is_spanish else "en"
        
        try:
            if self.tts_engine == "espeak":
                # Use espeak for Linux
                subprocess.Popen(["espeak", "-v", language, text])
            elif self.tts_engine == "windows":
                # Use PowerShell for Windows
                ps_script = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{text}")'
                subprocess.Popen(["powershell", "-Command", ps_script])
            elif self.tts_engine == "macos":
                # Use say command for macOS
                voice = "Juan" if is_spanish else "Alex"  # Default Spanish and English voices
                subprocess.Popen(["say", "-v", voice, text])
            elif self.tts_engine == "pyttsx3":
                # Use pyttsx3 as fallback
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {str(e)}")
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"TTS error: {str(e)}")
                    )
                )
    
    async def speak_source_text(self, e):
        """Speak the source Spanish text"""
        if not self.text_to_translate.value:
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Please enter text to speak")
                    )
                )
            return
            
        await self.speak(self.text_to_translate.value, True)
    
    async def speak_translated_text(self, e):
        """Speak the translated English text"""
        if not self.translated_text or self.translated_text.startswith("Error:"):
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("No translation available to speak")
                    )
                )
            return
            
        await self.speak(self.translated_text, False)
    
    async def translate_text(self, e):
        """Translate the text from Spanish to English"""
        if not self.text_to_translate.value:
            self.translated_text = ""
            self.update_translation_display()
            return
        
        self.is_loading = True
        self.update_ui_for_loading()
        
        try:
            # Using LibreTranslate API (public instance)
            async with aiohttp.ClientSession() as session:
                # You can replace this URL with your preferred translation API
                url = "https://translate.argosopentech.com/translate"
                
                data = {
                    "q": self.text_to_translate.value,
                    "source": "es",
                    "target": "en"
                }
                
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.translated_text = result.get("translatedText", "Translation failed")
                    else:
                        self.translated_text = "Translation service unavailable. Please try again later."
                        if self.page:
                            self.page.show_snack_bar(
                                ft.SnackBar(
                                    content=ft.Text("Translation service unavailable. Please try again later.")
                                )
                            )
        except Exception as e:
            self.translated_text = f"Translation failed: {str(e)}"
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Translation service unavailable. Please try again later.")
                    )
                )
        finally:
            self.is_loading = False
            self.update_ui_for_loading()
            self.update_translation_display()
    
    def update_ui_for_loading(self):
        """Update UI elements to reflect loading state"""
        if self.is_loading:
            self.translate_button.content = self.progress_ring
        else:
            self.translate_button.content = ft.Text("Translate")
        self.translate_button.disabled = self.is_loading
        self.update()
    
    def update_translation_display(self):
        """Update the translation display container"""
        if self.translated_text:
            self.translation_container.content = ft.SelectableText(
                self.translated_text,
                size=16
            )
            self.copy_row.visible = not self.translated_text.startswith("Error:")
        else:
            self.translation_container.content = ft.Text(
                "Translation will appear here...",
                color='#757575',
                italic=True
            )
            self.copy_row.visible = False
        self.update()
    
    def clear_text(self, e):
        """Clear the input text and translation"""
        self.text_to_translate.value = ""
        self.translated_text = ""
        self.update_translation_display()
    
    def copy_to_clipboard(self, e):
        """Copy the translated text to clipboard"""
        if self.translated_text:
            self.page.set_clipboard(self.translated_text)
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Translation copied to clipboard!")
                )
            )
    
    def build(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Spanish:", size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),  # Spacer
                            ft.IconButton(
                                icon=ft.Icons.VOLUME_UP,
                                tooltip="Speak Spanish text",
                                on_click=self.speak_source_text
                            )
                        ]
                    ),
                    ft.Container(height=8),
                    self.text_to_translate,
                    ft.Container(height=16),
                    self.translate_button,
                    ft.Container(height=16),
                    ft.Row(
                        [
                            ft.Text("English:", size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),  # Spacer
                            ft.IconButton(
                                icon=ft.Icons.VOLUME_UP,
                                tooltip="Speak English translation",
                                on_click=self.speak_translated_text
                            )
                        ]
                    ),
                    ft.Container(height=8),
                    self.translation_container,
                    self.copy_row,
                    ft.Container(height=20)
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=ft.padding.all(16)
        )

def create_interactive_translator_widget(page, initial_text=""):
    """Create and return an interactive translator widget"""
    translator_widget = InteractiveTranslatorWidget(initial_text)
    return translator_widget
