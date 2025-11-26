"""Pydantic schemas for statistics API endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentStats(BaseModel):
    """Statistics for documents in the knowledge base."""

    total_documents: int = Field(
        ...,
        description="Total number of documents",
        ge=0,
    )
    jira_documents: int = Field(
        ...,
        description="Number of Jira documents",
        ge=0,
    )
    confluence_documents: int = Field(
        ...,
        description="Number of Confluence documents",
        ge=0,
    )
    active_documents: int = Field(
        ...,
        description="Number of active (not deleted) documents",
        ge=0,
    )
    deleted_documents: int = Field(
        ...,
        description="Number of soft-deleted documents",
        ge=0,
    )
    total_chunks: int = Field(
        ...,
        description="Total number of document chunks",
        ge=0,
    )
    vector_count: int = Field(
        ...,
        description="Number of vectors in FAISS index",
        ge=0,
    )


class SyncStats(BaseModel):
    """Statistics for the last synchronization."""

    last_sync_at: datetime | None = Field(
        default=None,
        description="Timestamp of the last sync",
    )
    last_sync_status: str | None = Field(
        default=None,
        description="Status of the last sync (completed, failed, etc.)",
    )
    documents_added: int = Field(
        default=0,
        description="Number of documents added in last sync",
        ge=0,
    )
    documents_updated: int = Field(
        default=0,
        description="Number of documents updated in last sync",
        ge=0,
    )
    documents_deleted: int = Field(
        default=0,
        description="Number of documents deleted in last sync",
        ge=0,
    )


class ChatStats(BaseModel):
    """Statistics for chat interactions."""

    total_sessions: int = Field(
        default=0,
        description="Total number of chat sessions",
        ge=0,
    )
    total_messages: int = Field(
        default=0,
        description="Total number of chat messages",
        ge=0,
    )
    rag_responses: int = Field(
        default=0,
        description="Number of RAG-based responses",
        ge=0,
    )
    fallback_responses: int = Field(
        default=0,
        description="Number of LLM fallback responses",
        ge=0,
    )
    positive_feedback: int = Field(
        default=0,
        description="Number of helpful ratings",
        ge=0,
    )
    negative_feedback: int = Field(
        default=0,
        description="Number of not helpful ratings",
        ge=0,
    )


class StatsResponse(BaseModel):
    """Response schema for statistics endpoint."""

    documents: DocumentStats = Field(
        ...,
        description="Document statistics",
    )
    sync: SyncStats = Field(
        ...,
        description="Synchronization statistics",
    )
    chat: ChatStats = Field(
        default_factory=ChatStats,
        description="Chat interaction statistics",
    )
    status: str = Field(
        default="healthy",
        description="Overall system status",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when stats were generated",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "documents": {
                        "total_documents": 150,
                        "jira_documents": 80,
                        "confluence_documents": 70,
                        "active_documents": 145,
                        "deleted_documents": 5,
                        "total_chunks": 500,
                        "vector_count": 500,
                    },
                    "sync": {
                        "last_sync_at": "2024-01-15T10:00:00",
                        "last_sync_status": "completed",
                        "documents_added": 10,
                        "documents_updated": 5,
                        "documents_deleted": 2,
                    },
                    "chat": {
                        "total_sessions": 100,
                        "total_messages": 500,
                        "rag_responses": 350,
                        "fallback_responses": 150,
                        "positive_feedback": 80,
                        "negative_feedback": 20,
                    },
                    "status": "healthy",
                    "updated_at": "2024-01-15T10:30:00",
                }
            ]
        }
    }
