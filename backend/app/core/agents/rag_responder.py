"""RAG Responder agent for generating responses using retrieved context."""

import logging

from app.core.services import LLMService
from app.core.workflow.state import ChatState, Source

logger = logging.getLogger(__name__)

# System prompt for RAG-based response generation
RAG_SYSTEM_PROMPT = """You are a helpful knowledge base assistant that answers questions
based on company documents from Jira and Confluence.

Instructions:
1. Answer the question using ONLY the provided context
2. If the context contains relevant information, provide a clear and helpful answer
3. Cite your sources by mentioning the document titles
4. If the context doesn't fully answer the question, acknowledge what you found and
   note what additional information might be needed
5. Respond in the same language as the user's question (Korean if Korean, English if English)
6. Be concise but thorough"""


def rag_responder(state: ChatState) -> ChatState:
    """Generate response using RAG context.

    This agent takes the search results and generates a response
    using the retrieved documents as context.

    Args:
        state: Current chat state with search_results

    Returns:
        Updated state with response, response_type, and sources
    """
    user_query = state.get("user_query", "")
    search_results = state.get("search_results", [])

    if not search_results:
        logger.warning("No search results provided to rag_responder")
        state["response"] = "죄송합니다. 관련 문서를 찾을 수 없습니다."
        state["response_type"] = "rag"
        state["sources"] = []
        return state

    try:
        # Build context from search results (top 3)
        context_parts = []
        sources = []

        for i, result in enumerate(search_results[:3], 1):
            doc_type = result.get("doc_type", "document")
            title = result.get("title", "Untitled")
            content = result.get("chunk_text") or result.get("content", "")
            url = result.get("url", "")

            # Format context entry
            context_parts.append(
                f"[Document {i}]\n"
                f"Type: {doc_type.upper()}\n"
                f"Title: {title}\n"
                f"Content: {content[:800]}"  # Limit content length
            )

            # Add to sources
            sources.append(Source(
                doc_id=result.get("doc_id", ""),
                doc_type=result.get("doc_type", "jira"),
                title=title,
                url=url,
            ))

        context = "\n\n".join(context_parts)

        # Generate response with LLM
        llm = LLMService()
        response = llm.generate_with_context(
            query=user_query,
            context=context,
            system_prompt=RAG_SYSTEM_PROMPT,
            temperature=0.3,  # Lower temperature for factual responses
            max_tokens=1024,
        )

        state["response"] = response
        state["response_type"] = "rag"
        state["sources"] = sources

        logger.info(f"Generated RAG response with {len(sources)} sources")

    except Exception as e:
        logger.error(f"RAG response generation failed: {e}")
        state["response"] = "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
        state["response_type"] = "rag"
        state["sources"] = []
        state["error"] = f"Response generation error: {str(e)}"

    return state
