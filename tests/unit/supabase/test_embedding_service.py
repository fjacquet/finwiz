"""
Unit tests for Supabase EmbeddingService.

Tests embedding service functionality including:
- generate_embedding() with valid text input
- generate_embedding() with OpenAI API failure (retry logic)
- Caching behavior to avoid redundant API calls
- Batch embedding generation
- Error handling for empty text and API failures
"""

import pytest
from openai import OpenAIError

from finwiz.supabase.services.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test suite for EmbeddingService."""

    @pytest.fixture
    def mock_openai_client(self, mocker):
        """Create mock AsyncOpenAI client."""
        mock_client = mocker.AsyncMock()
        mocker.patch(
            "finwiz.supabase.services.embedding_service.AsyncOpenAI",
            return_value=mock_client,
        )
        return mock_client

    @pytest.fixture
    def embedding_service(self, mock_openai_client, mocker):
        """Create EmbeddingService with mocked OpenAI client."""
        mocker.patch.dict("os.environ", {"OPENAI_API_KEY": "test-key-12345678"})
        return EmbeddingService()

    @pytest.fixture
    def sample_embedding(self):
        """Create sample 1536-dimensional embedding."""
        return [0.1] * 1536

    @pytest.mark.asyncio
    async def test_should_initialize_with_api_key(self, mocker):
        """Test EmbeddingService initialization with API key."""
        # Arrange
        mocker.patch.dict("os.environ", {"OPENAI_API_KEY": "test-key-12345678"})
        mock_client = mocker.AsyncMock()
        mocker.patch(
            "finwiz.supabase.services.embedding_service.AsyncOpenAI",
            return_value=mock_client,
        )

        # Act
        service = EmbeddingService()

        # Assert
        assert service.client == mock_client
        assert service.model == "text-embedding-3-small"
        assert service.dimensions == 1536
        assert isinstance(service.cache, dict)
        assert len(service.cache) == 0

    @pytest.mark.asyncio
    async def test_should_raise_error_when_api_key_missing(self, mocker):
        """Test initialization fails without API key."""
        # Arrange
        mocker.patch.dict("os.environ", {}, clear=True)

        # Act & Assert
        with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable must be set"):
            EmbeddingService()

    @pytest.mark.asyncio
    async def test_should_generate_embedding_with_valid_text(self, embedding_service, mock_openai_client, sample_embedding, mocker):
        """Test generate_embedding() with valid text input."""
        # Arrange
        text = "Apple Inc. is a technology company with strong fundamentals"
        mock_response = mocker.Mock()
        mock_response.data = [mocker.Mock(embedding=sample_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response

        # Act
        result = await embedding_service.generate_embedding(text)

        # Assert
        assert result == sample_embedding
        assert len(result) == 1536
        mock_openai_client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input=text,
            dimensions=1536,
        )

    @pytest.mark.asyncio
    async def test_should_cache_embedding_to_avoid_redundant_calls(self, embedding_service, mock_openai_client, sample_embedding, mocker):
        """Test that embeddings are cached to avoid redundant API calls."""
        # Arrange
        text = "Test text for caching"
        mock_response = mocker.Mock()
        mock_response.data = [mocker.Mock(embedding=sample_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response

        # Act - First call (cache miss)
        result1 = await embedding_service.generate_embedding(text)

        # Act - Second call (cache hit)
        result2 = await embedding_service.generate_embedding(text)

        # Assert
        assert result1 == sample_embedding
        assert result2 == sample_embedding
        assert result1 == result2

        # Verify API was called only once (second call used cache)
        mock_openai_client.embeddings.create.assert_called_once()

        # Verify cache contains the embedding
        assert embedding_service.get_cache_size() == 1

    @pytest.mark.asyncio
    async def test_should_retry_on_openai_api_failure(self, embedding_service, mock_openai_client, sample_embedding, mocker):
        """Test generate_embedding() with OpenAI API failure (retry logic)."""
        # Arrange
        text = "Test text for retry"
        mock_response = mocker.Mock()
        mock_response.data = [mocker.Mock(embedding=sample_embedding)]

        # First two calls fail, third succeeds
        mock_openai_client.embeddings.create.side_effect = [
            OpenAIError("Rate limit exceeded"),
            OpenAIError("Temporary error"),
            mock_response,
        ]

        # Mock asyncio.sleep to avoid actual delays
        mocker.patch("asyncio.sleep", return_value=None)

        # Act
        result = await embedding_service.generate_embedding(text, max_retries=3)

        # Assert
        assert result == sample_embedding
        assert mock_openai_client.embeddings.create.call_count == 3

    @pytest.mark.asyncio
    async def test_should_raise_error_after_max_retries(self, embedding_service, mock_openai_client, mocker):
        """Test that error is raised after exhausting all retries."""
        # Arrange
        text = "Test text for max retries"
        mock_openai_client.embeddings.create.side_effect = OpenAIError("Persistent error")

        # Mock asyncio.sleep to avoid actual delays
        mocker.patch("asyncio.sleep", return_value=None)

        # Act & Assert
        with pytest.raises(OpenAIError, match="Failed to generate embedding after 3 attempts"):
            await embedding_service.generate_embedding(text, max_retries=3)

        # Verify all retry attempts were made
        assert mock_openai_client.embeddings.create.call_count == 3

    @pytest.mark.asyncio
    async def test_should_raise_error_for_empty_text(self, embedding_service):
        """Test that empty text raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await embedding_service.generate_embedding("")

        with pytest.raises(ValueError, match="Text cannot be empty"):
            await embedding_service.generate_embedding("   ")  # Whitespace only

    @pytest.mark.asyncio
    async def test_should_strip_whitespace_from_text(self, embedding_service, mock_openai_client, sample_embedding, mocker):
        """Test that text is stripped before processing."""
        # Arrange
        text_with_whitespace = "  Test text with whitespace  "
        text_stripped = "Test text with whitespace"
        mock_response = mocker.Mock()
        mock_response.data = [mocker.Mock(embedding=sample_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response

        # Act
        result = await embedding_service.generate_embedding(text_with_whitespace)

        # Assert
        assert result == sample_embedding
        mock_openai_client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input=text_stripped,  # Whitespace stripped
            dimensions=1536,
        )

    @pytest.mark.asyncio
    async def test_should_validate_embedding_dimensions(self, embedding_service, mock_openai_client, mocker):
        """Test that incorrect embedding dimensions raise error."""
        # Arrange
        text = "Test text"
        wrong_dimensions_embedding = [0.1] * 512  # Wrong size
        mock_response = mocker.Mock()
        mock_response.data = [mocker.Mock(embedding=wrong_dimensions_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response

        # Act & Assert
        with pytest.raises(ValueError, match="Expected 1536 dimensions, got 512"):
            await embedding_service.generate_embedding(text)

    @pytest.mark.asyncio
    async def test_should_generate_embeddings_batch(self, embedding_service, mock_openai_client, sample_embedding, mocker):
        """Test batch embedding generation."""
        # Arrange
        texts = [
            "First text",
            "Second text",
            "Third text",
        ]
        mock_response = mocker.Mock()
        mock_response.data = [mocker.Mock(embedding=sample_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response

        # Act
        results = await embedding_service.generate_embeddings_batch(texts)

        # Assert
        assert len(results) == 3
        assert all(len(emb) == 1536 for emb in results)
        assert mock_openai_client.embeddings.create.call_count == 3

    @pytest.mark.asyncio
    async def test_should_return_empty_list_for_empty_batch(self, embedding_service):
        """Test batch generation with empty list."""
        # Act
        results = await embedding_service.generate_embeddings_batch([])

        # Assert
        assert results == []

    @pytest.mark.asyncio
    async def test_should_clear_cache(self, embedding_service, mock_openai_client, sample_embedding, mocker):
        """Test clearing the embedding cache."""
        # Arrange
        text = "Test text"
        mock_response = mocker.Mock()
        mock_response.data = [mocker.Mock(embedding=sample_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response

        # Generate embedding to populate cache
        await embedding_service.generate_embedding(text)
        assert embedding_service.get_cache_size() == 1

        # Act
        embedding_service.clear_cache()

        # Assert
        assert embedding_service.get_cache_size() == 0
        assert len(embedding_service.cache) == 0

    @pytest.mark.asyncio
    async def test_should_get_cache_size(self, embedding_service, mock_openai_client, sample_embedding, mocker):
        """Test getting cache size."""
        # Arrange
        texts = ["Text 1", "Text 2", "Text 3"]
        mock_response = mocker.Mock()
        mock_response.data = [mocker.Mock(embedding=sample_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response

        # Act
        for text in texts:
            await embedding_service.generate_embedding(text)

        # Assert
        assert embedding_service.get_cache_size() == 3

    @pytest.mark.asyncio
    async def test_should_use_cache_key_based_on_text_content(self, embedding_service, mock_openai_client, sample_embedding, mocker):
        """Test that cache key is based on text content."""
        # Arrange
        text1 = "Same text"
        text2 = "Same text"  # Identical content
        text3 = "Different text"

        mock_response = mocker.Mock()
        mock_response.data = [mocker.Mock(embedding=sample_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response

        # Act
        await embedding_service.generate_embedding(text1)
        await embedding_service.generate_embedding(text2)  # Should use cache
        await embedding_service.generate_embedding(text3)  # Should generate new

        # Assert
        # Only 2 API calls (text1 and text3), text2 used cache
        assert mock_openai_client.embeddings.create.call_count == 2
        assert embedding_service.get_cache_size() == 2

    @pytest.mark.asyncio
    async def test_should_handle_unexpected_errors_without_retry(self, embedding_service, mock_openai_client, mocker):
        """Test that unexpected errors are not retried."""
        # Arrange
        text = "Test text"
        mock_openai_client.embeddings.create.side_effect = RuntimeError("Unexpected error")

        # Mock asyncio.sleep to verify it's not called
        mock_sleep = mocker.patch("asyncio.sleep")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Unexpected error"):
            await embedding_service.generate_embedding(text)

        # Verify only one attempt was made (no retries for unexpected errors)
        assert mock_openai_client.embeddings.create.call_count == 1
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_use_exponential_backoff_for_retries(self, embedding_service, mock_openai_client, sample_embedding, mocker):
        """Test exponential backoff timing for retries."""
        # Arrange
        text = "Test text"
        mock_response = mocker.Mock()
        mock_response.data = [mocker.Mock(embedding=sample_embedding)]

        # First two calls fail, third succeeds
        mock_openai_client.embeddings.create.side_effect = [
            OpenAIError("Error 1"),
            OpenAIError("Error 2"),
            mock_response,
        ]

        # Mock asyncio.sleep to capture backoff times
        mock_sleep = mocker.patch("asyncio.sleep")

        # Act
        await embedding_service.generate_embedding(text, max_retries=3)

        # Assert
        # Verify exponential backoff: 2^0=1s, 2^1=2s
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 1  # First backoff: 1s
        assert mock_sleep.call_args_list[1][0][0] == 2  # Second backoff: 2s

    @pytest.mark.asyncio
    async def test_should_log_cache_hits_and_misses(self, embedding_service, mock_openai_client, sample_embedding, mocker):
        """Test logging of cache hits and misses."""
        # Arrange
        text = "Test text"
        mock_response = mocker.Mock()
        mock_response.data = [mocker.Mock(embedding=sample_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response

        mock_logger = mocker.patch("finwiz.supabase.services.embedding_service.logger")

        # Act
        await embedding_service.generate_embedding(text)  # Cache miss
        await embedding_service.generate_embedding(text)  # Cache hit

        # Assert
        # Verify cache miss was logged
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("Cache MISS" in call for call in debug_calls)
        assert any("Cache HIT" in call for call in debug_calls)
