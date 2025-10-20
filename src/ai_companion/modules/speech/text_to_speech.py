import logging
import os
from typing import Optional

from ai_companion.core.exceptions import TextToSpeechError
from ai_companion.settings import settings
from elevenlabs import ElevenLabs, Voice, VoiceSettings

logger = logging.getLogger(__name__)


class TextToSpeech:
    """A class to handle text-to-speech conversion using ElevenLabs."""

    # Required environment variables
    REQUIRED_ENV_VARS = ["ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID"]

    def __init__(self):
        """Initialize the TextToSpeech class and validate environment variables."""
        self._validate_env_vars()
        self._client: Optional[ElevenLabs] = None

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    @property
    def client(self) -> ElevenLabs:
        """Get or create ElevenLabs client instance using singleton pattern."""
        if self._client is None:
            self._client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        return self._client

    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """Convert text to speech using ElevenLabs.

        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID to override default (useful for Rose-specific voice)

        Returns:
            bytes: Audio data

        Raises:
            ValueError: If the input text is empty or too long
            TextToSpeechError: If the text-to-speech conversion fails
        """
        if not text.strip():
            raise ValueError("Input text cannot be empty")

        if len(text) > 5000:  # ElevenLabs typical limit
            raise ValueError("Input text exceeds maximum length of 5000 characters")

        # Use Rose-specific voice if configured, otherwise use default
        selected_voice_id = voice_id or settings.ROSE_VOICE_ID or settings.ELEVENLABS_VOICE_ID

        logger.info(f"Synthesizing speech: {len(text)} chars, voice_id={selected_voice_id}")

        try:
            audio_generator = self.client.generate(
                text=text,
                voice=Voice(
                    voice_id=selected_voice_id,
                    settings=VoiceSettings(
                        stability=0.6,  # Higher stability for calming effect
                        similarity_boost=0.5,
                    ),
                ),
                model=settings.TTS_MODEL_NAME,
            )

            # Convert generator to bytes
            audio_bytes = b"".join(audio_generator)
            if not audio_bytes:
                raise TextToSpeechError("Generated audio is empty")

            logger.info(f"Successfully generated {len(audio_bytes)} bytes of audio")
            return audio_bytes

        except ValueError:
            # Re-raise validation errors
            logger.error(f"TTS validation error: {text[:50]}...")
            raise
        except Exception as e:
            logger.error(f"TTS conversion failed: {type(e).__name__}: {str(e)}", exc_info=True)
            raise TextToSpeechError(f"Text-to-speech conversion failed: {str(e)}") from e
