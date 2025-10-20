"""Voice processing endpoints."""

import logging
import tempfile
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from pydantic import BaseModel

from ai_companion.graph.graph import create_workflow_graph
from ai_companion.modules.speech.speech_to_text import SpeechToText
from ai_companion.modules.speech.text_to_speech import TextToSpeech
from ai_companion.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

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
async def process_voice(
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
        except Exception as e:
            logger.error(f"Speech-to-text failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to transcribe audio")

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
            logger.error(f"LangGraph workflow failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate response")

        # Generate audio response
        try:
            audio_bytes = await tts.synthesize(response_text)
            logger.info(f"Generated audio: {len(audio_bytes)} bytes")
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate audio response")

        # Save audio file temporarily
        audio_id = str(uuid.uuid4())
        audio_path = AUDIO_DIR / f"{audio_id}.mp3"

        try:
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)
            logger.info(f"Saved audio to {audio_path}")
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
