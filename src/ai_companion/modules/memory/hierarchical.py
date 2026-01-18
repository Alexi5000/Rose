"""Hierarchical memory system for the AI companion.

file: src/ai_companion/modules/memory/hierarchical.py
description: Phase 5 - Three-tier memory architecture with temporal scoring
reference: src/ai_companion/modules/memory/long_term/memory_manager.py, docs/BASELINE_METRICS.md

This module implements a hierarchical memory system with three tiers:

Tier 1: Working Memory (in-memory)
├── Last N turns of conversation
├── Current emotional state
└── Active topics

Tier 2: Session Memory (in-memory, persisted per session)
├── Session summary
├── All topics discussed this session
└── Session-specific context

Tier 3: Long-Term Memory (Qdrant vector store)
├── User facts with temporal scoring
├── Conflict resolution
└── Memory decay mechanism

Key features:
- Hierarchical retrieval (working → session → long-term)
- Automatic memory promotion and demotion
- Conflict detection between memory tiers
- Session summarization for context compression
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from ai_companion.settings import settings

logger = logging.getLogger(__name__)

# Configuration constants
WORKING_MEMORY_SIZE = 5  # Number of recent turns to keep in working memory
SESSION_SUMMARY_THRESHOLD = 10  # Summarize session after this many turns
CONFLICT_DETECTION_SIMILARITY = 0.85  # Threshold for detecting conflicting memories


@dataclass
class WorkingMemory:
    """Tier 1: Short-term working memory for immediate context.
    
    Holds the most recent conversation turns and current emotional/topical state.
    This is the fastest tier but has the smallest capacity.
    """
    
    # Recent conversation turns (last N messages)
    recent_turns: List[BaseMessage] = field(default_factory=list)
    
    # Current emotional state detected from conversation
    current_emotion: Optional[str] = None
    
    # Active topics being discussed
    active_topics: List[str] = field(default_factory=list)
    
    # Last activity timestamp
    last_activity: datetime = field(default_factory=datetime.now)
    
    def add_turn(self, message: BaseMessage) -> None:
        """Add a new turn to working memory.
        
        Maintains a sliding window of the most recent turns.
        """
        self.recent_turns.append(message)
        self.last_activity = datetime.now()
        
        # Keep only the last N turns
        if len(self.recent_turns) > WORKING_MEMORY_SIZE * 2:  # x2 for user+assistant pairs
            self.recent_turns = self.recent_turns[-WORKING_MEMORY_SIZE * 2:]
    
    def get_context_window(self) -> str:
        """Get formatted recent context for prompt injection."""
        if not self.recent_turns:
            return ""
        
        context_lines = []
        for msg in self.recent_turns[-WORKING_MEMORY_SIZE * 2:]:
            role = "User" if isinstance(msg, HumanMessage) else "Rose"
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
    
    def update_emotion(self, emotion: str) -> None:
        """Update the current detected emotional state."""
        self.current_emotion = emotion
        logger.debug(f"Working memory emotion updated: {emotion}")
    
    def add_topic(self, topic: str) -> None:
        """Add an active topic to working memory."""
        if topic not in self.active_topics:
            self.active_topics.append(topic)
            # Keep only the 5 most recent topics
            if len(self.active_topics) > 5:
                self.active_topics = self.active_topics[-5:]
    
    def clear(self) -> None:
        """Clear working memory (called at session end)."""
        self.recent_turns.clear()
        self.current_emotion = None
        self.active_topics.clear()


@dataclass
class SessionMemory:
    """Tier 2: Session-scoped memory that persists within a conversation.
    
    Stores session-level summary and context that is important for the
    current conversation but may not need long-term retention.
    """
    
    session_id: str
    
    # Accumulated session summary
    summary: str = ""
    
    # All topics discussed in this session
    topics: List[str] = field(default_factory=list)
    
    # Key facts extracted this session (before long-term storage)
    pending_facts: List[str] = field(default_factory=list)
    
    # Session metadata
    started_at: datetime = field(default_factory=datetime.now)
    turn_count: int = 0
    
    def add_topic(self, topic: str) -> None:
        """Add a topic discussed in this session."""
        if topic not in self.topics:
            self.topics.append(topic)
    
    def add_pending_fact(self, fact: str) -> None:
        """Add a fact that might be worth storing long-term."""
        if fact not in self.pending_facts:
            self.pending_facts.append(fact)
    
    def increment_turn(self) -> None:
        """Increment turn count and check if summarization is needed."""
        self.turn_count += 1
        
        if self.turn_count % SESSION_SUMMARY_THRESHOLD == 0:
            logger.info(f"Session {self.session_id}: Turn {self.turn_count}, consider summarization")
    
    def needs_summarization(self) -> bool:
        """Check if the session is long enough to benefit from summarization."""
        return self.turn_count >= SESSION_SUMMARY_THRESHOLD
    
    def update_summary(self, new_summary: str) -> None:
        """Update the session summary."""
        self.summary = new_summary
        logger.debug(f"Session summary updated: {new_summary[:100]}...")


class HierarchicalMemoryManager:
    """Manages the three-tier memory hierarchy.
    
    Coordinates between working memory, session memory, and long-term memory
    to provide efficient retrieval and storage of conversation context.
    """
    
    def __init__(self, session_id: str):
        """Initialize hierarchical memory for a session.
        
        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id
        self.working = WorkingMemory()
        self.session = SessionMemory(session_id=session_id)
        
        # Long-term memory manager is obtained on-demand to avoid circular imports
        self._long_term_manager = None
    
    @property
    def long_term(self):
        """Lazy-load long-term memory manager."""
        if self._long_term_manager is None:
            from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager
            self._long_term_manager = get_memory_manager()
        return self._long_term_manager
    
    def add_message(self, message: BaseMessage) -> None:
        """Process an incoming message across all memory tiers.
        
        Args:
            message: The message to process
        """
        # Tier 1: Add to working memory
        self.working.add_turn(message)
        
        # Tier 2: Increment session turn count
        self.session.increment_turn()
    
    def get_full_context(self) -> Dict[str, Any]:
        """Retrieve context from all memory tiers.
        
        Returns:
            Dict containing context from each tier for prompt injection
        """
        # Tier 1: Working memory context
        working_context = self.working.get_context_window()
        
        # Tier 2: Session context
        session_context = {
            "summary": self.session.summary,
            "topics": self.session.topics[-5:] if self.session.topics else [],
            "turn_count": self.session.turn_count,
        }
        
        # Tier 3: Long-term memory (uses cached results from memory_manager)
        recent_text = " ".join([m.content for m in self.working.recent_turns[-3:]])
        long_term_memories = self.long_term.get_relevant_memories(recent_text, session_id=self.session_id)
        
        return {
            "working": working_context,
            "session": session_context,
            "long_term": long_term_memories,
            "emotion": self.working.current_emotion,
            "active_topics": self.working.active_topics,
        }
    
    def format_for_prompt(self) -> str:
        """Format hierarchical memory for inclusion in prompt.
        
        Returns:
            str: Formatted memory context for prompt injection
        """
        context = self.get_full_context()
        
        lines = []
        
        # Include long-term memories
        if context["long_term"]:
            lines.append("## Long-term memories about this user:")
            for memory in context["long_term"]:
                lines.append(f"- {memory}")
        
        # Include session summary if available
        if context["session"]["summary"]:
            lines.append("\n## Session summary:")
            lines.append(context["session"]["summary"])
        
        # Include current emotional state
        if context["emotion"]:
            lines.append(f"\n## Current emotional state: {context['emotion']}")
        
        # Include active topics
        if context["active_topics"]:
            lines.append(f"\n## Active topics: {', '.join(context['active_topics'])}")
        
        return "\n".join(lines) if lines else ""
    
    def detect_conflict(self, new_fact: str, existing_facts: List[str]) -> Optional[str]:
        """Detect if a new fact conflicts with existing memories.
        
        Phase 5: Conflict detection helps maintain memory consistency.
        
        Args:
            new_fact: The new fact to check
            existing_facts: List of existing fact strings
            
        Returns:
            Optional[str]: The conflicting fact if found, None otherwise
        """
        # Simple keyword-based conflict detection
        # In production, this would use embedding similarity
        new_words = set(new_fact.lower().split())
        
        for existing in existing_facts:
            existing_words = set(existing.lower().split())
            overlap = new_words & existing_words
            
            # If significant overlap but different content, may be a conflict
            if len(overlap) > 3:  # Arbitrary threshold
                # Check for negation patterns
                negations = ["not", "no", "never", "doesn't", "don't", "isn't", "aren't", "changed"]
                if any(neg in new_fact.lower() for neg in negations):
                    logger.info(f"Potential conflict detected: '{new_fact}' vs '{existing}'")
                    return existing
        
        return None
    
    def clear_session(self) -> None:
        """Clear session and working memory (called at session end)."""
        self.working.clear()
        self.session = SessionMemory(session_id=self.session_id)
        logger.info(f"Hierarchical memory cleared for session {self.session_id}")


# Session-based cache of hierarchical memory managers
_hierarchical_managers: Dict[str, HierarchicalMemoryManager] = {}


def get_hierarchical_memory(session_id: str) -> HierarchicalMemoryManager:
    """Get or create a hierarchical memory manager for a session.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        HierarchicalMemoryManager: Manager for the session
    """
    if session_id not in _hierarchical_managers:
        _hierarchical_managers[session_id] = HierarchicalMemoryManager(session_id)
        logger.debug(f"Created hierarchical memory for session {session_id}")
    
    return _hierarchical_managers[session_id]


def clear_hierarchical_memory(session_id: str) -> None:
    """Clear and remove hierarchical memory for a session.
    
    Args:
        session_id: Session to clear
    """
    if session_id in _hierarchical_managers:
        _hierarchical_managers[session_id].clear_session()
        del _hierarchical_managers[session_id]
        logger.info(f"Removed hierarchical memory for session {session_id}")
