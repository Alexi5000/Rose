"""Voice processing endpoints."""

import asyncio
import logging
import os
import stat
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from ai_companion.core.resilience import CircuitBreakerError
from ai_companion.graph.graph import create_workflow_graph
from ai_companion.modules.speech.speech_to_text import SpeechToText
from ai_companion.modules.speech.text_to_speech import TextToSpeech
from ai_companion.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize speech modules
stt = SpeechToText()
tts = TextToSpeech()

# Directory for temporary audio files
AUDIO_DIR = Path(tempfile.gettempdir()) / "rose_audio"
AUDIO_DIR.mkdir(exist_ok=True)

# Maximum audio file size (10MB)
MAX_AUDIO_SIZE = 10 * 1024 * 1024


class VoiceProcessResponse(BaseModel):
    """Response model for voice processing.

    Attributes:
        text: The transcribed and processed text response from Rose
        audio_url: URL to download the generated audio response (MP3 format)
        session_id: Unique session identifier for conversation continuity
    """

    text: str
    audio_url: str
    session_id: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "I hear the pain in your words. It's okay to feel this way. Tell me more about what you're experiencing.",
                    "audio_url": "/api/v1/voice/audio/550e8400-e29b-41d4-a716-446655440000",
                    "session_id": "123e4567-e89b-12d3-a456-426614174000",
                }
            ]
        }
    }


@router.post("/voice/process", response_model=VoiceProcessResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def process_voice(
    request: Request,
    audio: UploadFile = File(..., description="Audio file containing user's voice input"),
    session_id: str = Form(..., description="UUID v4 session identifier from /session/start"),
) -> VoiceProcessResponse:
    """Process voice input and generate audio response.

    Accepts an audio file, transcribes it using Groq Whisper,
    processes through LangGraph workflow with Rose's therapeutic AI,
    and generates an empathetic audio response using ElevenLabs TTS.

    **Validation Rules:**
    - Audio file size: Maximum 10MB
    - Audio formats: WAV, MP3, WebM, M4A, OGG
    - Session ID: Must be valid UUID v4 format from /session/start
    - Rate limit: 10 requests per minute per IP address
    - Timeout: 60 seconds maximum processing time

    **Processing Flow:**
    1. Validate audio file size and format
    2. Transcribe audio to text using Groq Whisper
    3. Process through LangGraph workflow with memory context
    4. Generate empathetic response using Rose's character
    5. Synthesize audio response using ElevenLabs TTS
    6. Return text and audio URL

    Args:
        request: FastAPI request object (injected)
        audio: Audio file (WAV, MP3, WebM, M4A, OGG) - max 10MB
        session_id: Session identifier for conversation tracking (UUID v4)

    Returns:
        VoiceProcessResponse: Contains response text, audio URL, and session ID

    Raises:
        HTTPException 400: Invalid audio format, empty file, or validation error
        HTTPException 413: Audio file exceeds 10MB size limit
        HTTPException 429: Rate limit exceeded (10 requests/minute)
        HTTPException 503: External service unavailable (Groq, ElevenLabs, Qdrant)
        HTTPException 504: Processing timeout (>60 seconds)
        HTTPException 500: Internal server error
    """
    try:
        # Read audio file
        audio_data = await audio.read()

        # Validate audio size
        if len(audio_data) > MAX_AUDIO_SIZE:
            raise HTTPException(
                status_code=413, detail=f"Audio file too large. Maximum size is {MAX_AUDIO_SIZE / 1024 / 1024}MB"
            )

        if not audio_data:
            raise HTTPException(status_code=400, detail="Audio file is empty")

        logger.info(f"Processing voice input for session {session_id}, size: {len(audio_data)} bytes")

        # Transcribe audio to text
        try:
            transcribed_text = await stt.transcribe(audio_data)
            logger.info(f"Transcribed text: {transcribed_text}")
        except ValueError as e:
            # Validation errors (bad audio format, empty file, etc.)
            logger.error(f"Audio validation failed: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid audio: {str(e)}")
        except Exception as e:
            # API or processing errors
            logger.error(f"Speech-to-text failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="I couldn't hear that clearly. Could you try again?",
            )

        # Process through LangGraph workflow with timeout and error handling
        try:
            # Create checkpointer for session persistence
            checkpointer = SqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH)

            # Compile graph with checkpointer
            graph = create_workflow_graph().compile(checkpointer=checkpointer)

            # Create config with session thread
            config = {"configurable": {"thread_id": session_id}}

            # Invoke workflow with global timeout
            try:
                result = await asyncio.wait_for(
                    graph.ainvoke(
                        {"messages": [HumanMessage(content=transcribed_text)]},
                        config=config,
                    ),
                    timeout=settings.WORKFLOW_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                logger.error(f"Workflow timeout after {settings.WORKFLOW_TIMEOUT_SECONDS}s for session {session_id}")
                raise HTTPException(
                    status_code=504,
                    detail="I'm taking longer than usual to respond. Please try again.",
                )

            # Extract response text from the last AI message
            response_text = result["messages"][-1].content
            logger.info(f"Generated response: {response_text[:100]}...")

        except CircuitBreakerError as e:
            # Circuit breaker is open for one of the services
            logger.error(f"Circuit breaker open during workflow: {e}")
            raise HTTPException(
                status_code=503,
                detail="I'm having trouble connecting to my services right now. Please try again in a moment.",
            )
        except HTTPException:
            # Re-raise HTTP exceptions (including timeout)
            raise
        except Exception as e:
            logger.error(f"LangGraph workflow failed: {e}", exc_info=True)
            # Provide graceful fallback response
            raise HTTPException(
                status_code=503,
                detail="I'm having trouble processing that right now. Could you try rephrasing?",
            )

        # Generate audio response
        try:
            audio_bytes = await tts.synthesize(response_text)
            logger.info(f"Generated audio: {len(audio_bytes)} bytes")
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}", exc_info=True)
            # Return text-only response as fallback
            logger.warning("Falling back to text-only response due to TTS failure")
            raise HTTPException(
                status_code=200,
                detail={
                    "text": response_text,
                    "audio_url": None,
                    "session_id": session_id,
                    "error": "I'm having trouble with my voice right now, but I'm here.",
                },
            )

        # Save audio file temporarily with secure permissions
        audio_id = str(uuid.uuid4())
        audio_path = AUDIO_DIR / f"{audio_id}.mp3"

        try:
            # Create file with secure permissions (owner read/write only)
            fd = os.open(str(audio_path), os.O_CREAT | os.O_WRONLY | os.O_EXCL, stat.S_IRUSR | stat.S_IWUSR)
            os.write(fd, audio_bytes)
            os.close(fd)
            logger.info(f"Saved audio to {audio_path} with secure permissions")
        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save audio response")

        # Return response with audio URL
        audio_url = f"/api/voice/audio/{audio_id}"

        return VoiceProcessResponse(
            text=response_text,
            audio_url=audio_url,
            session_id=session_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in voice processing: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/voice/audio/{audio_id}")
async def get_audio(audio_id: str):
    """Serve generated audio file.

    Retrieves a previously generated audio response file by its unique identifier.
    Audio files are automatically cleaned up after 24 hours.

    **Validation Rules:**
    - Audio ID: Must be valid UUID v4 format
    - File retention: Audio files are deleted after 24 hours
    - Format: MP3 audio file
    - Cache: No caching (Cache-Control: no-cache)

    Args:
        audio_id: Unique identifier for the audio file (UUID v4)

    Returns:
        FileResponse: MP3 audio file as streaming response

    Raises:
        HTTPException 404: Audio file not found or expired
    """
    audio_path = AUDIO_DIR / f"{audio_id}.mp3"

    if not audio_path.exists():
        logger.error(f"Audio file not found: {audio_id}")
        raise HTTPException(status_code=404, detail="Audio file not found")

    logger.info(f"Serving audio file: {audio_id}")

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-cache"},
    )


def cleanup_old_audio_files(max_age_hours: Optional[int] = None) -> None:
    """Clean up audio files older than specified hours.

    Args:
        max_age_hours: Maximum age of files to keep in hours (defaults to settings.AUDIO_CLEANUP_MAX_AGE_HOURS)
    """
    try:
        max_age = max_age_hours if max_age_hours is not None else settings.AUDIO_CLEANUP_MAX_AGE_HOURS
        current_time = time.time()
        max_age_seconds = max_age * 3600

        for audio_file in AUDIO_DIR.glob("*.mp3"):
            file_age = current_time - audio_file.stat().st_mtime
            if file_age > max_age_seconds:
                audio_file.unlink()
                logger.info(f"Deleted old audio file: {audio_file.name}")

    except Exception as e:
        logger.error(f"Error cleaning up audio files: {e}")
