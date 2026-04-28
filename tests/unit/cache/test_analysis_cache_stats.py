"""Unit tests for AnalysisCacheManager stats and cleanup behavior."""

import json
from datetime import datetime, timedelta

import pytest

from finwiz.cache.analysis_cache_manager import AnalysisCacheManager, CrewAnalysisResult


@pytest.fixture
def temp_cache_dir(tmp_path):
    return tmp_path / "test_cache"


@pytest.fixture
def cache_manager(temp_cache_dir):
    return AnalysisCacheManager(cache_dir=str(temp_cache_dir), ttl_hours=24)


@pytest.fixture
def sample_analysis():
    return CrewAnalysisResult(
        ticker="AAPL",
        asset_class="stock",
        crew_name="StockCrew",
        analyzed_at=datetime.now(),
        composite_score=0.85,
        grade="A",
    )


class TestStaleCleanup:
    def test_should_clear_stale_cache_entries(self, cache_manager, sample_analysis):
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)
        cache_manager.cache_analysis("MSFT", "stock", sample_analysis)

        cache_path = cache_manager._get_cache_path("AAPL", "stock")
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
        data["cached_at"] = (datetime.now() - timedelta(hours=25)).isoformat()
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        removed_count = cache_manager.clear_stale_cache()

        assert removed_count == 1
        assert not cache_path.exists()
        msft_path = cache_manager._get_cache_path("MSFT", "stock")
        assert msft_path.exists()

    def test_should_clear_all_stale_entries_across_asset_classes(self, cache_manager):
        for ticker, asset_class in [("AAPL", "stock"), ("SPY", "etf"), ("BTC", "crypto")]:
            analysis = CrewAnalysisResult(ticker=ticker, asset_class=asset_class, crew_name="TestCrew", analyzed_at=datetime.now(), composite_score=0.85, grade="A")
            cache_manager.cache_analysis(ticker, asset_class, analysis)

            cache_path = cache_manager._get_cache_path(ticker, asset_class)
            with open(cache_path, encoding="utf-8") as f:
                data = json.load(f)
            data["cached_at"] = (datetime.now() - timedelta(hours=25)).isoformat()
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

        removed_count = cache_manager.clear_stale_cache()
        assert removed_count == 3

    def test_should_handle_corrupted_cache_files(self, cache_manager, sample_analysis):
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)
        cache_path = cache_manager._get_cache_path("AAPL", "stock")
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write("invalid json content")

        removed_count = cache_manager.clear_stale_cache()

        assert removed_count == 1
        assert not cache_path.exists()

    def test_should_return_zero_when_no_stale_entries(self, cache_manager, sample_analysis):
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)
        removed_count = cache_manager.clear_stale_cache()
        assert removed_count == 0

    def test_should_track_cache_cleanup_statistics(self, cache_manager, sample_analysis):
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)

        cache_path = cache_manager._get_cache_path("AAPL", "stock")
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
        data["cached_at"] = (datetime.now() - timedelta(hours=25)).isoformat()
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        cache_manager.clear_stale_cache()
        assert cache_manager.stats["cache_cleanups"] == 1


class TestStats:
    def test_should_get_cache_statistics(self, cache_manager, sample_analysis):
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)
        cache_manager.get_cached_analysis("AAPL", "stock")  # hit
        cache_manager.get_cached_analysis("MSFT", "stock")  # miss

        stats = cache_manager.get_cache_stats()

        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["cache_stores"] == 1
        assert stats["total_requests"] == 2
        assert stats["hit_rate_percent"] == 50.0
        assert stats["cache_file_count"] == 1
        assert stats["ttl_hours"] == 24
        assert "cache_size_mb" in stats

    def test_should_calculate_hit_rate_correctly(self, cache_manager, sample_analysis):
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)

        cache_manager.get_cached_analysis("AAPL", "stock")
        cache_manager.get_cached_analysis("AAPL", "stock")
        cache_manager.get_cached_analysis("AAPL", "stock")
        cache_manager.get_cached_analysis("MSFT", "stock")

        stats = cache_manager.get_cache_stats()

        assert stats["cache_hits"] == 3
        assert stats["cache_misses"] == 1
        assert stats["total_requests"] == 4
        assert stats["hit_rate_percent"] == 75.0

    def test_should_handle_zero_requests_in_stats(self, cache_manager):
        stats = cache_manager.get_cache_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["total_requests"] == 0
        assert stats["hit_rate_percent"] == 0

    def test_should_log_cache_statistics(self, cache_manager, sample_analysis, mocker):
        mock_logger = mocker.patch("finwiz.cache._helpers.logger")
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)
        cache_manager.get_cached_analysis("AAPL", "stock")

        cache_manager.log_cache_stats()

        assert mock_logger.info.called
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Cache Statistics" in call for call in log_calls)
        assert any("Hit Rate" in call for call in log_calls)


class TestErrorHandling:
    def test_should_handle_cache_errors_gracefully(self, cache_manager, mocker):
        mock_logger = mocker.patch("finwiz.cache.analysis_cache_manager.logger")
        mocker.patch("builtins.open", side_effect=PermissionError("Access denied"))

        analysis = CrewAnalysisResult(ticker="AAPL", asset_class="stock", crew_name="StockCrew", analyzed_at=datetime.now(), composite_score=0.85, grade="A")
        cache_manager.cache_analysis("AAPL", "stock", analysis)

        assert mock_logger.error.called
        error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
        assert any("Error caching analysis" in call for call in error_calls)
