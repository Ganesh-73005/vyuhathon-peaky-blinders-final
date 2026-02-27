from typing import Dict, Any, Optional, List
from services import GroqService, WhisperService, CartesiaService
from agents.nlp_agent import NLPExtractionAgent
from agents.stock_agent import StockIntelligenceAgent
from agents.leakage_agent import LeakageDetectiveAgent
from models.conversation import Conversation, Message, MessageRole, MessageType
from models.transaction import Transaction, TransactionType, TransactionItem, PersonInfo, PaymentMode
from models.stock import StockItem
from loguru import logger
from datetime import datetime
import json

class MasterOrchestrator:
    """Central brain coordinating all specialist agents with enhanced memory"""
    
    def __init__(
        self,
        groq_service: GroqService,
        whisper_service: WhisperService,
        cartesia_service: CartesiaService
    ):
        self.groq = groq_service
        self.whisper = whisper_service
        self.cartesia = cartesia_service
        
        # Initialize specialist agents
        self.nlp_agent = NLPExtractionAgent(groq_service)
        self.stock_agent = StockIntelligenceAgent()
        self.leakage_agent = LeakageDetectiveAgent()
        
        # Pending transactions awaiting confirmation
        self.pending_confirmations = {}
    
    async def process_message(
        self,
        user_input: str,
        user_id: str,
        shop_id: str,
        input_type: str = "text",
        language: str = "tamil",
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Main entry point with enhanced memory and context"""

        # Get or create conversation
        conversation = await self._get_or_create_conversation(
            conversation_id, user_id, shop_id
        )

        # Build rich conversation context
        context = await self._build_conversation_context(conversation, user_id, shop_id)

        # Check if this is the first message in a new conversation
        is_first_message = len(conversation.messages) == 0

        # Add user message
        user_message = Message(
            role=MessageRole.USER,
            type=MessageType.TEXT if input_type == "text" else MessageType.VOICE,
            content=user_input
        )
        conversation.messages.append(user_message)

        # Use LLM to understand intent with FULL context
        response_data = await self._process_with_context(
            user_input, language, user_id, shop_id, conversation, context
        )

        # Prepend greeting if first message
        if is_first_message:
            greeting_en, greeting_ta = await self._generate_greeting(context, language)
            logger.info(f"First message - adding greeting: {greeting_en[:80]}...")
            response_data["response"] = greeting_en + "\n\n" + response_data["response"]
            if response_data.get("response_tamil"):
                response_data["response_tamil"] = greeting_ta + "\n\n" + response_data["response_tamil"]

        # Generate voice response if needed
        audio_url = None
        if response_data.get("response_tamil"):
            prefer_tamil = (language == "tamil")
            logger.info(f"Generating voice response: language={language}, prefer_tamil={prefer_tamil}")
            audio_url = await self.cartesia.generate_voice_response(
                response_data["response"],
                response_data["response_tamil"],
                prefer_tamil=prefer_tamil
            )
            logger.info(f"Voice audio generated: {audio_url}")
        
        # Add assistant message
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            type=MessageType.TEXT,
            content=response_data["response"],
            content_tamil=response_data.get("response_tamil"),
            audio_url=audio_url,
            metadata=response_data.get("metadata", {})
        )
        conversation.messages.append(assistant_message)
        conversation.last_message_at = datetime.now()
        
        # Store context for next turn
        if response_data.get("pending_data"):
            conversation.metadata = conversation.metadata or {}
            conversation.metadata["pending_data"] = response_data["pending_data"]
            # Clear clarification if we're now waiting for confirmation
            if response_data["pending_data"].get("awaiting_confirmation"):
                conversation.pending_clarification = None
            else:
                conversation.pending_clarification = response_data.get("clarification_type")
        elif response_data.get("clear_pending"):
            # Clear pending data after successful save
            conversation.metadata = conversation.metadata or {}
            conversation.metadata["pending_data"] = None
            conversation.pending_clarification = None
        
        await conversation.save()
        
        return {
            **response_data,
            "audio_url": audio_url,
            "conversation_id": str(conversation.id)
        }

    async def _generate_greeting(self, context: Dict[str, Any], language: str) -> tuple:
        """Generate a personalized greeting with business context"""

        user_info = context.get("user_info", {})
        business_stats = context.get("business_stats", {})
        low_stock = context.get("low_stock_items", [])

        shop_name = user_info.get("shop_name", "your shop")
        today_revenue = business_stats.get("today_revenue", 0)
        today_txns = business_stats.get("today_transactions", 0)
        total_items = business_stats.get("total_stock_items", 0)
        low_stock_count = business_stats.get("low_stock_count", 0)

        # Build greeting
        greeting_en = f"Welcome to {shop_name}! "
        greeting_ta = f"{shop_name} க்கு வரவேற்கிறோம்! "

        # Add today's summary
        if today_txns > 0:
            greeting_en += f"Today you've made {today_txns} transaction(s) totaling ₹{today_revenue:.2f}. "
            greeting_ta += f"இன்று நீங்கள் {today_txns} பரிவர்த்தனைகள் செய்துள்ளீர்கள், மொத்தம் ₹{today_revenue:.2f}. "
        else:
            greeting_en += "No transactions yet today. "
            greeting_ta += "இன்று இன்னும் பரிவர்த்தனைகள் இல்லை. "

        # Add stock info
        if total_items > 0:
            greeting_en += f"You have {total_items} items in stock"
            greeting_ta += f"உங்களிடம் {total_items} பொருட்கள் உள்ளன"

            if low_stock_count > 0:
                greeting_en += f" (⚠️ {low_stock_count} running low). "
                greeting_ta += f" (⚠️ {low_stock_count} குறைந்து வருகின்றன). "
            else:
                greeting_en += ". "
                greeting_ta += ". "
        else:
            greeting_en += "You don't have any stock items yet. You can add stock by saying 'add stock' or record sales directly. "
            greeting_ta += "உங்களிடம் இன்னும் சரக்கு பொருட்கள் இல்லை. 'சரக்கு சேர்' என்று சொல்லி சேர்க்கலாம் அல்லது நேரடியாக விற்பனையை பதிவு செய்யலாம். "

        greeting_en += "How can I help you today?"
        greeting_ta += "இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?"

        return greeting_en, greeting_ta

    async def _build_conversation_context(
        self,
        conversation: Conversation,
        user_id: str,
        shop_id: str
    ) -> Dict[str, Any]:
        """Build rich context from conversation history, database, and user profile"""

        # Get user/business information
        from models.user import User
        user = await User.find_one(User.user_id == user_id)

        if user:
            logger.info(f"Found user: {user.shop_name} ({user.business_type.value})")
        else:
            logger.warning(f"User not found for user_id: {user_id}")

        # Get last 10 messages for context
        recent_messages = conversation.messages[-10:] if conversation.messages else []

        # Get recent transactions for reference
        recent_txns = await Transaction.find(
            Transaction.user_id == user_id,
            Transaction.shop_id == shop_id
        ).sort(-Transaction.timestamp).limit(5).to_list()

        logger.info(f"Found {len(recent_txns)} recent transactions")

        # Get stock summary - try to get ALL stock items first
        stock_items = await StockItem.find(
            StockItem.user_id == user_id,
            StockItem.shop_id == shop_id
        ).to_list()

        logger.info(f"Found {len(stock_items)} stock items for user_id={user_id}, shop_id={shop_id}")

        # Calculate business stats
        from datetime import datetime, timedelta
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Today's sales
        today_sales = await Transaction.find(
            Transaction.user_id == user_id,
            Transaction.shop_id == shop_id,
            Transaction.type == TransactionType.SALE,
            Transaction.timestamp >= today
        ).to_list()

        today_revenue = sum(t.total_amount for t in today_sales)
        today_transactions_count = len(today_sales)

        # Total stock value
        total_stock_value = sum(s.current_stock * s.selling_price for s in stock_items)

        # Low stock items
        low_stock_items = [s for s in stock_items if s.current_stock < s.reorder_point and s.reorder_point > 0]

        # Build context string
        context = {
            "user_info": {
                "shop_name": user.shop_name if user else "Your Shop",
                "business_type": user.business_type.value if user else "kirana",
                "location": user.location.city if user and user.location else None,
                "phone": user.phone if user else None
            },
            "business_stats": {
                "today_revenue": today_revenue,
                "today_transactions": today_transactions_count,
                "total_stock_value": total_stock_value,
                "low_stock_count": len(low_stock_items),
                "total_stock_items": len(stock_items)
            },
            "conversation_history": [
                {"role": msg.role.value, "content": msg.content, "metadata": msg.metadata}
                for msg in recent_messages
            ],
            "pending_data": conversation.metadata.get("pending_data") if conversation.metadata else None,
            "pending_clarification": conversation.pending_clarification,
            "recent_transactions": [
                {
                    "type": t.type.value,
                    "items": [{"name": i.item_name, "qty": i.quantity, "price": i.unit_price} for i in t.items],
                    "total": t.total_amount,
                    "time": t.timestamp.strftime("%H:%M")
                }
                for t in recent_txns
            ],
            "stock_items": [
                {"name": s.name, "stock": s.current_stock, "price": s.selling_price, "unit": s.unit}
                for s in stock_items
            ],
            "low_stock_items": [
                {"name": s.name, "stock": s.current_stock, "reorder_point": s.reorder_point}
                for s in low_stock_items
            ]
        }

        # Log context summary
        logger.info(f"Context built - Shop: {context['user_info']['shop_name']}, "
                   f"Stock items: {len(stock_items)}, "
                   f"Today's revenue: ₹{today_revenue}, "
                   f"Low stock: {len(low_stock_items)}")

        return context
    
    async def _process_with_context(
        self,
        user_input: str,
        language: str,
        user_id: str,
        shop_id: str,
        conversation: Conversation,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process message with full context awareness"""
        
        logger.info(f"Processing: '{user_input}' | pending_data: {context.get('pending_data')} | pending_clarification: {context.get('pending_clarification')}")
        
        # Check if this is a confirmation response
        if context.get("pending_clarification"):
            logger.info("Handling clarification response")
            return await self._handle_clarification_response(
                user_input, language, user_id, shop_id, context
            )
        
        # Check if this is a confirmation (approve/reject)
        if context.get("pending_data") and context["pending_data"].get("awaiting_confirmation"):
            lower_input = user_input.lower()
            logger.info(f"Checking confirmation - input: {lower_input}")
            if any(word in lower_input for word in ["yes", "confirm", "ok", "சரி", "ஆம்", "approve"]):
                logger.info("Confirming pending data")
                return await self._confirm_pending_data(user_id, shop_id, context, language)
            elif any(word in lower_input for word in ["no", "cancel", "reject", "வேண்டாம்", "இல்லை"]):
                return await self._reject_pending_data(language)
        
        # Use intelligent LLM to understand and respond
        system_prompt = self._build_system_prompt(context, language)
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history
        for msg in context["conversation_history"][-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": user_input})
        
        # Get LLM response with structured output
        response = await self.groq.chat_completion(
            messages,
            json_mode=True,
            temperature=0.3,
            max_tokens=1024
        )
        
        try:
            result = json.loads(response)
        except:
            result = {"action": "general_response", "response": response}
        
        return await self._handle_llm_result(result, user_input, language, user_id, shop_id, context)
    
    def _build_system_prompt(self, context: Dict[str, Any], language: str) -> str:
        """Build comprehensive system prompt with context"""

        # Business context
        user_info = context.get("user_info", {})
        business_stats = context.get("business_stats", {})

        logger.info(f"Building system prompt with: {len(context.get('stock_items', []))} stock items, "
                   f"{len(context.get('recent_transactions', []))} recent transactions")

        business_str = f"""
BUSINESS INFORMATION:
- Shop Name: {user_info.get('shop_name', 'Your Shop')}
- Business Type: {user_info.get('business_type', 'kirana').title()}
- Location: {user_info.get('location', 'Not specified')}

TODAY'S SUMMARY:
- Revenue: ₹{business_stats.get('today_revenue', 0):.2f}
- Transactions: {business_stats.get('today_transactions', 0)}
- Total Stock Value: ₹{business_stats.get('total_stock_value', 0):.2f}
- Low Stock Items: {business_stats.get('low_stock_count', 0)}
- Total Items in Stock: {business_stats.get('total_stock_items', 0)}"""

        history_str = ""
        if context.get("conversation_history"):
            history_str = "\n\nRECENT CONVERSATION:\n"
            for msg in context["conversation_history"][-5:]:
                history_str += f"{msg['role'].upper()}: {msg['content']}\n"

        pending_str = ""
        if context.get("pending_data"):
            pending_str = f"\n\nPENDING DATA FROM PREVIOUS TURN:\n{json.dumps(context['pending_data'], indent=2)}"

        stock_str = ""
        if context.get("stock_items"):
            stock_str = "\n\nCURRENT STOCK INVENTORY:\n" + "\n".join([
                f"- {s['name']}: {s['stock']} {s.get('unit', 'units')} @ ₹{s['price']}"
                for s in context["stock_items"][:15]
            ])
            if len(context["stock_items"]) > 15:
                stock_str += f"\n... and {len(context['stock_items']) - 15} more items"

        low_stock_str = ""
        if context.get("low_stock_items"):
            low_stock_str = "\n\n⚠️ LOW STOCK ALERTS:\n" + "\n".join([
                f"- {s['name']}: {s['stock']} (reorder at {s['reorder_point']})"
                for s in context["low_stock_items"][:5]
            ])

        txn_str = ""
        if context.get("recent_transactions"):
            txn_str = "\n\nRECENT TRANSACTIONS:\n" + "\n".join([
                f"- {t['type']}: {t['items'][0]['name'] if t['items'] else 'items'} - ₹{t['total']} at {t['time']}"
                for t in context["recent_transactions"][:5]
            ])

        return f"""You are Hisaab, an intelligent AI accountant for {user_info.get('shop_name', 'this shop')}.
You MUST maintain context from the conversation and remember what the user said.
{business_str}

CRITICAL: Always refer to the conversation history to understand what item/transaction the user is talking about.
{history_str}{pending_str}{stock_str}{low_stock_str}{txn_str}

YOUR CAPABILITIES:
1. Record SALES: "sold 20 samosas at 10 each", "விற்றேன் 20 சமோசா"
2. Record STOCK/PURCHASES: "bought 50kg rice at 40 per kg", "அரிசி வாங்கினேன்"
3. Record EXPENSES: "paid 500 for electricity"
4. Answer QUERIES:
   - Stock queries: "how much samosa do I have?", "what's in stock?", "low stock items?"
   - Sales queries: "how much did I sell today?", "total revenue?"
   - Use the CURRENT STOCK INVENTORY and RECENT TRANSACTIONS data provided above
5. Parse BILLS/PDFs: Extract items from uploaded bills

IMPORTANT FOR QUERIES:
- When user asks about stock, refer to the CURRENT STOCK INVENTORY section above
- When user asks about sales/revenue, refer to TODAY'S SUMMARY and RECENT TRANSACTIONS
- Give specific numbers from the data provided
- If asking about an item not in stock, say it's not in inventory

RESPONSE FORMAT - Always return valid JSON:
{{
    "action": "record_transaction" | "record_stock" | "query_response" | "clarification_needed" | "general_response" | "confirm_transaction",
    "data": {{
        "transaction_type": "sale" | "purchase" | "expense" | "stock_add",
        "items": [
            {{"item_name": "samosa", "quantity": 20, "unit_price": 10, "unit": "piece"}}
        ],
        "total_amount": 200,
        "payment_mode": "cash" | "upi" | "credit",
        "person_name": "optional customer name"
    }},
    "clarification_question": "What was the price per samosa?",
    "clarification_type": "price" | "quantity" | "item" | "type",
    "response": "English response",
    "response_tamil": "Tamil response",
    "confidence": 0-100,
    "show_confirmation": true/false
}}

RULES:
1. **For SALES**: If user mentions item but not price, ask for price
2. **For STOCK ADDITIONS**: If user says "add stock" or "add X to stock":
   - If quantity missing: ask "How many X?"
   - If price missing: ask "What's the selling price per unit?"
   - If cost price missing: ask "What's the cost price?" (optional)
   - Use action="clarification_needed" to ask for missing info
3. If user mentions price but not item, ask what item (BUT CHECK HISTORY FIRST!)
4. If user says "10rs" after mentioning "samosa", connect them!
5. Always show confirmation table before recording transactions
6. Be conversational in {language}
7. Calculate total = quantity × unit_price
8. For stock additions, transaction_type should be "stock_add"

REMEMBER: The user may reference items from previous messages. ALWAYS check history!

EXAMPLES:
User: "add samosa to stock"
→ action="clarification_needed", clarification_question="How many samosas do you want to add?", clarification_type="quantity"

User: "add 10 samosas"
→ action="clarification_needed", clarification_question="What's the selling price per samosa?", clarification_type="price"

User: "sold 5 cakes"
→ action="clarification_needed", clarification_question="What's the price per cake?", clarification_type="price"
"""
    
    async def _handle_llm_result(
        self,
        result: Dict[str, Any],
        user_input: str,
        language: str,
        user_id: str,
        shop_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle the structured LLM response"""
        
        action = result.get("action", "general_response")
        
        if action == "clarification_needed":
            # Store partial data for next turn
            return {
                "response": result.get("response", result.get("clarification_question", "Can you provide more details?")),
                "response_tamil": result.get("response_tamil", result.get("clarification_question")),
                "pending_data": result.get("data", {}),
                "clarification_type": result.get("clarification_type"),
                "needs_clarification": True
            }
        
        elif action == "record_transaction" or action == "confirm_transaction":
            data = result.get("data", {})
            
            # If high confidence and show_confirmation, show table for approval
            if result.get("confidence", 0) >= 70 or result.get("show_confirmation"):
                items = data.get("items", [])
                total = data.get("total_amount", sum(i.get("quantity", 0) * i.get("unit_price", 0) for i in items))
                
                # Build confirmation table
                table_data = {
                    "type": data.get("transaction_type", "sale"),
                    "items": items,
                    "total": total,
                    "payment_mode": data.get("payment_mode", "cash")
                }
                
                response_en = f"Please confirm this {data.get('transaction_type', 'sale')}:\n"
                response_ta = f"இந்த {data.get('transaction_type', 'விற்பனை')} உறுதிப்படுத்துங்கள்:\n"
                
                for item in items:
                    response_en += f"• {item.get('item_name')}: {item.get('quantity')} × ₹{item.get('unit_price')} = ₹{item.get('quantity', 0) * item.get('unit_price', 0)}\n"
                    response_ta += f"• {item.get('item_name')}: {item.get('quantity')} × ₹{item.get('unit_price')} = ₹{item.get('quantity', 0) * item.get('unit_price', 0)}\n"
                
                response_en += f"\nTotal: ₹{total}\n\nSay 'Confirm' to save or 'Cancel' to discard."
                response_ta += f"\nமொத்தம்: ₹{total}\n\nசேமிக்க 'சரி' அல்லது ரத்து செய்ய 'வேண்டாம்' சொல்லுங்கள்."
                
                return {
                    "response": response_en,
                    "response_tamil": response_ta,
                    "pending_data": {**table_data, "awaiting_confirmation": True},
                    "show_table": True,
                    "table_data": table_data
                }
            else:
                return {
                    "response": result.get("response", "I need more details to record this."),
                    "response_tamil": result.get("response_tamil"),
                    "pending_data": data,
                    "clarification_type": result.get("clarification_type")
                }
        
        elif action == "record_stock":
            data = result.get("data", {})
            items = data.get("items", [])
            
            table_data = {
                "type": "stock_add",
                "items": items,
                "total": sum(i.get("quantity", 0) * i.get("unit_price", 0) for i in items)
            }
            
            response_en = "Please confirm this stock addition:\n"
            response_ta = "இந்த சரக்கு சேர்ப்பை உறுதிப்படுத்துங்கள்:\n"
            
            for item in items:
                response_en += f"• {item.get('item_name')}: {item.get('quantity')} {item.get('unit', 'units')} @ ₹{item.get('unit_price')}\n"
                response_ta += f"• {item.get('item_name')}: {item.get('quantity')} {item.get('unit', 'units')} @ ₹{item.get('unit_price')}\n"
            
            response_en += "\nSay 'Confirm' to save or 'Cancel' to discard."
            response_ta += "\nசேமிக்க 'சரி' சொல்லுங்கள்."
            
            return {
                "response": response_en,
                "response_tamil": response_ta,
                "pending_data": {**table_data, "awaiting_confirmation": True},
                "show_table": True,
                "table_data": table_data
            }
        
        elif action == "query_response":
            return {
                "response": result.get("response", "Here's what I found."),
                "response_tamil": result.get("response_tamil"),
                "data": result.get("data")
            }
        
        else:
            return {
                "response": result.get("response", "I'm here to help! Tell me about your sales or ask any question."),
                "response_tamil": result.get("response_tamil")
            }
    
    async def _handle_clarification_response(
        self,
        user_input: str,
        language: str,
        user_id: str,
        shop_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle response to a clarification question"""
        
        pending = context.get("pending_data", {})
        clarification_type = context.get("pending_clarification")
        
        # Merge the new info with pending data
        system_prompt = f"""You are completing a transaction entry. 
Previous data: {json.dumps(pending)}
Clarification was asked for: {clarification_type}
User responded: {user_input}

Merge this information and return the complete transaction data.
Return JSON with action="record_transaction" or "confirm_transaction" and complete data."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = await self.groq.chat_completion(messages, json_mode=True, temperature=0.2)
        
        try:
            result = json.loads(response)
            result["show_confirmation"] = True
            return await self._handle_llm_result(result, user_input, language, user_id, shop_id, context)
        except:
            return {
                "response": "I didn't quite catch that. Could you please repeat?",
                "response_tamil": "புரியவில்லை. மீண்டும் சொல்லுங்கள்?"
            }
    
    async def _confirm_pending_data(
        self,
        user_id: str,
        shop_id: str,
        context: Dict[str, Any],
        language: str
    ) -> Dict[str, Any]:
        """Confirm and save the pending transaction/stock"""
        
        pending = context.get("pending_data", {})
        data_type = pending.get("type", "sale")
        items = pending.get("items", [])
        
        if data_type == "stock_add":
            # Add to stock
            for item in items:
                stock_item = await StockItem.find_one(
                    StockItem.name == item.get("item_name"),
                    StockItem.user_id == user_id
                )
                
                if stock_item:
                    stock_item.current_stock += item.get("quantity", 0)
                    stock_item.selling_price = item.get("unit_price", stock_item.selling_price)
                    await stock_item.save()
                else:
                    new_stock = StockItem(
                        name=item.get("item_name"),
                        category="general",
                        current_stock=item.get("quantity", 0),
                        unit=item.get("unit", "piece"),
                        cost_price=item.get("unit_price", 0) * 0.8,
                        selling_price=item.get("unit_price", 0),
                        user_id=user_id,
                        shop_id=shop_id
                    )
                    await new_stock.save()
            
            return {
                "response": f"Stock added successfully! {len(items)} item(s) updated.",
                "response_tamil": f"சரக்கு சேர்க்கப்பட்டது! {len(items)} பொருட்கள் புதுப்பிக்கப்பட்டன.",
                "success": True,
                "clear_pending": True
            }
        else:
            # Create transaction
            type_mapping = {
                "sale": TransactionType.SALE,
                "purchase": TransactionType.PURCHASE,
                "expense": TransactionType.EXPENSE
            }

            # For sales, verify stock availability first
            if data_type == "sale":
                stock_issues = []

                for item in items:
                    # Find stock item (case-insensitive)
                    all_stock = await StockItem.find(
                        StockItem.user_id == user_id,
                        StockItem.shop_id == shop_id
                    ).to_list()

                    stock_item = None
                    for stock in all_stock:
                        if stock.name.lower() == item.get("item_name", "").lower():
                            stock_item = stock
                            break

                    if not stock_item:
                        stock_issues.append(f"{item.get('item_name')} not found in inventory")
                    elif stock_item.current_stock < item.get("quantity", 0):
                        stock_issues.append(
                            f"{item.get('item_name')}: only {stock_item.current_stock} {stock_item.unit} available, "
                            f"but {item.get('quantity', 0)} requested"
                        )

                if stock_issues:
                    error_msg_en = "Cannot complete sale - Stock issues:\n" + "\n".join(f"• {issue}" for issue in stock_issues)
                    error_msg_ta = "விற்பனை முடிக்க முடியாது - சரக்கு பிரச்சனைகள்:\n" + "\n".join(f"• {issue}" for issue in stock_issues)

                    return {
                        "response": error_msg_en,
                        "response_tamil": error_msg_ta,
                        "success": False,
                        "clear_pending": True
                    }

            try:
                transaction = Transaction(
                    type=type_mapping.get(data_type, TransactionType.SALE),
                    items=[
                        TransactionItem(
                            item_name=item.get("item_name", "item"),
                            normalized_name=item.get("item_name", "item").lower(),
                            quantity=item.get("quantity", 1),
                            unit=item.get("unit", "piece"),
                            unit_price=item.get("unit_price", 0),
                            total=item.get("quantity", 1) * item.get("unit_price", 0)
                        )
                        for item in items
                    ],
                    total_amount=pending.get("total", sum(i.get("quantity", 0) * i.get("unit_price", 0) for i in items)),
                    payment_mode=PaymentMode(pending.get("payment_mode", "cash")),
                    confidence_score=100,
                    source="chat",
                    original_input="Voice/Chat entry",
                    language=language,
                    user_id=user_id,
                    shop_id=shop_id
                )
                logger.info(f"Saving transaction: {transaction.transaction_id} for user {user_id}")
                await transaction.save()
                logger.info(f"Transaction saved successfully: {transaction.transaction_id}")
            except Exception as e:
                logger.error(f"Failed to save transaction: {e}")
                return {
                    "response": f"Error saving transaction: {str(e)}",
                    "response_tamil": f"பிழை: {str(e)}",
                    "success": False
                }

            # Update stock for sales
            if data_type == "sale":
                for item in items:
                    # Find and update stock directly
                    all_stock = await StockItem.find(
                        StockItem.user_id == user_id,
                        StockItem.shop_id == shop_id
                    ).to_list()

                    for stock in all_stock:
                        if stock.name.lower() == item.get("item_name", "").lower():
                            stock.current_stock -= item.get("quantity", 0)
                            await stock.save()
                            logger.info(f"Updated stock for {stock.name}: -{item.get('quantity', 0)}, new stock: {stock.current_stock}")
                            break

            # Update stock for purchases
            elif data_type == "purchase":
                for item in items:
                    # Find or create stock item
                    all_stock = await StockItem.find(
                        StockItem.user_id == user_id,
                        StockItem.shop_id == shop_id
                    ).to_list()

                    stock_item = None
                    for stock in all_stock:
                        if stock.name.lower() == item.get("item_name", "").lower():
                            stock_item = stock
                            break

                    if stock_item:
                        stock_item.current_stock += item.get("quantity", 0)
                        await stock_item.save()
                    else:
                        new_stock = StockItem(
                            name=item.get("item_name"),
                            category="general",
                            current_stock=item.get("quantity", 0),
                            unit=item.get("unit", "piece"),
                            cost_price=item.get("unit_price", 0),
                            selling_price=item.get("unit_price", 0) * 1.25,
                            user_id=user_id,
                            shop_id=shop_id
                        )
                        await new_stock.save()
            
            return {
                "response": f"Recorded! {data_type.title()} of ₹{pending.get('total', 0)} saved.",
                "response_tamil": f"பதிவு செய்யப்பட்டது! ₹{pending.get('total', 0)} {data_type} சேமிக்கப்பட்டது.",
                "transaction_id": transaction.transaction_id,
                "success": True,
                "clear_pending": True
            }
    
    async def _reject_pending_data(self, language: str) -> Dict[str, Any]:
        """Cancel pending transaction"""
        return {
            "response": "Cancelled. What else can I help you with?",
            "response_tamil": "ரத்து செய்யப்பட்டது. வேறு என்ன உதவி?",
            "clear_pending": True
        }
    
    async def process_pdf(
        self,
        pdf_text: str,
        pdf_type: str,  # "sales" or "stock"
        user_id: str,
        shop_id: str,
        language: str = "tamil"
    ) -> Dict[str, Any]:
        """Process extracted PDF text and return structured data"""
        
        system_prompt = f"""You are an expert at extracting data from {pdf_type} bills/invoices.
Extract all items with their quantities, unit prices, and totals.

Return JSON:
{{
    "type": "{pdf_type}",
    "items": [
        {{"item_name": "...", "quantity": ..., "unit_price": ..., "unit": "..."}},
    ],
    "total": ...,
    "vendor_name": "...",
    "bill_date": "...",
    "bill_number": "..."
}}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract data from this bill:\n\n{pdf_text}"}
        ]
        
        response = await self.groq.chat_completion(messages, json_mode=True)
        
        try:
            data = json.loads(response)
            data["awaiting_confirmation"] = True
            
            # Build response with table
            items = data.get("items", [])
            total = data.get("total", sum(i.get("quantity", 0) * i.get("unit_price", 0) for i in items))
            
            response_en = f"I found {len(items)} items in this {pdf_type} bill:\n\n"
            for item in items:
                response_en += f"• {item.get('item_name')}: {item.get('quantity')} × ₹{item.get('unit_price')}\n"
            response_en += f"\nTotal: ₹{total}\n\nConfirm to save or Cancel to discard."
            
            return {
                "response": response_en,
                "response_tamil": response_en,  # TODO: translate
                "pending_data": data,
                "show_table": True,
                "table_data": data
            }
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            return {
                "response": "I couldn't parse this bill. Please try again or enter manually.",
                "response_tamil": "பில் படிக்க முடியவில்லை. மீண்டும் முயற்சிக்கவும்."
            }
    
    async def _get_or_create_conversation(
        self,
        conversation_id: Optional[str],
        user_id: str,
        shop_id: str
    ) -> Conversation:
        """Get existing conversation or create new one"""
        
        if conversation_id:
            conversation = await Conversation.get(conversation_id)
            if conversation:
                return conversation
        
        # Create new conversation
        conversation = Conversation(
            user_id=user_id,
            shop_id=shop_id,
            metadata={}
        )
        await conversation.save()
        
        return conversation
