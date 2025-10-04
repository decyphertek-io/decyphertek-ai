
from typing import List, Dict, Any, Optional
import subprocess
import sys
from pathlib import Path

class AdminotaurAgent:
    """
    The core agent for interacting with the DecypherTek AI environment.
    It can discover and launch Flet applications from the agent-store.
    """
    def __init__(self, main_class: Any):
        """
        Initializes the Adminotaur agent.
        :param main_class: A reference to the main application class that holds the UI (page) and other state.
        """
        self.main_class = main_class
        self.page = main_class.page
        self.app_store_path = Path("./apps") # Assuming apps are in an 'apps' directory relative to the main app
        self.available_apps = self._discover_flet_apps()
        print(f"[Adminotaur] Initialized. Discovered apps: {list(self.available_apps.keys())}")

    def _discover_flet_apps(self) -> Dict[str, Dict]:
        """Discover available Flet applications from the app store"""
        apps = {}
        if not self.app_store_path.exists():
            print(f"[Adminotaur] App store not found at {self.app_store_path}")
            return apps
        
        for app_dir in self.app_store_path.iterdir():
            if app_dir.is_dir():
                app_name = app_dir.name
                main_py = app_dir / "src" / "main.py"
                
                if main_py.exists():
                    apps[app_name.lower()] = {
                        'name': app_name,
                        'path': app_dir,
                        'main_file': main_py,
                    }
        return apps

    async def chat(self, messages: List[Dict], user_message: str) -> str:
        """
        Main chat method for the Adminotaur agent.
        Determines if a tool needs to be used, like launching an app.
        """
        print("[Adminotaur] Thinking...")
        
        message_lower = user_message.lower()
        app_launch_keywords = ["run", "launch", "start", "open", "execute"]
        
        # Check for app launch intent
        triggered_keyword = next((word for word in app_launch_keywords if word in message_lower), None)
        
        if triggered_keyword:
            # Find which app is being requested
            app_to_launch = None
            for app_name in self.available_apps.keys():
                if app_name in message_lower:
                    app_to_launch = app_name
                    break
            
            if app_to_launch:
                print(f"[Adminotaur] Detected request to launch '{app_to_launch}'")
                # The main_class should have a generic launch method
                if hasattr(self.main_class, "launch_app_by_name"):
                    self.main_class.launch_app_by_name(app_to_launch)
                    return f"I have launched the {self.available_apps[app_to_launch]['name']} application for you."
                else:
                    return f"Sorry, I can't launch applications right now. The main application is missing the 'launch_app_by_name' method."
            
        # Default response if no specific action is taken
        return "I can help with launching applications. What would you like to do?"
