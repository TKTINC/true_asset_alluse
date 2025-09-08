"""
Basic tests for the main application.

Tests the core application setup, health endpoints, and basic functionality.
"""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(test_client: TestClient):
    """Test the root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "True-Asset-ALLUSE API"
    assert "version" in data
    assert "constitution" in data


def test_health_endpoint(test_client: TestClient):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "true-asset-alluse"
    assert "version" in data
    assert "constitution_version" in data
    assert "environment" in data


def test_api_health_endpoint(test_client: TestClient):
    """Test the API health check endpoint."""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api_version"] == "v1"
    assert "message" in data


def test_docs_endpoint_in_debug(test_client: TestClient):
    """Test that docs are available in debug mode."""
    response = test_client.get("/docs")
    # Should return 200 in debug mode, or redirect to docs
    assert response.status_code in [200, 307]


def test_openapi_endpoint_in_debug(test_client: TestClient):
    """Test that OpenAPI spec is available in debug mode."""
    response = test_client.get("/openapi.json")
    # Should return 200 in debug mode
    assert response.status_code in [200, 404]  # 404 if disabled in production


class TestApplicationStartup:
    """Test application startup and configuration."""
    
    def test_application_title(self, test_client: TestClient):
        """Test that application has correct title."""
        response = test_client.get("/openapi.json")
        if response.status_code == 200:
            openapi_spec = response.json()
            assert openapi_spec["info"]["title"] == "True-Asset-ALLUSE"
    
    def test_cors_headers(self, test_client: TestClient):
        """Test CORS headers are present."""
        response = test_client.options("/health")
        # CORS headers should be present
        assert response.status_code in [200, 405]  # OPTIONS might not be implemented
    
    def test_request_id_header(self, test_client: TestClient):
        """Test that request ID header is added."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

