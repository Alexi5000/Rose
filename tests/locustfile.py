"""Locust load testing configuration for Rose the Healer Shaman.

To run:
1. Install locust: pip install locust
2. Start the server: uvicorn ai_companion.interfaces.web.app:app
3. Run locust: locust -f tests/locustfile.py --host=http://localhost:8080
4. Open browser: http://localhost:8089
5. Configure users and spawn rate, then start test
"""

import io
import random
from locust import HttpUser, task, between, events


class RoseUser(HttpUser):
    """Simulates a user interacting with Rose."""

    # Wait 2-5 seconds between tasks (simulating thinking time)
    wait_time = between(2, 5)

    def on_start(self):
        """Called when a user starts - initialize session."""
        response = self.client.post("/api/session/start")
        if response.status_code == 200:
            self.session_id = response.json()["session_id"]
        else:
            self.session_id = "fallback-session"

    @task(1)
    def health_check(self):
        """Periodic health check (low frequency)."""
        self.client.get("/api/health")

    @task(10)
    def voice_interaction(self):
        """Main voice interaction flow (high frequency)."""
        # Create mock audio data
        audio_data = b"RIFF" + b"\x00" * 1000  # Small mock audio file

        # Send voice request
        with self.client.post(
            "/api/voice/process",
            files={"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")},
            data={"session_id": self.session_id},
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "audio_url" in data:
                    # Fetch the audio response
                    audio_url = data["audio_url"]
                    self.client.get(audio_url)
                    response.success()
                else:
                    response.failure("No audio URL in response")
            elif response.status_code == 503:
                # Service temporarily unavailable - expected under load
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def new_session(self):
        """Occasionally start a new session."""
        response = self.client.post("/api/session/start")
        if response.status_code == 200:
            self.session_id = response.json()["session_id"]


class LightLoadUser(HttpUser):
    """Simulates light load - mostly health checks."""

    wait_time = between(5, 10)

    @task(5)
    def health_check(self):
        self.client.get("/api/health")

    @task(1)
    def session_start(self):
        self.client.post("/api/session/start")


class HeavyLoadUser(HttpUser):
    """Simulates heavy load - rapid voice interactions."""

    wait_time = between(1, 2)

    def on_start(self):
        response = self.client.post("/api/session/start")
        if response.status_code == 200:
            self.session_id = response.json()["session_id"]
        else:
            self.session_id = "fallback-session"

    @task
    def rapid_voice_interactions(self):
        """Rapid fire voice interactions."""
        audio_data = b"RIFF" + b"\x00" * 500

        self.client.post(
            "/api/voice/process",
            files={"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")},
            data={"session_id": self.session_id},
        )


# Custom event handlers for detailed reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("=" * 60)
    print("Starting Rose Load Test")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("=" * 60)
    print("Rose Load Test Complete")
    print("=" * 60)
    print("\nKey Metrics:")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"Requests per second: {environment.stats.total.total_rps:.2f}")


# Load test scenarios
"""
Recommended test scenarios:

1. Baseline Test (5 users, 1/sec spawn rate, 5 min)
   - Establishes baseline performance
   - Identifies any immediate issues

2. Normal Load (20 users, 2/sec spawn rate, 10 min)
   - Simulates typical usage
   - Tests sustained performance

3. Peak Load (50 users, 5/sec spawn rate, 10 min)
   - Simulates peak hours
   - Tests system limits

4. Stress Test (100 users, 10/sec spawn rate, 5 min)
   - Identifies breaking point
   - Tests error handling under stress

5. Spike Test (10 → 100 → 10 users)
   - Tests auto-scaling
   - Tests recovery from spikes

Monitor during tests:
- Response times (p50, p95, p99)
- Error rates
- CPU usage
- Memory usage
- API costs (Groq, ElevenLabs)
- Database connections

Railway-specific considerations:
- Free tier: 500 hours/month, 512MB RAM, 1GB disk
- Starter tier: $5/month, 8GB RAM, 100GB disk
- Monitor costs during load tests
- Set up alerts for resource limits
"""
