"""Custom exceptions for the Knowledge Base AI Chatbot."""

from fastapi import HTTPException, status


class KnowledgeBaseException(Exception):
    """Base exception for Knowledge Base AI Chatbot."""

    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


class DocumentNotFoundError(KnowledgeBaseException):
    """Raised when a document is not found."""

    def __init__(self, doc_id: str | None = None):
        message = f"Document not found: {doc_id}" if doc_id else "Document not found"
        super().__init__(message)


class ChatHistoryNotFoundError(KnowledgeBaseException):
    """Raised when chat history is not found."""

    def __init__(self, session_id: str | None = None):
        message = (
            f"Chat history not found for session: {session_id}"
            if session_id
            else "Chat history not found"
        )
        super().__init__(message)


class VectorDBNotLoadedError(KnowledgeBaseException):
    """Raised when FAISS index is not loaded."""

    def __init__(self):
        super().__init__("Vector database (FAISS index) is not loaded")


class EmbeddingServiceError(KnowledgeBaseException):
    """Raised when embedding service fails."""

    def __init__(self, message: str = "Embedding service error"):
        super().__init__(message)


class LLMServiceError(KnowledgeBaseException):
    """Raised when LLM service fails."""

    def __init__(self, message: str = "LLM service error"):
        super().__init__(message)


class WorkflowExecutionError(KnowledgeBaseException):
    """Raised when workflow execution fails."""

    def __init__(self, message: str = "Workflow execution error"):
        super().__init__(message)


class DatabaseConnectionError(KnowledgeBaseException):
    """Raised when database connection fails."""

    def __init__(self, message: str = "Database connection error"):
        super().__init__(message)


class ExternalAPIError(KnowledgeBaseException):
    """Raised when external API (Jira/Confluence) fails."""

    def __init__(self, service: str, message: str = ""):
        full_message = f"{service} API error: {message}" if message else f"{service} API error"
        super().__init__(full_message)


# HTTP Exception helpers
def raise_not_found(resource: str, identifier: str | None = None) -> None:
    """Raise HTTP 404 Not Found exception."""
    detail = f"{resource} not found"
    if identifier:
        detail = f"{resource} '{identifier}' not found"
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def raise_bad_request(message: str) -> None:
    """Raise HTTP 400 Bad Request exception."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def raise_internal_error(message: str = "Internal server error") -> None:
    """Raise HTTP 500 Internal Server Error exception."""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message,
    )


def raise_service_unavailable(message: str = "Service temporarily unavailable") -> None:
    """Raise HTTP 503 Service Unavailable exception."""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=message,
    )
