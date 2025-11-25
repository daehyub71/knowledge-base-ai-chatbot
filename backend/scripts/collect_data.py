#!/usr/bin/env python3
"""Data collection script for Jira and Confluence documents.

Run from the backend directory:
    python scripts/collect_data.py --source jira
    python scripts/collect_data.py --source confluence
    python scripts/collect_data.py --source all
    python scripts/collect_data.py --source all --detect-deleted
"""

import argparse
import logging
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text

from app.database import SessionLocal
from app.core.services.deletion_detector import DeletionDetector
from app.core.services.incremental_sync import IncrementalSync

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for data collection."""
    parser = argparse.ArgumentParser(description="Collect documents from Jira and Confluence")
    parser.add_argument(
        "--source",
        choices=["jira", "confluence", "all"],
        required=True,
        help="Data source to collect from",
    )
    parser.add_argument(
        "--project-key",
        help="Jira project key to filter (optional)",
    )
    parser.add_argument(
        "--space-key",
        help="Confluence space key to filter (optional)",
    )
    parser.add_argument(
        "--detect-deleted",
        action="store_true",
        help="Also detect and mark deleted documents",
    )
    parser.add_argument(
        "--full-sync",
        action="store_true",
        help="Perform full sync instead of incremental",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Data Collection Script")
    print("=" * 60)
    print(f"\nSource: {args.source}")
    if args.project_key:
        print(f"Project Key: {args.project_key}")
    if args.space_key:
        print(f"Space Key: {args.space_key}")
    print(f"Detect Deleted: {args.detect_deleted}")
    print(f"Full Sync: {args.full_sync}")
    print()

    # Create database session
    db = SessionLocal()

    try:
        # Initialize sync service
        sync_service = IncrementalSync(db)

        # Run sync
        print(f"Starting {args.source} sync...")
        stats = sync_service.run_sync(
            sync_type=args.source,
            project_key=args.project_key,
            space_key=args.space_key,
        )

        print("\nSync Results:")
        print(f"  - Added: {stats.get('added', 0)}")
        print(f"  - Updated: {stats.get('updated', 0)}")
        print(f"  - Skipped: {stats.get('skipped', 0)}")
        print(f"  - Errors: {stats.get('errors', 0)}")

        # Detect deleted documents if requested
        if args.detect_deleted:
            print("\nDetecting deleted documents...")
            detector = DeletionDetector(db)
            deleted_stats = detector.detect_all_deleted(
                project_key=args.project_key,
                space_key=args.space_key,
            )
            print(f"  - Jira deleted: {deleted_stats.get('jira', 0)}")
            print(f"  - Confluence deleted: {deleted_stats.get('confluence', 0)}")

        # Show document counts
        print("\nDatabase Statistics:")
        result = db.execute(text("SELECT COUNT(*) FROM documents WHERE deleted = false"))
        total_docs = result.scalar()
        print(f"  - Total active documents: {total_docs}")

        result = db.execute(
            text("SELECT doc_type, COUNT(*) FROM documents WHERE deleted = false GROUP BY doc_type")
        )
        for row in result:
            print(f"    - {row[0]}: {row[1]}")

        print("\n" + "=" * 60)
        print("Data collection completed successfully!")
        print("=" * 60)

    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        print("\nPlease check your .env file and ensure all required")
        print("API credentials are set for the selected source.")
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
