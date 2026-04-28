"""Unit tests for cache model classes (CrewAnalysisResult, CachedAnalysis)."""

from datetime import datetime, timedelta

from finwiz.cache.analysis_cache_manager import CachedAnalysis, CrewAnalysisResult


class TestCrewAnalysisResult:
    """Test suite for CrewAnalysisResult model."""

    def test_should_create_crew_analysis_result_with_required_fields(self):
        """Test creating CrewAnalysisResult with required fields."""
        result = CrewAnalysisResult(ticker="AAPL", asset_class="stock", crew_name="StockCrew", analyzed_at=datetime.now(), composite_score=0.85, grade="A")

        assert result.ticker == "AAPL"
        assert result.asset_class == "stock"
        assert result.crew_name == "StockCrew"
        assert result.composite_score == 0.85
        assert result.grade == "A"
        assert result.fundamental_score is None
        assert result.technical_score is None

    def test_should_create_crew_analysis_result_with_all_fields(self):
        """Test creating CrewAnalysisResult with all fields."""
        result = CrewAnalysisResult(
            ticker="MSFT",
            asset_class="stock",
            crew_name="StockCrew",
            analyzed_at=datetime.now(),
            fundamental_score=0.90,
            technical_score=0.80,
            quality_score=0.85,
            risk_score=2.5,
            composite_score=0.85,
            grade="A+",
            metrics={"pe_ratio": 25.5, "revenue_growth": 0.15},
            raw_output={"recommendation": "BUY"},
        )

        assert result.fundamental_score == 0.90
        assert result.technical_score == 0.80
        assert result.quality_score == 0.85
        assert result.risk_score == 2.5
        assert result.metrics["pe_ratio"] == 25.5
        assert result.raw_output["recommendation"] == "BUY"


class TestCachedAnalysis:
    """Test suite for CachedAnalysis model."""

    def test_should_check_freshness_within_ttl(self):
        """Test that cached data within TTL is considered fresh."""
        analysis = CrewAnalysisResult(ticker="AAPL", asset_class="stock", crew_name="StockCrew", analyzed_at=datetime.now(), composite_score=0.85, grade="A")
        cached = CachedAnalysis(ticker="AAPL", asset_class="stock", cached_at=datetime.now() - timedelta(hours=12), analysis=analysis)

        assert cached.is_fresh(ttl_hours=24) is True
        assert cached.is_fresh(ttl_hours=13) is True

    def test_should_check_freshness_outside_ttl(self):
        """Test that cached data outside TTL is considered stale."""
        analysis = CrewAnalysisResult(ticker="AAPL", asset_class="stock", crew_name="StockCrew", analyzed_at=datetime.now(), composite_score=0.85, grade="A")
        cached = CachedAnalysis(ticker="AAPL", asset_class="stock", cached_at=datetime.now() - timedelta(hours=25), analysis=analysis)

        assert cached.is_fresh(ttl_hours=24) is False
        assert cached.is_fresh(ttl_hours=20) is False

    def test_should_calculate_age_in_hours(self):
        """Test age_hours property calculation."""
        analysis = CrewAnalysisResult(ticker="AAPL", asset_class="stock", crew_name="StockCrew", analyzed_at=datetime.now(), composite_score=0.85, grade="A")
        cached = CachedAnalysis(ticker="AAPL", asset_class="stock", cached_at=datetime.now() - timedelta(hours=6, minutes=30), analysis=analysis)

        age = cached.age_hours

        assert 6.4 < age < 6.6  # Should be approximately 6.5 hours
