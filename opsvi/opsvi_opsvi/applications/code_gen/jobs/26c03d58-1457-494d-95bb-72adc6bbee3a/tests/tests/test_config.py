import pytest
from app.config import get_api_settings, ApiSettings, Config


def test_get_api_settings_returns_settings_instance():
    settings = get_api_settings()
    assert isinstance(settings, ApiSettings)
    # Check some expected attribute names
    assert hasattr(settings, "debug")
    assert hasattr(settings, "title")


def test_api_settings_config_class_is_correct():
    config = ApiSettings.Config
    # Check for common pydantic config attributes
    assert hasattr(config, "env_prefix")
    assert isinstance(config.env_prefix, str)


def test_config_class_attributes():
    config = Config
    # Check if class has attributes like env_file
    if hasattr(config, "env_file"):
        assert isinstance(config.env_file, str)
