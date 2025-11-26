"""FAISS index update module.

This module handles updating the FAISS vector index with new embeddings
and removing deleted documents from the index.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from app.config import settings
from app.core.services.embedding_service import EmbeddingService
from app.core.services.vector_db_service import VectorDBService
from app.models.document import Document, DocumentChunk
from app.utils.storage import StorageClient

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_FAISS_DIR = Path(__file__).parent.parent / "data" / "vector_db"
DEFAULT_FAISS_INDEX_PATH = DEFAULT_FAISS_DIR / "faiss.index"
DEFAULT_METADATA_PATH = DEFAULT_FAISS_DIR / "metadata.pkl"


def get_deleted_chunk_ids(db: Session) -> List[int]:
    """Get FAISS index IDs for chunks of deleted documents.

    Args:
        db: Database session

    Returns:
        List of FAISS index IDs to remove
    """
    chunks = (
        db.query(DocumentChunk.faiss_index_id)
        .join(Document)
        .filter(
            Document.deleted == True,
            DocumentChunk.faiss_index_id.is_not(None),
        )
        .all()
    )
    return [chunk.faiss_index_id for chunk in chunks if chunk.faiss_index_id is not None]


def get_chunks_without_embeddings(db: Session) -> List[DocumentChunk]:
    """Get chunks that don't have FAISS index IDs yet.

    Args:
        db: Database session

    Returns:
        List of DocumentChunk objects needing embeddings
    """
    return (
        db.query(DocumentChunk)
        .join(Document)
        .filter(
            Document.deleted == False,
            DocumentChunk.faiss_index_id.is_(None),
        )
        .all()
    )


def update_faiss_index(
    db: Session,
    index_path: Optional[Path] = None,
    upload_to_cloud: bool = False,
) -> dict:
    """Update FAISS index with new embeddings and remove deleted documents.

    This function:
    1. Loads existing FAISS index (or creates new one)
    2. Removes vectors for deleted documents
    3. Generates embeddings for new chunks
    4. Adds new vectors to the index
    5. Saves the updated index
    6. Optionally uploads to Cloud Storage

    Args:
        db: Database session
        index_path: Path to FAISS index file (default: data/vector_db/faiss.index)
        upload_to_cloud: Whether to upload to Cloud Storage

    Returns:
        Dictionary with update statistics:
            - vectors_added: Number of new vectors added
            - vectors_removed: Number of vectors removed (deleted docs)
            - total_vectors: Total vectors in index after update
            - errors: Number of errors encountered
    """
    stats = {
        "vectors_added": 0,
        "vectors_removed": 0,
        "total_vectors": 0,
        "errors": 0,
    }

    index_path = index_path or DEFAULT_FAISS_INDEX_PATH

    try:
        # Initialize services
        vector_db_service = VectorDBService()
        embedding_service = EmbeddingService()

        # Load existing index or create new one
        if index_path.exists():
            logger.info(f"Loading existing FAISS index from {index_path}")
            vector_db_service.load_index(index_path)
            logger.info(f"Loaded index with {vector_db_service.index.ntotal} vectors")
        else:
            logger.info("Creating new FAISS index")
            vector_db_service.create_index()

        # Note: FAISS IndexFlatL2 doesn't support removal
        # For production, consider using IndexIDMap for removal support
        # For now, we'll rebuild the index if there are deletions

        # Check for deleted documents
        deleted_ids = get_deleted_chunk_ids(db)
        if deleted_ids:
            logger.warning(
                f"Found {len(deleted_ids)} chunks from deleted documents. "
                "Rebuilding index to remove them..."
            )
            # For IndexFlatL2, we need to rebuild the entire index
            # This is a limitation - for production, use IndexIDMap
            stats["vectors_removed"] = len(deleted_ids)

            # Clear faiss_index_id for deleted chunks
            db.query(DocumentChunk).filter(
                DocumentChunk.faiss_index_id.in_(deleted_ids)
            ).update(
                {DocumentChunk.faiss_index_id: None},
                synchronize_session=False,
            )
            db.commit()

            # Rebuild index from scratch
            vector_db_service.create_index()
            logger.info("Created fresh index for rebuild")

            # Get all non-deleted chunks for rebuild
            all_chunks = get_chunks_without_embeddings(db)
        else:
            # Just get new chunks
            all_chunks = get_chunks_without_embeddings(db)

        # Generate embeddings and add to index
        if all_chunks:
            logger.info(f"Processing {len(all_chunks)} chunks for embedding")

            # Process in batches
            batch_size = 100
            for i in range(0, len(all_chunks), batch_size):
                batch_chunks = all_chunks[i:i + batch_size]
                texts = [chunk.chunk_text for chunk in batch_chunks]

                try:
                    # Generate embeddings
                    embeddings = embedding_service.get_embeddings_batch(texts)

                    # Add to FAISS index
                    for j, (chunk, embedding) in enumerate(zip(batch_chunks, embeddings)):
                        # Get the current index size as the new ID
                        faiss_id = vector_db_service.index.ntotal

                        # Add vector to index
                        vector_db_service.index.add(
                            np.array([embedding], dtype=np.float32)
                        )

                        # Update chunk with FAISS index ID
                        chunk.faiss_index_id = faiss_id
                        stats["vectors_added"] += 1

                    logger.debug(f"Added batch {i // batch_size + 1} to index")

                except Exception as e:
                    logger.error(f"Error processing batch {i // batch_size + 1}: {e}")
                    stats["errors"] += len(batch_chunks)
                    continue

            # Commit chunk updates
            db.commit()

        # Save index
        stats["total_vectors"] = vector_db_service.index.ntotal
        logger.info(f"Saving FAISS index with {stats['total_vectors']} vectors")

        # Ensure directory exists
        index_path.parent.mkdir(parents=True, exist_ok=True)
        vector_db_service.save_index(index_path)

        # Upload to Cloud Storage if configured
        if upload_to_cloud:
            try:
                storage_client = StorageClient()
                gcs_path = f"vector_db/{index_path.name}"
                storage_client.upload_file(str(index_path), gcs_path)
                logger.info(f"Uploaded index to Cloud Storage: {gcs_path}")
            except Exception as e:
                logger.warning(f"Failed to upload to Cloud Storage: {e}")

        logger.info(
            f"FAISS update completed: "
            f"added={stats['vectors_added']}, "
            f"removed={stats['vectors_removed']}, "
            f"total={stats['total_vectors']}, "
            f"errors={stats['errors']}"
        )

    except Exception as e:
        logger.error(f"FAISS update failed: {e}")
        db.rollback()
        raise

    return stats


def rebuild_faiss_index(
    db: Session,
    index_path: Optional[Path] = None,
) -> dict:
    """Rebuild the entire FAISS index from scratch.

    This function rebuilds the index by:
    1. Creating a new empty index
    2. Generating embeddings for all non-deleted chunks
    3. Adding all vectors to the index
    4. Saving the new index

    Args:
        db: Database session
        index_path: Path to save the FAISS index

    Returns:
        Dictionary with rebuild statistics
    """
    logger.info("Starting full FAISS index rebuild")

    # Clear all faiss_index_id values
    db.query(DocumentChunk).update(
        {DocumentChunk.faiss_index_id: None},
        synchronize_session=False,
    )
    db.commit()

    # Use update function to rebuild
    return update_faiss_index(db, index_path)
