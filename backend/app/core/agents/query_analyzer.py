"""Query Analyzer agent for parsing and analyzing user queries."""

import logging

from app.core.services import LLMService
from app.core.workflow.state import AnalyzedQuery, ChatState

logger = logging.getLogger(__name__)

# System prompt for query analysis
QUERY_ANALYZER_PROMPT = """You are a query analyzer for a knowledge base chatbot.
Your job is to analyze user queries and extract structured information.

Analyze the user's query and extract:
1. intent: The user's intention
   - "search": Looking for specific information or documents
   - "question": Asking a specific question
   - "clarification": Asking for more details
   - "greeting": Greeting or small talk
   - "other": Other types of queries

2. keywords: Important keywords for searching (list of strings)
   - Extract key terms, concepts, and entities
   - Include both Korean and English terms if present

3. doc_type_filter: If the query specifically mentions document type
   - "jira": Mentions Jira issues, tickets, bugs, tasks
   - "confluence": Mentions Confluence pages, documents, wiki
   - null: No specific document type mentioned

4. date_filter: If the query mentions time constraints
   - {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"}
   - For "last week", "recent", etc. calculate appropriate dates
   - null: No time constraints mentioned

Respond ONLY with valid JSON, no markdown formatting."""


def query_analyzer(state: ChatState) -> ChatState:
    """Analyze user query and extract structured information.

    This agent parses the user's query to identify:
    - Intent (search, question, clarification, etc.)
    - Keywords for search
    - Document type filters
    - Date range filters

    Args:
        state: Current chat state with user_query

    Returns:
        Updated state with analyzed_query populated
    """
    user_query = state["user_query"]

    if not user_query or not user_query.strip():
        logger.warning("Empty query provided to query_analyzer")
        state["analyzed_query"] = AnalyzedQuery(
            original_query="",
            intent="other",
            keywords=[],
            doc_type_filter=None,
            date_filter=None,
        )
        return state

    try:
        llm = LLMService()
        analysis = llm.analyze_query(user_query)

        # Build analyzed query from LLM response
        analyzed_query = AnalyzedQuery(
            original_query=user_query,
            intent=analysis.get("intent", "question"),
            keywords=analysis.get("keywords", user_query.split()),
            doc_type_filter=analysis.get("doc_type_filter"),
            date_filter=analysis.get("date_filter"),
        )

        state["analyzed_query"] = analyzed_query
        logger.info(
            f"Query analyzed: intent={analyzed_query['intent']}, "
            f"keywords={analyzed_query['keywords']}, "
            f"doc_type={analyzed_query['doc_type_filter']}"
        )

    except Exception as e:
        logger.error(f"Query analysis failed: {e}")
        # Fallback to basic analysis
        state["analyzed_query"] = AnalyzedQuery(
            original_query=user_query,
            intent="question",
            keywords=user_query.split(),
            doc_type_filter=None,
            date_filter=None,
        )
        state["error"] = f"Query analysis error: {str(e)}"

    return state
