from langgraph.graph import MessagesState


class AICompanionState(MessagesState):
    """State class for the AI Companion workflow.

    Extends MessagesState to track conversation history and workflow state.

    Attributes:
        summary: Running summary of the conversation for context window management.
        workflow: Current workflow type (always "audio" in voice-first mode).
        audio_buffer: Generated audio bytes from TTS synthesis.
        current_activity: Rose's current scheduled activity context.
        apply_activity: Whether the activity context has changed and should be applied.
        memory_context: Retrieved long-term memories formatted for prompt injection.
    """

    summary: str
    workflow: str
    audio_buffer: bytes
    current_activity: str
    apply_activity: bool
    memory_context: str
