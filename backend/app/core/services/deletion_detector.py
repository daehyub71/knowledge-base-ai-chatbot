"""Deletion detection service for identifying removed documents."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.services.confluence_client import ConfluenceClient
from app.core.services.jira_client import JiraClient
from app.models.document import Document

logger = logging.getLogger(__name__)


class DeletionDetector:
    """Service for detecting deleted documents."""

    def __init__(self, db: Session):
        """Initialize deletion detector.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_stored_doc_ids(self, doc_type: str) -> set[str]:
        """Get all stored document IDs for a given type.

        Args:
            doc_type: 'jira' or 'confluence'

        Returns:
            Set of document IDs
        """
        docs = (
            self.db.query(Document.doc_id)
            .filter(
                Document.doc_type == doc_type,
                Document.deleted == False,  # noqa: E712
            )
            .all()
        )
        return {doc.doc_id for doc in docs}

    def get_current_jira_doc_ids(self, project_key: Optional[str] = None) -> set[str]:
        """Get all current document IDs from Jira.

        Args:
            project_key: Optional project key to filter

        Returns:
            Set of document IDs
        """
        try:
            client = JiraClient()
            issues = client.get_issues_updated_since(project_key=project_key)

            doc_ids = set()
            for issue in issues:
                issue_key = issue.get("key", "")
                if issue_key:
                    doc_ids.add(f"jira-{issue_key}")

            logger.info(f"Found {len(doc_ids)} current Jira documents")
            return doc_ids

        except Exception as e:
            logger.error(f"Failed to get current Jira doc IDs: {e}")
            raise

    def get_current_confluence_doc_ids(self, space_key: Optional[str] = None) -> set[str]:
        """Get all current document IDs from Confluence.

        Args:
            space_key: Optional space key to filter

        Returns:
            Set of document IDs
        """
        try:
            client = ConfluenceClient()
            pages = client.get_pages_updated_since(space_key=space_key)

            doc_ids = set()
            for page in pages:
                # Handle both CQL result format and direct page format
                if "content" in page:
                    page_id = page.get("content", {}).get("id", "")
                else:
                    page_id = page.get("id", "")

                if page_id:
                    doc_ids.add(f"confluence-{page_id}")

            logger.info(f"Found {len(doc_ids)} current Confluence documents")
            return doc_ids

        except Exception as e:
            logger.error(f"Failed to get current Confluence doc IDs: {e}")
            raise

    def detect_deleted_documents(
        self,
        doc_type: str,
        current_doc_ids: set[str],
    ) -> int:
        """Detect and mark deleted documents.

        Args:
            doc_type: 'jira' or 'confluence'
            current_doc_ids: Set of document IDs currently in the source

        Returns:
            Number of documents marked as deleted
        """
        stored_doc_ids = self.get_stored_doc_ids(doc_type)

        # Find documents that exist in DB but not in source
        deleted_doc_ids = stored_doc_ids - current_doc_ids

        if not deleted_doc_ids:
            logger.info(f"No deleted {doc_type} documents detected")
            return 0

        logger.info(f"Detected {len(deleted_doc_ids)} deleted {doc_type} documents")

        # Mark documents as deleted
        deleted_count = (
            self.db.query(Document)
            .filter(Document.doc_id.in_(deleted_doc_ids))
            .update(
                {
                    Document.deleted: True,
                    Document.last_synced_at: datetime.utcnow(),
                },
                synchronize_session=False,
            )
        )

        self.db.commit()
        logger.info(f"Marked {deleted_count} documents as deleted")
        return deleted_count

    def detect_all_deleted(
        self,
        project_key: Optional[str] = None,
        space_key: Optional[str] = None,
    ) -> dict:
        """Detect deleted documents from all sources.

        Args:
            project_key: Optional Jira project key
            space_key: Optional Confluence space key

        Returns:
            Statistics dictionary with deleted counts per source
        """
        stats = {"jira": 0, "confluence": 0}

        try:
            # Detect deleted Jira documents
            jira_current = self.get_current_jira_doc_ids(project_key)
            stats["jira"] = self.detect_deleted_documents("jira", jira_current)
        except Exception as e:
            logger.error(f"Jira deletion detection failed: {e}")

        try:
            # Detect deleted Confluence documents
            confluence_current = self.get_current_confluence_doc_ids(space_key)
            stats["confluence"] = self.detect_deleted_documents("confluence", confluence_current)
        except Exception as e:
            logger.error(f"Confluence deletion detection failed: {e}")

        total_deleted = stats["jira"] + stats["confluence"]
        logger.info(f"Total deleted documents detected: {total_deleted}")
        return stats
