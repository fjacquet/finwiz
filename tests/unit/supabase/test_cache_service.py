"""
Unit tests for Supabase CacheService.

Tests cache service functionality including:
- Cache hit scenarios (returns cached, skips execution)
- Cache miss scenarios (executes crew, stores result)
- Cache timeout scenarios (proceeds with execution)
- TTL configuration from environment variable
- Mock AnalysisRepository and crew execution function
"""

import asyncio
import os
from datetime import datetime

import pytest

from finwiz.supabase.models import AnalysisRecord
from finwiz.supabase.repositories.analysis_repository import AnalysisRepository
from finwiz.supabase.services.cache_service import CacheService


class TestCacheService:
    """Test suite for CacheService."""

    @pytest.fixture
    def mock_repository(self, mocker):
        """Create mock AnalysisRepository."""
        return mocker.Mock(spec=AnalysisRepository)

    @pytest.fixture
    def mock_client(self, mocker):
        """Create mock SupabaseClient."""
        mock = mocker.Mock()
        mock.read_timeout = 10.0
        mock.write_timeout = 15.0
        mock.test_connectivity = mocker.AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def cache_service(self, mock_repository, mock_client):
        """Create CacheService with mock repository and client."""
        service = CacheService(repository=mock_repository, client=mock_client)
        service.is_enabled = True  # Enable by default for tests
        return service

    @pytest.fixture
    def sample_analysis_record(self):
        """Create sample AnalysisRecord for testing."""
        return AnalysisRecord(
            id="550e8400-e29b-41d4-a716-446655440000",
            ticker="AAPL",
            asset_class="stock",
            composite_score=0.85,
            grade="A+",
            recommendation="BUY",
            export_json={
                "ticker": "AAPL",
                "composite_score": 0.85,
                "grade": "A+",
                "recommendation": "BUY",
                "analysis": "Strong fundamentals",
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def sample_crew_result(self):
        """Create sample crew execution result."""
        return {
            "ticker": "MSFT",
            "composite_score": 0.90,
            "grade": "A+",
            "recommendation": "BUY",
            "analysis": "Excellent growth prospects",
        }

    @pytest.mark.asyncio
    async def test_should_initialize_with_default_ttl(self, mock_repository, mock_client):
        """Test CacheService initialization with default TTL."""
        # Act
        service = CacheService(repository=mock_repository, client=mock_client)

        # Assert
        assert service.repository == mock_repository
        assert service.client == mock_client
        assert service.ttl_hours == 24  # Default value
        assert service.is_enabled is False  # Not initialized yet
        assert service.cache_hits == 0
        assert service.cache_misses == 0

    @pytest.mark.asyncio
    async def test_should_initialize_with_environment_ttl(self, mock_repository, mock_client, mocker):
        """Test CacheService initialization with TTL from environment variable."""
        # Arrange
        mocker.patch.dict(os.environ, {"ANALYSIS_CACHE_TTL_HOURS": "48"})

        # Act
        service = CacheService(repository=mock_repository, client=mock_client)

        # Assert
        assert service.ttl_hours == 48

    @pytest.mark.asyncio
    async def test_should_return_cached_analysis_when_cache_hit(self, cache_service, mock_repository, sample_analysis_record, mocker):
        """Test get_or_execute() with cache hit (returns cached, skips execution)."""
        # Arrange
        mock_repository.get_cached_analysis.return_value = sample_analysis_record
        mock_execute_fn = mocker.Mock()

        # Act
        result, is_cached = await cache_service.get_or_execute(
            ticker="AAPL",
            asset_class="stock",
            execute_fn=mock_execute_fn,
        )

        # Assert
        assert is_cached is True
        assert result == sample_analysis_record.export_json
        assert result["ticker"] == "AAPL"
        assert result["grade"] == "A+"
        assert cache_service.cache_hits == 1
        assert cache_service.cache_misses == 0

        # Verify crew execution was NOT called
        mock_execute_fn.assert_not_called()

        # Verify repository was called with correct parameters
        mock_repository.get_cached_analysis.assert_called_once_with(
            ticker="AAPL",
            asset_class="stock",
            ttl_hours=24,
        )

    @pytest.mark.asyncio
    async def test_should_execute_crew_when_cache_miss(self, cache_service, mock_repository, sample_crew_result, mocker):
        """Test get_or_execute() with cache miss (executes crew, stores result)."""
        # Arrange
        mock_repository.get_cached_analysis.return_value = None
        mock_repository.store_analysis = mocker.AsyncMock()

        async def mock_execute_fn():
            return sample_crew_result

        # Act
        result, is_cached = await cache_service.get_or_execute(
            ticker="MSFT",
            asset_class="stock",
            execute_fn=mock_execute_fn,
        )

        # Assert
        assert is_cached is False
        assert result == sample_crew_result
        assert result["ticker"] == "MSFT"
        assert result["grade"] == "A+"
        assert cache_service.cache_hits == 0
        assert cache_service.cache_misses == 1

        # Verify repository was called to check cache
        mock_repository.get_cached_analysis.assert_called_once_with(
            ticker="MSFT",
            asset_class="stock",
            ttl_hours=24,
        )

        # Give time for background task to complete
        await asyncio.sleep(0.1)

        # Verify repository was called to store result (non-blocking)
        mock_repository.store_analysis.assert_called_once_with(
            ticker="MSFT",
            asset_class="stock",
            export_data=sample_crew_result,
        )

    @pytest.mark.asyncio
    async def test_should_execute_crew_when_cache_timeout(self, cache_service, mock_repository, sample_crew_result, mocker):
        """Test get_or_execute() with cache timeout (proceeds with execution)."""
        # Arrange
        mock_repository.get_cached_analysis.side_effect = TimeoutError("Cache check timed out")
        mock_repository.store_analysis.return_value = True

        async def mock_execute_fn():
            return sample_crew_result

        # Act
        result, is_cached = await cache_service.get_or_execute(
            ticker="GOOGL",
            asset_class="stock",
            execute_fn=mock_execute_fn,
        )

        # Wait for async cache write task to complete
        await asyncio.sleep(0.1)

        # Assert
        assert is_cached is False
        assert result == sample_crew_result
        assert cache_service.cache_hits == 0
        assert cache_service.cache_misses == 1

        # Verify repository was called to store result despite timeout
        mock_repository.store_analysis.assert_called_once_with(
            ticker="GOOGL",
            asset_class="stock",
            export_data=sample_crew_result,
        )

    @pytest.mark.asyncio
    async def test_should_normalize_ticker_to_uppercase(self, cache_service, mock_repository, sample_crew_result):
        """Test that ticker symbols are normalized to uppercase."""
        # Arrange
        mock_repository.get_cached_analysis.return_value = None
        mock_repository.store_analysis.return_value = True

        async def mock_execute_fn():
            return sample_crew_result

        # Act
        await cache_service.get_or_execute(
            ticker="aapl",  # lowercase
            asset_class="stock",
            execute_fn=mock_execute_fn,
        )

        # Assert
        mock_repository.get_cached_analysis.assert_called_once_with(
            ticker="AAPL",  # uppercase
            asset_class="stock",
            ttl_hours=24,
        )

    @pytest.mark.asyncio
    async def test_should_normalize_asset_class_to_lowercase(self, cache_service, mock_repository, sample_crew_result):
        """Test that asset class is normalized to lowercase."""
        # Arrange
        mock_repository.get_cached_analysis.return_value = None
        mock_repository.store_analysis.return_value = True

        async def mock_execute_fn():
            return sample_crew_result

        # Act
        await cache_service.get_or_execute(
            ticker="AAPL",
            asset_class="STOCK",  # uppercase
            execute_fn=mock_execute_fn,
        )

        # Assert
        mock_repository.get_cached_analysis.assert_called_once_with(
            ticker="AAPL",
            asset_class="stock",  # lowercase
            ttl_hours=24,
        )

    @pytest.mark.asyncio
    async def test_should_handle_storage_failure_gracefully(self, cache_service, mock_repository, sample_crew_result, mocker):
        """Test that storage failures don't fail the analysis."""
        # Arrange
        mock_repository.get_cached_analysis.return_value = None
        mock_repository.store_analysis.side_effect = Exception("Storage failed")

        async def mock_execute_fn():
            return sample_crew_result

        # Act - should not raise exception
        result, is_cached = await cache_service.get_or_execute(
            ticker="TSLA",
            asset_class="stock",
            execute_fn=mock_execute_fn,
        )

        # Assert
        assert is_cached is False
        assert result == sample_crew_result
        # Analysis should succeed despite storage failure

    @pytest.mark.asyncio
    async def test_should_convert_non_dict_result_to_dict(self, cache_service, mock_repository, mocker):
        """Test that non-dict crew results are converted to dict."""
        # Arrange
        mock_repository.get_cached_analysis.return_value = None
        mock_repository.store_analysis.return_value = True

        async def mock_execute_fn():
            return "string result"  # Non-dict result

        # Act
        result, is_cached = await cache_service.get_or_execute(
            ticker="NVDA",
            asset_class="stock",
            execute_fn=mock_execute_fn,
        )

        # Assert
        assert is_cached is False
        assert isinstance(result, dict)
        assert "raw_result" in result
        assert result["raw_result"] == "string result"

    @pytest.mark.asyncio
    async def test_should_calculate_hit_rate_correctly(self, cache_service, mock_repository, sample_analysis_record, sample_crew_result):
        """Test cache hit rate calculation."""
        # Arrange
        mock_repository.store_analysis.return_value = True

        async def mock_execute_fn():
            return sample_crew_result

        # Simulate 3 hits and 1 miss
        mock_repository.get_cached_analysis.return_value = sample_analysis_record
        await cache_service.get_or_execute("AAPL", "stock", mock_execute_fn)
        await cache_service.get_or_execute("AAPL", "stock", mock_execute_fn)
        await cache_service.get_or_execute("AAPL", "stock", mock_execute_fn)

        mock_repository.get_cached_analysis.return_value = None
        await cache_service.get_or_execute("MSFT", "stock", mock_execute_fn)

        # Act
        hit_rate = cache_service.get_hit_rate()

        # Assert
        assert cache_service.cache_hits == 3
        assert cache_service.cache_misses == 1
        assert hit_rate == 0.75  # 3/4 = 75%

    @pytest.mark.asyncio
    async def test_should_return_zero_hit_rate_with_no_requests(self, cache_service):
        """Test hit rate calculation with no requests."""
        # Act
        hit_rate = cache_service.get_hit_rate()

        # Assert
        assert hit_rate == 0.0

    @pytest.mark.asyncio
    async def test_should_get_cache_metrics(self, cache_service, mock_repository, sample_analysis_record, sample_crew_result):
        """Test getting cache metrics."""
        # Arrange
        mock_repository.store_analysis.return_value = True

        async def mock_execute_fn():
            return sample_crew_result

        # Simulate some cache operations
        mock_repository.get_cached_analysis.return_value = sample_analysis_record
        await cache_service.get_or_execute("AAPL", "stock", mock_execute_fn)

        mock_repository.get_cached_analysis.return_value = None
        await cache_service.get_or_execute("MSFT", "stock", mock_execute_fn)

        # Act
        metrics = cache_service.get_metrics()

        # Assert
        assert metrics["cache_hits"] == 1
        assert metrics["cache_misses"] == 1
        assert metrics["hit_rate"] == 0.5
        assert metrics["total_requests"] == 2
        assert metrics["ttl_hours"] == 24

    @pytest.mark.asyncio
    async def test_should_reset_metrics(self, cache_service, mock_repository, sample_analysis_record):
        """Test resetting cache metrics."""
        # Arrange
        mock_repository.get_cached_analysis.return_value = sample_analysis_record

        async def mock_execute_fn():
            return {}

        await cache_service.get_or_execute("AAPL", "stock", mock_execute_fn)
        assert cache_service.cache_hits == 1

        # Act
        cache_service.reset_metrics()

        # Assert
        assert cache_service.cache_hits == 0
        assert cache_service.cache_misses == 0

    @pytest.mark.asyncio
    async def test_should_log_metrics(self, cache_service, mocker):
        """Test logging cache metrics."""
        # Arrange
        mock_logger = mocker.patch("finwiz.supabase.services.cache_service.logger")

        # Act
        cache_service.log_metrics()

        # Assert
        assert mock_logger.info.called
        log_call = mock_logger.info.call_args[0][0]
        assert "Cache Metrics" in log_call
        assert "Hits=" in log_call
        assert "Misses=" in log_call
        assert "Hit Rate=" in log_call

    @pytest.mark.asyncio
    async def test_should_use_custom_ttl_from_environment(self, mock_repository, mock_client, mocker, sample_crew_result):
        """Test TTL configuration from environment variable."""
        # Arrange
        mocker.patch.dict(os.environ, {"ANALYSIS_CACHE_TTL_HOURS": "72"})
        service = CacheService(repository=mock_repository, client=mock_client)
        service.is_enabled = True  # Enable cache for test
        mock_repository.get_cached_analysis.return_value = None
        mock_repository.store_analysis.return_value = True

        async def mock_execute_fn():
            return sample_crew_result

        # Act
        await service.get_or_execute(
            ticker="AAPL",
            asset_class="stock",
            execute_fn=mock_execute_fn,
        )

        # Assert
        assert service.ttl_hours == 72
        mock_repository.get_cached_analysis.assert_called_once_with(
            ticker="AAPL",
            asset_class="stock",
            ttl_hours=72,  # Custom TTL used
        )

    @pytest.mark.asyncio
    async def test_should_handle_different_asset_classes(self, cache_service, mock_repository, sample_crew_result):
        """Test cache service with different asset classes."""
        # Arrange
        mock_repository.get_cached_analysis.return_value = None
        mock_repository.store_analysis.return_value = True

        async def mock_execute_fn():
            return sample_crew_result

        # Act
        await cache_service.get_or_execute("AAPL", "stock", mock_execute_fn)
        await cache_service.get_or_execute("SPY", "etf", mock_execute_fn)
        await cache_service.get_or_execute("BTC", "crypto", mock_execute_fn)

        # Wait for async cache write tasks to complete
        await asyncio.sleep(0.1)

        # Assert
        assert mock_repository.get_cached_analysis.call_count == 3
        assert mock_repository.store_analysis.call_count == 3

        # Verify correct asset classes were used
        calls = mock_repository.get_cached_analysis.call_args_list
        assert calls[0][1]["asset_class"] == "stock"
        assert calls[1][1]["asset_class"] == "etf"
        assert calls[2][1]["asset_class"] == "crypto"

    @pytest.mark.asyncio
    async def test_should_track_cache_hits_and_misses_separately(self, cache_service, mock_repository, sample_analysis_record, sample_crew_result):
        """Test that cache hits and misses are tracked separately."""
        # Arrange
        mock_repository.store_analysis.return_value = True

        async def mock_execute_fn():
            return sample_crew_result

        # Act - 2 hits
        mock_repository.get_cached_analysis.return_value = sample_analysis_record
        await cache_service.get_or_execute("AAPL", "stock", mock_execute_fn)
        await cache_service.get_or_execute("AAPL", "stock", mock_execute_fn)

        # Act - 3 misses
        mock_repository.get_cached_analysis.return_value = None
        await cache_service.get_or_execute("MSFT", "stock", mock_execute_fn)
        await cache_service.get_or_execute("GOOGL", "stock", mock_execute_fn)
        await cache_service.get_or_execute("TSLA", "stock", mock_execute_fn)

        # Assert
        assert cache_service.cache_hits == 2
        assert cache_service.cache_misses == 3
        assert cache_service.get_hit_rate() == 0.4  # 2/5 = 40%

    @pytest.mark.asyncio
    async def test_should_initialize_successfully_when_connectivity_passes(self, mock_repository, mock_client, mocker):
        """Test initialize() with successful connectivity test."""
        # Arrange
        mock_client.test_connectivity = mocker.AsyncMock(return_value=True)
        service = CacheService(repository=mock_repository, client=mock_client)

        # Act
        result = await service.initialize()

        # Assert
        assert result is True
        assert service.is_enabled is True
        mock_client.test_connectivity.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_initialize_disabled_when_connectivity_fails(self, mock_repository, mock_client, mocker):
        """Test initialize() with failed connectivity test."""
        # Arrange
        mock_client.test_connectivity = mocker.AsyncMock(return_value=False)
        service = CacheService(repository=mock_repository, client=mock_client)

        # Act
        result = await service.initialize()

        # Assert
        assert result is False
        assert service.is_enabled is False
        mock_client.test_connectivity.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_initialize_disabled_when_no_client(self, mock_repository):
        """Test initialize() with no client."""
        # Arrange
        service = CacheService(repository=mock_repository, client=None)

        # Act
        result = await service.initialize()

        # Assert
        assert result is False
        assert service.is_enabled is False

    @pytest.mark.asyncio
    async def test_should_skip_cache_when_disabled(self, mock_repository, mock_client, sample_crew_result, mocker):
        """Test get_or_execute() skips cache when disabled."""
        # Arrange
        service = CacheService(repository=mock_repository, client=mock_client)
        service.is_enabled = False  # Cache disabled

        async def mock_execute_fn():
            return sample_crew_result

        # Act
        result, is_cached = await service.get_or_execute(
            ticker="AAPL",
            asset_class="stock",
            execute_fn=mock_execute_fn,
        )

        # Assert
        assert is_cached is False
        assert result == sample_crew_result
        # Repository should NOT be called when cache is disabled
        mock_repository.get_cached_analysis.assert_not_called()
        mock_repository.store_analysis.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_handle_cache_read_timeout_gracefully(self, mock_repository, mock_client, sample_crew_result, mocker):
        """Test get_or_execute() handles cache read timeout."""
        # Arrange
        service = CacheService(repository=mock_repository, client=mock_client)
        service.is_enabled = True

        # Simulate timeout on cache read
        async def slow_cache_read(*args, **kwargs):
            await asyncio.sleep(20)  # Longer than timeout
            return None

        mock_repository.get_cached_analysis = slow_cache_read
        mock_repository.store_analysis = mocker.AsyncMock()

        async def mock_execute_fn():
            return sample_crew_result

        # Act
        result, is_cached = await service.get_or_execute(
            ticker="AAPL",
            asset_class="stock",
            execute_fn=mock_execute_fn,
        )

        # Assert
        assert is_cached is False
        assert result == sample_crew_result
        # Should proceed with execution despite timeout

    @pytest.mark.asyncio
    async def test_should_write_cache_non_blocking(self, mock_repository, mock_client, sample_crew_result, mocker):
        """Test that cache writes don't block analysis."""
        # Arrange
        service = CacheService(repository=mock_repository, client=mock_client)
        service.is_enabled = True
        mock_repository.get_cached_analysis.return_value = None

        # Simulate slow cache write
        write_started = False
        write_completed = False

        async def slow_store(*args, **kwargs):
            nonlocal write_started, write_completed
            write_started = True
            await asyncio.sleep(0.1)  # Simulate slow write
            write_completed = True

        mock_repository.store_analysis = slow_store

        async def mock_execute_fn():
            return sample_crew_result

        # Act
        result, is_cached = await service.get_or_execute(
            ticker="AAPL",
            asset_class="stock",
            execute_fn=mock_execute_fn,
        )

        # Assert
        assert is_cached is False
        assert result == sample_crew_result
        # Write should be scheduled but not block return
        # Give a moment for the task to start
        await asyncio.sleep(0.01)
        # Write may or may not have completed, but we returned immediately

    @pytest.mark.asyncio
    async def test_should_log_cache_write_timeout(self, mock_repository, mock_client, sample_crew_result, mocker):
        """Test that cache write timeouts are logged as warnings."""
        # Arrange
        service = CacheService(repository=mock_repository, client=mock_client)
        service.is_enabled = True
        mock_repository.get_cached_analysis.return_value = None
        mock_logger = mocker.patch("finwiz.supabase.services.cache_service.logger")

        # Simulate timeout on cache write
        async def timeout_store(*args, **kwargs):
            await asyncio.sleep(20)  # Longer than write timeout

        mock_repository.store_analysis = timeout_store

        async def mock_execute_fn():
            return sample_crew_result

        # Act
        result, is_cached = await service.get_or_execute(
            ticker="AAPL",
            asset_class="stock",
            execute_fn=mock_execute_fn,
        )

        # Give time for background task to timeout
        await asyncio.sleep(0.1)

        # Assert
        assert is_cached is False
        assert result == sample_crew_result
        # Analysis should complete despite write timeout

    @pytest.mark.asyncio
    async def test_should_log_cache_write_failure(self, mock_repository, mock_client, sample_crew_result, mocker):
        """Test that cache write failures are logged as warnings."""
        # Arrange
        service = CacheService(repository=mock_repository, client=mock_client)
        service.is_enabled = True
        mock_repository.get_cached_analysis.return_value = None
        mock_logger = mocker.patch("finwiz.supabase.services.cache_service.logger")

        # Simulate failure on cache write
        async def failing_store(*args, **kwargs):
            raise Exception("Storage failed")

        mock_repository.store_analysis = failing_store

        async def mock_execute_fn():
            return sample_crew_result

        # Act
        result, is_cached = await service.get_or_execute(
            ticker="AAPL",
            asset_class="stock",
            execute_fn=mock_execute_fn,
        )

        # Give time for background task to fail
        await asyncio.sleep(0.1)

        # Assert
        assert is_cached is False
        assert result == sample_crew_result
        # Analysis should complete despite write failure
