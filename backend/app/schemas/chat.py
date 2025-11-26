"""Pydantic schemas for chat API endpoints."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    query: str = Field(
        ...,
        description="User's question or query",
        min_length=1,
        max_length=2000,
        examples=["Confluence API 사용법을 알려주세요"],
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session ID for conversation continuity",
    )


class Source(BaseModel):
    """Schema for a document source in the response."""

    doc_id: str = Field(
        ...,
        description="Unique document identifier",
        examples=["confluence-12345"],
    )
    doc_type: Literal["jira", "confluence"] = Field(
        ...,
        description="Type of the source document",
    )
    title: str = Field(
        ...,
        description="Document title",
        examples=["API 가이드라인"],
    )
    url: str | None = Field(
        default=None,
        description="URL to the original document",
    )
    score: float = Field(
        default=0.0,
        description="Relevance score (0-1)",
        ge=0.0,
        le=1.0,
    )
    snippet: str | None = Field(
        default=None,
        description="Relevant text snippet from the document",
    )


class AnalyzedQueryResponse(BaseModel):
    """Schema for analyzed query details in the response."""

    intent: str = Field(
        ...,
        description="Detected intent of the query",
        examples=["information_seeking"],
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Extracted keywords from the query",
    )
    filters: dict[str, str] = Field(
        default_factory=dict,
        description="Extracted filters (e.g., doc_type, date)",
    )


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""

    response: str = Field(
        ...,
        description="The chatbot's response text",
    )
    response_type: Literal["rag", "llm_fallback", "error"] = Field(
        ...,
        description=(
            "Type of response: 'rag' for document-based, "
            "'llm_fallback' for general knowledge, 'error' for failures"
        ),
    )
    sources: list[Source] = Field(
        default_factory=list,
        description="List of source documents used in the response",
    )
    relevance_decision: Literal["relevant", "irrelevant"] | None = Field(
        default=None,
        description="Whether relevant documents were found",
    )
    analyzed_query: AnalyzedQueryResponse | None = Field(
        default=None,
        description="Details of how the query was analyzed",
    )
    session_id: str | None = Field(
        default=None,
        description="Session ID for conversation continuity",
    )
    error: str | None = Field(
        default=None,
        description="Error message if response_type is 'error'",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "response": "Confluence API를 사용하려면...",
                    "response_type": "rag",
                    "sources": [
                        {
                            "doc_id": "confluence-12345",
                            "doc_type": "confluence",
                            "title": "Confluence API 가이드",
                            "url": "http://confluence.example.com/pages/12345",
                            "score": 0.85,
                            "snippet": "REST API를 통해...",
                        }
                    ],
                    "relevance_decision": "relevant",
                    "analyzed_query": {
                        "intent": "information_seeking",
                        "keywords": ["Confluence", "API", "사용법"],
                        "filters": {},
                    },
                    "session_id": "abc123",
                    "error": None,
                }
            ]
        }
    }
