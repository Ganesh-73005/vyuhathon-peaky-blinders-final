from typing import Dict, Any, Optional, List
from services.groq_service import GroqService
from models.transaction import TransactionType, PaymentMode
from config.settings import settings
from loguru import logger
import json

class NLPExtractionAgent:
    """Agent for extracting structured data from unstructured input using LLM"""

    def __init__(self, groq_service: GroqService):
        self.groq = groq_service
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD

    async def classify_intent(
        self,
        text: str,
        language: str = "tamil",
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Classify user intent using LLM

        Returns:
            {
                "intent": "transaction|query|clarification|greeting|complaint",
                "sub_intent": "sale|purchase|credit_check|stock_query|...",
                "confidence": 0-100,
                "reasoning": "explanation"
            }
        """

        system_prompt = """You are an expert intent classifier for a Tamil kirana store accounting system.

Classify user messages into these intents:
1. TRANSACTION - User is logging a sale, purchase, expense, credit, freebie, or loss
2. QUERY - User is asking for information (credit status, stock levels, revenue, etc.)
3. CLARIFICATION - User is responding to a clarification question
4. GREETING - User is greeting or starting conversation
5. COMPLAINT - User is expressing frustration or reporting an issue
6. COMMAND - User wants to perform an action (generate report, send reminder, etc.)

For TRANSACTION, identify sub-intent:
- sale, purchase, expense, credit_given, credit_received, freebie, wastage, spoilage

For QUERY, identify sub-intent:
- credit_status, stock_check, revenue_summary, daily_summary, customer_info, leakage_analysis

Return JSON:
{
  "intent": "main intent",
  "sub_intent": "specific sub-intent or null",
  "confidence": 0-100,
  "reasoning": "brief explanation",
  "entities_hint": ["list of entities likely present"]
}"""

        context_str = ""
        if conversation_history:
            recent = conversation_history[-3:]  # Last 3 messages
            context_str = "\n\nRecent conversation:\n" + "\n".join([
                f"{msg['role']}: {msg['content']}" for msg in recent
            ])

        user_prompt = f"""Language: {language}
User message: "{text}"{context_str}

Classify this message's intent:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await self.groq.chat_completion(messages, json_mode=True, temperature=0.3)
            result = json.loads(response)
            logger.info(f"Intent classified: {result['intent']} (confidence: {result['confidence']}%)")
            return result
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {
                "intent": "unknown",
                "sub_intent": None,
                "confidence": 0,
                "reasoning": "Classification failed",
                "entities_hint": []
            }

    async def extract_transaction(
        self,
        text: str,
        language: str = "tamil",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract transaction details from text using LLM

        Returns:
            {
                "entities": {...},
                "confidence": 0-100,
                "ambiguities": [...],
                "clarification_needed": "question" or None
            }
        """

        # Use LLM for extraction
        llm_result = await self._llm_extraction(text, language, context)

        # Check if clarification needed
        if llm_result["confidence"] < self.confidence_threshold:
            llm_result["clarification_needed"] = await self._generate_smart_clarification(
                text, llm_result, language
            )

        return llm_result
    
    def _rule_based_extraction(self, text: str, language: str) -> Dict[str, Any]:
        """Fast rule-based extraction for common patterns"""
        
        text_lower = text.lower()
        entities = {}
        confidence = 100
        ambiguities = []
        
        # Detect transaction type
        if any(word in text_lower for word in ["sold", "விற்றேன்", "விற்பனை", "sale"]):
            entities["transaction_type"] = TransactionType.SALE
        elif any(word in text_lower for word in ["bought", "வாங்கினேன்", "purchase", "கொள்முதல்"]):
            entities["transaction_type"] = TransactionType.PURCHASE
        elif any(word in text_lower for word in ["paid", "செலுத்தினேன்", "expense"]):
            entities["transaction_type"] = TransactionType.EXPENSE
        elif any(word in text_lower for word in ["credit", "கடன்", "took on credit"]):
            entities["transaction_type"] = TransactionType.CREDIT
        elif any(word in text_lower for word in ["free", "இலவசம்", "freebie"]):
            entities["transaction_type"] = TransactionType.FREEBIE
        elif any(word in text_lower for word in ["waste", "spoil", "கெட்டுப்", "வீணாக"]):
            entities["transaction_type"] = TransactionType.LOSS
        else:
            ambiguities.append("transaction_type")
            confidence -= 30
        
        # Extract numbers
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        
        if len(numbers) >= 2:
            # Pattern: "sold 20 samosas 10 each" or "20 samosa 10 rupees"
            entities["quantity"] = float(numbers[0])
            entities["unit_price"] = float(numbers[1])
            entities["total_amount"] = entities["quantity"] * entities["unit_price"]
        elif len(numbers) == 1:
            # Only one number - could be total or quantity
            entities["total_amount"] = float(numbers[0])
            ambiguities.append("quantity_or_price")
            confidence -= 20
        else:
            ambiguities.append("amount")
            confidence -= 40
        
        # Extract item name (simple heuristic)
        # Look for words between numbers or after action verbs
        item_patterns = [
            r'(?:sold|விற்றேன்|bought|வாங்கினேன்)\s+\d*\s*(\w+)',
            r'(\w+)\s+\d+\s*(?:each|rupees|ரூபாய்)',
        ]
        
        for pattern in item_patterns:
            match = re.search(pattern, text_lower)
            if match:
                entities["item_name"] = match.group(1)
                break
        
        if "item_name" not in entities:
            ambiguities.append("item_name")
            confidence -= 25
        
        # Extract person name (look for capitalized words or common names)
        person_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', text)
        if person_match:
            entities["person_name"] = person_match.group(1)
        
        # Payment mode detection
        if any(word in text_lower for word in ["cash", "காசு", "பணம்"]):
            entities["payment_mode"] = PaymentMode.CASH
        elif any(word in text_lower for word in ["upi", "gpay", "phonepe", "paytm"]):
            entities["payment_mode"] = PaymentMode.UPI
        elif any(word in text_lower for word in ["credit", "கடன்"]):
            entities["payment_mode"] = PaymentMode.CREDIT
        
        return {
            "entities": entities,
            "confidence": max(0, confidence),
            "ambiguities": ambiguities,
            "clarification_needed": None,
            "method": "rule_based"
        }
    
    async def _llm_extraction(
        self,
        text: str,
        language: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """LLM-based extraction using Groq"""

        system_prompt = """You are an expert at extracting transaction information from casual Tamil/English shop owner speech.

You understand:
- Mixed Tamil-English (Tanglish)
- Casual abbreviations ("R" for Ramesh, "samosa" for சமோசா)
- Implicit information (if someone says "Ramesh took again", check context for what/how much)
- Common shop terminology

Extract these fields:
- transaction_type: sale, purchase, expense, loss, credit, personal, freebie
- item_name: name of item/product (normalize to English)
- item_name_tamil: Tamil name if mentioned
- quantity: number of items (float)
- unit: piece, kg, liter, packet, etc.
- unit_price: price per item (float)
- total_amount: total transaction amount (float)
- person_name: customer/supplier name if mentioned
- payment_mode: cash, upi, credit, card
- notes: any additional context

IMPORTANT RULES:
1. If quantity and unit_price are given, calculate total_amount = quantity × unit_price
2. If only total_amount is given, try to infer quantity or unit_price from context
3. For credit transactions, person_name is REQUIRED
4. Common patterns:
   - "sold 20 samosas 10 each" → quantity=20, unit_price=10, total=200
   - "bought milk 500" → item=milk, total=500 (quantity/price unclear)
   - "Ramesh took on credit" → person=Ramesh, payment=credit (amount unclear)

Return JSON:
{
  "entities": {
    "transaction_type": "...",
    "item_name": "...",
    "quantity": number or null,
    "unit_price": number or null,
    "total_amount": number or null,
    "person_name": "..." or null,
    "payment_mode": "..." or null,
    ...
  },
  "confidence": 0-100,
  "ambiguities": ["list of fields that are unclear"],
  "reasoning": "brief explanation of extraction logic"
}

If a field is unclear or missing, set it to null and add to ambiguities list."""

        context_str = ""
        if context:
            # Include memory context for better extraction
            if "recent_transactions" in context:
                context_str += "\n\nRecent transactions:\n"
                for txn in context["recent_transactions"][:3]:
                    context_str += f"- {txn}\n"

            if "customer_history" in context:
                context_str += f"\n\nCustomer history: {context['customer_history']}"

        user_prompt = f"""Language: {language}
User input: "{text}"{context_str}

Extract transaction details as JSON:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await self.groq.chat_completion(
                messages,
                json_mode=True,
                temperature=0.2,  # Lower temperature for more consistent extraction
                max_tokens=512
            )
            result = json.loads(response)

            # Validate and normalize entities
            entities = result.get("entities", {})

            # Calculate total if missing but have quantity and price
            if entities.get("quantity") and entities.get("unit_price") and not entities.get("total_amount"):
                entities["total_amount"] = entities["quantity"] * entities["unit_price"]

            # Ensure confidence is reasonable
            confidence = result.get("confidence", 50)
            ambiguities = result.get("ambiguities", [])

            # Reduce confidence if critical fields are missing
            if not entities.get("item_name"):
                confidence = min(confidence, 40)
            if not entities.get("total_amount") and not (entities.get("quantity") and entities.get("unit_price")):
                confidence = min(confidence, 50)

            logger.info(f"LLM extraction: {entities.get('item_name', 'unknown')} - confidence {confidence}%")

            return {
                "entities": entities,
                "confidence": confidence,
                "ambiguities": ambiguities,
                "reasoning": result.get("reasoning", ""),
                "method": "llm"
            }
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {
                "entities": {},
                "confidence": 0,
                "ambiguities": ["all"],
                "reasoning": f"Extraction failed: {str(e)}",
                "method": "failed"
            }
    
    def _merge_extractions(
        self,
        rule_based: Dict[str, Any],
        llm_based: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge rule-based and LLM extractions, preferring higher confidence"""
        
        if rule_based["confidence"] >= llm_based["confidence"]:
            return rule_based
        else:
            # Use LLM but fill gaps with rule-based
            merged_entities = {**rule_based["entities"], **llm_based["entities"]}
            return {
                "entities": merged_entities,
                "confidence": llm_based["confidence"],
                "ambiguities": llm_based.get("ambiguities", []),
                "clarification_needed": None,
                "method": "merged"
            }
    
    async def _generate_smart_clarification(
        self,
        original_text: str,
        extraction: Dict[str, Any],
        language: str
    ) -> Optional[str]:
        """Generate intelligent clarification question using LLM"""

        ambiguities = extraction.get("ambiguities", [])
        entities = extraction.get("entities", {})

        if not ambiguities:
            return None

        # Use LLM to generate contextual clarification
        system_prompt = """You are a helpful assistant for a Tamil shop owner.

When transaction details are unclear, ask ONE specific clarification question in a natural, conversational way.

Rules:
1. Ask in the same language as the user (Tamil or English)
2. Be specific about what's missing
3. Keep it short and friendly
4. Reference what you DO understand to show you're listening
5. Only ask about the MOST critical missing piece

Examples:
- User: "sold samosas" → "How many samosas did you sell?"
- User: "Ramesh took" → "What did Ramesh take?"
- User: "20 samosas" → "What was the price per samosa?"
- User: "gave credit" → "Who did you give credit to and how much?"
"""

        user_prompt = f"""User said: "{original_text}"

I understood:
{json.dumps(entities, indent=2)}

But these are unclear: {', '.join(ambiguities)}

Generate ONE clarification question in {language}:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await self.groq.chat_completion(
                messages,
                temperature=0.7,
                max_tokens=100
            )

            clarification = response.strip()
            logger.info(f"Generated clarification: {clarification}")
            return clarification

        except Exception as e:
            logger.error(f"Clarification generation failed: {e}")
            # Fallback to simple clarification
            return self._simple_clarification(ambiguities, entities)

    def _simple_clarification(self, ambiguities: List[str], entities: Dict) -> str:
        """Simple rule-based clarification fallback"""

        if "amount" in ambiguities or "total_amount" not in entities:
            return "How much was the total amount?"

        if "item_name" in ambiguities or "item_name" not in entities:
            return "What item was this for?"

        if "quantity_or_price" in ambiguities:
            if "quantity" not in entities:
                return "How many items?"
            if "unit_price" not in entities:
                return "What was the price per item?"

        if "transaction_type" in ambiguities:
            return "Was this a sale, purchase, or expense?"

        return "Can you provide more details about this transaction?"

