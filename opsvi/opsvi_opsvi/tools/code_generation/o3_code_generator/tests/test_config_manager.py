"""Tests for ConfigManager."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
    ConfigManager,
)


class TestConfigManager:
    """Test cases for ConfigManager."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "openai": {
                    "api_key": "test-key-from-yaml",
                    "base_url": "https://api.openai.com/v1",
                },
                "logging": {"level": "DEBUG", "enable_debug_log": True},
                "model": {"default": "gpt-4o", "timeout": 60},
            }
            yaml.dump(config_data, f)
            yield Path(f.name)
        os.unlink(f.name)

    def test_env_var_override(self, temp_config_file, monkeypatch):
        """Test that environment variables override YAML config."""
        # Set environment variable
        monkeypatch.setenv("OPENAI_API_KEY", "env-override-key")

        config = ConfigManager(str(temp_config_file))

        # Environment variable should take precedence
        assert config.get("openai.api_key") == "env-override-key"
        # YAML value should be used when no env var
        assert config.get("openai.base_url") == "https://api.openai.com/v1"

    def test_yaml_fallback(self, temp_config_file):
        """Test that YAML config is used when no env var."""
        config = ConfigManager(str(temp_config_file))

        assert config.get("openai.api_key") == "test-key-from-yaml"
        assert config.get("logging.level") == "DEBUG"

    def test_default_fallback(self, temp_config_file):
        """Test that defaults are used when key not found."""
        config = ConfigManager(str(temp_config_file))

        assert config.get("nonexistent.key", "default-value") == "default-value"

    def test_dot_notation_env_conversion(self, monkeypatch):
        """Test that dot notation converts to env var format."""
        monkeypatch.setenv("LOGGING_LEVEL", "ERROR")

        config = ConfigManager()

        assert config.get("logging.level") == "ERROR"

    def test_get_api_key_success(self, monkeypatch):
        """Test successful API key retrieval."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")

        config = ConfigManager()

        assert config.get_api_key() == "test-api-key"

    def test_get_api_key_missing(self):
        """Test API key retrieval when missing."""
        config = ConfigManager()

        with pytest.raises(ValueError, match="OpenAI API key not found"):
            config.get_api_key()

    def test_get_logging_config(self, temp_config_file):
        """Test logging config with defaults."""
        config = ConfigManager(str(temp_config_file))

        logging_config = config.get_logging_config()

        assert logging_config["level"] == "DEBUG"
        assert logging_config["enable_debug_log"] is True
        assert "format" in logging_config

    def test_get_model_config(self, temp_config_file):
        """Test model config with defaults."""
        config = ConfigManager(str(temp_config_file))

        model_config = config.get_model_config()

        assert model_config["default_model"] == "gpt-4o"
        assert model_config["timeout"] == 60
        assert "max_retries" in model_config

    def test_nonexistent_config_file(self):
        """Test handling of nonexistent config file."""
        config = ConfigManager("/nonexistent/path/config.yaml")

        # Should not raise, should use defaults
        assert config.get("some.key", "default") == "default"

    def test_invalid_yaml_file(self):
        """Test handling of invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            invalid_file = f.name

        try:
            config = ConfigManager(invalid_file)
            # Should not raise, should use defaults
            assert config.get("some.key", "default") == "default"
        finally:
            os.unlink(invalid_file)
