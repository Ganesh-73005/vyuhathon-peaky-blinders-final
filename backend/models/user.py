from beanie import Document
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class BusinessType(str, Enum):
    KIRANA = "kirana"
    BAKERY = "bakery"
    HOTEL = "hotel"
    SUPERMARKET = "supermarket"
    RESTAURANT = "restaurant"
    PHARMACY = "pharmacy"
    GENERAL_STORE = "general_store"
    VEGETABLE_SHOP = "vegetable_shop"
    FRUIT_SHOP = "fruit_shop"
    OTHER = "other"

class ShopLocation(BaseModel):
    latitude: float
    longitude: float
    address: str
    city: str
    state: str = "Tamil Nadu"
    pincode: Optional[str] = None

class User(Document):
    user_id: str = Field(default_factory=lambda: f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    email: EmailStr
    password_hash: str
    shop_name: str
    business_type: BusinessType = BusinessType.KIRANA
    location: Optional[ShopLocation] = None
    phone: Optional[str] = None
    language_preference: str = "tamil"
    voice_enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    class Settings:
        name = "users"
        indexes = [
            "user_id",
            "email",
        ]
