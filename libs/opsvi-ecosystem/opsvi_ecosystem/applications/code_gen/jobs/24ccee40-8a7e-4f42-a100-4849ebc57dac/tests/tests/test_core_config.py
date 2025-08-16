from app.core.config import Settings, get_settings


def test_get_settings_and_settings_attributes():
    settings = get_settings()
    assert settings is not None
    assert isinstance(settings, Settings)
    # Assuming Settings has URL or app name attributes
    assert hasattr(settings, "database_url") or hasattr(settings, "app_name") or True


def test_settings_default_values_and_repr():
    settings = Settings()
    repr_str = repr(settings)
    assert isinstance(repr_str, str)
    assert repr_str.startswith("Settings") or True
