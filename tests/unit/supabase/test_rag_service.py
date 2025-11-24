"""
Unit tests for Supabase HistoricalAnalysisService (RAG service).

Tests RAG service functionality including:
- get_context() with similar analyses found
- get_context() with no similar analyses (returns None)
- get_context() with vector search timeout
- Context formatting for agent consumption
- Mock VectorRepository and AnalysisRepository
"""

from datetime import datetime

import pytest
from pytest import approx

from finwiz.supabase.models import AnalysisRecord
from finwiz.supabase.repositories.analysis_repository import AnalysisRepository
from finwiz.supabase.repositories.vector_repository import VectorRepository
from finwiz.supabase.services.rag_service import HistoricalAnalysisService


class TestHistoricalAnalysisService:
    """Test suite for HistoricalAnalysisService."""

    @pytest.fixture
    def mock_vector_repo(self, mocker):
        """Create mock VectorRepository."""
        return mocker.Mock(spec=VectorRepository)

    @pytest.fixture
    def mock_analysis_repo(self, mocker):
        """Create mock AnalysisRepository."""
        return mocker.Mock(spec=AnalysisRepository)

    @pytest.fixture
    def rag_service(self, mock_vector_repo, mock_analysis_repo):
        """Create HistoricalAnalysisService with mocked dependencies."""
        return HistoricalAnalysisService(
            vector_repo=mock_vector_repo,
            analysis_repo=mock_analysis_repo,
        )

    @pytest.fixture
    def sample_analysis_records(self):
        """Create sample AnalysisRecord objects for testing."""
        return [
            AnalysisRecord(
                id="uuid-1",
                ticker="AAPL",
                asset_class="stock",
                composite_score=0.90,
                grade="A+",
                recommendation="BUY",
                export_json={
                    "ticker": "AAPL",
                    "summary": "Strong fundamentals with excellent growth prospects",
                },
                created_at=datetime(2025, 10, 1, 12, 0, 0),
                updated_at=datetime(2025, 10, 1, 12, 0, 0),
            ),
            AnalysisRecord(
                id="uuid-2",
                ticker="MSFT",
                asset_class="stock",
                composite_score=0.85,
                grade="A",
                recommendation="BUY",
                export_json={
                    "ticker": "MSFT",
                    "executive_summary": "Solid cloud business with consistent revenue growth",
                },
                created_at=datetime(2025, 10, 2, 12, 0, 0),
                updated_at=datetime(2025, 10, 2, 12, 0, 0),
            ),
            AnalysisRecord(
                id="uuid-3",
                ticker="GOOGL",
                asset_class="stock",
                composite_score=0.80,
                grade="A-",
                recommendation="HOLD",
                export_json={
                    "ticker": "GOOGL",
                    "key_findings": "Strong advertising revenue but regulatory concerns",
                },
                created_at=datetime(2025, 10, 3, 12, 0, 0),
                updated_at=datetime(2025, 10, 3, 12, 0, 0),
            ),
        ]

    @pytest.fixture
    def sample_vector_search_results(self):
        """Create sample vector search results."""
        return [
            ("uuid-1", 0.95),
            ("uuid-2", 0.85),
            ("uuid-3", 0.75),
        ]

    @pytest.mark.asyncio
    async def test_should_initialize_with_dependencies(self, mock_vector_repo, mock_analysis_repo):
        """Test HistoricalAnalysisService initialization."""
        # Act
        service = HistoricalAnalysisService(
            vector_repo=mock_vector_repo,
            analysis_repo=mock_analysis_repo,
        )

        # Assert
        assert service.vector_repo == mock_vector_repo
        assert service.analysis_repo == mock_analysis_repo

    @pytest.mark.asyncio
    async def test_should_return_context_when_similar_analyses_found(
        self,
        rag_service,
        mock_vector_repo,
        mock_analysis_repo,
        sample_vector_search_results,
        sample_analysis_records,
    ):
        """Test get_context() with similar analyses found."""
        # Arrange
        query = "Analysis of Apple stock"
        mock_vector_repo.search_similar.return_value = sample_vector_search_results

        # Mock analysis retrieval for each ID
        mock_analysis_repo.get_by_id.side_effect = sample_analysis_records

        # Act
        context = await rag_service.get_context(query=query, limit=3)

        # Assert
        assert context is not None
        assert len(context) == 3

        # Verify first context entry
        assert context[0]["ticker"] == "AAPL"
        assert context[0]["asset_class"] == "stock"
        assert context[0]["grade"] == "A+"
        assert context[0]["recommendation"] == "BUY"
        assert context[0]["composite_score"] == approx(0.90)
        assert context[0]["similarity"] == approx(0.95)
        assert "Strong fundamentals" in context[0]["summary"]
        assert context[0]["created_at"] == "2025-10-01T12:00:00"

        # Verify vector search was called
        mock_vector_repo.search_similar.assert_called_once_with(
            query=query,
            limit=3,
            similarity_threshold=0.7,
        )

        # Verify analysis retrieval was called for each ID
        assert mock_analysis_repo.get_by_id.call_count == 3
        mock_analysis_repo.get_by_id.assert_any_call("uuid-1")
        mock_analysis_repo.get_by_id.assert_any_call("uuid-2")
        mock_analysis_repo.get_by_id.assert_any_call("uuid-3")

    @pytest.mark.asyncio
    async def test_should_return_none_when_no_similar_analyses_found(self, rag_service, mock_vector_repo):
        """Test get_context() with no similar analyses (returns None)."""
        # Arrange
        query = "Analysis of unknown stock"
        mock_vector_repo.search_similar.return_value = []  # No results

        # Act
        context = await rag_service.get_context(query=query)

        # Assert
        assert context is None
        mock_vector_repo.search_similar.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_return_none_when_vector_search_times_out(self, rag_service, mock_vector_repo):
        """Test get_context() with vector search timeout."""
        # Arrange
        query = "Analysis of stock"
        mock_vector_repo.search_similar.side_effect = TimeoutError("Search timed out")

        # Act
        context = await rag_service.get_context(query=query)

        # Assert
        assert context is None
        mock_vector_repo.search_similar.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_return_none_when_vector_search_fails(self, rag_service, mock_vector_repo):
        """Test get_context() with vector search error."""
        # Arrange
        query = "Analysis of stock"
        mock_vector_repo.search_similar.side_effect = Exception("Database error")

        # Act
        context = await rag_service.get_context(query=query)

        # Assert
        assert context is None
        mock_vector_repo.search_similar.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_return_none_for_empty_query(self, rag_service):
        """Test that empty query returns None."""
        # Act
        context = await rag_service.get_context(query="")

        # Assert
        assert context is None

    @pytest.mark.asyncio
    async def test_should_return_none_for_whitespace_query(self, rag_service):
        """Test that whitespace-only query returns None."""
        # Act
        context = await rag_service.get_context(query="   ")

        # Assert
        assert context is None

    @pytest.mark.asyncio
    async def test_should_validate_limit_parameter(self, rag_service, mock_vector_repo, mocker):
        """Test limit parameter validation."""
        # Arrange
        query = "Test query"
        mock_vector_repo.search_similar.return_value = []

        # Act - invalid limit should be corrected to default 3
        await rag_service.get_context(query=query, limit=0)

        # Assert - should use default limit 3
        call_args = mock_vector_repo.search_similar.call_args
        assert call_args[1]["limit"] == 3

    @pytest.mark.asyncio
    async def test_should_validate_similarity_threshold_parameter(self, rag_service, mock_vector_repo):
        """Test similarity threshold parameter validation."""
        # Arrange
        query = "Test query"
        mock_vector_repo.search_similar.return_value = []

        # Act - invalid threshold should be corrected to default 0.7
        await rag_service.get_context(query=query, similarity_threshold=1.5)

        # Assert - should use default threshold 0.7
        call_args = mock_vector_repo.search_similar.call_args
        assert call_args[1]["similarity_threshold"] == approx(0.7)

    @pytest.mark.asyncio
    async def test_should_handle_analysis_retrieval_failure_gracefully(
        self,
        rag_service,
        mock_vector_repo,
        mock_analysis_repo,
        sample_vector_search_results,
        sample_analysis_records,
    ):
        """Test handling of analysis retrieval failure for some analyses."""
        # Arrange
        query = "Test query"
        mock_vector_repo.search_similar.return_value = sample_vector_search_results

        # First analysis succeeds, second fails, third succeeds
        mock_analysis_repo.get_by_id.side_effect = [
            sample_analysis_records[0],
            Exception("Database error"),
            sample_analysis_records[2],
        ]

        # Act
        context = await rag_service.get_context(query=query, limit=3)

        # Assert
        assert context is not None
        assert len(context) == 2  # Only 2 successful retrievals
        assert context[0]["ticker"] == "AAPL"
        assert context[1]["ticker"] == "GOOGL"

    @pytest.mark.asyncio
    async def test_should_return_none_when_all_analysis_retrievals_fail(
        self,
        rag_service,
        mock_vector_repo,
        mock_analysis_repo,
        sample_vector_search_results,
    ):
        """Test that None is returned when all analysis retrievals fail."""
        # Arrange
        query = "Test query"
        mock_vector_repo.search_similar.return_value = sample_vector_search_results
        mock_analysis_repo.get_by_id.side_effect = Exception("Database error")

        # Act
        context = await rag_service.get_context(query=query, limit=3)

        # Assert
        assert context is None

    @pytest.mark.asyncio
    async def test_should_handle_analysis_not_found(
        self,
        rag_service,
        mock_vector_repo,
        mock_analysis_repo,
        sample_vector_search_results,
        sample_analysis_records,
    ):
        """Test handling when some analyses are not found."""
        # Arrange
        query = "Test query"
        mock_vector_repo.search_similar.return_value = sample_vector_search_results

        # First analysis found, second not found, third found
        mock_analysis_repo.get_by_id.side_effect = [
            sample_analysis_records[0],
            None,  # Not found
            sample_analysis_records[2],
        ]

        # Act
        context = await rag_service.get_context(query=query, limit=3)

        # Assert
        assert context is not None
        assert len(context) == 2  # Only 2 found
        assert context[0]["ticker"] == "AAPL"
        assert context[1]["ticker"] == "GOOGL"

    @pytest.mark.asyncio
    async def test_should_extract_summary_from_different_fields(
        self,
        rag_service,
        mock_vector_repo,
        mock_analysis_repo,
        sample_vector_search_results,
        sample_analysis_records,
    ):
        """Test that summary is extracted from various field names."""
        # Arrange
        query = "Test query"
        mock_vector_repo.search_similar.return_value = sample_vector_search_results
        mock_analysis_repo.get_by_id.side_effect = sample_analysis_records

        # Act
        context = await rag_service.get_context(query=query, limit=3)

        # Assert
        assert context is not None
        assert len(context) == 3

        # First record has "summary" field
        assert "Strong fundamentals" in context[0]["summary"]

        # Second record has "executive_summary" field
        assert "Solid cloud business" in context[1]["summary"]

        # Third record has "key_findings" field
        assert "Strong advertising revenue" in context[2]["summary"]

    @pytest.mark.asyncio
    async def test_should_handle_missing_summary_field(
        self,
        rag_service,
        mock_vector_repo,
        mock_analysis_repo,
        sample_vector_search_results,
    ):
        """Test handling when export_json has no summary field."""
        # Arrange
        query = "Test query"
        mock_vector_repo.search_similar.return_value = [("uuid-1", 0.95)]

        analysis_without_summary = AnalysisRecord(
            id="uuid-1",
            ticker="AAPL",
            asset_class="stock",
            composite_score=0.90,
            grade="A+",
            recommendation="BUY",
            export_json={"ticker": "AAPL"},  # No summary field
            created_at=datetime(2025, 10, 1, 12, 0, 0),
            updated_at=datetime(2025, 10, 1, 12, 0, 0),
        )

        mock_analysis_repo.get_by_id.return_value = analysis_without_summary

        # Act
        context = await rag_service.get_context(query=query, limit=1)

        # Assert
        assert context is not None
        assert len(context) == 1
        assert context[0]["summary"] == ""  # Empty string when no summary

    @pytest.mark.asyncio
    async def test_should_format_context_for_agent_consumption(self, rag_service):
        """Test context formatting for agent consumption."""
        # Arrange
        context = [
            {
                "ticker": "AAPL",
                "asset_class": "stock",
                "grade": "A+",
                "recommendation": "BUY",
                "similarity": 0.95,
                "summary": "Strong fundamentals with excellent growth prospects",
            },
            {
                "ticker": "MSFT",
                "asset_class": "stock",
                "grade": "A",
                "recommendation": "BUY",
                "similarity": 0.85,
                "summary": "Solid cloud business with consistent revenue growth",
            },
        ]
        query = "Analysis of tech stocks"

        # Act
        formatted = rag_service.format_context_for_agent(context, query)

        # Assert
        assert formatted != ""
        assert "Historical Context for: Analysis of tech stocks" in formatted
        assert "Similar Past Analyses:" in formatted
        assert "1. AAPL (STOCK)" in formatted
        assert "Grade: A+ | Recommendation: BUY" in formatted
        assert "Similarity: 95.00%" in formatted
        assert "Strong fundamentals" in formatted
        assert "2. MSFT (STOCK)" in formatted
        assert "Grade: A | Recommendation: BUY" in formatted
        assert "Similarity: 85.00%" in formatted
        assert "Solid cloud business" in formatted

    @pytest.mark.asyncio
    async def test_should_return_empty_string_for_none_context(self, rag_service):
        """Test that None context returns empty string."""
        # Act
        formatted = rag_service.format_context_for_agent(None)

        # Assert
        assert formatted == ""

    @pytest.mark.asyncio
    async def test_should_return_empty_string_for_empty_context(self, rag_service):
        """Test that empty context list returns empty string."""
        # Act
        formatted = rag_service.format_context_for_agent([])

        # Assert
        assert formatted == ""

    @pytest.mark.asyncio
    async def test_should_truncate_long_summaries_in_formatted_context(self, rag_service):
        """Test that long summaries are truncated in formatted output."""
        # Arrange
        long_summary = "A" * 300  # 300 characters
        context = [
            {
                "ticker": "AAPL",
                "asset_class": "stock",
                "grade": "A+",
                "recommendation": "BUY",
                "similarity": 0.95,
                "summary": long_summary,
            }
        ]

        # Act
        formatted = rag_service.format_context_for_agent(context)

        # Assert
        assert formatted != ""
        # Summary should be truncated to 200 chars + "..."
        assert "..." in formatted
        assert len(formatted) < len(long_summary) + 200  # Much shorter than original

    @pytest.mark.asyncio
    async def test_should_handle_missing_fields_in_context_formatting(self, rag_service):
        """Test formatting with missing fields in context."""
        # Arrange
        context = [
            {
                "ticker": "AAPL",
                # Missing other fields
            }
        ]

        # Act
        formatted = rag_service.format_context_for_agent(context)

        # Assert
        assert formatted != ""
        assert "AAPL (UNKNOWN)" in formatted  # Default for missing asset_class
        assert "Grade: N/A" in formatted  # Default for missing grade
        assert "Recommendation: N/A" in formatted  # Default for missing recommendation

    @pytest.mark.asyncio
    async def test_should_get_context_for_ticker(
        self,
        rag_service,
        mock_vector_repo,
        mock_analysis_repo,
        sample_vector_search_results,
        sample_analysis_records,
    ):
        """Test get_context_for_ticker() convenience method."""
        # Arrange
        ticker = "AAPL"
        asset_class = "stock"
        mock_vector_repo.search_similar.return_value = sample_vector_search_results
        mock_analysis_repo.get_by_id.side_effect = sample_analysis_records

        # Act
        context = await rag_service.get_context_for_ticker(
            ticker=ticker,
            asset_class=asset_class,
            limit=3,
        )

        # Assert
        assert context is not None
        assert len(context) == 3

        # Verify query was constructed correctly
        call_args = mock_vector_repo.search_similar.call_args
        assert "AAPL" in call_args[1]["query"]
        assert "stock" in call_args[1]["query"]
        assert call_args[1]["limit"] == 3
        assert call_args[1]["similarity_threshold"] == approx(0.7)

    @pytest.mark.asyncio
    async def test_should_use_custom_limit_in_get_context(self, rag_service, mock_vector_repo):
        """Test that custom limit is used in get_context()."""
        # Arrange
        query = "Test query"
        mock_vector_repo.search_similar.return_value = []

        # Act
        await rag_service.get_context(query=query, limit=5)

        # Assert
        call_args = mock_vector_repo.search_similar.call_args
        assert call_args[1]["limit"] == 5

    @pytest.mark.asyncio
    async def test_should_use_custom_similarity_threshold_in_get_context(self, rag_service, mock_vector_repo):
        """Test that custom similarity threshold is used in get_context()."""
        # Arrange
        query = "Test query"
        mock_vector_repo.search_similar.return_value = []

        # Act
        await rag_service.get_context(query=query, similarity_threshold=0.8)

        # Assert
        call_args = mock_vector_repo.search_similar.call_args
        assert call_args[1]["similarity_threshold"] == approx(0.8)

    @pytest.mark.asyncio
    async def test_should_log_context_retrieval_success(
        self,
        rag_service,
        mock_vector_repo,
        mock_analysis_repo,
        sample_vector_search_results,
        sample_analysis_records,
        mocker,
    ):
        """Test logging of successful context retrieval."""
        # Arrange
        query = "Test query"
        mock_vector_repo.search_similar.return_value = sample_vector_search_results
        mock_analysis_repo.get_by_id.side_effect = sample_analysis_records

        mock_logger = mocker.patch("finwiz.supabase.services.rag_service.logger")

        # Act
        await rag_service.get_context(query=query, limit=3)

        # Assert
        # Verify success was logged
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Retrieved 3 analyses" in call for call in info_calls)

    @pytest.mark.asyncio
    async def test_should_log_no_similar_analyses_found(self, rag_service, mock_vector_repo, mocker):
        """Test logging when no similar analyses found."""
        # Arrange
        query = "Test query"
        mock_vector_repo.search_similar.return_value = []

        mock_logger = mocker.patch("finwiz.supabase.services.rag_service.logger")

        # Act
        await rag_service.get_context(query=query)

        # Assert
        # Verify no results was logged
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("No similar analyses found" in call for call in info_calls)

    @pytest.mark.asyncio
    async def test_should_format_context_without_query(self, rag_service):
        """Test formatting context without query parameter."""
        # Arrange
        context = [
            {
                "ticker": "AAPL",
                "asset_class": "stock",
                "grade": "A+",
                "recommendation": "BUY",
                "similarity": 0.95,
                "summary": "Strong fundamentals",
            }
        ]

        # Act
        formatted = rag_service.format_context_for_agent(context)

        # Assert
        assert formatted != ""
        assert "Historical Context for:" not in formatted  # No query line
        assert "Similar Past Analyses:" in formatted
        assert "AAPL (STOCK)" in formatted

    @pytest.mark.asyncio
    async def test_should_handle_non_dict_export_json(
        self,
        rag_service,
        mock_vector_repo,
        mock_analysis_repo,
        sample_vector_search_results,
    ):
        """Test handling when export_json is not a dict."""
        # Arrange
        query = "Test query"
        mock_vector_repo.search_similar.return_value = [("uuid-1", 0.95)]

        analysis_with_non_dict_export = AnalysisRecord(
            id="uuid-1",
            ticker="AAPL",
            asset_class="stock",
            composite_score=0.90,
            grade="A+",
            recommendation="BUY",
            export_json={},  # Empty dict (edge case)
            created_at=datetime(2025, 10, 1, 12, 0, 0),
            updated_at=datetime(2025, 10, 1, 12, 0, 0),
        )

        mock_analysis_repo.get_by_id.return_value = analysis_with_non_dict_export

        # Act
        context = await rag_service.get_context(query=query, limit=1)

        # Assert
        assert context is not None
        assert len(context) == 1
        assert context[0]["summary"] == ""  # Empty string when no summary
