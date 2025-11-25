"""Data collection service for Jira and Confluence documents."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.services.confluence_client import ConfluenceClient
from app.core.services.jira_client import JiraClient
from app.models.document import Document

logger = logging.getLogger(__name__)


class DataCollector:
    """Service for collecting documents from Jira and Confluence."""

    def __init__(self, db: Session):
        """Initialize data collector with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def collect_jira_documents(
        self,
        last_sync: Optional[datetime] = None,
        project_key: Optional[str] = None,
    ) -> dict:
        """Collect documents from Jira.

        Args:
            last_sync: Only collect issues updated after this time
            project_key: Filter by specific project

        Returns:
            Statistics dictionary with added, updated, skipped counts
        """
        logger.info("Starting Jira document collection")
        stats = {"added": 0, "updated": 0, "skipped": 0, "errors": 0}

        try:
            client = JiraClient()

            # Fetch issues
            issues = client.get_issues_updated_since(
                last_sync=last_sync,
                project_key=project_key,
            )

            logger.info(f"Processing {len(issues)} Jira issues")

            for issue in issues:
                try:
                    doc_data = client.format_issue_as_document(issue)
                    result = self._upsert_document(doc_data)
                    stats[result] += 1
                except Exception as e:
                    logger.error(f"Error processing issue {issue.get('key', 'unknown')}: {e}")
                    stats["errors"] += 1

            self.db.commit()
            logger.info(f"Jira collection complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Jira collection failed: {e}")
            self.db.rollback()
            raise

    def collect_confluence_documents(
        self,
        last_sync: Optional[datetime] = None,
        space_key: Optional[str] = None,
    ) -> dict:
        """Collect documents from Confluence.

        Args:
            last_sync: Only collect pages updated after this time
            space_key: Filter by specific space

        Returns:
            Statistics dictionary with added, updated, skipped counts
        """
        logger.info("Starting Confluence document collection")
        stats = {"added": 0, "updated": 0, "skipped": 0, "errors": 0}

        try:
            client = ConfluenceClient()

            # Fetch pages
            pages = client.get_pages_updated_since(
                last_sync=last_sync,
                space_key=space_key,
            )

            logger.info(f"Processing {len(pages)} Confluence pages")

            for page in pages:
                try:
                    doc_data = client.format_page_as_document(page)
                    result = self._upsert_document(doc_data)
                    stats[result] += 1
                except Exception as e:
                    logger.error(f"Error processing page: {e}")
                    stats["errors"] += 1

            self.db.commit()
            logger.info(f"Confluence collection complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Confluence collection failed: {e}")
            self.db.rollback()
            raise

    def _upsert_document(self, doc_data: dict) -> str:
        """Insert or update a document in the database.

        Args:
            doc_data: Document data dictionary

        Returns:
            "added", "updated", or "skipped"
        """
        doc_id = doc_data["doc_id"]

        # Check if document exists
        existing = self.db.query(Document).filter(Document.doc_id == doc_id).first()

        if existing:
            # Check if content has changed
            if existing.content == doc_data["content"] and not existing.deleted:
                logger.debug(f"Skipping unchanged document: {doc_id}")
                return "skipped"

            # Update existing document
            existing.title = doc_data["title"]
            existing.url = doc_data["url"]
            existing.content = doc_data["content"]
            existing.author = doc_data["author"]
            existing.updated_at = self._parse_datetime(doc_data.get("updated_at"))
            existing.last_synced_at = datetime.utcnow()
            existing.deleted = False
            existing.metadata_ = doc_data.get("metadata", {})

            logger.debug(f"Updated document: {doc_id}")
            return "updated"

        else:
            # Create new document
            new_doc = Document(
                doc_id=doc_data["doc_id"],
                doc_type=doc_data["doc_type"],
                title=doc_data["title"],
                url=doc_data.get("url"),
                content=doc_data["content"],
                author=doc_data.get("author"),
                created_at=self._parse_datetime(doc_data.get("created_at")) or datetime.utcnow(),
                updated_at=self._parse_datetime(doc_data.get("updated_at")) or datetime.utcnow(),
                last_synced_at=datetime.utcnow(),
                deleted=False,
                metadata_=doc_data.get("metadata", {}),
            )
            self.db.add(new_doc)
            logger.debug(f"Added new document: {doc_id}")
            return "added"

    @staticmethod
    def _parse_datetime(dt_string: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from Jira/Confluence API.

        Args:
            dt_string: ISO format datetime string

        Returns:
            Parsed datetime or None
        """
        if not dt_string:
            return None

        try:
            # Handle ISO format with timezone
            if "T" in dt_string:
                # Remove milliseconds and timezone for parsing
                dt_string = dt_string.split(".")[0]
                if "+" in dt_string:
                    dt_string = dt_string.split("+")[0]
                return datetime.fromisoformat(dt_string)
            return datetime.fromisoformat(dt_string)
        except (ValueError, TypeError):
            return None
