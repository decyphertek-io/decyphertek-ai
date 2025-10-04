import flet as ft
import json
import os
import asyncio
import platform
import subprocess
from pathlib import Path

class TtsSettingsScreen(ft.Column):
    def __init__(self):
        super().__init__()
        
        # Default values
        self.speech_rate = 0.5
        self.spanish_language_code = 'es-US'
        self.english_language_code = 'en-US'
        
        # Available language options
        self.spanish_options = []
        self.english_options = []
        
        self.is_loading = True
        
        # UI components
        self.progress_ring = ft.ProgressRing()
        
        # Speech rate slider
        self.speech_rate_slider = ft.Slider(
            min=0.1,
            max=1.0,
            divisions=9,
            label="{value}",
            on_change=self.on_speech_rate_change
        )
        
        self.speech_rate_text = ft.Text("50%")
        
        # Spanish language dropdown
        self.spanish_dropdown = ft.Dropdown(
            width=400,
            options=[],
            on_change=self.on_spanish_language_change
        )
        
        # English language dropdown
        self.english_dropdown = ft.Dropdown(
            width=400,
            options=[],
            on_change=self.on_english_language_change
        )
        
        # Main content
        self.content = ft.Column(
            [
                # Speech rate slider
                ft.Text("Speech Rate", style=ft.TextThemeStyle.TITLE_MEDIUM),
                self.speech_rate_slider,
                ft.Row(
                    [
                        ft.Text("Slow"),
                        self.speech_rate_text,
                        ft.Text("Fast"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=24),
                
                # Spanish language selection
                ft.Text("Spanish Voice", style=ft.TextThemeStyle.TITLE_MEDIUM),
                ft.Container(height=8),
                self.spanish_dropdown,
                ft.Container(height=8),
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.VOLUME_UP),
                        ft.Text("Test Spanish Voice")
                    ]),
                    on_click=self.test_spanish_tts
                ),
                ft.Container(height=24),
                
                # English language selection
                ft.Text("English Voice", style=ft.TextThemeStyle.TITLE_MEDIUM),
                ft.Container(height=8),
                self.english_dropdown,
                ft.Container(height=8),
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.VOLUME_UP),
                        ft.Text("Test English Voice")
                    ]),
                    on_click=self.test_english_tts
                ),
                ft.Container(height=32),
                
                # Save button
                ft.ElevatedButton(
                    text="Save Settings",
                    on_click=self.save_settings
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
    def did_mount(self):
        # Load settings when the screen is first created
        self.page.run_task(self.load_settings)
        
    async def load_settings(self):
        """Load saved TTS settings"""
        self.is_loading = True
        self.update()
        
        try:
            # Load saved settings from a JSON file
            prefs_file = os.path.join(Path.home(), "tts_preferences.json")
            
            if os.path.exists(prefs_file):
                try:
                    with open(prefs_file, "r") as f:
                        prefs = json.load(f)
                        self.speech_rate = prefs.get("tts_speech_rate", 0.5)
                        self.spanish_language_code = prefs.get("tts_spanish_code", "es-US")
                        self.english_language_code = prefs.get("tts_english_code", "en-US")
                except:
                    # Use defaults if there's an error
                    self.speech_rate = 0.5
                    self.spanish_language_code = "es-US"
                    self.english_language_code = "en-US"
            
            # Update UI with loaded values
            self.speech_rate_slider.value = self.speech_rate
            self.speech_rate_text.value = f"{int(self.speech_rate * 100)}%"
            
            # Load available languages
            await self.load_available_languages()
            
        except Exception as e:
            print(f"Error loading TTS settings: {str(e)}")
        finally:
            self.is_loading = False
            self.update()
    
    async def load_available_languages(self):
        """Load available TTS languages based on platform"""
        try:
            # In Python, we'll use a different approach to get TTS languages
            # This is a simplified version that provides common options
            
            spanish_options = [
                {"code": "es-US", "name": "Spanish (US)"},
                {"code": "es-ES", "name": "Spanish (Spain)"},
                {"code": "es-MX", "name": "Spanish (Mexico)"},
                {"code": "es", "name": "Spanish (Generic)"}
            ]
            
            english_options = [
                {"code": "en-US", "name": "English (US)"},
                {"code": "en-GB", "name": "English (UK)"},
                {"code": "en-AU", "name": "English (Australia)"},
                {"code": "en", "name": "English (Generic)"}
            ]
            
            # Check platform and adjust available options
            system = platform.system()
            
            if system == "Linux":
                # Check for espeak
                try:
                    result = subprocess.run(["espeak", "--voices"], capture_output=True, text=True)
                    if result.returncode == 0:
                        # Parse espeak voices
                        lines = result.stdout.splitlines()
                        for line in lines:
                            parts = line.split()
                            if len(parts) >= 4:
                                lang_code = parts[1]
                                if lang_code.startswith("es"):
                                    spanish_options.append({
                                        "code": lang_code,
                                        "name": f"Spanish ({parts[3]})"
                                    })
                                elif lang_code.startswith("en"):
                                    english_options.append({
                                        "code": lang_code,
                                        "name": f"English ({parts[3]})"
                                    })
                except:
                    pass
            
            # Update the dropdowns
            self.spanish_options = spanish_options
            self.english_options = english_options
            
            # Create dropdown options
            spanish_dropdown_options = [
                ft.dropdown.Option(key=option["code"], text=option["name"])
                for option in spanish_options
            ]
            
            english_dropdown_options = [
                ft.dropdown.Option(key=option["code"], text=option["name"])
                for option in english_options
            ]
            
            self.spanish_dropdown.options = spanish_dropdown_options
            self.english_dropdown.options = english_dropdown_options
            
            # Set current values
            self.spanish_dropdown.value = self.spanish_language_code
            self.english_dropdown.value = self.english_language_code
            
        except Exception as e:
            print(f"Error loading TTS languages: {str(e)}")
    
    def on_speech_rate_change(self, e):
        """Handle speech rate slider change"""
        self.speech_rate = e.control.value
        self.speech_rate_text.value = f"{int(self.speech_rate * 100)}%"
        self.update()
    
    def on_spanish_language_change(self, e):
        """Handle Spanish language dropdown change"""
        self.spanish_language_code = e.control.value
    
    def on_english_language_change(self, e):
        """Handle English language dropdown change"""
        self.english_language_code = e.control.value
    
    async def save_settings(self, e):
        """Save TTS settings"""
        try:
            prefs_file = os.path.join(Path.home(), "tts_preferences.json")
            
            # Load existing preferences or create new
            if os.path.exists(prefs_file):
                with open(prefs_file, "r") as f:
                    prefs = json.load(f)
            else:
                prefs = {}
            
            # Update with new settings
            prefs["tts_speech_rate"] = self.speech_rate
            prefs["tts_spanish_code"] = self.spanish_language_code
            prefs["tts_english_code"] = self.english_language_code
            
            # Save to file
            with open(prefs_file, "w") as f:
                json.dump(prefs, f)
            
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Settings saved"))
                )
                
            # Return to previous screen
            self.page.pop_route({
                "speechRate": self.speech_rate,
                "spanishCode": self.spanish_language_code,
                "englishCode": self.english_language_code
            })
            
        except Exception as e:
            print(f"Error saving TTS settings: {str(e)}")
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Failed to save settings"))
                )
    
    async def test_spanish_tts(self, e):
        """Test Spanish TTS voice"""
        try:
            await self.speak("Hola, esto es una prueba de voz en español.", self.spanish_language_code)
        except Exception as ex:
            print(f"Failed to play Spanish TTS: {str(ex)}")
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Failed to play Spanish TTS"))
                )
    
    async def test_english_tts(self, e):
        """Test English TTS voice"""
        try:
            await self.speak("Hello, this is an English voice test.", self.english_language_code)
        except Exception as ex:
            print(f"Failed to play English TTS: {str(ex)}")
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Failed to play English TTS"))
                )
    
    async def speak(self, text, language_code):
        """Speak text using the appropriate TTS engine"""
        system = platform.system()
        
        try:
            if system == "Windows":
                # Use PowerShell for Windows
                ps_script = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Rate = {int((self.speech_rate - 0.5) * 10)}; $speak.Speak("{text}")'
                subprocess.Popen(["powershell", "-Command", ps_script])
            elif system == "Darwin":  # macOS
                # Use say command for macOS
                language = language_code.split('-')[0]
                voice = "Juan" if language == "es" else "Alex"  # Default Spanish and English voices
                subprocess.Popen(["say", "-v", voice, "-r", str(int(self.speech_rate * 200)), text])
            elif system == "Linux":
                # Use espeak for Linux
                language = language_code.split('-')[0]
                speed = int(self.speech_rate * 200)
                subprocess.Popen(["espeak", "-v", language, "-s", str(speed), text])
            else:
                # Try pyttsx3 as fallback
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty('rate', int(self.speech_rate * 200))
                    engine.say(text)
                    engine.runAndWait()
                except:
                    raise Exception("No TTS engine available")
        except Exception as e:
            print(f"TTS error: {str(e)}")
            raise
    
    def build(self):
        if self.is_loading:
            return ft.Center(content=self.progress_ring)
        else:
            return ft.Container(
                content=self.content,
                padding=16
            )

def create_tts_settings_screen(page):
    tts_screen = TtsSettingsScreen()
    
    # Return a View with appbar and content
    return ft.View(
        route="/tts-settings",
        appbar=ft.AppBar(
            title=ft.Text("TTS Settings"),
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda e: page.pop_route()
            )
        ),
        controls=[tts_screen]
    )
