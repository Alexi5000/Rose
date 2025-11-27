#!/usr/bin/env python3
"""End-to-end voice processing test script.

This script will:
- Create a new session via /api/v1/session/start
- Generate a small WAV file (1 second 16kHz) in memory
- POST it as a multipart form to /api/v1/voice/process
- Print the JSON response and status code

Usage:
    python scripts/e2e_test_voice.py
"""

import io
import math
import wave
import uuid
import requests

# Config
BASE_URL = "http://localhost:8000/api/v1"


def create_sample_wav(duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    num_samples = int(duration_seconds * sample_rate)
    frequency = 440.0
    samples = []
    for i in range(num_samples):
        value = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
        samples.append(value)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for sample in samples:
            wav_file.writeframes(sample.to_bytes(2, byteorder="little", signed=True))

    buffer.seek(0)
    return buffer.read()


def start_session():
    url = f"{BASE_URL}/session/start"
    r = requests.post(url, timeout=5)
    r.raise_for_status()
    return r.json()["session_id"]


def process_voice(session_id: str, wav_bytes: bytes):
    url = f"{BASE_URL}/voice/process"
    files = {
        "audio": ("test.wav", wav_bytes, "audio/wav"),
    }
    data = {"session_id": session_id}
    r = requests.post(url, files=files, data=data, timeout=60)
    return r


def main():
    print("Starting E2E voice test...")
    session_id = start_session()
    print("Session started:", session_id)

    wav_bytes = create_sample_wav(duration_seconds=2.0)
    print("Posting voice data (2s WAV) to backend...")
    r = process_voice(session_id, wav_bytes)
    print("Status:", r.status_code)
    try:
        print("Response JSON:", r.json())
    except Exception:
        print("Response text:", r.text)


if __name__ == "__main__":
    main()
