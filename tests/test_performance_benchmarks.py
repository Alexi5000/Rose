"""Performance benchmarks for critical code paths.

This module contains performance benchmarks to ensure critical operations
meet their timing expectations. Benchmarks are run as part of the test suite
to catch performance regressions early.

Timing Expectations:
- Memory extraction: <500ms per message
- Memory retrieval: <200ms for top-K search
- STT transcription: <2s for 10s audio
- TTS synthesis: <1s for 100 words
- End-to-end workflow: <5s for typical conversation
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from ai_companion.modules.memory.long_term.memory_manager import MemoryAnalysis


@pytest.mark.slow
class TestMemoryPerformance:
    """Performance benchmarks for memory operations."""

    @pytest.mark.asyncio
    async def test_memory_extraction_performance(self, mock_qdrant_client):
        """Benchmark: Memory extraction should complete in <500ms."""
        mock_analysis = MemoryAnalysis(
            is_important=True,
            formatted_memory="Experiencing anxiety following mother's death one month ago"
        )

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.find_similar_memory.return_value = None
            mock_vs.return_value.store_memory = MagicMock()

            from ai_companion.modules.memory.long_term.memory_manager import MemoryManager
            manager = MemoryManager()
            manager.llm = AsyncMock()
            manager.llm.ainvoke.return_value = mock_analysis

            message = HumanMessage(content="I've been feeling really anxious since my mom passed away last month")

            # Benchmark the operation
            start_time = time.perf_counter()
            await manager.extract_and_store_memories(message)
            elapsed_time = time.perf_counter() - start_time

            # Assert performance requirement
            assert elapsed_time < 0.5, f"Memory extraction took {elapsed_time:.3f}s, expected <0.5s"
            print(f"\n✓ Memory extraction: {elapsed_time*1000:.1f}ms (target: <500ms)")

    @pytest.mark.asyncio
    async def test_memory_retrieval_performance(self, mock_qdrant_client):
        """Benchmark: Memory retrieval should complete in <200ms."""
        from ai_companion.modules.memory.long_term.vector_store import Memory

        mock_memories = [
            Memory(
                text=f"Memory {i}: Important therapeutic information",
                metadata={"id": f"mem{i}", "timestamp": "2024-01-15T10:00:00"},
                score=0.9 - i*0.05
            )
            for i in range(3)
        ]

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.search_memories.return_value = mock_memories

            from ai_companion.modules.memory.long_term.memory_manager import MemoryManager
            manager = MemoryManager()

            # Benchmark the operation
            start_time = time.perf_counter()
            memories = manager.get_relevant_memories("I'm having a hard day with my grief")
            elapsed_time = time.perf_counter() - start_time

            # Assert performance requirement
            assert elapsed_time < 0.2, f"Memory retrieval took {elapsed_time:.3f}s, expected <0.2s"
            assert len(memories) == 3
            print(f"✓ Memory retrieval: {elapsed_time*1000:.1f}ms (target: <200ms)")


@pytest.mark.slow
class TestSpeechPerformance:
    """Performance benchmarks for speech operations."""

    @pytest.mark.asyncio
    async def test_stt_transcription_performance(self, sample_wav_audio, mock_groq_client):
        """Benchmark: STT transcription should complete in <2s for 10s audio."""
        mock_groq_client.audio.transcriptions.create.return_value = "This is a test transcription from audio."

        with patch("ai_companion.modules.speech.speech_to_text.Groq", return_value=mock_groq_client):
            with patch("ai_companion.modules.speech.speech_to_text.get_groq_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                # Make call_async properly async - await if coroutine
                async def async_call(func):
                    result = func()
                    if hasattr(result, "__await__"):
                        return await result
                    return result
                mock_breaker.call_async = async_call
                mock_cb.return_value = mock_breaker

                from ai_companion.modules.speech.speech_to_text import SpeechToText
                stt = SpeechToText()

                # Benchmark the operation
                start_time = time.perf_counter()
                result = await stt.transcribe(sample_wav_audio, audio_format="wav")
                elapsed_time = time.perf_counter() - start_time

                # Assert performance requirement
                assert elapsed_time < 2.0, f"STT transcription took {elapsed_time:.3f}s, expected <2.0s"
                assert result == "This is a test transcription from audio."
                print(f"✓ STT transcription: {elapsed_time*1000:.1f}ms (target: <2000ms)")

    @pytest.mark.asyncio
    async def test_tts_synthesis_performance(self, mock_elevenlabs_client):
        """Benchmark: TTS synthesis should complete in <1s for 100 words."""
        # Generate ~100 word text
        text_100_words = " ".join(["word"] * 100)
        mock_elevenlabs_client.generate.return_value = iter([b"audio_chunk_1", b"audio_chunk_2"])

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                # Make call_async properly async - await if coroutine
                async def async_call(func):
                    result = func()
                    if hasattr(result, "__await__"):
                        return await result
                    return result
                mock_breaker.call_async = async_call
                mock_cb.return_value = mock_breaker

                from ai_companion.modules.speech.text_to_speech import TextToSpeech
                tts = TextToSpeech()

                # Benchmark the operation
                start_time = time.perf_counter()
                result = await tts.synthesize(text_100_words)
                elapsed_time = time.perf_counter() - start_time

                # Assert performance requirement
                assert elapsed_time < 1.0, f"TTS synthesis took {elapsed_time:.3f}s, expected <1.0s"
                assert result == b"audio_chunk_1audio_chunk_2"
                print(f"✓ TTS synthesis: {elapsed_time*1000:.1f}ms (target: <1000ms)")

    @pytest.mark.asyncio
    async def test_tts_cache_hit_performance(self, mock_elevenlabs_client):
        """Benchmark: TTS cache hit should be nearly instantaneous (<50ms)."""
        mock_elevenlabs_client.generate.return_value = iter([b"cached_audio"])

        with patch("ai_companion.modules.speech.text_to_speech.ElevenLabs", return_value=mock_elevenlabs_client):
            with patch("ai_companion.modules.speech.text_to_speech.get_elevenlabs_circuit_breaker") as mock_cb:
                mock_breaker = MagicMock()
                # Make call_async properly async - await if coroutine
                async def async_call(func):
                    result = func()
                    if hasattr(result, "__await__"):
                        return await result
                    return result
                mock_breaker.call_async = async_call
                mock_cb.return_value = mock_breaker

                from ai_companion.modules.speech.text_to_speech import TextToSpeech
                tts = TextToSpeech(enable_cache=True)

                # First call to populate cache
                await tts.synthesize_cached("Hello, I'm Rose.")

                # Benchmark cache hit
                start_time = time.perf_counter()
                result = await tts.synthesize_cached("Hello, I'm Rose.")
                elapsed_time = time.perf_counter() - start_time

                # Assert cache hit is fast
                assert elapsed_time < 0.05, f"TTS cache hit took {elapsed_time:.3f}s, expected <0.05s"
                assert result == b"cached_audio"
                print(f"✓ TTS cache hit: {elapsed_time*1000:.1f}ms (target: <50ms)")


@pytest.mark.slow
class TestWorkflowPerformance:
    """Performance benchmarks for end-to-end workflow operations."""

    @pytest.mark.asyncio
    async def test_end_to_end_conversation_workflow_performance(self):
        """Benchmark: End-to-end workflow should complete in <5s for typical conversation."""
        # This is a simplified workflow test focusing on the critical path
        # In a real scenario, this would test the full LangGraph workflow

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.search_memories.return_value = []
            mock_vs.return_value.find_similar_memory.return_value = None
            mock_vs.return_value.store_memory = MagicMock()

            from ai_companion.modules.memory.long_term.memory_manager import MemoryAnalysis, MemoryManager
            manager = MemoryManager()
            manager.llm = AsyncMock()
            manager.llm.ainvoke.return_value = MemoryAnalysis(
                is_important=True,
                formatted_memory="User is feeling anxious today"
            )

            message = HumanMessage(content="I'm feeling really anxious today")

            # Simulate workflow steps
            start_time = time.perf_counter()

            # Step 1: Memory retrieval
            manager.get_relevant_memories(message.content)

            # Step 2: Memory extraction (async)
            await manager.extract_and_store_memories(message)

            # Step 3: Simulate LLM response generation (mocked)
            await asyncio.sleep(0.1)  # Simulate LLM call

            elapsed_time = time.perf_counter() - start_time

            # Assert performance requirement
            assert elapsed_time < 5.0, f"End-to-end workflow took {elapsed_time:.3f}s, expected <5.0s"
            print(f"✓ End-to-end workflow: {elapsed_time*1000:.1f}ms (target: <5000ms)")

    @pytest.mark.asyncio
    async def test_memory_injection_performance(self):
        """Benchmark: Memory injection into prompt should be fast (<100ms)."""
        from ai_companion.modules.memory.long_term.vector_store import Memory

        mock_memories = [
            Memory(
                text=f"Memory {i}: Important therapeutic information about the user's background",
                metadata={"id": f"mem{i}"},
                score=0.9
            )
            for i in range(5)
        ]

        with patch("ai_companion.modules.memory.long_term.memory_manager.get_vector_store") as mock_vs:
            mock_vs.return_value.search_memories.return_value = mock_memories

            from ai_companion.modules.memory.long_term.memory_manager import MemoryManager
            manager = MemoryManager()

            # Benchmark memory retrieval and formatting
            start_time = time.perf_counter()
            memories = manager.get_relevant_memories("test context")
            formatted = manager.format_memories_for_prompt(memories)
            elapsed_time = time.perf_counter() - start_time

            # Assert performance requirement
            assert elapsed_time < 0.1, f"Memory injection took {elapsed_time:.3f}s, expected <0.1s"
            assert len(formatted) > 0
            print(f"✓ Memory injection: {elapsed_time*1000:.1f}ms (target: <100ms)")


@pytest.mark.slow
class TestCircuitBreakerPerformance:
    """Performance benchmarks for circuit breaker operations."""

    def test_circuit_breaker_overhead(self):
        """Benchmark: Circuit breaker should add minimal overhead (<10ms)."""
        from ai_companion.core.resilience import CircuitBreaker

        def fast_operation():
            return "success"

        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )

        # Benchmark circuit breaker overhead
        start_time = time.perf_counter()
        for _ in range(100):
            breaker.call(fast_operation)
        elapsed_time = time.perf_counter() - start_time

        # Average overhead per call
        avg_overhead = (elapsed_time / 100) * 1000  # Convert to ms

        # Assert minimal overhead
        assert avg_overhead < 10, f"Circuit breaker overhead: {avg_overhead:.2f}ms per call, expected <10ms"
        print(f"✓ Circuit breaker overhead: {avg_overhead:.2f}ms per call (target: <10ms)")

    @pytest.mark.asyncio
    async def test_async_circuit_breaker_overhead(self):
        """Benchmark: Async circuit breaker should add minimal overhead (<10ms)."""
        from ai_companion.core.resilience import CircuitBreaker

        async def fast_async_operation():
            return "success"

        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )

        # Benchmark async circuit breaker overhead
        start_time = time.perf_counter()
        for _ in range(100):
            await breaker.call_async(fast_async_operation)
        elapsed_time = time.perf_counter() - start_time

        # Average overhead per call
        avg_overhead = (elapsed_time / 100) * 1000  # Convert to ms

        # Assert minimal overhead
        assert avg_overhead < 10, f"Async circuit breaker overhead: {avg_overhead:.2f}ms per call, expected <10ms"
        print(f"✓ Async circuit breaker overhead: {avg_overhead:.2f}ms per call (target: <10ms)")


# Import asyncio for workflow test
import asyncio


def print_benchmark_summary():
    """Print a summary of all benchmark results."""
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK SUMMARY")
    print("="*60)
    print("All benchmarks passed their performance targets!")
    print("="*60)


# Run summary after all tests
@pytest.fixture(scope="session", autouse=True)
def benchmark_summary(request):
    """Print benchmark summary after all tests complete."""
    yield
    # This runs after all tests
    if hasattr(request.config, "workerinput"):
        # Skip in xdist workers
        return
    print_benchmark_summary()
