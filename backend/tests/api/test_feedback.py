"""Tests for feedback endpoint."""

import pytest
from tests.conftest import TestChatHistory


class TestFeedbackEndpoint:
    """Test cases for feedback endpoint."""

    def test_feedback_without_session(self, client, sample_feedback_request):
        """Test feedback submission without existing chat session returns 404."""
        response = client.post("/api/feedback", json=sample_feedback_request)
        # Should return 404 because no chat history exists for this session
        assert response.status_code == 404

    def test_feedback_with_valid_session(self, client, db_session):
        """Test feedback submission with valid chat session."""
        # First, create a chat history record using test model
        chat_history = TestChatHistory(
            session_id="valid-session-123",
            user_query="테스트 쿼리",
            response="테스트 응답",
            response_type="rag",
        )
        db_session.add(chat_history)
        db_session.commit()

        # Now submit feedback
        feedback_data = {
            "session_id": "valid-session-123",
            "rating": "helpful",
            "comment": "좋은 답변이었습니다.",
            "feedback_type": "accuracy",
        }
        response = client.post("/api/feedback", json=feedback_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "feedback_id" in data
        assert data["message"] == "피드백이 성공적으로 저장되었습니다."

    def test_feedback_not_helpful(self, client, db_session):
        """Test feedback submission with not_helpful rating."""
        # Create chat history using test model
        chat_history = TestChatHistory(
            session_id="session-456",
            user_query="질문",
            response="응답",
            response_type="llm_fallback",
        )
        db_session.add(chat_history)
        db_session.commit()

        feedback_data = {
            "session_id": "session-456",
            "rating": "not_helpful",
            "comment": "관련 없는 답변이었습니다.",
            "feedback_type": "relevance",
        }
        response = client.post("/api/feedback", json=feedback_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_feedback_invalid_rating(self, client):
        """Test feedback with invalid rating value."""
        feedback_data = {
            "session_id": "test-session",
            "rating": "invalid_rating",  # Invalid rating
            "comment": "테스트",
        }
        response = client.post("/api/feedback", json=feedback_data)
        # Should fail validation
        assert response.status_code == 422

    def test_feedback_missing_required_fields(self, client):
        """Test feedback with missing required fields."""
        # Missing session_id and rating
        response = client.post("/api/feedback", json={})
        assert response.status_code == 422

        # Missing rating
        response = client.post("/api/feedback", json={"session_id": "test"})
        assert response.status_code == 422
