from services.serpapi_service import SerpAPIService

class CompetitorIntelligenceAgent:
    """Agent for competitor analysis"""
    def __init__(self, serpapi_service: SerpAPIService):
        self.serpapi = serpapi_service
