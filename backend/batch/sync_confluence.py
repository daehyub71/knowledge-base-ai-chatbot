"""Confluence incremental synchronization module."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import settings
from app.core.services.confluence_client import ConfluenceClient
from app.models.document import Document
from app.models.sync import SyncHistory

logger = logging.getLogger(__name__)


def get_last_confluence_sync_time(db: Session) -> Optional[datetime]:
    """Get the last successful Confluence sync time.

    Args:
        db: Database session

    Returns:
        Last successful sync datetime or None if never synced
    """
    last_sync = (
        db.query(SyncHistory)
        .filter(
            SyncHistory.sync_type == "confluence",
            SyncHistory.status == "success",
        )
        .order_by(desc(SyncHistory.completed_at))
        .first()
    )

    if last_sync and last_sync.completed_at:
        logger.info(f"Last successful Confluence sync: {last_sync.completed_at}")
        return last_sync.completed_at

    logger.info("No previous successful Confluence sync found")
    return None


def sync_confluence_incremental(
    db: Session,
    space_key: Optional[str] = None,
) -> dict:
    """Perform incremental synchronization from Confluence.

    This function fetches pages updated since the last successful sync
    and updates the database accordingly.

    Args:
        db: Database session
        space_key: Optional space key to filter pages

    Returns:
        Dictionary with sync statistics:
            - added: Number of new documents added
            - updated: Number of existing documents updated
            - deleted: Number of documents marked as deleted
            - errors: Number of errors encountered
    """
    stats = {"added": 0, "updated": 0, "deleted": 0, "errors": 0}

    # Check if Confluence is configured
    if not settings.confluence_url:
        logger.warning("Confluence is not configured. Skipping Confluence sync.")
        return stats

    try:
        # Initialize Confluence client
        confluence_client = ConfluenceClient()

        # Get last sync time
        last_sync = get_last_confluence_sync_time(db)

        # Use provided space_key or default from settings
        target_space = space_key or settings.confluence_space_key

        logger.info(f"Fetching Confluence pages since {last_sync} for space {target_space}")

        # Fetch pages updated since last sync
        pages = confluence_client.get_pages_updated_since(
            last_sync=last_sync,
            space_key=target_space,
        )

        logger.info(f"Found {len(pages)} pages to process")

        for page in pages:
            try:
                page_id = page.get("id")
                doc_id = f"confluence-{page_id}"

                # Get detailed page content
                page_content = confluence_client.get_page_content(page_id)

                title = page.get("title", "")
                content = page_content.get("content", "") if page_content else ""

                # Get page comments
                comments = confluence_client.get_page_comments(page_id)
                comments_text = "\n\n".join([
                    f"Comment by {c.get('author', 'Unknown')}: {c.get('body', '')}"
                    for c in comments
                ]) if comments else ""

                if comments_text:
                    content += f"\n\n--- Comments ---\n{comments_text}"

                # Build URL
                page_url = page.get("_links", {}).get("webui", "")
                if page_url and not page_url.startswith("http"):
                    page_url = f"{settings.confluence_url}{page_url}"

                # Get author information
                author = page.get("history", {}).get("createdBy", {}).get("displayName")
                if not author:
                    author = page.get("version", {}).get("by", {}).get("displayName")

                # Check if document already exists
                existing_doc = (
                    db.query(Document)
                    .filter(Document.doc_id == doc_id)
                    .first()
                )

                if existing_doc:
                    # Update existing document
                    existing_doc.title = title
                    existing_doc.content = content
                    existing_doc.url = page_url
                    existing_doc.author = author
                    existing_doc.updated_at = datetime.utcnow()
                    existing_doc.last_synced_at = datetime.utcnow()
                    existing_doc.deleted = False
                    existing_doc.metadata_ = {
                        "space_key": page.get("space", {}).get("key"),
                        "space_name": page.get("space", {}).get("name"),
                        "version": page.get("version", {}).get("number"),
                        "type": page.get("type"),
                    }
                    stats["updated"] += 1
                    logger.debug(f"Updated page: {title}")
                else:
                    # Create new document
                    new_doc = Document(
                        doc_id=doc_id,
                        doc_type="confluence",
                        title=title,
                        url=page_url,
                        content=content,
                        author=author,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        last_synced_at=datetime.utcnow(),
                        deleted=False,
                        metadata_={
                            "space_key": page.get("space", {}).get("key"),
                            "space_name": page.get("space", {}).get("name"),
                            "version": page.get("version", {}).get("number"),
                            "type": page.get("type"),
                        },
                    )
                    db.add(new_doc)
                    stats["added"] += 1
                    logger.debug(f"Added new page: {title}")

            except Exception as e:
                logger.error(f"Error processing page {page.get('id', 'unknown')}: {e}")
                stats["errors"] += 1
                continue

        # Commit all changes
        db.commit()

        logger.info(
            f"Confluence sync completed: "
            f"added={stats['added']}, updated={stats['updated']}, "
            f"deleted={stats['deleted']}, errors={stats['errors']}"
        )

    except Exception as e:
        logger.error(f"Confluence sync failed: {e}")
        db.rollback()
        raise

    return stats
