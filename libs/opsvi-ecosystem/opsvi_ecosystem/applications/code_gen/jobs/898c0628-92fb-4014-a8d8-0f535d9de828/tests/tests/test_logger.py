import logging

import pytest
from json_data_processor import logger


def test_setup_logger_creates_logger_with_expected_level_and_handlers():
    log = logger.setup_logger("test_logger", level=logging.DEBUG)
    assert log.name == "test_logger"
    # Should have at least one handler
    assert len(log.handlers) > 0
    # Check log level
    assert log.level == logging.DEBUG
    # Test that log messages at different levels are handled
    with pytest.raises(TypeError):  # Passing wrong type to log message will raise
        log.debug(None)
