from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel
from typing import Optional
import shutil
from pathlib import Path
from config.settings import settings
from loguru import logger

router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    user_id: str = "demo_user"
    shop_id: str = "demo_shop"
    language: str = "english"  # Default to English instead of Tamil
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    response_tamil: Optional[str] = None
    audio_url: Optional[str] = None
    conversation_id: str
    data: Optional[dict] = None
    show_table: Optional[bool] = None
    table_data: Optional[dict] = None
    pending_data: Optional[dict] = None
    success: Optional[bool] = None

@router.post("/message", response_model=ChatResponse)
async def send_message(message: ChatMessage, request: Request):
    """
    Send a text message to Hisaab
    
    Example:
    ```json
    {
        "message": "sold 20 samosas 10 each",
        "user_id": "demo_user",
        "shop_id": "demo_shop",
        "language": "tamil"
    }
    ```
    """
    try:
        orchestrator = request.app.state.orchestrator
        
        result = await orchestrator.process_message(
            user_input=message.message,
            user_id=message.user_id,
            shop_id=message.shop_id,
            input_type="text",
            language=message.language,
            conversation_id=message.conversation_id
        )
        
        return ChatResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice", response_model=ChatResponse)
async def send_voice(
    audio: UploadFile = File(...),
    user_id: str = Form("demo_user"),
    shop_id: str = Form("demo_shop"),
    language: str = Form("english"),  # Default to English instead of Tamil
    conversation_id: Optional[str] = Form(None),
    request: Request = None
):
    """
    Send a voice message to Hisaab

    Upload an audio file (mp3, wav, m4a, etc.)
    """
    try:
        logger.info(f"Voice request - user_id: {user_id}, shop_id: {shop_id}, language: {language}")

        # Save uploaded audio
        audio_path = settings.UPLOAD_DIR / f"voice_{user_id}_{audio.filename}"
        with audio_path.open("wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        # Transcribe audio
        whisper_service = request.app.state.whisper_service
        transcription = await whisper_service.transcribe_audio(
            str(audio_path),
            language="ta" if language == "tamil" else "en"
        )
        
        # Process transcribed text
        orchestrator = request.app.state.orchestrator
        result = await orchestrator.process_message(
            user_input=transcription["text"],
            user_id=user_id,
            shop_id=shop_id,
            input_type="voice",
            language=language,
            conversation_id=conversation_id
        )
        
        # Clean up uploaded file
        audio_path.unlink()
        
        return ChatResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    from models.conversation import Conversation
    
    try:
        conversation = await Conversation.get(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "conversation_id": str(conversation.id),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "content_tamil": msg.content_tamil,
                    "timestamp": msg.timestamp.isoformat(),
                    "audio_url": msg.audio_url
                }
                for msg in conversation.messages
            ],
            "started_at": conversation.started_at.isoformat(),
            "last_message_at": conversation.last_message_at.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

