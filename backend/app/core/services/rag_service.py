"""RAG (Retrieval-Augmented Generation) service for document search."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.services.embedding_service import EmbeddingService
from app.core.services.vector_db_service import VectorDBService
from app.database import SessionLocal
from app.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-based document retrieval."""

    def __init__(
        self,
        vector_db_path: str | None = None,
        auto_load_index: bool = True,
    ):
        """Initialize the RAG service.

        Args:
            vector_db_path: Path to FAISS index file
            auto_load_index: Whether to auto-load index if path exists
        """
        self.embedding_service = EmbeddingService()
        self.vector_db_service = VectorDBService(
            dimension=self.embedding_service.dimension
        )
        self.vector_db_path = vector_db_path

        # Auto-load index if path provided and exists
        if auto_load_index and vector_db_path:
            try:
                self.vector_db_service.load_index(vector_db_path)
                logger.info(f"Loaded FAISS index from {vector_db_path}")
            except FileNotFoundError:
                logger.warning(
                    f"FAISS index not found at {vector_db_path}, "
                    "will create new index when documents are added"
                )

        logger.info("RAGService initialized")

    def search_documents(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float | None = None,
        doc_type: str | None = None,
        include_deleted: bool = False,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Search for relevant documents using vector similarity.

        Args:
            query: Search query text
            top_k: Number of results to return
            score_threshold: Minimum similarity score (0-1)
            doc_type: Filter by document type ('jira' or 'confluence')
            include_deleted: Whether to include deleted documents
            date_from: Filter documents updated after this date
            date_to: Filter documents updated before this date

        Returns:
            List of search results with document metadata
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []

        # Generate query embedding
        try:
            query_embedding = self.embedding_service.get_embedding(query)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return []

        # Search FAISS index
        search_results = self.vector_db_service.search_with_scores(
            query_embedding,
            k=top_k * 3,  # Get more results for filtering
            score_threshold=score_threshold,
        )

        if not search_results:
            logger.info(f"No results found for query: {query[:50]}...")
            return []

        # Get document details from database
        results = []
        with SessionLocal() as db:
            for result in search_results:
                metadata = result.get("metadata", {})
                chunk_id = metadata.get("chunk_id")
                doc_id = metadata.get("doc_id")

                if not chunk_id and not doc_id:
                    continue

                # Query document chunk and parent document
                doc_result = self._get_document_details(
                    db=db,
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    doc_type=doc_type,
                    include_deleted=include_deleted,
                    date_from=date_from,
                    date_to=date_to,
                )

                if doc_result:
                    doc_result["similarity_score"] = result["similarity_score"]
                    doc_result["distance"] = result["distance"]
                    doc_result["chunk_text"] = metadata.get("chunk_text", "")
                    results.append(doc_result)

                # Stop if we have enough results
                if len(results) >= top_k:
                    break

        logger.info(f"Search returned {len(results)} results for: {query[:50]}...")
        return results

    def _get_document_details(
        self,
        db: Session,
        chunk_id: int | None = None,
        doc_id: str | None = None,
        doc_type: str | None = None,
        include_deleted: bool = False,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict[str, Any] | None:
        """Get document details from database with filtering.

        Args:
            db: Database session
            chunk_id: DocumentChunk ID
            doc_id: Document doc_id
            doc_type: Filter by document type
            include_deleted: Include deleted documents
            date_from: Filter by update date (from)
            date_to: Filter by update date (to)

        Returns:
            Document details dictionary or None
        """
        # Build query
        if chunk_id:
            # Query via chunk
            chunk = db.get(DocumentChunk, chunk_id)
            if not chunk:
                return None
            document = chunk.document
        elif doc_id:
            # Query via doc_id
            stmt = select(Document).where(Document.doc_id == doc_id)
            document = db.execute(stmt).scalar_one_or_none()
            if not document:
                return None
            chunk = None
        else:
            return None

        # Apply filters
        if not include_deleted and document.deleted:
            return None

        if doc_type and document.doc_type != doc_type:
            return None

        if date_from and document.updated_at < date_from:
            return None

        if date_to and document.updated_at > date_to:
            return None

        # Build result
        return {
            "doc_id": document.doc_id,
            "doc_type": document.doc_type,
            "title": document.title,
            "url": document.url,
            "content": document.content[:500] if document.content else "",  # Truncate
            "author": document.author,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
            "chunk_index": chunk.chunk_index if chunk else None,
            "chunk_id": chunk.id if chunk else None,
        }

    def search_by_doc_type(
        self,
        query: str,
        doc_type: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Search documents filtered by type.

        Args:
            query: Search query
            doc_type: 'jira' or 'confluence'
            top_k: Number of results

        Returns:
            Filtered search results
        """
        return self.search_documents(
            query=query,
            top_k=top_k,
            doc_type=doc_type,
        )

    def search_jira(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search Jira issues only."""
        return self.search_by_doc_type(query, "jira", top_k)

    def search_confluence(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search Confluence pages only."""
        return self.search_by_doc_type(query, "confluence", top_k)

    def get_similar_documents(
        self,
        doc_id: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Find documents similar to a given document.

        Args:
            doc_id: Source document ID
            top_k: Number of similar documents to return

        Returns:
            List of similar documents
        """
        with SessionLocal() as db:
            # Get source document
            stmt = select(Document).where(Document.doc_id == doc_id)
            document = db.execute(stmt).scalar_one_or_none()

            if not document:
                logger.warning(f"Document not found: {doc_id}")
                return []

            # Use document content as query
            query_text = f"{document.title} {document.content[:1000]}"

        # Search for similar documents, excluding the source
        results = self.search_documents(query_text, top_k=top_k + 1)

        # Filter out the source document
        return [r for r in results if r["doc_id"] != doc_id][:top_k]

    def add_document_to_index(
        self,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> list[int]:
        """Add a document's chunks to the FAISS index.

        Args:
            document: Document metadata
            chunks: List of chunk dictionaries with 'chunk_text' and 'embedding'

        Returns:
            List of assigned FAISS index IDs
        """
        vectors = []
        metadata_list = []

        for chunk in chunks:
            if "embedding" not in chunk:
                # Generate embedding if not present
                embedding = self.embedding_service.get_embedding(chunk["chunk_text"])
                chunk["embedding"] = embedding

            vectors.append(chunk["embedding"])
            metadata_list.append({
                "doc_id": document.get("doc_id"),
                "chunk_id": chunk.get("chunk_id"),
                "chunk_index": chunk.get("chunk_index"),
                "chunk_text": chunk.get("chunk_text", "")[:200],  # Store truncated text
            })

        # Add to FAISS index
        index_ids = self.vector_db_service.add_vectors(vectors, metadata_list)

        logger.info(
            f"Added {len(index_ids)} chunks for document {document.get('doc_id')} "
            "to FAISS index"
        )
        return index_ids

    def save_index(self, filepath: str | None = None) -> None:
        """Save the FAISS index to file.

        Args:
            filepath: Path to save (uses default if not specified)
        """
        save_path = filepath or self.vector_db_path
        if not save_path:
            raise ValueError("No filepath specified for saving index")

        self.vector_db_service.save_index(save_path)
        logger.info(f"Saved FAISS index to {save_path}")

    def load_index(self, filepath: str | None = None) -> None:
        """Load the FAISS index from file.

        Args:
            filepath: Path to load (uses default if not specified)
        """
        load_path = filepath or self.vector_db_path
        if not load_path:
            raise ValueError("No filepath specified for loading index")

        self.vector_db_service.load_index(load_path)
        self.vector_db_path = load_path
        logger.info(f"Loaded FAISS index from {load_path}")

    def get_index_stats(self) -> dict[str, Any]:
        """Get statistics about the FAISS index.

        Returns:
            Index statistics dictionary
        """
        return self.vector_db_service.get_stats()
