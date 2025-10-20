"""Database backup utilities for Rose the Healer Shaman."""

import logging
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages database backups for SQLite and other data files."""

    def __init__(self, backup_dir: str = "/app/data/backups"):
        """Initialize the backup manager.

        Args:
            backup_dir: Directory to store backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Backup manager initialized with directory: {self.backup_dir}")

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
                logger.warning(f"Database file not found: {db_path}")
                return None

            # Create backup filename with timestamp (including microseconds for uniqueness)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_filename = f"memory_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename

            # Copy database file
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")

            # Cleanup old backups
            self._cleanup_old_backups(max_backups)

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create database backup: {e}", exc_info=True)
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
                logger.info(f"Removed old backup: {old_backup.name}")

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}", exc_info=True)

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
            logger.error(f"Failed to list backups: {e}", exc_info=True)
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
                logger.error(f"Backup file not found: {backup_filename}")
                return False

            if db_path is None:
                from ai_companion.settings import settings

                db_path = settings.SHORT_TERM_MEMORY_DB_PATH

            db_path = Path(db_path)

            # Create a backup of current database before restoring
            if db_path.exists():
                current_backup = db_path.with_suffix(".db.before_restore")
                shutil.copy2(db_path, current_backup)
                logger.info(f"Created safety backup: {current_backup}")

            # Restore from backup
            shutil.copy2(backup_path, db_path)
            logger.info(f"Database restored from backup: {backup_filename}")

            return True

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}", exc_info=True)
            return False


# Global backup manager instance
backup_manager = BackupManager()
