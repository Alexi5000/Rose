"""WhatsApp webhook handler for the AI companion.

This module provides the WhatsApp Cloud API webhook integration for the AI companion.
It handles incoming messages (text, audio, images) and sends responses back through
the WhatsApp Business API.

Module Dependencies:
- ai_companion.core.resilience: CircuitBreakerError for error handling
- ai_companion.graph: graph_builder for workflow execution
- ai_companion.modules.image: ImageToText for image analysis
- ai_companion.modules.speech: SpeechToText, TextToSpeech for audio processing
- ai_companion.settings: Configuration for timeouts, database paths, WhatsApp credentials
- fastapi: APIRouter, Request, Response for webhook handling
- langchain_core.messages: HumanMessage for message construction
- langgraph.checkpoint.sqlite.aio: AsyncSqliteSaver for conversation persistence
- httpx: HTTP client for WhatsApp API calls
- Standard library: asyncio, logging, os, io, typing

Architecture:
This module is part of the interfaces layer and provides WhatsApp integration.
Unlike the Chainlit interface which uses session-scoped instances, this module
uses global module instances (speech_to_text, text_to_speech, image_to_text)
since WhatsApp webhooks are stateless HTTP requests without session context.

Note on Direct Module Dependencies:
This interface directly imports modules.speech and modules.image for interface-specific
needs (audio/image handling in WhatsApp messages). While the graph layer orchestrates
most workflow logic, these direct imports are acceptable for interface-specific
preprocessing (e.g., downloading and analyzing WhatsApp media).

For detailed architecture documentation, see:
- docs/ARCHITECTURE.md: WhatsApp Integration section
- docs/PROJECT_STRUCTURE.md: Interfaces section

Example:
    Configure WhatsApp webhook URL:

    https://your-domain.com/whatsapp_response
"""

import asyncio
import logging
import os
from io import BytesIO
from typing import Dict

import aiofiles
import httpx
from fastapi import APIRouter, Request, Response
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ai_companion.core.resilience import CircuitBreakerError
from ai_companion.graph import graph_builder
from ai_companion.modules.image import ImageToText
from ai_companion.modules.speech import SpeechToText, TextToSpeech
from ai_companion.settings import settings

logger = logging.getLogger(__name__)

# Global module instances
speech_to_text = SpeechToText()
text_to_speech = TextToSpeech()
image_to_text = ImageToText()

# Router for WhatsApp responses
whatsapp_router = APIRouter()

# WhatsApp API credentials
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


@whatsapp_router.api_route("/whatsapp_response", methods=["GET", "POST"])
async def whatsapp_handler(request: Request) -> Response:
    """Handles incoming messages and status updates from the WhatsApp Cloud API."""

    if request.method == "GET":
        params = request.query_params
        if params.get("hub.verify_token") == os.getenv("WHATSAPP_VERIFY_TOKEN"):
            return Response(content=params.get("hub.challenge"), status_code=200)
        return Response(content="Verification token mismatch", status_code=403)

    try:
        data = await request.json()
        change_value = data["entry"][0]["changes"][0]["value"]
        if "messages" in change_value:
            message = change_value["messages"][0]
            from_number = message["from"]
            session_id = from_number

            # Get user message and handle different message types
            content = ""
            if message["type"] == "audio":
                content = await process_audio_message(message)
            elif message["type"] == "image":
                # Get image caption if any
                content = message.get("image", {}).get("caption", "")
                # Download and analyze image
                image_bytes = await download_media(message["image"]["id"])
                try:
                    description = await image_to_text.analyze_image(
                        image_bytes,
                        "Please describe what you see in this image in the context of our conversation.",
                    )
                    content += f"\n[Image Analysis: {description}]"
                except Exception as e:
                    logger.warning(f"Failed to analyze image: {e}")
            else:
                content = message["text"]["body"]

            # Process message through the graph agent with error handling
            try:
                async with AsyncSqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH) as short_term_memory:
                    graph = graph_builder.compile(checkpointer=short_term_memory)

                    # Invoke with timeout
                    try:
                        await asyncio.wait_for(
                            graph.ainvoke(
                                {"messages": [HumanMessage(content=content)]},
                                {"configurable": {"thread_id": session_id}},
                            ),
                            timeout=settings.WORKFLOW_TIMEOUT_SECONDS,
                        )
                    except asyncio.TimeoutError:
                        logger.error(f"Workflow timeout after {settings.WORKFLOW_TIMEOUT_SECONDS}s for {from_number}")
                        await send_response(
                            from_number,
                            "I'm taking longer than usual to respond. Please try again.",
                            "text",
                        )
                        return Response(content="Workflow timeout", status_code=200)

                    # Get the workflow type and response from the state
                    output_state = await graph.aget_state(config={"configurable": {"thread_id": session_id}})

            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker open during workflow: {e}")
                await send_response(
                    from_number,
                    "I'm having trouble connecting to my services right now. Please try again in a moment.",
                    "text",
                )
                return Response(content="Circuit breaker open", status_code=200)
            except Exception as e:
                logger.error(f"Workflow failed: {e}", exc_info=True)
                await send_response(
                    from_number,
                    "I'm having trouble processing that right now. Could you try rephrasing?",
                    "text",
                )
                return Response(content="Workflow error", status_code=200)

            workflow = output_state.values.get("workflow", "conversation")
            response_message = output_state.values["messages"][-1].content

            # Handle different response types based on workflow
            if workflow == "audio":
                audio_buffer = output_state.values["audio_buffer"]
                success = await send_response(from_number, response_message, "audio", audio_buffer)
            elif workflow == "image":
                image_path = output_state.values["image_path"]
                async with aiofiles.open(image_path, "rb") as f:
                    image_data = await f.read()
                success = await send_response(from_number, response_message, "image", image_data)
            else:
                success = await send_response(from_number, response_message, "text")

            if not success:
                return Response(content="Failed to send message", status_code=500)

            return Response(content="Message processed", status_code=200)

        elif "statuses" in change_value:
            return Response(content="Status update received", status_code=200)

        else:
            return Response(content="Unknown event type", status_code=400)

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return Response(content="Internal server error", status_code=500)


async def download_media(media_id: str) -> bytes:
    """Download media from WhatsApp."""
    media_metadata_url = f"https://graph.facebook.com/v21.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    async with httpx.AsyncClient() as client:
        metadata_response = await client.get(media_metadata_url, headers=headers)
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
        download_url = metadata.get("url")

        media_response = await client.get(download_url, headers=headers)
        media_response.raise_for_status()
        return media_response.content


async def process_audio_message(message: Dict) -> str:
    """Download and transcribe audio message."""
    audio_id = message["audio"]["id"]
    media_metadata_url = f"https://graph.facebook.com/v21.0/{audio_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    async with httpx.AsyncClient() as client:
        metadata_response = await client.get(media_metadata_url, headers=headers)
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
        download_url = metadata.get("url")

    # Download the audio file
    async with httpx.AsyncClient() as client:
        audio_response = await client.get(download_url, headers=headers)
        audio_response.raise_for_status()

    # Prepare for transcription
    audio_buffer = BytesIO(audio_response.content)
    audio_buffer.seek(0)
    audio_data = audio_buffer.read()

    return await speech_to_text.transcribe(audio_data)


async def send_response(
    from_number: str,
    response_text: str,
    message_type: str = "text",
    media_content: bytes = None,
) -> bool:
    """Send response to user via WhatsApp API."""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    if message_type in ["audio", "image"]:
        try:
            mime_type = "audio/mpeg" if message_type == "audio" else "image/png"
            media_buffer = BytesIO(media_content)
            media_id = await upload_media(media_buffer, mime_type)
            json_data = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": message_type,
                message_type: {"id": media_id},
            }

            # Add caption for images
            if message_type == "image":
                json_data["image"]["caption"] = response_text
        except Exception as e:
            logger.error(f"Media upload failed, falling back to text: {e}")
            message_type = "text"

    if message_type == "text":
        json_data = {
            "messaging_product": "whatsapp",
            "to": from_number,
            "type": "text",
            "text": {"body": response_text},
        }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages",
            headers=headers,
            json=json_data,
        )

    return response.status_code == 200


async def upload_media(media_content: BytesIO, mime_type: str) -> str:
    """Upload media to WhatsApp servers."""
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    files = {"file": ("response.mp3", media_content, mime_type)}
    data = {"messaging_product": "whatsapp", "type": mime_type}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/media",
            headers=headers,
            files=files,
            data=data,
        )
        result = response.json()

    if "id" not in result:
        raise Exception("Failed to upload media")
    return result["id"]
