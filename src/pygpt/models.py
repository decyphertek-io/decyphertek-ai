"""
Data models for PyGPT
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import time


@dataclass
class Message:
    """Chat message"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """Create from dictionary"""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", int(time.time() * 1000)),
            metadata=data.get("metadata", {})
        )


@dataclass
class Conversation:
    """Conversation with messages"""
    id: str
    title: str
    messages: List[Message] = field(default_factory=list)
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = field(default_factory=lambda: int(time.time() * 1000))
    metadata: Dict = field(default_factory=dict)
    
    def add_message(self, message: Message):
        """Add message to conversation"""
        self.messages.append(message)
        self.updated_at = int(time.time() * 1000)
    
    def get_messages_for_api(self, include_system: bool = True) -> List[Dict]:
        """Get messages formatted for API"""
        messages = []
        for msg in self.messages:
            if msg.role == "system" and not include_system:
                continue
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        return messages
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Conversation':
        """Create from dictionary"""
        messages = [Message.from_dict(msg) for msg in data.get("messages", [])]
        return cls(
            id=data["id"],
            title=data["title"],
            messages=messages,
            created_at=data.get("created_at", int(time.time() * 1000)),
            updated_at=data.get("updated_at", int(time.time() * 1000)),
            metadata=data.get("metadata", {})
        )

