"""Sample audio file fixtures for STT testing."""

import io
import wave
from pathlib import Path
from typing import Iterator

import pytest


def create_sample_wav(duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """
    Create a minimal valid WAV file for testing.

    Args:
        duration_seconds: Duration of the audio in seconds
        sample_rate: Sample rate in Hz

    Returns:
        WAV file as bytes
    """
    num_samples = int(duration_seconds * sample_rate)

    # Create a simple sine wave pattern (440 Hz tone)
    import math

    frequency = 440.0
    samples = []
    for i in range(num_samples):
        value = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
        samples.append(value)

    # Write to WAV format
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Convert samples to bytes
        for sample in samples:
            wav_file.writeframes(sample.to_bytes(2, byteorder="little", signed=True))

    buffer.seek(0)
    return buffer.read()


def create_sample_mp3_header() -> bytes:
    """
    Create a minimal MP3 file header for testing.
    Note: This is a simplified MP3 header, not a full valid MP3 file.
    """
    # MP3 frame header (simplified for testing purposes)
    # This creates a minimal valid MP3 frame sync pattern
    mp3_header = bytes(
        [
            0xFF,
            0xFB,  # Frame sync + MPEG 1 Layer 3
            0x90,
            0x00,  # Bitrate + sample rate
        ]
    )

    # Add some dummy audio data
    dummy_data = bytes([0x00] * 100)

    return mp3_header + dummy_data


@pytest.fixture
def sample_wav_file(tmp_path: Path) -> Iterator[Path]:
    """Create a temporary WAV file for testing."""
    wav_path = tmp_path / "test_audio.wav"
    wav_data = create_sample_wav(duration_seconds=2.0)
    wav_path.write_bytes(wav_data)
    yield wav_path


@pytest.fixture
def sample_mp3_file(tmp_path: Path) -> Iterator[Path]:
    """Create a temporary MP3 file for testing."""
    mp3_path = tmp_path / "test_audio.mp3"
    mp3_data = create_sample_mp3_header()
    mp3_path.write_bytes(mp3_data)
    yield mp3_path


@pytest.fixture
def sample_wav_bytes() -> bytes:
    """Provide sample WAV audio data as bytes."""
    return create_sample_wav(duration_seconds=1.0)


@pytest.fixture
def sample_mp3_bytes() -> bytes:
    """Provide sample MP3 audio data as bytes."""
    return create_sample_mp3_header()


@pytest.fixture
def sample_audio_buffer() -> io.BytesIO:
    """Provide sample audio data in a BytesIO buffer."""
    wav_data = create_sample_wav(duration_seconds=1.5)
    return io.BytesIO(wav_data)
