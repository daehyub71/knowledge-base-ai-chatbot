"""LLM service for generating responses using OpenAI/Azure OpenAI."""

import logging
from typing import Any

from openai import AzureOpenAI, OpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating responses using OpenAI or Azure OpenAI.

    Supports both OpenAI and Azure OpenAI APIs with automatic fallback.
    Uses the configured default provider from settings.
    """

    def __init__(self, provider: str | None = None, model: str | None = None):
        """Initialize the LLM service.

        Args:
            provider: Force a specific provider ('openai' or 'azure').
                     If None, uses DEFAULT_PROVIDER setting.
            model: Model to use. If None, uses DEFAULT_MODEL setting.
        """
        settings = get_settings()

        # Determine provider
        if provider is None:
            provider = getattr(settings, "default_provider", "openai")

        # Determine model
        if model is None:
            model = getattr(settings, "default_model", "gpt-4o-mini")

        # Initialize client based on provider
        if provider == "openai" and settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = model
            self.provider = "openai"
            logger.info(f"LLMService initialized with OpenAI (model: {self.model})")

        elif provider == "azure" and settings.azure_openai_api_key and settings.azure_openai_endpoint:
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
            )
            self.model = settings.azure_openai_deployment_gpt4o
            self.provider = "azure"
            logger.info(f"LLMService initialized with Azure OpenAI (model: {self.model})")

        elif settings.openai_api_key:
            # Fallback to OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = model
            self.provider = "openai"
            logger.info(f"LLMService initialized with OpenAI (fallback, model: {self.model})")

        elif settings.azure_openai_api_key and settings.azure_openai_endpoint:
            # Fallback to Azure
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
            )
            self.model = settings.azure_openai_deployment_gpt4o
            self.provider = "azure"
            logger.info(f"LLMService initialized with Azure OpenAI (fallback, model: {self.model})")

        else:
            raise ValueError(
                "No LLM API configured. Please set either "
                "AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT, "
                "or OPENAI_API_KEY in .env"
            )

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a response for a single prompt.

        Args:
            prompt: User prompt/query
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response

        Returns:
            Generated response text
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return self._call_api(messages, temperature, max_tokens)

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a response for a conversation.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt (prepended to messages)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response

        Returns:
            Generated response text
        """
        all_messages = []

        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})

        all_messages.extend(messages)

        return self._call_api(all_messages, temperature, max_tokens)

    def generate_with_context(
        self,
        query: str,
        context: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a response using RAG context.

        Args:
            query: User query
            context: Retrieved context from RAG
            system_prompt: Optional custom system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Generated response text
        """
        if system_prompt is None:
            system_prompt = (
                "You are a helpful assistant that answers questions based on the "
                "provided context. If the context doesn't contain relevant information, "
                "say so and provide a general answer if possible. "
                "Always cite your sources when using information from the context. "
                "Respond in the same language as the user's question."
            )

        prompt = f"""Context:
{context}

Question: {query}

Please answer the question based on the context provided above."""

        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _call_api(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Make the actual API call.

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content or ""
            logger.debug(
                f"Generated response with {response.usage.total_tokens if response.usage else 'N/A'} tokens"
            )
            return content

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise

    def analyze_query(self, query: str) -> dict[str, Any]:
        """Analyze a user query to extract intent and keywords.

        Args:
            query: User query to analyze

        Returns:
            Dictionary with intent, keywords, and filters
        """
        system_prompt = """You are a query analyzer. Analyze the user query and extract:
1. intent: The user's intention (search, question, clarification, greeting, other)
2. keywords: Important keywords for search (list of strings)
3. doc_type_filter: If the query mentions Jira issues or Confluence pages specifically (jira, confluence, or null)
4. date_filter: If the query mentions time (e.g., "last week", "recent") extract as {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"} or null

Respond in JSON format only, no markdown."""

        prompt = f"Query: {query}"

        try:
            response = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.0,
                max_tokens=500,
            )

            # Parse JSON response
            import json
            return json.loads(response)

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse query analysis response: {response}")
            return {
                "intent": "question",
                "keywords": query.split(),
                "doc_type_filter": None,
                "date_filter": None,
            }

    def check_relevance(
        self,
        query: str,
        search_results: list[dict[str, Any]],
    ) -> bool:
        """Check if search results are relevant to the query.

        Args:
            query: User query
            search_results: List of search result dicts

        Returns:
            True if results are relevant, False otherwise
        """
        if not search_results:
            return False

        # Format search results for analysis
        results_text = "\n\n".join([
            f"Title: {r.get('title', 'N/A')}\n"
            f"Type: {r.get('doc_type', 'N/A')}\n"
            f"Content: {r.get('chunk_text', r.get('content', ''))[:300]}"
            for r in search_results[:3]  # Only check top 3
        ])

        system_prompt = """You are a relevance checker. Determine if the search results are relevant to the user's query.
Respond with only "relevant" or "irrelevant"."""

        prompt = f"""Query: {query}

Search Results:
{results_text}

Are these results relevant to answering the query?"""

        try:
            response = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.0,
                max_tokens=50,
            )

            return "relevant" in response.lower()

        except Exception as e:
            logger.error(f"Relevance check failed: {e}")
            # Default to relevant if check fails
            return True

    def test_connection(self) -> bool:
        """Test the connection to the LLM API.

        Returns:
            True if connection is successful
        """
        try:
            response = self.generate(
                prompt="Hello, respond with 'OK'",
                temperature=0.0,
                max_tokens=10,
            )

            success = "ok" in response.lower()
            if success:
                logger.info(f"LLM API connection test successful (provider: {self.provider})")
            return success

        except Exception as e:
            logger.error(f"LLM API connection test failed: {e}")
            return False
