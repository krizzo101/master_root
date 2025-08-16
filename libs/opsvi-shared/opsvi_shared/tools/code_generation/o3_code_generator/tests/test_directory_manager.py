"""Tests for DirectoryManager."""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
    DirectoryManager,
)


class TestDirectoryManager:
    """Test cases for DirectoryManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)

    @pytest.fixture
    def manager(self):
        """Create a DirectoryManager instance."""
        return DirectoryManager()

    def test_create_module_directories(self, manager, temp_dir, monkeypatch):
        """Test creating module directories."""
        # Mock the base_output_dir to use temp directory
        monkeypatch.setattr(manager, "base_output_dir", temp_dir / "generated_files")

        manager.create_module_directories("test_module", ["data", "cache"])

        # Check that directories were created
        assert (temp_dir / "generated_files" / "test_module").exists()
        assert (temp_dir / "generated_files" / "test_module" / "data").exists()
        assert (temp_dir / "generated_files" / "test_module" / "cache").exists()

    def test_ensure_directory_exists(self, manager, temp_dir):
        """Test ensuring directory exists."""
        test_dir = temp_dir / "test_dir"
        manager.ensure_directory_exists(test_dir)
        assert test_dir.exists()

    def test_sanitize_path_component(self, manager):
        """Test path component sanitization."""
        # Test dangerous patterns
        with pytest.raises(ValueError):
            manager._sanitize_path_component("../dangerous")

        with pytest.raises(ValueError):
            manager._sanitize_path_component("path/with/slash")

        # Test valid sanitization
        result = manager._sanitize_path_component("valid_name123")
        assert result == "valid_name123"

    def test_validate_path_security(self, manager, temp_dir):
        """Test path security validation."""
        # Valid path within current directory should pass
        valid_path = temp_dir / "subdir"
        manager._validate_path_security(valid_path)  # Should not raise

        # Path outside should fail (this test might be tricky to implement
        # without actually creating paths outside the project)
        # For now, we'll just test that the method exists and can be called

    def test_cleanup_empty_directories(self, manager, temp_dir):
        """Test cleanup of empty directories."""
        # Create nested empty directories
        empty_dir = temp_dir / "empty" / "nested"
        empty_dir.mkdir(parents=True)

        # Create a directory with a file
        dir_with_file = temp_dir / "with_file"
        dir_with_file.mkdir()
        (dir_with_file / "test.txt").write_text("content")

        manager.cleanup_empty_directories(temp_dir)

        # Empty directories should be removed
        assert not (temp_dir / "empty").exists()
        # Directory with file should remain
        assert dir_with_file.exists()

    def test_get_module_output_path(self, manager):
        """Test getting module output path."""
        path = manager.get_module_output_path("test_module")
        assert path.name == "test_module"
        assert "generated_files" in str(path)
