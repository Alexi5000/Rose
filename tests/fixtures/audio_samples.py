"""Audio sample fixtures for speech-to-text testing.

This module provides pytest fixtures for test audio files in various formats.
The audio files are minimal valid files for testing format detection and processing.
"""

import io
import wave
from pathlib import Path

import pytest


@pytest.fixture
def sample_wav_audio() -> bytes:
    """Generate a minimal valid WAV audio file for testing.

    Returns:
        bytes: Valid WAV format audio data (1 second, mono, 16kHz)
    """
    # Create a minimal WAV file in memory
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        # Set parameters: 1 channel (mono), 2 bytes per sample, 16kHz sample rate
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)

        # Generate 1 second of silence (16000 frames)
        silence = b"\x00\x00" * 16000
        wav_file.writeframes(silence)

    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def sample_mp3_audio() -> bytes:
    """Generate a minimal MP3 audio file for testing.

    Note: This creates a minimal MP3 header. For actual audio processing tests,
    you may need real MP3 files with valid audio data.

    Returns:
        bytes: Minimal MP3 format audio data
    """
    # Minimal MP3 frame header (MPEG-1 Layer 3, 128kbps, 44.1kHz, mono)
    # This is a simplified MP3 header for format detection testing
    mp3_header = bytes([
        0xFF, 0xFB,  # Sync word and MPEG version
        0x90, 0x00,  # Bitrate and sample rate
    ])

    # Add some padding to make it look like a real MP3
    mp3_data = mp3_header + (b"\x00" * 1024)

    return mp3_data


@pytest.fixture
def sample_invalid_audio() -> bytes:
    """Generate invalid audio data for error testing.

    Returns:
        bytes: Invalid audio data that should fail format detection
    """
    return b"This is not valid audio data"


@pytest.fixture
def sample_empty_audio() -> bytes:
    """Generate empty audio data for error testing.

    Returns:
        bytes: Empty audio data
    """
    return b""


@pytest.fixture
def sample_oversized_audio() -> bytes:
    """Generate oversized audio data for size limit testing.

    Returns:
        bytes: Audio data exceeding typical size limits (30MB)
    """
    # Create 30MB of data (exceeds typical 25MB limit)
    return b"\x00" * (30 * 1024 * 1024)


@pytest.fixture
def audio_file_path(tmp_path: Path, sample_wav_audio: bytes) -> Path:
    """Create a temporary WAV audio file for file-based testing.

    Args:
        tmp_path: Pytest temporary directory fixture
        sample_wav_audio: WAV audio data fixture

    Returns:
        Path: Path to temporary WAV file
    """
    audio_path = tmp_path / "test_audio.wav"
    audio_path.write_bytes(sample_wav_audio)
    return audio_path


@pytest.fixture
def mp3_file_path(tmp_path: Path, sample_mp3_audio: bytes) -> Path:
    """Create a temporary MP3 audio file for file-based testing.

    Args:
        tmp_path: Pytest temporary directory fixture
        sample_mp3_audio: MP3 audio data fixture

    Returns:
        Path: Path to temporary MP3 file
    """
    audio_path = tmp_path / "test_audio.mp3"
    audio_path.write_bytes(sample_mp3_audio)
    return audio_path
