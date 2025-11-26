"""Text chunking and embedding processing module.

This module handles chunking documents into smaller pieces
and generating embeddings for vector search.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from app.core.services.embedding_service import EmbeddingService
from app.models.document import Document, DocumentChunk
from app.utils.text_splitter import chunk_documents

logger = logging.getLogger(__name__)

# Batch size for embedding generation
EMBEDDING_BATCH_SIZE = 100


def delete_existing_chunks(db: Session, document_id: int) -> int:
    """Delete existing chunks for a document.

    Args:
        db: Database session
        document_id: ID of the document

    Returns:
        Number of chunks deleted
    """
    deleted_count = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .delete(synchronize_session=False)
    )
    return deleted_count


def create_chunks_for_document(
    db: Session,
    document: Document,
) -> List[DocumentChunk]:
    """Create text chunks for a document.

    Args:
        db: Database session
        document: Document to chunk

    Returns:
        List of created DocumentChunk objects
    """
    # Use the text splitter to chunk the content
    chunks_data = chunk_documents([{
        "content": document.content,
        "metadata": {
            "doc_id": document.doc_id,
            "doc_type": document.doc_type,
            "title": document.title,
        }
    }])

    chunks = []
    for idx, chunk_data in enumerate(chunks_data):
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=idx,
            chunk_text=chunk_data["text"],
            created_at=datetime.utcnow(),
        )
        db.add(chunk)
        chunks.append(chunk)

    return chunks


def generate_embeddings_batch(
    texts: List[str],
    embedding_service: EmbeddingService,
) -> List[np.ndarray]:
    """Generate embeddings for a batch of texts.

    Args:
        texts: List of texts to embed
        embedding_service: Embedding service instance

    Returns:
        List of embedding vectors
    """
    embeddings = []

    # Process in batches
    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i:i + EMBEDDING_BATCH_SIZE]
        batch_embeddings = embedding_service.get_embeddings_batch(batch)
        embeddings.extend(batch_embeddings)

        logger.debug(f"Generated embeddings for batch {i // EMBEDDING_BATCH_SIZE + 1}")

    return embeddings


def process_document_chunks(
    db: Session,
    document_ids: Optional[List[int]] = None,
    force_reprocess: bool = False,
) -> dict:
    """Process documents: chunk text and generate embeddings.

    This function processes documents by:
    1. Chunking the document content into smaller pieces
    2. Generating embeddings for each chunk
    3. Storing chunks in the database

    Args:
        db: Database session
        document_ids: Optional list of specific document IDs to process.
                     If None, processes all documents needing updates.
        force_reprocess: If True, reprocess even if chunks exist

    Returns:
        Dictionary with processing statistics:
            - documents_processed: Number of documents processed
            - chunks_created: Number of chunks created
            - chunks_deleted: Number of old chunks deleted
            - embeddings_generated: Number of embeddings generated
            - errors: Number of errors encountered
    """
    stats = {
        "documents_processed": 0,
        "chunks_created": 0,
        "chunks_deleted": 0,
        "embeddings_generated": 0,
        "errors": 0,
    }

    try:
        # Initialize embedding service
        embedding_service = EmbeddingService()

        # Query documents to process
        query = db.query(Document).filter(Document.deleted == False)

        if document_ids:
            query = query.filter(Document.id.in_(document_ids))

        documents = query.all()
        logger.info(f"Processing {len(documents)} documents for chunking")

        all_chunks: List[DocumentChunk] = []
        all_texts: List[str] = []

        for document in documents:
            try:
                # Check if document already has chunks and we're not forcing reprocess
                existing_chunks = (
                    db.query(DocumentChunk)
                    .filter(DocumentChunk.document_id == document.id)
                    .count()
                )

                if existing_chunks > 0 and not force_reprocess:
                    logger.debug(f"Skipping document {document.doc_id} - already has {existing_chunks} chunks")
                    continue

                # Delete existing chunks if reprocessing
                if existing_chunks > 0:
                    deleted = delete_existing_chunks(db, document.id)
                    stats["chunks_deleted"] += deleted
                    logger.debug(f"Deleted {deleted} existing chunks for document {document.doc_id}")

                # Create new chunks
                chunks = create_chunks_for_document(db, document)
                all_chunks.extend(chunks)

                # Collect texts for embedding
                for chunk in chunks:
                    all_texts.append(chunk.chunk_text)

                stats["documents_processed"] += 1
                stats["chunks_created"] += len(chunks)

                logger.debug(f"Created {len(chunks)} chunks for document {document.doc_id}")

            except Exception as e:
                logger.error(f"Error processing document {document.doc_id}: {e}")
                stats["errors"] += 1
                continue

        # Commit chunks to database
        db.commit()

        # Generate embeddings for all chunks
        if all_texts:
            logger.info(f"Generating embeddings for {len(all_texts)} chunks")

            embeddings = generate_embeddings_batch(all_texts, embedding_service)
            stats["embeddings_generated"] = len(embeddings)

            # Store embeddings (will be used by update_faiss.py)
            # For now, we just return the stats
            # The actual FAISS update is done separately

        logger.info(
            f"Chunk processing completed: "
            f"documents={stats['documents_processed']}, "
            f"chunks_created={stats['chunks_created']}, "
            f"chunks_deleted={stats['chunks_deleted']}, "
            f"embeddings={stats['embeddings_generated']}, "
            f"errors={stats['errors']}"
        )

    except Exception as e:
        logger.error(f"Chunk processing failed: {e}")
        db.rollback()
        raise

    return stats


def get_chunks_needing_embeddings(db: Session) -> List[Tuple[DocumentChunk, str]]:
    """Get chunks that don't have FAISS index IDs yet.

    Args:
        db: Database session

    Returns:
        List of tuples (chunk, text) for chunks needing embeddings
    """
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.faiss_index_id.is_(None))
        .join(Document)
        .filter(Document.deleted == False)
        .all()
    )

    return [(chunk, chunk.chunk_text) for chunk in chunks]
