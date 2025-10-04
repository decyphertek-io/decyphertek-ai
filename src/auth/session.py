"""
Session management for maintaining user state
"""

import time
import secrets
from typing import Optional


class SessionManager:
    """Manages user sessions"""
    
    def __init__(self, timeout_minutes: int = 30):
        """
        Initialize session manager
        
        Args:
            timeout_minutes: Session timeout in minutes
        """
        self.timeout_seconds = timeout_minutes * 60
        self.session_token: Optional[str] = None
        self.username: Optional[str] = None
        self.last_activity: Optional[float] = None
    
    def create_session(self, username: str) -> str:
        """
        Create a new session
        
        Args:
            username: Username for the session
            
        Returns:
            Session token
        """
        self.session_token = secrets.token_urlsafe(32)
        self.username = username
        self.last_activity = time.time()
        return self.session_token
    
    def is_valid(self) -> bool:
        """
        Check if session is valid
        
        Returns:
            True if session is valid and not expired
        """
        if not self.session_token or not self.username or not self.last_activity:
            return False
        
        # Check if session has expired
        if time.time() - self.last_activity > self.timeout_seconds:
            self.destroy_session()
            return False
        
        return True
    
    def update_activity(self):
        """Update last activity timestamp"""
        if self.is_valid():
            self.last_activity = time.time()
    
    def destroy_session(self):
        """Destroy the current session"""
        self.session_token = None
        self.username = None
        self.last_activity = None
    
    def get_username(self) -> Optional[str]:
        """
        Get username from session
        
        Returns:
            Username if session is valid, None otherwise
        """
        if self.is_valid():
            self.update_activity()
            return self.username
        return None
    
    def get_time_remaining(self) -> int:
        """
        Get remaining session time in seconds
        
        Returns:
            Remaining seconds, or 0 if session invalid
        """
        if not self.is_valid():
            return 0
        
        elapsed = time.time() - self.last_activity
        remaining = self.timeout_seconds - elapsed
        return max(0, int(remaining))

