"""
Data models for MCP servers
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json


@dataclass
class MCPServer:
    """MCP Server definition"""
    id: str
    name: str
    description: str
    github_url: str
    python_file: str
    version: str = "1.0.0"
    author: str = ""
    requirements: List[str] = field(default_factory=list)
    config_schema: Dict = field(default_factory=dict)
    mobile_compatible: bool = True
    installed: bool = False
    enabled: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "github_url": self.github_url,
            "python_file": self.python_file,
            "version": self.version,
            "author": self.author,
            "requirements": self.requirements,
            "config_schema": self.config_schema,
            "mobile_compatible": self.mobile_compatible,
            "installed": self.installed,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MCPServer':
        """Create from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            github_url=data["github_url"],
            python_file=data["python_file"],
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            requirements=data.get("requirements", []),
            config_schema=data.get("config_schema", {}),
            mobile_compatible=data.get("mobile_compatible", True),
            installed=data.get("installed", False),
            enabled=data.get("enabled", False)
        )
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MCPServer':
        """Create from JSON string"""
        return cls.from_dict(json.loads(json_str))

