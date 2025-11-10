"""
Tests for Core Domain Exceptions

Tests KooAIError and all derived exception classes.
"""

import pytest


class TestKooAIError:
    """Test base KooAIError class"""

    def test_kooai_error_creation(self) -> None:
        """Test creating KooAIError"""
        from src.core.exceptions import KooAIError

        error = KooAIError("Test error message")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"

    def test_kooai_error_with_error_code(self) -> None:
        """Test KooAIError with custom error code"""
        from src.core.exceptions import KooAIError

        error = KooAIError("Test error", error_code="TEST_001")

        assert error.error_code == "TEST_001"

    def test_kooai_error_with_details(self) -> None:
        """Test KooAIError with details"""
        from src.core.exceptions import KooAIError

        details = {"field": "name", "value": "invalid"}
        error = KooAIError("Test error", details=details)

        assert error.details == details

    def test_kooai_error_default_error_code(self) -> None:
        """Test KooAIError generates default error code"""
        from src.core.exceptions import KooAIError

        error = KooAIError("Test error")

        assert error.error_code == "KOOAIERROR"

    def test_kooai_error_to_dict(self) -> None:
        """Test KooAIError to_dict method"""
        from src.core.exceptions import KooAIError

        error = KooAIError("Test error", error_code="TEST_001")
        error_dict = error.to_dict()

        assert error_dict["error_type"] == "KooAIError"
        assert error_dict["error_code"] == "TEST_001"
        assert error_dict["message"] == "Test error"

    def test_kooai_error_to_dict_with_details(self) -> None:
        """Test to_dict includes details"""
        from src.core.exceptions import KooAIError

        details = {"field": "name"}
        error = KooAIError("Test error", details=details)
        error_dict = error.to_dict()

        assert "details" in error_dict
        assert error_dict["details"] == details

    def test_kooai_error_str_with_details(self) -> None:
        """Test string representation with details"""
        from src.core.exceptions import KooAIError

        error = KooAIError("Test error", details={"key": "value"})
        error_str = str(error)

        assert "Test error" in error_str
        assert "details" in error_str


class TestParsingErrors:
    """Test parsing-related exceptions"""

    def test_parsing_error(self) -> None:
        """Test ParsingError"""
        from src.core.exceptions import ParsingError

        error = ParsingError("Failed to parse file")

        assert error.error_code == "PARSE_ERROR"
        assert isinstance(error, Exception)

    def test_unsupported_format_error(self) -> None:
        """Test UnsupportedFormatError"""
        from src.core.exceptions import UnsupportedFormatError

        error = UnsupportedFormatError("Unsupported format: .xyz")

        assert error.error_code == "PARSE_001"

    def test_corrupted_file_error(self) -> None:
        """Test CorruptedFileError"""
        from src.core.exceptions import CorruptedFileError

        error = CorruptedFileError("File is corrupted")

        assert error.error_code == "PARSE_002"

    def test_invalid_data_error(self) -> None:
        """Test InvalidDataError"""
        from src.core.exceptions import InvalidDataError

        error = InvalidDataError("Invalid data format")

        assert error.error_code == "PARSE_003"

    def test_missing_field_error(self) -> None:
        """Test MissingFieldError"""
        from src.core.exceptions import MissingFieldError

        error = MissingFieldError(field_name="velocity")

        assert error.error_code == "PARSE_004"
        assert error.field_name == "velocity"
        assert "velocity" in str(error)
        assert error.details["field_name"] == "velocity"

    def test_missing_field_error_custom_message(self) -> None:
        """Test MissingFieldError with custom message"""
        from src.core.exceptions import MissingFieldError

        error = MissingFieldError(
            field_name="pressure",
            message="Custom error message"
        )

        assert "Custom error message" in str(error)


class TestFileSystemErrors:
    """Test file system-related exceptions"""

    def test_file_system_error(self) -> None:
        """Test FileSystemError"""
        from src.core.exceptions import FileSystemError

        error = FileSystemError("File system error")

        assert error.error_code == "FS_ERROR"

    def test_file_not_found_error(self) -> None:
        """Test FileNotFoundError"""
        from src.core.exceptions import FileNotFoundError

        error = FileNotFoundError(file_path="/path/to/file.txt")

        assert error.error_code == "FS_001"
        assert error.file_path == "/path/to/file.txt"
        assert "/path/to/file.txt" in str(error)

    def test_file_permission_error(self) -> None:
        """Test FilePermissionError"""
        from src.core.exceptions import FilePermissionError

        error = FilePermissionError(
            file_path="/protected/file.txt",
            operation="write"
        )

        assert error.error_code == "FS_002"
        assert error.file_path == "/protected/file.txt"
        assert error.operation == "write"
        assert "write" in str(error)

    def test_file_permission_error_default_operation(self) -> None:
        """Test FilePermissionError with default operation"""
        from src.core.exceptions import FilePermissionError

        error = FilePermissionError(file_path="/file.txt")

        assert error.operation == "read"


class TestSimulationErrors:
    """Test simulation-related exceptions"""

    def test_simulation_error(self) -> None:
        """Test SimulationError"""
        from src.core.exceptions import SimulationError

        error = SimulationError("Simulation failed")

        assert isinstance(error, Exception)
        assert "Simulation failed" in str(error)


class TestComputationErrors:
    """Test computation-related exceptions"""

    def test_computation_error(self) -> None:
        """Test ComputationError"""
        from src.core.exceptions import ComputationError

        error = ComputationError("Computation failed")

        assert isinstance(error, Exception)
        assert "Computation failed" in str(error)


class TestDatabaseErrors:
    """Test database-related exceptions"""

    def test_database_error(self) -> None:
        """Test DatabaseError"""
        from src.core.exceptions import DatabaseError

        error = DatabaseError("Database connection failed")

        assert isinstance(error, Exception)
        assert "Database connection failed" in str(error)


class TestCacheErrors:
    """Test cache-related exceptions"""

    def test_cache_error(self) -> None:
        """Test CacheError"""
        from src.core.exceptions import CacheError

        error = CacheError("Cache unavailable")

        assert isinstance(error, Exception)
        assert "Cache unavailable" in str(error)


class TestAIErrors:
    """Test AI-related exceptions"""

    def test_ai_error(self) -> None:
        """Test AIError"""
        from src.core.exceptions import AIError

        error = AIError("AI model inference failed")

        assert isinstance(error, Exception)
        assert "AI model inference failed" in str(error)


class TestConfigurationErrors:
    """Test configuration-related exceptions"""

    def test_configuration_error(self) -> None:
        """Test ConfigurationError"""
        from src.core.exceptions import ConfigurationError

        error = ConfigurationError("Invalid configuration")

        assert isinstance(error, Exception)
        assert "Invalid configuration" in str(error)


class TestExternalServiceErrors:
    """Test external service-related exceptions"""

    def test_external_service_error(self) -> None:
        """Test ExternalServiceError"""
        from src.core.exceptions import ExternalServiceError

        error = ExternalServiceError("External API call failed")

        assert isinstance(error, Exception)
        assert "External API call failed" in str(error)


class TestExceptionInheritance:
    """Test exception inheritance hierarchy"""

    def test_parsing_error_is_kooai_error(self) -> None:
        """Test ParsingError inherits from KooAIError"""
        from src.core.exceptions import ParsingError, KooAIError

        error = ParsingError("Test")

        assert isinstance(error, KooAIError)

    def test_unsupported_format_is_parsing_error(self) -> None:
        """Test UnsupportedFormatError inherits from ParsingError"""
        from src.core.exceptions import UnsupportedFormatError, ParsingError

        error = UnsupportedFormatError("Test")

        assert isinstance(error, ParsingError)

    def test_file_not_found_is_file_system_error(self) -> None:
        """Test FileNotFoundError inherits from FileSystemError"""
        from src.core.exceptions import FileNotFoundError, FileSystemError

        error = FileNotFoundError("/file.txt")

        assert isinstance(error, FileSystemError)

    def test_all_errors_are_exceptions(self) -> None:
        """Test all errors inherit from Exception"""
        from src.core.exceptions import (
            KooAIError, ParsingError, FileSystemError,
            SimulationError, ComputationError
        )

        errors = [
            KooAIError("test"),
            ParsingError("test"),
            FileSystemError("test"),
            SimulationError("test"),
            ComputationError("test"),
        ]

        for error in errors:
            assert isinstance(error, Exception)
