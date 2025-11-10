"""
Tests for Logging Configuration

Tests the LogConfig class and logging setup functions.
"""

import logging
import os
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch, MagicMock
import pytest


class TestLogConfig:
    """Test LogConfig class"""

    def test_log_config_creation(self) -> None:
        """Test LogConfig can be created"""
        from src.infrastructure.logging.config import LogConfig

        config = LogConfig(level="INFO", format="console")
        assert config is not None
        assert config.level == logging.INFO
        assert config.format == "console"

    def test_log_config_parse_debug_level(self) -> None:
        """Test parsing DEBUG level"""
        from src.infrastructure.logging.config import LogConfig

        config = LogConfig(level="DEBUG")
        assert config.level == logging.DEBUG

    def test_log_config_parse_error_level(self) -> None:
        """Test parsing ERROR level"""
        from src.infrastructure.logging.config import LogConfig

        config = LogConfig(level="ERROR")
        assert config.level == logging.ERROR

    def test_log_config_parse_warning_level(self) -> None:
        """Test parsing WARNING level"""
        from src.infrastructure.logging.config import LogConfig

        config = LogConfig(level="WARNING")
        assert config.level == logging.WARNING

    def test_log_config_parse_critical_level(self) -> None:
        """Test parsing CRITICAL level"""
        from src.infrastructure.logging.config import LogConfig

        config = LogConfig(level="CRITICAL")
        assert config.level == logging.CRITICAL

    def test_log_config_case_insensitive(self) -> None:
        """Test level parsing is case insensitive"""
        from src.infrastructure.logging.config import LogConfig

        config = LogConfig(level="debug")
        assert config.level == logging.DEBUG

    def test_log_config_invalid_level_defaults_to_info(self) -> None:
        """Test invalid level defaults to INFO"""
        from src.infrastructure.logging.config import LogConfig

        config = LogConfig(level="INVALID")
        assert config.level == logging.INFO

    def test_log_config_json_format(self) -> None:
        """Test JSON format configuration"""
        from src.infrastructure.logging.config import LogConfig

        config = LogConfig(format="json")
        assert config.format == "json"

    def test_log_config_console_format(self) -> None:
        """Test console format configuration"""
        from src.infrastructure.logging.config import LogConfig

        config = LogConfig(format="console")
        assert config.format == "console"

    def test_log_config_with_log_file(self) -> None:
        """Test configuration with log file"""
        from src.infrastructure.logging.config import LogConfig

        config = LogConfig(log_file="/var/log/app.log")
        assert config.log_file == "/var/log/app.log"

    def test_log_config_environment(self) -> None:
        """Test environment configuration"""
        from src.infrastructure.logging.config import LogConfig

        config = LogConfig(environment="production")
        assert config.environment == "production"

    def test_log_config_from_env(self) -> None:
        """Test creating config from environment variables"""
        from src.infrastructure.logging.config import LogConfig

        with patch.dict(os.environ, {
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "json",
            "LOG_FILE": "/tmp/test.log",
            "ENVIRONMENT": "production"
        }):
            config = LogConfig.from_env()
            assert config.level == logging.DEBUG
            assert config.format == "json"
            assert config.log_file == "/tmp/test.log"
            assert config.environment == "production"

    def test_log_config_from_env_defaults(self) -> None:
        """Test from_env uses defaults when env vars not set"""
        from src.infrastructure.logging.config import LogConfig

        with patch.dict(os.environ, {}, clear=True):
            config = LogConfig.from_env()
            assert config.level == logging.INFO
            assert config.format == "console"
            assert config.environment == "development"


class TestLoggingProcessors:
    """Test logging processor functions"""

    def test_add_timestamp_processor(self) -> None:
        """Test add_timestamp processor"""
        from src.infrastructure.logging.config import add_timestamp

        event_dict = {"event": "test"}
        result = add_timestamp(None, "", event_dict)

        assert "timestamp" in result
        # Timestamp should be ISO format
        assert "T" in result["timestamp"]

    def test_add_app_context_processor(self) -> None:
        """Test add_app_context processor"""
        from src.infrastructure.logging.config import add_app_context, LogConfig

        # Setup config
        config = LogConfig(environment="test")
        with patch("src.infrastructure.logging.config._current_config", config):
            event_dict = {"event": "test"}
            result = add_app_context(None, "", event_dict)

            assert result["app"] == "kooai"
            assert result["environment"] == "test"

    def test_censor_sensitive_data_password(self) -> None:
        """Test censoring password field"""
        from src.infrastructure.logging.config import censor_sensitive_data

        event_dict = {"user": "john", "password": "secret123"}
        result = censor_sensitive_data(None, "", event_dict)

        assert result["password"] == "***CENSORED***"
        assert result["user"] == "john"

    def test_censor_sensitive_data_token(self) -> None:
        """Test censoring token field"""
        from src.infrastructure.logging.config import censor_sensitive_data

        event_dict = {"auth_token": "abc123", "user_id": "123"}
        result = censor_sensitive_data(None, "", event_dict)

        assert result["auth_token"] == "***CENSORED***"
        assert result["user_id"] == "123"

    def test_censor_sensitive_data_api_key(self) -> None:
        """Test censoring API key field"""
        from src.infrastructure.logging.config import censor_sensitive_data

        event_dict = {"api_key": "sk-123456", "action": "upload"}
        result = censor_sensitive_data(None, "", event_dict)

        assert result["api_key"] == "***CENSORED***"

    def test_censor_sensitive_data_secret(self) -> None:
        """Test censoring secret field"""
        from src.infrastructure.logging.config import censor_sensitive_data

        event_dict = {"aws_secret": "xyz789", "region": "us-east-1"}
        result = censor_sensitive_data(None, "", event_dict)

        assert result["aws_secret"] == "***CENSORED***"

    def test_censor_multiple_sensitive_fields(self) -> None:
        """Test censoring multiple sensitive fields"""
        from src.infrastructure.logging.config import censor_sensitive_data

        event_dict = {
            "password": "pass123",
            "api_key": "key456",
            "username": "john"
        }
        result = censor_sensitive_data(None, "", event_dict)

        assert result["password"] == "***CENSORED***"
        assert result["api_key"] == "***CENSORED***"
        assert result["username"] == "john"


class TestLoggingSetup:
    """Test logging setup functions"""

    def test_setup_logging_with_config(self) -> None:
        """Test setup_logging with LogConfig"""
        from src.infrastructure.logging.config import setup_logging, LogConfig

        config = LogConfig(level="DEBUG", format="console")
        setup_logging(config)

        # Should not raise exception
        assert True

    def test_setup_logging_without_config(self) -> None:
        """Test setup_logging without config uses env"""
        from src.infrastructure.logging.config import setup_logging

        with patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}):
            setup_logging()
            # Should not raise exception
            assert True

    @pytest.mark.skip(reason="Requires structlog and file system access")
    def test_setup_logging_with_file_handler(self, tmp_path: Path) -> None:
        """Test setup_logging creates file handler"""
        from src.infrastructure.logging.config import setup_logging, LogConfig

        log_file = tmp_path / "test.log"
        config = LogConfig(log_file=str(log_file))
        setup_logging(config)

        # File should be created when logging occurs
        import structlog
        logger = structlog.get_logger()
        logger.info("test message")

    def test_get_logger(self) -> None:
        """Test get_logger returns logger"""
        from src.infrastructure.logging.config import get_logger

        logger = get_logger("test.module")
        assert logger is not None

    def test_get_request_logger(self) -> None:
        """Test get_request_logger returns logger"""
        from src.infrastructure.logging.config import get_request_logger

        logger = get_request_logger()
        assert logger is not None

    def test_get_database_logger(self) -> None:
        """Test get_database_logger returns logger"""
        from src.infrastructure.logging.config import get_database_logger

        logger = get_database_logger()
        assert logger is not None

    def test_get_cache_logger(self) -> None:
        """Test get_cache_logger returns logger"""
        from src.infrastructure.logging.config import get_cache_logger

        logger = get_cache_logger()
        assert logger is not None

    def test_get_task_logger(self) -> None:
        """Test get_task_logger returns logger"""
        from src.infrastructure.logging.config import get_task_logger

        logger = get_task_logger()
        assert logger is not None

    def test_get_security_logger(self) -> None:
        """Test get_security_logger returns logger"""
        from src.infrastructure.logging.config import get_security_logger

        logger = get_security_logger()
        assert logger is not None
