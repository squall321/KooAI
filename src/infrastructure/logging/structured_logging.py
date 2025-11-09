"""
Structured Logging Configuration

Provides structured logging with JSON formatting for easy parsing and analysis.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import json

try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None


class StructuredLogger:
    """
    Structured logging service with JSON output.

    Provides consistent, parsable log format for analysis.
    """

    def __init__(
        self,
        name: str,
        log_file: Optional[Path] = None,
        level: str = "INFO",
        use_json: bool = True,
    ):
        """
        Initialize structured logger.

        Args:
            name: Logger name
            log_file: Optional log file path
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            use_json: Use JSON formatting (requires python-json-logger)

        Example:
            ```python
            logger = StructuredLogger("kooai", log_file=Path("app.log"))
            logger.info("User logged in", user_id="usr_123", ip="192.168.1.1")
            ```
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.handlers = []  # Clear existing handlers

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # File handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
        else:
            file_handler = None

        # Format
        if use_json and jsonlogger:
            # JSON format for structured logging
            formatter = jsonlogger.JsonFormatter(
                "%(timestamp)s %(name)s %(levelname)s %(message)s %(module)s %(funcName)s"
            )
        else:
            # Standard format
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        if file_handler:
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """Internal log method with extra fields."""
        extra = {
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs,
        }
        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with extra fields."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """
        Log info message with extra fields.

        Example:
            ```python
            logger.info("File uploaded", filename="data.vtk", size_mb=100)
            ```
        """
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with extra fields."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """
        Log error message with extra fields.

        Example:
            ```python
            logger.error("Database connection failed", db_url=url, error=str(e))
            ```
        """
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message with extra fields."""
        self._log(logging.CRITICAL, message, **kwargs)


class RequestLogger:
    """
    Request logging middleware for FastAPI.

    Logs HTTP requests with timing and status.
    """

    def __init__(self, logger: StructuredLogger):
        """Initialize request logger."""
        self.logger = logger

    async def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Log HTTP request.

        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            user_id: Optional user ID
            **kwargs: Additional fields
        """
        self.logger.info(
            f"{method} {path} {status_code}",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            user_id=user_id,
            **kwargs,
        )


class MetricsLogger:
    """
    Metrics logging for operational insights.

    Logs business metrics and KPIs.
    """

    def __init__(self, logger: StructuredLogger):
        """Initialize metrics logger."""
        self.logger = logger

    def log_file_upload(
        self,
        user_id: str,
        filename: str,
        file_size: int,
        duration_seconds: float,
        success: bool,
        **kwargs: Any,
    ) -> None:
        """Log file upload event."""
        self.logger.info(
            "File upload",
            event_type="file_upload",
            user_id=user_id,
            filename=filename,
            file_size_bytes=file_size,
            file_size_mb=round(file_size / 1024 / 1024, 2),
            duration_seconds=round(duration_seconds, 2),
            success=success,
            **kwargs,
        )

    def log_llm_request(
        self,
        user_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_seconds: float,
        cost_usd: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Log LLM request event."""
        self.logger.info(
            "LLM request",
            event_type="llm_request",
            user_id=user_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            duration_seconds=round(duration_seconds, 2),
            cost_usd=cost_usd,
            **kwargs,
        )

    def log_visualization_render(
        self,
        user_id: str,
        viz_type: str,
        duration_seconds: float,
        success: bool,
        **kwargs: Any,
    ) -> None:
        """Log visualization render event."""
        self.logger.info(
            "Visualization render",
            event_type="visualization_render",
            user_id=user_id,
            viz_type=viz_type,
            duration_seconds=round(duration_seconds, 2),
            success=success,
            **kwargs,
        )

    def log_error(
        self,
        error_type: str,
        error_message: str,
        user_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log error event."""
        self.logger.error(
            "Error occurred",
            event_type="error",
            error_type=error_type,
            error_message=error_message,
            user_id=user_id,
            **kwargs,
        )


class AuditLogger:
    """
    Audit logging for security and compliance.

    Logs security-relevant events.
    """

    def __init__(self, logger: StructuredLogger):
        """Initialize audit logger."""
        self.logger = logger

    def log_authentication(
        self,
        event: str,  # login, logout, login_failed, token_refresh
        user_id: Optional[str],
        email: Optional[str],
        ip_address: str,
        user_agent: str,
        success: bool,
        **kwargs: Any,
    ) -> None:
        """Log authentication event."""
        self.logger.info(
            f"Authentication: {event}",
            event_type="authentication",
            auth_event=event,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            **kwargs,
        )

    def log_authorization(
        self,
        event: str,  # access_granted, access_denied
        user_id: str,
        resource: str,
        action: str,
        granted: bool,
        **kwargs: Any,
    ) -> None:
        """Log authorization event."""
        self.logger.info(
            f"Authorization: {event}",
            event_type="authorization",
            auth_event=event,
            user_id=user_id,
            resource=resource,
            action=action,
            granted=granted,
            **kwargs,
        )

    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,  # read, write, delete
        **kwargs: Any,
    ) -> None:
        """Log data access event."""
        self.logger.info(
            f"Data access: {action} {resource_type}",
            event_type="data_access",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            **kwargs,
        )

    def log_configuration_change(
        self,
        user_id: str,
        setting: str,
        old_value: str,
        new_value: str,
        **kwargs: Any,
    ) -> None:
        """Log configuration change."""
        self.logger.info(
            f"Configuration changed: {setting}",
            event_type="configuration_change",
            user_id=user_id,
            setting=setting,
            old_value=old_value,
            new_value=new_value,
            **kwargs,
        )


# Global logger instances
_app_logger: Optional[StructuredLogger] = None
_request_logger: Optional[RequestLogger] = None
_metrics_logger: Optional[MetricsLogger] = None
_audit_logger: Optional[AuditLogger] = None


def get_app_logger() -> StructuredLogger:
    """Get application logger instance."""
    global _app_logger
    if _app_logger is None:
        _app_logger = StructuredLogger(
            "kooai",
            log_file=Path("logs/app.log"),
            level="INFO",
        )
    return _app_logger


def get_request_logger() -> RequestLogger:
    """Get request logger instance."""
    global _request_logger
    if _request_logger is None:
        logger = StructuredLogger(
            "kooai.requests",
            log_file=Path("logs/requests.log"),
            level="INFO",
        )
        _request_logger = RequestLogger(logger)
    return _request_logger


def get_metrics_logger() -> MetricsLogger:
    """Get metrics logger instance."""
    global _metrics_logger
    if _metrics_logger is None:
        logger = StructuredLogger(
            "kooai.metrics",
            log_file=Path("logs/metrics.log"),
            level="INFO",
        )
        _metrics_logger = MetricsLogger(logger)
    return _metrics_logger


def get_audit_logger() -> AuditLogger:
    """Get audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        logger = StructuredLogger(
            "kooai.audit",
            log_file=Path("logs/audit.log"),
            level="INFO",
        )
        _audit_logger = AuditLogger(logger)
    return _audit_logger
