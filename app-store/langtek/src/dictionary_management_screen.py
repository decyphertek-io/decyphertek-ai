import flet as ft
import asyncio
from dictionary_service import DictionaryService

class DictionaryManagementScreen(ft.Column):
    def __init__(self):
        super().__init__()
        self.dictionary_service = DictionaryService()
        self.spanish_controller = ft.TextField(
            label="Spanish Word",
            border=ft.InputBorder.OUTLINE,
        )
        self.english_controller = ft.TextField(
            label="English Translation",
            border=ft.InputBorder.OUTLINE,
        )
        self.search_result = ""
        self.status_message = ""
        self.status_text = ft.Text(self.status_message)
        self.result_text = ft.Text(self.search_result, size=16)
        
    def did_mount(self):
        # Initialize the database when the screen is first created
        asyncio.create_task(self.initialize_dictionary())
        
    async def initialize_dictionary(self):
        try:
            await self.dictionary_service.initialize()
            self.status_message = "Dictionary ready."
            self.status_text.value = self.status_message
            await self.update_async()
        except Exception as e:
            self.status_message = f"Error initializing dictionary: {str(e)}"
            self.status_text.value = self.status_message
            print(f"DM Screen: Error initializing dictionary: {str(e)}")
            await self.update_async()
            
    async def search_word(self, e):
        if not self.spanish_controller.value:
            self.status_message = "Please enter a Spanish word to search."
            self.status_text.value = self.status_message
            await self.update_async()
            return
            
        result = await self.dictionary_service.translate(self.spanish_controller.value)
        if result:
            self.search_result = f"Translation: {result}"
            self.result_text.value = self.search_result
            self.english_controller.value = result
            self.status_message = "Word found."
            self.status_text.value = self.status_message
        else:
            self.search_result = "Word not found."
            self.result_text.value = self.search_result
            self.english_controller.value = ""
            self.status_message = "Word not found in dictionary."
            self.status_text.value = self.status_message
            
        await self.update_async()
        
    async def add_or_update_word(self, e):
        if not self.spanish_controller.value or not self.english_controller.value:
            self.status_message = "Please enter both Spanish and English words."
            self.status_text.value = self.status_message
            await self.update_async()
            return
            
        # Try to find the word first to decide if it's an add or update
        existing_translation = await self.dictionary_service.translate(self.spanish_controller.value)
        
        if existing_translation:
            # Word exists, let's update
            updated_rows = await self.dictionary_service.update_translation(
                self.spanish_controller.value,
                self.english_controller.value
            )
            if updated_rows > 0:
                self.status_message = "Translation updated successfully."
                self.status_text.value = self.status_message
            else:
                self.status_message = "Failed to update translation. Word might not exist or an error occurred."
                self.status_text.value = self.status_message
        else:
            # Word doesn't exist, let's add
            await self.dictionary_service.add_word(
                self.spanish_controller.value,
                self.english_controller.value
            )
            self.status_message = "Word added successfully."
            self.status_text.value = self.status_message
            
        self.spanish_controller.value = ""
        self.english_controller.value = ""
        self.search_result = ""
        self.result_text.value = self.search_result
        await self.update_async()
        
    def build(self):
        return ft.Container(
            content=ft.Column(
                [
                    self.status_text,
                    ft.Container(height=10),
                    self.spanish_controller,
                    ft.Container(height=10),
                    self.english_controller,
                    ft.Container(height=20),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                text="Search",
                                on_click=self.search_word
                            ),
                            ft.ElevatedButton(
                                text="Add/Update",
                                on_click=self.add_or_update_word
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    ),
                    ft.Container(height=20),
                    self.result_text,
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            padding=16,
        )

def create_dictionary_management_screen(page):
    dictionary_screen = DictionaryManagementScreen()
    
    # Return a View with appbar and content
    return ft.View(
        route="/dictionary-management",
        appbar=ft.AppBar(
            title=ft.Text("Manage Dictionary"),
        ),
        controls=[dictionary_screen]
    )
