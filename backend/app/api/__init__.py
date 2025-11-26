"""API routers for the Knowledge Base AI Chatbot."""

from app.api.chat import router as chat_router
from app.api.feedback import router as feedback_router
from app.api.health import router as health_router
from app.api.stats import router as stats_router

__all__ = [
    "chat_router",
    "feedback_router",
    "health_router",
    "stats_router",
]
