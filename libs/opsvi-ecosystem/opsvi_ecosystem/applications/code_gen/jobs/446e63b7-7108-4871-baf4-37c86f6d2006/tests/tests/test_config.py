import pytest
from app.config import Config


def test_config_attributes_are_set_correctly():
    config = Config()
    # Example expected keys
    assert hasattr(config, "SECRET_KEY")
    assert config.SECRET_KEY is not None
    assert hasattr(config, "WEATHER_API_KEY")
    assert config.WEATHER_API_KEY is not None
    assert hasattr(config, "CACHE_TYPE")
    assert (
        config.CACHE_TYPE == "simple"
        or config.CACHE_TYPE == "null"
        or config.CACHE_TYPE is not None
    )
