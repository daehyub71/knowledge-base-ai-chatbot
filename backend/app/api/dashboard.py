"""Dashboard API endpoints."""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.models.sync import SyncHistory
from app.schemas.dashboard import (
    DashboardStats,
    SyncHistoryItem,
    SyncActivity,
    SyncHistoryResponse,
    SyncTriggerRequest,
    SyncTriggerResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)) -> DashboardStats:
    """Get dashboard statistics.

    Returns aggregated stats for the dashboard including:
    - Total documents count
    - Jira and Confluence document counts
    - Sync status
    - Last and next sync times
    """
    try:
        # Get document counts
        total_docs = db.query(func.count(Document.id)).filter(Document.deleted == False).scalar() or 0
        jira_count = db.query(func.count(Document.id)).filter(
            Document.doc_type == "jira",
            Document.deleted == False
        ).scalar() or 0
        confluence_count = db.query(func.count(Document.id)).filter(
            Document.doc_type == "confluence",
            Document.deleted == False
        ).scalar() or 0

        # Get last sync
        last_sync = db.query(SyncHistory).order_by(SyncHistory.completed_at.desc()).first()
        last_sync_str = last_sync.completed_at.isoformat() if last_sync and last_sync.completed_at else None

        # Determine sync status
        sync_status = "healthy"
        if last_sync and last_sync.status == "failed":
            sync_status = "error"
        elif last_sync and last_sync.status == "running":
            sync_status = "syncing"

        # Calculate next sync (assume 12 hour interval)
        next_sync_str = None
        if last_sync and last_sync.completed_at:
            next_sync = last_sync.completed_at + timedelta(hours=12)
            next_sync_str = next_sync.isoformat()

        return DashboardStats(
            total_documents=total_docs,
            jira_count=jira_count,
            confluence_count=confluence_count,
            sync_status=sync_status,
            last_sync=last_sync_str,
            next_sync=next_sync_str,
        )

    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-history", response_model=SyncHistoryResponse)
async def get_sync_history(db: Session = Depends(get_db)) -> SyncHistoryResponse:
    """Get sync history for charts and activity table.

    Returns:
    - chart_data: Last 7 days of sync data for the chart
    - activities: Recent sync activities for the table
    """
    try:
        # Generate chart data (last 7 days)
        chart_data: List[SyncHistoryItem] = []
        today = datetime.now().date()

        for i in range(6, -1, -1):
            date = today - timedelta(days=i)

            # Count documents synced on this day
            docs_count = db.query(func.count(Document.id)).filter(
                func.date(Document.updated_at) == date
            ).scalar() or 0

            chart_data.append(SyncHistoryItem(
                date=date.strftime("%b %d"),
                documents=docs_count,
            ))

        # Get recent sync activities
        sync_records = db.query(SyncHistory).order_by(
            SyncHistory.started_at.desc()
        ).limit(10).all()

        activities: List[SyncActivity] = []
        for record in sync_records:
            status = "success" if record.status == "completed" else (
                "in_progress" if record.status == "running" else "failed"
            )

            docs_affected = (record.documents_added or 0) + (record.documents_updated or 0)
            source_name = record.sync_type if record.sync_type in ["jira", "confluence"] else "all sources"
            description = f"Synced {docs_affected} documents from {source_name}"

            if record.status == "failed" and record.error_message:
                description = record.error_message[:100]

            activities.append(SyncActivity(
                id=str(record.id),
                timestamp=record.started_at.isoformat() if record.started_at else "",
                event_type=record.sync_type or "Full Sync",
                status=status,
                description=description,
            ))

        return SyncHistoryResponse(
            chart_data=chart_data,
            activities=activities,
        )

    except Exception as e:
        logger.error(f"Failed to get sync history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _run_sync_task(sync_id: str, source: str | None):
    """Background task to run sync (placeholder)."""
    logger.info(f"Running sync task {sync_id} for source: {source or 'all'}")
    # TODO: Implement actual sync logic
    # This would call the batch sync process


@router.post("/sync", response_model=SyncTriggerResponse)
async def trigger_sync(
    request: SyncTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> SyncTriggerResponse:
    """Trigger a manual sync.

    Starts a background sync task for the specified source or all sources.
    """
    try:
        sync_id = str(uuid.uuid4())

        # Create sync history record
        sync_record = SyncHistory(
            sync_type=request.source or "all",
            status="running",
            started_at=datetime.now(),
        )
        db.add(sync_record)
        db.commit()

        # Add background task
        background_tasks.add_task(_run_sync_task, sync_id, request.source)

        return SyncTriggerResponse(
            success=True,
            message=f"Sync started for {request.source or 'all sources'}",
            sync_id=sync_id,
        )

    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))
