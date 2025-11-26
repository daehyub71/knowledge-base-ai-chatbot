"""Deleted document detection module.

This module detects documents that have been deleted from Jira/Confluence
and marks them as deleted in the database.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Set

from sqlalchemy.orm import Session

from app.config import settings
from app.core.services.jira_client import JiraClient
from app.core.services.confluence_client import ConfluenceClient
from app.models.document import Document

logger = logging.getLogger(__name__)


def get_jira_document_ids(project_key: Optional[str] = None) -> Set[str]:
    """Get all current document IDs from Jira.

    Args:
        project_key: Optional project key to filter

    Returns:
        Set of document IDs in format 'jira-{issue_key}'
    """
    if not settings.jira_url or not settings.jira_api_token:
        logger.warning("Jira is not configured. Skipping Jira deletion detection.")
        return set()

    try:
        jira_client = JiraClient()
        target_project = project_key or settings.jira_project_key

        # Get all issues from Jira (no date filter)
        issues = jira_client.get_issues_updated_since(
            last_sync=None,
            project_key=target_project,
        )

        doc_ids = {f"jira-{issue.get('key')}" for issue in issues if issue.get("key")}
        logger.info(f"Found {len(doc_ids)} Jira issues in project {target_project}")
        return doc_ids

    except Exception as e:
        logger.error(f"Failed to get Jira document IDs: {e}")
        return set()


def get_confluence_document_ids(space_key: Optional[str] = None) -> Set[str]:
    """Get all current document IDs from Confluence.

    Args:
        space_key: Optional space key to filter

    Returns:
        Set of document IDs in format 'confluence-{page_id}'
    """
    if not settings.confluence_url:
        logger.warning("Confluence is not configured. Skipping Confluence deletion detection.")
        return set()

    try:
        confluence_client = ConfluenceClient()
        target_space = space_key or settings.confluence_space_key

        # Get all pages from Confluence (no date filter)
        pages = confluence_client.get_pages_updated_since(
            last_sync=None,
            space_key=target_space,
        )

        # CQL search returns results with 'content' wrapper containing the page ID
        doc_ids = set()
        for page in pages:
            # Handle CQL result format where ID is in content.id
            if "content" in page:
                page_id = page.get("content", {}).get("id")
            else:
                page_id = page.get("id")

            if page_id:
                doc_ids.add(f"confluence-{page_id}")

        logger.info(f"Found {len(doc_ids)} Confluence pages in space {target_space}")
        return doc_ids

    except Exception as e:
        logger.error(f"Failed to get Confluence document IDs: {e}")
        return set()


def get_db_document_ids(db: Session, doc_type: str) -> Set[str]:
    """Get all non-deleted document IDs from database.

    Args:
        db: Database session
        doc_type: Document type ('jira' or 'confluence')

    Returns:
        Set of document IDs
    """
    docs = (
        db.query(Document.doc_id)
        .filter(
            Document.doc_type == doc_type,
            Document.deleted == False,
        )
        .all()
    )
    return {doc.doc_id for doc in docs}


def detect_and_mark_deleted(
    db: Session,
    source: str,
    project_key: Optional[str] = None,
    space_key: Optional[str] = None,
) -> dict:
    """Detect and mark deleted documents.

    This function compares document IDs in the database with current IDs
    from Jira/Confluence and marks missing documents as deleted.

    Args:
        db: Database session
        source: Source type ('jira', 'confluence', or 'all')
        project_key: Optional Jira project key
        space_key: Optional Confluence space key

    Returns:
        Dictionary with deletion statistics:
            - jira_deleted: Number of Jira documents marked as deleted
            - confluence_deleted: Number of Confluence documents marked as deleted
            - total_deleted: Total documents marked as deleted
    """
    stats = {
        "jira_deleted": 0,
        "confluence_deleted": 0,
        "total_deleted": 0,
    }

    try:
        # Process Jira deletions
        if source in ("jira", "all"):
            current_jira_ids = get_jira_document_ids(project_key)
            db_jira_ids = get_db_document_ids(db, "jira")

            # Find documents in DB that are not in Jira anymore
            deleted_jira_ids = db_jira_ids - current_jira_ids

            if deleted_jira_ids:
                logger.info(f"Marking {len(deleted_jira_ids)} Jira documents as deleted")

                db.query(Document).filter(
                    Document.doc_id.in_(deleted_jira_ids)
                ).update(
                    {
                        Document.deleted: True,
                        Document.updated_at: datetime.now(timezone.utc),
                    },
                    synchronize_session=False,
                )

                stats["jira_deleted"] = len(deleted_jira_ids)
                logger.debug(f"Deleted Jira docs: {deleted_jira_ids}")

        # Process Confluence deletions
        if source in ("confluence", "all"):
            current_confluence_ids = get_confluence_document_ids(space_key)
            db_confluence_ids = get_db_document_ids(db, "confluence")

            # Find documents in DB that are not in Confluence anymore
            deleted_confluence_ids = db_confluence_ids - current_confluence_ids

            if deleted_confluence_ids:
                logger.info(f"Marking {len(deleted_confluence_ids)} Confluence documents as deleted")

                db.query(Document).filter(
                    Document.doc_id.in_(deleted_confluence_ids)
                ).update(
                    {
                        Document.deleted: True,
                        Document.updated_at: datetime.now(timezone.utc),
                    },
                    synchronize_session=False,
                )

                stats["confluence_deleted"] = len(deleted_confluence_ids)
                logger.debug(f"Deleted Confluence docs: {deleted_confluence_ids}")

        # Commit changes
        db.commit()

        stats["total_deleted"] = stats["jira_deleted"] + stats["confluence_deleted"]

        logger.info(
            f"Deletion detection completed: "
            f"jira={stats['jira_deleted']}, "
            f"confluence={stats['confluence_deleted']}, "
            f"total={stats['total_deleted']}"
        )

    except Exception as e:
        logger.error(f"Deletion detection failed: {e}")
        db.rollback()
        raise

    return stats
