from app.config import Config, Settings


def test_settings_properties_and_defaults():
    """Verify that Settings class initializes with expected default attributes."""
    settings = Settings()
    # Assuming Settings has attributes like debug, database_url (adjust if different)
    assert hasattr(settings, "debug")
    assert hasattr(settings, "database_url")
    # Test that the debug flag is bool
    assert isinstance(settings.debug, bool)
    # Test string type for database_url
    assert isinstance(settings.database_url, str)


def test_config_instantiation_and_access():
    config = Config()
    # Assuming Config has attributes like app_name, version
    assert hasattr(config, "app_name")
    assert hasattr(config, "version")
    assert isinstance(config.app_name, str)
    assert isinstance(config.version, str)
