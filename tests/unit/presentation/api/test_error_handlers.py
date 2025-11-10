"""
Tests for API Exception Handlers

Tests exception handlers and error response generation.
"""

from typing import Any
from unittest.mock import Mock, AsyncMock
import pytest
from fastapi import HTTPException


class TestErrorResponseGeneration:
    """Test error response generation functions"""

    def test_generate_request_id(self) -> None:
        """Test request ID generation"""
        from src.presentation.api.exceptions import generate_request_id

        request_id = generate_request_id()

        assert request_id is not None
        assert isinstance(request_id, str)
        assert len(request_id) > 0

    def test_request_id_is_unique(self) -> None:
        """Test request IDs are unique"""
        from src.presentation.api.exceptions import generate_request_id

        id1 = generate_request_id()
        id2 = generate_request_id()

        assert id1 != id2

    def test_create_error_response_basic(self) -> None:
        """Test creating basic error response"""
        from src.presentation.api.exceptions import create_error_response

        response = create_error_response(
            error_type="TestError", message="Test message", status_code=400
        )

        assert response["error"]["type"] == "TestError"
        assert response["error"]["message"] == "Test message"
        assert response["error"]["status_code"] == 400

    def test_create_error_response_with_code(self) -> None:
        """Test error response with error code"""
        from src.presentation.api.exceptions import create_error_response

        response = create_error_response(
            error_type="TestError",
            message="Test message",
            status_code=400,
            error_code="TEST_001",
        )

        assert response["error"]["code"] == "TEST_001"

    def test_create_error_response_with_details(self) -> None:
        """Test error response with details"""
        from src.presentation.api.exceptions import create_error_response

        details = {"field": "username", "issue": "too short"}
        response = create_error_response(
            error_type="ValidationError",
            message="Validation failed",
            status_code=400,
            details=details,
        )

        assert response["error"]["details"] == details

    def test_create_error_response_with_request_id(self) -> None:
        """Test error response with request ID"""
        from src.presentation.api.exceptions import create_error_response

        response = create_error_response(
            error_type="TestError",
            message="Test message",
            status_code=400,
            request_id="req_123",
        )

        assert response["request_id"] == "req_123"


class TestValidationErrorHandler:
    """Test ValidationError handler"""

    @pytest.fixture
    def mock_request(self) -> Mock:
        """Create mock request"""
        request = Mock()
        request.url.path = "/api/test"
        return request

    @pytest.mark.asyncio
    async def test_validation_error_handler_returns_400(self, mock_request: Mock) -> None:
        """Test ValidationError handler returns 400"""
        from src.presentation.api.exceptions import validation_error_handler
        from src.application.use_cases import ValidationError

        exc = ValidationError("Invalid input")
        response = await validation_error_handler(mock_request, exc)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_validation_error_handler_response_structure(self, mock_request: Mock) -> None:
        """Test ValidationError handler response structure"""
        from src.presentation.api.exceptions import validation_error_handler
        from src.application.use_cases import ValidationError

        exc = ValidationError("Invalid input")
        response = await validation_error_handler(mock_request, exc)

        import json

        body = json.loads(response.body)
        assert "error" in body
        assert body["error"]["type"] == "ValidationError"
        assert "request_id" in body


class TestNotFoundErrorHandler:
    """Test NotFoundError handler"""

    @pytest.fixture
    def mock_request(self) -> Mock:
        """Create mock request"""
        request = Mock()
        request.url.path = "/api/test"
        return request

    @pytest.mark.asyncio
    async def test_not_found_error_handler_returns_404(self, mock_request: Mock) -> None:
        """Test NotFoundError handler returns 404"""
        from src.presentation.api.exceptions import not_found_error_handler
        from src.application.use_cases import NotFoundError

        exc = NotFoundError("Resource not found")
        response = await not_found_error_handler(mock_request, exc)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_not_found_error_handler_response_structure(self, mock_request: Mock) -> None:
        """Test NotFoundError handler response structure"""
        from src.presentation.api.exceptions import not_found_error_handler
        from src.application.use_cases import NotFoundError

        exc = NotFoundError("Resource not found")
        response = await not_found_error_handler(mock_request, exc)

        import json

        body = json.loads(response.body)
        assert "error" in body
        assert body["error"]["type"] == "NotFoundError"


class TestAlreadyExistsErrorHandler:
    """Test AlreadyExistsError handler"""

    @pytest.fixture
    def mock_request(self) -> Mock:
        """Create mock request"""
        request = Mock()
        request.url.path = "/api/test"
        return request

    @pytest.mark.asyncio
    async def test_already_exists_error_handler_returns_409(self, mock_request: Mock) -> None:
        """Test AlreadyExistsError handler returns 409"""
        from src.presentation.api.exceptions import already_exists_error_handler
        from src.application.use_cases import AlreadyExistsError

        exc = AlreadyExistsError("Resource already exists")
        response = await already_exists_error_handler(mock_request, exc)

        assert response.status_code == 409


class TestHTTPExceptionHandler:
    """Test HTTPException handler"""

    @pytest.fixture
    def mock_request(self) -> Mock:
        """Create mock request"""
        request = Mock()
        request.url.path = "/api/test"
        return request

    @pytest.mark.asyncio
    async def test_http_exception_handler(self, mock_request: Mock) -> None:
        """Test HTTPException handler"""
        from src.presentation.api.exceptions import http_exception_handler

        exc = HTTPException(status_code=403, detail="Forbidden")
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_http_exception_handler_response_structure(self, mock_request: Mock) -> None:
        """Test HTTPException handler response structure"""
        from src.presentation.api.exceptions import http_exception_handler

        exc = HTTPException(status_code=403, detail="Forbidden")
        response = await http_exception_handler(mock_request, exc)

        import json

        body = json.loads(response.body)
        assert "error" in body
        assert body["error"]["type"] == "HTTPException"
        assert body["error"]["message"] == "Forbidden"


class TestGeneralExceptionHandler:
    """Test general exception handler"""

    @pytest.fixture
    def mock_request(self) -> Mock:
        """Create mock request"""
        request = Mock()
        request.url.path = "/api/test"
        request.app.state.debug = False
        return request

    @pytest.mark.asyncio
    async def test_general_exception_handler_returns_500(self, mock_request: Mock) -> None:
        """Test general exception handler returns 500"""
        from src.presentation.api.exceptions import general_exception_handler

        exc = Exception("Unexpected error")
        response = await general_exception_handler(mock_request, exc)

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_general_exception_handler_hides_details(self, mock_request: Mock) -> None:
        """Test general exception handler hides details in production"""
        from src.presentation.api.exceptions import general_exception_handler

        mock_request.app.state.debug = False

        exc = Exception("Sensitive error message")
        response = await general_exception_handler(mock_request, exc)

        import json

        body = json.loads(response.body)
        # Should have generic message, not the sensitive one
        assert body["error"]["message"] != "Sensitive error message"
        assert "details" not in body["error"] or body["error"]["details"] is None

    @pytest.mark.asyncio
    async def test_general_exception_handler_shows_details_in_debug(self, mock_request: Mock) -> None:
        """Test general exception handler shows details in debug mode"""
        from src.presentation.api.exceptions import general_exception_handler

        mock_request.app.state.debug = True

        exc = Exception("Debug error message")
        response = await general_exception_handler(mock_request, exc)

        import json

        body = json.loads(response.body)
        # Should have details in debug mode
        assert "details" in body["error"]


class TestExceptionHandlerRegistration:
    """Test exception handler registration"""

    def test_register_exception_handlers_function_exists(self) -> None:
        """Test register_exception_handlers function exists"""
        from src.presentation.api.exceptions import register_exception_handlers

        assert register_exception_handlers is not None

    def test_register_exception_handlers(self) -> None:
        """Test registering exception handlers"""
        from src.presentation.api.exceptions import register_exception_handlers

        mock_app = Mock()
        mock_app.add_exception_handler = Mock()

        register_exception_handlers(mock_app)

        # Should have registered multiple handlers
        assert mock_app.add_exception_handler.call_count > 0
