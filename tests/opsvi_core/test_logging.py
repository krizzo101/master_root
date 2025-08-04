import structlog
import opsvi_core.logging as log_mod


def test_get_logger_returns_logger():
    logger = log_mod.get_logger("unit-test")
    # structlog returns a BoundLoggerLazyProxy initially
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "debug")
    # Test that it can actually log
    logger.info("test message")
