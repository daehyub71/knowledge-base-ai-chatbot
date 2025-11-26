"""Chat API endpoint for the Knowledge Base AI Chatbot."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.chat import ChatHistory
from app.schemas.chat import (
    AnalyzedQueryResponse,
    ChatRequest,
    ChatResponse,
    Source,
)
from app.core.workflow import run_workflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


def _convert_sources(search_results: list[dict[str, Any]]) -> list[Source]:
    """Convert search results to Source schema objects."""
    sources = []
    for result in search_results:
        source = Source(
            doc_id=result.get("doc_id", ""),
            doc_type=result.get("doc_type", "confluence"),
            title=result.get("title", "Untitled"),
            url=result.get("url"),
            score=result.get("score", 0.0),
            snippet=result.get("content", "")[:200] if result.get("content") else None,
        )
        sources.append(source)
    return sources


def _convert_analyzed_query(analyzed: dict[str, Any] | None) -> AnalyzedQueryResponse | None:
    """Convert analyzed query dict to schema object."""
    if not analyzed:
        return None
    return AnalyzedQueryResponse(
        intent=analyzed.get("intent", "unknown"),
        keywords=analyzed.get("keywords", []),
        filters=analyzed.get("filters", {}),
    )


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Process a chat query and return AI-generated response.

    This endpoint:
    1. Analyzes the user query
    2. Searches for relevant documents in the knowledge base
    3. Generates a response using RAG or falls back to general LLM knowledge
    4. Saves the chat history to the database
    5. Returns the formatted response with sources

    Args:
        request: ChatRequest containing the user's query and optional session_id
        db: Database session

    Returns:
        ChatResponse with the AI response, sources, and metadata
    """
    logger.info(f"Received chat request: {request.query[:50]}...")

    # Generate session_id if not provided
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # Run the LangGraph workflow
        result = run_workflow(request.query)

        # Extract results
        response_text = result.get("response", "")
        response_type = result.get("response_type", "error")
        search_results = result.get("sources", [])
        relevance_decision = result.get("relevance_decision")
        analyzed_query = result.get("analyzed_query")
        error = result.get("error")

        # Convert to schema objects
        sources = _convert_sources(search_results)
        analyzed_query_response = _convert_analyzed_query(analyzed_query)

        # Save to chat history
        chat_history = ChatHistory(
            session_id=session_id,
            user_query=request.query,
            response=response_text,
            response_type=response_type,
            source_documents=[s.model_dump() for s in sources],
            relevance_score=sources[0].score if sources else None,
        )
        db.add(chat_history)
        db.commit()
        db.refresh(chat_history)

        logger.info(
            f"Chat completed: session={session_id}, "
            f"type={response_type}, sources={len(sources)}"
        )

        return ChatResponse(
            response=response_text,
            response_type=response_type,
            sources=sources,
            relevance_decision=relevance_decision,
            analyzed_query=analyzed_query_response,
            session_id=session_id,
            error=error,
        )

    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}",
        )
