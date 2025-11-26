"""Text chunking utilities using LangChain's RecursiveCharacterTextSplitter."""

import logging
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class TextSplitter:
    """Text splitter for chunking documents into smaller pieces."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: list[str] | None = None,
    ):
        """Initialize the text splitter.

        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Overlap between consecutive chunks
            separators: List of separators to use for splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Default separators for various document types
        if separators is None:
            separators = [
                "\n\n",  # Paragraph breaks
                "\n",    # Line breaks
                ". ",    # Sentence endings
                "! ",    # Exclamation
                "? ",    # Question
                "; ",    # Semicolon
                ", ",    # Comma
                " ",     # Space
                "",      # Character level
            ]

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False,
        )

        logger.info(
            f"TextSplitter initialized with chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}"
        )

    def split_text(self, text: str) -> list[str]:
        """Split text into chunks.

        Args:
            text: The text to split

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        chunks = self.splitter.split_text(text)
        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks

    def split_document(self, document: dict[str, Any]) -> list[dict[str, Any]]:
        """Split a document into chunks with metadata.

        Args:
            document: Document dictionary with 'content' and metadata fields

        Returns:
            List of chunk dictionaries with metadata
        """
        content = document.get("content", "")
        if not content or not content.strip():
            return []

        # Extract metadata
        doc_id = document.get("doc_id", "")
        doc_type = document.get("doc_type", "")
        title = document.get("title", "")
        url = document.get("url", "")
        author = document.get("author", "")
        created_at = document.get("created_at", "")
        updated_at = document.get("updated_at", "")
        metadata = document.get("metadata", {})

        # Split content into chunks
        text_chunks = self.split_text(content)

        # Create chunk dictionaries with metadata
        chunks = []
        for idx, chunk_text in enumerate(text_chunks):
            chunk = {
                "doc_id": doc_id,
                "doc_type": doc_type,
                "chunk_index": idx,
                "chunk_text": chunk_text,
                "chunk_size": len(chunk_text),
                "total_chunks": len(text_chunks),
                "title": title,
                "url": url,
                "author": author,
                "created_at": created_at,
                "updated_at": updated_at,
                "metadata": metadata,
            }
            chunks.append(chunk)

        logger.debug(
            f"Document '{doc_id}' split into {len(chunks)} chunks "
            f"(avg size: {sum(len(c['chunk_text']) for c in chunks) // max(len(chunks), 1)} chars)"
        )
        return chunks


def chunk_documents(
    documents: list[dict[str, Any]],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict[str, Any]]:
    """Chunk multiple documents into smaller pieces.

    Args:
        documents: List of document dictionaries
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Overlap between consecutive chunks

    Returns:
        List of chunk dictionaries with metadata
    """
    splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    all_chunks = []
    for doc in documents:
        chunks = splitter.split_document(doc)
        all_chunks.extend(chunks)

    logger.info(
        f"Chunked {len(documents)} documents into {len(all_chunks)} chunks "
        f"(chunk_size={chunk_size}, overlap={chunk_overlap})"
    )
    return all_chunks
