import httpx
from typing import Optional
from config.settings import settings
from loguru import logger
import tempfile
import os
import uuid
from datetime import datetime

class CartesiaService:
    """Service for text-to-speech using Cartesia Voice API"""

    def __init__(self):
        self.api_key = settings.CARTESIA_API_KEY
        self.base_url = "https://api.cartesia.ai/tts/bytes"
        self.client = httpx.AsyncClient(timeout=30.0)

        # Voice IDs for Tamil and English from settings
        self.voice_ids = {
            "tamil": settings.CARTESIA_VOICE_TAMIL,
            "english": settings.CARTESIA_VOICE_ENGLISH
        }

    async def text_to_speech(
        self,
        text: str,
        language: str = "tamil",
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Convert text to speech using Cartesia API

        Args:
            text: Text to convert
            language: Language ("tamil" or "english")
            output_path: Path to save audio file

        Returns:
            Path to generated audio file or None
        """
        if not self.api_key:
            logger.warning("Cartesia API key not configured")
            return self._dummy_audio(text, output_path)

        try:
            # Select voice ID based on language
            voice_id = self.voice_ids.get(language, self.voice_ids["tamil"])

            # Prepare request payload
            payload = {
                "model_id": "sonic-3",
                "transcript": text,
                "voice": {
                    "mode": "id",
                    "id": voice_id
                },
                "output_format": {
                    "container": "wav",
                    "encoding": "pcm_f32le",
                    "sample_rate": 44100
                },
                "speed": "normal",
                "generation_config": {
                    "speed": 1,
                    "volume": 1
                }
            }

            # Make API request
            response = await self.client.post(
                self.base_url,
                headers={
                    "Cartesia-Version": "2025-04-16",
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if response.status_code == 200:
                # Save audio file to uploads directory
                if not output_path:
                    # Create unique filename in uploads directory
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_id = str(uuid.uuid4())[:8]
                    filename = f"audio_{timestamp}_{unique_id}.wav"
                    output_path = settings.UPLOAD_DIR / filename

                with open(output_path, "wb") as f:
                    f.write(response.content)

                logger.info(f"Generated TTS audio: {output_path} ({language})")

                # Return URL path instead of file system path
                return f"/uploads/{output_path.name}"
            else:
                logger.error(f"Cartesia API error: {response.status_code} - {response.text}")
                return self._dummy_audio(text, output_path)

        except Exception as e:
            logger.error(f"TTS error: {e}")
            return self._dummy_audio(text, output_path)

    async def generate_voice_response(
        self,
        text_english: str,
        text_tamil: str,
        prefer_tamil: bool = True
    ) -> Optional[str]:
        """Generate voice response in preferred language"""

        text = text_tamil if prefer_tamil and text_tamil else text_english
        language = "tamil" if prefer_tamil and text_tamil else "english"

        logger.info(f"Voice generation: prefer_tamil={prefer_tamil}, selected_language={language}")
        logger.info(f"Text (first 50 chars): {text[:50]}...")

        return await self.text_to_speech(text, language)

    def _dummy_audio(self, text: str, output_path: Optional[str]) -> Optional[str]:
        """Generate dummy audio file (silent or beep)"""
        logger.warning(f"Cartesia API not configured, skipping TTS for: {text[:50]}...")
        return None

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

