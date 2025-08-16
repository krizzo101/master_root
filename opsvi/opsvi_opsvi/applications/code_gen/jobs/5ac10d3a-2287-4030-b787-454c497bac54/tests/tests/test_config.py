import pytest
from app.config import Config


def test_config_attributes_presence():
    config = Config()
    assert hasattr(config, "DEBUG"), "Config should have DEBUG attribute"
    assert isinstance(config.DEBUG, bool), "DEBUG should be a boolean"
    assert hasattr(
        config, "WEATHER_API_KEY"
    ), "Config should have WEATHER_API_KEY attribute"
    assert config.WEATHER_API_KEY is None or isinstance(
        config.WEATHER_API_KEY, str
    ), "WEATHER_API_KEY should be None or string"
    assert hasattr(
        config, "WEATHER_API_URL"
    ), "Config should have WEATHER_API_URL attribute"
    assert isinstance(config.WEATHER_API_URL, str), "WEATHER_API_URL should be a string"


def test_config_can_be_customized():
    class CustomConfig(Config):
        DEBUG = True
        WEATHER_API_KEY = "dummykey"
        WEATHER_API_URL = "http://testapi.example.com"

    config = CustomConfig()
    assert config.DEBUG is True
    assert config.WEATHER_API_KEY == "dummykey"
    assert config.WEATHER_API_URL == "http://testapi.example.com"
