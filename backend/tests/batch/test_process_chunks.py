"""Tests for batch process_chunks module."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from batch.process_chunks import (
    delete_existing_chunks,
    EMBEDDING_BATCH_SIZE,
)


class TestDeleteExistingChunks:
    """Test cases for delete_existing_chunks function."""

    def test_deletes_chunks_for_document(self):
        """Test deletes existing chunks for document."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.delete.return_value = 5
        mock_db.query.return_value.filter.return_value = mock_query

        result = delete_existing_chunks(mock_db, 1)

        assert result == 5
        mock_query.delete.assert_called_once()

    def test_returns_zero_when_no_chunks(self):
        """Test returns zero when no chunks exist."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.delete.return_value = 0
        mock_db.query.return_value.filter.return_value = mock_query

        result = delete_existing_chunks(mock_db, 999)

        assert result == 0


class TestConstants:
    """Test cases for module constants."""

    def test_embedding_batch_size_is_reasonable(self):
        """Test embedding batch size is reasonable."""
        assert 10 <= EMBEDDING_BATCH_SIZE <= 200
