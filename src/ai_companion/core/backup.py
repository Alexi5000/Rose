"""Database backup utilities for Rose the Healer Shaman."""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

from ai_companion.core.privacy_logging import exc_info_for_log, exception_message_for_log

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages database backups for SQLite and other data files."""

    def __init__(self, backup_dir: str | None = None):
        """Initialize the backup manager.

        Args:
            backup_dir: Directory to store backups
        """
        self.backup_dir = Path(backup_dir or os.getenv("BACKUP_DIR", "/app/data/backups"))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Backup manager initialized")

    def backup_database(self, max_backups: int = 7, db_path: str | None = None) -> Path | None:
        """Create a backup of the SQLite database.

        Args:
            max_backups: Maximum number of backups to keep (default: 7 for daily backups)
            db_path: Path to database file (if None, uses settings.SHORT_TERM_MEMORY_DB_PATH)

        Returns:
            Path to the backup file, or None if backup failed
        """
        try:
            if db_path is None:
                from ai_companion.settings import settings

                db_path = settings.SHORT_TERM_MEMORY_DB_PATH

            db_path = Path(db_path)

            if not db_path.exists():
                logger.warning("Database file not found")
                return None

            # Create backup filename with timestamp (including microseconds for uniqueness)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_filename = f"memory_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename

            # Copy database file
            shutil.copy2(db_path, backup_path)
            logger.info("Database backup created: %s", backup_path.name)

            # Cleanup old backups
            self._cleanup_old_backups(max_backups)

            return backup_path

        except Exception as e:
            logger.error(
                "Failed to create database backup: %s",
                exception_message_for_log(e),
                exc_info=exc_info_for_log(),
            )
            return None

    def _cleanup_old_backups(self, max_backups: int):
        """Remove old backup files, keeping only the most recent ones.

        Args:
            max_backups: Maximum number of backups to keep
        """
        try:
            # Get all backup files sorted by modification time (newest first)
            backup_files = sorted(
                self.backup_dir.glob("memory_backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True
            )

            # Remove old backups beyond the limit
            for old_backup in backup_files[max_backups:]:
                old_backup.unlink()
                logger.info("Removed old backup: %s", old_backup.name)

        except Exception as e:
            logger.error(
                "Failed to cleanup old backups: %s",
                exception_message_for_log(e),
                exc_info=exc_info_for_log(),
            )

    def list_backups(self) -> list[dict]:
        """List all available backups with metadata.

        Returns:
            List of backup information dictionaries
        """
        try:
            backups = []
            for backup_file in sorted(
                self.backup_dir.glob("memory_backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True
            ):
                stat = backup_file.stat()
                backups.append(
                    {
                        "filename": backup_file.name,
                        "path": str(backup_file),
                        "size_bytes": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                )
            return backups

        except Exception as e:
            logger.error(
                "Failed to list backups: %s",
                exception_message_for_log(e),
                exc_info=exc_info_for_log(),
            )
            return []

    def restore_backup(self, backup_filename: str, db_path: str | None = None) -> bool:
        """Restore database from a backup file.

        Args:
            backup_filename: Name of the backup file to restore
            db_path: Path to database file (if None, uses settings.SHORT_TERM_MEMORY_DB_PATH)

        Returns:
            True if restore was successful, False otherwise
        """
        try:
            backup_path = self.backup_dir / backup_filename

            if not backup_path.exists():
                logger.error("Backup file not found")
                return False

            if db_path is None:
                from ai_companion.settings import settings

                db_path = settings.SHORT_TERM_MEMORY_DB_PATH

            db_path = Path(db_path)

            # Create a backup of current database before restoring
            if db_path.exists():
                current_backup = db_path.with_suffix(".db.before_restore")
                shutil.copy2(db_path, current_backup)
                logger.info("Created safety backup: %s", current_backup.name)

            # Restore from backup
            shutil.copy2(backup_path, db_path)
            logger.info("Database restored from backup: %s", backup_filename)

            return True

        except Exception as e:
            logger.error(
                "Failed to restore backup: %s",
                exception_message_for_log(e),
                exc_info=exc_info_for_log(),
            )
            return False


# Global backup manager instance
backup_manager = BackupManager()
