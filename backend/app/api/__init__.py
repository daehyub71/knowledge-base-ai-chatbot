"""API routers for the Knowledge Base AI Chatbot."""

from app.api.chat import router as chat_router
from app.api.dashboard import router as dashboard_router
from app.api.feedback import router as feedback_router
from app.api.health import router as health_router
from app.api.settings import router as settings_router
from app.api.stats import router as stats_router

__all__ = [
    "chat_router",
    "dashboard_router",
    "feedback_router",
    "health_router",
    "settings_router",
    "stats_router",
]
