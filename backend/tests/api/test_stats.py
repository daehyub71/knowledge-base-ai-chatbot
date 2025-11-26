"""Tests for statistics endpoint."""

import pytest


class TestStatsEndpoint:
    """Test cases for statistics endpoint."""

    def test_get_stats(self, client):
        """Test statistics endpoint returns expected structure."""
        response = client.get("/api/stats")
        assert response.status_code == 200

        data = response.json()

        # Check top-level fields
        assert "documents" in data
        assert "sync" in data
        assert "chat" in data
        assert "status" in data
        assert "updated_at" in data

    def test_stats_documents_structure(self, client):
        """Test documents statistics structure."""
        response = client.get("/api/stats")
        data = response.json()

        docs = data["documents"]
        assert "total_documents" in docs
        assert "jira_documents" in docs
        assert "confluence_documents" in docs
        assert "active_documents" in docs
        assert "deleted_documents" in docs
        assert "total_chunks" in docs
        assert "vector_count" in docs

        # Values should be non-negative integers
        assert docs["total_documents"] >= 0
        assert docs["jira_documents"] >= 0
        assert docs["confluence_documents"] >= 0

    def test_stats_sync_structure(self, client):
        """Test sync statistics structure."""
        response = client.get("/api/stats")
        data = response.json()

        sync = data["sync"]
        assert "last_sync_at" in sync
        assert "last_sync_status" in sync
        assert "documents_added" in sync
        assert "documents_updated" in sync
        assert "documents_deleted" in sync

    def test_stats_chat_structure(self, client):
        """Test chat statistics structure."""
        response = client.get("/api/stats")
        data = response.json()

        chat = data["chat"]
        assert "total_sessions" in chat
        assert "total_messages" in chat
        assert "rag_responses" in chat
        assert "fallback_responses" in chat
        assert "positive_feedback" in chat
        assert "negative_feedback" in chat

        # Values should be non-negative integers
        assert chat["total_sessions"] >= 0
        assert chat["total_messages"] >= 0
