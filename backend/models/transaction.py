from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class TransactionType(str, Enum):
    SALE = "sale"
    PURCHASE = "purchase"
    EXPENSE = "expense"
    LOSS = "loss"
    CREDIT = "credit"
    PERSONAL = "personal"
    FREEBIE = "freebie"

class PaymentMode(str, Enum):
    CASH = "cash"
    UPI = "upi"
    CREDIT = "credit"
    CARD = "card"

class TransactionItem(BaseModel):
    item_name: str
    normalized_name: str
    quantity: float
    unit: str = "piece"
    unit_price: float
    total: float
    cost_price: Optional[float] = None
    margin: Optional[float] = None

class PersonInfo(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    profile_id: Optional[str] = None

class Transaction(Document):
    transaction_id: str = Field(default_factory=lambda: f"txn_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    timestamp: datetime = Field(default_factory=datetime.now)
    type: TransactionType
    items: List[TransactionItem] = []
    total_amount: float
    payment_mode: PaymentMode = PaymentMode.CASH
    person: Optional[PersonInfo] = None
    confidence_score: int = 100
    source: str = "text"  # voice, text, image, pdf
    original_input: str
    language: str = "tamil"
    location: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    
    # User reference
    user_id: str
    shop_id: str
    
    class Settings:
        name = "transactions"
        indexes = [
            "transaction_id",
            "user_id",
            "shop_id",
            "timestamp",
            "type",
        ]

