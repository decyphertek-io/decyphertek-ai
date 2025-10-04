"""
Chat Session Manager
Handles saving, loading, and managing chat conversations
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import uuid


class ChatSessionManager:
    """Manages chat sessions with persistence"""
    
    def __init__(self, storage_dir: str):
        """
        Initialize chat session manager
        
        Args:
            storage_dir: Directory to store chat sessions
        """
        self.storage_dir = Path(storage_dir)
        self.sessions_dir = self.storage_dir / "chat_sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session
        self.current_session_id = None
        self.current_messages = []
    
    def create_new_session(self, title: Optional[str] = None) -> str:
        """
        Create a new chat session
        
        Args:
            title: Optional title for the session
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        self.current_messages = []
        
        # Create session metadata
        session_data = {
            "id": session_id,
            "title": title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": []
        }
        
        # Save session
        self._save_session(session_id, session_data)
        
        print(f"[ChatSessions] Created new session: {session_id}")
        return session_id
    
    def add_message(self, role: str, content: str):
        """
        Add a message to the current session
        
        Args:
            role: Message role (user/assistant)
            content: Message content
        """
        if not self.current_session_id:
            # Create new session if none exists
            self.create_new_session()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.current_messages.append(message)
        
        # Save session
        self._update_session()
    
    def load_session(self, session_id: str) -> List[Dict]:
        """
        Load a chat session
        
        Args:
            session_id: Session ID to load
            
        Returns:
            List of messages
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            print(f"[ChatSessions] Session not found: {session_id}")
            return []
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            self.current_session_id = session_id
            self.current_messages = session_data.get('messages', [])
            
            print(f"[ChatSessions] Loaded session: {session_id}")
            return self.current_messages
            
        except Exception as e:
            print(f"[ChatSessions] Error loading session: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if successful
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        
        try:
            if session_file.exists():
                session_file.unlink()
                
                # If deleting current session, reset
                if session_id == self.current_session_id:
                    self.current_session_id = None
                    self.current_messages = []
                
                print(f"[ChatSessions] Deleted session: {session_id}")
                return True
            return False
            
        except Exception as e:
            print(f"[ChatSessions] Error deleting session: {e}")
            return False
    
    def list_sessions(self) -> List[Dict]:
        """
        List all saved chat sessions
        
        Returns:
            List of session metadata (sorted by updated_at, newest first)
        """
        sessions = []
        
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    
                    # Add summary info
                    sessions.append({
                        "id": session_data["id"],
                        "title": session_data["title"],
                        "created_at": session_data["created_at"],
                        "updated_at": session_data["updated_at"],
                        "message_count": len(session_data.get("messages", []))
                    })
            except Exception as e:
                print(f"[ChatSessions] Error reading session {session_file}: {e}")
        
        # Sort by updated_at (newest first)
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return sessions
    
    def update_session_title(self, session_id: str, new_title: str) -> bool:
        """
        Update session title
        
        Args:
            session_id: Session ID
            new_title: New title
            
        Returns:
            True if successful
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        
        try:
            if session_file.exists():
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                session_data["title"] = new_title
                session_data["updated_at"] = datetime.now().isoformat()
                
                with open(session_file, 'w') as f:
                    json.dump(session_data, f, indent=2)
                
                print(f"[ChatSessions] Updated title for session: {session_id}")
                return True
            return False
            
        except Exception as e:
            print(f"[ChatSessions] Error updating title: {e}")
            return False
    
    def get_current_messages(self) -> List[Dict]:
        """Get messages from current session"""
        return self.current_messages
    
    def _save_session(self, session_id: str, session_data: Dict):
        """Save session to disk"""
        session_file = self.sessions_dir / f"{session_id}.json"
        
        try:
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            print(f"[ChatSessions] Error saving session: {e}")
    
    def _update_session(self):
        """Update current session on disk"""
        if not self.current_session_id:
            return
        
        session_file = self.sessions_dir / f"{self.current_session_id}.json"
        
        try:
            # Load existing session
            if session_file.exists():
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
            else:
                # Create new session data
                session_data = {
                    "id": self.current_session_id,
                    "title": f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "created_at": datetime.now().isoformat(),
                }
            
            # Update messages and timestamp
            session_data["messages"] = self.current_messages
            session_data["updated_at"] = datetime.now().isoformat()
            
            # Auto-generate title from first message if needed
            if len(self.current_messages) == 1 and session_data["title"].startswith("Chat "):
                first_msg = self.current_messages[0]["content"]
                session_data["title"] = first_msg[:50] + ("..." if len(first_msg) > 50 else "")
            
            # Save
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
        except Exception as e:
            print(f"[ChatSessions] Error updating session: {e}")

