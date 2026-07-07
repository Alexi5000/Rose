"""Privacy regressions for admin and maintenance diagnostics."""

import sqlite3
from datetime import datetime

import pytest
from fastapi import HTTPException

from ai_companion.core import backup as backup_module
from ai_companion.core import session_cleanup as session_cleanup_module
from ai_companion.core.privacy_logging import REDACTED_TEXT, session_id_for_log
from ai_companion.core.session_cleanup import SessionCleanupManager
from ai_companion.interfaces.web import middleware as security_middleware
from ai_companion.interfaces.web.routes import admin as admin_routes
from ai_companion.modules.memory.long_term import startup as memory_startup
from ai_companion.settings import settings


class FakeLogger:
    def __init__(self):
        self.info_calls = []
        self.error_calls = []
        self.warning_calls = []

    def info(self, event, **kwargs):
        self.info_calls.append((event, kwargs))

    def error(self, event, *args, **kwargs):
        self.error_calls.append((event, args, kwargs))

    def warning(self, event, **kwargs):
        self.warning_calls.append((event, kwargs))


@pytest.mark.asyncio
async def test_admin_status_redacts_backend_error_and_returns_generic_detail(monkeypatch):
    class FailingVectorStore:
        def get_collection_info(self):
            raise RuntimeError("qdrant echoed my private grief transcript")

    fake_logger = FakeLogger()
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(admin_routes, "logger", fake_logger)
    monkeypatch.setattr(admin_routes, "get_vector_store", lambda: FailingVectorStore())

    with pytest.raises(HTTPException) as exc_info:
        await admin_routes.get_memory_status()

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to get memory status"
    assert fake_logger.error_calls
    assert fake_logger.error_calls[0][2]["error"] == REDACTED_TEXT
    assert fake_logger.error_calls[0][2]["exc_info"] is False
    assert "private grief" not in str(fake_logger.error_calls)


def test_session_cleanup_hashes_deleted_thread_ids(monkeypatch, tmp_path):
    fake_logger = FakeLogger()
    monkeypatch.setattr(session_cleanup_module, "logger", fake_logger)

    db_path = tmp_path / "checkpoints.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE checkpoints (
            thread_id TEXT,
            checkpoint_id REAL,
            metadata TEXT
        )
        """
    )
    conn.execute("INSERT INTO checkpoints VALUES (?, ?, ?)", ("session-private-raw", 1.0, "{}"))
    conn.commit()
    conn.close()

    stats = SessionCleanupManager(str(db_path)).cleanup_old_sessions(retention_days=1)

    assert stats["sessions_deleted"] == 1
    completed_logs = [kwargs for event, kwargs in fake_logger.info_calls if event == "session_cleanup_completed"]
    assert completed_logs
    assert completed_logs[0]["thread_ids_deleted"] == [session_id_for_log("session-private-raw")]
    assert "session-private-raw" not in str(fake_logger.info_calls)


def test_session_cleanup_redacts_database_errors(monkeypatch, tmp_path):
    fake_logger = FakeLogger()
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(session_cleanup_module, "logger", fake_logger)

    db_path = tmp_path / "checkpoints.db"
    db_path.write_bytes(b"not sqlite")

    def raise_sensitive_error(_):
        raise sqlite3.OperationalError("database echoed private grief path")

    monkeypatch.setattr(sqlite3, "connect", raise_sensitive_error)

    stats = SessionCleanupManager(str(db_path)).cleanup_old_sessions(retention_days=1)

    assert stats["errors"] == ["Database error"]
    assert fake_logger.error_calls
    assert fake_logger.error_calls[0][2]["error"] == REDACTED_TEXT
    assert fake_logger.error_calls[0][2]["exc_info"] is False
    assert "private grief" not in str(fake_logger.error_calls)


def test_backup_failures_redact_exception_text(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)

    db_path = tmp_path / "memory.db"
    db_path.write_bytes(b"sqlite")
    manager = backup_module.BackupManager(str(tmp_path / "backups"))

    def raise_sensitive_copy_error(*_args, **_kwargs):
        raise RuntimeError("copy failed with private grief transcript")

    monkeypatch.setattr(backup_module.shutil, "copy2", raise_sensitive_copy_error)

    with caplog.at_level("ERROR", logger=backup_module.__name__):
        assert manager.backup_database(db_path=str(db_path)) is None

    assert REDACTED_TEXT in caplog.text
    assert "private grief" not in caplog.text


def test_secure_permission_failures_redact_path_and_exception(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    sensitive_path = tmp_path / "private-grief-audio.wav"

    def raise_sensitive_chmod_error(*_args, **_kwargs):
        raise PermissionError(f"denied for {sensitive_path} with private grief transcript")

    monkeypatch.setattr(security_middleware.os, "chmod", raise_sensitive_chmod_error)

    with caplog.at_level("ERROR", logger=security_middleware.__name__):
        security_middleware.set_secure_file_permissions(str(sensitive_path))

    assert REDACTED_TEXT in caplog.text
    assert "private grief" not in caplog.text
    assert str(sensitive_path) not in caplog.text


def test_memory_startup_logs_redacted_initialization_errors(monkeypatch, caplog):
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(
        memory_startup,
        "get_vector_store",
        lambda: (_ for _ in ()).throw(RuntimeError("qdrant echoed private grief transcript")),
    )

    with caplog.at_level("ERROR", logger=memory_startup.__name__):
        assert memory_startup.initialize_memory_system(required=False) is False

    assert REDACTED_TEXT in caplog.text
    assert "private grief" not in caplog.text


def test_memory_startup_required_error_remains_generic(monkeypatch):
    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(
        memory_startup,
        "get_vector_store",
        lambda: (_ for _ in ()).throw(RuntimeError("qdrant echoed private grief transcript")),
    )

    with pytest.raises(RuntimeError) as exc_info:
        memory_startup.initialize_memory_system(required=True)

    assert str(exc_info.value) == "ERROR Memory system initialization failed"
    assert "private grief" not in str(exc_info.value)


def test_memory_verify_logs_redacted_check_errors(monkeypatch, caplog):
    class FailingVectorStore:
        def get_collection_info(self):
            raise RuntimeError(f"qdrant check echoed private grief at {datetime.now().isoformat()}")

    monkeypatch.setattr(settings, "LOG_SENSITIVE_CONTENT", False)
    monkeypatch.setattr(memory_startup, "get_vector_store", lambda: FailingVectorStore())

    with caplog.at_level("ERROR", logger=memory_startup.__name__):
        assert memory_startup.verify_memory_system() is None

    assert REDACTED_TEXT in caplog.text
    assert "private grief" not in caplog.text
