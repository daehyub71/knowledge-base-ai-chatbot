"""Statistics API endpoint for the Knowledge Base AI Chatbot."""

import logging
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.state import get_vector_db_service
from app.models.document import Document, DocumentChunk
from app.models.chat import ChatHistory
from app.models.feedback import Feedback
from app.models.sync import SyncHistory
from app.schemas.stats import (
    ChatStats,
    DocumentStats,
    StatsResponse,
    SyncStats,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["Statistics"])


def _get_document_stats(db: Session) -> DocumentStats:
    """Get document statistics from database."""
    try:
        # Total documents
        total_docs = db.query(func.count(Document.id)).scalar() or 0

        # Documents by type
        jira_docs = (
            db.query(func.count(Document.id))
            .filter(Document.doc_type == "jira")
            .scalar() or 0
        )
        confluence_docs = (
            db.query(func.count(Document.id))
            .filter(Document.doc_type == "confluence")
            .scalar() or 0
        )

        # Active vs deleted
        active_docs = (
            db.query(func.count(Document.id))
            .filter(Document.deleted == False)
            .scalar() or 0
        )
        deleted_docs = (
            db.query(func.count(Document.id))
            .filter(Document.deleted == True)
            .scalar() or 0
        )

        # Total chunks
        total_chunks = db.query(func.count(DocumentChunk.id)).scalar() or 0

        # Vector count from FAISS
        vector_db_service = get_vector_db_service()
        vector_count = (
            vector_db_service.index.ntotal
            if vector_db_service and vector_db_service.index
            else 0
        )

        return DocumentStats(
            total_documents=total_docs,
            jira_documents=jira_docs,
            confluence_documents=confluence_docs,
            active_documents=active_docs,
            deleted_documents=deleted_docs,
            total_chunks=total_chunks,
            vector_count=vector_count,
        )
    except Exception as e:
        logger.error(f"Failed to get document stats: {e}")
        return DocumentStats(
            total_documents=0,
            jira_documents=0,
            confluence_documents=0,
            active_documents=0,
            deleted_documents=0,
            total_chunks=0,
            vector_count=0,
        )


def _get_sync_stats(db: Session) -> SyncStats:
    """Get synchronization statistics from database."""
    try:
        # Get last successful sync
        last_sync = (
            db.query(SyncHistory)
            .filter(SyncHistory.status == "completed")
            .order_by(SyncHistory.completed_at.desc())
            .first()
        )

        if last_sync:
            return SyncStats(
                last_sync_at=last_sync.completed_at,
                last_sync_status=last_sync.status,
                documents_added=last_sync.documents_added or 0,
                documents_updated=last_sync.documents_updated or 0,
                documents_deleted=last_sync.documents_deleted or 0,
            )
        return SyncStats()
    except Exception as e:
        logger.error(f"Failed to get sync stats: {e}")
        return SyncStats()


def _get_chat_stats(db: Session) -> ChatStats:
    """Get chat interaction statistics from database."""
    try:
        # Total sessions (unique session_ids)
        total_sessions = (
            db.query(func.count(func.distinct(ChatHistory.session_id))).scalar() or 0
        )

        # Total messages
        total_messages = db.query(func.count(ChatHistory.id)).scalar() or 0

        # RAG vs Fallback responses
        rag_responses = (
            db.query(func.count(ChatHistory.id))
            .filter(ChatHistory.response_type == "rag")
            .scalar() or 0
        )
        fallback_responses = (
            db.query(func.count(ChatHistory.id))
            .filter(ChatHistory.response_type == "llm_fallback")
            .scalar() or 0
        )

        # Feedback counts
        positive_feedback = (
            db.query(func.count(Feedback.id))
            .filter(Feedback.rating > 0)
            .scalar() or 0
        )
        negative_feedback = (
            db.query(func.count(Feedback.id))
            .filter(Feedback.rating < 0)
            .scalar() or 0
        )

        return ChatStats(
            total_sessions=total_sessions,
            total_messages=total_messages,
            rag_responses=rag_responses,
            fallback_responses=fallback_responses,
            positive_feedback=positive_feedback,
            negative_feedback=negative_feedback,
        )
    except Exception as e:
        logger.error(f"Failed to get chat stats: {e}")
        return ChatStats()


@router.get("", response_model=StatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
) -> StatsResponse:
    """Get comprehensive statistics for the knowledge base system.

    This endpoint aggregates statistics from:
    1. Documents: total count, by type, active/deleted, chunks, vectors
    2. Sync: last sync info, documents added/updated/deleted
    3. Chat: sessions, messages, response types, feedback

    Returns:
        StatsResponse with all statistics
    """
    logger.info("Fetching system statistics...")

    try:
        document_stats = _get_document_stats(db)
        sync_stats = _get_sync_stats(db)
        chat_stats = _get_chat_stats(db)

        # Determine overall status
        vector_db_service = get_vector_db_service()
        if vector_db_service and vector_db_service.index:
            status = "healthy"
        else:
            status = "degraded"

        return StatsResponse(
            documents=document_stats,
            sync=sync_stats,
            chat=chat_stats,
            status=status,
            updated_at=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}",
        )
