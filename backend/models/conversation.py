from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class MessageType(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    ALERT = "alert"
    INSIGHT = "insight"

class Message(BaseModel):
    message_id: str = Field(default_factory=lambda: f"msg_{datetime.now().strftime('%Y%m%d%H%M%S%f')}")
    role: MessageRole
    type: MessageType = MessageType.TEXT
    content: str
    content_tamil: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}
    audio_url: Optional[str] = None
    image_url: Optional[str] = None

class Conversation(Document):
    conversation_id: str = Field(default_factory=lambda: f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    messages: List[Message] = []
    started_at: datetime = Field(default_factory=datetime.now)
    last_message_at: datetime = Field(default_factory=datetime.now)
    active: bool = True
    
    # Context tracking
    current_topic: Optional[str] = None
    pending_clarification: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # User reference
    user_id: str
    shop_id: str
    
    class Settings:
        name = "conversations"
        indexes = [
            "conversation_id",
            "user_id",
            "shop_id",
            "started_at",
        ]

