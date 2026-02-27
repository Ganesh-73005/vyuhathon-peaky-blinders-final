from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MemoryType(str, Enum):
    CLARIFICATION = "clarification"
    PATTERN = "pattern"
    PREFERENCE = "preference"
    GOAL = "goal"
    RELATIONSHIP = "relationship"

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class LearnedRule(BaseModel):
    trigger: str
    action: str
    confidence_boost: int = 100

class MemoryRecord(Document):
    memory_id: str = Field(default_factory=lambda: f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    type: MemoryType
    timestamp: datetime = Field(default_factory=datetime.now)
    context: str
    learned_rule: Optional[LearnedRule] = None
    applies_to: List[str] = []
    examples: List[str] = []
    never_ask_again: bool = False
    priority: Priority = Priority.MEDIUM
    metadata: Dict[str, Any] = {}
    
    # User reference
    user_id: str
    shop_id: str
    
    class Settings:
        name = "memory_records"
        indexes = [
            "memory_id",
            "user_id",
            "shop_id",
            "type",
        ]

