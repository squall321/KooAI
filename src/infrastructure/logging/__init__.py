"""
Logging Infrastructure

Centralized logging system for KooAI platform.

Features:
- Structured logging with structlog
- Multiple output formats (console, JSON)
- Environment-based configuration
- Sensitive data censoring
- File rotation
- Pre-configured loggers for different components

Usage:
    from src.infrastructure.logging import setup_logging, get_logger

    # Initialize logging (once at application startup)
    setup_logging()

    # Get logger instance
    logger = get_logger(__name__)

    # Log structured events
    logger.info("user_action", user_id=123, action="login", ip="192.168.1.1")
    logger.error("processing_failed", file_id=456, error="timeout")

Environment Variables:
    LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
    LOG_FORMAT: console, json (default: console)
    LOG_FILE: Path to log file (default: None, logs to stdout)
    ENVIRONMENT: development, staging, production (default: development)
"""

from .config import (
    LogConfig,
    setup_logging,
    get_logger,
    get_request_logger,
    get_database_logger,
    get_cache_logger,
    get_task_logger,
    get_security_logger,
)

from .structured_logging import (
    StructuredLogger,
    RequestLogger as StructuredRequestLogger,
    MetricsLogger,
    AuditLogger,
    get_app_logger,
    get_metrics_logger,
    get_audit_logger,
)

from .log_analyzer import (
    LogAnalyzer,
    MetricsAnalyzer,
    AuditAnalyzer,
    generate_dashboard_report,
)

__all__ = [
    # Original loggers
    "LogConfig",
    "setup_logging",
    "get_logger",
    "get_request_logger",
    "get_database_logger",
    "get_cache_logger",
    "get_task_logger",
    "get_security_logger",
    # Structured loggers
    "StructuredLogger",
    "StructuredRequestLogger",
    "MetricsLogger",
    "AuditLogger",
    "get_app_logger",
    "get_metrics_logger",
    "get_audit_logger",
    # Analyzers
    "LogAnalyzer",
    "MetricsAnalyzer",
    "AuditAnalyzer",
    "generate_dashboard_report",
]
