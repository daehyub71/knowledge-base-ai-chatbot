"""LangGraph state definitions for the chatbot workflow."""

from typing import Annotated, Any, Literal

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class SearchResult(TypedDict):
    """Individual search result from RAG."""

    doc_id: str
    doc_type: Literal["jira", "confluence"]
    title: str
    url: str
    content: str
    chunk_text: str
    similarity_score: float
    author: str | None
    updated_at: str | None


class AnalyzedQuery(TypedDict):
    """Analyzed query information."""

    original_query: str
    intent: str  # e.g., "search", "question", "clarification"
    keywords: list[str]
    doc_type_filter: Literal["jira", "confluence", "all"] | None
    date_filter: dict[str, str] | None  # {"from": "...", "to": "..."}


class Source(TypedDict):
    """Source reference for citations."""

    doc_id: str
    doc_type: Literal["jira", "confluence"]
    title: str
    url: str


class ChatState(TypedDict):
    """State definition for the chatbot LangGraph workflow.

    This state is passed between nodes in the graph and contains all
    information needed for the RAG pipeline and response generation.

    Attributes:
        user_query: The original user input query
        analyzed_query: Parsed query with intent, keywords, filters
        search_results: List of documents retrieved from RAG
        relevance_decision: Whether search results are relevant
        response: The final generated response
        response_type: Whether response came from RAG or LLM fallback
        sources: List of source documents cited in response
        messages: Conversation history (for multi-turn)
        error: Any error that occurred during processing
    """

    # User input
    user_query: str

    # Query analysis results
    analyzed_query: AnalyzedQuery | None

    # RAG search results
    search_results: list[SearchResult]

    # Relevance assessment
    relevance_decision: Literal["relevant", "irrelevant"] | None

    # Response generation
    response: str
    response_type: Literal["rag", "llm_fallback"] | None

    # Source citations
    sources: list[Source]

    # Conversation history (supports multi-turn with add_messages reducer)
    messages: Annotated[list[Any], add_messages]

    # Error handling
    error: str | None


# Initial state factory
def create_initial_state(user_query: str) -> ChatState:
    """Create an initial state with default values.

    Args:
        user_query: The user's input query

    Returns:
        ChatState with initialized default values
    """
    return ChatState(
        user_query=user_query,
        analyzed_query=None,
        search_results=[],
        relevance_decision=None,
        response="",
        response_type=None,
        sources=[],
        messages=[],
        error=None,
    )
