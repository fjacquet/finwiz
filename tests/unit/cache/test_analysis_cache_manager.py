"""Unit tests for AnalysisCacheManager core get/cache/path behavior.

Stats / cleanup tests live in `test_analysis_cache_stats.py`; model tests
live in `test_cache_models.py`.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from finwiz.cache.analysis_cache_manager import AnalysisCacheManager, CrewAnalysisResult


class TestAnalysisCacheManager:
    """Test suite for AnalysisCacheManager."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        return tmp_path / "test_cache"

    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        return AnalysisCacheManager(cache_dir=str(temp_cache_dir), ttl_hours=24)

    @pytest.fixture
    def sample_analysis(self):
        return CrewAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="StockCrew",
            analyzed_at=datetime.now(),
            composite_score=0.85,
            grade="A",
        )

    def test_should_initialize_cache_manager(self, temp_cache_dir):
        """Test cache manager initialization."""
        manager = AnalysisCacheManager(cache_dir=str(temp_cache_dir), ttl_hours=12)

        assert manager.cache_dir == temp_cache_dir
        assert manager.ttl_hours == 12
        assert temp_cache_dir.exists()
        assert manager.stats["cache_hits"] == 0
        assert manager.stats["cache_misses"] == 0

    def test_should_create_cache_directory_structure(self, temp_cache_dir):
        """Test that cache directory is created on initialization."""
        AnalysisCacheManager(cache_dir=str(temp_cache_dir))
        assert temp_cache_dir.exists()
        assert temp_cache_dir.is_dir()

    def test_should_cache_analysis_result(self, cache_manager, sample_analysis):
        """Test caching analysis result."""
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)

        cache_path = cache_manager._get_cache_path("AAPL", "stock")
        assert cache_path.exists()

        with open(cache_path, encoding="utf-8") as f:
            cache_data = json.load(f)
        assert cache_data["ticker"] == "AAPL"
        assert cache_data["asset_class"] == "stock"
        assert cache_data["analysis"]["composite_score"] == 0.85

    def test_should_retrieve_fresh_cached_analysis(self, cache_manager, sample_analysis):
        """Test retrieving fresh cached analysis."""
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)
        cached = cache_manager.get_cached_analysis("AAPL", "stock")

        assert cached is not None
        assert cached.ticker == "AAPL"
        assert cached.asset_class == "stock"
        assert cached.analysis.composite_score == 0.85
        assert cache_manager.stats["cache_hits"] == 1
        assert cache_manager.stats["cache_misses"] == 0

    def test_should_return_none_for_missing_cache(self, cache_manager):
        """Test that missing cache returns None."""
        cached = cache_manager.get_cached_analysis("UNKNOWN", "stock")

        assert cached is None
        assert cache_manager.stats["cache_misses"] == 1

    def test_should_return_none_for_stale_cache(self, cache_manager, sample_analysis):
        """Test that stale cache returns None and cleans up."""
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)

        cache_path = cache_manager._get_cache_path("AAPL", "stock")
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
        data["cached_at"] = (datetime.now() - timedelta(hours=25)).isoformat()
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        cached = cache_manager.get_cached_analysis("AAPL", "stock")

        assert cached is None
        assert not cache_path.exists()
        assert cache_manager.stats["cache_misses"] == 1

    def test_should_handle_different_asset_classes(self, cache_manager, sample_analysis):
        """Test caching different asset classes separately."""
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)

        etf_analysis = CrewAnalysisResult(
            ticker="SPY",
            asset_class="etf",
            crew_name="EtfCrew",
            analyzed_at=datetime.now(),
            composite_score=0.80,
            grade="B+",
        )
        cache_manager.cache_analysis("SPY", "etf", etf_analysis)

        crypto_analysis = CrewAnalysisResult(
            ticker="BTC",
            asset_class="crypto",
            crew_name="CryptoCrew",
            analyzed_at=datetime.now(),
            composite_score=0.75,
            grade="B",
        )
        cache_manager.cache_analysis("BTC", "crypto", crypto_analysis)

        assert (Path(str(cache_manager.cache_dir)) / "stock").exists()
        assert (Path(str(cache_manager.cache_dir)) / "etf").exists()
        assert (Path(str(cache_manager.cache_dir)) / "crypto").exists()

        stock_cached = cache_manager.get_cached_analysis("AAPL", "stock")
        etf_cached = cache_manager.get_cached_analysis("SPY", "etf")
        crypto_cached = cache_manager.get_cached_analysis("BTC", "crypto")

        assert stock_cached is not None
        assert etf_cached is not None
        assert crypto_cached is not None
        assert stock_cached.analysis.grade == "A"
        assert etf_cached.analysis.grade == "B+"
        assert crypto_cached.analysis.grade == "B"

    def test_should_normalize_ticker_case(self, cache_manager, sample_analysis):
        """Test that ticker case is normalized."""
        cache_manager.cache_analysis("aapl", "stock", sample_analysis)
        cached_upper = cache_manager.get_cached_analysis("AAPL", "stock")
        cached_lower = cache_manager.get_cached_analysis("aapl", "stock")

        assert cached_upper is not None
        assert cached_lower is not None
        assert cached_upper.ticker == "AAPL"
        assert cached_lower.ticker == "AAPL"

    def test_should_check_freshness_with_custom_ttl(self, cache_manager):
        """Test freshness check with custom TTL."""
        recent_time = datetime.now() - timedelta(hours=1)
        old_time = datetime.now() - timedelta(hours=48)

        assert cache_manager.is_fresh(recent_time) is True
        assert cache_manager.is_fresh(old_time) is False

    def test_should_use_date_in_cache_filename(self, cache_manager, sample_analysis):
        """Test that cache filename includes current date."""
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)

        cache_path = cache_manager._get_cache_path("AAPL", "stock")
        date_str = datetime.now().strftime("%Y-%m-%d")
        assert date_str in cache_path.name
        assert cache_path.name.startswith("AAPL_")
        assert cache_path.name.endswith(".json")
