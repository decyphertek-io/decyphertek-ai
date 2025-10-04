import flet as ft
import re
import asyncio
import html
from bs4 import BeautifulSoup
import aiohttp
from datetime import datetime

from dictionary_service import DictionaryService
from cache_service import CacheService
from article_extractor import ArticleExtractor
from sentence_widget import SentenceWidget

# Helper class to hold parts for a single sentence and its translation
class SentenceTranslationUnit:
    def __init__(self, id, spanish_parts, english_parts, contextual_translation=None):
        self.id = id  # Unique ID for Key
        self.spanish_parts = spanish_parts  # Words and punctuation of the Spanish sentence
        self.english_parts = english_parts  # Corresponding English words, placeholders, or punctuation
        self.contextual_translation = contextual_translation  # Full contextual translation of the sentence
        self.is_contextual_translation_visible = False  # Whether to show the contextual translation

    @property
    def spanish_sentence_text(self):
        return ' '.join(self.spanish_parts)


class ArticleDetailScreen(ft.Column):
    def __init__(self, article, page=None):
        super().__init__()
        self.article = article
        self.page = page
        self.dictionary_service = DictionaryService()
        self.cache_service = CacheService()
        self.article_extractor = ArticleExtractor()
        
        self.is_dictionary_ready = False
        self.translation_units = []
        self.is_translating_in_progress = False
        self.is_content_prepped = False
        self.content_error = None
        
        # TTS language codes
        self.spanish_language_code = 'es-US'
        self.english_language_code = 'en-US'
        
        # UI components
        self.loading_indicator = ft.ProgressRing(
            width=24,
            height=24,
            stroke_width=2,
            color='#2196f3'
        )
        
        self.content_column = ft.Column(
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

    async def did_mount_async(self):
        print("ArticleDetailScreen did_mount_async called")
        await self.init_and_prepare_content_for_translation()
    
    def did_mount(self):
        print("ArticleDetailScreen did_mount called")
        # Use page.run_task if available, otherwise fall back to self.page.run_task
        if hasattr(self, 'page') and self.page:
            self.page.run_task(self.did_mount_async)
        else:
            # If page is not available yet, try to get it from the parent
            self.run_task(self.did_mount_async)
    
    def build(self):
        return ft.Container(
            content=ft.Column([
                # App bar is handled by the parent
                
                # Loading indicator
                ft.Container(
                    content=self.loading_indicator,
                    alignment=ft.MainAxisAlignment.CENTER,
                    visible=self.is_translating_in_progress,
                    padding=ft.padding.symmetric(vertical=8)
                ),
                
                # Content
                self.content_column,
            ]),
            expand=True
        )
    
    async def init_and_prepare_content_for_translation(self):
        print("init_and_prepare_content_for_translation called")
        self.is_translating_in_progress = True
        self.update()
        
        try:
            # Initialize dictionary service
            print("Initializing dictionary service")
            await self.dictionary_service.initialize()
            self.is_dictionary_ready = True
            print("Dictionary service initialized")
            self.update()
            
            # Get article content
            print("Getting article content")
            description = await ArticleExtractor.get_full_content(
                getattr(self.article.item, 'description', ''), 
                getattr(self.article.item, 'link', '')
            )
            print(f"Article content retrieved, length: {len(description) if description else 0}")
            
            if not description or description.strip() == "":
                self.content_error = "No content available for this article."
                print("No content available for this article.")
                self.is_content_prepped = True  # Allow UI to show error
                self.is_translating_in_progress = False
                self.update()
                return
            
            # Parse HTML to plain text
            plain_text = self.parse_html_to_plain_text(description)
            print(f"Plain text parsed, length: {len(plain_text) if plain_text else 0}")
            
            # Segment text into sentences and prepare for translation
            self.segment_text_and_set_placeholders(plain_text)
            print(f"Text segmented into {len(self.translation_units)} translation units")
            
            self.is_content_prepped = True  # Now the UI can build with placeholders
            self.update()
            
            # A small delay to ensure UI renders placeholders before intensive translation starts
            await asyncio.sleep(0.2)
            
            # Begin progressive translation
            await self.begin_progressive_word_translation()
            
        except Exception as e:
            print(f"Error during content preparation: {str(e)}")
            self.content_error = f"Error during content preparation: {str(e)}"
            self.is_content_prepped = True  # Allow UI to show error
            self.is_translating_in_progress = False
            self.update()
    
    def parse_html_to_plain_text(self, html_string):
        if not html_string or html_string.strip() == "":
            return ""
        
        try:
            soup = BeautifulSoup(html_string, 'html.parser')
            text = soup.get_text()
            # Normalize whitespace: replace multiple spaces/newlines with a single space
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception:
            return html_string  # Fallback to original if parsing fails
    
    def segment_text_and_set_placeholders(self, plain_text):
        self.translation_units = []
        
        # Skip metadata in the article content
        if len(plain_text) > 200:
            plain_text = plain_text[200:]
        
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z\u00BF\u00A1])|\n+', plain_text)
        
        word_or_punctuation_regex = re.compile(r"([\wÀ-ÖØ-öø-ÿ]+(?:[''][\wÀ-ÖØ-öø-ÿ]+)*|[.,!?;:])")
        sentence_id_counter = 0
        
        for sentence_text in sentences:
            if not sentence_text.strip():
                continue
                
            current_spanish_parts = []
            current_english_parts = []
            matches = word_or_punctuation_regex.finditer(sentence_text)
            
            for match in matches:
                part = match.group(0)
                current_spanish_parts.append(part)
                
                # If it starts like a word
                if re.match(r"^[\wÀ-ÖØ-öø-ÿ]", part):
                    current_english_parts.append("(Translating...)")
                else:  # Punctuation
                    current_english_parts.append(part)
            
            if current_spanish_parts:
                self.translation_units.append(SentenceTranslationUnit(
                    id=f'sentence_{sentence_id_counter}',
                    spanish_parts=current_spanish_parts,
                    english_parts=current_english_parts
                ))
                sentence_id_counter += 1
        
        self.update_content_column()
    
    async def begin_progressive_word_translation(self):
        print(f"begin_progressive_word_translation called, dictionary_ready: {self.is_dictionary_ready}")
        if not self.is_dictionary_ready:
            self.is_translating_in_progress = False
            self.update()
            return
        
        self.is_translating_in_progress = True
        self.update()
        
        print(f"Starting translation for {len(self.translation_units)} translation units")
        for i in range(len(self.translation_units)):
            unit = self.translation_units[i]
            print(f"Translating unit {i}: {unit.spanish_sentence_text}")
            
            for j in range(len(unit.spanish_parts)):
                spanish_word = unit.spanish_parts[j]
                
                # Only translate if it's a placeholder
                if unit.english_parts[j] == "(Translating...)":
                    try:
                        translated_word = await self.dictionary_service.translate(spanish_word.lower())
                        self.translation_units[i].english_parts[j] = translated_word or spanish_word
                        print(f"Translated '{spanish_word}' to '{translated_word}'")
                    except Exception:
                        self.translation_units[i].english_parts[j] = spanish_word  # Fallback to original
                        print(f"Failed to translate '{spanish_word}', using original")
                
                # Update UI and delay to make updates visible
                self.update_content_column()
                await asyncio.sleep(0.075)  # Adjust timing as needed
        
        print("Translation process completed")
        self.is_translating_in_progress = False
        self.update()
    
    def update_content_column(self):
        print("update_content_column called")
        self.content_column.controls.clear()
        
        # Handle error state
        if self.content_error:
            print(f"Displaying error: {self.content_error}")
            self.content_column.controls.append(
                ft.Text(self.content_error, text_align=ft.TextAlign.CENTER)
            )
            self.update()
            return
        
        # Handle empty state
        if not self.translation_units and not self.is_translating_in_progress:
            print("Displaying no content message")
            self.content_column.controls.append(
                ft.Text("No content available for this article.", text_align=ft.TextAlign.CENTER)
            )
            self.update()
            return
        
        # Display each sentence with its translation
        # Skip the first few sentences if they're metadata
        start_index = min(2, len(self.translation_units)) if self.translation_units else 0
        print(f"Displaying {len(self.translation_units) - start_index} translation units")
        
        for i in range(start_index, len(self.translation_units)):
            unit = self.translation_units[i]
            sentence_widget = SentenceWidget(
                spanish_text=unit.spanish_sentence_text,
                dictionary_service=self.dictionary_service,
                cache_service=self.cache_service,
                spanish_language_code=self.spanish_language_code,
                english_language_code=self.english_language_code
            )
            self.content_column.controls.append(sentence_widget)
        
        self.update()
    
    async def launch_original_article_url(self, url_string):
        if not url_string:
            # Show error message
            return
        
        try:
            # Make sure URL is properly formatted
            formatted_url = url_string
            if not formatted_url.startswith('http://') and not formatted_url.startswith('https://'):
                formatted_url = f'https://{formatted_url}'
            
            # Open URL in browser
            await self.page.launch_url(formatted_url)
        except Exception as e:
            # Show error message
            pass

def create_article_detail_screen(article, page=None):
    """Factory function to create an ArticleDetailScreen instance"""
    return ArticleDetailScreen(article, page)
