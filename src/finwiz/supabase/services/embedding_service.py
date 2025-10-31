"""
Embedding service for vector generation.

Generates vector embeddings using OpenAI text-embedding-3-small model
with caching to avoid redundant API calls and retry logic for reliability.
"""

import asyncio
import hashlib
import logging
import os

from openai import AsyncOpenAI, OpenAIError

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating vector embeddings.

    Uses OpenAI text-embedding-3-small model (1536 dimensions) with:
    - Automatic retry logic with exponential backoff
    - In-memory caching to avoid redundant API calls
    - Graceful error handling and logging

    Attributes:
        client: AsyncOpenAI client instance
        model: Embedding model name (text-embedding-3-small)
        dimensions: Embedding dimensions (1536)
        cache: In-memory cache for embeddings (text_hash -> embedding)

    """

    def __init__(self) -> None:
        """
        Initialize embedding service.

        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set

        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"
        self.dimensions = 1536
        self.cache: dict[str, list[float]] = {}

        logger.info(f"EmbeddingService initialized with model: {self.model}")

    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key for text.

        Uses SHA-256 hash of text for efficient cache lookups.

        Args:
            text: Input text

        Returns:
            Cache key (hex digest of text hash)

        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def generate_embedding(
        self,
        text: str,
        max_retries: int = 3,
    ) -> list[float]:
        """
        Generate vector embedding for text.

        Generates 1536-dimensional embedding using OpenAI text-embedding-3-small.
        Uses in-memory cache to avoid redundant API calls and implements
        exponential backoff retry logic for reliability.

        Args:
            text: Input text to embed (will be stripped)
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            List of 1536 floats representing the embedding

        Raises:
            ValueError: If text is empty after stripping
            OpenAIError: If all retry attempts fail

        """
        # Validate input
        text_stripped = text.strip()
        if not text_stripped:
            raise ValueError("Text cannot be empty")

        # Check cache first
        cache_key = self._get_cache_key(text_stripped)
        if cache_key in self.cache:
            logger.debug(f"Cache HIT for embedding (text length: {len(text_stripped)})")
            return self.cache[cache_key]

        logger.debug(f"Cache MISS for embedding (text length: {len(text_stripped)}), generating with {self.model}")

        # Generate embedding with retry logic
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                # Call OpenAI API
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=text_stripped,
                    dimensions=self.dimensions,
                )

                # Extract embedding
                embedding = response.data[0].embedding

                # Validate dimensions
                if len(embedding) != self.dimensions:
                    raise ValueError(f"Expected {self.dimensions} dimensions, got {len(embedding)}")

                # Cache the result
                self.cache[cache_key] = embedding

                logger.info(f"Generated embedding successfully (text length: {len(text_stripped)}, attempt: {attempt + 1})")

                return embedding

            except OpenAIError as e:
                last_error = e
                logger.warning(f"OpenAI API call failed (attempt {attempt + 1}/{max_retries}): {e}")

                # Exponential backoff before retry (except on last attempt)
                if attempt < max_retries - 1:
                    backoff_seconds = 2**attempt  # 1s, 2s, 4s
                    logger.debug(f"Retrying in {backoff_seconds}s...")
                    await asyncio.sleep(backoff_seconds)

            except Exception as e:
                # Unexpected error - don't retry
                logger.error(f"Unexpected error generating embedding: {e}")
                raise

        # All retries exhausted
        error_msg = f"Failed to generate embedding after {max_retries} attempts"
        logger.error(f"{error_msg}: {last_error}")
        raise OpenAIError(error_msg) from last_error

    async def generate_embeddings_batch(
        self,
        texts: list[str],
        max_retries: int = 3,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in parallel.

        Efficiently generates embeddings for multiple texts using asyncio.gather.
        Each text is processed independently with caching and retry logic.

        Args:
            texts: List of input texts to embed
            max_retries: Maximum number of retry attempts per text (default: 3)

        Returns:
            List of embeddings (each embedding is a list of 1536 floats)

        Raises:
            ValueError: If any text is empty after stripping
            OpenAIError: If any embedding generation fails after retries

        """
        if not texts:
            return []

        logger.info(f"Generating embeddings for {len(texts)} texts in parallel")

        # Generate all embeddings in parallel
        embeddings = await asyncio.gather(*[self.generate_embedding(text, max_retries=max_retries) for text in texts])

        logger.info(f"Generated {len(embeddings)} embeddings successfully")
        return embeddings

    def clear_cache(self) -> None:
        """
        Clear the embedding cache.

        Removes all cached embeddings from memory. Useful for testing
        or when memory usage is a concern.
        """
        cache_size = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared embedding cache ({cache_size} entries)")

    def get_cache_size(self) -> int:
        """
        Get the number of cached embeddings.

        Returns:
            Number of embeddings currently in cache

        """
        return len(self.cache)
