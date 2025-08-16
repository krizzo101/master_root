from backend.config import Settings


def test_settings_load_default_configuration():
    settings = Settings()
    assert hasattr(settings, "cpu_threshold")
    assert hasattr(settings, "memory_threshold")
