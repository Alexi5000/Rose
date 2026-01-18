"""WebSocket endpoint for real-time voice streaming.

file: src/ai_companion/interfaces/web/routes/voice_websocket.py
description: Phase 6 - Bi-directional WebSocket for low-latency voice interactions
reference: src/ai_companion/interfaces/web/routes/voice.py, docs/BASELINE_METRICS.md

This module provides WebSocket-based voice processing that enables:
- Real-time audio streaming from client to server
- Overlapped processing (STT while receiving, TTS while generating)
- Streaming responses back to client
- Barge-in support (client can interrupt Rose)

Protocol:
1. Client connects to /api/v1/voice/ws?session_id=<uuid>
2. Client sends binary audio chunks
3. Server sends JSON control messages and binary audio responses
4. Client can send interrupt signal to stop Rose mid-response

Message Types (JSON):
- {"type": "start_listening"}: Begin audio capture
- {"type": "stop_listening"}: End audio capture, process
- {"type": "interrupt"}: Stop current response
- {"type": "transcription", "text": "..."}: Partial/final transcription
- {"type": "response", "text": "..."}: Rose's response text
- {"type": "audio_start"}: Audio streaming starting
- {"type": "audio_end"}: Audio streaming complete
- {"type": "error", "message": "..."}: Error occurred

Binary Messages:
- Client → Server: Audio chunks (webm/opus)
- Server → Client: Audio chunks (mp3)
"""

import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ai_companion.core.logging_config import get_logger
from ai_companion.core.metrics import metrics
from ai_companion.graph.graph import create_workflow_graph
from ai_companion.modules.speech.speech_to_text import SpeechToText
from ai_companion.modules.speech.text_to_speech import TextToSpeech
from ai_companion.settings import settings

logger = get_logger(__name__)

router = APIRouter()

# WebSocket message types
MSG_START_LISTENING = "start_listening"
MSG_STOP_LISTENING = "stop_listening"
MSG_INTERRUPT = "interrupt"
MSG_TRANSCRIPTION = "transcription"
MSG_RESPONSE = "response"
MSG_AUDIO_START = "audio_start"
MSG_AUDIO_END = "audio_end"
MSG_ERROR = "error"
MSG_CONNECTED = "connected"


class VoiceWebSocketSession:
    """Manages state for a single WebSocket voice session.
    
    Handles audio buffering, interruption signals, and response streaming.
    """
    
    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.audio_buffer: bytearray = bytearray()
        self.is_listening = False
        self.is_responding = False
        self.interrupted = False
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
    
    async def send_json(self, msg_type: str, **kwargs) -> None:
        """Send a JSON control message to the client."""
        message = {"type": msg_type, **kwargs}
        await self.websocket.send_json(message)
    
    async def send_audio(self, audio_chunk: bytes) -> None:
        """Send audio data to the client."""
        await self.websocket.send_bytes(audio_chunk)
    
    def handle_interrupt(self) -> None:
        """Handle interruption signal from client."""
        self.interrupted = True
        logger.info("ws_session_interrupted", session_id=self.session_id)
    
    def reset_for_new_turn(self) -> None:
        """Reset session state for a new conversation turn."""
        self.audio_buffer.clear()
        self.is_listening = False
        self.is_responding = False
        self.interrupted = False


async def get_ws_checkpointer():
    """Create checkpointer for WebSocket sessions."""
    from pathlib import Path
    db_path = Path(settings.SHORT_TERM_MEMORY_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        yield checkpointer


@router.websocket("/voice/ws")
async def voice_websocket(
    websocket: WebSocket,
    session_id: str = Query(..., description="Session ID for conversation tracking"),
) -> None:
    """WebSocket endpoint for real-time voice streaming.
    
    Provides bi-directional audio streaming for low-latency voice interactions.
    Supports interruption (barge-in) while Rose is speaking.
    
    Args:
        websocket: FastAPI WebSocket connection
        session_id: Session identifier from /session/start
    """
    await websocket.accept()
    logger.info("ws_connection_accepted", session_id=session_id)
    
    session = VoiceWebSocketSession(websocket, session_id)
    
    # Send connection confirmation
    await session.send_json(MSG_CONNECTED, session_id=session_id)
    
    try:
        while True:
            # Receive message (text or binary)
            message = await websocket.receive()
            
            if message["type"] == "websocket.disconnect":
                break
            
            # Handle text messages (JSON control messages)
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")
                    
                    if msg_type == MSG_START_LISTENING:
                        session.reset_for_new_turn()
                        session.is_listening = True
                        logger.debug("ws_start_listening", session_id=session_id)
                    
                    elif msg_type == MSG_STOP_LISTENING:
                        session.is_listening = False
                        logger.debug("ws_stop_listening", session_id=session_id, buffer_size=len(session.audio_buffer))
                        
                        # Process the collected audio
                        if session.audio_buffer:
                            await _process_audio_and_respond(session)
                    
                    elif msg_type == MSG_INTERRUPT:
                        session.handle_interrupt()
                        await session.send_json(MSG_AUDIO_END, interrupted=True)
                    
                except json.JSONDecodeError as e:
                    logger.warning("ws_invalid_json", session_id=session_id, error=str(e))
                    await session.send_json(MSG_ERROR, message="Invalid JSON message")
            
            # Handle binary messages (audio chunks)
            elif "bytes" in message:
                if session.is_listening:
                    session.audio_buffer.extend(message["bytes"])
                    # Optional: Send partial transcription for streaming STT
                    # This would require streaming STT provider (Phase 4)
    
    except WebSocketDisconnect:
        logger.info("ws_connection_closed", session_id=session_id)
    
    except Exception as e:
        logger.error("ws_error", session_id=session_id, error=str(e), exc_info=True)
        try:
            await session.send_json(MSG_ERROR, message=str(e))
        except Exception:
            pass


async def _process_audio_and_respond(session: VoiceWebSocketSession) -> None:
    """Process buffered audio and stream response back to client.
    
    This is the core processing pipeline for WebSocket voice:
    1. Transcribe audio (STT)
    2. Send transcription to client
    3. Run LangGraph workflow
    4. Send response text to client
    5. Stream TTS audio to client
    
    Supports interruption at any point.
    """
    session_id = session.session_id
    
    try:
        # Step 1: Transcribe audio
        audio_data = bytes(session.audio_buffer)
        
        if len(audio_data) < 1000:  # Too short to be meaningful
            logger.debug("ws_audio_too_short", session_id=session_id, size=len(audio_data))
            return
        
        transcription = await session.stt.transcribe(audio_data)
        
        if not transcription or not transcription.strip():
            logger.debug("ws_empty_transcription", session_id=session_id)
            return
        
        # Send transcription to client
        await session.send_json(MSG_TRANSCRIPTION, text=transcription, final=True)
        
        if session.interrupted:
            return
        
        # Step 2: Process through workflow
        session.is_responding = True
        
        # Create checkpointer inline (WebSocket doesn't use FastAPI Depends)
        from pathlib import Path
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        
        db_path = Path(settings.SHORT_TERM_MEMORY_DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer:
            graph = create_workflow_graph().compile(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": session_id}}
            
            result = await asyncio.wait_for(
                graph.ainvoke(
                    {"messages": [HumanMessage(content=transcription)]},
                    config=config,
                ),
                timeout=settings.WORKFLOW_TIMEOUT_SECONDS,
            )
        
        if session.interrupted:
            logger.info("ws_interrupted_after_workflow", session_id=session_id)
            return
        
        response_text = result["messages"][-1].content
        
        # Send response text to client
        await session.send_json(MSG_RESPONSE, text=response_text)
        
        # Step 3: Stream TTS audio
        await session.send_json(MSG_AUDIO_START)
        
        try:
            async for audio_chunk in session.tts.synthesize_streaming(response_text):
                if session.interrupted:
                    logger.info("ws_interrupted_during_tts", session_id=session_id)
                    break
                await session.send_audio(audio_chunk)
        except Exception as tts_error:
            logger.warning("ws_tts_streaming_failed", session_id=session_id, error=str(tts_error))
            # Fall back to batch TTS
            try:
                audio_bytes = await session.tts.synthesize(response_text)
                if not session.interrupted:
                    await session.send_audio(audio_bytes)
            except Exception as batch_error:
                logger.error("ws_tts_batch_failed", session_id=session_id, error=str(batch_error))
        
        await session.send_json(MSG_AUDIO_END, interrupted=session.interrupted)
        session.is_responding = False
        
        logger.info("ws_response_complete", session_id=session_id, response_length=len(response_text))
    
    except asyncio.TimeoutError:
        logger.error("ws_workflow_timeout", session_id=session_id)
        await session.send_json(MSG_ERROR, message="Processing timeout")
    
    except Exception as e:
        logger.error("ws_processing_error", session_id=session_id, error=str(e), exc_info=True)
        await session.send_json(MSG_ERROR, message="Processing failed")
    
    finally:
        session.is_responding = False
