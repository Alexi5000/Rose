"""Voice processing endpoints."""

import logging
import os
import stat
import tempfile
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

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
    """Response model for voice processing."""

    text: str
    audio_url: str
    session_id: str


@router.post("/voice/process", response_model=VoiceProcessResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def process_voice(
    request: Request,
    audio: UploadFile = File(...),
    session_id: str = Form(...),
) -> VoiceProcessResponse:
    """Process voice input and generate audio response.

    Accepts an audio file, transcribes it using Groq Whisper,
    processes through LangGraph workflow, and generates audio response.

    Args:
        audio: Audio file (WAV, MP3, WebM)
        session_id: Session identifier for conversation tracking

    Returns:
        VoiceProcessResponse: Text response, audio URL, and session ID

    Raises:
        HTTPException: If audio processing fails
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

        # Process through LangGraph workflow
        try:
            # Create checkpointer for session persistence
            checkpointer = SqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH)

            # Compile graph with checkpointer
            graph = create_workflow_graph().compile(checkpointer=checkpointer)

            # Create config with session thread
            config = {"configurable": {"thread_id": session_id}}

            # Invoke workflow with transcribed text
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=transcribed_text)]},
                config=config,
            )

            # Extract response text from the last AI message
            response_text = result["messages"][-1].content
            logger.info(f"Generated response: {response_text[:100]}...")

        except Exception as e:
            logger.error(f"LangGraph workflow failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="Rose is having trouble connecting. Please try again in a moment.",
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
            fd = os.open(
                str(audio_path),
                os.O_CREAT | os.O_WRONLY | os.O_EXCL,
                stat.S_IRUSR | stat.S_IWUSR
            )
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

    Args:
        audio_id: Unique identifier for the audio file

    Returns:
        FileResponse: Audio file as streaming response

    Raises:
        HTTPException: If audio file not found
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


def cleanup_old_audio_files(max_age_hours: int = 24):
    """Clean up audio files older than specified hours.

    Args:
        max_age_hours: Maximum age of files to keep in hours
    """
    try:
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        for audio_file in AUDIO_DIR.glob("*.mp3"):
            file_age = current_time - audio_file.stat().st_mtime
            if file_age > max_age_seconds:
                audio_file.unlink()
                logger.info(f"Deleted old audio file: {audio_file.name}")

    except Exception as e:
        logger.error(f"Error cleaning up audio files: {e}")
