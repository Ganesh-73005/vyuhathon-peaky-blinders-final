from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class CustomerType(str, Enum):
    REGULAR = "regular"
    OCCASIONAL = "occasional"
    ONE_TIME = "one_time"

class VisitFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class PriceSensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class CreditAging(BaseModel):
    days_0_7: float = 0
    days_8_14: float = 0
    days_15_30: float = 0
    days_30_plus: float = 0

class CreditBehavior(BaseModel):
    total_credit_given: float = 0
    total_repaid: float = 0
    outstanding: float = 0
    avg_repayment_days: int = 0
    credit_limit: float = 500
    risk_score: int = 50  # 0-100, higher is riskier
    aging: CreditAging = Field(default_factory=CreditAging)
    defaulted_count: int = 0
    last_credit_date: Optional[datetime] = None

class PurchasePattern(BaseModel):
    favorite_items: List[str] = []
    avg_basket_size: float = 0
    preferred_time: Optional[str] = None
    price_sensitivity: PriceSensitivity = PriceSensitivity.MEDIUM

class CustomerProfile(Document):
    profile_id: str = Field(default_factory=lambda: f"cust_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    name: str
    phone: Optional[str] = None
    type: CustomerType = CustomerType.OCCASIONAL
    
    first_seen: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)
    visit_frequency: VisitFrequency = VisitFrequency.WEEKLY
    
    total_transactions: int = 0
    lifetime_value: float = 0
    
    credit_behavior: CreditBehavior = Field(default_factory=CreditBehavior)
    purchase_pattern: PurchasePattern = Field(default_factory=PurchasePattern)
    
    behavioral_tags: List[str] = []
    notes: Optional[str] = None
    
    # User reference
    user_id: str
    shop_id: str
    
    class Settings:
        name = "customer_profiles"
        indexes = [
            "profile_id",
            "user_id",
            "shop_id",
            "name",
            "phone",
        ]

