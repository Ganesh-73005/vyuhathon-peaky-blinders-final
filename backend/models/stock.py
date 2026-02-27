from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class VelocityType(str, Enum):
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"

class SpoilageRisk(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class PriceHistory(BaseModel):
    date: datetime
    price: float

class SupplierInfo(BaseModel):
    name: str
    phone: Optional[str] = None
    lead_time_hours: int = 4
    min_order: int = 0
    last_price: float
    price_history: List[PriceHistory] = []

class ConsumptionPattern(BaseModel):
    avg_daily: float = 0
    peak_days: List[str] = []
    peak_hours: List[str] = []
    seasonal_multiplier: float = 1.0

class StockItem(Document):
    item_id: str = Field(default_factory=lambda: f"item_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    name: str
    aliases: List[str] = []
    category: str
    current_stock: float = 0
    unit: str = "piece"
    reorder_point: float = 0
    reorder_quantity: float = 0
    cost_price: float
    selling_price: float
    margin_percent: float = 0
    
    supplier: Optional[SupplierInfo] = None
    consumption_pattern: ConsumptionPattern = Field(default_factory=ConsumptionPattern)
    
    predicted_runout: Optional[datetime] = None
    spoilage_risk: SpoilageRisk = SpoilageRisk.LOW
    shelf_life_hours: Optional[int] = None
    last_restock: Optional[datetime] = None
    dead_stock_alert: bool = False
    velocity: VelocityType = VelocityType.MEDIUM
    
    # User reference
    user_id: str
    shop_id: str
    
    class Settings:
        name = "stock_items"
        indexes = [
            "item_id",
            "user_id",
            "shop_id",
            "name",
            "category",
        ]

