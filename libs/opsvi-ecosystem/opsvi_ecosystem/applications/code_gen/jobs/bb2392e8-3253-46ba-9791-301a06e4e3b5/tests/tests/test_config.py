import pytest
from unittest import mock
from multiagent_cli import config

@pytest.fixture
 def sample_config_file(tmp_path):
    config_content = "openai_api_key: 'testkey123'\nlanggraph_settings:\n  param: value"
    file = tmp_path / "config.yaml"
    file.write_text(config_content)
    return str(file)


def test_load_dotenv_config_loads_and_returns_dict(sample_config_file):
    config_dict = config.load_dotenv_config(sample_config_file)
    assert isinstance(config_dict, dict)
    assert "openai_api_key" in config_dict


def test_get_config_returns_AppConfig_instance(sample_config_file):
    with mock.patch("multiagent_cli.config.load_dotenv_config") as mock_load:
        mock_load.return_value = {"openai_api_key": "abc123"}
        cfg = config.get_config()
        from multiagent_cli.config import AppConfig
        assert isinstance(cfg, AppConfig)
        assert hasattr(cfg, "openai_api_key")

