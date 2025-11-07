"""
Logging Configuration

Centralized logging configuration using structlog.
Supports multiple environments (development, production) and output formats (console, JSON).
"""

import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.types import EventDict, Processor


class LogConfig:
    """
    Logging configuration settings

    Environment variables:
    - LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - LOG_FORMAT: Output format (console, json)
    - LOG_FILE: Optional log file path
    - ENVIRONMENT: Environment name (development, production)
    """

    def __init__(
        self,
        level: str = "INFO",
        format: str = "console",
        log_file: Optional[str] = None,
        environment: str = "development",
    ):
        self.level = self._parse_level(level)
        self.format = format.lower()
        self.log_file = log_file
        self.environment = environment.lower()

    @staticmethod
    def _parse_level(level: str) -> int:
        """Parse log level string to logging level"""
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return levels.get(level.upper(), logging.INFO)

    @classmethod
    def from_env(cls) -> "LogConfig":
        """Create config from environment variables"""
        import os

        return cls(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "console"),
            log_file=os.getenv("LOG_FILE"),
            environment=os.getenv("ENVIRONMENT", "development"),
        )


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application context to log events

    Adds:
    - app: Application name
    - version: Application version
    - environment: Environment name
    """
    event_dict["app"] = "kooai"
    event_dict["environment"] = _get_current_config().environment

    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add ISO8601 timestamp to log events"""
    import datetime

    event_dict["timestamp"] = datetime.datetime.utcnow().isoformat()
    return event_dict


def censor_sensitive_data(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Censor sensitive data in log events

    Censors fields like:
    - password
    - token
    - secret
    - api_key
    """
    sensitive_keys = ["password", "token", "secret", "api_key", "apikey"]

    for key in event_dict.keys():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            event_dict[key] = "***CENSORED***"

    return event_dict


def setup_logging(config: Optional[LogConfig] = None) -> None:
    """
    Configure structured logging for the application

    Args:
        config: LogConfig instance, or None to use environment variables

    Example:
        >>> from src.infrastructure.logging import setup_logging, get_logger
        >>> setup_logging()
        >>> logger = get_logger(__name__)
        >>> logger.info("application_started", version="1.0.0")
    """
    if config is None:
        config = LogConfig.from_env()

    # Store config globally
    global _current_config
    _current_config = config

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=config.level,
    )

    # Determine processors based on format
    if config.format == "json":
        processors = _get_json_processors()
    else:
        processors = _get_console_processors()

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(config.level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure file handler if specified
    if config.log_file:
        _setup_file_handler(config)


def _get_console_processors() -> list[Processor]:
    """Get processors for console output"""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        add_timestamp,
        add_app_context,
        censor_sensitive_data,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]


def _get_json_processors() -> list[Processor]:
    """Get processors for JSON output"""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_timestamp,
        add_app_context,
        censor_sensitive_data,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]


def _setup_file_handler(config: LogConfig) -> None:
    """Setup file handler for logging"""
    import logging.handlers

    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        filename=config.log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )

    file_handler.setLevel(config.level)

    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)


def _get_current_config() -> LogConfig:
    """Get current logging config"""
    global _current_config
    if _current_config is None:
        _current_config = LogConfig.from_env()
    return _current_config


# Global config storage
_current_config: Optional[LogConfig] = None


# Convenience function for getting logger
def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a configured logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structlog logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("user_logged_in", user_id=123, ip="192.168.1.1")
    """
    return structlog.get_logger(name)


# Pre-configured logger instances for common use cases
def get_request_logger() -> structlog.BoundLogger:
    """Get logger for HTTP requests"""
    return get_logger("kooai.request")


def get_database_logger() -> structlog.BoundLogger:
    """Get logger for database operations"""
    return get_logger("kooai.database")


def get_cache_logger() -> structlog.BoundLogger:
    """Get logger for cache operations"""
    return get_logger("kooai.cache")


def get_task_logger() -> structlog.BoundLogger:
    """Get logger for background tasks"""
    return get_logger("kooai.task")


def get_security_logger() -> structlog.BoundLogger:
    """Get logger for security events"""
    return get_logger("kooai.security")
