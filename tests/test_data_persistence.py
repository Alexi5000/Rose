"""Tests for data persistence and backup functionality."""

import tempfile
from pathlib import Path

import pytest

from ai_companion.core.backup import BackupManager


class TestBackupManager:
    """Test suite for BackupManager class."""

    @pytest.fixture
    def temp_backup_dir(self):
        """Create a temporary directory for backups."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def temp_db_file(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmpfile:
            tmpfile.write(b"test database content")
            db_path = tmpfile.name
        yield db_path
        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def backup_manager(self, temp_backup_dir):
        """Create a BackupManager instance with temporary directory."""
        return BackupManager(backup_dir=temp_backup_dir)

    def test_backup_manager_initialization(self, temp_backup_dir):
        """Test BackupManager initializes correctly."""
        manager = BackupManager(backup_dir=temp_backup_dir)
        assert manager.backup_dir == Path(temp_backup_dir)
        assert manager.backup_dir.exists()

    def test_backup_database_creates_backup(self, backup_manager, temp_db_file):
        """Test that backup_database creates a backup file."""
        backup_path = backup_manager.backup_database(db_path=temp_db_file)

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.name.startswith("memory_backup_")
        assert backup_path.suffix == ".db"

        # Verify backup content matches original
        with open(backup_path, "rb") as f:
            backup_content = f.read()
        with open(temp_db_file, "rb") as f:
            original_content = f.read()
        assert backup_content == original_content

    def test_backup_database_nonexistent_file(self, backup_manager):
        """Test backup_database handles nonexistent database gracefully."""
        backup_path = backup_manager.backup_database(db_path="/nonexistent/path/db.db")

        assert backup_path is None

    def test_cleanup_old_backups(self, backup_manager, temp_db_file):
        """Test that old backups are cleaned up correctly."""
        # Create 10 backups
        for _ in range(10):
            backup_manager.backup_database(db_path=temp_db_file)

        # Verify only max_backups are kept (default 7)
        backup_files = list(backup_manager.backup_dir.glob("memory_backup_*.db"))
        assert len(backup_files) == 7

    def test_list_backups(self, backup_manager, temp_db_file):
        """Test listing backups returns correct information."""
        # Create a few backups
        backup_manager.backup_database(db_path=temp_db_file)
        backup_manager.backup_database(db_path=temp_db_file)

        backups = backup_manager.list_backups()

        assert len(backups) >= 2
        for backup in backups:
            assert "filename" in backup
            assert "path" in backup
            assert "size_bytes" in backup
            assert "created_at" in backup
            assert backup["filename"].startswith("memory_backup_")

    def test_restore_backup(self, backup_manager, temp_db_file):
        """Test restoring from a backup file."""
        # Create a backup
        backup_path = backup_manager.backup_database(db_path=temp_db_file)
        assert backup_path is not None

        # Modify the original database
        with open(temp_db_file, "wb") as f:
            f.write(b"modified content")

        # Restore from backup
        success = backup_manager.restore_backup(backup_path.name, db_path=temp_db_file)
        assert success is True

        # Verify content is restored
        with open(temp_db_file, "rb") as f:
            restored_content = f.read()
        assert restored_content == b"test database content"

    def test_restore_nonexistent_backup(self, backup_manager, temp_db_file):
        """Test restoring from nonexistent backup fails gracefully."""
        success = backup_manager.restore_backup("nonexistent_backup.db", db_path=temp_db_file)
        assert success is False
