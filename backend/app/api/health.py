"""Health check API endpoint for the Knowledge Base AI Chatbot."""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.state import get_vector_db_service
from app.models.sync import SyncHistory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


class DatabaseHealth(BaseModel):
    """Database health status."""

    status: str = Field(..., description="Database connection status")
    message: str | None = Field(default=None, description="Status message or error")


class VectorDBHealth(BaseModel):
    """Vector database health status."""

    status: str = Field(..., description="FAISS index status")
    vector_count: int = Field(default=0, description="Number of vectors in index")


class SyncHealth(BaseModel):
    """Synchronization health status."""

    last_sync_at: datetime | None = Field(default=None, description="Last sync timestamp")
    last_sync_status: str | None = Field(default=None, description="Last sync status")
    source_type: str | None = Field(default=None, description="Last sync source type")


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""

    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    database: DatabaseHealth = Field(..., description="Database health")
    vector_db: VectorDBHealth = Field(..., description="Vector DB health")
    sync: SyncHealth = Field(..., description="Sync health")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "timestamp": "2024-01-15T10:30:00",
                    "database": {"status": "connected", "message": None},
                    "vector_db": {"status": "loaded", "vector_count": 500},
                    "sync": {
                        "last_sync_at": "2024-01-15T06:00:00",
                        "last_sync_status": "completed",
                        "source_type": "all",
                    },
                }
            ]
        }
    }


def _check_database(db: Session) -> DatabaseHealth:
    """Check database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return DatabaseHealth(status="connected", message=None)
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return DatabaseHealth(status="error", message=str(e))


def _check_vector_db() -> VectorDBHealth:
    """Check FAISS index status."""
    vector_db_service = get_vector_db_service()
    if vector_db_service and vector_db_service.index:
        return VectorDBHealth(
            status="loaded",
            vector_count=vector_db_service.index.ntotal,
        )
    return VectorDBHealth(status="not_loaded", vector_count=0)


def _check_sync(db: Session) -> SyncHealth:
    """Check last synchronization status."""
    try:
        last_sync = (
            db.query(SyncHistory)
            .order_by(SyncHistory.started_at.desc())
            .first()
        )
        if last_sync:
            return SyncHealth(
                last_sync_at=last_sync.completed_at or last_sync.started_at,
                last_sync_status=last_sync.status,
                source_type=last_sync.sync_type,
            )
        return SyncHealth()
    except Exception as e:
        logger.error(f"Sync health check failed: {e}")
        return SyncHealth()


@router.get("", response_model=HealthResponse)
async def health_check(
    db: Session = Depends(get_db),
) -> HealthResponse:
    """Check the health status of all system components.

    This endpoint checks:
    1. Database connectivity
    2. FAISS vector index status
    3. Last synchronization status

    Returns:
        HealthResponse with status of all components
    """
    logger.debug("Running health check...")

    # Check all components
    db_health = _check_database(db)
    vector_db_health = _check_vector_db()
    sync_health = _check_sync(db)

    # Determine overall status
    if db_health.status == "error":
        overall_status = "unhealthy"
    elif vector_db_health.status == "not_loaded":
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        database=db_health,
        vector_db=vector_db_health,
        sync=sync_health,
    )
