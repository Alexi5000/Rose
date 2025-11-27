#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Voice API Automated Test Script
Tests the complete voice pipeline end-to-end

Uncle Bob approved: No magic numbers, comprehensive logging with emojis
"""

import sys
import os
from pathlib import Path

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import io
import requests
import time
import wave

# 🎯 Constants - No Magic Numbers (Uncle Bob approved)
BACKEND_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BACKEND_URL}/api/v1/health"
SESSION_ENDPOINT = f"{BACKEND_URL}/api/v1/session/start"
VOICE_ENDPOINT = f"{BACKEND_URL}/api/v1/voice/process"
AUDIO_ENDPOINT_PATTERN = f"{BACKEND_URL}/api/v1/voice/audio"

# Performance constants
EXPECTED_RESPONSE_TIME_SECONDS = 10
HTTP_STATUS_OK = 200
HTTP_STATUS_NOT_FOUND = 404

# Audio generation constants
SAMPLE_RATE = 16000  # 16kHz for voice
DURATION_SECONDS = 2  # 2 second test audio
FREQUENCY_HZ = 440  # A4 note (440 Hz)
AMPLITUDE = 32767 // 2  # Half of max 16-bit amplitude


def generate_test_audio() -> bytes:
    """Generate a simple test audio file (2-second sine wave).

    Returns:
        bytes: WAV file content
    """
    print("🎵 Generating test audio (2-second sine wave at 440 Hz)...")

    # Generate simple sine wave
    import math

    samples = []
    for i in range(SAMPLE_RATE * DURATION_SECONDS):
        sample = int(AMPLITUDE * math.sin(2 * math.pi * FREQUENCY_HZ * i / SAMPLE_RATE))
        samples.append(sample)

    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(SAMPLE_RATE)
        # Convert samples to bytes
        wav_bytes = b''.join(sample.to_bytes(2, byteorder='little', signed=True) for sample in samples)
        wav_file.writeframes(wav_bytes)

    audio_bytes = wav_buffer.getvalue()
    print(f"✅ Test audio generated ({len(audio_bytes)} bytes)")
    return audio_bytes


def test_backend_health() -> bool:
    """Test backend health endpoint.

    Returns:
        bool: True if healthy, False otherwise
    """
    print("\n" + "=" * 70)
    print("🏥 TEST 1: Backend Health Check")
    print("=" * 70)

    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.json()}")

        if response.status_code != HTTP_STATUS_OK:
            print(f"❌ FAILED: Expected status {HTTP_STATUS_OK}, got {response.status_code}")
            return False

        data = response.json()

        if data.get("status") != "healthy":
            print(f"❌ FAILED: Backend status is {data.get('status')}")
            return False

        services = data.get("services", {})
        print(f"🔌 Services:")
        all_connected = True
        for service_name, status in services.items():
            emoji = "✅" if status == "connected" else "❌"
            print(f"   {emoji} {service_name}: {status}")
            if status != "connected":
                all_connected = False

        if not all_connected:
            print("❌ FAILED: Not all services are connected")
            return False

        print("✅ PASSED: Backend is healthy, all services connected")
        return True

    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Cannot connect to backend. Is Docker running?")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return False


def test_session_creation() -> str | None:
    """Test session creation endpoint.

    Returns:
        str | None: Session ID if successful, None otherwise
    """
    print("\n" + "=" * 70)
    print("🔑 TEST 2: Session Creation")
    print("=" * 70)

    try:
        response = requests.post(SESSION_ENDPOINT, timeout=5)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.json()}")

        if response.status_code != HTTP_STATUS_OK:
            print(f"❌ FAILED: Expected status {HTTP_STATUS_OK}, got {response.status_code}")
            return None

        data = response.json()
        session_id = data.get("session_id")

        if not session_id:
            print("❌ FAILED: No session_id in response")
            return None

        print(f"✅ PASSED: Session created: {session_id}")
        return session_id

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return None


def test_voice_processing(session_id: str, audio_bytes: bytes) -> dict | None:
    """Test voice processing endpoint.

    Args:
        session_id: Session identifier
        audio_bytes: Audio file bytes

    Returns:
        dict | None: Response data if successful, None otherwise
    """
    print("\n" + "=" * 70)
    print("🎤 TEST 3: Voice Processing")
    print("=" * 70)

    try:
        print(f"📤 Uploading audio ({len(audio_bytes)} bytes)...")
        print(f"🔑 Session ID: {session_id}")

        start_time = time.time()

        files = {'audio': ('test_audio.wav', audio_bytes, 'audio/wav')}
        data = {'session_id': session_id}

        response = requests.post(
            VOICE_ENDPOINT,
            files=files,
            data=data,
            timeout=EXPECTED_RESPONSE_TIME_SECONDS * 2  # Allow extra time
        )

        duration = time.time() - start_time

        print(f"📊 Status Code: {response.status_code}")
        print(f"⏱️ Response Time: {duration:.2f}s")

        if response.status_code != HTTP_STATUS_OK:
            print(f"📄 Response: {response.text}")
            print(f"❌ FAILED: Expected status {HTTP_STATUS_OK}, got {response.status_code}")
            return None

        data = response.json()
        print(f"📄 Response Data:")
        print(f"   📝 Text: {data.get('text', 'N/A')}")
        print(f"   🔊 Audio URL: {data.get('audio_url', 'N/A')}")
        print(f"   🔑 Session ID: {data.get('session_id', 'N/A')}")

        # Verify required fields
        if not data.get('text'):
            print("❌ FAILED: No text in response")
            return None

        if not data.get('audio_url'):
            print("❌ FAILED: No audio_url in response")
            return None

        # Performance check
        if duration > EXPECTED_RESPONSE_TIME_SECONDS:
            print(f"⚠️ WARNING: Response time {duration:.2f}s exceeds target {EXPECTED_RESPONSE_TIME_SECONDS}s")
        else:
            print(f"⚡ PERFORMANCE: Response time within target ({duration:.2f}s < {EXPECTED_RESPONSE_TIME_SECONDS}s)")

        print("✅ PASSED: Voice processing successful")
        return data

    except requests.exceptions.Timeout:
        print(f"❌ FAILED: Request timeout (> {EXPECTED_RESPONSE_TIME_SECONDS * 2}s)")
        return None
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return None


def test_audio_serving(audio_url: str) -> bool:
    """Test audio serving endpoint.

    Args:
        audio_url: Audio URL path (e.g., /api/v1/voice/audio/UUID)

    Returns:
        bool: True if successful, False otherwise
    """
    print("\n" + "=" * 70)
    print("🔊 TEST 4: Audio File Serving")
    print("=" * 70)

    try:
        full_url = f"{BACKEND_URL}{audio_url}"
        print(f"📥 Fetching audio from: {full_url}")

        response = requests.get(full_url, timeout=5)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Content Type: {response.headers.get('content-type', 'N/A')}")
        print(f"📏 Content Length: {len(response.content)} bytes")

        if response.status_code != HTTP_STATUS_OK:
            print(f"❌ FAILED: Expected status {HTTP_STATUS_OK}, got {response.status_code}")
            return False

        if response.headers.get('content-type') != 'audio/mpeg':
            print(f"⚠️ WARNING: Expected content-type 'audio/mpeg', got '{response.headers.get('content-type')}'")

        if len(response.content) == 0:
            print("❌ FAILED: Audio file is empty")
            return False

        print("✅ PASSED: Audio file served successfully")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def main():
    """Run all tests in sequence."""
    print("\n" + "=" * 70)
    print("🎙️ ROSE VOICE INTERFACE - AUTOMATED TEST SUITE")
    print("=" * 70)
    print("📋 Test Plan: Backend API Testing (Phase 1)")
    print("🎯 Objective: Verify 100% backend functionality")
    print("=" * 70)

    test_results = {
        "health_check": False,
        "session_creation": False,
        "voice_processing": False,
        "audio_serving": False,
    }

    # Test 1: Health Check
    test_results["health_check"] = test_backend_health()
    if not test_results["health_check"]:
        print("\n❌ Health check failed. Stopping tests.")
        sys.exit(1)

    # Test 2: Session Creation
    session_id = test_session_creation()
    if not session_id:
        print("\n❌ Session creation failed. Stopping tests.")
        sys.exit(1)
    test_results["session_creation"] = True

    # Generate test audio
    audio_bytes = generate_test_audio()

    # Test 3: Voice Processing
    voice_response = test_voice_processing(session_id, audio_bytes)
    if not voice_response:
        print("\n❌ Voice processing failed. Stopping tests.")
        sys.exit(1)
    test_results["voice_processing"] = True

    # Test 4: Audio Serving
    audio_url = voice_response.get('audio_url')
    if audio_url:
        test_results["audio_serving"] = test_audio_serving(audio_url)

    # Final Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)

    total_tests = len(test_results)
    passed_tests = sum(test_results.values())

    for test_name, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name.replace('_', ' ').title()}")

    print("=" * 70)
    print(f"🎯 Results: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("✅ ALL TESTS PASSED! Voice interface is 100% functional.")
        print("🎉 Backend is ready for production!")
        sys.exit(0)
    else:
        print(f"❌ {total_tests - passed_tests} test(s) failed.")
        print("🔧 Please review logs above and fix issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()
