"""LLM Fallback agent for generating responses when RAG has no relevant results."""

import logging

from app.core.services import LLMService
from app.core.workflow.state import ChatState

logger = logging.getLogger(__name__)

# System prompt for fallback responses
FALLBACK_SYSTEM_PROMPT = """You are a helpful assistant. The user has asked a question,
but no relevant documents were found in the company's knowledge base (Jira and Confluence).

Instructions:
1. Acknowledge that you couldn't find specific information in the company documents
2. Provide a helpful general answer based on your knowledge if applicable
3. Suggest the user might want to:
   - Check with their team members
   - Create a new Jira issue or Confluence page
   - Provide more specific keywords
4. Be honest about the limitations of your response
5. Respond in the same language as the user's question

Important: Always include a disclaimer that this response is NOT based on company documents."""


def llm_fallback(state: ChatState) -> ChatState:
    """Generate fallback response when RAG results are irrelevant.

    This agent generates a response using general LLM knowledge
    when no relevant documents are found in the knowledge base.

    Args:
        state: Current chat state

    Returns:
        Updated state with response, response_type, and empty sources
    """
    user_query = state.get("user_query", "")
    analyzed_query = state.get("analyzed_query", {})

    # Check if this is a greeting
    intent = analyzed_query.get("intent", "question") if analyzed_query else "question"

    try:
        llm = LLMService()

        if intent == "greeting":
            # Simple greeting response
            response = llm.generate(
                prompt=user_query,
                system_prompt="You are a friendly knowledge base assistant. Respond to greetings warmly and briefly introduce yourself as a helper for Jira and Confluence questions. Respond in the same language as the user.",
                temperature=0.7,
                max_tokens=200,
            )
            disclaimer = ""
        else:
            # Generate fallback response for questions
            prompt = f"""Question: {user_query}

Please provide a helpful response, keeping in mind that no relevant company documents were found for this query."""

            response = llm.generate(
                prompt=prompt,
                system_prompt=FALLBACK_SYSTEM_PROMPT,
                temperature=0.5,
                max_tokens=800,
            )

            # Add disclaimer
            disclaimer = "\n\n---\n*이 응답은 회사 문서(Jira/Confluence)에 기반하지 않은 일반적인 답변입니다.*"

        state["response"] = response + disclaimer
        state["response_type"] = "llm_fallback"
        state["sources"] = []

        logger.info(f"Generated fallback response for intent: {intent}")

    except Exception as e:
        logger.error(f"Fallback response generation failed: {e}")
        state["response"] = (
            "죄송합니다. 관련 문서를 찾지 못했고, 응답 생성 중 오류가 발생했습니다. "
            "다른 키워드로 다시 검색해 주세요."
        )
        state["response_type"] = "llm_fallback"
        state["sources"] = []
        state["error"] = f"Fallback generation error: {str(e)}"

    return state
