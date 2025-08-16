#!/usr/bin/env python3
"""
Tests for UniversalInputLoader module.
"""

from unittest.mock import MagicMock

import pytest
from utils.input_loader import UniversalInputLoader
import yaml


class TestUniversalInputLoader:
    """Test cases for UniversalInputLoader class."""

    def test_init_with_logger(self, mock_logger):
        """Test initialization with custom logger."""
        assert loader.logger == mock_logger
        assert loader.max_file_size == 10 * 1024 * 1024  # 10MB
        assert loader.supported_formats == {".json", ".yaml", ".yml"}

    def test_init_without_logger(self):
        """Test initialization without custom logger."""
        assert loader.logger is not None
        assert loader.max_file_size == 10 * 1024 * 1024
        assert loader.supported_formats == {".json", ".yaml", ".yml"}

    def test_load_json_file_success(self, input_loader, sample_json_file):
        """Test successful JSON file loading."""

        assert isinstance(result, dict)
        assert result["title"] == "Test Analysis"
        assert result["description"] == "This is a test analysis"
        assert result["parameters"]["param1"] == "value1"

    def test_load_json_file_nonexistent(self, input_loader, temp_dir):
        """Test loading nonexistent JSON file."""

        with pytest.raises(FileNotFoundError):
            input_loader.load_json_file(nonexistent_file)

    def test_load_json_file_invalid_json(self, input_loader, temp_dir):
        """Test loading file with invalid JSON."""
        invalid_json_file.write_text("{ invalid json content")

        with pytest.raises(ValueError, match="Invalid JSON"):
            input_loader.load_json_file(invalid_json_file)

    def test_load_json_file_not_dict(self, input_loader, temp_dir):
        """Test loading JSON file that doesn't contain a dictionary."""
        array_json_file.write_text("[1, 2, 3]")

        with pytest.raises(ValueError, match="must contain a dictionary"):
            input_loader.load_json_file(array_json_file)

    def test_load_yaml_file_success(self, input_loader, sample_yaml_file):
        """Test successful YAML file loading."""

        assert isinstance(result, dict)
        assert result["title"] == "Test Analysis"
        assert result["description"] == "This is a test analysis"
        assert result["parameters"]["param1"] == "value1"

    def test_load_yaml_file_nonexistent(self, input_loader, temp_dir):
        """Test loading nonexistent YAML file."""

        with pytest.raises(FileNotFoundError):
            input_loader.load_yaml_file(nonexistent_file)

    def test_load_yaml_file_invalid_yaml(self, input_loader, temp_dir):
        """Test loading file with invalid YAML."""
        invalid_yaml_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ValueError, match="Invalid YAML"):
            input_loader.load_yaml_file(invalid_yaml_file)

    def test_load_yaml_file_not_dict(self, input_loader, temp_dir):
        """Test loading YAML file that doesn't contain a dictionary."""
        list_yaml_file.write_text("- item1\n- item2")

        with pytest.raises(ValueError, match="must contain a dictionary"):
            input_loader.load_yaml_file(list_yaml_file)

    def test_load_file_by_extension_json(self, input_loader, sample_json_file):
        """Test auto-detection and loading of JSON file."""

        assert isinstance(result, dict)
        assert result["title"] == "Test Analysis"

    def test_load_file_by_extension_yaml(self, input_loader, sample_yaml_file):
        """Test auto-detection and loading of YAML file."""

        assert isinstance(result, dict)
        assert result["title"] == "Test Analysis"

    def test_load_file_by_extension_yml(self, input_loader, temp_dir, sample_data):
        """Test auto-detection and loading of .yml file."""
        with open(yml_file, "w") as f:
            yaml.dump(sample_data, f)


        assert isinstance(result, dict)
        assert result["title"] == "Test Analysis"

    def test_load_file_by_extension_unsupported(self, input_loader, temp_dir):
        """Test loading file with unsupported extension."""
        unsupported_file.write_text("plain text content")

        with pytest.raises(ValueError, match="Unsupported file format"):
            input_loader.load_file_by_extension(unsupported_file)

    def test_validate_required_fields_success(self, input_loader, sample_data):
        """Test successful field validation."""

        # Should not raise an exception
        input_loader.validate_required_fields(sample_data, required_fields)

    def test_validate_required_fields_missing(self, input_loader, sample_data):
        """Test field validation with missing fields."""

        with pytest.raises(ValueError, match="Missing required fields"):
            input_loader.validate_required_fields(sample_data, required_fields)

    def test_validate_required_fields_none_value(self, input_loader):
        """Test field validation with None values."""

        with pytest.raises(ValueError, match="Missing required fields"):
            input_loader.validate_required_fields(data, required_fields)

    def test_validate_required_fields_not_dict(self, input_loader):
        """Test field validation with non-dictionary data."""

        with pytest.raises(ValueError, match="Data must be a dictionary"):
            input_loader.validate_required_fields(data, required_fields)

    def test_validate_required_fields_not_list(self, input_loader, sample_data):
        """Test field validation with non-list required fields."""

        with pytest.raises(ValueError, match="Required fields must be a list"):
            input_loader.validate_required_fields(sample_data, required_fields)

    def test_clean_template_data_success(self, input_loader):
        """Test successful template data cleaning."""
            "normal_field": "value1",
            "_template_metadata": "should be removed",
            "nested": {
                "normal_nested": "value2",
                "_nested_metadata": "should be removed",
            },
        }


        assert result == expected

    def test_clean_template_data_not_dict(self, input_loader):
        """Test template data cleaning with non-dictionary data."""

        assert result == data

    def test_clean_template_data_empty_dict(self, input_loader):
        """Test template data cleaning with empty dictionary."""

        assert result == {}

    def test_clean_template_data_only_metadata(self, input_loader):
        """Test template data cleaning with only metadata fields."""

        assert result == {}

    def test_validate_file_path_success(self, input_loader, temp_dir):
        """Test successful file path validation."""
        test_file.write_text("test content")

        # Should not raise an exception
        input_loader._validate_file_path(test_file)

    def test_validate_file_path_empty(self, input_loader):
        """Test file path validation with empty path."""
        with pytest.raises(ValueError, match="File path cannot be empty"):
            input_loader._validate_file_path("")

    def test_validate_file_path_none(self, input_loader):
        """Test file path validation with None path."""
        with pytest.raises(ValueError, match="File path cannot be empty"):
            input_loader._validate_file_path(None)

    def test_validate_file_path_traversal(self, input_loader, temp_dir):
        """Test file path validation with path traversal."""

        with pytest.raises(ValueError, match="resolves outside"):
            input_loader._validate_file_path(dangerous_path)

    def test_validate_file_size_success(self, input_loader, temp_dir):
        """Test successful file size validation."""
        test_file.write_text("small content")

        # Should not raise an exception
        input_loader._validate_file_size(test_file)

    def test_validate_file_size_too_large(self, input_loader, temp_dir, monkeypatch):
        """Test file size validation with too large file."""
        test_file.write_text("content")

        # Mock stat to return large file size
        def mock_stat():
            mock_stat_result.st_size = 20 * 1024 * 1024  # 20MB
            return mock_stat_result

        monkeypatch.setattr(test_file, "stat", mock_stat)

        with pytest.raises(ValueError, match="too large"):
            input_loader._validate_file_size(test_file)

    def test_validate_file_size_stat_error(self, input_loader, temp_dir, monkeypatch):
        """Test file size validation with stat error."""
        test_file.write_text("content")

        # Mock stat to raise OSError
        def mock_stat():
            raise OSError("Stat failed")

        monkeypatch.setattr(test_file, "stat", mock_stat)

        with pytest.raises(OSError, match="Could not determine file size"):
            input_loader._validate_file_size(test_file)

    def test_logging_integration(self, input_loader, mock_logger, sample_json_file):
        """Test that logging is properly integrated."""
        input_loader.load_json_file(sample_json_file)

        # Verify logging calls were made
        mock_logger.log_info.assert_called()

    def test_error_handling_file_not_found(self, input_loader, temp_dir):
        """Test error handling for file not found."""

        with pytest.raises(FileNotFoundError):
            input_loader.load_json_file(nonexistent_file)

    def test_error_handling_permission_denied(
        self, input_loader, temp_dir, monkeypatch
    ):
        """Test error handling for permission denied."""
        test_file.write_text('{"test": "data"}')

        # Mock open to raise PermissionError
        def mock_open_func(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr("builtins.open", mock_open_func)

        with pytest.raises(OSError, match="Error reading file"):
            input_loader.load_json_file(test_file)

    def test_error_handling_encoding_error(self, input_loader, temp_dir, monkeypatch):
        """Test error handling for encoding error."""
        test_file.write_text('{"test": "data"}')

        # Mock open to raise UnicodeDecodeError
        def mock_open_func(*args, **kwargs):
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "Invalid encoding")

        monkeypatch.setattr("builtins.open", mock_open_func)

        with pytest.raises(OSError, match="Error reading file"):
            input_loader.load_json_file(test_file)
