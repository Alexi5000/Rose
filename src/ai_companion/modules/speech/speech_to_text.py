import logging
import os
import tempfile
import time
from typing import Optional

from groq import Groq

from ai_companion.core.exceptions import SpeechToTextError
from ai_companion.settings import settings

logger = logging.getLogger(__name__)


class SpeechToText:
    """A class to handle speech-to-text conversion using Groq's Whisper model."""

    # Required environment variables
    REQUIRED_ENV_VARS = ["GROQ_API_KEY"]

    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1.0  # seconds
    MAX_BACKOFF = 10.0  # seconds
    TIMEOUT = 60  # seconds

    # Supported audio formats
    SUPPORTED_FORMATS = [".wav", ".mp3", ".webm", ".m4a", ".ogg", ".flac"]

    def __init__(self):
        """Initialize the SpeechToText class and validate environment variables."""
        self._validate_env_vars()
        self._client: Optional[Groq] = None

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    @property
    def client(self) -> Groq:
        """Get or create Groq client instance using singleton pattern."""
        if self._client is None:
            self._client = Groq(api_key=settings.GROQ_API_KEY, timeout=self.TIMEOUT)
        return self._client

    def _detect_audio_format(self, audio_data: bytes) -> str:
        """Detect audio format from file header.

        Args:
            audio_data: Binary audio data

        Returns:
            str: File extension (e.g., '.wav', '.mp3')
        """
        # Check for common audio file signatures
        if audio_data[:4] == b"RIFF" and audio_data[8:12] == b"WAVE":
            return ".wav"
        elif audio_data[:3] == b"ID3" or audio_data[:2] == b"\xff\xfb" or audio_data[:2] == b"\xff\xf3":
            return ".mp3"
        elif audio_data[:4] == b"OggS":
            return ".ogg"
        elif audio_data[:4] == b"fLaC":
            return ".flac"
        elif len(audio_data) > 8 and audio_data[4:8] == b"ftyp":
            return ".m4a"
        else:
            # Default to wav if format cannot be detected
            logger.warning("Could not detect audio format, defaulting to .wav")
            return ".wav"

    async def transcribe(self, audio_data: bytes, audio_format: Optional[str] = None) -> str:
        """Convert speech to text using Groq's Whisper model with retry logic.

        Args:
            audio_data: Binary audio data
            audio_format: Optional audio format (e.g., 'wav', 'mp3'). If not provided, will be auto-detected.

        Returns:
            str: Transcribed text

        Raises:
            ValueError: If the audio file is empty or invalid
            SpeechToTextError: If the transcription fails after all retries
        """
        if not audio_data:
            raise ValueError("Audio data cannot be empty")

        # Validate audio size (max 25MB for Groq Whisper)
        max_size = 25 * 1024 * 1024
        if len(audio_data) > max_size:
            raise ValueError(f"Audio file too large. Maximum size is {max_size / 1024 / 1024}MB")

        # Determine file extension
        if audio_format:
            file_ext = f".{audio_format.lstrip('.')}"
            if file_ext not in self.SUPPORTED_FORMATS:
                logger.warning(f"Unsupported format {file_ext}, attempting anyway")
        else:
            file_ext = self._detect_audio_format(audio_data)

        logger.info(f"Transcribing audio: size={len(audio_data)} bytes, format={file_ext}")

        # Retry loop with exponential backoff
        last_exception = None
        for attempt in range(self.MAX_RETRIES):
            try:
                # Create a temporary file with appropriate extension
                with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
                    temp_file.write(audio_data)
                    temp_file_path = temp_file.name

                try:
                    # Open the temporary file for the API request
                    with open(temp_file_path, "rb") as audio_file:
                        logger.info(f"Attempt {attempt + 1}/{self.MAX_RETRIES}: Calling Groq Whisper API")

                        transcription = self.client.audio.transcriptions.create(
                            file=audio_file,
                            model=settings.STT_MODEL_NAME,
                            language="en",
                            response_format="text",
                        )

                    if not transcription:
                        raise SpeechToTextError("Transcription result is empty")

                    logger.info(f"Transcription successful: {transcription[:100]}...")
                    return transcription

                finally:
                    # Clean up the temporary file
                    try:
                        os.unlink(temp_file_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup temp file: {cleanup_error}")

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt + 1}/{self.MAX_RETRIES} failed: {type(e).__name__}: {str(e)}",
                    exc_info=attempt == self.MAX_RETRIES - 1,  # Full traceback on last attempt
                )

                # Don't retry on validation errors
                if isinstance(e, ValueError):
                    raise

                # If not the last attempt, wait with exponential backoff
                if attempt < self.MAX_RETRIES - 1:
                    backoff_time = min(self.INITIAL_BACKOFF * (2**attempt), self.MAX_BACKOFF)
                    logger.info(f"Retrying in {backoff_time:.1f} seconds...")
                    time.sleep(backoff_time)

        # All retries exhausted
        error_msg = f"Speech-to-text conversion failed after {self.MAX_RETRIES} attempts"
        if last_exception:
            error_msg += f": {str(last_exception)}"
        logger.error(error_msg)
        raise SpeechToTextError(error_msg) from last_exception
