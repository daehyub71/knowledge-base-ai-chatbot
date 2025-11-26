"""Dashboard API schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Dashboard statistics response."""
    total_documents: int = 0
    jira_count: int = 0
    confluence_count: int = 0
    sync_status: str = "healthy"  # healthy, error, syncing
    last_sync: Optional[str] = None
    next_sync: Optional[str] = None


class SyncHistoryItem(BaseModel):
    """Single sync history entry."""
    date: str
    documents: int


class SyncActivity(BaseModel):
    """Sync activity log entry."""
    id: str
    timestamp: str
    event_type: str
    status: str  # success, failed, in_progress
    description: str


class SyncHistoryResponse(BaseModel):
    """Sync history response for charts and tables."""
    chart_data: List[SyncHistoryItem]
    activities: List[SyncActivity]


class SyncTriggerRequest(BaseModel):
    """Manual sync trigger request."""
    source: Optional[str] = None  # jira, confluence, or None for all


class SyncTriggerResponse(BaseModel):
    """Manual sync trigger response."""
    success: bool
    message: str
    sync_id: Optional[str] = None
