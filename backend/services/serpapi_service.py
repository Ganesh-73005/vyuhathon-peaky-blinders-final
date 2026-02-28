from serpapi import GoogleSearch
from typing import List, Dict, Optional, Any
from config.settings import settings
from loguru import logger
from datetime import datetime, timedelta

class SerpAPIService:
    """Service for competitor intelligence using SerpAPI"""
    
    def __init__(self):
        self.api_key = settings.SERPAPI_KEY
    
    async def search_nearby_competitors(
        self,
        location: str,
        business_type: str = "kirana store",
        radius_km: int = 2
    ) -> List[Dict[str, Any]]:
        """Search for nearby competitors using Google Maps"""
        if not self.api_key:
            return self._dummy_competitors()
        
        try:
            params = {
                "engine": "google_maps",
                "q": f"{business_type} near {location}",
                "type": "search",
                "api_key": self.api_key
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            competitors = []
            for place in results.get("local_results", [])[:10]:
                competitors.append({
                    "name": place.get("title"),
                    "address": place.get("address"),
                    "rating": place.get("rating"),
                    "reviews_count": place.get("reviews"),
                    "place_id": place.get("place_id"),
                    "phone": place.get("phone"),
                    "hours": place.get("hours"),
                    "type": place.get("type"),
                    "price_level": place.get("price"),
                    "thumbnail": place.get("thumbnail")
                })
            
            return competitors
        
        except Exception as e:
            logger.error(f"SerpAPI search error: {e}")
            return self._dummy_competitors()
    
    async def search_festivals(
        self,
        location: str = "Tamil Nadu",
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """Search for upcoming festivals in the region"""
        if not self.api_key:
            return self._dummy_festivals()
        
        try:
            # Search for upcoming festivals
            params = {
                "engine": "google",
                "q": f"upcoming festivals in {location} next {days_ahead} days 2024 2025",
                "api_key": self.api_key
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            festivals = []
            
            # Extract from organic results
            for result in results.get("organic_results", [])[:5]:
                festivals.append({
                    "name": result.get("title", "").split("-")[0].strip(),
                    "description": result.get("snippet", ""),
                    "source": result.get("link"),
                    "type": "religious" if any(word in result.get("title", "").lower() for word in ["pongal", "diwali", "navratri", "ganesh"]) else "cultural"
                })
            
            # Add known Tamil Nadu festivals if search fails
            if not festivals:
                festivals = self._dummy_festivals()
            
            return festivals
        
        except Exception as e:
            logger.error(f"Festival search error: {e}")
            return self._dummy_festivals()
    
    async def search_market_trends(
        self,
        location: str,
        category: str = "grocery"
    ) -> List[Dict[str, Any]]:
        """Search for market trends and pricing"""
        if not self.api_key:
            return self._dummy_trends()
        
        try:
            params = {
                "engine": "google",
                "q": f"{category} prices trends {location} India 2024",
                "api_key": self.api_key
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            trends = []
            for result in results.get("organic_results", [])[:5]:
                trends.append({
                    "title": result.get("title"),
                    "snippet": result.get("snippet"),
                    "source": result.get("link")
                })
            
            return trends if trends else self._dummy_trends()
        
        except Exception as e:
            logger.error(f"Trend search error: {e}")
            return self._dummy_trends()
    
    async def get_reviews(
        self,
        place_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get Google reviews for a place
        
        Args:
            place_id: Google Maps place ID
            limit: Maximum number of reviews to fetch
        
        Returns:
            List of reviews
        """
        if not self.api_key:
            return self._dummy_reviews()
        
        try:
            params = {
                "engine": "google_maps_reviews",
                "place_id": place_id,
                "api_key": self.api_key
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            reviews = []
            for review in results.get("reviews", [])[:limit]:
                reviews.append({
                    "author": review.get("user", {}).get("name"),
                    "rating": review.get("rating"),
                    "text": review.get("snippet"),
                    "date": review.get("date"),
                    "likes": review.get("likes", 0)
                })
            
            return reviews
        
        except Exception as e:
            logger.error(f"SerpAPI reviews error: {e}")
            return self._dummy_reviews()
    
    async def analyze_competitor_reviews(
        self,
        reviews: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze reviews to extract complaints and opportunities
        
        Returns:
            Analysis with complaints, strengths, opportunities
        """
        complaints = []
        strengths = []
        
        # Simple keyword-based analysis (in production, use LLM)
        complaint_keywords = ["out of stock", "expensive", "rude", "dirty", "closed", "late"]
        strength_keywords = ["fresh", "cheap", "friendly", "clean", "helpful"]
        
        for review in reviews:
            text = review.get("text") or ""
            text = text.lower() if text else ""
            rating = review.get("rating") or 5
            try:
                rating = int(rating)
            except (ValueError, TypeError):
                rating = 5
            
            if rating <= 3:
                for keyword in complaint_keywords:
                    if keyword in text:
                        complaints.append({
                            "keyword": keyword,
                            "review": text[:100],
                            "rating": rating
                        })
            
            if rating >= 4:
                for keyword in strength_keywords:
                    if keyword in text:
                        strengths.append({
                            "keyword": keyword,
                            "review": text[:100],
                            "rating": rating
                        })
        
        # Calculate average rating safely
        ratings = []
        for r in reviews:
            try:
                rating = r.get("rating")
                if rating is not None:
                    ratings.append(float(rating))
            except (ValueError, TypeError):
                pass
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        return {
            "total_reviews": len(reviews),
            "avg_rating": avg_rating,
            "complaints": complaints[:5],
            "strengths": strengths[:5],
            "opportunities": self._extract_opportunities(complaints)
        }
    
    def _extract_opportunities(self, complaints: List[Dict]) -> List[str]:
        """Convert complaints into actionable opportunities"""
        opportunities = []
        
        complaint_map = {
            "out of stock": "Keep extra stock of popular items",
            "expensive": "Offer competitive pricing",
            "rude": "Focus on friendly customer service",
            "dirty": "Maintain cleanliness",
            "closed": "Extend operating hours",
            "late": "Open earlier or close later"
        }
        
        seen_keywords = set()
        for complaint in complaints:
            keyword = complaint["keyword"]
            if keyword not in seen_keywords and keyword in complaint_map:
                opportunities.append(complaint_map[keyword])
                seen_keywords.add(keyword)
        
        return opportunities
    
    def _dummy_competitors(self) -> List[Dict[str, Any]]:
        """Return dummy competitor data"""
        return [
            {
                "name": "Kumar Stores",
                "address": "123 Main St, Chennai",
                "rating": 4.2,
                "reviews_count": 45,
                "place_id": "dummy_place_1",
                "phone": "+919876543210",
                "hours": "6 AM - 10 PM",
                "type": "Grocery store"
            },
            {
                "name": "Lakshmi Provision Store",
                "address": "456 Market Rd, Chennai",
                "rating": 3.8,
                "reviews_count": 32,
                "place_id": "dummy_place_2",
                "phone": "+919876543211",
                "hours": "7 AM - 9 PM",
                "type": "Grocery store"
            }
        ]
    
    def _dummy_reviews(self) -> List[Dict[str, Any]]:
        """Return dummy review data"""
        return [
            {
                "author": "Ramesh Kumar",
                "rating": 2,
                "text": "Always out of stock. Went for milk, not available.",
                "date": "2 days ago",
                "likes": 3
            },
            {
                "author": "Priya S",
                "rating": 5,
                "text": "Very friendly owner. Fresh vegetables daily.",
                "date": "1 week ago",
                "likes": 5
            }
        ]
    
    def _dummy_festivals(self) -> List[Dict[str, Any]]:
        """Return dummy festival data for Tamil Nadu"""
        return [
            {
                "name": "Pongal",
                "description": "Tamil harvest festival celebrated in January",
                "type": "religious",
                "suggested_items": ["Rice", "Jaggery", "Sugarcane", "Turmeric", "Banana leaves", "New pots"]
            },
            {
                "name": "Deepavali",
                "description": "Festival of lights celebrated in October/November",
                "type": "religious",
                "suggested_items": ["Sweets", "Crackers", "Diyas", "Decorations", "New clothes", "Snacks"]
            },
            {
                "name": "Navaratri",
                "description": "Nine-night festival celebrating goddess Durga",
                "type": "religious",
                "suggested_items": ["Flowers", "Fruits", "Coconuts", "Kumkum", "Sandalwood", "Lamps"]
            },
            {
                "name": "Tamil New Year",
                "description": "Tamil calendar new year in April",
                "type": "cultural",
                "suggested_items": ["Mango", "Neem flowers", "Raw banana", "Jaggery", "New vessels"]
            }
        ]
    
    def _dummy_trends(self) -> List[Dict[str, Any]]:
        """Return dummy market trend data"""
        return [
            {
                "title": "Rice prices stable in Tamil Nadu",
                "snippet": "Rice prices remain stable with good harvest season.",
                "trend": "stable"
            },
            {
                "title": "Vegetable prices rising due to monsoon",
                "snippet": "Tomato and onion prices increased by 20% this week.",
                "trend": "up"
            },
            {
                "title": "Cooking oil prices dropping",
                "snippet": "Sunflower and palm oil prices showing downward trend.",
                "trend": "down"
            }
        ]

