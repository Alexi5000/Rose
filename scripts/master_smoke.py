#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Master A-Z Smoke Test
Unifies frontend and backend verification into a single robust suite.
Runs the full cycle 3 times to ensure stability.

Uncle Bob approved: No magic numbers, comprehensive logging with emojis.
"""

import io
import math
import os
import re
import sys
import time
import wave

import requests

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# 🎯 Constants - No Magic Numbers
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

# Endpoints
HEALTH_ENDPOINT = f"{BACKEND_URL}/api/v1/health"
SESSION_ENDPOINT = f"{BACKEND_URL}/api/v1/session/start"
VOICE_ENDPOINT = f"{BACKEND_URL}/api/v1/voice/process"

# Performance & Config
EXPECTED_RESPONSE_TIME_SECONDS = 10
HTTP_STATUS_OK = 200
TOTAL_CYCLES = 10
CYCLE_DELAY_SECONDS = 2

# Audio Generation Constants
SAMPLE_RATE = 16000  # 16kHz for voice
DURATION_SECONDS = 2  # 2 second test audio
FREQUENCY_HZ = 440  # A4 note (440 Hz)
AMPLITUDE = 32767 // 2  # Half of max 16-bit amplitude

def generate_test_audio() -> bytes:
    """Generate a simple test audio file (2-second sine wave)."""
    print("   🎵 Generating test audio (2-second sine wave)...")
    samples = []
    for i in range(SAMPLE_RATE * DURATION_SECONDS):
        sample = int(AMPLITUDE * math.sin(2 * math.pi * FREQUENCY_HZ * i / SAMPLE_RATE))
        samples.append(sample)

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_bytes = b"".join(sample.to_bytes(2, byteorder="little", signed=True) for sample in samples)
        wav_file.writeframes(wav_bytes)

    return wav_buffer.getvalue()

def check_frontend_assets(html_content: str) -> bool:
    """Extract and verify frontend assets (JS/CSS) from HTML."""
    print("   🎨 Checking Frontend Assets...")

    # Find script src and link href
    # <script type="module" crossorigin src="/assets/index-Bws9d4kT.js"></script>
    # <link rel="stylesheet" crossorigin href="/assets/index-C7uRqfbJ.css">

    assets = []
    assets.extend(re.findall(r'src="(/assets/[^"]+)"', html_content))
    assets.extend(re.findall(r'href="(/assets/[^"]+)"', html_content))

    if not assets:
        print("      ⚠️  No assets found in HTML (might be inline or different path)")
        return True  # Not necessarily a failure if structure is different

    all_good = True
    for asset_path in assets:
        asset_url = f"{FRONTEND_URL}{asset_path}"
        try:
            resp = requests.get(asset_url, timeout=5)
            if resp.status_code == HTTP_STATUS_OK:
                print(f"      ✅ Found asset: {asset_path}")
            else:
                print(f"      ❌ Missing asset: {asset_path} ({resp.status_code})")
                all_good = False
        except Exception as e:
            print(f"      ❌ Error fetching {asset_path}: {e}")
            all_good = False

    return all_good


def check_frontend() -> bool:
    """Verify frontend is serving content."""
    print(f"   🖥️  Checking Frontend at {FRONTEND_URL}...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == HTTP_STATUS_OK:
            # Simple check for HTML content
            if "<html" in response.text.lower() or "<!doctype" in response.text.lower():
                print("   ✅ Frontend is reachable and serving HTML")
                return check_frontend_assets(response.text)
            else:
                print("   ⚠️  Frontend reachable but content doesn't look like HTML")
                return False
        else:
            print(f"   ❌ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Frontend connection failed. Is the service running on port 3000?")
        return False
    except Exception as e:
        print(f"   ❌ Frontend check error: {e}")
        return False

def check_backend_health() -> bool:
    """Verify backend health and services."""
    print(f"   🏥 Checking Backend Health at {HEALTH_ENDPOINT}...")
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code != HTTP_STATUS_OK:
            print(f"   ❌ Backend returned status {response.status_code}")
            return False

        data = response.json()
        if data.get("status") != "healthy":
            print(f"   ❌ Backend status is {data.get('status')}")
            return False

        # Check individual services
        services = data.get("services", {})
        print("      🔌 Services:")
        all_connected = True
        for service_name, status in services.items():
            emoji = "✅" if status == "connected" else "❌"
            print(f"         {emoji} {service_name}: {status}")
            if status != "connected":
                all_connected = False

        if not all_connected:
            print("      ❌ Not all services are connected")
            return False

        print("   ✅ Backend is healthy")
        return True
    except Exception as e:
        print(f"   ❌ Backend health check error: {e}")
        return False

def run_voice_cycle(cycle_id: int) -> bool:
    """Run a full voice interaction cycle."""
    print(f"\n🔄 CYCLE {cycle_id}/{TOTAL_CYCLES}: Starting Voice Interaction Flow")
    
    # 1. Start Session
    print("   1️⃣  Starting Session...")
    try:
        session_resp = requests.post(SESSION_ENDPOINT, timeout=5)
        if session_resp.status_code != HTTP_STATUS_OK:
            print(f"      ❌ Session creation failed: {session_resp.status_code}")
            return False
        session_id = session_resp.json().get("session_id")
        print(f"      ✅ Session created: {session_id}")
    except Exception as e:
        print(f"      ❌ Session error: {e}")
        return False

    # 2. Generate Audio
    audio_bytes = generate_test_audio()

    # 3. Process Voice
    print("   2️⃣  Sending Audio to Voice Processing...")
    try:
        files = {"audio": ("test_audio.wav", audio_bytes, "audio/wav")}
        data = {"session_id": session_id}

        start_time = time.time()
        voice_resp = requests.post(
            VOICE_ENDPOINT,
            files=files,
            data=data,
            timeout=EXPECTED_RESPONSE_TIME_SECONDS * 2
        )
        duration = time.time() - start_time
        
        if voice_resp.status_code != HTTP_STATUS_OK:
            print(f"      ❌ Voice processing failed: {voice_resp.status_code}")
            print(f"      📄 Response: {voice_resp.text}")
            return False

        voice_data = voice_resp.json()
        audio_url = voice_data.get("audio_url")
        text_response = voice_data.get("text")

        print(f"      ✅ Processed in {duration:.2f}s")
        print(f'      🗣️  Response: "{text_response}"')
        
    except Exception as e:
        print(f"      ❌ Voice processing error: {e}")
        return False

    # 4. Fetch Resulting Audio
    if audio_url:
        print(f"   3️⃣  Fetching Response Audio from {audio_url}...")
        try:
            full_audio_url = f"{BACKEND_URL}{audio_url}"
            audio_resp = requests.get(full_audio_url, timeout=5)
            
            if audio_resp.status_code == HTTP_STATUS_OK and len(audio_resp.content) > 0:
                print(f"      ✅ Audio retrieved ({len(audio_resp.content)} bytes)")
            else:
                print(f"      ❌ Failed to retrieve audio: {audio_resp.status_code}")
                return False
        except Exception as e:
            print(f"      ❌ Audio fetch error: {e}")
            return False
    else:
        print("      ⚠️  No audio URL returned (might be text-only response)")

    print(f"✅ CYCLE {cycle_id} COMPLETED SUCCESSFULLY")
    return True

def main():
    print("\n" + "=" * 60)
    print("🚀 MASTER A-Z SMOKE TEST")
    print("   Target: Local Docker Environment")
    print("=" * 60)

    # Phase 1: Infrastructure Check
    print("\n🔍 PHASE 1: INFRASTRUCTURE CHECK")
    if not check_frontend():
        print("\n❌ CRITICAL: Frontend is down. Aborting.")
        sys.exit(1)
        
    if not check_backend_health():
        print("\n❌ CRITICAL: Backend is down. Aborting.")
        sys.exit(1)
        
    print("\n✅ Infrastructure looks good. Proceeding to functional cycles.")

    # Phase 2: Functional Cycles
    print(f"\n🔄 PHASE 2: FUNCTIONAL CYCLES (Running {TOTAL_CYCLES} times)")
    
    successful_cycles = 0
    for i in range(1, TOTAL_CYCLES + 1):
        if run_voice_cycle(i):
            successful_cycles += 1
        else:
            print(f"❌ CYCLE {i} FAILED")
        
        if i < TOTAL_CYCLES:
            time.sleep(CYCLE_DELAY_SECONDS)

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Cycles: {TOTAL_CYCLES}")
    print(f"Successful:   {successful_cycles}")
    print(f"Failed:       {TOTAL_CYCLES - successful_cycles}")
    
    if successful_cycles == TOTAL_CYCLES:
        print("\n🎉 ALL SYSTEMS GO! Ready for Railway deployment.")
        sys.exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED. Check logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
