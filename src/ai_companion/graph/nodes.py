import os
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig

from ai_companion.graph.state import AICompanionState
from ai_companion.graph.utils.chains import (
    get_character_response_chain,
    get_router_chain,
)
from ai_companion.graph.utils.helpers import (
    get_chat_model,
    get_text_to_image_module,
    get_text_to_speech_module,
)
from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager
from ai_companion.modules.schedules.context_generation import ScheduleContextGenerator
from ai_companion.settings import settings


async def router_node(state: AICompanionState) -> dict[str, str]:
    """Route the conversation to the appropriate workflow type.

    Analyzes recent messages to determine if the user wants:
    - conversation: Regular text conversation
    - image: Image generation request
    - audio: Audio/voice interaction

    Args:
        state: Current conversation state

    Returns:
        Dictionary with workflow type: {"workflow": "conversation"|"image"|"audio"}
    """
    chain = get_router_chain()
    response = await chain.ainvoke({"messages": state["messages"][-settings.ROUTER_MESSAGES_TO_ANALYZE :]})
    return {"workflow": response.response_type}


def context_injection_node(state: AICompanionState) -> dict[str, bool | str]:
    """Inject current activity context into the conversation state.

    Determines if the current scheduled activity has changed and should be
    applied to the conversation context.

    Args:
        state: Current conversation state

    Returns:
        Dictionary with activity context: {
            "apply_activity": bool,
            "current_activity": str
        }
    """
    schedule_context = ScheduleContextGenerator.get_current_activity()
    if schedule_context != state.get("current_activity", ""):
        apply_activity = True
    else:
        apply_activity = False
    return {"apply_activity": apply_activity, "current_activity": schedule_context}


async def conversation_node(state: AICompanionState, config: RunnableConfig) -> dict[str, AIMessage]:
    """Generate a conversational response using Rose's character.

    Processes the conversation through the character response chain with
    memory context and current activity awareness.

    Args:
        state: Current conversation state
        config: LangGraph runnable configuration

    Returns:
        Dictionary with AI response: {"messages": AIMessage}
    """
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))

    response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
    return {"messages": AIMessage(content=response)}


async def image_node(state: AICompanionState, config: RunnableConfig) -> dict[str, AIMessage | str]:
    """Generate an image and respond with context about it.

    Creates an image based on conversation context, then generates a
    conversational response about the generated image.

    Args:
        state: Current conversation state
        config: LangGraph runnable configuration

    Returns:
        Dictionary with response and image path: {
            "messages": AIMessage,
            "image_path": str
        }
    """
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))
    text_to_image_module = get_text_to_image_module()

    scenario = await text_to_image_module.create_scenario(state["messages"][-5:])
    os.makedirs("generated_images", exist_ok=True)
    img_path = f"generated_images/image_{str(uuid4())}.png"
    await text_to_image_module.generate_image(scenario.image_prompt, img_path)

    # Inject the image prompt information as an AI message
    scenario_message = HumanMessage(content=f"<image attached by Ava generated from prompt: {scenario.image_prompt}>")
    updated_messages = state["messages"] + [scenario_message]

    response = await chain.ainvoke(
        {
            "messages": updated_messages,
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )

    return {"messages": AIMessage(content=response), "image_path": img_path}


async def audio_node(state: AICompanionState, config: RunnableConfig) -> dict[str, str | bytes]:
    """Generate a voice response with audio output.

    Creates a text response and synthesizes it to audio using TTS.

    Args:
        state: Current conversation state
        config: LangGraph runnable configuration

    Returns:
        Dictionary with response and audio: {
            "messages": str,
            "audio_buffer": bytes
        }
    """
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))
    text_to_speech_module = get_text_to_speech_module()

    response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
    output_audio = await text_to_speech_module.synthesize(response)

    return {"messages": response, "audio_buffer": output_audio}


async def summarize_conversation_node(state: AICompanionState) -> dict[str, str | list[RemoveMessage]]:
    """Summarize conversation history and trim old messages.

    Creates or extends a conversation summary and removes old messages
    to keep the context window manageable.

    Args:
        state: Current conversation state

    Returns:
        Dictionary with summary and messages to remove: {
            "summary": str,
            "messages": list[RemoveMessage]
        }
    """
    model = get_chat_model()
    summary = state.get("summary", "")

    if summary:
        summary_message = (
            f"This is summary of the conversation to date between Ava and the user: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = (
            "Create a summary of the conversation above between Ava and the user. "
            "The summary must be a short description of the conversation so far, "
            "but that captures all the relevant information shared between Ava and the user:"
        )

    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = await model.ainvoke(messages)

    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][: -settings.TOTAL_MESSAGES_AFTER_SUMMARY]]
    return {"summary": response.content, "messages": delete_messages}


async def memory_extraction_node(state: AICompanionState) -> dict:
    """Extract and store important information from the last message.

    Analyzes the most recent message and stores relevant memories
    in the long-term memory system (Qdrant).

    Args:
        state: Current conversation state

    Returns:
        Empty dictionary (state update handled by memory manager)
    """
    if not state["messages"]:
        return {}

    memory_manager = get_memory_manager()
    await memory_manager.extract_and_store_memories(state["messages"][-1])
    return {}


def memory_injection_node(state: AICompanionState) -> dict[str, str]:
    """Retrieve and inject relevant memories into the character card.

    Searches long-term memory for relevant context based on recent
    conversation and formats it for inclusion in the prompt.

    Args:
        state: Current conversation state

    Returns:
        Dictionary with memory context: {"memory_context": str}
    """
    memory_manager = get_memory_manager()

    # Get relevant memories based on recent conversation
    recent_context = " ".join([m.content for m in state["messages"][-3:]])
    memories = memory_manager.get_relevant_memories(recent_context)

    # Format memories for the character card
    memory_context = memory_manager.format_memories_for_prompt(memories)

    return {"memory_context": memory_context}
