"""Unit tests for AnalysisCacheManager core get/cache/path behavior.

Stats / cleanup tests live in `test_analysis_cache_stats.py`; model tests
live in `test_cache_models.py`.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from finwiz.cache import analysis_cache_manager as acm_module
from finwiz.cache.analysis_cache_manager import (
    AnalysisCacheManager,
    CrewAnalysisResult,
    get_analysis_cache_manager,
)


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

    # --- regression tests for PR #27 review findings -------------------

    def test_get_cache_path_rejects_path_traversal_ticker(self, cache_manager):
        """#4: ticker with path-traversal sequences raises ValueError."""
        for evil in ["../../etc/passwd", "..", "a/b", "a\\b"]:
            with pytest.raises(ValueError, match="invalid ticker"):
                cache_manager._get_cache_path(evil, "stock")

    def test_get_cache_path_rejects_path_traversal_asset_class(self, cache_manager):
        """#4: asset_class with path-traversal sequences raises ValueError."""
        for evil in ["../etc", "..", "a/b", "STOCK!", "with space"]:
            with pytest.raises(ValueError, match="invalid asset_class"):
                cache_manager._get_cache_path("AAPL", evil)

    def test_quality_score_round_trips_through_cache(self, cache_manager):
        """#2: quality_score must survive a dict-input round-trip."""
        analysis_dict = {
            "crew_name": "deep_analysis",
            "fundamental_score": 0.9,
            "technical_score": 0.8,
            "quality_score": 0.77,
            "risk_score": 0.7,
            "composite_score": 0.85,
            "grade": "A",
        }
        cache_manager.cache_analysis("AAPL", "stock", analysis_dict)
        cached = cache_manager.get_cached_analysis("AAPL", "stock")
        assert cached is not None
        assert cached.analysis.quality_score == 0.77

    def test_clear_stale_keeps_files_on_transient_io_error(self, cache_manager, sample_analysis, mocker):
        """#3: PermissionError during read leaves the file intact."""
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)
        cache_path = cache_manager._get_cache_path("AAPL", "stock")
        assert cache_path.exists()

        # Stub `open` only inside _helpers.clear_stale_cache to raise
        # PermissionError on the first read attempt.
        real_open = open

        def fake_open(path, *args, **kwargs):
            if str(path) == str(cache_path):
                raise PermissionError("simulated transient I/O")
            return real_open(path, *args, **kwargs)

        mocker.patch("finwiz.cache._helpers.open", side_effect=fake_open)

        removed = cache_manager.clear_stale_cache()

        assert removed == 0  # no removal because read failed transiently
        assert cache_path.exists()  # file is untouched

    def test_clear_stale_removes_file_on_corrupted_json(self, cache_manager, sample_analysis):
        """#3: confirmed JSONDecodeError is still treated as corruption."""
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)
        cache_path = cache_manager._get_cache_path("AAPL", "stock")
        cache_path.write_text("not valid json {{{", encoding="utf-8")

        removed = cache_manager.clear_stale_cache()

        assert removed == 1
        assert not cache_path.exists()

    def test_atomic_write_no_temp_files_left_behind(self, cache_manager, sample_analysis):
        """#5: successful write leaves no .tmp sidecar files."""
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)
        asset_dir = cache_manager.cache_dir / "stock"
        tmp_files = list(asset_dir.glob("*.tmp"))
        assert tmp_files == []

    def test_atomic_write_cleans_up_on_failure(self, cache_manager, sample_analysis, mocker):
        """#5: a failed os.replace removes the temp file (no orphaned .tmp)."""
        # Make os.replace blow up so the rename never lands.
        mocker.patch("finwiz.cache.analysis_cache_manager.os.replace", side_effect=OSError("simulated rename failure"))

        # cache_analysis swallows exceptions and logs; the orphan-cleanup
        # path is what we want to exercise.
        cache_manager.cache_analysis("AAPL", "stock", sample_analysis)

        asset_dir = cache_manager.cache_dir / "stock"
        tmp_files = list(asset_dir.glob("*.tmp"))
        assert tmp_files == [], f"orphaned tmp files: {tmp_files}"

    def test_init_disables_cache_when_dir_not_writable(self, tmp_path, mocker):
        """#1: a non-writable cache_dir flips cache_enabled=False instead of crashing."""
        cache_dir = tmp_path / "blocked"
        # Patch verify_cache_directory to simulate the unwritable case.
        mocker.patch(
            "finwiz.cache.analysis_cache_manager.verify_cache_directory",
            side_effect=lambda mgr: setattr(mgr, "cache_enabled", False) or False,
        )
        manager = AnalysisCacheManager(cache_dir=str(cache_dir))
        assert manager.cache_enabled is False

    def test_get_analysis_cache_manager_preserves_ttl_zero(self, mocker):
        """#6: explicit ttl_hours=0 is preserved; only None falls back to 24."""
        mocker.patch.object(acm_module, "_cache_manager", None)
        manager = get_analysis_cache_manager(ttl_hours=0)
        assert manager.ttl_hours == 0  # NOT 24

    def test_get_analysis_cache_manager_default_when_none(self, mocker):
        """#6: ttl_hours=None still defaults to 24."""
        mocker.patch.object(acm_module, "_cache_manager", None)
        manager = get_analysis_cache_manager()
        assert manager.ttl_hours == 24
