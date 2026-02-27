from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from models.transaction import Transaction, TransactionItem, TransactionType, PaymentMode, PersonInfo
from models.stock import StockItem
from loguru import logger

router = APIRouter()

class ManualTransactionItem(BaseModel):
    item_name: str
    quantity: float
    unit_price: float
    unit: str = "piece"

class ManualTransactionRequest(BaseModel):
    type: str = "sale"
    items: List[ManualTransactionItem]
    payment_mode: str = "cash"
    person_name: Optional[str] = None
    notes: Optional[str] = None
    user_id: str = "demo_user"
    shop_id: str = "demo_shop"

@router.post("/manual")
async def create_manual_transaction(request: ManualTransactionRequest):
    """Create a manual transaction entry with stock verification"""
    try:
        # Calculate total
        total_amount = sum(item.quantity * item.unit_price for item in request.items)

        # Map string type to enum
        type_mapping = {
            "sale": TransactionType.SALE,
            "purchase": TransactionType.PURCHASE,
            "expense": TransactionType.EXPENSE,
            "credit": TransactionType.CREDIT,
            "personal": TransactionType.PERSONAL,
            "freebie": TransactionType.FREEBIE,
            "loss": TransactionType.LOSS
        }

        payment_mapping = {
            "cash": PaymentMode.CASH,
            "upi": PaymentMode.UPI,
            "credit": PaymentMode.CREDIT,
            "card": PaymentMode.CARD
        }

        transaction_type = type_mapping.get(request.type.lower(), TransactionType.SALE)

        # For sales, verify stock availability
        if transaction_type == TransactionType.SALE:
            stock_issues = []

            for item in request.items:
                # Find stock item (case-insensitive)
                all_stock = await StockItem.find(
                    StockItem.user_id == request.user_id,
                    StockItem.shop_id == request.shop_id
                ).to_list()

                stock_item = None
                for stock in all_stock:
                    if stock.name.lower() == item.item_name.lower():
                        stock_item = stock
                        break

                if not stock_item:
                    stock_issues.append(f"{item.item_name} not found in inventory")
                elif stock_item.current_stock < item.quantity:
                    stock_issues.append(
                        f"{item.item_name}: only {stock_item.current_stock} {stock_item.unit} available, "
                        f"but {item.quantity} requested"
                    )

            if stock_issues:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Insufficient stock",
                        "issues": stock_issues
                    }
                )

        # Create transaction
        transaction = Transaction(
            type=transaction_type,
            items=[
                TransactionItem(
                    item_name=item.item_name,
                    normalized_name=item.item_name.lower(),
                    quantity=item.quantity,
                    unit=item.unit,
                    unit_price=item.unit_price,
                    total=item.quantity * item.unit_price
                )
                for item in request.items
            ],
            total_amount=total_amount,
            payment_mode=payment_mapping.get(request.payment_mode.lower(), PaymentMode.CASH),
            person=PersonInfo(name=request.person_name) if request.person_name else None,
            confidence_score=100,
            source="manual",
            original_input=f"Manual entry: {request.notes or 'No notes'}",
            language="english",
            user_id=request.user_id,
            shop_id=request.shop_id
        )

        await transaction.save()

        # Update stock for sales and purchases
        if transaction_type == TransactionType.SALE:
            for item in request.items:
                # Find and update stock
                all_stock = await StockItem.find(
                    StockItem.user_id == request.user_id,
                    StockItem.shop_id == request.shop_id
                ).to_list()

                for stock in all_stock:
                    if stock.name.lower() == item.item_name.lower():
                        stock.current_stock -= item.quantity
                        await stock.save()
                        logger.info(f"Updated stock for {stock.name}: -{item.quantity}, new stock: {stock.current_stock}")
                        break

        elif transaction_type == TransactionType.PURCHASE:
            for item in request.items:
                # Find or create stock item
                all_stock = await StockItem.find(
                    StockItem.user_id == request.user_id,
                    StockItem.shop_id == request.shop_id
                ).to_list()

                stock_item = None
                for stock in all_stock:
                    if stock.name.lower() == item.item_name.lower():
                        stock_item = stock
                        break

                if stock_item:
                    stock_item.current_stock += item.quantity
                    stock_item.last_restock = datetime.now()
                    await stock_item.save()
                    logger.info(f"Updated stock for {stock_item.name}: +{item.quantity}, new stock: {stock_item.current_stock}")
                else:
                    # Create new stock item
                    new_stock = StockItem(
                        name=item.item_name,
                        category="general",
                        current_stock=item.quantity,
                        unit=item.unit,
                        cost_price=item.unit_price,
                        selling_price=item.unit_price * 1.25,  # 25% markup
                        margin_percent=25,
                        reorder_point=item.quantity * 0.2,
                        reorder_quantity=item.quantity,
                        last_restock=datetime.now(),
                        user_id=request.user_id,
                        shop_id=request.shop_id
                    )
                    await new_stock.save()
                    logger.info(f"Created new stock item: {new_stock.name} with {new_stock.current_stock} units")

        return {
            "success": True,
            "transaction_id": transaction.transaction_id,
            "total_amount": total_amount,
            "type": request.type,
            "items_count": len(request.items)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transaction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_transactions(
    user_id: str = "demo_user",
    shop_id: str = "demo_shop",
    days: int = Query(7, description="Number of days to fetch"),
    transaction_type: Optional[str] = None
):
    """Get recent transactions"""
    
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        query = Transaction.find(
            Transaction.user_id == user_id,
            Transaction.shop_id == shop_id,
            Transaction.timestamp >= start_date
        )
        
        if transaction_type:
            query = query.find(Transaction.type == transaction_type)
        
        transactions = await query.sort(-Transaction.timestamp).to_list()
        
        return {
            "count": len(transactions),
            "transactions": [
                {
                    "transaction_id": t.transaction_id,
                    "timestamp": t.timestamp.isoformat(),
                    "type": t.type,
                    "total_amount": t.total_amount,
                    "items": [
                        {
                            "item_name": item.item_name,
                            "quantity": item.quantity,
                            "unit_price": item.unit_price,
                            "total": item.total
                        }
                        for item in t.items
                    ],
                    "payment_mode": t.payment_mode,
                    "person": t.person.dict() if t.person else None,
                    "original_input": t.original_input
                }
                for t in transactions
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str):
    """Get specific transaction"""
    
    try:
        transaction = await Transaction.find_one(
            Transaction.transaction_id == transaction_id
        )
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return transaction.dict()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

