"""Tests for health check endpoints."""

import pytest


class TestHealthEndpoints:
    """Test cases for health check endpoints."""

    def test_simple_health_check(self, client):
        """Test simple health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "vector_db" in data
        assert data["status"] == "healthy"

    def test_detailed_health_check(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "vector_db" in data
        assert "sync" in data
        assert "timestamp" in data

        # Check database health
        assert "status" in data["database"]

        # Check vector_db health
        assert "status" in data["vector_db"]
        assert "vector_count" in data["vector_db"]

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Knowledge Base AI Chatbot API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert data["docs"] == "/docs"
