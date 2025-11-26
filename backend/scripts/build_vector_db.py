"""Script to build FAISS vector database from PostgreSQL documents."""

import argparse
import logging
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func

from app.config import get_settings
from app.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.utils.text_splitter import TextSplitter
from app.core.services.embedding_service import EmbeddingService
from app.core.services.vector_db_service import VectorDBService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_INDEX_PATH = Path(__file__).parent.parent / "data" / "vector_db" / "faiss.index"
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_BATCH_SIZE = 50


def count_documents(db) -> dict:
    """Count documents by type."""
    total = db.execute(select(func.count(Document.id))).scalar()
    jira_count = db.execute(
        select(func.count(Document.id)).where(Document.doc_type == "jira")
    ).scalar()
    confluence_count = db.execute(
        select(func.count(Document.id)).where(Document.doc_type == "confluence")
    ).scalar()
    deleted_count = db.execute(
        select(func.count(Document.id)).where(Document.deleted == True)
    ).scalar()

    return {
        "total": total,
        "jira": jira_count,
        "confluence": confluence_count,
        "deleted": deleted_count,
        "active": total - deleted_count,
    }


def clear_existing_chunks(db) -> int:
    """Delete all existing document chunks."""
    count = db.query(DocumentChunk).delete()
    db.commit()
    logger.info(f"Deleted {count} existing chunks")
    return count


def build_vector_db(
    index_path: str | Path = DEFAULT_INDEX_PATH,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    batch_size: int = DEFAULT_BATCH_SIZE,
    clear_existing: bool = True,
    include_deleted: bool = False,
) -> dict:
    """Build FAISS vector database from PostgreSQL documents.

    Args:
        index_path: Path to save FAISS index
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        batch_size: Number of chunks to process per embedding batch
        clear_existing: Whether to clear existing chunks before building
        include_deleted: Whether to include deleted documents

    Returns:
        Statistics dictionary
    """
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    stats = {
        "documents_processed": 0,
        "chunks_created": 0,
        "embeddings_generated": 0,
        "errors": 0,
    }

    # Initialize services
    logger.info("Initializing services...")
    text_splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    embedding_service = EmbeddingService()
    vector_db_service = VectorDBService(dimension=embedding_service.dimension)
    vector_db_service.create_index()

    with SessionLocal() as db:
        # Count documents
        doc_counts = count_documents(db)
        logger.info(f"Document counts: {doc_counts}")

        # Clear existing chunks if requested
        if clear_existing:
            clear_existing_chunks(db)

        # Query documents
        stmt = select(Document)
        if not include_deleted:
            stmt = stmt.where(Document.deleted == False)

        documents = db.execute(stmt).scalars().all()
        total_docs = len(documents)
        logger.info(f"Processing {total_docs} documents...")

        # Process documents
        all_chunks_for_embedding = []
        chunk_db_records = []

        for i, document in enumerate(documents, 1):
            try:
                # Skip if no content
                if not document.content or not document.content.strip():
                    logger.debug(f"Skipping empty document: {document.doc_id}")
                    continue

                # Create document dict for chunking
                doc_dict = {
                    "doc_id": document.doc_id,
                    "doc_type": document.doc_type,
                    "title": document.title or "",
                    "content": document.content,
                    "url": document.url or "",
                    "author": document.author or "",
                    "created_at": document.created_at.isoformat() if document.created_at else "",
                    "updated_at": document.updated_at.isoformat() if document.updated_at else "",
                }

                # Split into chunks
                chunks = text_splitter.split_document(doc_dict)

                if not chunks:
                    logger.debug(f"No chunks created for: {document.doc_id}")
                    continue

                # Store chunk records for database
                for chunk in chunks:
                    chunk_record = DocumentChunk(
                        document_id=document.id,
                        chunk_index=chunk["chunk_index"],
                        chunk_text=chunk["chunk_text"],
                    )
                    db.add(chunk_record)
                    chunk_db_records.append((chunk_record, chunk))

                stats["documents_processed"] += 1
                stats["chunks_created"] += len(chunks)

                # Log progress
                if i % 10 == 0 or i == total_docs:
                    logger.info(f"Chunked {i}/{total_docs} documents ({stats['chunks_created']} chunks)")

            except Exception as e:
                logger.error(f"Error processing document {document.doc_id}: {e}")
                stats["errors"] += 1

        # Commit chunk records to get IDs
        db.commit()
        logger.info(f"Saved {len(chunk_db_records)} chunks to database")

        # Generate embeddings in batches
        logger.info(f"Generating embeddings for {len(chunk_db_records)} chunks...")

        for i in range(0, len(chunk_db_records), batch_size):
            batch = chunk_db_records[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(chunk_db_records) + batch_size - 1) // batch_size

            try:
                # Extract texts for embedding
                texts = [chunk["chunk_text"] for _, chunk in batch]

                # Generate embeddings
                embeddings = embedding_service.get_embeddings_batch(texts)

                # Add to FAISS index with metadata
                vectors = []
                metadata_list = []

                for (chunk_record, chunk_dict), embedding in zip(batch, embeddings):
                    vectors.append(embedding)
                    metadata_list.append({
                        "chunk_id": chunk_record.id,
                        "doc_id": chunk_dict["doc_id"],
                        "chunk_index": chunk_dict["chunk_index"],
                        "chunk_text": chunk_dict["chunk_text"][:200],
                    })

                    # Update chunk record with FAISS index ID
                    # (will be updated after add_vectors)

                # Add to FAISS
                index_ids = vector_db_service.add_vectors(vectors, metadata_list)

                # Update chunk records with FAISS index IDs
                for (chunk_record, _), faiss_id in zip(batch, index_ids):
                    chunk_record.faiss_index_id = faiss_id

                stats["embeddings_generated"] += len(embeddings)

                logger.info(
                    f"Batch {batch_num}/{total_batches}: "
                    f"Generated {len(embeddings)} embeddings"
                )

            except Exception as e:
                logger.error(f"Error generating embeddings for batch {batch_num}: {e}")
                stats["errors"] += 1

        # Commit FAISS index IDs
        db.commit()
        logger.info("Updated chunk records with FAISS index IDs")

    # Save FAISS index
    vector_db_service.save_index(index_path)
    logger.info(f"Saved FAISS index to {index_path}")

    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    stats["elapsed_seconds"] = round(elapsed_time, 2)
    stats["elapsed_minutes"] = round(elapsed_time / 60, 2)

    # Final stats
    index_stats = vector_db_service.get_stats()
    stats["index_vectors"] = index_stats["total_vectors"]
    stats["index_dimension"] = index_stats["dimension"]

    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build FAISS vector database from PostgreSQL documents"
    )
    parser.add_argument(
        "--index-path",
        type=str,
        default=str(DEFAULT_INDEX_PATH),
        help=f"Path to save FAISS index (default: {DEFAULT_INDEX_PATH})",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Chunk size in characters (default: {DEFAULT_CHUNK_SIZE})",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"Chunk overlap in characters (default: {DEFAULT_CHUNK_OVERLAP})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Embedding batch size (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Don't clear existing chunks before building",
    )
    parser.add_argument(
        "--include-deleted",
        action="store_true",
        help="Include deleted documents",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Knowledge Base AI Chatbot - 벡터 DB 빌드")
    print("=" * 60)
    print(f"인덱스 경로: {args.index_path}")
    print(f"청크 크기: {args.chunk_size}")
    print(f"청크 오버랩: {args.chunk_overlap}")
    print(f"배치 크기: {args.batch_size}")
    print("=" * 60)

    try:
        stats = build_vector_db(
            index_path=args.index_path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            batch_size=args.batch_size,
            clear_existing=not args.no_clear,
            include_deleted=args.include_deleted,
        )

        print("\n" + "=" * 60)
        print("빌드 완료!")
        print("=" * 60)
        print(f"처리된 문서: {stats['documents_processed']}")
        print(f"생성된 청크: {stats['chunks_created']}")
        print(f"생성된 임베딩: {stats['embeddings_generated']}")
        print(f"인덱스 벡터 수: {stats['index_vectors']}")
        print(f"벡터 차원: {stats['index_dimension']}")
        print(f"오류 수: {stats['errors']}")
        print(f"소요 시간: {stats['elapsed_minutes']} 분 ({stats['elapsed_seconds']} 초)")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Build failed: {e}")
        print(f"\n❌ 빌드 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
