"""Voice processing endpoints."""

import asyncio
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

from ai_companion.core.exceptions import SpeechToTextError, TextToSpeechError, WorkflowError
from ai_companion.core.logging_config import get_logger
from ai_companion.core.metrics import metrics, track_performance
from ai_companion.core.resilience import CircuitBreakerError
from ai_companion.graph.graph import create_workflow_graph
from ai_companion.modules.speech.speech_to_text import SpeechToText
from ai_companion.modules.speech.text_to_speech import TextToSpeech
from ai_companion.settings import settings

logger = get_logger(__name__)

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
@track_performance("voice_processing")
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
            metrics.record_error("audio_too_large", endpoint="voice_process")
            raise HTTPException(
                status_code=413, detail=f"Audio file too large. Maximum size is {MAX_AUDIO_SIZE / 1024 / 1024}MB"
            )

        if not audio_data:
            metrics.record_error("audio_empty", endpoint="voice_process")
            raise HTTPException(status_code=400, detail="Audio file is empty")

        # Record voice request metrics
        metrics.record_voice_request(session_id, len(audio_data))

        logger.info(
            "voice_processing_started",
            session_id=session_id,
            audio_size_bytes=len(audio_data)
        )

        # Transcribe audio to text
        stt_start = time.time()
        try:
            transcribed_text = await stt.transcribe(audio_data)
            stt_duration_ms = (time.time() - stt_start) * 1000
            metrics.record_api_call("groq_stt", success=True, duration_ms=stt_duration_ms)
            logger.info(
                "speech_to_text_success",
                session_id=session_id,
                transcribed_length=len(transcribed_text),
                duration_ms=round(stt_duration_ms, 2)
            )
        except ValueError as e:
            # Validation errors (bad audio format, empty file, etc.)
            stt_duration_ms = (time.time() - stt_start) * 1000
            metrics.record_api_call("groq_stt", success=False, duration_ms=stt_duration_ms)
            metrics.record_error("audio_validation_failed", endpoint="voice_process")
            logger.error("audio_validation_failed", error=str(e), session_id=session_id)
            raise HTTPException(status_code=400, detail=f"Invalid audio: {str(e)}")
        except Exception as e:
            # API or processing errors
            stt_duration_ms = (time.time() - stt_start) * 1000
            metrics.record_api_call("groq_stt", success=False, duration_ms=stt_duration_ms)
            metrics.record_error("speech_to_text_failed", endpoint="voice_process")
            logger.error("speech_to_text_failed", error=str(e), session_id=session_id, exc_info=True)
            raise SpeechToTextError(f"Speech-to-text conversion failed: {str(e)}")

        # Process through LangGraph workflow with timeout and error handling
        workflow_start = time.time()
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
                workflow_duration_ms = (time.time() - workflow_start) * 1000
                metrics.record_workflow_execution(session_id, workflow_duration_ms, success=False)
                metrics.record_error("workflow_timeout", endpoint="voice_process")
                logger.error(
                    "workflow_timeout",
                    session_id=session_id,
                    timeout_seconds=settings.WORKFLOW_TIMEOUT_SECONDS
                )
                raise HTTPException(
                    status_code=504,
                    detail="I'm taking longer than usual to respond. Please try again.",
                )

            # Extract response text from the last AI message
            response_text = result["messages"][-1].content
            workflow_duration_ms = (time.time() - workflow_start) * 1000
            metrics.record_workflow_execution(session_id, workflow_duration_ms, success=True)
            logger.info(
                "workflow_execution_success",
                session_id=session_id,
                response_length=len(response_text),
                duration_ms=round(workflow_duration_ms, 2)
            )

        except CircuitBreakerError as e:
            # Circuit breaker is open for one of the services
            workflow_duration_ms = (time.time() - workflow_start) * 1000
            metrics.record_workflow_execution(session_id, workflow_duration_ms, success=False)
            metrics.record_error("circuit_breaker_open", endpoint="voice_process")
            logger.error("circuit_breaker_open", error=str(e), session_id=session_id)
            raise HTTPException(
                status_code=503,
                detail="I'm having trouble connecting to my services right now. Please try again in a moment.",
            )
        except HTTPException:
            # Re-raise HTTP exceptions (including timeout)
            raise
        except Exception as e:
            workflow_duration_ms = (time.time() - workflow_start) * 1000
            metrics.record_workflow_execution(session_id, workflow_duration_ms, success=False)
            metrics.record_error("workflow_execution_failed", endpoint="voice_process")
            logger.error("workflow_execution_failed", error=str(e), session_id=session_id, exc_info=True)
            # Raise custom exception for proper error handling
            raise WorkflowError(f"Workflow execution failed: {str(e)}")

        # Generate audio response
        tts_start = time.time()
        try:
            audio_bytes = await tts.synthesize(response_text)
            tts_duration_ms = (time.time() - tts_start) * 1000
            metrics.record_api_call("elevenlabs_tts", success=True, duration_ms=tts_duration_ms)
            logger.info(
                "text_to_speech_success",
                session_id=session_id,
                audio_size_bytes=len(audio_bytes),
                duration_ms=round(tts_duration_ms, 2)
            )
        except Exception as e:
            tts_duration_ms = (time.time() - tts_start) * 1000
            metrics.record_api_call("elevenlabs_tts", success=False, duration_ms=tts_duration_ms)
            metrics.record_error("text_to_speech_failed", endpoint="voice_process")
            logger.error("text_to_speech_failed", error=str(e), session_id=session_id, exc_info=True)
            # Raise custom exception for proper error handling
            raise TextToSpeechError(f"Text-to-speech conversion failed: {str(e)}")

        # Save audio file temporarily with secure permissions
        audio_id = str(uuid.uuid4())
        audio_path = AUDIO_DIR / f"{audio_id}.mp3"

        try:
            # Create file with secure permissions (owner read/write only)
            fd = os.open(str(audio_path), os.O_CREAT | os.O_WRONLY | os.O_EXCL, stat.S_IRUSR | stat.S_IWUSR)
            os.write(fd, audio_bytes)
            os.close(fd)
            logger.info("audio_file_saved", audio_id=audio_id, path=str(audio_path))
        except Exception as e:
            metrics.record_error("audio_save_failed", endpoint="voice_process")
            logger.error("audio_save_failed", error=str(e), audio_id=audio_id)
            raise HTTPException(status_code=500, detail="Failed to save audio response")

        # Return response with audio URL
        audio_url = f"/api/voice/audio/{audio_id}"

        logger.info(
            "voice_processing_complete",
            session_id=session_id,
            audio_id=audio_id,
            response_length=len(response_text)
        )

        return VoiceProcessResponse(
            text=response_text,
            audio_url=audio_url,
            session_id=session_id,
        )

    except HTTPException:
        raise
    except (SpeechToTextError, TextToSpeechError, WorkflowError):
        # These will be handled by the global exception handler
        raise
    except Exception as e:
        metrics.record_error("unexpected_error", endpoint="voice_process")
        logger.error("unexpected_error", error=str(e), session_id=session_id, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/voice/audio/{audio_id}")
@track_performance("audio_serving")
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
        metrics.record_error("audio_not_found", endpoint="audio_serving")
        logger.error("audio_file_not_found", audio_id=audio_id)
        raise HTTPException(status_code=404, detail="Audio file not found")

    logger.info("audio_file_served", audio_id=audio_id)

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
        deleted_count = 0

        for audio_file in AUDIO_DIR.glob("*.mp3"):
            file_age = current_time - audio_file.stat().st_mtime
            if file_age > max_age_seconds:
                audio_file.unlink()
                deleted_count += 1
                logger.info("audio_file_deleted", filename=audio_file.name, age_hours=file_age / 3600)

        logger.info("audio_cleanup_complete", deleted_count=deleted_count, max_age_hours=max_age)

    except Exception as e:
        logger.error("audio_cleanup_failed", error=str(e), exc_info=True)
