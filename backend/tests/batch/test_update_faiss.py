"""Tests for batch update_faiss module."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from batch.update_faiss import (
    get_chunks_without_embeddings,
    DEFAULT_FAISS_INDEX_PATH,
)


class TestGetChunksWithoutEmbeddings:
    """Test cases for get_chunks_without_embeddings function."""

    def test_returns_chunks_without_faiss_id(self):
        """Test returns chunks without FAISS index ID."""
        mock_db = MagicMock()

        mock_chunks = [
            MagicMock(id=1, chunk_text="Text 1"),
            MagicMock(id=2, chunk_text="Text 2"),
        ]
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = mock_chunks

        result = get_chunks_without_embeddings(mock_db)

        assert len(result) == 2


class TestUpdateFaissIndex:
    """Test cases for update_faiss_index function."""

    @patch("batch.update_faiss.get_chunks_without_embeddings")
    @patch("batch.update_faiss.get_deleted_chunk_ids")
    @patch("batch.update_faiss.VectorDBService")
    @patch("batch.update_faiss.EmbeddingService")
    def test_updates_index_successfully(
        self,
        mock_embedding_class,
        mock_vector_class,
        mock_get_deleted,
        mock_get_chunks,
    ):
        """Test updates FAISS index successfully."""
        from batch.update_faiss import update_faiss_index

        mock_db = MagicMock()

        mock_get_deleted.return_value = []
        mock_get_chunks.return_value = []

        mock_vector = MagicMock()
        mock_vector.index = MagicMock()
        mock_vector.index.ntotal = 10
        mock_vector_class.return_value = mock_vector

        result = update_faiss_index(mock_db)

        assert result["errors"] == 0
        assert "total_vectors" in result

    @patch("batch.update_faiss.get_chunks_without_embeddings")
    @patch("batch.update_faiss.get_deleted_chunk_ids")
    @patch("batch.update_faiss.VectorDBService")
    @patch("batch.update_faiss.EmbeddingService")
    def test_handles_deleted_chunks(
        self,
        mock_embedding_class,
        mock_vector_class,
        mock_get_deleted,
        mock_get_chunks,
    ):
        """Test handles deleted chunks by rebuilding index."""
        from batch.update_faiss import update_faiss_index

        mock_db = MagicMock()

        # There are deleted chunks
        mock_get_deleted.return_value = [1, 2, 3]
        mock_get_chunks.return_value = []

        mock_vector = MagicMock()
        mock_vector.index = MagicMock()
        mock_vector.index.ntotal = 5
        mock_vector_class.return_value = mock_vector

        # Mock the query for active chunks
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = update_faiss_index(mock_db)

        assert result["vectors_removed"] >= 0


class TestRebuildFaissIndex:
    """Test cases for rebuild_faiss_index function."""

    @patch("batch.update_faiss.EmbeddingService")
    @patch("batch.update_faiss.VectorDBService")
    def test_handles_empty_database(
        self,
        mock_vector_class,
        mock_embedding_class,
    ):
        """Test handles empty database gracefully."""
        from batch.update_faiss import rebuild_faiss_index

        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        mock_vector = MagicMock()
        mock_vector.index = MagicMock()
        mock_vector.index.ntotal = 0
        mock_vector_class.return_value = mock_vector

        result = rebuild_faiss_index(mock_db)

        assert result["vectors_added"] == 0
        assert result["total_vectors"] == 0


class TestConstants:
    """Test cases for module constants."""

    def test_default_faiss_path_exists(self):
        """Test default FAISS path is a valid path."""
        assert DEFAULT_FAISS_INDEX_PATH is not None
        assert isinstance(DEFAULT_FAISS_INDEX_PATH, Path)
