"""Jira incremental synchronization module."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import settings
from app.core.services.jira_client import JiraClient
from app.models.document import Document
from app.models.sync import SyncHistory

logger = logging.getLogger(__name__)


def get_last_jira_sync_time(db: Session) -> Optional[datetime]:
    """Get the last successful Jira sync time.

    Args:
        db: Database session

    Returns:
        Last successful sync datetime or None if never synced
    """
    last_sync = (
        db.query(SyncHistory)
        .filter(
            SyncHistory.sync_type == "jira",
            SyncHistory.status == "success",
        )
        .order_by(desc(SyncHistory.completed_at))
        .first()
    )

    if last_sync and last_sync.completed_at:
        logger.info(f"Last successful Jira sync: {last_sync.completed_at}")
        return last_sync.completed_at

    logger.info("No previous successful Jira sync found")
    return None


def sync_jira_incremental(
    db: Session,
    project_key: Optional[str] = None,
) -> dict:
    """Perform incremental synchronization from Jira.

    This function fetches issues updated since the last successful sync
    and updates the database accordingly.

    Args:
        db: Database session
        project_key: Optional project key to filter issues

    Returns:
        Dictionary with sync statistics:
            - added: Number of new documents added
            - updated: Number of existing documents updated
            - deleted: Number of documents marked as deleted
            - errors: Number of errors encountered
    """
    stats = {"added": 0, "updated": 0, "deleted": 0, "errors": 0}

    # Check if Jira is configured
    if not settings.jira_url or not settings.jira_api_token:
        logger.warning("Jira is not configured. Skipping Jira sync.")
        return stats

    try:
        # Initialize Jira client
        jira_client = JiraClient()

        # Get last sync time
        last_sync = get_last_jira_sync_time(db)

        # Use provided project_key or default from settings
        target_project = project_key or settings.jira_project_key

        logger.info(f"Fetching Jira issues since {last_sync} for project {target_project}")

        # Fetch issues updated since last sync
        issues = jira_client.get_issues_updated_since(
            last_sync=last_sync,
            project_key=target_project,
        )

        logger.info(f"Found {len(issues)} issues to process")

        for issue in issues:
            try:
                issue_key = issue.get("key")
                doc_id = f"jira-{issue_key}"

                # Get detailed issue information
                issue_details = jira_client.get_issue_details(issue_key)

                # Build content from issue fields
                fields = issue_details.get("fields", {})
                summary = fields.get("summary", "")
                description = fields.get("description", "") or ""

                # Get comments
                comments = jira_client.get_comments(issue_key)
                comments_text = "\n\n".join([
                    f"Comment by {c.get('author', {}).get('displayName', 'Unknown')}: {c.get('body', '')}"
                    for c in comments
                ])

                content = f"{summary}\n\n{description}"
                if comments_text:
                    content += f"\n\n--- Comments ---\n{comments_text}"

                # Build URL
                issue_url = f"{settings.jira_url}/browse/{issue_key}"

                # Check if document already exists
                existing_doc = (
                    db.query(Document)
                    .filter(Document.doc_id == doc_id)
                    .first()
                )

                if existing_doc:
                    # Update existing document
                    existing_doc.title = summary
                    existing_doc.content = content
                    existing_doc.url = issue_url
                    existing_doc.author = fields.get("creator", {}).get("displayName")
                    existing_doc.updated_at = datetime.utcnow()
                    existing_doc.last_synced_at = datetime.utcnow()
                    existing_doc.deleted = False
                    existing_doc.metadata_ = {
                        "issue_type": fields.get("issuetype", {}).get("name"),
                        "status": fields.get("status", {}).get("name"),
                        "priority": fields.get("priority", {}).get("name"),
                        "project": fields.get("project", {}).get("key"),
                    }
                    stats["updated"] += 1
                    logger.debug(f"Updated issue: {issue_key}")
                else:
                    # Create new document
                    new_doc = Document(
                        doc_id=doc_id,
                        doc_type="jira",
                        title=summary,
                        url=issue_url,
                        content=content,
                        author=fields.get("creator", {}).get("displayName"),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        last_synced_at=datetime.utcnow(),
                        deleted=False,
                        metadata_={
                            "issue_type": fields.get("issuetype", {}).get("name"),
                            "status": fields.get("status", {}).get("name"),
                            "priority": fields.get("priority", {}).get("name"),
                            "project": fields.get("project", {}).get("key"),
                        },
                    )
                    db.add(new_doc)
                    stats["added"] += 1
                    logger.debug(f"Added new issue: {issue_key}")

            except Exception as e:
                logger.error(f"Error processing issue {issue.get('key', 'unknown')}: {e}")
                stats["errors"] += 1
                continue

        # Commit all changes
        db.commit()

        logger.info(
            f"Jira sync completed: "
            f"added={stats['added']}, updated={stats['updated']}, "
            f"deleted={stats['deleted']}, errors={stats['errors']}"
        )

    except Exception as e:
        logger.error(f"Jira sync failed: {e}")
        db.rollback()
        raise

    return stats
