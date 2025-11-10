"""
Tests for Security Headers Middleware

Tests SecurityHeadersMiddleware that adds security headers to responses.
"""

from unittest.mock import Mock, AsyncMock
import pytest
from starlette.requests import Request
from starlette.responses import Response


class TestSecurityHeadersMiddleware:
    """Test SecurityHeadersMiddleware class"""

    @pytest.fixture
    def middleware(self):
        """Create SecurityHeadersMiddleware instance"""
        from src.presentation.api.middleware.security import SecurityHeadersMiddleware

        # Mock app
        mock_app = Mock()
        return SecurityHeadersMiddleware(mock_app)

    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        request = Mock(spec=Request)
        return request

    @pytest.mark.asyncio
    async def test_middleware_adds_security_headers(self, middleware, mock_request):
        """Test middleware adds security headers to response"""
        # Mock call_next to return a response
        async def mock_call_next(request):
            return Response(content="test", status_code=200)

        response = await middleware.dispatch(mock_request, mock_call_next)

        # Check security headers are added
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    @pytest.mark.asyncio
    async def test_middleware_adds_hsts_header(self, middleware, mock_request):
        """Test middleware adds HSTS header"""
        async def mock_call_next(request):
            return Response(content="test", status_code=200)

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]

    @pytest.mark.asyncio
    async def test_middleware_adds_csp_header(self, middleware, mock_request):
        """Test middleware adds Content-Security-Policy header"""
        async def mock_call_next(request):
            return Response(content="test", status_code=200)

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert "Content-Security-Policy" in response.headers
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]

    @pytest.mark.asyncio
    async def test_middleware_adds_referrer_policy(self, middleware, mock_request):
        """Test middleware adds Referrer-Policy header"""
        async def mock_call_next(request):
            return Response(content="test", status_code=200)

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_middleware_removes_server_header(self, middleware, mock_request):
        """Test middleware removes Server header"""
        async def mock_call_next(request):
            response = Response(content="test", status_code=200)
            response.headers["Server"] = "Uvicorn"
            return response

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert "Server" not in response.headers

    @pytest.mark.asyncio
    async def test_middleware_removes_powered_by_header(self, middleware, mock_request):
        """Test middleware removes X-Powered-By header"""
        async def mock_call_next(request):
            response = Response(content="test", status_code=200)
            response.headers["X-Powered-By"] = "FastAPI"
            return response

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert "X-Powered-By" not in response.headers

    @pytest.mark.asyncio
    async def test_middleware_preserves_response_content(self, middleware, mock_request):
        """Test middleware preserves response content"""
        test_content = b"Hello, World!"

        async def mock_call_next(request):
            return Response(content=test_content, status_code=200)

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.body == test_content

    @pytest.mark.asyncio
    async def test_middleware_preserves_status_code(self, middleware, mock_request):
        """Test middleware preserves status code"""
        async def mock_call_next(request):
            return Response(content="test", status_code=201)

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_middleware_works_with_error_responses(self, middleware, mock_request):
        """Test middleware works with error responses"""
        async def mock_call_next(request):
            return Response(content="Error", status_code=500)

        response = await middleware.dispatch(mock_request, mock_call_next)

        # Security headers should still be added
        assert "X-Content-Type-Options" in response.headers
        assert response.status_code == 500
