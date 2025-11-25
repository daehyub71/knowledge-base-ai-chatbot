"""Feedback model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.chat import ChatHistory


class Feedback(Base):
    """Feedback model for storing user feedback on chat responses."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_history_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_history.id"), unique=True, nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 (negative) or 5 (positive)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to chat history
    chat_history: Mapped["ChatHistory"] = relationship("ChatHistory", back_populates="feedback")

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, chat_history_id={self.chat_history_id}, rating={self.rating})>"
