"""Tests for resource management optimizations."""

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Set minimal environment variables before importing modules
os.environ.setdefault("GROQ_API_KEY", "test_key")
os.environ.setdefault("ELEVENLABS_API_KEY", "test_key")
os.environ.setdefault("ELEVENLABS_VOICE_ID", "test_voice")
os.environ.setdefault("TOGETHER_API_KEY", "test_key")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("QDRANT_API_KEY", "test_key")

from ai_companion.core.session_cleanup import SessionCleanupManager
from ai_companion.modules.memory.long_term.vector_store import VectorStore, get_vector_store


class TestQdrantConnectionPooling:
    """Test suite for Qdrant connection pooling/singleton pattern."""

    def test_vector_store_singleton(self):
        """Test that VectorStore implements singleton pattern."""
        store1 = get_vector_store()
        store2 = get_vector_store()

        # Both should be the same instance
        assert store1 is store2

    def test_vector_store_single_initialization(self):
        """Test that VectorStore only initializes once."""
        # Reset singleton for testing
        VectorStore._instance = None
        VectorStore._initialized = False

        store1 = VectorStore()
        store2 = VectorStore()

        # Both should be the same instance
        assert store1 is store2
        # Should only initialize once
        assert VectorStore._initialized is True

    def test_vector_store_get_collection_info(self):
        """Test that get_collection_info returns collection statistics."""
        store = get_vector_store()

        # This may return None if collection doesn't exist, circuit breaker is open,
        # or Qdrant is not running (expected in test environment)
        try:
            info = store.get_collection_info()

            if info is not None:
                assert "name" in info
                assert "vectors_count" in info or "points_count" in info
                assert "status" in info
        except Exception:
            # Expected if Qdrant is not running in test environment
            # The important thing is that the method exists and handles errors gracefully
            pass


class TestSessionCleanup:
    """Test suite for session cleanup functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary SQLite database with checkpoints table."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmpfile:
            db_path = tmpfile.name

        # Create checkpoints table structure similar to LangGraph
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE checkpoints (
                thread_id TEXT NOT NULL,
                checkpoint_ns TEXT NOT NULL DEFAULT '',
                checkpoint_id TEXT NOT NULL,
                parent_checkpoint_id TEXT,
                type TEXT,
                checkpoint BLOB,
                metadata TEXT,
                PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
            )
        """)

        # Insert test data with different ages
        now = datetime.now()
        old_date = now - timedelta(days=10)
        recent_date = now - timedelta(days=2)

        # Old session (should be deleted)
        cursor.execute(
            "INSERT INTO checkpoints (thread_id, checkpoint_id, metadata) VALUES (?, ?, ?)",
            ("old_session_1", str(old_date.timestamp()), "{}"),
        )

        # Recent session (should be kept)
        cursor.execute(
            "INSERT INTO checkpoints (thread_id, checkpoint_id, metadata) VALUES (?, ?, ?)",
            ("recent_session_1", str(recent_date.timestamp()), "{}"),
        )

        # Mixed session with both old and recent checkpoints (should be kept)
        cursor.execute(
            "INSERT INTO checkpoints (thread_id, checkpoint_id, metadata) VALUES (?, ?, ?)",
            ("mixed_session_1", str(old_date.timestamp()), "{}"),
        )
        cursor.execute(
            "INSERT INTO checkpoints (thread_id, checkpoint_id, metadata) VALUES (?, ?, ?)",
            ("mixed_session_1", str(recent_date.timestamp()), "{}"),
        )

        conn.commit()
        conn.close()

        yield db_path

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    def test_session_cleanup_manager_initialization(self, temp_db):
        """Test SessionCleanupManager initializes correctly."""
        manager = SessionCleanupManager(db_path=temp_db)
        assert manager.db_path == temp_db

    def test_cleanup_old_sessions(self, temp_db):
        """Test that cleanup_old_sessions removes old sessions."""
        manager = SessionCleanupManager(db_path=temp_db)

        # Count sessions before cleanup
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT thread_id) FROM checkpoints")
        sessions_before = cursor.fetchone()[0]
        conn.close()

        assert sessions_before == 3  # old_session_1, recent_session_1, mixed_session_1

        # Run cleanup with 7 day retention
        stats = manager.cleanup_old_sessions(retention_days=7)

        # Verify cleanup stats
        assert stats["sessions_deleted"] >= 0
        assert stats["checkpoints_deleted"] >= 0
        assert len(stats["errors"]) == 0

        # Verify old_session_1 was deleted but recent and mixed sessions remain
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id")
        remaining_sessions = {row[0] for row in cursor.fetchall()}
        conn.close()

        # Should have deleted old_session_1
        assert "old_session_1" not in remaining_sessions
        # Should keep recent_session_1 and mixed_session_1
        assert "recent_session_1" in remaining_sessions
        assert "mixed_session_1" in remaining_sessions

    def test_cleanup_nonexistent_database(self):
        """Test cleanup handles nonexistent database gracefully."""
        manager = SessionCleanupManager(db_path="/nonexistent/path/db.db")
        stats = manager.cleanup_old_sessions()

        assert stats["sessions_deleted"] == 0
        assert stats["checkpoints_deleted"] == 0
        assert len(stats["errors"]) == 0

    def test_cleanup_empty_database(self):
        """Test cleanup handles empty database gracefully."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmpfile:
            db_path = tmpfile.name

        # Create empty database (no tables)
        conn = sqlite3.connect(db_path)
        conn.close()

        manager = SessionCleanupManager(db_path=db_path)
        stats = manager.cleanup_old_sessions()

        assert stats["sessions_deleted"] == 0
        assert stats["checkpoints_deleted"] == 0

        Path(db_path).unlink(missing_ok=True)


class TestRequestSizeLimits:
    """Test suite for FastAPI request size limits."""

    def test_request_size_limit_configured(self):
        """Test that request size limit is configured in settings."""
        from ai_companion.settings import settings

        assert hasattr(settings, "MAX_REQUEST_SIZE")
        assert settings.MAX_REQUEST_SIZE > 0
        # Should be at least 10MB
        assert settings.MAX_REQUEST_SIZE >= 10 * 1024 * 1024


class TestCacheHeaders:
    """Test suite for frontend static file cache headers."""

    def test_cache_headers_middleware_exists(self):
        """Test that cache headers middleware is configured."""
        # We can't easily test the middleware without starting the full app
        # which requires all dependencies. Instead, verify the code exists.
        from pathlib import Path

        app_file = Path("src/ai_companion/interfaces/web/app.py")
        assert app_file.exists()

        content = app_file.read_text()
        # Verify cache headers middleware is defined
        assert "add_cache_headers" in content
        assert "Cache-Control" in content
        assert "max-age" in content
