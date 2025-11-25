"""ChatHistory model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ChatHistory(Base):
    """ChatHistory model for storing chat interactions."""

    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    response_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'rag' or 'llm_fallback'
    source_documents: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to feedback
    feedback: Mapped[Optional["Feedback"]] = relationship(
        "Feedback", back_populates="chat_history", uselist=False
    )

    def __repr__(self) -> str:
        return f"<ChatHistory(id={self.id}, session_id={self.session_id}, response_type={self.response_type})>"


# Import Feedback for type hints
from app.models.feedback import Feedback  # noqa: E402, F401
