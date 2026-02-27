from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import io
from loguru import logger

router = APIRouter()

class PDFConfirmRequest(BaseModel):
    bill_type: str  # "sales" or "stock" or "purchase"
    data: Dict[str, Any]
    user_id: str = "demo_user"
    shop_id: str = "demo_shop"

async def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF using PyMuPDF or fallback"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except ImportError:
        logger.warning("PyMuPDF not installed, trying alternative")
        # Fallback: return placeholder
        return "PDF text extraction requires PyMuPDF library"
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to extract PDF text: {str(e)}")

@router.post("/parse")
async def parse_pdf(
    file: UploadFile = File(...),
    user_id: str = Form("demo_user"),
    shop_id: str = Form("demo_shop"),
    language: str = Form("english"),
    request: Request = None
):
    """
    Upload and parse a PDF bill/invoice.
    Returns extracted data and asks for confirmation on bill type.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read file content
        content = await file.read()
        
        # Extract text from PDF
        extracted_text = await extract_text_from_pdf(content)
        
        if not extracted_text or len(extracted_text) < 10:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Use LLM to analyze the bill
        groq_service = request.app.state.groq_service
        
        analysis_prompt = f"""Analyze this bill/invoice text and extract structured data:

{extracted_text[:3000]}

Return JSON:
{{
    "detected_type": "sales_bill" | "purchase_bill" | "expense_bill" | "unknown",
    "confidence": 0-100,
    "vendor_name": "...",
    "bill_date": "...",
    "bill_number": "...",
    "items": [
        {{"item_name": "...", "quantity": ..., "unit_price": ..., "total": ...}}
    ],
    "subtotal": ...,
    "tax": ...,
    "grand_total": ...,
    "needs_clarification": true/false,
    "clarification_question": "Is this a sales bill or purchase bill?"
}}"""
        
        messages = [
            {"role": "system", "content": "You are an expert at parsing Indian bills and invoices."},
            {"role": "user", "content": analysis_prompt}
        ]
        
        response = await groq_service.chat_completion(messages, json_mode=True, temperature=0.2)
        
        import json
        try:
            result = json.loads(response)
        except:
            result = {
                "detected_type": "unknown",
                "items": [],
                "needs_clarification": True,
                "clarification_question": "Is this a sales bill (items you sold) or purchase bill (items you bought for stock)?"
            }
        
        # Always ask for confirmation on bill type
        result["needs_type_confirmation"] = True
        result["extracted_text_preview"] = extracted_text[:500]
        
        return {
            "success": True,
            "filename": file.filename,
            "analysis": result,
            "message": "Please confirm: Is this a SALES bill (goods you sold) or STOCK/PURCHASE bill (goods you bought)?",
            "message_tamil": "உறுதிப்படுத்துங்கள்: இது விற்பனை பில் (விற்ற பொருட்கள்) அல்லது கொள்முதல் பில் (வாங்கிய பொருட்கள்)?"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF parsing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/confirm")
async def confirm_pdf_data(
    request_data: PDFConfirmRequest,
    request: Request = None
):
    """Confirm and save the parsed PDF data"""
    from models.transaction import Transaction, TransactionItem, TransactionType, PaymentMode
    from models.stock import StockItem
    from datetime import datetime

    try:
        bill_type = request_data.bill_type
        data = request_data.data
        user_id = request_data.user_id
        shop_id = request_data.shop_id

        logger.info(f"PDF confirm request: bill_type={bill_type}, user_id={user_id}, items={len(data.get('items', []))}")

        items = data.get("items", [])
        
        if bill_type == "stock" or bill_type == "purchase":
            # Add to stock
            for item in items:
                stock_item = await StockItem.find_one(
                    StockItem.name == item.get("item_name"),
                    StockItem.user_id == user_id
                )
                
                if stock_item:
                    stock_item.current_stock += item.get("quantity", 0)
                    stock_item.cost_price = item.get("unit_price", stock_item.cost_price)
                    await stock_item.save()
                else:
                    new_item = StockItem(
                        name=item.get("item_name"),
                        category="general",
                        current_stock=item.get("quantity", 0),
                        unit="piece",
                        cost_price=item.get("unit_price", 0),
                        selling_price=item.get("unit_price", 0) * 1.2,  # 20% markup
                        user_id=user_id,
                        shop_id=shop_id
                    )
                    await new_item.save()
            
            return {
                "success": True,
                "type": "stock",
                "items_added": len(items),
                "message": f"Added {len(items)} items to stock"
            }
        else:
            # Create sales transaction
            transaction = Transaction(
                type=TransactionType.SALE,
                items=[
                    TransactionItem(
                        item_name=item.get("item_name", "item"),
                        normalized_name=item.get("item_name", "item").lower(),
                        quantity=item.get("quantity", 1),
                        unit="piece",
                        unit_price=item.get("unit_price", 0),
                        total=item.get("total", item.get("quantity", 1) * item.get("unit_price", 0))
                    )
                    for item in items
                ],
                total_amount=data.get("grand_total", sum(i.get("total", 0) for i in items)),
                payment_mode=PaymentMode.CASH,
                confidence_score=100,
                source="pdf",
                original_input=f"PDF Bill: {data.get('bill_number', 'Unknown')}",
                language="english",
                user_id=user_id,
                shop_id=shop_id
            )
            await transaction.save()
            
            return {
                "success": True,
                "type": "sales",
                "transaction_id": transaction.transaction_id,
                "total": transaction.total_amount,
                "message": f"Recorded sale of ₹{transaction.total_amount}"
            }
    
    except Exception as e:
        logger.error(f"PDF confirmation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
