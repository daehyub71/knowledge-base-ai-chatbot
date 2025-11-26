"""Relevance Checker agent for assessing search result relevance."""

import logging

from app.core.services import LLMService
from app.core.workflow.state import ChatState

logger = logging.getLogger(__name__)

# Minimum similarity score threshold
SIMILARITY_THRESHOLD = 0.35  # Adjusted based on testing

# Minimum number of results to consider relevant
MIN_RESULTS_FOR_RELEVANCE = 1


def relevance_checker(state: ChatState) -> ChatState:
    """Check if search results are relevant to the user query.

    This agent performs two-level relevance checking:
    1. Similarity score threshold check
    2. LLM-based semantic relevance verification

    Args:
        state: Current chat state with search_results

    Returns:
        Updated state with relevance_decision populated
    """
    search_results = state.get("search_results", [])
    user_query = state.get("user_query", "")

    # Check 1: Do we have any results?
    if not search_results:
        logger.info("No search results - marking as irrelevant")
        state["relevance_decision"] = "irrelevant"
        return state

    # Check 2: Similarity score threshold
    top_score = search_results[0].get("similarity_score", 0.0) if search_results else 0.0

    if top_score < SIMILARITY_THRESHOLD:
        logger.info(
            f"Top similarity score {top_score:.4f} below threshold {SIMILARITY_THRESHOLD} "
            "- marking as irrelevant"
        )
        state["relevance_decision"] = "irrelevant"
        return state

    # Check 3: LLM-based semantic relevance check
    try:
        llm = LLMService()
        is_relevant = llm.check_relevance(user_query, search_results[:3])

        if is_relevant:
            logger.info("LLM determined search results are relevant")
            state["relevance_decision"] = "relevant"
        else:
            logger.info("LLM determined search results are irrelevant")
            state["relevance_decision"] = "irrelevant"

    except Exception as e:
        logger.error(f"LLM relevance check failed: {e}")
        # Fallback: If we have results above threshold, consider them relevant
        if top_score >= SIMILARITY_THRESHOLD:
            logger.info("Fallback: using threshold check - marking as relevant")
            state["relevance_decision"] = "relevant"
        else:
            state["relevance_decision"] = "irrelevant"

    return state


def should_use_rag(state: ChatState) -> str:
    """Routing function for conditional edge in LangGraph.

    Args:
        state: Current chat state with relevance_decision

    Returns:
        "rag_responder" if relevant, "llm_fallback" otherwise
    """
    relevance = state.get("relevance_decision", "irrelevant")

    if relevance == "relevant":
        return "rag_responder"
    else:
        return "llm_fallback"
