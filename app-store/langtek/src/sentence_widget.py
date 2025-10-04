import flet as ft
import aiohttp
import json
import asyncio
import re
from pathlib import Path
import os

class SentenceWidget(ft.Column):
    def __init__(
        self,
        spanish_text: str,
        is_title: bool = False,
        dictionary_service=None,
        tts_service=None,
        cache_service=None,
        spanish_language_code: str = "es-ES",
        english_language_code: str = "en-US",
    ):
        super().__init__()
        self.spanish_text = spanish_text
        self.is_title = is_title
        self.dictionary_service = dictionary_service
        self.tts_service = tts_service
        self.cache_service = cache_service
        self.spanish_language_code = spanish_language_code
        self.english_language_code = english_language_code
        
        # State variables
        self.word_by_word_translation = None
        self.contextual_translation = None
        self.is_contextual_translation_visible = False
        self.is_loading = True
        
        # UI components
        self.text_spanish = ft.Text(
            spanish_text,
            weight=ft.FontWeight.BOLD if is_title else ft.FontWeight.W_500,
            size=24 if is_title else 17,
            text_align=ft.TextAlign.LEFT,
        )
        
        self.text_word_by_word = ft.Text(
            "Translating...",
            italic=True,
            color='#9e9e9e',
            size=15,
            text_align=ft.TextAlign.LEFT,
        )
        
        self.text_contextual = ft.Text(
            "",
            italic=True,
            color='#9e9e9e',
            size=15,
            text_align=ft.TextAlign.LEFT,
            visible=False,
        )
        
        # Buttons
        self.btn_speak_spanish = ft.IconButton(
            icon=ft.Icons.VOLUME_UP,
            tooltip="Speak Spanish",
            icon_size=20,
            on_click=self.speak_spanish,
        )
        
        self.btn_contextual_translation = ft.IconButton(
            icon=ft.Icons.TRANSLATE,
            tooltip="Contextual Translation",
            icon_size=20,
            on_click=self.get_contextual_translation,
        )
        
        self.btn_speak_english = ft.IconButton(
            icon=ft.Icons.VOLUME_UP,
            tooltip="Speak English Translation",
            icon_size=20,
            on_click=self.speak_english,
            visible=False,
        )
    
    def did_mount(self):
        # Equivalent to initState in Flutter
        asyncio.create_task(self.translate_word_by_word())
    
    async def translate_word_by_word(self):
        try:
            # Check cache first
            cached_translation = None
            if self.cache_service:
                cached_translation = await self.cache_service.get_cached_translation(
                    source_text=self.spanish_text,
                    language_from='es',
                    language_to='en',
                    translation_type='word-by-word',
                )
            
            if cached_translation:
                self.word_by_word_translation = cached_translation
                self.text_word_by_word.value = cached_translation
                self.is_loading = False
                await self.update_async()
                return
            
            # No cache, do translation
            word_regex = re.compile(r"([\wÀ-ÖØ-öø-ÿ]+|[.,!?;:])")
            matches = word_regex.finditer(self.spanish_text)
            
            translated_words = []
            
            for match in matches:
                original_word = match.group(0)
                word_to_translate = original_word.lower()  # Used for DB lookup

                if re.match(r"^[\wÀ-ÖØ-öø-ÿ]+$", word_to_translate):  # Check if it's a translatable word (not punctuation)
                    db_translation = None
                    if self.dictionary_service:
                        db_translation = await self.dictionary_service.translate(word_to_translate)
                    
                    final_word_to_add = original_word  # default to originalWord

                    if db_translation:
                        # Check if the original Spanish word's first letter was capitalized
                        is_original_first_letter_capitalized = (
                            len(original_word) > 0 and 
                            original_word[0] != original_word[0].lower()
                        )

                        if is_original_first_letter_capitalized:
                            # Capitalize the first letter of the translation
                            final_word_to_add = db_translation[0].upper() + db_translation[1:]
                        else:
                            # Use the translation as is (it's lowercase from DB)
                            final_word_to_add = db_translation
                    
                    translated_words.append(final_word_to_add)
                else:
                    # It's punctuation or a non-word token, add it as is
                    translated_words.append(original_word)
            
            translation = " ".join(translated_words)
            
            # Cache the translation
            if self.cache_service:
                await self.cache_service.cache_translation(
                    source_text=self.spanish_text,
                    translated_text=translation,
                    language_from='es',
                    language_to='en',
                    translation_type='word-by-word',
                )
            
            self.word_by_word_translation = translation
            self.text_word_by_word.value = translation
            self.is_loading = False
            await self.update_async()
            
        except Exception as e:
            print(f"Word-by-word translation error: {str(e)}")
            self.word_by_word_translation = "Translation failed"
            self.text_word_by_word.value = "Translation failed"
            self.is_loading = False
            await self.update_async()
    
    async def get_contextual_translation(self, e=None):
        if (self.contextual_translation and 
            self.contextual_translation != "Translating..." and 
            self.contextual_translation != "Translation failed. Please try again."):
            # Toggle visibility if translation already exists
            self.is_contextual_translation_visible = not self.is_contextual_translation_visible
            self.text_contextual.visible = self.is_contextual_translation_visible
            self.btn_speak_english.visible = self.is_contextual_translation_visible
            await self.update_async()
            return
        
        try:
            # Show loading state
            self.contextual_translation = "Translating..."
            self.text_contextual.value = "Translating..."
            self.is_contextual_translation_visible = True
            self.text_contextual.visible = True
            await self.update_async()
            
            # Check cache first
            cached_translation = None
            if self.cache_service:
                cached_translation = await self.cache_service.get_cached_translation(
                    source_text=self.spanish_text,
                    language_from='es',
                    language_to='en',
                    translation_type='contextual',
                )
            
            if cached_translation:
                # Use cached translation
                self.contextual_translation = cached_translation
                self.text_contextual.value = cached_translation
                self.is_contextual_translation_visible = True
                self.text_contextual.visible = True
                self.btn_speak_english.visible = True
                await self.update_async()
                return
            
            # No cache available, use direct HTTP request to Google Translate API
            async with aiohttp.ClientSession() as session:
                url = f'https://translate.googleapis.com/translate_a/single?client=gtx&sl=es&tl=en&dt=t&q={self.spanish_text}'
                async with session.get(url) as response:
                    if response.status == 200:
                        # Parse the response
                        json_response = await response.json()
                        
                        # Extract the translated text from the response
                        translated_text = ""
                        
                        if isinstance(json_response, list) and json_response and isinstance(json_response[0], list):
                            translations = json_response[0]
                            for segment in translations:
                                if isinstance(segment, list) and segment:
                                    translated_text += str(segment[0])
                        
                        if not translated_text:
                            translated_text = "No translation available"
                        
                        # Cache the translation
                        if self.cache_service:
                            await self.cache_service.cache_translation(
                                source_text=self.spanish_text,
                                translated_text=translated_text,
                                language_from='es',
                                language_to='en',
                                translation_type='contextual',
                            )
                        
                        self.contextual_translation = translated_text
                        self.text_contextual.value = translated_text
                        self.is_contextual_translation_visible = True
                        self.text_contextual.visible = True
                        self.btn_speak_english.visible = True
                        await self.update_async()
                    else:
                        raise Exception('Failed to load translation')
                        
        except Exception as e:
            print(f"Contextual translation error: {str(e)}")
            # Try to get cached translation as fallback
            cached_translation = None
            if self.cache_service:
                cached_translation = await self.cache_service.get_cached_translation(
                    source_text=self.spanish_text,
                    language_from='es',
                    language_to='en',
                    translation_type='contextual',
                )
            
            if cached_translation:
                # Use cached translation as fallback
                self.contextual_translation = cached_translation
                self.text_contextual.value = cached_translation
                self.is_contextual_translation_visible = True
                self.text_contextual.visible = True
                self.btn_speak_english.visible = True
                await self.update_async()
                return
            
            # Handle translation error when no cache is available
            self.page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Translation service unavailable. Please try again later.")
            ))
            # Reset translation if error occurs
            self.contextual_translation = "Translation failed. Please try again."
            self.text_contextual.value = "Translation failed. Please try again."
            await self.update_async()
    
    async def speak_spanish(self, e=None):
        if not self.spanish_text:
            return
        
        if self.tts_service:
            try:
                # Get speech rate from settings (default to 0.5)
                speech_rate = 0.5  # This would come from settings in a real app
                
                await self.tts_service.speak(
                    text=self.spanish_text,
                    language=self.spanish_language_code,
                    rate=speech_rate
                )
            except Exception as e:
                print(f"Spanish TTS error: {str(e)}")
                # Try with fallback codes
                fallback_codes = ['es-US', 'es-ES', 'es-MX', 'es']
                success = False
                
                for code in fallback_codes:
                    try:
                        await self.tts_service.speak(
                            text=self.spanish_text,
                            language=code,
                            rate=0.5  # Default fallback rate
                        )
                        success = True
                        break
                    except Exception:
                        continue
                
                if not success:
                    self.page.show_snack_bar(ft.SnackBar(
                        content=ft.Text("Spanish TTS failed. Check TTS settings")
                    ))
    
    async def speak_english(self, e=None):
        if not self.contextual_translation:
            return
        
        if self.tts_service:
            try:
                # Get speech rate from settings (default to 0.5)
                speech_rate = 0.5  # This would come from settings in a real app
                
                await self.tts_service.speak(
                    text=self.contextual_translation,
                    language=self.english_language_code,
                    rate=speech_rate
                )
            except Exception as e:
                print(f"English TTS error: {str(e)}")
                # Try with fallback codes
                fallback_codes = ['en-US', 'en-GB', 'en']
                success = False
                
                for code in fallback_codes:
                    try:
                        await self.tts_service.speak(
                            text=self.contextual_translation,
                            language=code,
                            rate=0.5  # Default fallback rate
                        )
                        success = True
                        break
                    except Exception:
                        continue
                
                if not success:
                    self.page.show_snack_bar(ft.SnackBar(
                        content=ft.Text("English TTS failed. Check TTS settings")
                    ))
    
    def build(self):
        # Spanish text with TTS button
        row_spanish = ft.Row(
            controls=[
                ft.Container(
                    content=self.text_spanish,
                    expand=True,
                ),
                self.btn_speak_spanish,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        
        # Word-by-word translation with contextual translation button
        row_word_by_word = ft.Row(
            controls=[
                ft.Container(
                    content=self.text_word_by_word,
                    expand=True,
                ),
                self.btn_contextual_translation,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        
        # Contextual translation (if available)
        row_contextual = ft.Row(
            controls=[
                ft.Container(
                    content=self.text_contextual,
                    expand=True,
                ),
                self.btn_speak_english,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
            visible=self.is_contextual_translation_visible,
        )
        
        return ft.Column(
            controls=[
                row_spanish,
                ft.Container(height=5),  # Spacing
                row_word_by_word,
                ft.Container(
                    content=row_contextual,
                    padding=ft.padding.only(top=5),
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )
