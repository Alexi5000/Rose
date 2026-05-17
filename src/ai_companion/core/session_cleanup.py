"""Session cleanup utilities for managing old session data."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from ai_companion.core.logging_config import get_logger
from ai_companion.settings import settings

logger = get_logger(__name__)


class SessionCleanupManager:
    """Manager for cleaning up old session data from SQLite checkpointer."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize session cleanup manager.

        Args:
            db_path: Path to SQLite database. Defaults to settings.SHORT_TERM_MEMORY_DB_PATH
        """
        self.db_path = db_path or settings.SHORT_TERM_MEMORY_DB_PATH

    def cleanup_old_sessions(self, retention_days: Optional[int] = None) -> Dict[str, Any]:
        """Clean up sessions older than specified retention period.

        Args:
            retention_days: Number of days to retain sessions. Defaults to settings.SESSION_RETENTION_DAYS

        Returns:
            dict: Statistics about cleanup operation (sessions_deleted, checkpoints_deleted, errors)
        """
        retention_days = retention_days or settings.SESSION_RETENTION_DAYS
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        stats: Dict[str, Any] = {"sessions_deleted": 0, "checkpoints_deleted": 0, "errors": []}

        # Check if database exists
        db_file = Path(self.db_path)
        if not db_file.exists():
            logger.info("session_cleanup_skipped", reason="database_not_found", db_path=self.db_path)
            return stats

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if checkpoints table exists (LangGraph creates this)
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='checkpoints'
            """)

            if not cursor.fetchone():
                logger.info("session_cleanup_skipped", reason="checkpoints_table_not_found")
                conn.close()
                return stats

            # Get table schema to understand structure
            cursor.execute("PRAGMA table_info(checkpoints)")
            columns = {row[1] for row in cursor.fetchall()}

            # LangGraph checkpoints table typically has: thread_id, checkpoint_ns, checkpoint_id,
            # parent_checkpoint_id, type, checkpoint, metadata
            # We'll use checkpoint_id which contains timestamp information

            if "checkpoint_id" in columns and "metadata" in columns:
                # Count sessions before cleanup
                cursor.execute("SELECT COUNT(DISTINCT thread_id) FROM checkpoints")
                sessions_before = cursor.fetchone()[0]

                # Count checkpoints before cleanup
                cursor.execute("SELECT COUNT(*) FROM checkpoints")
                checkpoints_before = cursor.fetchone()[0]

                logger.info(
                    "session_cleanup_analysis",
                    total_sessions=sessions_before,
                    total_checkpoints=checkpoints_before,
                    retention_days=retention_days,
                    cutoff_date=cutoff_date.isoformat(),
                )

                # LangGraph checkpoint_id format is typically a timestamp-based UUID
                # We'll identify old sessions by finding thread_ids where ALL checkpoints
                # are older than the cutoff date

                # First, find thread_ids that have at least one recent checkpoint
                # (these are active sessions we want to keep)
                cursor.execute(
                    """
                    SELECT DISTINCT thread_id
                    FROM checkpoints
                    WHERE checkpoint_id > ?
                """,
                    (cutoff_date.timestamp(),),
                )

                active_thread_ids = {row[0] for row in cursor.fetchall()}

                # Now find all thread_ids
                cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
                all_thread_ids = {row[0] for row in cursor.fetchall()}

                # Thread IDs to delete are those with no recent activity
                thread_ids_to_delete = all_thread_ids - active_thread_ids

                if thread_ids_to_delete:
                    # Delete checkpoints for old sessions
                    placeholders = ",".join("?" * len(thread_ids_to_delete))
                    cursor.execute(
                        f"DELETE FROM checkpoints WHERE thread_id IN ({placeholders})",
                        tuple(thread_ids_to_delete),
                    )

                    stats["checkpoints_deleted"] = cursor.rowcount
                    stats["sessions_deleted"] = len(thread_ids_to_delete)

                    conn.commit()

                    logger.info(
                        "session_cleanup_completed",
                        sessions_deleted=stats["sessions_deleted"],
                        checkpoints_deleted=stats["checkpoints_deleted"],
                        sessions_remaining=sessions_before - stats["sessions_deleted"],
                        thread_ids_deleted=list(thread_ids_to_delete)[:5],  # Log first 5 for debugging
                    )
                else:
                    logger.info(
                        "session_cleanup_completed",
                        sessions_deleted=0,
                        checkpoints_deleted=0,
                        sessions_remaining=sessions_before,
                        message="No old sessions found to delete",
                    )
            else:
                logger.warning("session_cleanup_failed", reason="unexpected_table_schema", columns=list(columns))
                stats["errors"].append("Unexpected checkpoints table schema")

            conn.close()

        except sqlite3.Error as e:
            logger.error("session_cleanup_error", error=str(e), db_path=self.db_path)
            stats["errors"].append(f"Database error: {str(e)}")
        except Exception as e:
            logger.error("session_cleanup_unexpected_error", error=str(e), exc_info=True)
            stats["errors"].append(f"Unexpected error: {str(e)}")

        return stats


def cleanup_old_sessions(retention_days: Optional[int] = None) -> Dict[str, Any]:
    """Convenience function to clean up old sessions.

    Args:
        retention_days: Number of days to retain sessions. Defaults to settings.SESSION_RETENTION_DAYS

    Returns:
        dict: Statistics about cleanup operation
    """
    manager = SessionCleanupManager()
    return manager.cleanup_old_sessions(retention_days)
