from langgraph.graph import MessagesState


class AICompanionState(MessagesState):
    """State class for the AI Companion workflow.

    Extends MessagesState to track conversation history and workflow state.

    Attributes:
        summary: Running summary of the conversation for context window management.
        workflow: Current workflow type (always "audio" in voice-first mode).
        audio_buffer: Generated audio bytes from TTS synthesis.
        current_activity: Ambient support-tone context for the current time slot.
        apply_activity: Whether the activity context has changed and should be applied.
        memory_context: Retrieved long-term memories formatted for prompt injection.
        affect_state: Current conversational affect hint for response shaping.
        safety_risk: Safety risk category for the current turn.
        safety_response: Direct safety response that bypasses normal LLM generation.
    """

    summary: str
    workflow: str
    audio_buffer: bytes
    current_activity: str
    apply_activity: bool
    memory_context: str
    affect_state: str
    safety_risk: str
    safety_response: str
