"""Test to verify test infrastructure is properly set up.

This test module validates that all fixtures are accessible and working correctly.
"""

import pytest


@pytest.mark.unit
def test_mock_groq_client_fixture(mock_groq_client):
    """Verify mock Groq client fixture is available and functional."""
    assert mock_groq_client is not None

    # Test transcription mock
    result = mock_groq_client.audio.transcriptions.create()
    assert "transcription" in result.text.lower()


@pytest.mark.unit
def test_mock_qdrant_client_fixture(mock_qdrant_client):
    """Verify mock Qdrant client fixture is available and functional."""
    assert mock_qdrant_client is not None

    # Test search mock
    results = mock_qdrant_client.search()
    assert len(results) >= 1
    assert results[0].score > 0.8


@pytest.mark.unit
def test_sample_wav_audio_fixture(sample_wav_audio):
    """Verify WAV audio sample fixture is available and valid."""
    assert sample_wav_audio is not None
    assert len(sample_wav_audio) > 0
    # Check WAV header (RIFF)
    assert sample_wav_audio[:4] == b"RIFF"


@pytest.mark.unit
def test_sample_mp3_audio_fixture(sample_mp3_audio):
    """Verify MP3 audio sample fixture is available and valid."""
    assert sample_mp3_audio is not None
    assert len(sample_mp3_audio) > 0
    # Check MP3 sync word
    assert sample_mp3_audio[0] == 0xFF
    assert sample_mp3_audio[1] == 0xFB


@pytest.mark.unit
def test_mock_responses_fixtures(
    mock_groq_transcription_response, mock_qdrant_search_response, mock_memory_extraction_result
):
    """Verify mock response fixtures are available and properly structured."""
    # Test Groq transcription response
    assert "text" in mock_groq_transcription_response
    assert mock_groq_transcription_response["language"] == "en"

    # Test Qdrant search response
    assert len(mock_qdrant_search_response) == 3
    assert mock_qdrant_search_response[0]["score"] > 0.9

    # Test memory extraction result
    assert "memory" in mock_memory_extraction_result
    assert "emotion" in mock_memory_extraction_result


@pytest.mark.unit
def test_test_settings_fixture(test_settings):
    """Verify test settings fixture is available and contains required keys."""
    assert test_settings is not None
    assert "GROQ_API_KEY" in test_settings
    assert "QDRANT_URL" in test_settings
    assert test_settings["MEMORY_TOP_K"] == 3


@pytest.mark.unit
def test_audio_file_fixtures(audio_file_path, mp3_file_path):
    """Verify audio file path fixtures create actual files."""
    assert audio_file_path.exists()
    assert audio_file_path.suffix == ".wav"

    assert mp3_file_path.exists()
    assert mp3_file_path.suffix == ".mp3"
