from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.stock import StockItem, VelocityType, SpoilageRisk

router = APIRouter()

class StockAddRequest(BaseModel):
    name: str
    category: str
    quantity: float
    unit: str = "piece"
    cost_price: float
    selling_price: float
    user_id: str = "demo_user"
    shop_id: str = "demo_shop"

class StockUpdateRequest(BaseModel):
    quantity_change: float
    reason: str = "manual_adjustment"

@router.post("/add")
async def add_stock_item(request: StockAddRequest):
    """Add a new stock item or update existing"""
    try:
        # Check if item exists (case-insensitive search)
        all_items = await StockItem.find(
            StockItem.user_id == request.user_id,
            StockItem.shop_id == request.shop_id
        ).to_list()
        
        existing = None
        for item in all_items:
            if item.name.lower() == request.name.lower():
                existing = item
                break
        
        if existing:
            # Update existing stock
            existing.current_stock += request.quantity
            existing.cost_price = request.cost_price
            existing.selling_price = request.selling_price
            existing.margin_percent = ((request.selling_price - request.cost_price) / request.cost_price * 100) if request.cost_price > 0 else 0
            existing.last_restock = datetime.now()
            await existing.save()
            
            return {
                "success": True,
                "action": "updated",
                "item_id": existing.item_id,
                "current_stock": existing.current_stock
            }
        else:
            # Create new stock item
            margin = ((request.selling_price - request.cost_price) / request.cost_price * 100) if request.cost_price > 0 else 0
            
            stock_item = StockItem(
                name=request.name,
                category=request.category,
                current_stock=request.quantity,
                unit=request.unit,
                cost_price=request.cost_price,
                selling_price=request.selling_price,
                margin_percent=margin,
                reorder_point=request.quantity * 0.2,
                reorder_quantity=request.quantity,
                last_restock=datetime.now(),
                user_id=request.user_id,
                shop_id=request.shop_id
            )
            await stock_item.save()
            
            return {
                "success": True,
                "action": "created",
                "item_id": stock_item.item_id,
                "current_stock": stock_item.current_stock
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{item_id}")
async def update_stock(item_id: str, request: StockUpdateRequest):
    """Update stock quantity"""
    try:
        item = await StockItem.find_one(StockItem.item_id == item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Stock item not found")
        
        item.current_stock += request.quantity_change
        if item.current_stock < 0:
            item.current_stock = 0
        
        await item.save()
        
        return {
            "success": True,
            "item_id": item_id,
            "current_stock": item.current_stock,
            "quantity_change": request.quantity_change
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{item_id}")
async def delete_stock(item_id: str):
    """Delete a stock item"""
    try:
        item = await StockItem.find_one(StockItem.item_id == item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Stock item not found")
        
        await item.delete()
        
        return {"success": True, "deleted": item_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
@router.get("/")
async def get_stock(
    user_id: str = "demo_user",
    shop_id: str = "demo_shop"
):
    """Get all stock items"""
    
    try:
        items = await StockItem.find(
            StockItem.user_id == user_id,
            StockItem.shop_id == shop_id
        ).to_list()
        
        return {
            "count": len(items),
            "items": [
                {
                    "item_id": item.item_id,
                    "name": item.name,
                    "category": item.category,
                    "current_stock": item.current_stock,
                    "unit": item.unit,
                    "cost_price": item.cost_price,
                    "selling_price": item.selling_price,
                    "margin_percent": item.margin_percent,
                    "predicted_runout": item.predicted_runout.isoformat() if item.predicted_runout else None,
                    "velocity": item.velocity,
                    "dead_stock_alert": item.dead_stock_alert
                }
                for item in items
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_stock_summary(
    user_id: str = "demo_user",
    shop_id: str = "demo_shop",
    request: Request = None
):
    """Get stock summary with alerts"""
    
    try:
        stock_agent = request.app.state.orchestrator.stock_agent
        summary = await stock_agent.get_stock_summary(user_id, shop_id)
        
        return summary
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

