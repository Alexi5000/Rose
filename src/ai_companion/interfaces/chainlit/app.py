"""Chainlit web interface for the AI companion.

This module provides the Chainlit-based web chat interface for interacting with
the AI companion. It handles text messages, images, and audio input/output with
session-scoped module instances for better resource management.

Module Dependencies:
- ai_companion.core.resilience: CircuitBreakerError for error handling
- ai_companion.graph: graph_builder for workflow execution
- ai_companion.modules.image: ImageToText for image analysis
- ai_companion.modules.speech: SpeechToText, TextToSpeech for audio processing
- ai_companion.settings: Configuration for timeouts, database paths
- chainlit: Web interface framework
- langchain_core.messages: Message types (AIMessageChunk, HumanMessage)
- langgraph.checkpoint.sqlite.aio: AsyncSqliteSaver for conversation persistence
- Standard library: asyncio, io

Architecture:
This module is part of the interfaces layer and provides a user-facing web interface.
It uses session-scoped module instances (stored in cl.user_session) to ensure proper
resource management and testability. Factory functions (get_speech_to_text, etc.)
provide access to these instances.

Note on Direct Module Dependencies:
This interface directly imports modules.speech and modules.image for interface-specific
needs (audio/image handling). While the graph layer orchestrates most workflow logic,
these direct imports are acceptable for interface-specific preprocessing (e.g., image
analysis before sending to graph, audio transcription).

For detailed architecture documentation, see:
- docs/ARCHITECTURE.md: Module Initialization Patterns section
- docs/PROJECT_STRUCTURE.md: Interfaces section
- .kiro/specs/technical-debt-management/design.md: Module Initialization Optimization

Example:
    Run the Chainlit interface:

    $ chainlit run src/ai_companion/interfaces/chainlit/app.py
"""

import asyncio
from io import BytesIO

import aiofiles
import chainlit as cl
from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ai_companion.core.resilience import CircuitBreakerError
from ai_companion.graph import graph_builder
from ai_companion.modules.image import ImageToText
from ai_companion.modules.speech import SpeechToText, TextToSpeech
from ai_companion.settings import settings


def get_speech_to_text() -> SpeechToText:
    """Factory function to get or create SpeechToText instance for the current session.

    Module Lifecycle:
    - Created once per session in on_chat_start
    - Stored in cl.user_session for reuse across message handlers
    - Automatically cleaned up when session ends

    Returns:
        SpeechToText: Session-scoped SpeechToText instance
    """
    instance = cl.user_session.get("speech_to_text")
    if instance is None:
        instance = SpeechToText()
        cl.user_session.set("speech_to_text", instance)
    return instance


def get_text_to_speech() -> TextToSpeech:
    """Factory function to get or create TextToSpeech instance for the current session.

    Module Lifecycle:
    - Created once per session in on_chat_start
    - Stored in cl.user_session for reuse across message handlers
    - Automatically cleaned up when session ends

    Returns:
        TextToSpeech: Session-scoped TextToSpeech instance
    """
    instance = cl.user_session.get("text_to_speech")
    if instance is None:
        instance = TextToSpeech()
        cl.user_session.set("text_to_speech", instance)
    return instance


def get_image_to_text() -> ImageToText:
    """Factory function to get or create ImageToText instance for the current session.

    Module Lifecycle:
    - Created once per session in on_chat_start
    - Stored in cl.user_session for reuse across message handlers
    - Automatically cleaned up when session ends

    Returns:
        ImageToText: Session-scoped ImageToText instance
    """
    instance = cl.user_session.get("image_to_text")
    if instance is None:
        instance = ImageToText()
        cl.user_session.set("image_to_text", instance)
    return instance


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session with session-scoped module instances.

    This handler creates and stores module instances in the user session,
    ensuring each session has its own isolated instances for better
    testability and resource management.
    """
    # Set thread ID for conversation continuity
    cl.user_session.set("thread_id", 1)

    # Initialize session-scoped module instances
    # These will be reused across all message handlers in this session
    cl.user_session.set("speech_to_text", SpeechToText())
    cl.user_session.set("text_to_speech", TextToSpeech())
    cl.user_session.set("image_to_text", ImageToText())


@cl.on_message
async def on_message(message: cl.Message):
    """Handle text messages and images.

    Uses session-scoped module instances retrieved via factory functions
    for better testability and resource management.
    """
    msg = cl.Message(content="")

    # Process any attached images
    content = message.content
    if message.elements:
        for elem in message.elements:
            if isinstance(elem, cl.Image):
                # Read image file content asynchronously
                async with aiofiles.open(elem.path, "rb") as f:
                    image_bytes = await f.read()

                # Analyze image and add to message content
                try:
                    # Use session-scoped ImageToText instance
                    image_to_text_module = get_image_to_text()
                    description = await image_to_text_module.analyze_image(
                        image_bytes,
                        "Please describe what you see in this image in the context of our conversation.",
                    )
                    content += f"\n[Image Analysis: {description}]"
                except Exception as e:
                    cl.logger.warning(f"Failed to analyze image: {e}")

    # Process through graph with enriched message content and error handling
    thread_id = cl.user_session.get("thread_id")

    try:
        async with cl.Step(type="run"):
            async with AsyncSqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH) as short_term_memory:
                graph = graph_builder.compile(checkpointer=short_term_memory)

                # Stream with timeout
                try:
                    async with asyncio.timeout(settings.WORKFLOW_TIMEOUT_SECONDS):
                        async for chunk in graph.astream(
                            {"messages": [HumanMessage(content=content)]},
                            {"configurable": {"thread_id": thread_id}},
                            stream_mode="messages",
                        ):
                            if chunk[1]["langgraph_node"] == "conversation_node" and isinstance(
                                chunk[0], AIMessageChunk
                            ):
                                await msg.stream_token(chunk[0].content)

                        output_state = await graph.aget_state(config={"configurable": {"thread_id": thread_id}})
                except asyncio.TimeoutError:
                    cl.logger.error(f"Workflow timeout after {settings.WORKFLOW_TIMEOUT_SECONDS}s")
                    await cl.Message(
                        content="I'm taking longer than usual to respond. Please try again."
                    ).send()
                    return

    except CircuitBreakerError as e:
        cl.logger.error(f"Circuit breaker open during workflow: {e}")
        await cl.Message(
            content="I'm having trouble connecting to my services right now. Please try again in a moment."
        ).send()
        return
    except Exception as e:
        cl.logger.error(f"Workflow failed: {e}", exc_info=True)
        await cl.Message(
            content="I'm having trouble processing that right now. Could you try rephrasing?"
        ).send()
        return

    if output_state.values.get("workflow") == "audio":
        response = output_state.values["messages"][-1].content
        audio_buffer = output_state.values["audio_buffer"]
        output_audio_el = cl.Audio(
            name="Audio",
            auto_play=True,
            mime="audio/mpeg3",
            content=audio_buffer,
        )
        await cl.Message(content=response, elements=[output_audio_el]).send()
    elif output_state.values.get("workflow") == "image":
        response = output_state.values["messages"][-1].content
        image = cl.Image(path=output_state.values["image_path"], display="inline")
        await cl.Message(content=response, elements=[image]).send()
    else:
        await msg.send()


@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.AudioChunk):
    """Handle incoming audio chunks"""
    if chunk.isStart:
        buffer = BytesIO()
        buffer.name = f"input_audio.{chunk.mimeType.split('/')[1]}"
        cl.user_session.set("audio_buffer", buffer)
        cl.user_session.set("audio_mime_type", chunk.mimeType)
    cl.user_session.get("audio_buffer").write(chunk.data)


@cl.on_audio_end
async def on_audio_end(elements):
    """Process completed audio input.

    Uses session-scoped module instances retrieved via factory functions
    for speech-to-text transcription and text-to-speech synthesis.
    """
    # Get audio data
    audio_buffer = cl.user_session.get("audio_buffer")
    audio_buffer.seek(0)
    audio_data = audio_buffer.read()

    # Show user's audio message
    input_audio_el = cl.Audio(mime="audio/mpeg3", content=audio_data)
    await cl.Message(author="You", content="", elements=[input_audio_el, *elements]).send()

    # Use session-scoped SpeechToText instance
    speech_to_text_module = get_speech_to_text()
    transcription = await speech_to_text_module.transcribe(audio_data)

    thread_id = cl.user_session.get("thread_id")

    try:
        async with AsyncSqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH) as short_term_memory:
            graph = graph_builder.compile(checkpointer=short_term_memory)

            # Invoke with timeout
            try:
                output_state = await asyncio.wait_for(
                    graph.ainvoke(
                        {"messages": [HumanMessage(content=transcription)]},
                        {"configurable": {"thread_id": thread_id}},
                    ),
                    timeout=settings.WORKFLOW_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                cl.logger.error(f"Workflow timeout after {settings.WORKFLOW_TIMEOUT_SECONDS}s")
                await cl.Message(
                    content="I'm taking longer than usual to respond. Please try again."
                ).send()
                return

        # Use session-scoped TextToSpeech instance
        text_to_speech_module = get_text_to_speech()
        audio_buffer = await text_to_speech_module.synthesize(output_state["messages"][-1].content)

        output_audio_el = cl.Audio(
            name="Audio",
            auto_play=True,
            mime="audio/mpeg3",
            content=audio_buffer,
        )
        await cl.Message(content=output_state["messages"][-1].content, elements=[output_audio_el]).send()

    except CircuitBreakerError as e:
        cl.logger.error(f"Circuit breaker open during audio workflow: {e}")
        await cl.Message(
            content="I'm having trouble connecting to my services right now. Please try again in a moment."
        ).send()
    except Exception as e:
        cl.logger.error(f"Audio workflow failed: {e}", exc_info=True)
        await cl.Message(
            content="I'm having trouble processing that right now. Could you try rephrasing?"
        ).send()
