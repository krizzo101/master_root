import pytest
import os
from simple_news_scraper.config import load_config, setup_logging


import json


def test_load_config_returns_dict_for_valid_file(tmp_path):
    config_data = {"timeout": 10, "loglevel": "INFO"}
    config_file = tmp_path / "config.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f)
    loaded_config = load_config(str(config_file))
    assert isinstance(loaded_config, dict)
    assert loaded_config == config_data


def test_load_config_handles_missing_file_gracefully(tmp_path):
    non_existent_file = tmp_path / "does_not_exist.json"
    config = load_config(str(non_existent_file))
    assert config == {}


import logging


def test_setup_logging_configures_logger_level(caplog):
    setup_logging("DEBUG")
    logger = logging.getLogger()
    assert logger.level == logging.DEBUG
    setup_logging("INFO")
    assert logger.level == logging.INFO
