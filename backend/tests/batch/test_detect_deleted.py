"""Tests for batch detect_deleted module."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from batch.detect_deleted import (
    get_jira_document_ids,
    get_confluence_document_ids,
    get_db_document_ids,
    detect_and_mark_deleted,
)


class TestGetJiraDocumentIds:
    """Test cases for get_jira_document_ids function."""

    @patch("batch.detect_deleted.settings")
    def test_returns_empty_when_not_configured(self, mock_settings):
        """Test returns empty set when Jira is not configured."""
        mock_settings.jira_url = None
        mock_settings.jira_api_token = None

        result = get_jira_document_ids()

        assert result == set()

    @patch("batch.detect_deleted.JiraClient")
    @patch("batch.detect_deleted.settings")
    def test_returns_document_ids(self, mock_settings, mock_jira_client_class):
        """Test returns document IDs from Jira."""
        mock_settings.jira_url = "http://localhost:8080"
        mock_settings.jira_api_token = "token"
        mock_settings.jira_project_key = "TEST"

        mock_client = MagicMock()
        mock_client.get_issues_updated_since.return_value = [
            {"key": "TEST-1"},
            {"key": "TEST-2"},
            {"key": "TEST-3"},
        ]
        mock_jira_client_class.return_value = mock_client

        result = get_jira_document_ids()

        assert result == {"jira-TEST-1", "jira-TEST-2", "jira-TEST-3"}

    @patch("batch.detect_deleted.JiraClient")
    @patch("batch.detect_deleted.settings")
    def test_handles_exception(self, mock_settings, mock_jira_client_class):
        """Test handles exception gracefully."""
        mock_settings.jira_url = "http://localhost:8080"
        mock_settings.jira_api_token = "token"
        mock_settings.jira_project_key = "TEST"

        mock_jira_client_class.side_effect = Exception("Connection error")

        result = get_jira_document_ids()

        assert result == set()


class TestGetConfluenceDocumentIds:
    """Test cases for get_confluence_document_ids function."""

    @patch("batch.detect_deleted.settings")
    def test_returns_empty_when_not_configured(self, mock_settings):
        """Test returns empty set when Confluence is not configured."""
        mock_settings.confluence_url = None

        result = get_confluence_document_ids()

        assert result == set()

    @patch("batch.detect_deleted.ConfluenceClient")
    @patch("batch.detect_deleted.settings")
    def test_returns_document_ids_from_cql_format(self, mock_settings, mock_confluence_client_class):
        """Test returns document IDs from CQL format response."""
        mock_settings.confluence_url = "http://localhost:8090"
        mock_settings.confluence_space_key = "TES"

        mock_client = MagicMock()
        # CQL format has content.id structure
        mock_client.get_pages_updated_since.return_value = [
            {"content": {"id": "123"}},
            {"content": {"id": "456"}},
            {"content": {"id": "789"}},
        ]
        mock_confluence_client_class.return_value = mock_client

        result = get_confluence_document_ids()

        assert result == {"confluence-123", "confluence-456", "confluence-789"}

    @patch("batch.detect_deleted.ConfluenceClient")
    @patch("batch.detect_deleted.settings")
    def test_returns_document_ids_from_direct_format(self, mock_settings, mock_confluence_client_class):
        """Test returns document IDs from direct format response."""
        mock_settings.confluence_url = "http://localhost:8090"
        mock_settings.confluence_space_key = "TES"

        mock_client = MagicMock()
        # Direct format has id at top level
        mock_client.get_pages_updated_since.return_value = [
            {"id": "123"},
            {"id": "456"},
        ]
        mock_confluence_client_class.return_value = mock_client

        result = get_confluence_document_ids()

        assert result == {"confluence-123", "confluence-456"}


class TestGetDbDocumentIds:
    """Test cases for get_db_document_ids function."""

    def test_returns_non_deleted_document_ids(self):
        """Test returns only non-deleted document IDs."""
        mock_db = MagicMock()

        # Create mock result objects
        mock_results = [
            MagicMock(doc_id="jira-TEST-1"),
            MagicMock(doc_id="jira-TEST-2"),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query

        result = get_db_document_ids(mock_db, "jira")

        assert result == {"jira-TEST-1", "jira-TEST-2"}


class TestDetectAndMarkDeleted:
    """Test cases for detect_and_mark_deleted function."""

    @patch("batch.detect_deleted.get_confluence_document_ids")
    @patch("batch.detect_deleted.get_jira_document_ids")
    @patch("batch.detect_deleted.get_db_document_ids")
    def test_marks_deleted_documents(
        self,
        mock_get_db_ids,
        mock_get_jira_ids,
        mock_get_confluence_ids,
    ):
        """Test marks deleted documents correctly."""
        # DB has documents that don't exist in source anymore
        mock_get_db_ids.side_effect = [
            {"jira-TEST-1", "jira-TEST-2", "jira-TEST-3"},  # Jira DB IDs
            {"confluence-1", "confluence-2"},  # Confluence DB IDs
        ]

        # Source only has some of the documents
        mock_get_jira_ids.return_value = {"jira-TEST-1"}  # TEST-2 and TEST-3 deleted
        mock_get_confluence_ids.return_value = {"confluence-1"}  # confluence-2 deleted

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = None

        result = detect_and_mark_deleted(mock_db, "all")

        assert result["jira_deleted"] == 2
        assert result["confluence_deleted"] == 1
        assert result["total_deleted"] == 3
        mock_db.commit.assert_called_once()

    @patch("batch.detect_deleted.get_jira_document_ids")
    @patch("batch.detect_deleted.get_db_document_ids")
    def test_no_deletions_when_all_exist(
        self,
        mock_get_db_ids,
        mock_get_jira_ids,
    ):
        """Test no deletions when all documents exist."""
        # All documents exist in both DB and source
        mock_get_db_ids.return_value = {"jira-TEST-1", "jira-TEST-2"}
        mock_get_jira_ids.return_value = {"jira-TEST-1", "jira-TEST-2"}

        mock_db = MagicMock()

        result = detect_and_mark_deleted(mock_db, "jira")

        assert result["jira_deleted"] == 0
        assert result["total_deleted"] == 0

    @patch("batch.detect_deleted.get_jira_document_ids")
    @patch("batch.detect_deleted.get_db_document_ids")
    def test_handles_empty_db(
        self,
        mock_get_db_ids,
        mock_get_jira_ids,
    ):
        """Test handles empty database."""
        mock_get_db_ids.return_value = set()
        mock_get_jira_ids.return_value = {"jira-TEST-1"}

        mock_db = MagicMock()

        result = detect_and_mark_deleted(mock_db, "jira")

        assert result["jira_deleted"] == 0
        assert result["total_deleted"] == 0
