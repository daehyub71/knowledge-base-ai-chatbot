"""Response Formatter agent for formatting the final response."""

import logging

from app.core.workflow.state import ChatState

logger = logging.getLogger(__name__)


def response_formatter(state: ChatState) -> ChatState:
    """Format the final response with sources and metadata.

    This agent formats the response in a user-friendly markdown format,
    including source citations and links.

    Args:
        state: Current chat state with response and sources

    Returns:
        Updated state with formatted response
    """
    response = state.get("response", "")
    response_type = state.get("response_type", "rag")
    sources = state.get("sources", [])

    if not response:
        state["response"] = "죄송합니다. 응답을 생성할 수 없습니다."
        return state

    # Format sources section if available
    if sources and response_type == "rag":
        source_lines = []
        for i, source in enumerate(sources, 1):
            doc_type = source.get("doc_type", "document")
            title = source.get("title", "Untitled")
            url = source.get("url", "")

            # Format based on document type
            if doc_type == "jira":
                icon = "🎫"
                type_label = "Jira"
            else:
                icon = "📄"
                type_label = "Confluence"

            if url:
                source_lines.append(f"{i}. {icon} [{title}]({url}) ({type_label})")
            else:
                source_lines.append(f"{i}. {icon} {title} ({type_label})")

        if source_lines:
            sources_section = "\n\n---\n### 📚 참고 문서\n" + "\n".join(source_lines)
            formatted_response = response + sources_section
        else:
            formatted_response = response
    else:
        formatted_response = response

    state["response"] = formatted_response

    logger.info(
        f"Formatted response: type={response_type}, "
        f"sources_count={len(sources)}, "
        f"length={len(formatted_response)}"
    )

    return state
