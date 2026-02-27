from groq import Groq
from typing import List, Dict, Optional, Any
from config.settings import settings
from loguru import logger
import json

class GroqService:
    """Service for interacting with Groq LLaMA API"""

    def __init__(self):
        self.client = None
        if settings.GROQ_API_KEY:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
        else:
            logger.warning("GROQ_API_KEY not set, using dummy mode")

        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"  # Updated model

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        max_tokens: int = 1024,
        json_mode: bool = False,
        stream: bool = False
    ) -> str:
        """
        Get chat completion from Groq

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            json_mode: Whether to force JSON output
            stream: Whether to stream response

        Returns:
            Response content as string
        """
        if not self.client:
            return self._dummy_response(messages, json_mode)

        try:
            # Prepare request parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_completion_tokens": max_tokens,
                "top_p": 1,
                "stream": stream,
                "stop": None
            }

            # Add JSON mode if requested
            if json_mode:
                params["response_format"] = {"type": "json_object"}
                # Ensure system message requests JSON
                if messages and messages[0]["role"] == "system":
                    messages[0]["content"] += "\n\nYou must respond with valid JSON only."

            completion = self.client.chat.completions.create(**params)

            # Handle streaming vs non-streaming
            if stream:
                full_response = ""
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                return full_response
            else:
                return completion.choices[0].message.content

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            # Check if rate limited
            if "rate_limit" in str(e).lower() or "429" in str(e):
                logger.warning("Rate limited - using fallback parsing")
                return self._fallback_parse(messages, json_mode)
            return self._dummy_response(messages, json_mode)
    
    def _fallback_parse(self, messages: List[Dict[str, str]], json_mode: bool) -> str:
        """Fallback parsing when LLM is rate limited"""
        import re
        user_msg = messages[-1].get("content", "").lower() if messages else ""
        
        # Pattern: sold/bought X items at Y price
        sale_pattern = r'(?:sold|விற்றேன்)\s*(\d+)\s*(\w+)\s*(?:at|@)?\s*(\d+)\s*(?:rs|rupees|each)?'
        stock_pattern = r'(?:bought|வாங்கினேன்)\s*(\d+)\s*(?:kg|piece|units?)?\s*(\w+)\s*(?:at|@)?\s*(\d+)'
        
        sale_match = re.search(sale_pattern, user_msg, re.IGNORECASE)
        stock_match = re.search(stock_pattern, user_msg, re.IGNORECASE)
        
        if sale_match:
            qty = int(sale_match.group(1))
            item = sale_match.group(2)
            price = int(sale_match.group(3))
            result = {
                "action": "record_transaction",
                "data": {
                    "transaction_type": "sale",
                    "items": [{"item_name": item, "quantity": qty, "unit_price": price, "unit": "piece"}],
                    "total_amount": qty * price,
                    "payment_mode": "cash"
                },
                "confidence": 85,
                "show_confirmation": True,
                "response": f"Recording sale of {qty} {item} at ₹{price} each = ₹{qty*price}. Please confirm.",
                "response_tamil": f"{qty} {item} விற்பனை ₹{price} = ₹{qty*price}. உறுதிப்படுத்துங்கள்."
            }
            return json.dumps(result)
        
        if stock_match:
            qty = int(stock_match.group(1))
            item = stock_match.group(2)
            price = int(stock_match.group(3))
            result = {
                "action": "record_stock",
                "data": {
                    "transaction_type": "stock_add",
                    "items": [{"item_name": item, "quantity": qty, "unit_price": price, "unit": "piece"}]
                },
                "confidence": 85,
                "show_confirmation": True,
                "response": f"Adding {qty} {item} to stock at ₹{price} each. Please confirm."
            }
            return json.dumps(result)
        
        # Default fallback
        if json_mode:
            return json.dumps({
                "action": "general_response",
                "response": "I'm here to help! Tell me about your sales or ask any question.",
                "response_tamil": "நான் உதவ இங்கே இருக்கிறேன்! விற்பனை பற்றி சொல்லுங்கள்."
            })
        return "I'm here to help! Tell me about your sales."
    
    async def extract_entities(self, text: str, language: str = "tamil") -> Dict[str, Any]:
        """Extract transaction entities from text"""
        
        system_prompt = """You are an expert at extracting transaction information from casual shop owner speech.
Extract: item_name, quantity, unit_price, total_amount, transaction_type, person_name.
Return JSON with extracted entities and confidence score (0-100).
If information is missing, set field to null and reduce confidence."""
        
        user_prompt = f"Language: {language}\nText: {text}\n\nExtract transaction details as JSON."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, json_mode=True)
        
        try:
            return json.loads(response)
        except:
            return {"error": "Failed to parse response", "confidence": 0}
    
    async def categorize_transaction(
        self,
        transaction_data: Dict[str, Any],
        memory_context: List[Dict[str, Any]] = []
    ) -> Dict[str, Any]:
        """Categorize transaction using learned patterns"""
        
        system_prompt = """You are a smart ledger categorization system.
Categorize transactions into: revenue, inventory, operations, wastage, personal, freebie, leakage.
Use memory context to learn user's patterns.
Return JSON with category, subcategory, confidence, and business_vs_personal flag."""
        
        context_str = "\n".join([f"- {m['context']}" for m in memory_context[:5]])
        user_prompt = f"Transaction: {json.dumps(transaction_data)}\n\nLearned patterns:\n{context_str}\n\nCategorize this transaction."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, json_mode=True)
        
        try:
            return json.loads(response)
        except:
            return {"category": "revenue", "confidence": 50}
    
    async def generate_insight(
        self,
        insight_type: str,
        data: Dict[str, Any],
        language: str = "tamil"
    ) -> Dict[str, str]:
        """Generate conversational insight in Tamil and English"""
        
        system_prompt = f"""You are Hisaab, a friendly Tamil shop accountant.
Generate {insight_type} insight in both Tamil and English.
Be conversational, practical, and actionable. No jargon.
Return JSON with 'english' and 'tamil' keys."""
        
        user_prompt = f"Data: {json.dumps(data)}\n\nGenerate {insight_type} insight."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, json_mode=True, temperature=0.8)
        
        try:
            return json.loads(response)
        except:
            return {
                "english": "Unable to generate insight",
                "tamil": "தகவல் உருவாக்க முடியவில்லை"
            }
    
    async def get_festival_stock_suggestions(
        self,
        festival_name: str,
        festival_type: str = "religious",
        location: str = "Tamil Nadu"
    ) -> List[Dict[str, Any]]:
        """Get stock suggestions for upcoming festivals"""
        
        system_prompt = """You are an expert on Indian festivals and retail inventory planning.
Given a festival, suggest items that kirana stores should stock up on.

Return JSON array of items:
[
    {"item": "Item name", "category": "category", "priority": "high/medium/low", "reason": "Why this item is needed"}
]"""
        
        user_prompt = f"""Festival: {festival_name}
Type: {festival_type}
Location: {location}

Suggest 10 essential items a kirana store should stock for this festival."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self.chat_completion(messages, json_mode=True, temperature=0.5)
            suggestions = json.loads(response)
            return suggestions if isinstance(suggestions, list) else suggestions.get("items", [])
        except Exception as e:
            logger.error(f"Festival suggestion error: {e}")
            return [
                {"item": "Sweets", "category": "food", "priority": "high", "reason": "Essential for celebrations"},
                {"item": "Flowers", "category": "puja", "priority": "high", "reason": "Used in decorations and worship"},
                {"item": "Fruits", "category": "food", "priority": "medium", "reason": "Offerings and gifts"}
            ]
    
    def _dummy_response(self, messages: List[Dict[str, str]], json_mode: bool) -> str:
        """Generate dummy response when API is not available"""
        if json_mode:
            return json.dumps({
                "dummy": True,
                "message": "Groq API not configured",
                "confidence": 50
            })
        return "Groq API not configured. Using dummy mode."

