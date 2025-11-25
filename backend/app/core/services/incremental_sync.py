"""Incremental synchronization service."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.services.data_collector import DataCollector
from app.models.sync import SyncHistory

logger = logging.getLogger(__name__)


class IncrementalSync:
    """Service for incremental data synchronization."""

    def __init__(self, db: Session):
        """Initialize incremental sync service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.collector = DataCollector(db)

    def get_last_sync_time(self, sync_type: str) -> Optional[datetime]:
        """Get the last successful sync time for a given source.

        Args:
            sync_type: Type of sync ('jira', 'confluence', or 'all')

        Returns:
            Last successful sync datetime or None if never synced
        """
        last_sync = (
            self.db.query(SyncHistory)
            .filter(
                SyncHistory.sync_type == sync_type,
                SyncHistory.status == "success",
            )
            .order_by(desc(SyncHistory.completed_at))
            .first()
        )

        if last_sync:
            logger.info(f"Last successful {sync_type} sync: {last_sync.completed_at}")
            return last_sync.completed_at

        logger.info(f"No previous successful {sync_type} sync found")
        return None

    def start_sync(self, sync_type: str) -> SyncHistory:
        """Start a new sync and record it in history.

        Args:
            sync_type: Type of sync ('jira', 'confluence', or 'all')

        Returns:
            SyncHistory record
        """
        sync_record = SyncHistory(
            sync_type=sync_type,
            status="running",
            started_at=datetime.utcnow(),
        )
        self.db.add(sync_record)
        self.db.commit()
        logger.info(f"Started {sync_type} sync (id: {sync_record.id})")
        return sync_record

    def complete_sync(
        self,
        sync_record: SyncHistory,
        stats: dict,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Complete a sync and update the record.

        Args:
            sync_record: The sync history record to update
            stats: Statistics dictionary with added, updated, deleted counts
            success: Whether the sync was successful
            error_message: Error message if failed
        """
        sync_record.status = "success" if success else "failed"
        sync_record.completed_at = datetime.utcnow()
        sync_record.documents_added = stats.get("added", 0)
        sync_record.documents_updated = stats.get("updated", 0)
        sync_record.documents_deleted = stats.get("deleted", 0)
        sync_record.error_message = error_message

        self.db.commit()
        logger.info(
            f"Completed {sync_record.sync_type} sync: "
            f"added={sync_record.documents_added}, "
            f"updated={sync_record.documents_updated}, "
            f"deleted={sync_record.documents_deleted}"
        )

    def fetch_incremental_jira(self, project_key: Optional[str] = None) -> dict:
        """Fetch incremental updates from Jira.

        Args:
            project_key: Optional project key to filter

        Returns:
            Statistics dictionary
        """
        last_sync = self.get_last_sync_time("jira")
        logger.info(f"Fetching Jira updates since {last_sync}")

        return self.collector.collect_jira_documents(
            last_sync=last_sync,
            project_key=project_key,
        )

    def fetch_incremental_confluence(self, space_key: Optional[str] = None) -> dict:
        """Fetch incremental updates from Confluence.

        Args:
            space_key: Optional space key to filter

        Returns:
            Statistics dictionary
        """
        last_sync = self.get_last_sync_time("confluence")
        logger.info(f"Fetching Confluence updates since {last_sync}")

        return self.collector.collect_confluence_documents(
            last_sync=last_sync,
            space_key=space_key,
        )

    def run_sync(
        self,
        sync_type: str,
        project_key: Optional[str] = None,
        space_key: Optional[str] = None,
    ) -> dict:
        """Run a complete incremental sync.

        Args:
            sync_type: 'jira', 'confluence', or 'all'
            project_key: Optional Jira project key
            space_key: Optional Confluence space key

        Returns:
            Combined statistics dictionary
        """
        sync_record = self.start_sync(sync_type)
        combined_stats = {"added": 0, "updated": 0, "deleted": 0, "errors": 0}

        try:
            if sync_type in ("jira", "all"):
                jira_stats = self.fetch_incremental_jira(project_key)
                for key in combined_stats:
                    combined_stats[key] += jira_stats.get(key, 0)

            if sync_type in ("confluence", "all"):
                confluence_stats = self.fetch_incremental_confluence(space_key)
                for key in combined_stats:
                    combined_stats[key] += confluence_stats.get(key, 0)

            self.complete_sync(sync_record, combined_stats, success=True)
            return combined_stats

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Sync failed: {error_msg}")
            self.complete_sync(sync_record, combined_stats, success=False, error_message=error_msg)
            raise
