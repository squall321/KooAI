"""
Tests for Structured Logging System

Tests the StructuredLogger, RequestLogger, MetricsLogger, and AuditLogger classes.
"""

import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from datetime import datetime


class TestStructuredLogger:
    """Test StructuredLogger class"""

    @pytest.fixture
    def temp_log_file(self, tmp_path: Path) -> Path:
        """Create temporary log file"""
        return tmp_path / "test.log"

    def test_structured_logger_creation(self, temp_log_file: Path) -> None:
        """Test StructuredLogger can be created"""
        from src.infrastructure.logging.structured_logging import StructuredLogger

        logger = StructuredLogger("test", log_file=temp_log_file, level="INFO")
        assert logger is not None
        assert logger.logger.name == "test"

    def test_logger_level_configuration(self, temp_log_file: Path) -> None:
        """Test logger level can be configured"""
        from src.infrastructure.logging.structured_logging import StructuredLogger

        logger = StructuredLogger("test", level="DEBUG")
        assert logger.logger.level == logging.DEBUG

        logger = StructuredLogger("test2", level="ERROR")
        assert logger.logger.level == logging.ERROR

    def test_logger_creates_log_directory(self, tmp_path: Path) -> None:
        """Test logger creates log directory if not exists"""
        from src.infrastructure.logging.structured_logging import StructuredLogger

        log_file = tmp_path / "nested" / "dir" / "test.log"
        logger = StructuredLogger("test", log_file=log_file)

        assert log_file.parent.exists()

    def test_logger_info_method(self, temp_log_file: Path) -> None:
        """Test logger.info() logs message"""
        from src.infrastructure.logging.structured_logging import StructuredLogger

        logger = StructuredLogger("test", log_file=temp_log_file, use_json=False)
        logger.info("Test message", user_id="123")

        # Verify log file contains message
        content = temp_log_file.read_text()
        assert "Test message" in content

    def test_logger_error_method(self, temp_log_file: Path) -> None:
        """Test logger.error() logs error"""
        from src.infrastructure.logging.structured_logging import StructuredLogger

        logger = StructuredLogger("test", log_file=temp_log_file, use_json=False)
        logger.error("Error occurred", error_code="E001")

        content = temp_log_file.read_text()
        assert "Error occurred" in content

    def test_logger_debug_method(self, temp_log_file: Path) -> None:
        """Test logger.debug() logs debug message"""
        from src.infrastructure.logging.structured_logging import StructuredLogger

        logger = StructuredLogger("test", log_file=temp_log_file, level="DEBUG", use_json=False)
        logger.debug("Debug info")

        content = temp_log_file.read_text()
        assert "Debug info" in content

    def test_logger_warning_method(self, temp_log_file: Path) -> None:
        """Test logger.warning() logs warning"""
        from src.infrastructure.logging.structured_logging import StructuredLogger

        logger = StructuredLogger("test", log_file=temp_log_file, use_json=False)
        logger.warning("Warning message")

        content = temp_log_file.read_text()
        assert "Warning message" in content

    def test_logger_critical_method(self, temp_log_file: Path) -> None:
        """Test logger.critical() logs critical message"""
        from src.infrastructure.logging.structured_logging import StructuredLogger

        logger = StructuredLogger("test", log_file=temp_log_file, use_json=False)
        logger.critical("Critical issue")

        content = temp_log_file.read_text()
        assert "Critical issue" in content

    def test_logger_with_extra_fields(self, temp_log_file: Path) -> None:
        """Test logger accepts extra fields"""
        from src.infrastructure.logging.structured_logging import StructuredLogger

        logger = StructuredLogger("test", log_file=temp_log_file, use_json=False)
        logger.info("Event", user_id="usr_123", action="login")

        # Should not raise exception
        assert temp_log_file.exists()


class TestRequestLogger:
    """Test RequestLogger class"""

    @pytest.fixture
    def mock_structured_logger(self) -> Mock:
        """Create mock StructuredLogger"""
        mock = Mock()
        mock.info = Mock()
        return mock

    def test_request_logger_creation(self, mock_structured_logger: Mock) -> None:
        """Test RequestLogger can be created"""
        from src.infrastructure.logging.structured_logging import RequestLogger

        req_logger = RequestLogger(mock_structured_logger)
        assert req_logger is not None

    @pytest.mark.asyncio
    async def test_log_request_basic(self, mock_structured_logger: Mock) -> None:
        """Test logging basic HTTP request"""
        from src.infrastructure.logging.structured_logging import RequestLogger

        req_logger = RequestLogger(mock_structured_logger)
        await req_logger.log_request("GET", "/api/files", 200, 45.5)

        mock_structured_logger.info.assert_called_once()
        call_args = mock_structured_logger.info.call_args
        assert "GET" in call_args[0][0]
        assert "/api/files" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_log_request_with_user(self, mock_structured_logger: Mock) -> None:
        """Test logging request with user ID"""
        from src.infrastructure.logging.structured_logging import RequestLogger

        req_logger = RequestLogger(mock_structured_logger)
        await req_logger.log_request(
            "POST", "/api/upload", 201, 150.25, user_id="usr_123"
        )

        call_args = mock_structured_logger.info.call_args
        assert call_args[1]["user_id"] == "usr_123"

    @pytest.mark.asyncio
    async def test_log_request_rounds_duration(self, mock_structured_logger: Mock) -> None:
        """Test request duration is rounded"""
        from src.infrastructure.logging.structured_logging import RequestLogger

        req_logger = RequestLogger(mock_structured_logger)
        await req_logger.log_request("GET", "/api/status", 200, 123.456789)

        call_args = mock_structured_logger.info.call_args
        assert call_args[1]["duration_ms"] == 123.46


class TestMetricsLogger:
    """Test MetricsLogger class"""

    @pytest.fixture
    def mock_structured_logger(self) -> Mock:
        """Create mock StructuredLogger"""
        mock = Mock()
        mock.info = Mock()
        return mock

    def test_metrics_logger_creation(self, mock_structured_logger: Mock) -> None:
        """Test MetricsLogger can be created"""
        from src.infrastructure.logging.structured_logging import MetricsLogger

        metrics_logger = MetricsLogger(mock_structured_logger)
        assert metrics_logger is not None

    def test_log_file_upload(self, mock_structured_logger: Mock) -> None:
        """Test logging file upload event"""
        from src.infrastructure.logging.structured_logging import MetricsLogger

        metrics_logger = MetricsLogger(mock_structured_logger)
        metrics_logger.log_file_upload(
            user_id="usr_123",
            filename="data.vtk",
            file_size=10485760,  # 10MB
            duration_seconds=5.5,
            success=True,
        )

        call_args = mock_structured_logger.info.call_args
        assert call_args[1]["event_type"] == "file_upload"
        assert call_args[1]["file_size_mb"] == 10.0

    def test_log_llm_request(self, mock_structured_logger: Mock) -> None:
        """Test logging LLM request event"""
        from src.infrastructure.logging.structured_logging import MetricsLogger

        metrics_logger = MetricsLogger(mock_structured_logger)
        metrics_logger.log_llm_request(
            user_id="usr_123",
            model="claude-3-sonnet",
            prompt_tokens=100,
            completion_tokens=200,
            duration_seconds=2.5,
            cost_usd=0.05,
        )

        call_args = mock_structured_logger.info.call_args
        assert call_args[1]["event_type"] == "llm_request"
        assert call_args[1]["total_tokens"] == 300

    def test_log_visualization_render(self, mock_structured_logger: Mock) -> None:
        """Test logging visualization render event"""
        from src.infrastructure.logging.structured_logging import MetricsLogger

        metrics_logger = MetricsLogger(mock_structured_logger)
        metrics_logger.log_visualization_render(
            user_id="usr_123",
            viz_type="3d_mesh",
            duration_seconds=1.2,
            success=True,
        )

        call_args = mock_structured_logger.info.call_args
        assert call_args[1]["event_type"] == "visualization_render"
        assert call_args[1]["viz_type"] == "3d_mesh"

    def test_log_error(self, mock_structured_logger: Mock) -> None:
        """Test logging error event"""
        from src.infrastructure.logging.structured_logging import MetricsLogger

        mock_structured_logger.error = Mock()
        metrics_logger = MetricsLogger(mock_structured_logger)
        metrics_logger.log_error(
            error_type="ValidationError",
            error_message="Invalid file format",
            user_id="usr_123",
        )

        call_args = mock_structured_logger.error.call_args
        assert call_args[1]["event_type"] == "error"
        assert call_args[1]["error_type"] == "ValidationError"


class TestAuditLogger:
    """Test AuditLogger class"""

    @pytest.fixture
    def mock_structured_logger(self) -> Mock:
        """Create mock StructuredLogger"""
        mock = Mock()
        mock.info = Mock()
        return mock

    def test_audit_logger_creation(self, mock_structured_logger: Mock) -> None:
        """Test AuditLogger can be created"""
        from src.infrastructure.logging.structured_logging import AuditLogger

        audit_logger = AuditLogger(mock_structured_logger)
        assert audit_logger is not None

    def test_log_authentication_login(self, mock_structured_logger: Mock) -> None:
        """Test logging login authentication"""
        from src.infrastructure.logging.structured_logging import AuditLogger

        audit_logger = AuditLogger(mock_structured_logger)
        audit_logger.log_authentication(
            event="login",
            user_id="usr_123",
            email="user@example.com",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=True,
        )

        call_args = mock_structured_logger.info.call_args
        assert call_args[1]["event_type"] == "authentication"
        assert call_args[1]["auth_event"] == "login"

    def test_log_authentication_failed(self, mock_structured_logger: Mock) -> None:
        """Test logging failed authentication"""
        from src.infrastructure.logging.structured_logging import AuditLogger

        audit_logger = AuditLogger(mock_structured_logger)
        audit_logger.log_authentication(
            event="login_failed",
            user_id=None,
            email="bad@example.com",
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0",
            success=False,
        )

        call_args = mock_structured_logger.info.call_args
        assert call_args[1]["success"] is False

    def test_log_authorization(self, mock_structured_logger: Mock) -> None:
        """Test logging authorization event"""
        from src.infrastructure.logging.structured_logging import AuditLogger

        audit_logger = AuditLogger(mock_structured_logger)
        audit_logger.log_authorization(
            event="access_granted",
            user_id="usr_123",
            resource="simulation_file_456",
            action="read",
            granted=True,
        )

        call_args = mock_structured_logger.info.call_args
        assert call_args[1]["event_type"] == "authorization"
        assert call_args[1]["granted"] is True

    def test_log_data_access(self, mock_structured_logger: Mock) -> None:
        """Test logging data access event"""
        from src.infrastructure.logging.structured_logging import AuditLogger

        audit_logger = AuditLogger(mock_structured_logger)
        audit_logger.log_data_access(
            user_id="usr_123",
            resource_type="simulation_file",
            resource_id="file_456",
            action="write",
        )

        call_args = mock_structured_logger.info.call_args
        assert call_args[1]["event_type"] == "data_access"
        assert call_args[1]["action"] == "write"

    def test_log_configuration_change(self, mock_structured_logger: Mock) -> None:
        """Test logging configuration change"""
        from src.infrastructure.logging.structured_logging import AuditLogger

        audit_logger = AuditLogger(mock_structured_logger)
        audit_logger.log_configuration_change(
            user_id="admin_123",
            setting="max_upload_size",
            old_value="100MB",
            new_value="500MB",
        )

        call_args = mock_structured_logger.info.call_args
        assert call_args[1]["event_type"] == "configuration_change"
        assert call_args[1]["new_value"] == "500MB"


class TestGlobalLoggerInstances:
    """Test global logger instance functions"""

    def test_get_app_logger(self) -> None:
        """Test get_app_logger returns logger"""
        from src.infrastructure.logging.structured_logging import get_app_logger

        logger = get_app_logger()
        assert logger is not None
        assert logger.logger.name == "kooai"

    def test_get_request_logger(self) -> None:
        """Test get_request_logger returns RequestLogger"""
        from src.infrastructure.logging.structured_logging import get_request_logger

        logger = get_request_logger()
        assert logger is not None

    def test_get_metrics_logger(self) -> None:
        """Test get_metrics_logger returns MetricsLogger"""
        from src.infrastructure.logging.structured_logging import get_metrics_logger

        logger = get_metrics_logger()
        assert logger is not None

    def test_get_audit_logger(self) -> None:
        """Test get_audit_logger returns AuditLogger"""
        from src.infrastructure.logging.structured_logging import get_audit_logger

        logger = get_audit_logger()
        assert logger is not None
