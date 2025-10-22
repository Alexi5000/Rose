#!/usr/bin/env python3
"""Performance profiling script for AI Companion application.

This script profiles critical code paths to identify performance bottlenecks
and optimization opportunities.

Usage:
    python scripts/profile_performance.py [--operation OPERATION] [--iterations N]

Operations:
    - memory_extraction: Profile memory extraction from messages
    - memory_retrieval: Profile memory retrieval from vector store
    - speech_to_text: Profile STT transcription
    - text_to_speech: Profile TTS synthesis
    - workflow: Profile end-to-end workflow
    - all: Profile all operations (default)
"""

import argparse
import asyncio
import cProfile
import pstats

# Add src to path
import sys
import time
from io import StringIO
from pathlib import Path
from typing import Callable
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class PerformanceProfiler:
    """Profile performance of critical operations."""

    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.results = {}

    def profile_sync(self, name: str, func: Callable, *args, **kwargs) -> dict:
        """Profile a synchronous function."""
        print(f"\nProfiling {name}...")

        # Warm up
        for _ in range(10):
            func(*args, **kwargs)

        # Profile with cProfile
        profiler = cProfile.Profile()
        profiler.enable()

        start_time = time.perf_counter()
        for _ in range(self.iterations):
            func(*args, **kwargs)
        elapsed_time = time.perf_counter() - start_time

        profiler.disable()

        # Get stats
        stats_stream = StringIO()
        stats = pstats.Stats(profiler, stream=stats_stream)
        stats.strip_dirs()
        stats.sort_stats("cumulative")
        stats.print_stats(10)  # Top 10 functions

        avg_time = (elapsed_time / self.iterations) * 1000  # Convert to ms

        result = {
            "name": name,
            "iterations": self.iterations,
            "total_time_ms": elapsed_time * 1000,
            "avg_time_ms": avg_time,
            "profile_stats": stats_stream.getvalue()
        }

        self.results[name] = result

        print(f"  Average time: {avg_time:.3f}ms")
        print(f"  Total time: {elapsed_time*1000:.1f}ms")

        return result

    async def profile_async(self, name: str, func: Callable, *args, **kwargs) -> dict:
        """Profile an asynchronous function."""
        print(f"\nProfiling {name}...")

        # Warm up
        for _ in range(10):
            await func(*args, **kwargs)

        # Profile with timing
        start_time = time.perf_counter()
        for _ in range(self.iterations):
            await func(*args, **kwargs)
        elapsed_time = time.perf_counter() - start_time

        avg_time = (elapsed_time / self.iterations) * 1000  # Convert to ms

        result = {
            "name": name,
            "iterations": self.iterations,
            "total_time_ms": elapsed_time * 1000,
            "avg_time_ms": avg_time,
        }

        self.results[name] = result

        print(f"  Average time: {avg_time:.3f}ms")
        print(f"  Total time: {elapsed_time*1000:.1f}ms")

        return result

    def print_summary(self):
        """Print summary of all profiling results."""
        print("\n" + "="*70)
        print("PERFORMANCE PROFILING SUMMARY")
        print("="*70)

        # Sort by average time
        sorted_results = sorted(
            self.results.values(),
            key=lambda x: x["avg_time_ms"],
            reverse=True
        )

        print(f"\n{'Operation':<40} {'Avg Time (ms)':<15} {'Total (ms)':<15}")
        print("-"*70)

        for result in sorted_results:
            print(f"{result['name']:<40} {result['avg_time_ms']:>12.3f}   {result['total_time_ms']:>12.1f}")

        print("="*70)


async def profile_memory_extraction(profiler: PerformanceProfiler):
    """Profile memory extraction operation."""
    from langchain_core.messages import HumanMessage

    from ai_companion.modules.memory.long_term.memory_manager import MemoryAnalysis, MemoryManager

    mock_analysis = MemoryAnalysis(
        is_important=True,
        formatted_memory="Experiencing anxiety following mother's death"
    )

    with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
        mock_vs.return_value.find_similar_memory.return_value = None
        mock_vs.return_value.store_memory = MagicMock()

        manager = MemoryManager()
        manager.llm = AsyncMock()
        manager.llm.ainvoke.return_value = mock_analysis

        message = HumanMessage(content="I've been feeling really anxious since my mom passed away")

        await profiler.profile_async(
            "Memory Extraction",
            manager.extract_and_store_memories,
            message
        )


def profile_memory_retrieval(profiler: PerformanceProfiler):
    """Profile memory retrieval operation."""
    from ai_companion.modules.memory.long_term.memory_manager import MemoryManager
    from ai_companion.modules.memory.long_term.vector_store import Memory

    mock_memories = [
        Memory(
            text=f"Memory {i}: Important information",
            metadata={"id": f"mem{i}"},
            score=0.9 - i*0.05
        )
        for i in range(3)
    ]

    with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
        mock_vs.return_value.search_memories.return_value = mock_memories

        manager = MemoryManager()

        profiler.profile_sync(
            "Memory Retrieval",
            manager.get_relevant_memories,
            "I'm having a hard day"
        )


def profile_memory_formatting(profiler: PerformanceProfiler):
    """Profile memory formatting operation."""
    from ai_companion.modules.memory.long_term.memory_manager import MemoryManager

    with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store"):
        manager = MemoryManager()

        memories = [
            f"Memory {i}: Important therapeutic information about the user"
            for i in range(5)
        ]

        profiler.profile_sync(
            "Memory Formatting",
            manager.format_memories_for_prompt,
            memories
        )


async def profile_speech_to_text(profiler: PerformanceProfiler):
    """Profile STT transcription operation."""
    from ai_companion.modules.speech.speech_to_text import SpeechToText

    # Create sample audio data
    sample_audio = b"RIFF" + b"\x00" * 1000

    mock_groq_client = MagicMock()
    mock_groq_client.audio.transcriptions.create.return_value = "Test transcription"

    with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
        with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
            mock_breaker = MagicMock()
            async def async_call(func):
                result = func()
                if hasattr(result, "__await__"):
                    return await result
                return result
            mock_breaker.call_async = async_call
            mock_cb.return_value = mock_breaker

            stt = SpeechToText()

            await profiler.profile_async(
                "Speech-to-Text Transcription",
                stt.transcribe,
                sample_audio,
                audio_format="wav"
            )


async def profile_text_to_speech(profiler: PerformanceProfiler):
    """Profile TTS synthesis operation."""
    from ai_companion.modules.speech.text_to_speech import TextToSpeech

    mock_elevenlabs_client = MagicMock()
    mock_elevenlabs_client.generate.return_value = iter([b"audio_chunk"])

    with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
        with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
            mock_breaker = MagicMock()
            async def async_call(func):
                result = func()
                if hasattr(result, "__await__"):
                    return await result
                return result
            mock_breaker.call_async = async_call
            mock_cb.return_value = mock_breaker

            tts = TextToSpeech()

            await profiler.profile_async(
                "Text-to-Speech Synthesis",
                tts.synthesize,
                "Hello, I'm Rose. How are you feeling today?"
            )


def profile_circuit_breaker(profiler: PerformanceProfiler):
    """Profile circuit breaker overhead."""
    from ai_companion.core.resilience import CircuitBreaker

    def fast_operation():
        return "success"

    breaker = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=Exception
    )

    profiler.profile_sync(
        "Circuit Breaker (sync)",
        breaker.call,
        fast_operation
    )


async def profile_async_circuit_breaker(profiler: PerformanceProfiler):
    """Profile async circuit breaker overhead."""
    from ai_companion.core.resilience import CircuitBreaker

    async def fast_async_operation():
        return "success"

    breaker = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=Exception
    )

    await profiler.profile_async(
        "Circuit Breaker (async)",
        breaker.call_async,
        fast_async_operation
    )


async def main():
    """Main profiling entry point."""
    parser = argparse.ArgumentParser(description="Profile AI Companion performance")
    parser.add_argument(
        "--operation",
        choices=["memory_extraction", "memory_retrieval", "memory_formatting",
                 "speech_to_text", "text_to_speech", "circuit_breaker", "all"],
        default="all",
        help="Operation to profile"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of iterations for profiling"
    )

    args = parser.parse_args()

    profiler = PerformanceProfiler(iterations=args.iterations)

    print(f"Performance Profiling - {args.iterations} iterations per operation")
    print("="*70)

    operations = {
        "memory_extraction": profile_memory_extraction,
        "memory_retrieval": profile_memory_retrieval,
        "memory_formatting": profile_memory_formatting,
        "speech_to_text": profile_speech_to_text,
        "text_to_speech": profile_text_to_speech,
        "circuit_breaker": profile_circuit_breaker,
    }

    if args.operation == "all":
        # Run all operations
        await profile_memory_extraction(profiler)
        profile_memory_retrieval(profiler)
        profile_memory_formatting(profiler)
        await profile_speech_to_text(profiler)
        await profile_text_to_speech(profiler)
        profile_circuit_breaker(profiler)
        await profile_async_circuit_breaker(profiler)
    else:
        # Run specific operation
        operation_func = operations[args.operation]
        if asyncio.iscoroutinefunction(operation_func):
            await operation_func(profiler)
        else:
            operation_func(profiler)

    profiler.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
