import pytest
from app.config import Config


def test_config_has_essential_attributes():
    """Verify Config class has attributes like API keys, URLs, and settings with correct types."""
    config = Config
    # Check some hypothetical attributes (may vary per actual Config class)
    for attr in ["API_KEY", "BASE_URL", "DEFAULT_LOCATION", "UNITS", "TIMEOUT"]:
        assert hasattr(config, attr), f"Config missing attribute {attr}"

    # Check API_KEY is string
    assert isinstance(config.API_KEY, str) and config.API_KEY
    # Check BASE_URL is string and a URL
    assert isinstance(config.BASE_URL, str) and config.BASE_URL.startswith(
        ("http://", "https://")
    )
    # DEFAULT_LOCATION non-empty string
    assert isinstance(config.DEFAULT_LOCATION, str) and config.DEFAULT_LOCATION
    # UNITS typically 'metric' or 'imperial'
    assert config.UNITS in ["metric", "imperial"]
    # TIMEOUT should be a positive number
    assert isinstance(config.TIMEOUT, (int, float)) and config.TIMEOUT > 0
