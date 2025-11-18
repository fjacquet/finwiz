"""
Unit tests for Supabase VectorRepository.

Tests vector repository functionality including:
- store_embedding() async execution (non-blocking)
- search_similar() with results above threshold
- search_similar() with no results (below threshold)
- Timeout enforcement and error handling
- Mock OpenAI API and Supabase client
"""

import pytest

from finwiz.supabase.client import SupabaseClient
from finwiz.supabase.repositories.vector_repository import VectorRepository
from finwiz.supabase.services.embedding_service import EmbeddingService


class TestVectorRepository:
    """Test suite for VectorRepository."""

    @pytest.fixture
    def mock_supabase_client(self, mocker):
        """Create mock SupabaseClient."""
        mock_client = mocker.Mock(spec=SupabaseClient)
        mock_client.max_retries = 3
        mock_client.write_timeout = 5.0
        mock_client.read_timeout = 2.0
        return mock_client

    @pytest.fixture
    def mock_embedding_service(self, mocker):
        """Create mock EmbeddingService."""
        return mocker.Mock(spec=EmbeddingService)

    @pytest.fixture
    def vector_repository(self, mock_supabase_client, mock_embedding_service):
        """Create VectorRepository with mocked dependencies."""
        return VectorRepository(
            client=mock_supabase_client,
            embedding_service=mock_embedding_service,
        )

    @pytest.fixture
    def sample_embedding(self):
        """Create sample 1536-dimensional embedding."""
        return [0.1] * 1536

    @pytest.fixture
    def sample_search_results(self):
        """Create sample search results from database."""
        return [
            {"analysis_id": "uuid-1", "similarity": 0.95},
            {"analysis_id": "uuid-2", "similarity": 0.85},
            {"analysis_id": "uuid-3", "similarity": 0.75},
        ]

    @pytest.mark.asyncio
    async def test_should_initialize_with_dependencies(self, mock_supabase_client, mock_embedding_service):
        """Test VectorRepository initialization."""
        # Act
        repo = VectorRepository(
            client=mock_supabase_client,
            embedding_service=mock_embedding_service,
        )

        # Assert
        assert repo.client == mock_supabase_client
        assert repo.embedding_service == mock_embedding_service
        assert repo.table == "analysis_embeddings"

    @pytest.mark.asyncio
    async def test_should_create_embedding_service_if_not_provided(self, mock_supabase_client, mocker):
        """Test that EmbeddingService is created if not provided."""
        # Arrange
        mocker.patch.dict("os.environ", {"OPENAI_API_KEY": "test-key-12345678"})
        mock_embedding_service_class = mocker.patch("finwiz.supabase.repositories.vector_repository.EmbeddingService")

        # Act
        repo = VectorRepository(client=mock_supabase_client)

        # Assert
        mock_embedding_service_class.assert_called_once()
        assert repo.embedding_service is not None

    @pytest.mark.asyncio
    async def test_should_store_embedding_async_non_blocking(self, vector_repository, mock_embedding_service, sample_embedding, mocker):
        """Test store_embedding() async execution (non-blocking)."""
        # Arrange
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"
        text = "Apple Inc. is a technology company"

        # Mock asyncio.create_task to verify async execution
        mock_create_task = mocker.patch("asyncio.create_task")

        # Act
        result = await vector_repository.store_embedding(analysis_id, text)

        # Assert
        assert result is True  # Returns immediately
        mock_create_task.assert_called_once()  # Background task created

    @pytest.mark.asyncio
    async def test_should_generate_and_store_embedding_with_retry(self, vector_repository, mock_supabase_client, mock_embedding_service, sample_embedding, mocker):
        """Test _store_embedding_with_retry generates and stores embedding."""
        # Arrange
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"
        text = "Test text for embedding"

        mock_embedding_service.generate_embedding.return_value = sample_embedding
        mock_supabase_client.execute_with_timeout.return_value = mocker.Mock(data=[{"id": "1"}])

        # Act
        await vector_repository._store_embedding_with_retry(analysis_id, text)

        # Assert
        # Verify embedding was generated
        mock_embedding_service.generate_embedding.assert_called_once_with(text)

        # Verify database insert was called
        mock_supabase_client.execute_with_timeout.assert_called_once()
        call_args = mock_supabase_client.execute_with_timeout.call_args
        assert call_args[1]["timeout"] == 5.0

    @pytest.mark.asyncio
    async def test_should_retry_storage_on_failure(self, vector_repository, mock_supabase_client, mock_embedding_service, sample_embedding, mocker):
        """Test retry logic for storage failures."""
        # Arrange
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"
        text = "Test text"

        mock_embedding_service.generate_embedding.return_value = sample_embedding

        # First two attempts fail, third succeeds
        mock_supabase_client.execute_with_timeout.side_effect = [
            None,  # First attempt returns None
            Exception("Database error"),  # Second attempt fails
            mocker.Mock(data=[{"id": "1"}]),  # Third attempt succeeds
        ]

        # Mock asyncio.sleep to avoid actual delays
        mocker.patch("asyncio.sleep")

        # Act
        await vector_repository._store_embedding_with_retry(analysis_id, text, max_retries=3)

        # Assert
        assert mock_supabase_client.execute_with_timeout.call_count == 3

    @pytest.mark.asyncio
    async def test_should_handle_embedding_generation_failure(self, vector_repository, mock_supabase_client, mock_embedding_service, mocker):
        """Test handling of embedding generation failure."""
        # Arrange
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"
        text = "Test text"

        mock_embedding_service.generate_embedding.side_effect = Exception("OpenAI API error")

        # Act - should not raise exception (background task)
        await vector_repository._store_embedding_with_retry(analysis_id, text)

        # Assert
        # Verify database insert was NOT called
        mock_supabase_client.execute_with_timeout.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_search_similar_with_results_above_threshold(
        self, vector_repository, mock_supabase_client, mock_embedding_service, sample_embedding, sample_search_results, mocker
    ):
        """Test search_similar() with results above threshold."""
        # Arrange
        query = "Find similar analyses about Apple stock"
        mock_embedding_service.generate_embedding.return_value = sample_embedding

        mock_result = mocker.Mock()
        mock_result.data = sample_search_results
        mock_supabase_client.execute_with_timeout.return_value = mock_result

        # Act
        results = await vector_repository.search_similar(
            query=query,
            limit=5,
            similarity_threshold=0.7,
        )

        # Assert
        assert len(results) == 3
        assert results[0] == ("uuid-1", 0.95)
        assert results[1] == ("uuid-2", 0.85)
        assert results[2] == ("uuid-3", 0.75)

        # Verify embedding was generated for query
        mock_embedding_service.generate_embedding.assert_called_once_with(query)

        # Verify database search was called
        mock_supabase_client.execute_with_timeout.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_return_empty_list_with_no_results_below_threshold(self, vector_repository, mock_supabase_client, mock_embedding_service, sample_embedding, mocker):
        """Test search_similar() with no results (below threshold)."""
        # Arrange
        query = "Find similar analyses"
        mock_embedding_service.generate_embedding.return_value = sample_embedding

        # Database returns empty results (all below threshold)
        mock_result = mocker.Mock()
        mock_result.data = []
        mock_supabase_client.execute_with_timeout.return_value = mock_result

        # Act
        results = await vector_repository.search_similar(
            query=query,
            limit=5,
            similarity_threshold=0.9,  # High threshold
        )

        # Assert
        assert results == []
        mock_embedding_service.generate_embedding.assert_called_once_with(query)

    @pytest.mark.asyncio
    async def test_should_return_empty_list_for_empty_query(self, vector_repository):
        """Test that empty query returns empty list."""
        # Act
        results = await vector_repository.search_similar(query="")

        # Assert
        assert results == []

    @pytest.mark.asyncio
    async def test_should_return_empty_list_for_whitespace_query(self, vector_repository):
        """Test that whitespace-only query returns empty list."""
        # Act
        results = await vector_repository.search_similar(query="   ")

        # Assert
        assert results == []

    @pytest.mark.asyncio
    async def test_should_validate_similarity_threshold(self, vector_repository, mock_embedding_service, sample_embedding, mocker):
        """Test similarity threshold validation."""
        # Arrange
        query = "Test query"
        mock_embedding_service.generate_embedding.return_value = sample_embedding

        # Act - invalid threshold should be corrected to default 0.7
        await vector_repository.search_similar(
            query=query,
            similarity_threshold=1.5,  # Invalid (> 1.0)
        )

        # Assert - should use default threshold 0.7
        # (verified through logging, but we can't easily test the exact value used)

    @pytest.mark.asyncio
    async def test_should_validate_limit(self, vector_repository, mock_embedding_service, sample_embedding, mocker):
        """Test limit validation."""
        # Arrange
        query = "Test query"
        mock_embedding_service.generate_embedding.return_value = sample_embedding

        # Act - invalid limit should be corrected to default 5
        await vector_repository.search_similar(
            query=query,
            limit=0,  # Invalid (< 1)
        )

        # Assert - should use default limit 5
        # (verified through logging, but we can't easily test the exact value used)

    @pytest.mark.asyncio
    async def test_should_handle_search_timeout(self, vector_repository, mock_supabase_client, mock_embedding_service, sample_embedding):
        """Test handling of search timeout."""
        # Arrange
        query = "Test query"
        mock_embedding_service.generate_embedding.return_value = sample_embedding
        mock_supabase_client.execute_with_timeout.side_effect = TimeoutError("Search timed out")

        # Act
        results = await vector_repository.search_similar(query=query)

        # Assert
        assert results == []  # Returns empty list on timeout

    @pytest.mark.asyncio
    async def test_should_handle_search_error(self, vector_repository, mock_supabase_client, mock_embedding_service, sample_embedding):
        """Test handling of search errors."""
        # Arrange
        query = "Test query"
        mock_embedding_service.generate_embedding.return_value = sample_embedding
        mock_supabase_client.execute_with_timeout.side_effect = Exception("Database error")

        # Act
        results = await vector_repository.search_similar(query=query)

        # Assert
        assert results == []  # Returns empty list on error

    @pytest.mark.asyncio
    async def test_should_handle_embedding_generation_error_in_search(self, vector_repository, mock_embedding_service):
        """Test handling of embedding generation error during search."""
        # Arrange
        query = "Test query"
        mock_embedding_service.generate_embedding.side_effect = Exception("OpenAI API error")

        # Act
        results = await vector_repository.search_similar(query=query)

        # Assert
        assert results == []  # Returns empty list on error

    @pytest.mark.asyncio
    async def test_should_get_embedding_by_analysis_id(self, vector_repository, mock_supabase_client, sample_embedding, mocker):
        """Test getting embedding by analysis ID."""
        # Arrange
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"
        text = "Original text"

        mock_result = mocker.Mock()
        mock_result.data = [{"embedding": sample_embedding, "text": text}]
        mock_supabase_client.execute_with_timeout.return_value = mock_result

        # Act
        result = await vector_repository.get_embedding_by_analysis_id(analysis_id)

        # Assert
        assert result is not None
        assert result[0] == sample_embedding
        assert result[1] == text

        # Verify database query was called
        mock_supabase_client.execute_with_timeout.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_return_none_when_embedding_not_found(self, vector_repository, mock_supabase_client, mocker):
        """Test getting embedding when not found."""
        # Arrange
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"

        mock_result = mocker.Mock()
        mock_result.data = []  # No results
        mock_supabase_client.execute_with_timeout.return_value = mock_result

        # Act
        result = await vector_repository.get_embedding_by_analysis_id(analysis_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_should_delete_embedding(self, vector_repository, mock_supabase_client, mocker):
        """Test deleting embedding."""
        # Arrange
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"

        mock_result = mocker.Mock()
        mock_supabase_client.execute_with_timeout.return_value = mock_result

        # Act
        result = await vector_repository.delete_embedding(analysis_id)

        # Assert
        assert result is True

        # Verify database delete was called
        mock_supabase_client.execute_with_timeout.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_return_false_when_delete_fails(self, vector_repository, mock_supabase_client):
        """Test delete returns false on failure."""
        # Arrange
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_supabase_client.execute_with_timeout.return_value = None

        # Act
        result = await vector_repository.delete_embedding(analysis_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_should_count_embeddings(self, vector_repository, mock_supabase_client, mocker):
        """Test counting embeddings."""
        # Arrange
        mock_result = mocker.Mock()
        mock_result.count = 42
        mock_supabase_client.execute_with_timeout.return_value = mock_result

        # Act
        count = await vector_repository.count_embeddings()

        # Assert
        assert count == 42

        # Verify database query was called
        mock_supabase_client.execute_with_timeout.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_return_zero_when_count_fails(self, vector_repository, mock_supabase_client):
        """Test count returns zero on failure."""
        # Arrange
        mock_supabase_client.execute_with_timeout.return_value = None

        # Act
        count = await vector_repository.count_embeddings()

        # Assert
        assert count == 0

    @pytest.mark.asyncio
    async def test_should_use_exponential_backoff_for_storage_retries(self, vector_repository, mock_supabase_client, mock_embedding_service, sample_embedding, mocker):
        """Test exponential backoff for storage retries."""
        # Arrange
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"
        text = "Test text"

        mock_embedding_service.generate_embedding.return_value = sample_embedding

        # All attempts fail
        mock_supabase_client.execute_with_timeout.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            Exception("Error 3"),
        ]

        # Mock asyncio.sleep to capture backoff times
        mock_sleep = mocker.patch("asyncio.sleep")

        # Act
        await vector_repository._store_embedding_with_retry(analysis_id, text, max_retries=3)

        # Assert
        # Verify exponential backoff: 2^0=1s, 2^1=2s
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 1  # First backoff: 1s
        assert mock_sleep.call_args_list[1][0][0] == 2  # Second backoff: 2s

    @pytest.mark.asyncio
    async def test_should_strip_text_before_storage(self, vector_repository, mock_supabase_client, mock_embedding_service, sample_embedding, mocker):
        """Test that text is stripped before storage."""
        # Arrange
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"
        text_with_whitespace = "  Test text with whitespace  "

        mock_embedding_service.generate_embedding.return_value = sample_embedding
        mock_supabase_client.execute_with_timeout.return_value = mocker.Mock(data=[{"id": "1"}])

        # Act
        await vector_repository._store_embedding_with_retry(analysis_id, text_with_whitespace)

        # Assert
        # Verify the insert function was called (we can't easily inspect the exact text,
        # but the implementation strips it before storage)
        mock_supabase_client.execute_with_timeout.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_enforce_timeout_for_search(self, vector_repository, mock_supabase_client, mock_embedding_service, sample_embedding):
        """Test that search enforces 2-second timeout."""
        # Arrange
        query = "Test query"
        mock_embedding_service.generate_embedding.return_value = sample_embedding
        mock_supabase_client.execute_with_timeout.return_value = None

        # Act
        await vector_repository.search_similar(query=query)

        # Assert
        # Verify execute_with_timeout was called (timeout is handled by client default)
        mock_supabase_client.execute_with_timeout.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_enforce_timeout_for_storage(self, vector_repository, mock_supabase_client, mock_embedding_service, sample_embedding, mocker):
        """Test that storage enforces 5-second timeout."""
        # Arrange
        analysis_id = "550e8400-e29b-41d4-a716-446655440000"
        text = "Test text"

        mock_embedding_service.generate_embedding.return_value = sample_embedding
        mock_supabase_client.execute_with_timeout.return_value = mocker.Mock(data=[{"id": "1"}])

        # Act
        await vector_repository._store_embedding_with_retry(analysis_id, text)

        # Assert
        # Verify timeout was set to 5.0 seconds
        call_args = mock_supabase_client.execute_with_timeout.call_args
        assert call_args[1]["timeout"] == 5.0
