"""Batch processing module for Knowledge Base AI Chatbot.

This module contains batch jobs for:
- Incremental synchronization from Jira and Confluence
- Deleted document detection
- Text chunking and embedding
- FAISS index updates
- Retry logic with exponential backoff
"""

from batch.sync_jira import sync_jira_incremental
from batch.sync_confluence import sync_confluence_incremental
from batch.detect_deleted import detect_and_mark_deleted
from batch.process_chunks import process_document_chunks
from batch.update_faiss import update_faiss_index, rebuild_faiss_index
from batch.retry_handler import retry_with_backoff, RetryError, RetryContext

__all__ = [
    "sync_jira_incremental",
    "sync_confluence_incremental",
    "detect_and_mark_deleted",
    "process_document_chunks",
    "update_faiss_index",
    "rebuild_faiss_index",
    "retry_with_backoff",
    "RetryError",
    "RetryContext",
]
