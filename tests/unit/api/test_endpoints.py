"""
API Endpoint Tests

FastAPI 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from src.presentation.api.main import app


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Simulation Post-Processing API"
    assert data["version"] == "1.0.0"
    assert data["docs"] == "/docs"


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


def test_openapi_docs_available(client):
    """Test OpenAPI docs are available"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_available(client):
    """Test ReDoc is available"""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_openapi_json(client):
    """Test OpenAPI JSON schema"""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "Simulation Post-Processing API"


def test_cors_headers(client):
    """Test CORS headers are set"""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    # CORS middleware should add these headers
    assert "access-control-allow-origin" in response.headers


def test_api_version_in_prefix(client):
    """Test API version prefix"""
    # API routes should be under /api/v1
    response = client.get("/api/v1/simulations/")

    # Even if it fails (no implementation), it should reach the router
    # 404 or 405 is OK, 500 is not
    assert response.status_code in [200, 404, 405, 422]


def test_404_for_invalid_route(client):
    """Test 404 for non-existent routes"""
    response = client.get("/api/v1/invalid-route")

    assert response.status_code == 404


def test_content_type_json(client):
    """Test API returns JSON by default"""
    response = client.get("/health")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
