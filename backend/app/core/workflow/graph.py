"""LangGraph workflow definition for the chatbot."""

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from app.core.agents import (
    llm_fallback,
    query_analyzer,
    rag_responder,
    rag_searcher,
    relevance_checker,
    response_formatter,
)
from app.core.agents.relevance_checker import should_use_rag
from app.core.workflow.state import ChatState, create_initial_state

logger = logging.getLogger(__name__)


def create_workflow() -> StateGraph:
    """Create the LangGraph workflow for the chatbot.

    The workflow follows this pattern:
    1. query_analyzer: Parse and analyze the user query
    2. rag_searcher: Search for relevant documents in vector DB
    3. relevance_checker: Assess if results are relevant
    4. rag_responder OR llm_fallback: Generate response based on relevance
    5. response_formatter: Format the final response with sources

    Returns:
        Compiled StateGraph workflow
    """
    # Create the graph with ChatState
    workflow = StateGraph(ChatState)

    # Add nodes (agents)
    workflow.add_node("query_analyzer", query_analyzer)
    workflow.add_node("rag_searcher", rag_searcher)
    workflow.add_node("relevance_checker", relevance_checker)
    workflow.add_node("rag_responder", rag_responder)
    workflow.add_node("llm_fallback", llm_fallback)
    workflow.add_node("response_formatter", response_formatter)

    # Define edges
    # Entry point -> Query Analyzer
    workflow.set_entry_point("query_analyzer")

    # Query Analyzer -> RAG Searcher
    workflow.add_edge("query_analyzer", "rag_searcher")

    # RAG Searcher -> Relevance Checker
    workflow.add_edge("rag_searcher", "relevance_checker")

    # Relevance Checker -> Conditional routing
    workflow.add_conditional_edges(
        "relevance_checker",
        should_use_rag,
        {
            "rag_responder": "rag_responder",
            "llm_fallback": "llm_fallback",
        }
    )

    # RAG Responder -> Response Formatter
    workflow.add_edge("rag_responder", "response_formatter")

    # LLM Fallback -> Response Formatter
    workflow.add_edge("llm_fallback", "response_formatter")

    # Response Formatter -> END
    workflow.add_edge("response_formatter", END)

    return workflow


# Compile the workflow
_workflow = create_workflow()
app = _workflow.compile()


def run_workflow(user_query: str) -> dict[str, Any]:
    """Run the chatbot workflow with a user query.

    Args:
        user_query: The user's input query

    Returns:
        Dictionary containing:
        - response: The formatted response text
        - response_type: "rag" or "llm_fallback"
        - sources: List of source documents (if any)
        - error: Error message (if any)
    """
    # Create initial state
    initial_state = create_initial_state(user_query)

    logger.info(f"Running workflow for query: {user_query[:50]}...")

    try:
        # Run the workflow
        final_state = app.invoke(initial_state)

        # Extract results
        result = {
            "response": final_state.get("response", ""),
            "response_type": final_state.get("response_type", "unknown"),
            "sources": final_state.get("sources", []),
            "relevance_decision": final_state.get("relevance_decision"),
            "analyzed_query": final_state.get("analyzed_query"),
            "error": final_state.get("error"),
        }

        logger.info(
            f"Workflow completed: type={result['response_type']}, "
            f"sources={len(result['sources'])}"
        )

        return result

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        return {
            "response": "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.",
            "response_type": "error",
            "sources": [],
            "error": str(e),
        }


def get_workflow_graph() -> StateGraph:
    """Get the workflow graph for visualization.

    Returns:
        The compiled StateGraph
    """
    return app
