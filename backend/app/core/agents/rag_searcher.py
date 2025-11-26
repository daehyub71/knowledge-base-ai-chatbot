"""RAG Searcher agent for retrieving relevant documents."""

import logging
from pathlib import Path

from app.core.services import RAGService
from app.core.workflow.state import ChatState, SearchResult

logger = logging.getLogger(__name__)

# Default vector DB path
DEFAULT_INDEX_PATH = Path(__file__).parent.parent.parent.parent / "data" / "vector_db" / "faiss.index"


def rag_searcher(state: ChatState) -> ChatState:
    """Search for relevant documents using RAG.

    This agent uses the analyzed query to search the vector database
    and retrieve relevant documents from Jira and Confluence.

    Args:
        state: Current chat state with analyzed_query

    Returns:
        Updated state with search_results populated
    """
    analyzed_query = state.get("analyzed_query")

    if not analyzed_query:
        logger.warning("No analyzed query provided to rag_searcher")
        state["search_results"] = []
        return state

    # Build search query from keywords or original query
    search_query = analyzed_query.get("original_query", "")
    if not search_query:
        keywords = analyzed_query.get("keywords", [])
        search_query = " ".join(keywords) if keywords else ""

    if not search_query.strip():
        logger.warning("Empty search query")
        state["search_results"] = []
        return state

    try:
        # Initialize RAG service with vector DB
        index_path = str(DEFAULT_INDEX_PATH)
        rag_service = RAGService(vector_db_path=index_path)

        # Extract filters from analyzed query
        doc_type_filter = analyzed_query.get("doc_type_filter")
        date_filter = analyzed_query.get("date_filter")

        # Parse date filter if present
        date_from = None
        date_to = None
        if date_filter:
            from datetime import datetime
            if date_filter.get("from"):
                try:
                    date_from = datetime.fromisoformat(date_filter["from"])
                except ValueError:
                    pass
            if date_filter.get("to"):
                try:
                    date_to = datetime.fromisoformat(date_filter["to"])
                except ValueError:
                    pass

        # Search documents
        results = rag_service.search_documents(
            query=search_query,
            top_k=5,
            score_threshold=0.3,  # Adjusted threshold based on testing
            doc_type=doc_type_filter if doc_type_filter != "all" else None,
            date_from=date_from,
            date_to=date_to,
        )

        # Convert to SearchResult format
        search_results = []
        for result in results:
            search_result = SearchResult(
                doc_id=result.get("doc_id", ""),
                doc_type=result.get("doc_type", "jira"),
                title=result.get("title", "Untitled"),
                url=result.get("url", ""),
                content=result.get("content", ""),
                chunk_text=result.get("chunk_text", ""),
                similarity_score=result.get("similarity_score", 0.0),
                author=result.get("author"),
                updated_at=result.get("updated_at"),
            )
            search_results.append(search_result)

        state["search_results"] = search_results
        logger.info(f"RAG search returned {len(search_results)} results for: {search_query[:50]}...")

    except FileNotFoundError:
        logger.error(f"FAISS index not found at {DEFAULT_INDEX_PATH}")
        state["search_results"] = []
        state["error"] = "Vector database not found. Please run build_vector_db.py first."

    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        state["search_results"] = []
        state["error"] = f"Search error: {str(e)}"

    return state
