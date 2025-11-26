"""FastAPI application entry point for Knowledge Base AI Chatbot."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.exceptions import KnowledgeBaseException
from app.core.services.vector_db_service import VectorDBService
from app.state import get_vector_db_service, set_vector_db_service
from app.api import chat_router, feedback_router, health_router, stats_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Knowledge Base AI Chatbot API...")

    try:
        # Load FAISS index
        service = VectorDBService()
        # Default FAISS index path
        faiss_path = Path(__file__).parent.parent / "data" / "vector_db" / "faiss.index"
        if faiss_path.exists() and service.load_index(faiss_path):
            logger.info(
                f"FAISS index loaded successfully: "
                f"{service.index.ntotal} vectors"
            )
            set_vector_db_service(service)
        else:
            logger.warning(
                f"FAISS index not found at {faiss_path}. "
                "Run 'python scripts/build_vector_db.py' first."
            )
            set_vector_db_service(service)
    except Exception as e:
        logger.error(f"Failed to load FAISS index: {e}")

    logger.info("API startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Knowledge Base AI Chatbot API...")

    # Cleanup resources
    set_vector_db_service(None)

    logger.info("API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Knowledge Base AI Chatbot API",
    description=(
        "Jira/Confluence 문서 기반 RAG(Retrieval-Augmented Generation) AI 챗봇 API. "
        "회사 내부 문서를 기반으로 질문에 답변하고, 관련 문서가 없을 경우 "
        "일반 LLM 지식으로 응답합니다."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(chat_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(stats_router, prefix="/api")


# Exception handlers
@app.exception_handler(KnowledgeBaseException)
async def knowledge_base_exception_handler(
    request: Request, exc: KnowledgeBaseException
) -> JSONResponse:
    """Handle custom Knowledge Base exceptions."""
    logger.error(f"KnowledgeBaseException: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "knowledge_base_error",
            "message": exc.message,
            "detail": str(exc),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "서버 내부 오류가 발생했습니다.",
            "detail": str(exc) if settings.debug else None,
        },
    )


@app.get("/")
async def root():
    """Root endpoint returning API info."""
    return {
        "name": "Knowledge Base AI Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check_simple():
    """Simple health check endpoint."""
    service = get_vector_db_service()
    vector_db_status = "loaded" if service and service.index else "not_loaded"
    vector_count = service.index.ntotal if service and service.index else 0

    return {
        "status": "healthy",
        "vector_db": {
            "status": vector_db_status,
            "vector_count": vector_count,
        },
    }
