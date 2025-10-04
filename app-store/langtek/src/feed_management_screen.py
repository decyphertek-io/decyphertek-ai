import flet as ft
import asyncio
import re
import os
import json
from pathlib import Path

class FeedManagementScreen(ft.Column):
    def __init__(self, page: ft.Page, initial_feed_urls=None):
        super().__init__()
        self._page = page  # Use private attribute to store page reference
        self.initial_feed_urls = initial_feed_urls or []
        self.prefs_key = 'rss_feed_urls'
        self.feed_urls = []
        self.feed_details = []
        self.made_changes = False
        
        # Text controllers
        self.new_feed_url = ft.TextField(
            label="Feed URL",
            hint_text="Enter RSS feed URL",
            autofocus=True
        )
        self.new_feed_name = ft.TextField(
            label="Feed Name (optional)",
            hint_text="Enter a name for this feed"
        )
        self.edit_feed_url = ft.TextField(
            label="Feed URL",
            hint_text="Enter RSS feed URL"
        )
        self.edit_feed_name = ft.TextField(
            label="Feed Name",
            hint_text="Enter a name for this feed"
        )
        
        # Main content
        self.feeds_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=10
        )

        # Set initial controls
        self.controls = [self.feeds_list]
        self.expand = True
        
        # Empty state message
        self.empty_message = ft.Container(
            content=ft.Text(
                "No RSS feeds added yet. Tap the + button to add one.",
                size=16,
                text_align=ft.TextAlign.CENTER
            ),
            alignment=ft.MainAxisAlignment.CENTER
        )
        

    def did_mount(self):
        print("did_mount called")
        print(f"Page reference: {self._page}")
        print(f"Initial feed_urls: {self.feed_urls}")
        print(f"Initial feed_details: {self.feed_details}")
        self._page.run_task(self.load_and_update_feeds)
        print("did_mount finished")

    async def load_and_update_feeds(self):
        print("load_and_update_feeds called")
        await self.load_feed_preferences()
        print(f"After load_feed_preferences: feed_urls={self.feed_urls}, feed_details={self.feed_details}")
        self.update_list_view()
        print("After update_list_view")
        self.update()
        print("After self.update")

    async def load_feed_preferences(self):
        """Load feed preferences from the JSON file."""
        prefs_file = os.path.join(os.path.dirname(__file__), "storage", "data", "feed_preferences.json")
        print(f"Looking for prefs file: {prefs_file}")
        
        if os.path.exists(prefs_file):
            try:
                with open(prefs_file, "r") as f:
                    prefs = json.load(f)
                print(f"Loaded prefs: {prefs}")
                
                # Load feed details
                self.feed_details = prefs.get('feed_details', [])
                # Extract URLs for backward compatibility with other parts of code
                self.feed_urls = [feed['url'] for feed in self.feed_details]
                
                print(f"Loaded feed_details: {self.feed_details}")
                print(f"Extracted feed_urls: {self.feed_urls}")
            except Exception as e:
                print(f"Error loading feed preferences: {e}")
                self.feed_urls = []
                self.feed_details = []
        else:
            print("Prefs file does not exist")
            self.feed_urls = []
            self.feed_details = []
    
    async def save_feed_names(self):
        prefs_file = os.path.join(os.path.dirname(__file__), "storage", "data", "feed_preferences.json")
        
        try:
            if os.path.exists(prefs_file):
                with open(prefs_file, "r") as f:
                    prefs = json.load(f)
            else:
                prefs = {}
            
            names = [feed.get('name', '') for feed in self.feed_details]
            prefs["rss_feed_names"] = names
            
            with open(prefs_file, "w") as f:
                json.dump(prefs, f)
        except Exception as e:
            print(f"Error saving feed names: {str(e)}")
    
    async def save_feed_urls_and_mark_changes(self):
        # Save only feed_details (contains both URLs and names)
        prefs_file = os.path.join(os.path.dirname(__file__), "storage", "data", "feed_preferences.json")
        
        try:
            prefs = {"feed_details": self.feed_details}
            
            with open(prefs_file, "w") as f:
                json.dump(prefs, f, indent=2)
        except Exception as e:
            print(f"Error saving feed data: {str(e)}")
        
        self.made_changes = True
        
    def add_feed(self, url, name):
        print(f"add_feed called with URL: '{url}', Name: '{name}'")
        if not url:
            print("URL is empty, showing snack bar")
            self._page.snack_bar = ft.SnackBar(
                content=ft.Text("URL cannot be empty")
            )
            self._page.snack_bar.open = True
            self._page.update()
            return
        
        if url in self.feed_urls:
            print("URL already exists, showing snack bar")
            self._page.snack_bar = ft.SnackBar(
                content=ft.Text("Feed URL already exists")
            )
            self._page.snack_bar.open = True
            self._page.update()
            return
        
        print(f"Adding URL to feed_urls list. Current list: {self.feed_urls}")
        self.feed_urls.append(url)
        print(f"feed_urls after append: {self.feed_urls}")
        
        # Generate default name if not provided
        if not name:
            default_name = re.sub(r'https?://', '', url)
            default_name = re.sub(r'www\.', '', default_name)
            default_name = default_name.split('/')[0]
            name = default_name
            print(f"Generated default name: '{name}'")
        
        feed_detail = {
            'url': url,
            'name': name
        }
        print(f"Adding feed detail: {feed_detail}")
        self.feed_details.append(feed_detail)
        print(f"feed_details after append: {self.feed_details}")
        
        print("Calling save_feed_urls_and_mark_changes")
        self._page.run_task(self.save_feed_urls_and_mark_changes)
        print("Calling update_list_view")
        self.update_list_view()
        print("Calling self.update")
        self.update()
    
    def remove_feed(self, index):
        self.feed_urls.pop(index)
        self.feed_details.pop(index)
        self._page.run_task(self.save_feed_urls_and_mark_changes)
        self.update_list_view()
        self.update()
    
    def edit_feed(self, index, new_url, new_name):
        # Check if the new URL already exists in another index
        if new_url != self.feed_urls[index] and new_url in self.feed_urls:
            self._page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Feed URL already exists")
            ))
            return
        
        self.feed_urls[index] = new_url
        
        # Generate default name if not provided
        if not new_name:
            default_name = re.sub(r'https?://', '', new_url)
            default_name = re.sub(r'www\.', '', default_name)
            default_name = default_name.split('/')[0]
            new_name = default_name
            
        self.feed_details[index] = {
            'url': new_url,
            'name': new_name
        }
        
        self._page.run_task(self.save_feed_urls_and_mark_changes)
        self.update_list_view()
        self.update()
    
    def show_add_feed_dialog(self, e):
        print(f"Add feed dialog called! Page: {self.page}")
        if not self._page:
            print("ERROR: No page reference!")
            return
            
        self.new_feed_url.value = ""
        self.new_feed_name.value = ""
        
        dialog = ft.AlertDialog(
            title=ft.Text("Add New RSS Feed"),
            content=ft.Column(
                [
                    self.new_feed_name,
                    ft.Container(height=16),
                    self.new_feed_url,
                ],
                tight=True,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self.close_dialog),
                ft.TextButton("Add", on_click=self.add_feed_from_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self._page.show_dialog(dialog)
        print("Dialog opened using page.show_dialog()")
    
    def show_edit_feed_dialog(self, e):
        index = e.control.data
        self.edit_feed_url.value = self.feed_urls[index]
        self.edit_feed_name.value = self.feed_details[index].get('name', '')
        
        dialog = ft.AlertDialog(
            title=ft.Text("Edit RSS Feed"),
            content=ft.Column(
                [
                    self.edit_feed_name,
                    ft.Container(height=16),
                    self.edit_feed_url,
                ],
                tight=True,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self.close_dialog),
                ft.TextButton("Save", on_click=lambda e: self.save_edit_feed(index)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self._page.dialog = dialog
        dialog.open = True
        self._page.update()
    
    def close_dialog(self, e):
        self._page.pop_dialog()
    
    def add_feed_from_dialog(self, e):
        url = self.new_feed_url.value.strip()
        name = self.new_feed_name.value.strip()
        print(f"Adding feed: URL='{url}', Name='{name}'")
        self.add_feed(url, name)
        self.close_dialog(e)
    
    def save_edit_feed(self, index):
        self.edit_feed(index, self.edit_feed_url.value.strip(), self.edit_feed_name.value.strip())
        self.close_dialog(None)
    
    def update_list_view(self):
        print(f"update_list_view called with feed_details: {self.feed_details}")
        self.feeds_list.controls.clear()
        if not self.feed_details:
            print("No feed details, showing empty message")
            self.controls = [self.empty_message]
        else:
            print(f"Adding {len(self.feed_details)} feeds to list")
            for i, feed in enumerate(self.feed_details):
                url = feed['url']
                name = feed.get('name', '')
                print(f"Adding feed {i}: {name} - {url}")
                self.feeds_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(name if name else url),
                        subtitle=ft.Text(url),
                        trailing=ft.Row(
                            [
                                ft.IconButton(
                                    icon="edit",
                                    tooltip="Edit Feed",
                                    data=i,
                                    on_click=self.show_edit_feed_dialog,
                                ),
                                ft.IconButton(
                                    icon="delete",
                                    tooltip="Remove Feed",
                                    data=i,
                                    on_click=lambda e: self.remove_feed(e.control.data),
                                )
                            ],
                            tight=True,
                        ),
                    )
                )
            print(f"Setting controls to feeds_list with {len(self.feeds_list.controls)} items")
            self.controls = [self.feeds_list]
        self._page.update()

    
    def handle_back(self, e):
        if self._page and len(self._page.views) > 1:
            self._page.views.pop()
            self._page.update()
    


def create_feed_management_screen(page, initial_feed_urls=None):
    feed_screen = FeedManagementScreen(page, initial_feed_urls)
    
    # Handle back button
    page.on_route_pop = lambda e: feed_screen.handle_back(e)
    
    # Return a View with appbar and floating action button
    return ft.View(
        route="/feed-management",
        appbar=ft.AppBar(
            title=ft.Text("Manage RSS Feeds"),
            leading=ft.IconButton(
                icon="arrow_back",
                on_click=feed_screen.handle_back,
            ),
        ),
        controls=[feed_screen],
        floating_action_button=ft.FloatingActionButton(
            icon="add",
            tooltip="Add New Feed",
            on_click=feed_screen.show_add_feed_dialog,
        ),
    )
