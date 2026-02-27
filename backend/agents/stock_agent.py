from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from models.stock import StockItem, VelocityType, SpoilageRisk
from models.alert import Alert, AlertType, Severity
from config.settings import settings
from loguru import logger

class StockIntelligenceAgent:
    """Agent for intelligent stock tracking and prediction"""
    
    def __init__(self):
        self.runout_warning_hours = settings.STOCK_RUNOUT_WARNING_HOURS
        self.spoilage_warning_percent = settings.SPOILAGE_WARNING_PERCENT
    
    async def update_stock_from_transaction(
        self,
        item_name: str,
        quantity: float,
        transaction_type: str,
        user_id: str,
        shop_id: str
    ) -> Optional[StockItem]:
        """Update stock based on transaction"""
        
        # Find or create stock item
        stock_item = await StockItem.find_one(
            StockItem.user_id == user_id,
            StockItem.shop_id == shop_id,
            StockItem.name == item_name
        )
        
        if not stock_item:
            # Create new stock item with defaults
            stock_item = StockItem(
                name=item_name,
                category="uncategorized",
                current_stock=0,
                cost_price=0,
                selling_price=0,
                user_id=user_id,
                shop_id=shop_id
            )
        
        # Update stock based on transaction type
        if transaction_type in ["sale", "loss", "freebie"]:
            stock_item.current_stock -= quantity
        elif transaction_type == "purchase":
            stock_item.current_stock += quantity
            stock_item.last_restock = datetime.now()
        
        # Ensure stock doesn't go negative
        stock_item.current_stock = max(0, stock_item.current_stock)
        
        await stock_item.save()
        
        # Update consumption patterns
        await self._update_consumption_pattern(stock_item, quantity, transaction_type)
        
        # Check for alerts
        await self._check_stock_alerts(stock_item, user_id, shop_id)
        
        return stock_item
    
    async def _update_consumption_pattern(
        self,
        stock_item: StockItem,
        quantity: float,
        transaction_type: str
    ):
        """Learn consumption patterns from transactions"""
        
        if transaction_type != "sale":
            return
        
        now = datetime.now()
        
        # Update average daily consumption (simple moving average)
        current_avg = stock_item.consumption_pattern.avg_daily
        if current_avg == 0:
            stock_item.consumption_pattern.avg_daily = quantity
        else:
            # Weighted average: 80% old, 20% new
            stock_item.consumption_pattern.avg_daily = current_avg * 0.8 + quantity * 0.2
        
        # Track peak days
        day_name = now.strftime("%A").lower()
        if day_name not in stock_item.consumption_pattern.peak_days:
            # Simple heuristic: if today's sale > avg, mark as peak
            if quantity > stock_item.consumption_pattern.avg_daily * 1.3:
                stock_item.consumption_pattern.peak_days.append(day_name)
        
        # Track peak hours
        hour_range = f"{now.hour:02d}:00-{(now.hour+1):02d}:00"
        if hour_range not in stock_item.consumption_pattern.peak_hours:
            if quantity > stock_item.consumption_pattern.avg_daily * 0.3:  # 30% of daily in one hour
                stock_item.consumption_pattern.peak_hours.append(hour_range)
        
        # Update velocity
        if stock_item.consumption_pattern.avg_daily > 50:
            stock_item.velocity = VelocityType.FAST
        elif stock_item.consumption_pattern.avg_daily > 10:
            stock_item.velocity = VelocityType.MEDIUM
        else:
            stock_item.velocity = VelocityType.SLOW
        
        await stock_item.save()
    
    async def predict_runout(self, stock_item: StockItem) -> Optional[datetime]:
        """Predict when stock will run out"""
        
        if stock_item.consumption_pattern.avg_daily == 0:
            return None
        
        if stock_item.current_stock <= 0:
            return datetime.now()
        
        # Simple prediction: current_stock / avg_daily_consumption
        days_remaining = stock_item.current_stock / stock_item.consumption_pattern.avg_daily
        hours_remaining = days_remaining * 24
        
        predicted_runout = datetime.now() + timedelta(hours=hours_remaining)
        
        # Update stock item
        stock_item.predicted_runout = predicted_runout
        await stock_item.save()
        
        return predicted_runout
    
    async def _check_stock_alerts(
        self,
        stock_item: StockItem,
        user_id: str,
        shop_id: str
    ):
        """Check if stock alerts need to be generated"""
        
        alerts = []
        
        # 1. Runout alert
        predicted_runout = await self.predict_runout(stock_item)
        if predicted_runout:
            hours_until_runout = (predicted_runout - datetime.now()).total_seconds() / 3600
            
            if hours_until_runout < self.runout_warning_hours:
                alert = Alert(
                    type=AlertType.STOCK_RUNOUT,
                    severity=Severity.HIGH if hours_until_runout < 2 else Severity.MEDIUM,
                    title=f"{stock_item.name} running low",
                    message=f"{stock_item.name} will run out in {hours_until_runout:.1f} hours. Reorder now!",
                    message_tamil=f"{stock_item.name} {hours_until_runout:.1f} மணி நேரத்தில் முடியும். இப்போது ஆர்டர் செய்யுங்கள்!",
                    data={
                        "item_name": stock_item.name,
                        "current_stock": stock_item.current_stock,
                        "predicted_runout": predicted_runout.isoformat(),
                        "suggested_order_quantity": stock_item.reorder_quantity or 100
                    },
                    user_id=user_id,
                    shop_id=shop_id
                )
                alerts.append(alert)
        
        # 2. Spoilage alert
        if stock_item.shelf_life_hours and stock_item.last_restock:
            hours_since_restock = (datetime.now() - stock_item.last_restock).total_seconds() / 3600
            shelf_life_percent = (hours_since_restock / stock_item.shelf_life_hours) * 100
            
            if shelf_life_percent > self.spoilage_warning_percent:
                stock_item.spoilage_risk = SpoilageRisk.HIGH
                
                alert = Alert(
                    type=AlertType.SPOILAGE,
                    severity=Severity.HIGH,
                    title=f"{stock_item.name} getting old",
                    message=f"{stock_item.name} is {shelf_life_percent:.0f}% through shelf life. Sell at discount or waste incoming!",
                    message_tamil=f"{stock_item.name} பழையதாகிறது. தள்ளுபடியில் விற்கவும் அல்லது வீணாகும்!",
                    data={
                        "item_name": stock_item.name,
                        "hours_since_restock": hours_since_restock,
                        "shelf_life_hours": stock_item.shelf_life_hours,
                        "shelf_life_percent": shelf_life_percent
                    },
                    user_id=user_id,
                    shop_id=shop_id
                )
                alerts.append(alert)
        
        # 3. Dead stock alert
        if stock_item.last_restock:
            days_since_restock = (datetime.now() - stock_item.last_restock).days
            if days_since_restock > 7 and stock_item.current_stock > 0:
                stock_item.dead_stock_alert = True
                
                alert = Alert(
                    type=AlertType.LEAKAGE,
                    severity=Severity.MEDIUM,
                    title=f"{stock_item.name} not selling",
                    message=f"{stock_item.name} hasn't sold in {days_since_restock} days. Stop reordering!",
                    message_tamil=f"{stock_item.name} {days_since_restock} நாட்களாக விற்கவில்லை. மீண்டும் ஆர்டர் செய்ய வேண்டாம்!",
                    data={
                        "item_name": stock_item.name,
                        "days_since_restock": days_since_restock,
                        "current_stock": stock_item.current_stock
                    },
                    user_id=user_id,
                    shop_id=shop_id
                )
                alerts.append(alert)
        
        # Save all alerts
        for alert in alerts:
            await alert.save()
        
        await stock_item.save()
    
    async def get_stock_summary(self, user_id: str, shop_id: str) -> Dict[str, Any]:
        """Get overall stock summary"""
        
        all_items = await StockItem.find(
            StockItem.user_id == user_id,
            StockItem.shop_id == shop_id
        ).to_list()
        
        low_stock = [item for item in all_items if item.current_stock < item.reorder_point]
        dead_stock = [item for item in all_items if item.dead_stock_alert]
        high_risk_spoilage = [item for item in all_items if item.spoilage_risk == SpoilageRisk.HIGH]
        
        return {
            "total_items": len(all_items),
            "low_stock_count": len(low_stock),
            "dead_stock_count": len(dead_stock),
            "spoilage_risk_count": len(high_risk_spoilage),
            "low_stock_items": [item.name for item in low_stock],
            "dead_stock_items": [item.name for item in dead_stock],
            "total_stock_value": sum(item.current_stock * item.cost_price for item in all_items)
        }

