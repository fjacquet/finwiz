"""
Vector repository for similarity search operations.

Provides vector embedding storage and semantic similarity search using
pgvector with async operations, timeout enforcement, and error handling.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from finwiz.supabase.client import SupabaseClient
from finwiz.supabase.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorRepository:
    """
    Repository for vector operations.

    Handles vector embedding storage and semantic similarity search with:
    - Async background storage (non-blocking)
    - Configurable similarity threshold (default 0.7)
    - Strict timeout enforcement (2 seconds for search)
    - Graceful error handling and logging

    Attributes:
        client: SupabaseClient instance for database operations
        embedding_service: EmbeddingService for generating embeddings
        table: Database table name for embeddings

    """

    def __init__(
        self,
        client: SupabaseClient,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        """
        Initialize vector repository.

        Args:
            client: SupabaseClient instance
            embedding_service: Optional EmbeddingService instance (creates new if None)

        """
        self.client = client
        self.embedding_service = embedding_service or EmbeddingService()
        self.table = "analysis_embeddings"

        logger.info("VectorRepository initialized")

    async def store_embedding(
        self,
        analysis_id: str,
        text: str,
    ) -> bool:
        """
        Store vector embedding asynchronously (background task).

        Generates embedding for text and stores it in the background without blocking.
        Returns immediately and logs success/failure asynchronously.

        Args:
            analysis_id: Associated analysis ID (UUID)
            text: Source text to embed (will be stripped)

        Returns:
            True (always returns immediately, actual storage is async)

        """
        logger.debug(f"Scheduling async embedding storage for analysis: {analysis_id} (text length: {len(text)})")

        # Execute in background task (non-blocking)
        asyncio.create_task(
            self._store_embedding_with_retry(
                analysis_id=analysis_id,
                text=text,
            )
        )

        return True  # Return immediately

    async def _store_embedding_with_retry(
        self,
        analysis_id: str,
        text: str,
        max_retries: int = 3,
    ) -> None:
        """
        Store embedding with retry logic.

        Generates embedding and stores it with exponential backoff retry.
        Logs success/failure but does not raise exceptions (background task).

        Args:
            analysis_id: Associated analysis ID (UUID)
            text: Source text to embed
            max_retries: Maximum number of retry attempts (default: 3)

        """
        try:
            # Generate embedding first (with its own retry logic)
            embedding = await self.embedding_service.generate_embedding(text)

            logger.debug(f"Generated embedding for analysis {analysis_id}, storing in database...")

            # Store embedding with retry logic
            for attempt in range(max_retries):
                try:

                    def insert(client: Any) -> Any:
                        """Insert function for execute_with_timeout."""
                        return (
                            client.table(self.table)
                            .insert(
                                {
                                    "analysis_id": analysis_id,
                                    "embedding": embedding,
                                    "text": text.strip(),
                                    "created_at": datetime.now(timezone.utc).isoformat(),
                                }
                            )
                            .execute()
                        )

                    result = await self.client.execute_with_timeout(insert, timeout=5.0)

                    if result:
                        logger.info(f"Embedding stored successfully for analysis: {analysis_id}")
                        return

                    logger.warning(f"Store attempt {attempt + 1}/{max_retries} returned None for analysis: {analysis_id}")

                except Exception as e:
                    logger.error(f"Store attempt {attempt + 1}/{max_retries} failed for analysis {analysis_id}: {e}")

                # Exponential backoff before retry (except on last attempt)
                if attempt < max_retries - 1:
                    backoff_seconds = 2**attempt  # 1s, 2s, 4s
                    logger.debug(f"Retrying in {backoff_seconds}s...")
                    await asyncio.sleep(backoff_seconds)

            # All retries exhausted
            logger.error(f"Failed to store embedding for analysis {analysis_id} after {max_retries} attempts")

        except Exception as e:
            # Embedding generation failed
            logger.error(f"Failed to generate embedding for analysis {analysis_id}: {e}")

    async def search_similar(
        self,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> list[tuple[str, float]]:
        """
        Search for similar analyses using vector similarity.

        Generates embedding for query text and performs pgvector similarity search.
        Uses strict 2-second timeout and configurable similarity threshold.

        Args:
            query: Query text to search for similar analyses
            limit: Maximum number of results to return (default: 5)
            similarity_threshold: Minimum similarity score 0-1 (default: 0.7)

        Returns:
            List of tuples (analysis_id, similarity_score) ordered by similarity desc.
            Returns empty list if search fails or no results above threshold.

        """
        # Validate inputs
        if not query or not query.strip():
            logger.warning("Empty query provided for similarity search")
            return []

        if not 0.0 <= similarity_threshold <= 1.0:
            logger.warning(f"Invalid similarity threshold: {similarity_threshold}, using default 0.7")
            similarity_threshold = 0.7

        if limit < 1:
            logger.warning(f"Invalid limit: {limit}, using default 5")
            limit = 5

        logger.debug(f"Searching for similar analyses (query length: {len(query)}, limit: {limit}, threshold: {similarity_threshold})")

        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(query)

            logger.debug("Query embedding generated, executing similarity search...")

            def search(client: Any) -> Any:
                """Search function for execute_with_timeout."""
                # Use pgvector similarity search function
                return client.rpc(
                    "match_analyses",
                    {
                        "query_embedding": query_embedding,
                        "match_threshold": similarity_threshold,
                        "match_count": limit,
                    },
                ).execute()

            # Execute with 2-second timeout
            result = await self.client.execute_with_timeout(search, timeout=2.0)

            if result and result.data:
                # Extract analysis_id and similarity from results
                matches = [(record["analysis_id"], record["similarity"]) for record in result.data]

                logger.info(f"Found {len(matches)} similar analyses (threshold: {similarity_threshold})")

                return matches

            logger.info(f"No similar analyses found above threshold {similarity_threshold}")
            return []

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

    async def get_embedding_by_analysis_id(
        self,
        analysis_id: str,
    ) -> tuple[list[float], str] | None:
        """
        Get embedding and text for an analysis.

        Retrieves the stored embedding and source text for a specific analysis.
        Uses strict 2-second timeout.

        Args:
            analysis_id: Analysis ID (UUID)

        Returns:
            Tuple of (embedding, text) if found, None otherwise

        """
        logger.debug(f"Fetching embedding for analysis: {analysis_id}")

        def query(client: Any) -> Any:
            """Query function for execute_with_timeout."""
            return client.table(self.table).select("embedding, text").eq("analysis_id", analysis_id).limit(1).execute()

        try:
            result = await self.client.execute_with_timeout(query, timeout=2.0)

            if result and result.data:
                record = result.data[0]
                embedding = record["embedding"]
                text = record["text"]

                logger.debug(f"Found embedding for analysis: {analysis_id}")
                return (embedding, text)

            logger.debug(f"No embedding found for analysis: {analysis_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to fetch embedding for analysis {analysis_id}: {e}")
            return None

    async def delete_embedding(
        self,
        analysis_id: str,
    ) -> bool:
        """
        Delete embedding for an analysis.

        Removes the stored embedding for a specific analysis.
        Uses strict 2-second timeout.

        Args:
            analysis_id: Analysis ID (UUID)

        Returns:
            True if deleted successfully, False otherwise

        """
        logger.debug(f"Deleting embedding for analysis: {analysis_id}")

        def delete(client: Any) -> Any:
            """Delete function for execute_with_timeout."""
            return client.table(self.table).delete().eq("analysis_id", analysis_id).execute()

        try:
            result = await self.client.execute_with_timeout(delete, timeout=2.0)

            if result:
                logger.info(f"Embedding deleted successfully for analysis: {analysis_id}")
                return True

            logger.warning(f"Failed to delete embedding for analysis: {analysis_id}")
            return False

        except Exception as e:
            logger.error(f"Error deleting embedding for analysis {analysis_id}: {e}")
            return False

    async def count_embeddings(self) -> int:
        """
        Count total number of stored embeddings.

        Returns:
            Number of embeddings in database, or 0 if query fails

        """
        logger.debug("Counting total embeddings")

        def query(client: Any) -> Any:
            """Query function for execute_with_timeout."""
            return client.table(self.table).select("id", count="exact").execute()

        try:
            result = await self.client.execute_with_timeout(query, timeout=2.0)

            if result:
                count = result.count or 0
                logger.info(f"Total embeddings in database: {count}")
                return count

            logger.warning("Failed to count embeddings")
            return 0

        except Exception as e:
            logger.error(f"Error counting embeddings: {e}")
            return 0
