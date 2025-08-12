from multiagent_cli import logs


def test_get_log_file_path_returns_valid_path(tmp_path):
    path = logs.get_log_file_path()
    # Should be a string
    assert isinstance(path, str)


def test_configure_logging_sets_logging_correctly(tmp_path):
    log_file = tmp_path / "app.log"
    log_file_path = str(log_file)
    logger = logs.configure_logging(log_file=log_file_path, verbose=True, quiet=False)
    import logging

    assert logger.level == logging.DEBUG
    # Log something and check file
    logger.debug("test debug message")
    logger.handlers[0].flush()
    log_contents = log_file.read_text()
    assert "test debug message" in log_contents
