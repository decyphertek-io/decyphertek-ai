import flet as ft
import feedparser
import re
import sqlite3
import os
from pathlib import Path
import asyncio
import tempfile
import json
import aiohttp
from datetime import datetime
import platform
import subprocess
from functools import partial

# Import all converted modules
from article_detail_screen import create_article_detail_screen
from article_extractor import ArticleExtractor
from cache_service import CacheService
from dictionary_service import DictionaryService
from feed_management_screen import create_feed_management_screen
from dictionary_management_screen import create_dictionary_management_screen
from interactive_translator_widget import create_interactive_translator_widget
from settings_screen import create_settings_screen
from tts_settings_screen import create_tts_settings_screen
from sentence_widget import SentenceWidget

class FeedItem:
    def __init__(self, item, source_name):
        self.item = item
        self.source_name = source_name
        self.translated_title = None
        self.is_translating = False
        self.show_translation = False
        self.contextual_translation = None
        self.show_contextual_translation = False
        self.guid = getattr(item, 'id', None) or getattr(item, 'link', None)

async def speak(text, language_code="es-US", speech_rate=0.5):
    """Speak text using gTTS for better quality speech"""
    try:
        # Use gTTS for better quality speech
        from gtts import gTTS
        import io
        import pygame
        import tempfile
        import os
        
        # Extract language code for gTTS (e.g., 'es' from 'es-US')
        lang = language_code.split('-')[0]
        
        # Create gTTS object
        tts = gTTS(text=text, lang=lang, slow=False, lang_check=False)
        
        # Create a temporary file to save the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_filename = fp.name
        
        # Save the audio to the temporary file
        tts.save(temp_filename)
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Load and play the audio
        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
        
        # Clean up the temporary file
        os.unlink(temp_filename)
        
    except Exception as e:
        print(f"gTTS error: {str(e)}")
        # Fallback to pyttsx3 if gTTS fails
        try:
            import pyttsx3
            
            # Initialize the TTS engine
            engine = pyttsx3.init()
            
            # Customizing speech properties
            engine.setProperty('rate', int(speech_rate * 200))  # Speed of speech (words per minute)
            engine.setProperty('volume', 0.8)  # Volume (0.0 to 1.0)
            
            # Try to set voice based on language
            voices = engine.getProperty('voices')
            language = language_code.split('-')[0]
            
            # Find a voice that matches the language
            for voice in voices:
                if language in voice.id.lower() or language in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            # Speak the text
            engine.say(text)
            engine.runAndWait()
        except Exception as e2:
            print(f"pyttsx3 fallback error: {str(e2)}")
            # Final fallback to system TTS
            system = platform.system()
            try:
                if system == "Windows":
                    # Use PowerShell for Windows
                    ps_script = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Rate = {int((speech_rate - 0.5) * 10)}; $speak.Speak("{text}")'
                    subprocess.Popen(["powershell", "-Command", ps_script])
                elif system == "Darwin":  # macOS
                    # Use say command for macOS
                    language = language_code.split('-')[0]
                    voice = "Juan" if language == "es" else "Alex"  # Default Spanish and English voices
                    subprocess.Popen(["say", "-v", voice, "-r", str(int(speech_rate * 200)), text])
                elif system == "Linux":
                    # Use espeak for Linux
                    language = language_code.split('-')[0]
                    speed = int(speech_rate * 200)
                    subprocess.Popen(["espeak", "-v", language, "-s", str(speed), text])
                else:
                    # No TTS engine available
                    raise Exception("No TTS engine available")
            except Exception as e3:
                print(f"System TTS fallback error: {str(e3)}")

def main(page: ft.Page):
    page.title = "LangTek"
    page.theme_mode = "dark"
    page.bgcolor = "#121212"  # Dark background like Flutter app
    page.padding = 10
    page.window_width = 400
    page.window_height = 800
    
    # Services
    dictionary_service = DictionaryService()
    cache_service = CacheService()
    article_extractor = ArticleExtractor()
    
    # State
    feed_items = []
    feed_urls = []
    feed_names = {}
    contextual_translations = {}
    show_contextual_translations = {}
    
    # TTS settings
    tts_settings = {
        "speech_rate": 0.5,
        "spanish_code": "es-US",
        "english_code": "en-US"
    }
    
    # UI Components
    loading_indicator = ft.ProgressRing(visible=False, width=24, height=24)
    feed_list = ft.ListView(expand=True, spacing=4, padding=10)
    
    async def load_settings():
        print("Loading settings...")
        # Load feed URLs from preferences
        prefs_file = os.path.join(os.path.dirname(__file__), "storage", "data", "feed_preferences.json")
        print(f"Looking for prefs file: {prefs_file}")
        if os.path.exists(prefs_file):
            print("Prefs file exists, loading...")
            try:
                with open(prefs_file, "r") as f:
                    prefs = json.load(f)
                    print(f"Loaded prefs: {prefs}")
                    feed_details = prefs.get("feed_details", [])
                    print(f"Found feed_details: {feed_details}")
                    
                    # Load feeds from feed_details format
                    for feed in feed_details:
                        if isinstance(feed, dict) and "url" in feed:
                            feed_urls.append(feed["url"])
                            print(f"Added feed URL: {feed['url']}")
                            if "name" in feed and feed["name"]:
                                feed_names[feed["url"]] = feed["name"]
                                print(f"Added feed name: {feed['name']}")
            except Exception as e:
                print(f"Error loading feed preferences: {str(e)}")
        else:
            print("Prefs file does not exist")
        
        # Use default if no feeds found
        if not feed_urls:
            print("No feeds found, using default")
            feed_urls.append("https://www.xataka.com/feedburner.xml")
        
        print(f"Final feed_urls: {feed_urls}")
        
        # Load TTS settings
        tts_prefs_file = os.path.join(Path.home(), "tts_preferences.json")
        if os.path.exists(tts_prefs_file):
            try:
                with open(tts_prefs_file, "r") as f:
                    prefs = json.load(f)
                    tts_settings["speech_rate"] = prefs.get("tts_speech_rate", 0.5)
                    tts_settings["spanish_code"] = prefs.get("tts_spanish_code", "es-US")
                    tts_settings["english_code"] = prefs.get("tts_english_code", "en-US")
            except Exception as e:
                print(f"Error loading TTS preferences: {str(e)}")
    
    async def get_word_by_word_translation(spanish_title):
        word_regex = re.compile(r"([\wÀ-ÖØ-öø-ÿ]+|[.,!?;:])")
        matches = word_regex.finditer(spanish_title)
        translated_words = []
        
        for match in matches:
            original_word = match.group(0)
            if re.match(r"^[\wÀ-ÖØ-öø-ÿ]+$", original_word):
                translation = await dictionary_service.translate(original_word.lower())
                translated_words.append(translation if translation else original_word)
            else:
                translated_words.append(original_word)
                
        return ' '.join(translated_words)
    
    async def translate_all_titles(items):
        for item in items:
            if item.item.title and not item.translated_title and not item.is_translating:
                item.is_translating = True
                page.update()
                
                item.translated_title = await get_word_by_word_translation(item.item.title)
                item.is_translating = False
                
                update_feed_list()
                await asyncio.sleep(0.1)
    
    async def fetch_feeds():
        loading_indicator.visible = True
        page.update()
        
        try:
            feed_items.clear()
            for url in feed_urls:
                try:
                    feed = await fetch_rss_feed(url)
                    source_name = feed_names.get(url, feed.feed.title if hasattr(feed.feed, 'title') else url)
                    new_items = [FeedItem(item, source_name) for item in feed.entries]
                    
                    # Sort by publication date if available
                    sorted_items = sorted(
                        new_items, 
                        key=lambda x: getattr(x.item, 'published_parsed', datetime.now().timetuple()),
                        reverse=True
                    )
                    
                    feed_items.extend(sorted_items)
                except Exception as e:
                    print(f"Error fetching feed {url}: {str(e)}")
                
                update_feed_list()
                
            # Start background translation
            page.run_task(translate_all_titles, feed_items)
                
        except Exception as e:
            print(f"Error: {e}")
            
        loading_indicator.visible = False
        update_feed_list()
    
    async def fetch_rss_feed(url):
        """Fetch RSS feed using aiohttp and feedparser"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        return feedparser.parse(content)
                    else:
                        print(f"Error fetching RSS feed: HTTP {response.status}")
                        return feedparser.FeedParserDict()
        except Exception as e:
            print(f"Error fetching RSS feed: {str(e)}")
            return feedparser.FeedParserDict()
    
    def get_image_url(item):
        # Try to extract image from description
        if hasattr(item, 'description') and item.description:
            try:
                import re
                img_pattern = re.compile(r'<img[^>]+src="([^"]+)"')
                match = img_pattern.search(item.description)
                if match:
                    return match.group(1)
            except:
                pass
        return None
    
    async def get_contextual_translation(title, item_id):
        # Toggle visibility if translation already exists
        if item_id in contextual_translations:
            show_contextual_translations[item_id] = not show_contextual_translations.get(item_id, False)
            update_feed_list()
            return
            
        try:
            # Set loading state
            contextual_translations[item_id] = "Translating..."
            show_contextual_translations[item_id] = True
            update_feed_list()
            
            # Use Google Translate API
            async with aiohttp.ClientSession() as session:
                url = f'https://translate.googleapis.com/translate_a/single?client=gtx&sl=es&tl=en&dt=t&q={title}'
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        translated_text = ""
                        
                        if data and isinstance(data[0], list):
                            for segment in data[0]:
                                if segment and len(segment) > 0:
                                    translated_text += segment[0]
                                    
                        contextual_translations[item_id] = translated_text or "No translation available"
                    else:
                        contextual_translations[item_id] = "Translation failed"
                        
            update_feed_list()
        except Exception as e:
            print(f"Translation error: {e}")
            contextual_translations[item_id] = "Translation service unavailable"
            update_feed_list()
    
    async def open_article(e, item):
        """Open article detail screen when a feed item is clicked"""
        print(f"Opening article: {item.item.title}")
        
        # Create the article detail screen
        article_screen = create_article_detail_screen(item, page)
        print(f"Article screen created: {article_screen}")
        
        # Simple approach - just navigate to the article view
        page.views.clear()
        page.views.append(
            ft.View(
                route="/",
                controls=[main_view],
                appbar=main_appbar
            )
        )
        page.views.append(
            ft.View(
                route=f"/article/{item.guid}",
                controls=[article_screen],
                appbar=ft.AppBar(
                    title=ft.Text("Article"),
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: page.go("/")
                    )
                )
            )
        )
        
        # Navigate to the route
        print(f"Navigating to: /article/{item.guid}")
        page.go(f"/article/{item.guid}")
    
    async def open_settings(e):
        """Open settings screen"""
        # Create the settings screen view
        settings_view = create_settings_screen(page)
        
        # Add the view to the page
        page.views.append(settings_view)
        
        # Navigate to the route
        page.go("/settings")
        
        # Handle return from settings
        def handle_view_pop(e):
            if e.data:
                # Refresh feeds if needed
                page.run_task(fetch_feeds)
        
        # Set up the pop handler
        page.on_view_pop = handle_view_pop
    
    async def open_feed_management(e):
        """Open feed management screen"""
        # Create the feed management screen view
        feed_management_view = create_feed_management_screen(page)
        
        # Add the view to the page
        page.views.append(feed_management_view)
        
        # Navigate to the route
        page.go("/feed_management")
        
        # Handle return from feed management
        def handle_view_pop(e):
            if e.data:
                # Refresh feeds if needed
                page.run_task(fetch_feeds)
        
        # Set up the pop handler
        page.on_view_pop = handle_view_pop
    
    async def open_translator(e):
        """Open interactive translator widget"""
        # Create a route name for the translator
        route = "/translator"
        
        # Create the translator widget
        translator_widget = create_interactive_translator_widget(page)
        
        # Set up the route
        page.views.append(
            ft.View(
                route=route,
                appbar=ft.AppBar(
                    title=ft.Text("Interactive Translator"),
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: page.pop_route()
                    )
                ),
                controls=[
                    ft.Container(
                        content=translator_widget,
                        padding=10,
                        expand=True
                    )
                ]
            )
        )
        
        # Navigate to the route
        page.go(route)
    
    def update_feed_list():
        feed_list.controls.clear()
        
        for item in feed_items:
            # Get image if available
            image_url = get_image_url(item.item)
            image_container = None
            
            if image_url:
                image_container = ft.Container(
                    content=ft.Image(
                        src=image_url,
                        fit=ft.ImageFit.COVER,
                        width=400,
                        height=200,
                    ),
                    border_radius=ft.border_radius.all(4),
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    margin=ft.margin.only(bottom=12)
                )
            
            # Main title row with speak button
            title_row = ft.Row(
                controls=[
                    ft.Text(
                        item.item.title,
                        size=17,
                        weight=ft.FontWeight.BOLD,
                        max_lines=3,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        expand=True,
                        color="white"
                    ),
                    ft.IconButton(
                        icon="volume_up",
                        icon_size=24,
                        on_click=lambda e, t=item.item.title: page.run_task(speak, t, tts_settings["spanish_code"], tts_settings["speech_rate"])
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
            
            # Translated title row with translate button
            translated_row = ft.Row(
                controls=[
                    ft.Text(
                        item.translated_title if item.translated_title else "(Translating...)",
                        size=15,
                        color="grey500",
                        italic=True,
                        max_lines=3,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        expand=True
                    ) if not item.is_translating else ft.ProgressRing(width=16, height=16),
                    ft.IconButton(
                        icon="translate",
                        icon_size=24,
                        on_click=lambda e, t=item.item.title, i=item.guid: page.run_task(get_contextual_translation, t, i)
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
            
            # Contextual translation row if available
            contextual_row = None
            if item.guid in contextual_translations and show_contextual_translations.get(item.guid, False):
                contextual_row = ft.Row(
                    controls=[
                        ft.Text(
                            contextual_translations[item.guid],
                            size=15,
                            color="grey500",
                            italic=True,
                            max_lines=3,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True
                        ),
                        ft.IconButton(
                            icon="volume_up",
                            icon_size=24,
                            on_click=lambda e, t=contextual_translations[item.guid]: page.run_task(speak, t, tts_settings["english_code"], tts_settings["speech_rate"])
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                )
            
            # Source name
            source_text = ft.Text(
                item.source_name,
                size=12,
                color="grey500",
                italic=True,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS
            )
            
            # Build column controls
            column_controls = []
            if image_container:
                column_controls.append(image_container)
                
            column_controls.extend([
                title_row,
                ft.Container(height=4),
                translated_row
            ])
            
            if contextual_row:
                column_controls.extend([
                    ft.Container(height=5),
                    contextual_row
                ])
                
            column_controls.extend([
                ft.Container(height=8),
                source_text
            ])
            
            # Create the card wrapped in a clickable container
            card = ft.Container(
                content=ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            controls=column_controls,
                            spacing=0
                        ),
                        padding=12
                    ),
                    elevation=2,
                ),
                margin=ft.margin.symmetric(horizontal=8, vertical=4),
                on_click=lambda e, i=item: page.run_task(open_article, e, i),
                ink=True,
            )
            
            feed_list.controls.append(card)
        
        page.update()
    
    # Initialize services and load settings
    async def initialize():
        print("Initialize function called!")
        try:
            print("Initializing dictionary service...")
            try:
                await dictionary_service.initialize()
            except Exception as e:
                print(f"Dictionary service error (continuing): {str(e)}")
            
            print("Initializing cache service...")
            try:
                await cache_service.initialize()
            except Exception as e:
                print(f"Cache service error (continuing): {str(e)}")
            
            print("Loading settings...")
            await load_settings()
            print("Fetching feeds...")
            await fetch_feeds()
            print("Initialization complete!")
        except Exception as e:
            print(f"Critical initialization error: {str(e)}")
    
    # Start initialization immediately
    page.run_task(initialize)

    # Initial setup
    main_view = ft.Column([
        ft.Stack(
            [   
                feed_list,
                ft.Container(
                    content=loading_indicator,
                    alignment=ft.alignment.center,
                    visible=False
                )
            ],
            expand=True
        )
    ])
    
    main_appbar = ft.AppBar(
        leading=ft.Icon(name="rss_feed"),
        leading_width=40,
        title=ft.Text("LangTek"),
        center_title=False,
        bgcolor="#1F1F1F",
        actions=[
            ft.IconButton(icon="refresh", on_click=lambda e: page.run_task(fetch_feeds)),
            ft.IconButton(icon="translate", on_click=lambda e: page.run_task(open_translator, e)),
            ft.IconButton(icon="settings", on_click=lambda e: page.run_task(open_settings, e)),
        ],
    )
    
    page.views.append(
        ft.View(
            route="/",
            controls=[main_view],
            appbar=main_appbar
        )
    )

ft.FLET_DISABLE_AUDIO = True
ft.app(target=main, assets_dir="assets")
