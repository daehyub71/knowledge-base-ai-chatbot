"""Main entry point for batch processing jobs.

Usage:
    python -m batch.main --source all
    python -m batch.main --source jira
    python -m batch.main --source confluence
    python -m batch.main --source all --full-sync  # Include chunking and FAISS update
    python -m batch.main --rebuild-faiss  # Rebuild FAISS index from scratch
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.sync import SyncHistory
from batch.sync_jira import sync_jira_incremental
from batch.sync_confluence import sync_confluence_incremental
from batch.detect_deleted import detect_and_mark_deleted
from batch.process_chunks import process_document_chunks
from batch.update_faiss import update_faiss_index, rebuild_faiss_index
from batch.retry_handler import retry_with_backoff, RetryError

# Ensure logs directory exists
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / f"batch_{datetime.now().strftime('%Y-%m-%d')}.log"),
    ],
)
logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def create_sync_history(
    db: Session,
    sync_type: str,
    status: str = "running",
) -> SyncHistory:
    """Create a new sync history record.

    Args:
        db: Database session
        sync_type: Type of sync (jira/confluence)
        status: Initial status

    Returns:
        Created SyncHistory record
    """
    sync_history = SyncHistory(
        sync_type=sync_type,
        status=status,
        started_at=get_utc_now(),
    )
    db.add(sync_history)
    db.commit()
    db.refresh(sync_history)
    return sync_history


def update_sync_history(
    db: Session,
    sync_history: SyncHistory,
    status: str,
    documents_added: int = 0,
    documents_updated: int = 0,
    documents_deleted: int = 0,
    error_message: str | None = None,
) -> None:
    """Update sync history record with results.

    Args:
        db: Database session
        sync_history: SyncHistory record to update
        status: Final status (success/failed)
        documents_added: Number of documents added
        documents_updated: Number of documents updated
        documents_deleted: Number of documents deleted
        error_message: Error message if failed
    """
    sync_history.status = status
    sync_history.documents_added = documents_added
    sync_history.documents_updated = documents_updated
    sync_history.documents_deleted = documents_deleted
    sync_history.error_message = error_message
    sync_history.completed_at = get_utc_now()
    db.commit()


@retry_with_backoff(max_retries=3, initial_delay=60, max_delay=3600)
def sync_jira_with_retry(db: Session) -> dict:
    """Sync Jira with retry logic."""
    return sync_jira_incremental(db)


@retry_with_backoff(max_retries=3, initial_delay=60, max_delay=3600)
def sync_confluence_with_retry(db: Session) -> dict:
    """Sync Confluence with retry logic."""
    return sync_confluence_incremental(db)


def run_batch(
    source: Literal["jira", "confluence", "all"],
    full_sync: bool = False,
    detect_deletions: bool = True,
    use_retry: bool = True,
) -> dict:
    """Run batch synchronization job.

    Args:
        source: Data source to sync (jira/confluence/all)
        full_sync: If True, also run chunking and FAISS update
        detect_deletions: If True, detect and mark deleted documents
        use_retry: If True, use retry logic for sync operations

    Returns:
        Dictionary with sync results
    """
    logger.info(f"Starting batch job for source: {source}")
    logger.info(f"Full sync: {full_sync}, Detect deletions: {detect_deletions}")

    results = {
        "jira": None,
        "confluence": None,
        "deletions": None,
        "chunks": None,
        "faiss": None,
        "success": True,
        "errors": [],
    }

    db = SessionLocal()

    try:
        # Sync Jira
        if source in ("jira", "all"):
            logger.info("=" * 40)
            logger.info("Starting Jira sync...")
            sync_history = create_sync_history(db, "jira")

            try:
                if use_retry:
                    jira_result = sync_jira_with_retry(db)
                else:
                    jira_result = sync_jira_incremental(db)

                update_sync_history(
                    db,
                    sync_history,
                    status="success",
                    documents_added=jira_result.get("added", 0),
                    documents_updated=jira_result.get("updated", 0),
                    documents_deleted=jira_result.get("deleted", 0),
                )
                results["jira"] = jira_result
                logger.info(f"Jira sync completed: {jira_result}")

            except RetryError as e:
                error_msg = f"Jira sync failed after retries: {e.last_exception}"
                logger.error(error_msg)
                update_sync_history(db, sync_history, status="failed", error_message=error_msg)
                results["errors"].append(error_msg)
                results["success"] = False

            except Exception as e:
                error_msg = f"Jira sync failed: {str(e)}"
                logger.error(error_msg)
                update_sync_history(db, sync_history, status="failed", error_message=error_msg)
                results["errors"].append(error_msg)
                results["success"] = False

        # Sync Confluence
        if source in ("confluence", "all"):
            logger.info("=" * 40)
            logger.info("Starting Confluence sync...")
            sync_history = create_sync_history(db, "confluence")

            try:
                if use_retry:
                    confluence_result = sync_confluence_with_retry(db)
                else:
                    confluence_result = sync_confluence_incremental(db)

                update_sync_history(
                    db,
                    sync_history,
                    status="success",
                    documents_added=confluence_result.get("added", 0),
                    documents_updated=confluence_result.get("updated", 0),
                    documents_deleted=confluence_result.get("deleted", 0),
                )
                results["confluence"] = confluence_result
                logger.info(f"Confluence sync completed: {confluence_result}")

            except RetryError as e:
                error_msg = f"Confluence sync failed after retries: {e.last_exception}"
                logger.error(error_msg)
                update_sync_history(db, sync_history, status="failed", error_message=error_msg)
                results["errors"].append(error_msg)
                results["success"] = False

            except Exception as e:
                error_msg = f"Confluence sync failed: {str(e)}"
                logger.error(error_msg)
                update_sync_history(db, sync_history, status="failed", error_message=error_msg)
                results["errors"].append(error_msg)
                results["success"] = False

        # Detect deletions
        if detect_deletions:
            logger.info("=" * 40)
            logger.info("Detecting deleted documents...")
            try:
                deletion_result = detect_and_mark_deleted(db, source)
                results["deletions"] = deletion_result
                logger.info(f"Deletion detection completed: {deletion_result}")
            except Exception as e:
                error_msg = f"Deletion detection failed: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

        # Full sync: process chunks and update FAISS
        if full_sync:
            logger.info("=" * 40)
            logger.info("Processing document chunks...")
            try:
                chunk_result = process_document_chunks(db, force_reprocess=False)
                results["chunks"] = chunk_result
                logger.info(f"Chunk processing completed: {chunk_result}")
            except Exception as e:
                error_msg = f"Chunk processing failed: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["success"] = False

            logger.info("=" * 40)
            logger.info("Updating FAISS index...")
            try:
                faiss_result = update_faiss_index(db)
                results["faiss"] = faiss_result
                logger.info(f"FAISS update completed: {faiss_result}")
            except Exception as e:
                error_msg = f"FAISS update failed: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["success"] = False

    finally:
        db.close()

    return results


def run_faiss_rebuild() -> dict:
    """Rebuild the entire FAISS index from scratch.

    Returns:
        Dictionary with rebuild results
    """
    logger.info("Starting FAISS index rebuild...")

    db = SessionLocal()
    try:
        result = rebuild_faiss_index(db)
        logger.info(f"FAISS rebuild completed: {result}")
        return result
    finally:
        db.close()


def main() -> None:
    """Main entry point for batch CLI."""
    parser = argparse.ArgumentParser(
        description="Knowledge Base AI Chatbot - Batch Sync Job"
    )
    parser.add_argument(
        "--source",
        type=str,
        choices=["jira", "confluence", "all"],
        default="all",
        help="Data source to sync (default: all)",
    )
    parser.add_argument(
        "--full-sync",
        action="store_true",
        help="Run full sync including chunking and FAISS update",
    )
    parser.add_argument(
        "--rebuild-faiss",
        action="store_true",
        help="Rebuild FAISS index from scratch (ignores --source)",
    )
    parser.add_argument(
        "--no-deletions",
        action="store_true",
        help="Skip deletion detection",
    )
    parser.add_argument(
        "--no-retry",
        action="store_true",
        help="Disable retry logic for sync operations",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without making changes (for testing)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("Knowledge Base AI Chatbot - Batch Sync Job")
    logger.info(f"Source: {args.source}")
    logger.info(f"Full Sync: {args.full_sync}")
    logger.info(f"Rebuild FAISS: {args.rebuild_faiss}")
    logger.info(f"Detect Deletions: {not args.no_deletions}")
    logger.info(f"Use Retry: {not args.no_retry}")
    logger.info(f"Dry Run: {args.dry_run}")
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        return

    try:
        # Rebuild FAISS if requested
        if args.rebuild_faiss:
            result = run_faiss_rebuild()
            logger.info("=" * 60)
            logger.info("FAISS Rebuild Completed")
            logger.info(f"Total vectors: {result.get('total_vectors', 0)}")
            logger.info("=" * 60)
            return

        # Run normal batch sync
        results = run_batch(
            source=args.source,
            full_sync=args.full_sync,
            detect_deletions=not args.no_deletions,
            use_retry=not args.no_retry,
        )

        logger.info("=" * 60)
        logger.info("Batch Job Completed")
        logger.info(f"Success: {results['success']}")

        if results["jira"]:
            logger.info(
                f"Jira: +{results['jira'].get('added', 0)} added, "
                f"~{results['jira'].get('updated', 0)} updated"
            )

        if results["confluence"]:
            logger.info(
                f"Confluence: +{results['confluence'].get('added', 0)} added, "
                f"~{results['confluence'].get('updated', 0)} updated"
            )

        if results["deletions"]:
            logger.info(f"Deletions: {results['deletions'].get('total_deleted', 0)} marked as deleted")

        if results["chunks"]:
            logger.info(
                f"Chunks: {results['chunks'].get('chunks_created', 0)} created, "
                f"{results['chunks'].get('documents_processed', 0)} documents processed"
            )

        if results["faiss"]:
            logger.info(
                f"FAISS: {results['faiss'].get('vectors_added', 0)} added, "
                f"{results['faiss'].get('total_vectors', 0)} total"
            )

        if results["errors"]:
            logger.error(f"Errors: {results['errors']}")
            sys.exit(1)

        logger.info("=" * 60)

    except Exception as e:
        logger.exception(f"Batch job failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
