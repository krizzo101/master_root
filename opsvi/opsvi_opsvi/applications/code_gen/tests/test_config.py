"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path
import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config, load_config


class TestConfig:
    """Test the Config class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()

        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.log_file is None
        assert config.max_concurrent_jobs == 5
        assert config.job_timeout_seconds == 300
        assert config.rate_limit_requests == 10
        assert config.rate_limit_window == 60
        assert config.max_request_size == 10000
        assert config.allowed_file_types is not None
        assert len(config.allowed_file_types) > 0

    def test_config_validation_invalid_port(self):
        """Test configuration validation with invalid port."""
        with pytest.raises(ValueError, match="Invalid port"):
            Config(port=0)

        with pytest.raises(ValueError, match="Invalid port"):
            Config(port=70000)

    def test_config_validation_invalid_concurrent_jobs(self):
        """Test configuration validation with invalid concurrent jobs."""
        with pytest.raises(ValueError, match="max_concurrent_jobs must be >= 1"):
            Config(max_concurrent_jobs=0)

    def test_config_validation_invalid_timeout(self):
        """Test configuration validation with invalid timeout."""
        with pytest.raises(ValueError, match="job_timeout_seconds must be >= 10"):
            Config(job_timeout_seconds=5)

    def test_config_validation_invalid_log_level(self):
        """Test configuration validation with invalid log level."""
        with pytest.raises(ValueError, match="Invalid log_level"):
            Config(log_level="INVALID")

    def test_job_output_dir_creation(self):
        """Test that job output directory is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir) / "test_jobs"
            config = Config(job_output_dir=job_dir)

            assert job_dir.exists()
            assert job_dir.is_dir()


class TestConfigLoading:
    """Test configuration loading from environment."""

    def test_load_config_defaults(self):
        """Test loading config with defaults when no env vars set."""
        # Clear any existing env vars
        env_vars = [
            "HOST",
            "PORT",
            "DEBUG",
            "LOG_LEVEL",
            "LOG_FILE",
            "OPENAI_API_KEY",
            "JOB_OUTPUT_DIR",
            "MAX_CONCURRENT_JOBS",
            "JOB_TIMEOUT_SECONDS",
            "RATE_LIMIT_REQUESTS",
            "RATE_LIMIT_WINDOW",
            "MAX_REQUEST_SIZE",
            "MAX_FILE_SIZE_MB",
            "ALLOWED_FILE_TYPES",
        ]

        original_values = {}
        for var in env_vars:
            original_values[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        try:
            config = load_config()

            assert config.host == "0.0.0.0"
            assert config.port == 8000
            assert config.debug is False
            assert config.log_level == "INFO"
            assert config.log_file is None
            assert config.openai_api_key is None

        finally:
            # Restore original env vars
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value

    def test_load_config_from_env(self):
        """Test loading config from environment variables."""
        env_vars = {
            "HOST": "127.0.0.1",
            "PORT": "9000",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
            "LOG_FILE": "/tmp/test.log",
            "OPENAI_API_KEY": "test-key-12345",
            "MAX_CONCURRENT_JOBS": "10",
            "JOB_TIMEOUT_SECONDS": "600",
            "RATE_LIMIT_REQUESTS": "20",
            "RATE_LIMIT_WINDOW": "120",
            "MAX_REQUEST_SIZE": "20000",
            "MAX_FILE_SIZE_MB": "200",
            "ALLOWED_FILE_TYPES": ".py,.js,.ts,.json",
        }

        # Set environment variables
        original_values = {}
        for var, value in env_vars.items():
            original_values[var] = os.environ.get(var)
            os.environ[var] = value

        try:
            config = load_config()

            assert config.host == "127.0.0.1"
            assert config.port == 9000
            assert config.debug is True
            assert config.log_level == "DEBUG"
            assert config.log_file == Path("/tmp/test.log")
            assert config.openai_api_key == "test-key-12345"
            assert config.max_concurrent_jobs == 10
            assert config.job_timeout_seconds == 600
            assert config.rate_limit_requests == 20
            assert config.rate_limit_window == 120
            assert config.max_request_size == 20000
            assert config.max_file_size_mb == 200
            assert config.allowed_file_types == [".py", ".js", ".ts", ".json"]

        finally:
            # Restore original env vars
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value
                elif var in os.environ:
                    del os.environ[var]

    def test_load_config_job_output_dir(self):
        """Test loading config with custom job output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_job_dir = Path(temp_dir) / "custom_jobs"

            original_value = os.environ.get("JOB_OUTPUT_DIR")
            os.environ["JOB_OUTPUT_DIR"] = str(custom_job_dir)

            try:
                config = load_config()
                assert config.job_output_dir == custom_job_dir
                assert custom_job_dir.exists()  # Should be created

            finally:
                if original_value is not None:
                    os.environ["JOB_OUTPUT_DIR"] = original_value
                elif "JOB_OUTPUT_DIR" in os.environ:
                    del os.environ["JOB_OUTPUT_DIR"]

    def test_debug_string_parsing(self):
        """Test that DEBUG environment variable parsing works correctly."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("yes", False),  # Only "true" should be True
            ("1", False),
            ("", False),
        ]

        original_value = os.environ.get("DEBUG")

        try:
            for env_value, expected in test_cases:
                os.environ["DEBUG"] = env_value
                config = load_config()
                assert config.debug == expected, f"Failed for DEBUG={env_value}"

        finally:
            if original_value is not None:
                os.environ["DEBUG"] = original_value
            elif "DEBUG" in os.environ:
                del os.environ["DEBUG"]


if __name__ == "__main__":
    pytest.main([__file__])
