"""Tests for chat endpoint."""

import pytest
from unittest.mock import patch, MagicMock


class TestChatEndpoint:
    """Test cases for chat endpoint."""

    def test_chat_request_validation(self, client):
        """Test chat request validation."""
        # Empty query should fail
        response = client.post("/api/chat", json={"query": ""})
        assert response.status_code == 422

        # Missing query should fail
        response = client.post("/api/chat", json={})
        assert response.status_code == 422

    def test_chat_request_with_valid_query(self, client):
        """Test chat with valid query (mocked workflow)."""
        mock_result = {
            "response": "테스트 응답입니다.",
            "response_type": "rag",
            "sources": [
                {
                    "doc_id": "confluence-123",
                    "doc_type": "confluence",
                    "title": "테스트 문서",
                    "url": "http://example.com/123",
                    "score": 0.85,
                    "content": "테스트 내용",
                }
            ],
            "relevance_decision": "relevant",
            "analyzed_query": {
                "intent": "information_seeking",
                "keywords": ["테스트"],
                "filters": {},
            },
            "error": None,
        }

        with patch("app.api.chat.run_workflow", return_value=mock_result):
            response = client.post(
                "/api/chat",
                json={"query": "테스트 쿼리입니다"}
            )

            assert response.status_code == 200
            data = response.json()

            assert "response" in data
            assert "response_type" in data
            assert "sources" in data
            assert "session_id" in data

            assert data["response_type"] == "rag"
            assert len(data["sources"]) == 1

    def test_chat_response_structure(self, client):
        """Test chat response has correct structure."""
        mock_result = {
            "response": "응답",
            "response_type": "llm_fallback",
            "sources": [],
            "relevance_decision": "irrelevant",
            "analyzed_query": None,
            "error": None,
        }

        with patch("app.api.chat.run_workflow", return_value=mock_result):
            response = client.post(
                "/api/chat",
                json={"query": "일반적인 질문입니다"}
            )

            assert response.status_code == 200
            data = response.json()

            # Check all expected fields exist
            assert "response" in data
            assert "response_type" in data
            assert "sources" in data
            assert "relevance_decision" in data
            assert "session_id" in data

    def test_chat_with_session_id(self, client):
        """Test chat preserves provided session_id."""
        mock_result = {
            "response": "응답",
            "response_type": "rag",
            "sources": [],
            "relevance_decision": "relevant",
            "analyzed_query": None,
            "error": None,
        }

        with patch("app.api.chat.run_workflow", return_value=mock_result):
            response = client.post(
                "/api/chat",
                json={
                    "query": "테스트",
                    "session_id": "my-custom-session-id"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "my-custom-session-id"

    def test_chat_generates_session_id_if_not_provided(self, client):
        """Test chat generates session_id if not provided."""
        mock_result = {
            "response": "응답",
            "response_type": "rag",
            "sources": [],
            "relevance_decision": "relevant",
            "analyzed_query": None,
            "error": None,
        }

        with patch("app.api.chat.run_workflow", return_value=mock_result):
            response = client.post(
                "/api/chat",
                json={"query": "테스트"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] is not None
            # Should be a valid UUID format
            assert len(data["session_id"]) == 36

    def test_chat_query_max_length(self, client):
        """Test chat query maximum length validation."""
        # Query exceeding max length (2000 chars)
        long_query = "a" * 2001
        response = client.post("/api/chat", json={"query": long_query})
        assert response.status_code == 422
