"""
Generic Logging Utilities

This module provides reusable logging setup and utility functions that can be
used across different projects and applications. It offers consistent logging
patterns, operation tracking, and configurable logging levels.

Key Features:
- Standardized logger setup for different modules
- Operation start/completion logging
- Performance timing utilities
- Configurable log levels and formats
- Context-aware logging with operation IDs
"""

import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

import numpy as np


class ProfileAnalysisLogger:
    """Enhanced logger with operation tracking and performance monitoring."""

    def __init__(self, name: str, level: int = logging.INFO):
        """Initialize logger with standard formatting.

        Args:
            name: Logger name (usually module name)
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            # Create console handler with standard format
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self._operation_stack: list = []
        self._timers: Dict[str, float] = {}

    def log_operation_start(self, operation: str, **context) -> str:
        """Log the start of an operation with context information.

        Args:
            operation: Name of the operation
            **context: Additional context key-value pairs

        Returns:
            Operation ID for tracking
        """
        operation_id = f"{operation}_{int(time.time() * 1000)}"

        self._operation_stack.append(operation_id)
        self._timers[operation_id] = time.time()

        context_str = " ".join(f"{k}={v}" for k, v in context.items())
        message = f"Started {operation}"
        if context_str:
            message += f" [{context_str}]"

        self.logger.info(f"[{operation_id}] {message}")
        return operation_id

    def log_operation_result(
        self,
        operation: str,
        success: bool,
        operation_id: Optional[str] = None,
        **results
    ) -> None:
        """Log the completion of an operation with results.

        Args:
            operation: Name of the operation
            success: Whether the operation succeeded
            operation_id: Operation ID from log_operation_start
            **results: Result key-value pairs to log
        """
        if operation_id is None and self._operation_stack:
            operation_id = self._operation_stack[-1]

        # Calculate duration if timer exists
        duration = None
        if operation_id and operation_id in self._timers:
            start_time = self._timers.pop(operation_id, None)
            if start_time:
                duration = time.time() - start_time

        # Build result message
        status = "completed successfully" if success else "failed"
        message = f"{operation} {status}"

        if duration is not None:
            message += f" in {duration:.3f}s"

        results_str = " ".join(f"{k}={v}" for k, v in results.items())
        if results_str:
            message += f" [{results_str}]"

        log_level = logging.INFO if success else logging.ERROR
        log_message = f"[{operation_id}] {message}" if operation_id else message

        self.logger.log(log_level, log_message)

        # Clean up operation stack
        if operation_id and operation_id in self._operation_stack:
            self._operation_stack.remove(operation_id)

    def log_data_stats(self, data: Any, name: str = "data") -> None:
        """Log statistics about data arrays or structures.

        Args:
            data: Data to analyze (numpy array, pandas DataFrame, etc.)
            name: Name of the data for logging
        """
        try:
            if isinstance(data, np.ndarray):
                self.logger.info(
                    f"{name}: shape={data.shape}, dtype={data.dtype}, "
                    f"range=[{data.min():.3f}, {data.max():.3f}], "
                    f"has_nan={np.any(np.isnan(data))}"
                )
            elif hasattr(data, 'shape'):  # pandas DataFrame/Series
                self.logger.info(
                    f"{name}: shape={data.shape}, columns={list(data.columns) if hasattr(data, 'columns') else 'N/A'}"
                )
            elif isinstance(data, (list, tuple)):
                self.logger.info(f"{name}: length={len(data)}, type={type(data).__name__}")
            else:
                self.logger.info(f"{name}: type={type(data).__name__}")
        except Exception as e:
            self.logger.warning(f"Could not log statistics for {name}: {e}")

    def log_error(self, error: Exception, operation: Optional[str] = None, **context) -> None:
        """Log an exception with full context.

        Args:
            error: Exception that occurred
            operation: Operation name (optional)
            **context: Additional context information
        """
        error_msg = f"{type(error).__name__}: {str(error)}"

        if operation:
            error_msg = f"Error in {operation}: {error_msg}"

        context_str = " ".join(f"{k}={v}" for k, v in context.items())
        if context_str:
            error_msg += f" [{context_str}]"

        self.logger.error(error_msg)

        # Log traceback if debug logging is enabled
        if self.logger.isEnabledFor(logging.DEBUG):
            import traceback
            self.logger.debug(f"Traceback:\n{traceback.format_exc()}")


def setup_module_logger(module_name: str, level: Union[str, int] = "INFO") -> ProfileAnalysisLogger:
    """Create a configured logger for a module.

    Args:
        module_name: Name of the module (e.g., 'csv_io', 'bmap_io')
        level: Logging level (string like 'DEBUG', 'INFO', or int)

    Returns:
        Configured ProfileAnalysisLogger instance
    """
    if isinstance(level, str):
        level_int = getattr(logging, level.upper(), logging.INFO)
    else:
        level_int = level

    return ProfileAnalysisLogger(module_name, level_int)


def setup_file_logging(
    log_file: Union[str, Path],
    level: Union[str, int] = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """Set up file logging with rotation.

    Args:
        log_file: Path to log file
        level: Logging level
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    """
    from logging.handlers import RotatingFileHandler

    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    # Create rotating file handler
    handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)


@contextmanager
def log_operation(logger: ProfileAnalysisLogger, operation: str, **context):
    """Context manager for logging operation start/completion.

    Args:
        logger: Logger instance
        operation: Operation name
        **context: Context information for logging

    Usage:
        with log_operation(logger, "process_data", file_count=5):
            # do work
            pass
    """
    operation_id = logger.log_operation_start(operation, **context)
    start_time = time.time()

    try:
        yield
        duration = time.time() - start_time
        logger.log_operation_result(
            operation, success=True, operation_id=operation_id,
            duration=f"{duration:.3f}s"
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.log_error(e, operation, operation_id=operation_id, duration=f"{duration:.3f}s")
        raise


def create_operation_logger(operation_name: str, log_level: str = "INFO") -> ProfileAnalysisLogger:
    """Create a temporary logger for a specific operation.

    Args:
        operation_name: Name for the operation logger
        log_level: Logging level

    Returns:
        Configured logger for the operation
    """
    return setup_module_logger(f"operation.{operation_name}", log_level)


def log_performance_stats(func_name: str, execution_time: float, **metrics) -> None:
    """Log performance statistics for an operation.

    Args:
        func_name: Name of the function/operation
        execution_time: Time taken in seconds
        **metrics: Additional performance metrics
    """
    logger = logging.getLogger("performance")

    message = f"{func_name} completed in {execution_time:.3f}s"

    if metrics:
        metrics_str = " ".join(f"{k}={v}" for k, v in metrics.items())
        message += f" [{metrics_str}]"

    logger.info(message)


def benchmark_function(logger: Optional[ProfileAnalysisLogger] = None) -> Callable:
    """Decorator to benchmark function execution time.

    Args:
        logger: Logger to use for output (creates default if None)

    Returns:
        Decorated function

    Usage:
        @benchmark_function()
        def my_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = setup_module_logger("benchmark")

            start_time = time.time()
            operation_id = logger.log_operation_start(f"call_{func.__name__}")

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                logger.log_operation_result(
                    f"call_{func.__name__}",
                    success=True,
                    operation_id=operation_id,
                    execution_time=f"{execution_time:.3f}s"
                )

                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.log_error(
                    e, f"call_{func.__name__}",
                    operation_id=operation_id,
                    execution_time=f"{execution_time:.3f}s"
                )
                raise

        return wrapper
    return decorator


def set_global_log_level(level: Union[str, int]) -> None:
    """Set the logging level for all loggers.

    Args:
        level: New logging level
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    logging.getLogger().setLevel(level)

    # Also set for any existing loggers
    for name in logging.root.manager.loggerDict:
        logger = logging.getLogger(name)
        logger.setLevel(level)

