#!/usr/bin/env python3
"""Database initialization script.

This script creates all database tables defined in the models.
Run from the backend directory:
    python scripts/init_db.py
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import inspect, text

from app.database import Base, engine
from app.models import ChatHistory, Document, DocumentChunk, Feedback, SyncHistory  # noqa: F401


def init_database():
    """Initialize the database by creating all tables."""
    print("Initializing database...")
    print(f"Database URL: {engine.url}")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

    # Verify tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("\nCreated tables:")
    for table in tables:
        print(f"  - {table}")

    # Count tables
    expected_tables = ["documents", "document_chunks", "chat_history", "feedback", "sync_history"]
    missing_tables = [t for t in expected_tables if t not in tables]

    if missing_tables:
        print(f"\nWarning: Missing tables: {missing_tables}")
        return False

    print(f"\nAll {len(expected_tables)} tables created successfully!")

    # Test connection with simple query
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM documents"))
        count = result.scalar()
        print(f"\nDocuments table row count: {count}")

    return True


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
