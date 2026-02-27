from typing import Dict, Any, Optional, List
from services import GroqService, WhisperService, CartesiaService
from agents.nlp_agent import NLPExtractionAgent
from agents.stock_agent import StockIntelligenceAgent
from agents.leakage_agent import LeakageDetectiveAgent
from models.conversation import Conversation, Message, MessageRole, MessageType
from models.transaction import Transaction, TransactionType, TransactionItem, PersonInfo, PaymentMode
from loguru import logger
from datetime import datetime

class MasterOrchestrator:
    """Central brain coordinating all specialist agents"""
    
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
    
    async def process_message(
        self,
        user_input: str,
        user_id: str,
        shop_id: str,
        input_type: str = "text",
        language: str = "tamil",
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing user messages
        
        Returns:
            {
                "response": "text response",
                "response_tamil": "tamil response",
                "audio_url": "path to audio",
                "data": {...extracted data...},
                "conversation_id": "conv_id"
            }
        """
        
        # Get or create conversation
        conversation = await self._get_or_create_conversation(
            conversation_id, user_id, shop_id
        )
        
        # Add user message to conversation
        user_message = Message(
            role=MessageRole.USER,
            type=MessageType.TEXT if input_type == "text" else MessageType.VOICE,
            content=user_input
        )
        conversation.messages.append(user_message)
        
        # Classify intent using LLM
        conversation_history = [
            {"role": msg.role.value, "content": msg.content}
            for msg in conversation.messages[-5:]  # Last 5 messages
        ]

        intent_result = await self.nlp_agent.classify_intent(
            user_input, language, conversation_history
        )

        logger.info(f"Intent: {intent_result['intent']} (sub: {intent_result.get('sub_intent')}, confidence: {intent_result['confidence']}%)")

        response_data = None
        intent = intent_result["intent"].lower()
        sub_intent = intent_result.get("sub_intent", "").lower() if intent_result.get("sub_intent") else None

        if intent == "transaction":
            response_data = await self._handle_transaction(
                user_input, language, user_id, shop_id, conversation, sub_intent
            )
        elif intent == "query":
            response_data = await self._handle_query(
                user_input, language, user_id, shop_id, conversation, sub_intent
            )
        elif intent == "clarification":
            response_data = await self._handle_clarification(
                user_input, language, user_id, shop_id, conversation
            )
        elif intent == "greeting":
            response_data = await self._handle_greeting(
                user_input, language, user_id, shop_id
            )
        elif intent == "complaint":
            response_data = await self._handle_complaint(
                user_input, language
            )
        elif intent == "command":
            response_data = await self._handle_command(
                user_input, language, user_id, shop_id, sub_intent
            )
        else:
            response_data = await self._handle_general(
                user_input, language, user_id, shop_id
            )
        
        # Generate voice response if needed
        audio_url = None
        if response_data.get("response_tamil"):
            audio_url = await self.cartesia.generate_voice_response(
                response_data["response"],
                response_data["response_tamil"],
                prefer_tamil=True
            )
        
        # Add assistant message to conversation
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            type=MessageType.TEXT,
            content=response_data["response"],
            content_tamil=response_data.get("response_tamil"),
            audio_url=audio_url
        )
        conversation.messages.append(assistant_message)
        conversation.last_message_at = datetime.now()
        
        await conversation.save()
        
        return {
            **response_data,
            "audio_url": audio_url,
            "conversation_id": str(conversation.id)
        }
    
    async def _handle_transaction(
        self,
        text: str,
        language: str,
        user_id: str,
        shop_id: str,
        conversation: Conversation,
        sub_intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle transaction logging"""
        
        # Extract transaction details
        extraction = await self.nlp_agent.extract_transaction(text, language)
        
        # Check if clarification needed
        if extraction.get("clarification_needed"):
            conversation.pending_clarification = extraction["clarification_needed"]
            await conversation.save()
            
            return {
                "response": extraction["clarification_needed"],
                "response_tamil": extraction["clarification_needed"],  # TODO: Translate
                "needs_clarification": True,
                "extraction": extraction
            }
        
        # Create transaction
        entities = extraction["entities"]
        
        transaction = Transaction(
            type=entities.get("transaction_type", TransactionType.SALE),
            items=[
                TransactionItem(
                    item_name=entities.get("item_name", "unknown"),
                    normalized_name=entities.get("item_name", "unknown").lower(),
                    quantity=entities.get("quantity", 1),
                    unit_price=entities.get("unit_price", 0),
                    total=entities.get("total_amount", 0)
                )
            ],
            total_amount=entities.get("total_amount", 0),
            payment_mode=entities.get("payment_mode", PaymentMode.CASH),
            person=PersonInfo(name=entities.get("person_name")) if entities.get("person_name") else None,
            confidence_score=extraction["confidence"],
            source="text",
            original_input=text,
            language=language,
            user_id=user_id,
            shop_id=shop_id
        )
        
        await transaction.save()
        
        # Update stock
        for item in transaction.items:
            await self.stock_agent.update_stock_from_transaction(
                item.item_name,
                item.quantity,
                transaction.type.value,
                user_id,
                shop_id
            )
        
        # Check for leakage
        if transaction.type == TransactionType.SALE:
            await self.leakage_agent.detect_underpricing(transaction, user_id, shop_id)
        
        # Generate confirmation response
        response = f"Got it! Logged {entities.get('quantity', 1)} {entities.get('item_name', 'items')} for ₹{entities.get('total_amount', 0)}."
        response_tamil = f"சரி! {entities.get('quantity', 1)} {entities.get('item_name', 'பொருட்கள்')} ₹{entities.get('total_amount', 0)} பதிவு செய்தேன்."
        
        return {
            "response": response,
            "response_tamil": response_tamil,
            "transaction_id": transaction.transaction_id,
            "data": extraction
        }
    
    async def _handle_query(
        self,
        text: str,
        language: str,
        user_id: str,
        shop_id: str,
        conversation: Conversation,
        sub_intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle information queries using LLM to generate intelligent responses"""

        # Route based on sub-intent
        if sub_intent == "credit_status" or "credit" in text.lower() or "கடன்" in text.lower():
            analysis = await self.leakage_agent.analyze_credit_black_holes(user_id, shop_id)

            response = f"Total credit outstanding: ₹{analysis['total_credit_outstanding']:.0f}. "
            response += f"{analysis['black_hole_count']} customers have overdue payments."

            response_tamil = f"மொத்த கடன்: ₹{analysis['total_credit_outstanding']:.0f}. "
            response_tamil += f"{analysis['black_hole_count']} வாடிக்கையாளர்கள் பணம் தரவில்லை."

        elif sub_intent == "stock_check" or "stock" in text.lower() or "பங்கு" in text.lower():
            # TODO: Implement stock query
            response = "Let me check your stock levels..."
            response_tamil = "உங்கள் பங்கு நிலைகளை சரிபார்க்கிறேன்..."

        elif sub_intent == "revenue_summary" or "revenue" in text.lower() or "sales" in text.lower():
            # TODO: Implement revenue summary
            response = "Let me get your revenue summary..."
            response_tamil = "உங்கள் வருவாய் சுருக்கத்தை பெறுகிறேன்..."

        else:
            # Use LLM to generate contextual response
            response = await self._generate_query_response(text, language, user_id, shop_id)
            response_tamil = response  # TODO: Translate

        return {
            "response": response,
            "response_tamil": response_tamil
        }

    async def _generate_query_response(
        self,
        query: str,
        language: str,
        user_id: str,
        shop_id: str
    ) -> str:
        """Generate intelligent query response using LLM"""

        system_prompt = """You are Hisaab, an AI accountant for a Tamil kirana store.

When the user asks a question, provide a helpful, concise answer based on what you can help with:
- Sales tracking and revenue analysis
- Stock management and reorder alerts
- Credit tracking and customer payment history
- Expense monitoring
- Leakage detection (personal use, underpricing, wastage)
- Daily/weekly business summaries

If you don't have specific data, explain what you CAN do and ask if they want that information.

Keep responses short, friendly, and actionable."""

        user_prompt = f"""User question ({language}): "{query}"

Provide a helpful response:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await self.groq.chat_completion(
                messages,
                temperature=0.7,
                max_tokens=200
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Query response generation failed: {e}")
            return "I can help you track sales, expenses, stock, and credit. What would you like to know?"
    
    async def _handle_clarification(
        self,
        text: str,
        language: str,
        user_id: str,
        shop_id: str,
        conversation: Conversation
    ) -> Dict[str, Any]:
        """Handle clarification responses"""

        # Get pending clarification context
        if conversation.pending_clarification:
            # Re-process with clarification context
            return await self._handle_transaction(
                text, language, user_id, shop_id, conversation, None
            )
        else:
            # No pending clarification, treat as new transaction
            return await self._handle_transaction(
                text, language, user_id, shop_id, conversation, None
            )

    async def _handle_greeting(
        self,
        text: str,
        language: str,
        user_id: str,
        shop_id: str
    ) -> Dict[str, Any]:
        """Handle greetings"""

        response = "Hello! I'm Hisaab, your AI shop accountant. Tell me about your sales, purchases, or ask me anything about your business!"
        response_tamil = "வணக்கம்! நான் ஹிசாப், உங்கள் AI கடை கணக்காளர். விற்பனை, கொள்முதல் சொல்லுங்கள் அல்லது உங்கள் வியாபாரம் பற்றி கேளுங்கள்!"

        return {
            "response": response,
            "response_tamil": response_tamil
        }

    async def _handle_complaint(
        self,
        text: str,
        language: str
    ) -> Dict[str, Any]:
        """Handle complaints or frustrations"""

        response = "I understand your concern. Let me help you with that. Can you tell me more about what's bothering you?"
        response_tamil = "உங்கள் கவலை புரிகிறது. நான் உதவுகிறேன். என்ன பிரச்சனை என்று சொல்லுங்கள்?"

        return {
            "response": response,
            "response_tamil": response_tamil
        }

    async def _handle_command(
        self,
        text: str,
        language: str,
        user_id: str,
        shop_id: str,
        sub_intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle commands like generate report, send reminder, etc."""

        # TODO: Implement specific commands
        response = "I'll help you with that command. This feature is coming soon!"
        response_tamil = "அந்த கட்டளையில் உதவுகிறேன். இந்த அம்சம் விரைவில் வரும்!"

        return {
            "response": response,
            "response_tamil": response_tamil
        }

    async def _handle_general(
        self,
        text: str,
        language: str,
        user_id: str,
        shop_id: str
    ) -> Dict[str, Any]:
        """Handle general conversation"""

        response = "I'm Hisaab, your shop accountant. Tell me about your sales, purchases, or ask me anything about your business!"
        response_tamil = "நான் ஹிசாப், உங்கள் கடை கணக்காளர். விற்பனை, கொள்முதல் சொல்லுங்கள் அல்லது உங்கள் வியாபாரம் பற்றி கேளுங்கள்!"

        return {
            "response": response,
            "response_tamil": response_tamil
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
            shop_id=shop_id
        )
        await conversation.save()
        
        return conversation

