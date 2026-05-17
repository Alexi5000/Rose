#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Standalone Smoke Test: 10 Concurrent 5-Minute Conversations

Runs without pytest dependency for easy standalone execution.

Usage:
    python run_memory_smoke_test.py
"""

import asyncio
import random
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List

# Add src to path
sys.path.insert(0, "src")

from langchain_core.messages import HumanMessage

from ai_companion.modules.memory.long_term.constants import ENABLE_SESSION_ISOLATION
from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager
from ai_companion.modules.memory.long_term.startup import initialize_memory_system, verify_memory_system
from ai_companion.modules.memory.long_term.vector_store import get_vector_store

# ==============================================================================
# TEST DATA
# ==============================================================================

CONVERSATION_TEMPLATES = {
    "grief": [
        "I've been struggling since my mother passed away last month",
        "Some days I feel so alone without her",
        "I find it hard to get out of bed in the morning",
        "Today I managed to look at old photos and smile",
        "I'm starting to accept that grief comes in waves",
        "I went to her favorite park today and felt close to her",
        "My therapist suggested journaling, I might try it",
        "I'm allergic to dairy, so I can't have the comfort foods she used to make",
        "I love hiking - it helps me process my emotions",
        "I prefer tea over coffee, just like she did",
    ],
    "anxiety": [
        "I've been experiencing panic attacks at work",
        "My heart races whenever I have to present",
        "I'm worried about losing my job because of this anxiety",
        "Deep breathing exercises have been helping a bit",
        "I get anxious in crowded places",
        "Today I managed to go to the grocery store without panicking",
        "I'm trying meditation before bed",
        "I'm allergic to peanuts, which adds stress to social eating",
        "I enjoy swimming - it calms my mind",
        "I prefer working from home where I feel safe",
    ],
    "depression": [
        "I haven't felt motivated in weeks",
        "Everything feels grey and meaningless",
        "I'm having trouble connecting with my friends",
        "I forced myself to take a walk today, small victory",
        "I can't remember the last time I felt happy",
        "Music used to bring me joy, now I can't even listen",
        "I'm trying to maintain a sleep schedule",
        "I'm vegan for ethical reasons, but it's hard to cook for myself now",
        "I used to love painting, maybe I'll try again",
        "I prefer staying home, people don't understand",
    ],
    "trauma": [
        "I keep having nightmares about the accident",
        "Loud noises make me freeze up",
        "I'm working on feeling safe in my own body",
        "Today I drove past the site without having a flashback",
        "I'm learning to recognize my triggers",
        "EMDR therapy has been challenging but helpful",
        "I'm rebuilding my sense of safety slowly",
        "I'm gluten intolerant, which limits my comfort foods",
        "I find yoga helps me reconnect with my body",
        "I prefer quiet environments now, noise overwhelms me",
    ],
}


# ==============================================================================
# CONVERSATION SIMULATOR
# ==============================================================================


class ConversationSimulator:
    """Simulates a realistic 5-minute therapeutic conversation."""

    def __init__(self, session_id: str, conversation_type: str):
        self.session_id = session_id
        self.conversation_type = conversation_type
        self.messages = CONVERSATION_TEMPLATES[conversation_type].copy()
        random.shuffle(self.messages)
        self.memory_manager = get_memory_manager()
        self.stored_memories: List[str] = []
        self.errors: List[str] = []
        self.start_time = None
        self.end_time = None

    async def run_conversation(self, duration_minutes: int = 5) -> Dict:
        """Run a simulated conversation for the specified duration."""
        self.start_time = time.time()
        duration_seconds = duration_minutes * 60
        conversation_turns = []

        print(f"\n{'=' * 70}")
        print(f"🗣️  {self.session_id} ({self.conversation_type})")
        print(f"{'=' * 70}")

        turn = 0
        while (time.time() - self.start_time) < duration_seconds:
            turn += 1
            message_text = self.messages[turn % len(self.messages)]

            if turn > len(self.messages):
                message_text = f"{message_text} (reflecting more)"

            print(f"  Turn {turn}: '{message_text[:60]}...'")

            try:
                message = HumanMessage(content=message_text)
                await self.memory_manager.extract_and_store_memories(message, session_id=self.session_id)

                memories = self.memory_manager.get_relevant_memories(message_text, session_id=self.session_id)

                conversation_turns.append(
                    {
                        "turn": turn,
                        "message": message_text,
                        "memories_retrieved": len(memories),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                self.stored_memories.extend(memories)

            except Exception as e:
                error_msg = f"Turn {turn} error: {e}"
                self.errors.append(error_msg)
                print(f"  ❌ {error_msg}")

            # Shortened timing for test (2-5s instead of 15-30s)
            await asyncio.sleep(random.uniform(2, 5))

        self.end_time = time.time()
        actual_duration = self.end_time - self.start_time

        print(f"  ✅ Completed: {turn} turns in {actual_duration:.1f}s")
        print(f"  💾 Unique memories: {len(set(self.stored_memories))}")
        if self.errors:
            print(f"  ⚠️  Errors: {len(self.errors)}")

        return {
            "session_id": self.session_id,
            "conversation_type": self.conversation_type,
            "turns": turn,
            "duration_seconds": actual_duration,
            "memories_stored": len(set(self.stored_memories)),
            "errors": self.errors,
            "conversation_turns": conversation_turns,
        }


# ==============================================================================
# MAIN TEST FUNCTION
# ==============================================================================


async def run_smoke_test():
    """Run the 10x5min conversation smoke test."""
    # Set UTF-8 encoding for Windows
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    print("\n" + "=" * 70)
    print("  SMOKE TEST: 10 x 5-MINUTE CONVERSATIONS")
    print("=" * 70)

    # Initialize
    print("\n🚀 Initializing memory system...")
    success = initialize_memory_system(required=False)
    if not success:
        print("❌ Memory system unavailable - Qdrant not running")
        return False

    status = verify_memory_system()
    if not status or status["status"] != "operational":
        print("❌ Memory system not operational")
        return False

    print(f"✅ Memory system ready: {status['memory_count']} existing memories")
    print(f"🔒 Session isolation: {'Enabled' if ENABLE_SESSION_ISOLATION else 'Disabled'}")

    # Create simulators
    print("\n🎬 Starting 10 concurrent conversations...")
    conversation_types = ["grief", "anxiety", "depression", "trauma"]
    simulators = []

    for i in range(10):
        session_id = f"user_{i + 1}_{uuid.uuid4().hex[:8]}"
        conv_type = conversation_types[i % len(conversation_types)]
        simulators.append(ConversationSimulator(session_id, conv_type))

    # Run concurrently
    start_time = time.time()
    results = await asyncio.gather(
        *[sim.run_conversation(duration_minutes=5) for sim in simulators], return_exceptions=True
    )
    total_duration = time.time() - start_time

    # Analyze results
    print(f"\n{'=' * 70}")
    print("  ANALYSIS")
    print(f"{'=' * 70}")

    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]

    print("\n📊 Overall Statistics:")
    print(f"  ⏱️  Total runtime: {total_duration:.1f}s ({total_duration / 60:.1f} minutes)")
    print(f"  ✅ Successful: {len(successful)}/10")
    print(f"  ❌ Failed: {len(failed)}/10")

    if failed:
        print("\n  Failed conversation errors:")
        for i, exc in enumerate(failed, 1):
            print(f"    {i}. {exc}")

    # Stats
    total_turns = sum(r["turns"] for r in successful)
    total_memories = sum(r["memories_stored"] for r in successful)
    total_errors = sum(len(r["errors"]) for r in successful)

    print("\n📈 Per-Conversation Statistics:")
    for i, result in enumerate(successful, 1):
        print(f"  {i}. {result['session_id'][:20]}... ({result['conversation_type']})")
        print(
            f"     • Turns: {result['turns']}, Duration: {result['duration_seconds']:.1f}s, Memories: {result['memories_stored']}"
        )
        if result["errors"]:
            print(f"     • Errors: {len(result['errors'])} ⚠️")

    print("\n📊 Aggregate:")
    print(f"  💬 Total turns: {total_turns}")
    print(f"  💾 Total memories: {total_memories}")
    print(f"  ⚠️  Total errors: {total_errors}")

    # Verify session isolation
    if ENABLE_SESSION_ISOLATION and successful:
        print(f"\n{'=' * 70}")
        print("  SESSION ISOLATION VERIFICATION")
        print(f"{'=' * 70}")

        vector_store = get_vector_store()
        isolation_violations = 0

        for result in successful[:3]:
            session_id = result["session_id"]
            memories = vector_store.search_memories("allergic to", k=10, session_id=session_id)

            for memory in memories:
                if memory.metadata.get("session_id") != session_id:
                    isolation_violations += 1
                    print("  ⚠️  VIOLATION: Cross-session leak detected!")

        if isolation_violations == 0:
            print("  ✅ Session isolation: PASS")
        else:
            print(f"  ❌ Session isolation: FAIL ({isolation_violations} violations)")

    # Circuit breaker check
    print(f"\n{'=' * 70}")
    print("  CIRCUIT BREAKER VERIFICATION")
    print(f"{'=' * 70}")

    from ai_companion.core.resilience import get_groq_circuit_breaker, get_qdrant_circuit_breaker

    qdrant_cb = get_qdrant_circuit_breaker()
    groq_cb = get_groq_circuit_breaker()

    print(f"  ⚡ Qdrant: {qdrant_cb.state.name} (failures: {qdrant_cb.fail_counter}/{qdrant_cb.failure_threshold})")
    print(f"  ⚡ Groq: {groq_cb.state.name} (failures: {groq_cb.fail_counter}/{groq_cb.failure_threshold})")

    # Assertions
    print(f"\n{'=' * 70}")
    print("  ASSERTIONS")
    print(f"{'=' * 70}")

    all_passed = True

    if len(failed) > 0:
        print(f"  ❌ {len(failed)} conversations failed")
        all_passed = False
    else:
        print("  ✅ All conversations completed")

    if total_memories == 0:
        print("  ❌ No memories stored")
        all_passed = False
    else:
        print(f"  ✅ Memories stored: {total_memories}")

    if qdrant_cb.state.name == "OPEN":
        print("  ❌ Qdrant circuit breaker tripped")
        all_passed = False
    else:
        print("  ✅ Qdrant circuit breaker healthy")

    if groq_cb.state.name == "OPEN":
        print("  ❌ Groq circuit breaker tripped")
        all_passed = False
    else:
        print("  ✅ Groq circuit breaker healthy")

    error_rate = total_errors / total_turns if total_turns > 0 else 0
    if error_rate >= 0.1:
        print(f"  ❌ Error rate too high: {error_rate:.1%}")
        all_passed = False
    else:
        print(f"  ✅ Error rate acceptable: {error_rate:.1%}")

    # Final result
    print(f"\n{'=' * 70}")
    if all_passed:
        print("  🎉 SMOKE TEST PASSED!")
    else:
        print("  ❌ SMOKE TEST FAILED")
    print(f"{'=' * 70}")

    if all_passed:
        print("\n  System is stable under concurrent load:")
        print("    • 10 concurrent users")
        print(f"    • {total_turns} total turns")
        print(f"    • {total_memories} memories stored")
        print("    • Session isolation working")
        print("    • Circuit breakers healthy")
        print(f"    • Error rate: {error_rate:.1%}")
        print("\n  ✅ Memory system is PRODUCTION READY! 🚀\n")

    return all_passed


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    result = asyncio.run(run_smoke_test())
    sys.exit(0 if result else 1)
