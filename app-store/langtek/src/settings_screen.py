import flet as ft
import json
import os
from pathlib import Path

# Define icon constants for compatibility
ICON_RECORD_VOICE_OVER = "record_voice_over"
ICON_MENU_BOOK = "menu_book"
ICON_RSS_FEED = "rss_feed"
ICON_ARROW_BACK = "arrow_back"

class SettingsScreen(ft.Column):
    def __init__(self):
        super().__init__()
        
        # Default settings
        self.theme_mode = "system"  # system, light, dark
        self.auto_translate = True
        self.save_history = True
        
        # UI components
        self.theme_dropdown = ft.Dropdown(
            label="Theme",
            width=400,
            options=[
                ft.dropdown.Option(key="system", text="System Default"),
                ft.dropdown.Option(key="light", text="Light"),
                ft.dropdown.Option(key="dark", text="Dark"),
            ],
            value="system",
            on_change=self.on_theme_change
        )
        
        self.auto_translate_switch = ft.Switch(
            label="Auto-translate articles",
            value=True,
            on_change=self.on_auto_translate_change
        )
        
        self.save_history_switch = ft.Switch(
            label="Save reading history",
            value=True,
            on_change=self.on_save_history_change
        )
        
        # Main content
        self.content = ft.Column(
            [
                ft.Text("App Settings", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                ft.Container(height=24),
                
                # Theme selection
                ft.Text("Appearance", style=ft.TextThemeStyle.TITLE_MEDIUM),
                ft.Container(height=8),
                self.theme_dropdown,
                ft.Container(height=24),
                
                # Translation settings
                ft.Text("Translation", style=ft.TextThemeStyle.TITLE_MEDIUM),
                ft.Container(height=8),
                self.auto_translate_switch,
                ft.Container(height=24),
                
                # History settings
                ft.Text("History", style=ft.TextThemeStyle.TITLE_MEDIUM),
                ft.Container(height=8),
                self.save_history_switch,
                ft.Container(height=32),
                
                # TTS settings button
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(name=ICON_RECORD_VOICE_OVER),
                        ft.Text("Text-to-Speech Settings")
                    ]),
                    on_click=self.open_tts_settings
                ),
                ft.Container(height=16),
                
                # Dictionary management button
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(name=ICON_MENU_BOOK),
                        ft.Text("Dictionary Management")
                    ]),
                    on_click=self.open_dictionary_management
                ),
                ft.Container(height=16),
                
                # Feed management button  
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(name=ICON_RSS_FEED),
                        ft.Text("RSS Feed Management")
                    ]),
                    on_click=lambda e: print("Button clicked but handler not set")
                ),
                ft.Container(height=32),
                
                # Save button
                ft.ElevatedButton(
                    content=ft.Text("Save Settings"),
                    on_click=self.save_settings
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
    def did_mount(self):
        # Load settings when the screen is first created
        self.load_settings()
        
    def load_settings(self):
        """Load saved app settings"""
        try:
            # Load saved settings from a JSON file
            prefs_file = os.path.join(Path.home(), "app_preferences.json")
            
            if os.path.exists(prefs_file):
                try:
                    with open(prefs_file, "r") as f:
                        prefs = json.load(f)
                        self.theme_mode = prefs.get("theme_mode", "system")
                        self.auto_translate = prefs.get("auto_translate", True)
                        self.save_history = prefs.get("save_history", True)
                except:
                    # Use defaults if there's an error
                    self.theme_mode = "system"
                    self.auto_translate = True
                    self.save_history = True
            
            # Update UI with loaded values
            self.theme_dropdown.value = self.theme_mode
            self.auto_translate_switch.value = self.auto_translate
            self.save_history_switch.value = self.save_history
            
            self.update()
            
        except Exception as e:
            print(f"Error loading app settings: {str(e)}")
    
    def on_theme_change(self, e):
        """Handle theme dropdown change"""
        self.theme_mode = e.control.value
        
        # Apply theme change immediately
        if self.page:
            if self.theme_mode == "light":
                self.page.theme_mode = ft.ThemeMode.LIGHT
            elif self.theme_mode == "dark":
                self.page.theme_mode = ft.ThemeMode.DARK
            else:  # system
                self.page.theme_mode = ft.ThemeMode.SYSTEM
            
            self.page.update()
    
    def on_auto_translate_change(self, e):
        """Handle auto-translate switch change"""
        self.auto_translate = e.control.value
    
    def on_save_history_change(self, e):
        """Handle save history switch change"""
        self.save_history = e.control.value
    
    def open_tts_settings(self, e):
        """Open TTS settings screen"""
        if self.page:
            self.page.push_route("/tts_settings")
    
    def open_dictionary_management(self, e):
        """Open dictionary management screen"""
        if self.page:
            self.page.push_route("/dictionary_management")
    
    def open_feed_management(self, e):
        """Open feed management screen"""
        print(f"Feed management button clicked! Page: {self.page}")
        if not self.page:
            print("ERROR: self.page is None!")
            return
        
        from feed_management_screen import create_feed_management_screen
        feed_management_view = create_feed_management_screen(self.page)
        self.page.views.append(feed_management_view)
        self.page.go("/feed_management")
    
    def save_settings(self, e):
        """Save app settings"""
        try:
            prefs_file = os.path.join(Path.home(), "app_preferences.json")
            
            # Load existing preferences or create new
            if os.path.exists(prefs_file):
                with open(prefs_file, "r") as f:
                    prefs = json.load(f)
            else:
                prefs = {}
            
            # Update with new settings
            prefs["theme_mode"] = self.theme_mode
            prefs["auto_translate"] = self.auto_translate
            prefs["save_history"] = self.save_history
            
            # Save to file
            with open(prefs_file, "w") as f:
                json.dump(prefs, f)
            
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Settings saved"))
                )
                
        except Exception as e:
            print(f"Error saving app settings: {str(e)}")
            if self.page:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Failed to save settings"))
                )
    
    def build(self):
        return ft.Container(
            content=self.content,
            padding=16
        )

def handle_back(page):
    """Handle back navigation from settings screen"""
    if page and len(page.views) > 1:
        page.views.pop()
        page.update()

def create_settings_screen(page):
    """Factory function to create a SettingsScreen instance"""
    settings_screen = SettingsScreen()
    
    # Override the open_feed_management method to work with the page
    def handle_feed_management_click(e):
        from feed_management_screen import create_feed_management_screen
        feed_management_view = create_feed_management_screen(page)
        page.views.append(feed_management_view)
        page.go("/feed_management")
    
    # Find and update the feed management button's click handler
    for control in settings_screen.content.controls:
        if isinstance(control, ft.ElevatedButton) and "RSS Feed Management" in str(control.content):
            control.on_click = handle_feed_management_click
            break
    
    # Return a View with the settings screen content directly
    return ft.View(
        route="/settings",
        appbar=ft.AppBar(
            title=ft.Text("Settings"),
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                on_click=lambda e: handle_back(page)
            )
        ),
        controls=[settings_screen.content]
    )
