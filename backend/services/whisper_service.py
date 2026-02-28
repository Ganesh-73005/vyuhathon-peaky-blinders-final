from groq import Groq
from pathlib import Path
from typing import Optional
from config.settings import settings
from loguru import logger
import os

class WhisperService:
    """Service for speech-to-text using Groq Whisper API"""

    def __init__(self):
        self.client = None
        if settings.GROQ_API_KEY:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            logger.info("Groq Whisper client initialized")
        else:
            logger.warning("GROQ_API_KEY not set, using dummy mode")

    async def transcribe_audio(
        self,
        audio_path: str,
        language: str = "ta"  # Tamil
    ) -> dict:
        """
        Transcribe audio file to text using Groq Whisper

        Args:
            audio_path: Path to audio file
            language: Language code (ta for Tamil, en for English)

        Returns:
            Dict with 'text', 'language', 'confidence', and detailed segments
        """
        if not self.client:
            return self._dummy_transcription()

        try:
            # Read audio file
            with open(audio_path, "rb") as file:
                # Use Groq's Whisper API with verbose JSON response
                transcription = self.client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), file.read()),
                    model="whisper-large-v3-turbo",
                    temperature=0,
                    response_format="verbose_json",
                    language=language if language != "ta" else None  # Groq uses ISO codes
                )

            # Extract text and metadata
            text = transcription.text.strip()
            detected_language = getattr(transcription, 'language', language)

            # Calculate confidence from segments if available
            confidence = 85  # Default high confidence for Groq Whisper
            if hasattr(transcription, 'segments') and transcription.segments:
                # Average confidence from segments
                segment_confidences = []
                for segment in transcription.segments:
                    if hasattr(segment, 'avg_logprob'):
                        # Convert log probability to percentage
                        conf = min(100, max(0, (segment.avg_logprob + 1) * 100))
                        segment_confidences.append(conf)

                if segment_confidences:
                    confidence = int(sum(segment_confidences) / len(segment_confidences))

            logger.info(f"Transcribed audio: '{text[:50]}...' (confidence: {confidence}%)")

            return {
                "text": text,
                "language": detected_language,
                "confidence": confidence,
                "duration": getattr(transcription, 'duration', None),
                "segments": getattr(transcription, 'segments', [])
            }

        except Exception as e:
            logger.error(f"Groq Whisper transcription error: {e}")
            return self._dummy_transcription()

    def _dummy_transcription(self) -> dict:
        """Return dummy transcription when API not available"""
        return {
            "text": "20 samosa விற்றேன் 10 ரூபாய் விலை",
            "language": "ta",
            "confidence": 50,
            "dummy": True,
            "duration": None,
            "segments": []
        }

    async def detect_language(self, audio_path: str) -> str:
        """Detect language from audio"""
        result = await self.transcribe_audio(audio_path)
        return result.get("language", "ta")

