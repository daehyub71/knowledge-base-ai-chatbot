"""Embedding service for generating text embeddings using OpenAI/Azure OpenAI."""

import logging
from typing import Any

from openai import AzureOpenAI, OpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)

# text-embedding-3-large produces 3072-dimensional vectors
EMBEDDING_DIMENSION = 3072
DEFAULT_BATCH_SIZE = 100


class EmbeddingService:
    """Service for generating text embeddings using OpenAI API."""

    def __init__(self, provider: str | None = None):
        """Initialize the embedding service with OpenAI or Azure OpenAI client.

        Args:
            provider: Force a specific provider ('openai' or 'azure').
                     If None, uses DEFAULT_PROVIDER setting or auto-detects.
        """
        settings = get_settings()

        # Determine which provider to use
        # Priority: explicit parameter > DEFAULT_PROVIDER setting > auto-detect
        if provider is None:
            provider = getattr(settings, "default_provider", "openai")

        if provider == "openai" and settings.openai_api_key:
            # Use OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = "text-embedding-3-large"
            self.provider = "openai"
            logger.info(
                f"EmbeddingService initialized with OpenAI "
                f"(model: {self.model})"
            )
        elif provider == "azure" and settings.azure_openai_api_key and settings.azure_openai_endpoint:
            # Use Azure OpenAI
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
            )
            self.model = settings.azure_openai_deployment_embedding
            self.provider = "azure"
            logger.info(
                f"EmbeddingService initialized with Azure OpenAI "
                f"(model: {self.model})"
            )
        elif settings.openai_api_key:
            # Fallback to OpenAI if preferred provider unavailable
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = "text-embedding-3-large"
            self.provider = "openai"
            logger.info(
                f"EmbeddingService initialized with OpenAI (fallback) "
                f"(model: {self.model})"
            )
        elif settings.azure_openai_api_key and settings.azure_openai_endpoint:
            # Fallback to Azure if OpenAI unavailable
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
            )
            self.model = settings.azure_openai_deployment_embedding
            self.provider = "azure"
            logger.info(
                f"EmbeddingService initialized with Azure OpenAI (fallback) "
                f"(model: {self.model})"
            )
        else:
            raise ValueError(
                "No embedding API configured. Please set either "
                "AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT, "
                "or OPENAI_API_KEY in .env"
            )

        self.dimension = EMBEDDING_DIMENSION
        self.batch_size = DEFAULT_BATCH_SIZE

    def get_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector (3072 dimensions)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding, returning zero vector")
            return [0.0] * self.dimension

        try:
            # Truncate text if too long (max ~8191 tokens for embedding models)
            # Approximate: 1 token ~= 4 characters
            max_chars = 30000  # Safe limit
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.warning(f"Text truncated to {max_chars} characters for embedding")

            response = self.client.embeddings.create(
                input=text,
                model=self.model,
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def get_embeddings_batch(
        self,
        texts: list[str],
        batch_size: int | None = None,
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process per API call (default: 100)

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        batch_size = batch_size or self.batch_size
        all_embeddings = []

        # Process in batches
        total_batches = (len(texts) + batch_size - 1) // batch_size
        logger.info(
            f"Processing {len(texts)} texts in {total_batches} batches "
            f"(batch_size={batch_size})"
        )

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_num = i // batch_size + 1

            try:
                # Prepare texts (truncate if needed)
                max_chars = 30000
                prepared_batch = []
                for text in batch:
                    if not text or not text.strip():
                        prepared_batch.append(" ")  # Empty placeholder
                    elif len(text) > max_chars:
                        prepared_batch.append(text[:max_chars])
                    else:
                        prepared_batch.append(text)

                response = self.client.embeddings.create(
                    input=prepared_batch,
                    model=self.model,
                )

                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.info(
                    f"Batch {batch_num}/{total_batches}: "
                    f"Generated {len(batch_embeddings)} embeddings"
                )

            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {batch_num}: {e}")
                # Fill with zero vectors for failed batch
                for _ in batch:
                    all_embeddings.append([0.0] * self.dimension)

        logger.info(f"Generated {len(all_embeddings)} embeddings total")
        return all_embeddings

    def embed_chunks(
        self,
        chunks: list[dict[str, Any]],
        text_key: str = "chunk_text",
    ) -> list[dict[str, Any]]:
        """Generate embeddings for document chunks.

        Args:
            chunks: List of chunk dictionaries
            text_key: Key containing the text to embed

        Returns:
            Chunks with added 'embedding' field
        """
        if not chunks:
            return []

        # Extract texts
        texts = [chunk.get(text_key, "") for chunk in chunks]

        # Generate embeddings
        embeddings = self.get_embeddings_batch(texts)

        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding

        logger.info(f"Added embeddings to {len(chunks)} chunks")
        return chunks

    def test_connection(self) -> bool:
        """Test the connection to the embedding API.

        Returns:
            True if connection is successful
        """
        try:
            test_text = "Hello, this is a test."
            embedding = self.get_embedding(test_text)

            if len(embedding) == self.dimension:
                logger.info(
                    f"Embedding API connection test successful "
                    f"(provider: {self.provider}, dimension: {len(embedding)})"
                )
                return True
            else:
                logger.error(
                    f"Unexpected embedding dimension: {len(embedding)} "
                    f"(expected: {self.dimension})"
                )
                return False

        except Exception as e:
            logger.error(f"Embedding API connection test failed: {e}")
            return False
