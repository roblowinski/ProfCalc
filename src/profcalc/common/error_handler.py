# =============================================================================  # noqa: D100
# Unified Error Handling and Logging Utilities
# =============================================================================
# This module combines structured logging and custom exception handling to provide
# a comprehensive error management system for the application.
#
# PURPOSE:
# This module provides a comprehensive logging and error handling system that ensures
# consistent error reporting, user-friendly messages, and detailed debugging information
# across all components of the Beach Profile Database application.
#
# KEY FEATURES:
# - Structured logging with component-based categorization
# - Hierarchical error handling with severity levels
# - User-friendly error messages with technical details
# - JSON-formatted log output for analysis
# - Configurable log levels and output destinations
# - Error recovery and graceful degradation
# - Performance monitoring and timing utilities
#
# LOGGING SYSTEM:
# - Component-based logging (database, data processing, spatial, etc.)
# - Structured log messages with context and metadata
# - Multiple output formats (console, file, JSON)
# - Log level filtering and verbosity control
# - Performance timing and operation tracking
#
# ERROR HANDLING:
# - Categorized error types (validation, database, file I/O, etc.)
# - Severity levels from debug to critical
# - Consistent error messages with actionable information
# - Error context preservation for debugging
# - Recovery mechanisms for common failure modes
#
# DESIGN PRINCIPLES:
# The error handling system is designed to provide appropriate feedback to both
# end users (through clean, actionable messages) and developers (through detailed
# technical information and stack traces).
#
# IMPORTANCE:
# This module is fundamental to the application's reliability, maintainability,
# and user experience, ensuring that errors are handled gracefully and logged
# comprehensively for troubleshooting and improvement.
#
# =============================================================================

import json
import logging
import sys
import time
from datetime import UTC, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Union

# Structured Logging Utilities


class LogLevel(Enum):
    """Standard logging levels for consistent log categorization.

    This enumeration defines the standard logging levels used throughout the
    Beach Profile Database application. It maps to Python's built-in logging
    module levels to ensure compatibility and consistent behavior.

    The levels follow the standard hierarchy:
    - DEBUG: Detailed diagnostic information for development
    - INFO: General information about application operation
    - WARNING: Indications of potential problems or important events
    - ERROR: Error conditions that don't prevent operation
    - CRITICAL: Serious errors that may prevent continued operation

    Attributes:
        DEBUG (int): Debug level (10) - detailed diagnostic information
        INFO (int): Info level (20) - general operational information
        WARNING (int): Warning level (30) - potential problem indicators
        ERROR (int): Error level (40) - error conditions
        CRITICAL (int): Critical level (50) - serious error conditions

    Example:
        >>> from beach_profile_db.utils.error_handler import LogLevel
        >>> level = LogLevel.INFO
        >>> level.value
        20

    Note:
        These levels correspond directly to Python's logging module constants
        and are used for consistent log filtering and output across the application.
    """

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogComponent(Enum):
    """Application components for categorized logging."""

    DATABASE = "database"
    DATA_PROCESSING = "data_processing"
    SPATIAL = "spatial"
    FILE_IO = "file_io"
    VALIDATION = "validation"
    CLI = "cli"
    WEB_GUI = "web_gui"
    API = "api"
    SYSTEM = "system"


class ErrorSeverity(Enum):
    """Error severity levels for consistent categorization."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """Error categories for better error classification."""

    DATABASE = "DATABASE"
    FILE_IO = "FILE_IO"
    VALIDATION = "VALIDATION"
    NETWORK = "NETWORK"
    CONFIGURATION = "CONFIGURATION"
    PROCESSING = "PROCESSING"
    SPATIAL = "SPATIAL"
    SYSTEM = "SYSTEM"
    USER_INPUT = "USER_INPUT"


class StructuredLogger:
    """Structured logging utility for consistent, searchable log entries.

    Provides JSON-formatted logging with context information for better
    monitoring, debugging, and analytics. Compatible with standard logging.Logger interface.
    """

    def __init__(
        self, component: LogComponent, base_logger: logging.Logger
    ) -> None:
        """Initialize the structured logger for a specific component.

        This method creates a new StructuredLogger instance that wraps a standard
        Python logger to provide JSON-formatted structured logging with component
        metadata. The structured logger maintains compatibility with the standard
        logging interface while adding contextual information.

        Parameters:
            component (LogComponent): The application component this logger represents.
                This is used to categorize log entries and provide context for filtering
                and analysis.
            base_logger (logging.Logger): The underlying Python logger instance that
                handles the actual logging output and level filtering.

        Attributes Set:
            component (LogComponent): The component identifier for log categorization.
            base_logger (logging.Logger): The wrapped logger for output and filtering.

        Example:
            >>> import logging
            >>> base = logging.getLogger("my_component")
            >>> logger = StructuredLogger(LogComponent.DATABASE, base)
            >>> logger.info("Database connected successfully")
        """
        self.component = component
        self.base_logger = base_logger

    def _format_structured_message(
        self, level: str, message: str, extra: dict[str, Any] | None = None
    ) -> str:
        """Format a log message as structured JSON.

        This private method creates a JSON-formatted log entry that includes
        timestamp, log level, component information, the message, and any
        additional context data. The structured format enables better log
        analysis, searching, and integration with log aggregation systems.

        Parameters:
            level (str): The log level string (e.g., "INFO", "ERROR").
            message (str): The log message content.
            extra (dict[str, Any] | None, optional): Additional context data to
                include in the structured log entry. Defaults to None.

        Returns:
            str: A JSON-formatted string containing the structured log data.

        Example:
            >>> logger = StructuredLogger(LogComponent.DATABASE, base_logger)
            >>> json_msg = logger._format_structured_message("INFO", "Connected", {"db": "main"})
            >>> print(json_msg)
            {"timestamp": "2023-10-15T10:30:00Z", "level": "INFO", ...}
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "level": level,
            "component": self.component.value,
            "message": message,
            "extra": extra or {},
        }
        return json.dumps(log_entry, default=str)

    def debug(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log a debug message with structured format.

        This method logs a message at the DEBUG level using structured JSON formatting.
        Debug messages provide detailed diagnostic information typically used during
        development and troubleshooting. The message is only logged if the logger's
        level is set to DEBUG or lower.

        Parameters:
            message (str): The debug message to log. Should contain detailed information
                useful for debugging and development.
            extra (dict[str, Any] | None, optional): Additional context data to include
                in the structured log entry, such as variable values or execution state.
                Defaults to None.

        Returns:
            None

        Example:
            >>> logger = StructuredLogger(LogComponent.DATABASE, base_logger)
            >>> logger.debug("Query execution time", {"query": "SELECT * FROM profiles", "time_ms": 150})
        """
        if self.base_logger.isEnabledFor(logging.DEBUG):
            structured_msg = self._format_structured_message(
                "DEBUG", message, extra
            )
            self.base_logger.debug(structured_msg)

    def info(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log an info message with structured format.

        This method logs a message at the INFO level using structured JSON formatting.
        Info messages provide general information about application operation and
        significant events. The message is only logged if the logger's level is set
        to INFO or lower.

        Parameters:
            message (str): The informational message to log. Should describe normal
                application operations or significant events.
            extra (dict[str, Any] | None, optional): Additional context data to include
                in the structured log entry. Defaults to None.

        Returns:
            None

        Example:
            >>> logger = StructuredLogger(LogComponent.API, base_logger)
            >>> logger.info("API request processed", {"endpoint": "/profiles", "method": "GET", "status": 200})
        """
        if self.base_logger.isEnabledFor(logging.INFO):
            structured_msg = self._format_structured_message(
                "INFO", message, extra
            )
            self.base_logger.info(structured_msg)

    def warning(
        self, message: str, extra: dict[str, Any] | None = None
    ) -> None:
        """Log a warning message with structured format.

        This method logs a message at the WARNING level using structured JSON formatting.
        Warning messages indicate potential problems or unusual conditions that do not
        prevent operation but may require attention. The message is only logged if the
        logger's level is set to WARNING or lower.

        Parameters:
            message (str): The warning message to log. Should describe potential issues
                or unusual conditions.
            extra (dict[str, Any] | None, optional): Additional context data to include
                in the structured log entry. Defaults to None.

        Returns:
            None

        Example:
            >>> logger = StructuredLogger(LogComponent.VALIDATION, base_logger)
            >>> logger.warning("Invalid coordinate format detected", {"field": "latitude", "value": "91.5"})
        """
        if self.base_logger.isEnabledFor(logging.WARNING):
            structured_msg = self._format_structured_message(
                "WARNING", message, extra
            )
            self.base_logger.warning(structured_msg)

    def error(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log an error message with structured format.

        This method logs a message at the ERROR level using structured JSON formatting.
        Error messages indicate failures or exceptions that may impact application
        functionality. The message is only logged if the logger's level is set to
        ERROR or lower.

        Parameters:
            message (str): The error message to log. Should describe the failure or
                exception that occurred.
            extra (dict[str, Any] | None, optional): Additional context data to include
                in the structured log entry, such as error details or stack traces.
                Defaults to None.

        Returns:
            None

        Example:
            >>> logger = StructuredLogger(LogComponent.DATABASE, base_logger)
            >>> logger.error("Database connection failed", {"error_code": "ECONNREFUSED", "host": "localhost"})
        """
        if self.base_logger.isEnabledFor(logging.ERROR):
            structured_msg = self._format_structured_message(
                "ERROR", message, extra
            )
            self.base_logger.error(structured_msg)

    def critical(
        self, message: str, extra: dict[str, Any] | None = None
    ) -> None:
        """Log a critical message with structured format.

        This method logs a message at the CRITICAL level using structured JSON formatting.
        Critical messages indicate serious failures that may prevent continued operation.
        The message is only logged if the logger's level is set to CRITICAL or lower.

        Parameters:
            message (str): The critical message to log. Should describe serious failures
                or conditions that prevent operation.
            extra (dict[str, Any] | None, optional): Additional context data to include
                in the structured log entry, such as error details or system state.
                Defaults to None.

        Returns:
            None

        Example:
            >>> logger = StructuredLogger(LogComponent.SYSTEM, base_logger)
            >>> logger.critical("Database connection lost", {"error_code": "ECONNLOST", "attempts": 5})
        """
        if self.base_logger.isEnabledFor(logging.CRITICAL):
            structured_msg = self._format_structured_message(
                "CRITICAL", message, extra
            )
            self.base_logger.critical(structured_msg)

    def log(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        """Standard logging log method for compatibility.

        This method provides compatibility with the standard Python logging.Logger
        interface, allowing StructuredLogger to be used as a drop-in replacement.
        It delegates to the underlying base logger.

        Parameters:
            level (int): The logging level (e.g., logging.INFO).
            message (str): The log message.
            *args: Variable positional arguments passed to the base logger.
            **kwargs: Variable keyword arguments passed to the base logger.

        Returns:
            None

        Note:
            This method does not use structured formatting. For structured logging,
            use the level-specific methods (debug, info, warning, error, critical).
        """
        self.base_logger.log(level, message, *args, **kwargs)

    def isEnabledFor(self, level: int) -> bool:
        """Check if logging is enabled for the given level.

        This method checks whether the underlying logger is configured to log
        messages at the specified level, allowing callers to avoid expensive
        message formatting when logging is disabled.

        Parameters:
            level (int): The logging level to check (e.g., logging.DEBUG).

        Returns:
            bool: True if logging is enabled for the level, False otherwise.

        Example:
            >>> if logger.isEnabledFor(logging.DEBUG):
            ...     logger.debug("Expensive debug info", {"data": expensive_computation()})
        """
        return self.base_logger.isEnabledFor(level)

    def setLevel(self, level: int) -> None:
        """Set the logging level for this logger.

        This method sets the minimum logging level for the underlying logger.
        Messages below this level will be filtered out and not logged.

        Parameters:
            level (int): The logging level to set (e.g., logging.INFO).

        Returns:
            None

        Example:
            >>> logger.setLevel(logging.DEBUG)  # Enable all log levels
            >>> logger.setLevel(logging.ERROR)  # Only log errors and critical messages
        """
        # Set the level on the underlying base logger wrapped by StructuredLogger
        self.base_logger.setLevel(level)

    def addHandler(self, handler: logging.Handler) -> None:
        """Add a handler to the logger.

        This method adds a logging handler to the underlying logger, allowing
        customization of log output destinations and formats.

        Parameters:
            handler (logging.Handler): The handler to add (e.g., StreamHandler, FileHandler).

        Returns:
            None

        Example:
            >>> import logging
            >>> handler = logging.FileHandler("app.log")
            >>> logger.addHandler(handler)
        """
        self.base_logger.addHandler(handler)

    def removeHandler(self, handler: logging.Handler) -> None:
        """Remove a handler from the logger.

        This method removes a previously added logging handler from the underlying logger.

        Parameters:
            handler (logging.Handler): The handler to remove.

        Returns:
            None

        Example:
            >>> logger.removeHandler(file_handler)
        """
        self.base_logger.removeHandler(handler)

    def hasHandlers(self) -> bool:
        """Check if the logger has any handlers configured.

        This method checks whether the underlying logger has any handlers attached,
        which determines whether log messages will be output anywhere.

        Parameters:
            None

        Returns:
            bool: True if the logger has handlers, False otherwise.

        Example:
            >>> if not logger.hasHandlers():
            ...     logger.addHandler(logging.StreamHandler())
        """
        return self.base_logger.hasHandlers()

    @property
    def level(self) -> int:
        """Get the current logging level.

        This property returns the current logging level of the underlying logger.

        Parameters:
            None

        Returns:
            int: The current logging level (e.g., logging.INFO).

        Example:
            >>> current_level = logger.level
            >>> print(f"Current level: {logging.getLevelName(current_level)}")
        """
        return self.base_logger.level

    @property
    def handlers(self) -> list:
        """Get the list of handlers attached to the logger.

        This property returns a list of all logging handlers currently attached
        to the underlying logger.

        Parameters:
            None

        Returns:
            list: List of logging.Handler objects attached to the logger.

        Example:
            >>> handlers = logger.handlers
            >>> print(f"Number of handlers: {len(handlers)}")
        """
        return self.base_logger.handlers

    def performance(
        self,
        operation: str,
        duration: float,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Log performance metrics with structured format.

        This method logs performance information including operation duration
        and additional metrics. Performance logs help monitor application
        performance and identify bottlenecks.

        Parameters:
            operation (str): The name or description of the operation being measured.
            duration (float): The duration of the operation in seconds.
            extra (dict[str, Any] | None, optional): Additional performance metrics
                or context data to include in the log entry. Defaults to None.

        Returns:
            None

        Example:
            >>> logger.performance("database_query", 0.125, {"rows_returned": 150, "query_type": "SELECT"})
        """
        perf_data = {
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            **(extra or {}),
        }
        # Use the StructuredLogger's info method for performance messages
        self.info(
            f"Performance: {operation}", extra={"performance": perf_data}
        )

    def audit(
        self,
        action: str,
        user: str | None = None,
        resource: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Log an audit event for security and compliance tracking.

        Records an audit event with user, action, and resource information for
        security monitoring and compliance purposes.

        Args:
            action: The action being performed (e.g., "login", "data_export").
            user: Optional identifier of the user performing the action.
            resource: Optional identifier of the resource being accessed.
            component: Application component where the action occurred.
            extra: Optional additional context data for the audit log.
        """
        audit_data = {
            "action": action,
            "user": user,
            "resource": resource,
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            **(extra or {}),
        }
        # Use the StructuredLogger's info method for audit messages
        self.info(f"Audit: {action}", extra={"audit": audit_data})


class PerformanceTimer:
    """Context manager for timing operations and logging performance metrics."""

    def __init__(
        self,
        logger: StructuredLogger,
        operation: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the performance timer.

        This method creates a new PerformanceTimer instance that can be used
        as a context manager to measure and log the duration of operations.

        Parameters:
            logger (StructuredLogger): The structured logger to use for logging
                performance metrics when the timer exits.
            operation (str): A descriptive name for the operation being timed.
            extra (dict[str, Any] | None, optional): Additional context data to
                include in the performance log entry. Defaults to None.

        Attributes Set:
            logger (StructuredLogger): The logger for performance output.
            operation (str): The operation name for logging.
            extra (dict[str, Any] | None): Additional context data.
            start_time (float | None): The start time, set when entering context.

        Example:
            >>> timer = PerformanceTimer(logger, "data_processing", {"input_size": 1000})
        """
        self.logger = logger
        self.operation = operation
        self.extra = extra or {}
        self.start_time: float | None = None

    def __enter__(self) -> "PerformanceTimer":
        """Enter the context manager and start timing.

        This method is called when entering the 'with' statement context.
        It records the current time as the start of the operation.

        Parameters:
            None

        Returns:
            PerformanceTimer: The timer instance for use in the context.

        Example:
            >>> with PerformanceTimer(logger, "operation") as timer:
            ...     # Operation code here
            ...     pass
        """
        self.start_time = time.time()
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: Path | None,
    ) -> None:
        """Exit the context manager and log performance metrics.

        This method is called when exiting the 'with' statement context.
        It calculates the duration since __enter__ was called and logs
        the performance metrics using the configured logger.

        Parameters:
            exc_type (type | None): The exception type if an exception occurred.
            exc_val (BaseException | None): The exception value if an exception occurred.
            exc_tb (Path | None): The traceback if an exception occurred.

        Returns:
            None

        Note:
            The performance metrics are logged regardless of whether an exception
            occurred, allowing measurement of failed operations as well.
        """
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.logger.performance(self.operation, duration, self.extra)


class BeachProfileLogger:
    """Centralized logging system for the beach profile database application.

    Provides component-specific loggers, structured logging, and consistent
    formatting across the entire application.
    """

    def __init__(
        self,
        log_level: int = logging.INFO,
        log_file: str | None = None,
        enable_structured: bool = True,
        enable_console: bool = True,
        enable_file: bool = True,
    ) -> None:
        """Initialize the centralized logger with comprehensive configuration.

        This method creates a BeachProfileLogger instance that manages logging
        across the entire beach profile database application. It sets up console
        and file handlers with appropriate formatting based on the structured
        logging preference.

        Parameters:
            log_level (int, optional): The base logging level for all handlers.
                Defaults to logging.INFO.
            log_file (str | None, optional): Path to the log file for file output.
                If None, file logging is disabled. Defaults to None.
            enable_structured (bool, optional): Whether to use JSON structured
                formatting for logs. Defaults to True.
            enable_console (bool, optional): Whether to enable console output.
                Defaults to True.
            enable_file (bool, optional): Whether to enable file output (requires
                log_file). Defaults to True.

        Attributes Set:
            log_level (int): The configured logging level.
            log_file (str | None): The log file path.
            enable_structured (bool): Whether structured logging is enabled.
            enable_console (bool): Whether console logging is enabled.
            enable_file (bool): Whether file logging is enabled.
            base_logger (logging.Logger): The root logger instance.
            _component_loggers (dict): Cache of component-specific loggers.

        Raises:
            OSError: If the log file directory cannot be created.

        Example:
            >>> logger = BeachProfileLogger(
            ...     log_level=logging.DEBUG,
            ...     log_file="beach_profile.log",
            ...     enable_structured=True
            ... )
        """
        self.log_level = log_level
        self.log_file = log_file
        self.enable_structured = enable_structured
        self.enable_console = enable_console
        self.enable_file = enable_file

        # Create base logger
        self.base_logger = logging.getLogger("beach_profile_db")
        self.base_logger.setLevel(log_level)

        # Remove existing handlers
        for handler in self.base_logger.handlers[:]:
            self.base_logger.removeHandler(handler)

        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            if enable_structured:
                # For console, use readable format
                console_formatter = logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                )
            else:
                console_formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(log_level)
            self.base_logger.addHandler(console_handler)

        # File handler
        if enable_file and log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            if enable_structured:
                # For file, use JSON format
                file_formatter = logging.Formatter(
                    "%(message)s"
                )  # StructuredLogger handles formatting
            else:
                file_formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
                )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(log_level)
            self.base_logger.addHandler(file_handler)

        # Component loggers cache
        self._component_loggers: dict[LogComponent, StructuredLogger] = {}

    def get_component_logger(
        self, component: LogComponent
    ) -> StructuredLogger:
        """Get a component-specific structured logger instance.

        This method returns a StructuredLogger for the specified component,
        creating it if it doesn't already exist. The logger is cached for
        performance and reused on subsequent calls.

        Parameters:
            component (LogComponent): The application component that needs logging.

        Returns:
            StructuredLogger: A structured logger instance configured for the component.

        Example:
            >>> db_logger = logger.get_component_logger(LogComponent.DATABASE)
            >>> db_logger.info("Database connection established")
        """
        if component not in self._component_loggers:
            # Create child logger for component
            component_logger = self.base_logger.getChild(component.value)
            self._component_loggers[component] = StructuredLogger(
                component, component_logger
            )

        return self._component_loggers[component]

    def configure_from_dict(self, config: dict[str, Any]) -> None:
        """Configure logging settings from a dictionary.

        This method allows runtime reconfiguration of logging settings through
        a configuration dictionary. It can update log levels, file paths, and
        output options dynamically.

        Parameters:
            config (dict[str, Any]): Configuration dictionary with logging settings.
                Supported keys: 'level', 'file', 'structured', 'console', 'file_output'.

        Returns:
            None

        Raises:
            ValueError: If an invalid log level name is provided.

        Example:
            >>> config = {
            ...     "level": "DEBUG",
            ...     "file": "new_log.log",
            ...     "structured": False
            ... }
            >>> logger.configure_from_dict(config)
        """
        # Update log level
        if "level" in config:
            level_name = config["level"].upper()
            if hasattr(logging, level_name):
                self.log_level = getattr(logging, level_name)
                self.base_logger.setLevel(self.log_level)
                for handler in self.base_logger.handlers:
                    handler.setLevel(self.log_level)

        # Update log file
        if "file" in config:
            self.log_file = config["file"]
            # Reconfigure file handler if needed
            self._reconfigure_file_handler()

        # Update structured logging
        if "structured" in config:
            self.enable_structured = config["structured"]

        # Update output options
        if "console" in config:
            self.enable_console = config["console"]
        if "file_output" in config:
            self.enable_file = config["file_output"]

    def _reconfigure_file_handler(self) -> None:
        """Reconfigure the file handler with current settings.

        This private method updates or creates the file handler based on the
        current log_file, enable_file, and enable_structured settings. It removes
        existing file handlers and creates a new one with the appropriate configuration.

        Parameters:
            None

        Returns:
            None

        Raises:
            OSError: If the log file directory cannot be created.
        """
        if not self.log_file:
            return

        # Remove existing file handlers
        handlers_to_remove = []
        for handler in self.base_logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handlers_to_remove.append(handler)

        for handler in handlers_to_remove:
            self.base_logger.removeHandler(handler)

        # Add new file handler
        if self.enable_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(self.log_file)
            if self.enable_structured:
                file_formatter = logging.Formatter("%(message)s")
            else:
                file_formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
                )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(self.log_level)
            self.base_logger.addHandler(file_handler)


class BeachProfileError(Exception):
    """Custom exception class for beach profile database errors.

    Provides structured error information with severity, category, and context.
    """

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        context: dict[str, Any] | None = None,
        original_exception: Exception | None = None,
        user_message: str | None = None,
    ) -> None:
        """Initialize a beach profile error with detailed context.

        This method creates a BeachProfileError instance with comprehensive error
        information including severity, category, context, and user-friendly messaging.
        The error can wrap original exceptions while providing additional structured
        information for better error handling and logging.

        Parameters:
            message (str): The technical error message describing what went wrong.
            severity (ErrorSeverity, optional): The severity level of the error.
                Defaults to ErrorSeverity.ERROR.
            category (ErrorCategory, optional): The category of the error for
                classification and routing. Defaults to ErrorCategory.SYSTEM.
            context (dict[str, Any] | None, optional): Additional context information
                such as file paths, user IDs, or operation parameters. Defaults to None.
            original_exception (Exception | None, optional): The original exception
                that caused this error, if any. Defaults to None.
            user_message (str | None, optional): A user-friendly message suitable
                for display to end users. If None, a generic message may be generated.
                Defaults to None.

        Attributes Set:
            message (str): The technical error message.
            severity (ErrorSeverity): The error severity level.
            category (ErrorCategory): The error category.
            context (dict[str, Any]): Additional context data.
            original_exception (Exception | None): The wrapped original exception.
            user_message (str | None): User-friendly message.

        Example:
            >>> error = BeachProfileError(
            ...     "Database connection failed",
            ...     category=ErrorCategory.DATABASE,
            ...     context={"host": "localhost", "port": 5432},
            ...     user_message="Unable to connect to database. Please try again later."
            ... )
        """
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.category = category
        self.context = context or {}
        self.original_exception = original_exception
        self.user_message = user_message


class ErrorHandler:
    """Centralized error handling and logging system.

    Provides consistent error formatting, logging, and user communication
    across the entire beach profile database application.
    """

    # Error message templates for consistency
    ERROR_TEMPLATES = {
        ErrorCategory.DATABASE: {
            "connection_failed": "Database connection failed: {details}",
            "query_failed": "Database query failed: {details}",
            "transaction_failed": "Database transaction failed: {details}",
            "index_creation_failed": "Failed to create database index: {details}",
            "partition_creation_failed": "Failed to create data partition: {details}",
        },
        ErrorCategory.FILE_IO: {
            "file_not_found": "File not found: {file_path}",
            "permission_denied": "Permission denied accessing file: {file_path}",
            "invalid_format": "Invalid file format: {file_path} - {details}",
            "read_error": "Error reading file: {file_path} - {details}",
            "write_error": "Error writing file: {file_path} - {details}",
        },
        ErrorCategory.VALIDATION: {
            "invalid_data": "Data validation failed: {details}",
            "missing_required_field": "Missing required field: {field_name}",
            "invalid_coordinate": "Invalid coordinate values: {details}",
            "date_format_error": "Invalid date format: {details}",
        },
        ErrorCategory.SPATIAL: {
            "invalid_geometry": "Invalid spatial geometry: {details}",
            "projection_error": "Coordinate system projection error: {details}",
            "bbox_error": "Invalid bounding box coordinates: {details}",
        },
        ErrorCategory.PROCESSING: {
            "import_failed": "Data import failed: {details}",
            "export_failed": "Data export failed: {details}",
            "processing_error": "Data processing error: {details}",
        },
        ErrorCategory.CONFIGURATION: {
            "invalid_config": "Invalid configuration: {details}",
            "missing_config": "Missing configuration: {setting_name}",
        },
        ErrorCategory.USER_INPUT: {
            "invalid_parameter": "Invalid parameter: {parameter_name} - {details}",
            "missing_parameter": "Missing required parameter: {parameter_name}",
        },
        ErrorCategory.SYSTEM: {
            "unexpected_error": "Unexpected system error: {details}",
            "memory_error": "Memory allocation error: {details}",
            "timeout_error": "Operation timeout: {details}",
        },
    }

    def __init__(
        self,
        log_level: int = logging.INFO,
        log_file: str | None = None,
        enable_structured: bool = False,
    ) -> None:
        """Initialize the error handler with comprehensive logging configuration."""
        self.log_level = log_level
        self.log_file = log_file
        self.enable_structured = enable_structured

        # Initialize the comprehensive logging system
        self.beach_logger = BeachProfileLogger(
            log_level=log_level,
            log_file=log_file,
            enable_structured=enable_structured,
            enable_console=True,
            enable_file=bool(log_file),
        )

        # For backward compatibility, keep a reference to the base logger
        # Use consistent name `base_logger` across logger classes
        self.base_logger = self.beach_logger.base_logger
        self.base_logger.debug("ErrorHandler.__init__ called")

        # Compatibility alias for older code that referenced `logger`
        self.logger = self.base_logger

        # Component loggers for different types of operations
        self._component_loggers: dict[LogComponent, StructuredLogger] = {}

    def get_component_logger(
        self, component: LogComponent
    ) -> StructuredLogger:
        """Get a component-specific logger for general logging operations.

        This method returns a StructuredLogger for the specified component,
        delegating to the BeachProfileLogger's get_component_logger method.
        The logger is cached for performance and reused on subsequent calls.

        Parameters:
            component (LogComponent): The application component that needs logging.

        Returns:
            StructuredLogger: A structured logger instance configured for the component.

        Example:
            >>> db_logger = error_handler.get_component_logger(LogComponent.DATABASE)
            >>> db_logger.info("Database operation completed")
        """
        return self.beach_logger.get_component_logger(component)

    def log_info(
        self,
        message: str,
        component: LogComponent = LogComponent.SYSTEM,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Log an informational message using the global error handler.

        This function logs a message at the INFO level through the centralized
        logging system. The message will be formatted and output according to
        the current logging configuration, including component-specific metadata
        and any additional context provided.

        Parameters:
            message (str): The informational message to log. This should be a clear,
                concise description of the event or state being recorded.
            component (LogComponent, optional): The application component associated
                with the message. Defaults to LogComponent.SYSTEM. This helps categorize
                log entries for better filtering and analysis.
            extra (dict[str, Any] | None, optional): Additional context data to include
                in the log entry, such as user IDs, operation details, or metrics.
                Defaults to None.

        Returns:
            None
        """
        logger = self.get_component_logger(component)
        logger.info(message, extra)

    def log_warning(
        self,
        message: str,
        component: LogComponent = LogComponent.SYSTEM,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Log a warning message using the global error handler.

        This function logs a message at the WARNING level through the centralized
        logging system. Warning messages indicate potential issues or unexpected
        conditions that do not prevent operation but may require attention.

        Parameters:
            message (str): The warning message to log. This should describe the
                potential issue or unusual condition.
            component (LogComponent, optional): The application component associated
                with the warning. Defaults to LogComponent.SYSTEM.
            extra (dict[str, Any] | None, optional): Additional context data to include
                in the log entry. Defaults to None.

        Returns:
            None
        """
        logger = self.get_component_logger(component)
        logger.warning(message, extra)

    def log_error(
        self,
        message: str,
        component: LogComponent = LogComponent.SYSTEM,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Log an error message using the global error handler.

        This function logs a message at the ERROR level through the centralized
        logging system. Error messages indicate failures or exceptions that may
        impact application functionality.

        Parameters:
            message (str): The error message to log. This should describe the
                failure or exception that occurred.
            component (LogComponent, optional): The application component associated
                with the error. Defaults to LogComponent.SYSTEM.
            extra (dict[str, Any] | None, optional): Additional context data to include
                in the log entry. Defaults to None.

        Returns:
            None
        """
        logger = self.get_component_logger(component)
        logger.error(message, extra)

    def log_debug(
        self,
        message: str,
        component: LogComponent = LogComponent.SYSTEM,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Log a debug message for detailed diagnostic information.

        Records a debug-level message containing detailed diagnostic information
        useful for development and troubleshooting. Debug messages are typically
        not shown in production environments.

        Args:
            message: The debug message to log.
            component: Application component where the debug event occurred.
            extra: Optional additional context data for the log entry.
        """
        logger = self.get_component_logger(component)
        logger.debug(message, extra)

    def log_critical(
        self,
        message: str,
        component: LogComponent = LogComponent.SYSTEM,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Log a critical error that may prevent continued operation.

        Records a critical-level error message indicating a serious problem
        that may prevent the application from continuing normal operation.

        Args:
            message: The critical error message to log.
            component: Application component where the error occurred.
            extra: Optional additional context data for the log entry.
        """
        logger = self.get_component_logger(component)
        logger.critical(message, extra)

    def log(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        """Standard logging log method for compatibility.

        This method provides compatibility with the standard Python logging.Logger
        interface, allowing StructuredLogger to be used as a drop-in replacement.
        It delegates to the underlying base logger.

        Parameters:
            level (int): The logging level (e.g., logging.INFO).
            message (str): The log message.
            *args: Variable positional arguments passed to the base logger.
            **kwargs: Variable keyword arguments passed to the base logger.

        Returns:
            None

        Note:
            This method does not use structured formatting. For structured logging,
            use the level-specific methods (debug, info, warning, error, critical).
        """
        self.base_logger.log(level, message, *args, **kwargs)

    def isEnabledFor(self, level: int) -> bool:
        """Check if logging is enabled for the given level.

        This method checks whether the underlying logger is configured to log
        messages at the specified level, allowing callers to avoid expensive
        message formatting when logging is disabled.

        Parameters:
            level (int): The logging level to check (e.g., logging.DEBUG).

        Returns:
            bool: True if logging is enabled for the level, False otherwise.

        Example:
            >>> if logger.isEnabledFor(logging.DEBUG):
            ...     logger.debug("Expensive debug info", {"data": expensive_computation()})
        """
        return self.base_logger.isEnabledFor(level)

    def setLevel(self, level: int) -> None:
        """Set the logging level for this logger.

        This method sets the minimum logging level for the underlying logger.
        Messages below this level will be filtered out and not logged.

        Parameters:
            level (int): The logging level to set (e.g., logging.INFO).

        Returns:
            None

        Example:
            >>> logger.setLevel(logging.DEBUG)  # Enable all log levels
            >>> logger.setLevel(logging.ERROR)  # Only log errors and critical messages
        """

        # ErrorHandler stores a reference to the base logger on self.base_logger
        # (assigned from beach_logger.base_logger during initialization)
        self.base_logger.setLevel(level)

    def addHandler(self, handler: logging.Handler) -> None:
        """Add a handler to the logger.

        This method adds a logging handler to the underlying logger, allowing
        customization of log output destinations and formats.

        Parameters:
            handler (logging.Handler): The handler to add (e.g., StreamHandler, FileHandler).

        Returns:
            None

        Example:
            >>> import logging
            >>> handler = logging.FileHandler("app.log")
            >>> logger.addHandler(handler)
        """
        self.base_logger.addHandler(handler)

    def removeHandler(self, handler: logging.Handler) -> None:
        """Remove a handler from the logger.

        This method removes a previously added logging handler from the underlying logger.

        Parameters:
            handler (logging.Handler): The handler to remove.

        Returns:
            None

        Example:
            >>> logger.removeHandler(file_handler)
        """
        self.base_logger.removeHandler(handler)

    def hasHandlers(self) -> bool:
        """Check if the logger has any handlers configured.

        This method checks whether the underlying logger has any handlers attached,
        which determines whether log messages will be output anywhere.

        Parameters:
            None

        Returns:
            bool: True if the logger has handlers, False otherwise.

        Example:
            >>> if not logger.hasHandlers():
            ...     logger.addHandler(logging.StreamHandler())
        """
        return self.base_logger.hasHandlers()

    @property
    def level(self) -> int:
        """Get the current logging level.

        This property returns the current logging level of the underlying logger.

        Parameters:
            None

        Returns:
            int: The current logging level (e.g., logging.INFO).

        Example:
            >>> current_level = logger.level
            >>> print(f"Current level: {logging.getLevelName(current_level)}")
        """
        return self.base_logger.level

    @property
    def handlers(self) -> list:
        """Get the list of handlers attached to the logger.

        This property returns a list of all logging handlers currently attached
        to the underlying logger.

        Parameters:
            None

        Returns:
            list: List of logging.Handler objects attached to the logger.

        Example:
            >>> handlers = logger.handlers
            >>> print(f"Number of handlers: {len(handlers)}")
        """
        return self.base_logger.handlers

    def performance(
        self,
        operation: str,
        duration: float,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Log performance metrics with structured format.

        This method logs performance information including operation duration
        and additional metrics. Performance logs help monitor application
        performance and identify bottlenecks.

        Parameters:
            operation (str): The name or description of the operation being measured.
            duration (float): The duration of the operation in seconds.
            extra (dict[str, Any] | None, optional): Additional performance metrics
                or context data to include in the log entry. Defaults to None.

        Returns:
            None

        Example:
            >>> logger.performance("database_query", 0.125, {"rows_returned": 150, "query_type": "SELECT"})
        """
        perf_data = {
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            **(extra or {}),
        }
        self.log_info(
            f"Performance: {operation}", extra={"performance": perf_data}
        )

    def audit(
        self,
        action: str,
        user: str | None = None,
        resource: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Log an audit event for security and compliance tracking.

        Records an audit event with user, action, and resource information for
        security monitoring and compliance purposes.

        Args:
            action: The action being performed (e.g., "login", "data_export").
            user: Optional identifier of the user performing the action.
            resource: Optional identifier of the resource being accessed.
            component: Application component where the action occurred.
            extra: Optional additional context data for the audit log.
        """
        audit_data = {
            "action": action,
            "user": user,
            "resource": resource,
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            **(extra or {}),
        }
        self.log_info(f"Audit: {action}", extra={"audit": audit_data})


# Custom Exceptions
class DataProcessingError(Exception):
    """Base exception for data processing operations."""

    pass


class FileOperationError(DataProcessingError):
    """Raised when file operations fail."""

    pass


class ValidationError(DataProcessingError):
    """Raised when data validation fails."""

    pass


class CoordinateError(DataProcessingError):
    """Raised when coordinate operations fail."""

    pass


class FormatError(DataProcessingError):
    """Raised when data format parsing fails."""

    pass


# Validation Helpers
def validate_file_path(path: Union[str, Path]) -> Path:
    """Ensure the given path exists and is a file."""
    path = Path(path)
    if not path.is_file():
        raise FileOperationError(f"Invalid file path: {path}")
    return path


def handle_database_error(
    error: Exception,
    operation: str,
    context: dict[str, Any] | None = None,
) -> None:
    """Handle database-specific errors with appropriate logging and user messaging.

    Provides specialized error handling for database operations, categorizing
    the error appropriately and generating user-friendly messages for database
    connection and operation failures.

    Args:
        error: The database exception that occurred.
        operation: Description of the database operation that failed.
        context: Optional additional context about the database operation.
    """
    handle_error(
        f"Database operation failed: {operation} - {str(error)}",
        severity="ERROR",
        category="DATABASE",
        user_message=f"Database operation failed: {operation}. Please check your database connection and try again.",
        context=context,
    )


# Global error handler instance for convenience functions
_global_error_handler = ErrorHandler()


def handle_error(
    message: str,
    severity: str = "ERROR",
    category: str = "SYSTEM",
    user_message: str | None = None,
    context: dict[str, Any] | None = None,
) -> None:
    """Standalone error handling function that logs and optionally raises errors.

    This function provides a unified interface for error handling across the application.
    It logs the error with appropriate severity and category, and can provide user-friendly
    messages for better error communication.

    Parameters:
        message (str): The technical error message.
        severity (str): Error severity level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
        category (str): Error category for classification.
        user_message (str | None): User-friendly message for display.
        context (dict[str, Any] | None): Additional context data.
    """
    # Map string severity to ErrorSeverity enum
    severity_map = {
        "DEBUG": ErrorSeverity.DEBUG,
        "INFO": ErrorSeverity.INFO,
        "WARNING": ErrorSeverity.WARNING,
        "ERROR": ErrorSeverity.ERROR,
        "CRITICAL": ErrorSeverity.CRITICAL,
    }
    error_severity = severity_map.get(severity.upper(), ErrorSeverity.ERROR)

    # Map string category to ErrorCategory enum
    category_map = {
        "DATABASE": ErrorCategory.DATABASE,
        "FILE_IO": ErrorCategory.FILE_IO,
        "VALIDATION": ErrorCategory.VALIDATION,
        "SPATIAL": ErrorCategory.SPATIAL,
        "PROCESSING": ErrorCategory.PROCESSING,
        "CONFIGURATION": ErrorCategory.CONFIGURATION,
        "USER_INPUT": ErrorCategory.USER_INPUT,
        "SYSTEM": ErrorCategory.SYSTEM,
    }
    error_category = category_map.get(category.upper(), ErrorCategory.SYSTEM)

    # Create BeachProfileError
    error = BeachProfileError(
        message=message,
        severity=error_severity,
        category=error_category,
        context=context,
        user_message=user_message,
    )

    # Log the error
    component = LogComponent.SYSTEM
    if category.upper() == "DATABASE":
        component = LogComponent.DATABASE
    elif category.upper() in [
        "FILE_IO",
        "VALIDATION",
        "SPATIAL",
        "PROCESSING",
    ]:
        component = LogComponent.DATA_PROCESSING

    _global_error_handler.log_error(str(error), component, context)


def get_logger(component: LogComponent) -> StructuredLogger:
    """Standalone function to get a component-specific logger.

    This function provides a convenient way to get a StructuredLogger for a specific
    application component without needing to instantiate an ErrorHandler.

    Parameters:
        component (LogComponent): The application component that needs logging.

    Returns:
        StructuredLogger: A structured logger instance configured for the component.

    Example:
        >>> db_logger = get_logger(LogComponent.DATABASE)
        >>> db_logger.info("Database connection established")
    """
    return _global_error_handler.get_component_logger(component)
