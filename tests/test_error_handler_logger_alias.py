import logging

from profcalc.common.error_handler import (
    ErrorHandler,
    LogComponent,
    StructuredLogger,
    get_logger,
)


def test_errorhandler_logger_alias() -> None:
    """ErrorHandler should expose base_logger and provide logger alias."""
    eh = ErrorHandler(log_level=logging.DEBUG, enable_structured=False)
    # attributes exist
    assert hasattr(eh, "base_logger")
    assert hasattr(eh, "logger")

    # alias points to same object
    assert eh.logger is eh.base_logger
    assert isinstance(eh.base_logger, logging.Logger)


def test_get_logger_returns_structuredlogger() -> None:
    """get_logger should return a StructuredLogger with an underlying logging.Logger."""
    logger = get_logger(LogComponent.DATABASE)
    assert isinstance(logger, StructuredLogger)
    assert isinstance(logger.base_logger, logging.Logger)

    # smoke: calling an info method should not raise
    logger.info("pytest: test_get_logger_returns_structuredlogger")
