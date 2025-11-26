"""Feedback API endpoint for the Knowledge Base AI Chatbot."""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.chat import ChatHistory
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackRequest, FeedbackResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    """Submit feedback for a chat response.

    This endpoint allows users to rate chat responses as helpful or not helpful,
    and optionally provide additional comments.

    Args:
        request: FeedbackRequest containing session_id, rating, and optional comment
        db: Database session

    Returns:
        FeedbackResponse confirming the feedback was recorded
    """
    logger.info(
        f"Received feedback: session={request.session_id}, "
        f"rating={request.rating}, type={request.feedback_type}"
    )

    try:
        # Find the most recent chat history for this session
        chat_history = (
            db.query(ChatHistory)
            .filter(ChatHistory.session_id == request.session_id)
            .order_by(ChatHistory.created_at.desc())
            .first()
        )

        if not chat_history:
            raise HTTPException(
                status_code=404,
                detail=f"세션 ID '{request.session_id}'에 대한 채팅 기록을 찾을 수 없습니다.",
            )

        # Convert rating to numeric value for storage
        rating_value = 1 if request.rating == "helpful" else -1

        # Create feedback record
        feedback_id = str(uuid.uuid4())
        feedback = Feedback(
            chat_history_id=chat_history.id,
            rating=rating_value,
            comment=request.comment,
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        logger.info(
            f"Feedback saved: id={feedback.id}, "
            f"chat_history_id={chat_history.id}, rating={rating_value}"
        )

        return FeedbackResponse(
            success=True,
            feedback_id=f"fb_{feedback.id}",
            message="피드백이 성공적으로 저장되었습니다.",
            created_at=feedback.created_at or datetime.now(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"피드백 저장 중 오류가 발생했습니다: {str(e)}",
        )
