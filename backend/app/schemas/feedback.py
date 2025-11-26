"""Pydantic schemas for feedback API endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    """Request schema for feedback submission."""

    session_id: str = Field(
        ...,
        description="Session ID of the chat conversation",
    )
    message_id: str | None = Field(
        default=None,
        description="Optional specific message ID for the feedback",
    )
    rating: Literal["helpful", "not_helpful"] = Field(
        ...,
        description="User's rating of the response",
    )
    comment: str | None = Field(
        default=None,
        description="Optional user comment about the response",
        max_length=1000,
    )
    feedback_type: Literal["accuracy", "relevance", "completeness", "other"] = Field(
        default="other",
        description="Category of the feedback",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "abc123",
                    "message_id": "msg_456",
                    "rating": "helpful",
                    "comment": "답변이 정확하고 도움이 되었습니다.",
                    "feedback_type": "accuracy",
                }
            ]
        }
    }


class FeedbackResponse(BaseModel):
    """Response schema for feedback submission."""

    success: bool = Field(
        ...,
        description="Whether the feedback was successfully recorded",
    )
    feedback_id: str = Field(
        ...,
        description="Unique identifier for the recorded feedback",
    )
    message: str = Field(
        default="피드백이 성공적으로 저장되었습니다.",
        description="Confirmation message",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when feedback was recorded",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "feedback_id": "fb_789",
                    "message": "피드백이 성공적으로 저장되었습니다.",
                    "created_at": "2024-01-15T10:30:00",
                }
            ]
        }
    }
