"""Tests for health and info endpoints."""

import pytest
from fastapi import status


class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "operational"

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_openapi_docs(self, client):
        """Test that OpenAPI documentation is accessible."""
        response = client.get("/docs")

        assert response.status_code == status.HTTP_200_OK

    def test_openapi_json(self, client):
        """Test that OpenAPI JSON spec is accessible."""
        response = client.get("/openapi.json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
