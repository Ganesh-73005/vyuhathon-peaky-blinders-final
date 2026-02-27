from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from config.settings import settings
from datetime import datetime, timedelta
import json

router = APIRouter()

# Hard-coded Tamil Nadu festivals with accurate dates and stock suggestions
TAMIL_FESTIVALS_2025_2026 = [
    {
        "name": "Pongal",
        "date": "January 14-17, 2026",
        "type": "harvest",
        "description": "Tamil harvest festival celebrating prosperity and thanksgiving",
        "suggested_items": [
            {"item": "Raw Rice", "category": "grocery", "priority": "high"},
            {"item": "Jaggery", "category": "grocery", "priority": "high"},
            {"item": "Sugarcane", "category": "produce", "priority": "high"},
            {"item": "Turmeric", "category": "spices", "priority": "high"},
            {"item": "New Earthen Pots", "category": "puja", "priority": "high"},
            {"item": "Banana Leaves", "category": "produce", "priority": "medium"},
            {"item": "Coconut", "category": "grocery", "priority": "high"},
            {"item": "Milk", "category": "dairy", "priority": "high"},
            {"item": "Ghee", "category": "dairy", "priority": "medium"},
            {"item": "Rangoli Colors", "category": "puja", "priority": "medium"}
        ]
    },
    {
        "name": "Thai Poosam",
        "date": "February 11, 2026",
        "type": "religious",
        "description": "Festival honoring Lord Murugan with kavadi processions",
        "suggested_items": [
            {"item": "Coconuts", "category": "puja", "priority": "high"},
            {"item": "Camphor", "category": "puja", "priority": "high"},
            {"item": "Flowers", "category": "puja", "priority": "high"},
            {"item": "Fruits", "category": "produce", "priority": "medium"},
            {"item": "Vibhuti", "category": "puja", "priority": "medium"},
            {"item": "Incense Sticks", "category": "puja", "priority": "medium"}
        ]
    },
    {
        "name": "Maha Shivaratri",
        "date": "February 26, 2026",
        "type": "religious",
        "description": "Night dedicated to Lord Shiva worship",
        "suggested_items": [
            {"item": "Milk", "category": "dairy", "priority": "high"},
            {"item": "Bilva Leaves", "category": "puja", "priority": "high"},
            {"item": "Fruits", "category": "produce", "priority": "high"},
            {"item": "Coconut", "category": "grocery", "priority": "high"},
            {"item": "Vibhuti", "category": "puja", "priority": "medium"},
            {"item": "Flowers", "category": "puja", "priority": "medium"}
        ]
    },
    {
        "name": "Tamil New Year (Puthandu)",
        "date": "April 14, 2026",
        "type": "cultural",
        "description": "Tamil calendar new year - start of Chithirai month",
        "suggested_items": [
            {"item": "Mango", "category": "produce", "priority": "high"},
            {"item": "Raw Mango", "category": "produce", "priority": "high"},
            {"item": "Neem Flowers", "category": "puja", "priority": "high"},
            {"item": "Jaggery", "category": "grocery", "priority": "high"},
            {"item": "New Vessels", "category": "household", "priority": "medium"},
            {"item": "Banana", "category": "produce", "priority": "medium"},
            {"item": "Coconut", "category": "grocery", "priority": "medium"}
        ]
    },
    {
        "name": "Chithirai Thiruvizha",
        "date": "April-May 2026",
        "type": "religious",
        "description": "Meenakshi Temple festival in Madurai",
        "suggested_items": [
            {"item": "Flowers", "category": "puja", "priority": "high"},
            {"item": "Coconuts", "category": "puja", "priority": "high"},
            {"item": "Fruits", "category": "produce", "priority": "medium"},
            {"item": "Sweets", "category": "food", "priority": "medium"}
        ]
    },
    {
        "name": "Aadi Perukku",
        "date": "August 2, 2026",
        "type": "cultural",
        "description": "Festival celebrating River Cauvery and water bodies",
        "suggested_items": [
            {"item": "Turmeric", "category": "grocery", "priority": "high"},
            {"item": "Kumkum", "category": "puja", "priority": "high"},
            {"item": "Banana Leaves", "category": "produce", "priority": "high"},
            {"item": "Coconuts", "category": "grocery", "priority": "high"},
            {"item": "Rice", "category": "grocery", "priority": "medium"},
            {"item": "Flowers", "category": "puja", "priority": "medium"}
        ]
    },
    {
        "name": "Vinayaka Chaturthi",
        "date": "September 7, 2026",
        "type": "religious",
        "description": "Birthday of Lord Ganesha",
        "suggested_items": [
            {"item": "Modak/Kozhukattai", "category": "food", "priority": "high"},
            {"item": "Coconuts", "category": "puja", "priority": "high"},
            {"item": "Durva Grass", "category": "puja", "priority": "high"},
            {"item": "Flowers", "category": "puja", "priority": "high"},
            {"item": "Fruits", "category": "produce", "priority": "high"},
            {"item": "Banana", "category": "produce", "priority": "high"},
            {"item": "Ganesha Idols", "category": "puja", "priority": "high"},
            {"item": "Camphor", "category": "puja", "priority": "medium"}
        ]
    },
    {
        "name": "Navaratri",
        "date": "October 2-10, 2026",
        "type": "religious",
        "description": "Nine nights festival celebrating Goddess Durga",
        "suggested_items": [
            {"item": "Kolu Dolls", "category": "puja", "priority": "high"},
            {"item": "Sundal Ingredients", "category": "grocery", "priority": "high"},
            {"item": "Flowers", "category": "puja", "priority": "high"},
            {"item": "Coconuts", "category": "grocery", "priority": "high"},
            {"item": "Fruits", "category": "produce", "priority": "high"},
            {"item": "Kumkum", "category": "puja", "priority": "high"},
            {"item": "Turmeric", "category": "grocery", "priority": "medium"},
            {"item": "Betel Leaves", "category": "puja", "priority": "medium"}
        ]
    },
    {
        "name": "Deepavali",
        "date": "October 21, 2026",
        "type": "religious",
        "description": "Festival of Lights - Victory of good over evil",
        "suggested_items": [
            {"item": "Sweets", "category": "food", "priority": "high"},
            {"item": "Savories/Snacks", "category": "food", "priority": "high"},
            {"item": "Firecrackers", "category": "festival", "priority": "high"},
            {"item": "Diyas/Lamps", "category": "puja", "priority": "high"},
            {"item": "Cooking Oil", "category": "grocery", "priority": "high"},
            {"item": "Gingelly Oil", "category": "grocery", "priority": "high"},
            {"item": "New Clothes", "category": "apparel", "priority": "medium"},
            {"item": "Gift Items", "category": "gifts", "priority": "medium"},
            {"item": "Rangoli Colors", "category": "puja", "priority": "medium"}
        ]
    },
    {
        "name": "Karthigai Deepam",
        "date": "November 29, 2026",
        "type": "religious",
        "description": "Festival of lamps celebrated in Tamil Nadu",
        "suggested_items": [
            {"item": "Oil Lamps", "category": "puja", "priority": "high"},
            {"item": "Gingelly Oil", "category": "grocery", "priority": "high"},
            {"item": "Cotton Wicks", "category": "puja", "priority": "high"},
            {"item": "Sweets", "category": "food", "priority": "medium"},
            {"item": "Flowers", "category": "puja", "priority": "medium"}
        ]
    }
]

class CompetitorSearchRequest(BaseModel):
    location: str = "Chennai"
    business_type: str = "kirana store"
    radius_km: int = 2

class InsightRequest(BaseModel):
    language: str = "english"
    user_id: str = "demo_user"
    shop_id: str = "demo_shop"

@router.get("/competitors")
async def get_competitors(
    location: str = "Chennai",
    business_type: str = "kirana store",
    radius_km: int = 2,
    request: Request = None
):
    """Search for nearby competitors"""
    try:
        serpapi_service = request.app.state.serpapi_service
        competitors = await serpapi_service.search_nearby_competitors(
            location=location,
            business_type=business_type,
            radius_km=radius_km
        )
        return {
            "count": len(competitors),
            "competitors": competitors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/competitors/{place_id}/reviews")
async def get_competitor_reviews(
    place_id: str,
    limit: int = 20,
    request: Request = None
):
    """Get reviews for a competitor"""
    try:
        serpapi_service = request.app.state.serpapi_service
        reviews = await serpapi_service.get_reviews(place_id, limit)
        analysis = await serpapi_service.analyze_competitor_reviews(reviews)
        
        return {
            "place_id": place_id,
            "reviews": reviews,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_business_summary(
    user_id: str = "demo_user",
    shop_id: str = "demo_shop",
    language: str = "english",
    request: Request = None
):
    """Get AI-generated business summary with user context"""
    from models.transaction import Transaction, TransactionType
    from models.user import User
    from models.stock import StockItem
    from loguru import logger

    try:
        # Get user profile
        user = await User.find_one(User.user_id == user_id)
        shop_name = user.shop_name if user else "Your Shop"
        business_type = user.business_type.value if user else "kirana"

        logger.info(f"Business summary for {shop_name} ({business_type})")

        # Get last 7 days data
        start_date = datetime.now() - timedelta(days=7)

        transactions = await Transaction.find(
            Transaction.user_id == user_id,
            Transaction.shop_id == shop_id,
            Transaction.timestamp >= start_date
        ).to_list()

        # Get stock data
        stock_items = await StockItem.find(
            StockItem.user_id == user_id,
            StockItem.shop_id == shop_id
        ).to_list()

        total_sales = sum(t.total_amount for t in transactions if t.type == TransactionType.SALE)
        total_transactions = len([t for t in transactions if t.type == TransactionType.SALE])
        total_stock_value = sum(s.current_stock * s.selling_price for s in stock_items)
        low_stock_count = sum(1 for s in stock_items if s.current_stock < s.reorder_point)

        data = {
            "shop_name": shop_name,
            "business_type": business_type,
            "total_sales": total_sales,
            "total_transactions": total_transactions,
            "avg_transaction": total_sales / total_transactions if total_transactions > 0 else 0,
            "total_stock_value": total_stock_value,
            "low_stock_count": low_stock_count,
            "stock_items_count": len(stock_items),
            "period": "7 days"
        }

        # Generate business-type specific insight
        if total_transactions > 0:
            insight = {
                "english": f"{shop_name} ({business_type}) made ₹{total_sales:,.0f} from {total_transactions} sales in the last 7 days. Average transaction: ₹{data['avg_transaction']:,.0f}. Stock value: ₹{total_stock_value:,.0f}.",
                "tamil": f"{shop_name} ({business_type}) கடந்த 7 நாட்களில் {total_transactions} விற்பனைகளில் இருந்து ₹{total_sales:,.0f} சம்பாதித்தது. சராசரி: ₹{data['avg_transaction']:,.0f}. சரக்கு மதிப்பு: ₹{total_stock_value:,.0f}."
            }

            if low_stock_count > 0:
                insight["english"] += f" ⚠️ {low_stock_count} items need restocking."
                insight["tamil"] += f" ⚠️ {low_stock_count} பொருட்கள் மீண்டும் சேர்க்க வேண்டும்."
        else:
            insight = {
                "english": f"{shop_name} - No sales recorded in the last 7 days. Start recording your sales to see insights!",
                "tamil": f"{shop_name} - கடந்த 7 நாட்களில் விற்பனை பதிவு இல்லை. நுண்ணறிவுகளைக் காண விற்பனையைப் பதிவு செய்யுங்கள்!"
            }

        return {
            "data": data,
            "insight": insight,
            "language": language
        }
    except Exception as e:
        logger.error(f"Business summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate")
async def translate_text(
    text: str,
    source_lang: str = "english",
    target_lang: str = "tamil",
    request: Request = None
):
    """Translate text between English and Tamil using Groq LLM"""
    try:
        groq_service = request.app.state.groq_service
        
        system_prompt = f"""You are a professional translator. Translate the following text from {source_lang} to {target_lang}.
Keep the translation natural and conversational. Only return the translated text, nothing else."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        
        translation = await groq_service.chat_completion(messages, temperature=0.3)
        
        return {
            "original": text,
            "translated": translation.strip(),
            "source_lang": source_lang,
            "target_lang": target_lang
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/festivals")
async def get_upcoming_festivals(
    location: str = "Tamil Nadu",
    days_ahead: int = 90,
    user_id: str = "demo_user",
    request: Request = None
):
    """Get upcoming local festivals with business-type specific stock suggestions"""
    from models.user import User
    from loguru import logger

    try:
        # Get user profile for business type
        user = await User.find_one(User.user_id == user_id)
        business_type = user.business_type.value if user else "kirana"

        logger.info(f"Festival suggestions for business_type: {business_type}")

        # Get current date
        today = datetime.now()

        # Filter festivals within the next N days
        upcoming = []
        for festival in TAMIL_FESTIVALS_2025_2026:
            # Filter suggested items based on business type
            filtered_items = _filter_items_by_business_type(
                festival["suggested_items"],
                business_type
            )

            if filtered_items:  # Only include if there are relevant items
                upcoming.append({
                    "name": festival["name"],
                    "date": festival["date"],
                    "type": festival["type"],
                    "description": festival["description"],
                    "suggested_items": filtered_items,
                    "days_until": "Check calendar for exact date",
                    "relevance": _calculate_festival_relevance(festival, business_type)
                })

        # Sort by relevance
        upcoming.sort(key=lambda x: x["relevance"], reverse=True)

        return {
            "location": location,
            "business_type": business_type,
            "count": len(upcoming),
            "festivals": upcoming[:6]  # Return next 6 festivals
        }
    except Exception as e:
        logger.error(f"Festival fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _filter_items_by_business_type(items: List[dict], business_type: str) -> List[dict]:
    """Filter festival items based on business type"""

    # Business type to category mapping
    business_categories = {
        "kirana": ["grocery", "puja", "dairy", "spices", "household"],
        "bakery": ["food", "dairy", "grocery"],
        "hotel": ["food", "grocery", "dairy"],
        "restaurant": ["food", "grocery", "dairy", "spices"],
        "pharmacy": ["household", "puja"],  # Limited relevance
        "supermarket": ["grocery", "puja", "dairy", "food", "household", "spices", "produce", "festival", "apparel", "gifts"],
        "general_store": ["grocery", "puja", "household", "festival", "gifts"],
        "vegetable_shop": ["produce", "grocery"],
        "fruit_shop": ["produce", "grocery"],
        "other": ["grocery", "puja", "food"]
    }

    relevant_categories = business_categories.get(business_type, ["grocery", "food"])

    # Filter items
    filtered = [
        item for item in items
        if item.get("category") in relevant_categories
    ]

    return filtered

def _calculate_festival_relevance(festival: dict, business_type: str) -> int:
    """Calculate how relevant a festival is to a business type (0-100)"""

    # Base relevance by business type
    relevance_map = {
        "kirana": {"religious": 90, "harvest": 85, "cultural": 80},
        "bakery": {"religious": 70, "harvest": 60, "cultural": 65},
        "hotel": {"religious": 60, "harvest": 50, "cultural": 55},
        "restaurant": {"religious": 65, "harvest": 55, "cultural": 60},
        "pharmacy": {"religious": 30, "harvest": 20, "cultural": 25},
        "supermarket": {"religious": 95, "harvest": 90, "cultural": 85},
        "general_store": {"religious": 85, "harvest": 80, "cultural": 75},
        "vegetable_shop": {"religious": 70, "harvest": 90, "cultural": 65},
        "fruit_shop": {"religious": 70, "harvest": 90, "cultural": 65},
        "other": {"religious": 70, "harvest": 65, "cultural": 60}
    }

    festival_type = festival.get("type", "cultural")
    business_relevance = relevance_map.get(business_type, {"religious": 70, "harvest": 65, "cultural": 60})

    return business_relevance.get(festival_type, 50)

@router.get("/competitors/detailed")
async def get_detailed_competitor_analysis(
    location: str = "Chennai",
    business_type: str = "kirana store",
    user_id: str = "demo_user",
    request: Request = None
):
    """Get detailed competitor analysis with business-type specific insights"""
    from models.user import User
    from loguru import logger

    try:
        # Get user profile
        user = await User.find_one(User.user_id == user_id)
        user_business_type = user.business_type.value if user else "kirana"
        shop_name = user.shop_name if user else "Your Shop"

        # Override business_type with user's actual business type
        search_business_type = f"{user_business_type} store"

        logger.info(f"Competitor analysis for {shop_name} ({user_business_type}) in {location}")

        serpapi_service = request.app.state.serpapi_service

        # Get competitors
        competitors = await serpapi_service.search_nearby_competitors(
            location=location,
            business_type=search_business_type,
            radius_km=3
        )

        detailed_analysis = []
        for comp in competitors[:5]:  # Analyze top 5
            # Get reviews with proper error handling
            place_id = comp.get("place_id") or ""
            reviews = await serpapi_service.get_reviews(place_id, limit=10) if place_id else []
            analysis = await serpapi_service.analyze_competitor_reviews(reviews)

            # Safely get rating
            rating = comp.get("rating")
            if rating is None:
                rating = 0
            try:
                rating = float(rating)
            except (ValueError, TypeError):
                rating = 0

            threat_level = "high" if rating > 4.0 else "medium" if rating > 3.5 else "low"

            detailed_analysis.append({
                "competitor": comp,
                "review_analysis": analysis,
                "threat_level": threat_level
            })

        # Generate business-type specific strategic insights
        strategic_insights = _generate_business_specific_insights(user_business_type, len(competitors))

        return {
            "location": location,
            "business_type": user_business_type,
            "shop_name": shop_name,
            "competitor_count": len(detailed_analysis),
            "competitors": detailed_analysis,
            "strategic_insights": strategic_insights
        }
    except Exception as e:
        logger.error(f"Competitor analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _generate_business_specific_insights(business_type: str, competitor_count: int) -> dict:
    """Generate strategic insights specific to business type"""

    # Business-type specific insights
    insights_map = {
        "kirana": {
            "key_opportunities": [
                "Stock essential groceries that competitors run out of",
                "Offer home delivery for elderly customers",
                "Maintain longer operating hours (6 AM - 10 PM)",
                "Stock local/regional specialty items",
                "Provide credit facility to regular customers",
                "Keep fresh vegetables and fruits daily"
            ],
            "recommended_actions": [
                "Survey regular customers about unmet needs",
                "Monitor competitor pricing on rice, dal, oil",
                "Maintain cleanliness and organization",
                "Build personal relationships with customers",
                "Stock festival items 2 weeks in advance"
            ],
            "pricing_insights": "Match competitor pricing on essentials (rice, dal, oil), add 10-15% margin on convenience items",
            "service_gaps_to_exploit": [
                "Quick checkout",
                "Product freshness",
                "Personal service",
                "Credit for regulars"
            ]
        },
        "bakery": {
            "key_opportunities": [
                "Offer fresh bread and pastries daily",
                "Introduce custom cake orders",
                "Provide breakfast combos",
                "Stock evening snacks",
                "Offer sugar-free options"
            ],
            "recommended_actions": [
                "Maintain consistent quality",
                "Introduce new items weekly",
                "Offer loyalty cards",
                "Partner with offices for bulk orders",
                "Use social media for promotions"
            ],
            "pricing_insights": "Premium pricing for fresh items, competitive for packaged goods",
            "service_gaps_to_exploit": [
                "Freshness guarantee",
                "Custom orders",
                "Quick service",
                "Variety"
            ]
        },
        "hotel": {
            "key_opportunities": [
                "Offer diverse menu options",
                "Provide quick service for lunch crowd",
                "Introduce combo meals",
                "Offer home delivery",
                "Maintain hygiene standards"
            ],
            "recommended_actions": [
                "Monitor food quality consistently",
                "Train staff for better service",
                "Collect customer feedback",
                "Optimize kitchen operations",
                "Maintain competitive pricing"
            ],
            "pricing_insights": "Value-for-money combos, premium for special dishes",
            "service_gaps_to_exploit": [
                "Fast service",
                "Cleanliness",
                "Taste consistency",
                "Portion sizes"
            ]
        },
        "restaurant": {
            "key_opportunities": [
                "Create signature dishes",
                "Offer family meal packages",
                "Provide catering services",
                "Introduce seasonal specials",
                "Maintain ambiance"
            ],
            "recommended_actions": [
                "Focus on food presentation",
                "Train staff for hospitality",
                "Collect reviews and feedback",
                "Optimize menu based on sales",
                "Create social media presence"
            ],
            "pricing_insights": "Premium for ambiance and service, competitive for takeaway",
            "service_gaps_to_exploit": [
                "Unique dishes",
                "Ambiance",
                "Service quality",
                "Consistency"
            ]
        },
        "pharmacy": {
            "key_opportunities": [
                "Stock essential medicines always",
                "Offer home delivery for elderly",
                "Provide health consultations",
                "Stock wellness products",
                "Maintain 24/7 availability"
            ],
            "recommended_actions": [
                "Ensure medicine availability",
                "Train staff on product knowledge",
                "Maintain proper storage",
                "Build trust with doctors",
                "Offer health camps"
            ],
            "pricing_insights": "Competitive on generic medicines, standard on branded",
            "service_gaps_to_exploit": [
                "Availability",
                "Expert advice",
                "Home delivery",
                "Trust"
            ]
        },
        "supermarket": {
            "key_opportunities": [
                "Stock wide variety of products",
                "Offer weekly promotions",
                "Provide loyalty programs",
                "Maintain fresh produce section",
                "Offer online ordering"
            ],
            "recommended_actions": [
                "Monitor inventory levels",
                "Analyze sales patterns",
                "Optimize shelf space",
                "Train staff for customer service",
                "Implement POS system"
            ],
            "pricing_insights": "Competitive on staples, premium on imported/specialty items",
            "service_gaps_to_exploit": [
                "Product variety",
                "Organized layout",
                "Quick billing",
                "Parking facility"
            ]
        },
        "vegetable_shop": {
            "key_opportunities": [
                "Source fresh vegetables daily",
                "Offer organic options",
                "Provide pre-cut vegetables",
                "Stock seasonal specialties",
                "Offer home delivery"
            ],
            "recommended_actions": [
                "Maintain freshness standards",
                "Reduce wastage",
                "Build supplier relationships",
                "Offer competitive pricing",
                "Display products attractively"
            ],
            "pricing_insights": "Competitive on staples (onion, tomato, potato), premium on exotic vegetables",
            "service_gaps_to_exploit": [
                "Freshness",
                "Variety",
                "Fair pricing",
                "Quality"
            ]
        },
        "fruit_shop": {
            "key_opportunities": [
                "Stock seasonal fruits",
                "Offer fruit baskets",
                "Provide juice services",
                "Stock exotic fruits",
                "Offer gift packaging"
            ],
            "recommended_actions": [
                "Maintain fruit quality",
                "Reduce wastage through pricing",
                "Build supplier network",
                "Offer tasting samples",
                "Create attractive displays"
            ],
            "pricing_insights": "Dynamic pricing based on freshness, premium for exotic fruits",
            "service_gaps_to_exploit": [
                "Freshness",
                "Variety",
                "Quality assurance",
                "Presentation"
            ]
        }
    }

    # Get insights for business type or use kirana as default
    insights = insights_map.get(business_type, insights_map["kirana"])

    # Add threat assessment
    insights["overall_threat_assessment"] = "high" if competitor_count > 5 else "medium" if competitor_count > 2 else "low"

    return insights

@router.get("/market-trends")
async def get_market_trends(
    location: str = "Chennai",
    category: str = "grocery",
    request: Request = None
):
    """Get market trends and pricing insights"""
    try:
        # Return static market trends (no external API dependency)
        trends = [
            {
                "title": "Rice Prices",
                "status": "stable",
                "change": "+2%",
                "insight": "Good harvest season keeping prices stable"
            },
            {
                "title": "Cooking Oil",
                "status": "decreasing",
                "change": "-5%",
                "insight": "Palm oil prices dropping globally"
            },
            {
                "title": "Pulses (Dal)",
                "status": "increasing",
                "change": "+8%",
                "insight": "Lower production affecting prices"
            },
            {
                "title": "Vegetables",
                "status": "seasonal",
                "change": "varies",
                "insight": "Prices fluctuate with monsoon patterns"
            },
            {
                "title": "Sugar",
                "status": "stable",
                "change": "0%",
                "insight": "Government controls maintaining prices"
            }
        ]
        
        recommendations = [
            "Stock up on cooking oil now while prices are low",
            "Consider buying pulses in bulk before further increase",
            "Maintain fresh vegetable inventory carefully to reduce waste",
            "Monitor sugar prices before festival season"
        ]
        
        return {
            "location": location,
            "category": category,
            "trends": trends,
            "recommendations": recommendations,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
