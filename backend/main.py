from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from loguru import logger
import sys
import os
from pathlib import Path

from config.settings import settings
from models import (
    Transaction, StockItem, CustomerProfile, LedgerEntry,
    MemoryRecord, Alert, Conversation
)
from models.user import User
from services import GroqService, WhisperService, CartesiaService, SerpAPIService
from agents.orchestrator_v2 import MasterOrchestrator
from api import chat, transactions, stock, analytics, alerts, insights, auth, pdf

# Configure logging
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)
try:
    Path(settings.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    logger.add(settings.LOG_FILE, rotation="1 day", retention="30 days", level=settings.LOG_LEVEL)
except Exception as e:
    logger.warning(f"Could not set up file logging: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    
    # Startup
    logger.info("Starting Hisaab backend...")
    
    # Initialize MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.MONGODB_DB_NAME]
    
    await init_beanie(
        database=database,
        document_models=[
            Transaction,
            StockItem,
            CustomerProfile,
            LedgerEntry,
            MemoryRecord,
            Alert,
            Conversation,
            User
        ]
    )
    
    logger.info("Database initialized")
    
    # Create upload directory
    try:
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"Could not create upload dir: {e}")
    
    # Initialize services
    app.state.groq_service = GroqService()
    app.state.whisper_service = WhisperService()
    app.state.cartesia_service = CartesiaService()
    app.state.serpapi_service = SerpAPIService()
    
    # Initialize orchestrator
    app.state.orchestrator = MasterOrchestrator(
        app.state.groq_service,
        app.state.whisper_service,
        app.state.cartesia_service
    )
    
    logger.info("Services initialized")
    logger.info(f"Hisaab backend started on {settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Hisaab backend...")
    await app.state.cartesia_service.close()
    client.close()

# Create FastAPI app
app = FastAPI(
    title="Hisaab API",
    description="AI-First Fintech Intelligence for Kirana Stores",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads only if directory exists
try:
    if settings.UPLOAD_DIR.exists():
        app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")
except Exception as e:
    logger.warning(f"Could not mount uploads: {e}")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(stock.router, prefix="/api/stock", tags=["Stock"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(insights.router, prefix="/api/insights", tags=["Insights"])
app.include_router(pdf.router, prefix="/api/pdf", tags=["PDF"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "groq": bool(settings.GROQ_API_KEY),
            "whisper": True,
            "cartesia": bool(settings.CARTESIA_API_KEY),
            "serpapi": bool(settings.SERPAPI_KEY)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )

