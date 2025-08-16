import io
import logging

import csv_reporter.logger as logger


def test_configure_logging_sets_level_and_stream():
    stream = io.StringIO()
    logger.configure_logging(level=logging.DEBUG, stream=stream)
    log = logging.getLogger()
    assert log.level == logging.DEBUG
    # Add a log record and check stream capture
    log.debug("test message")
    contents = stream.getvalue()
    assert "test message" in contents


def test_configure_logging_default_level_and_stream():
    logger.configure_logging()
    root_logger = logging.getLogger()
    assert root_logger.level == logging.WARNING
