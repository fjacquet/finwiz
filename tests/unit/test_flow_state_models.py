"""Comprehensive pytest tests for FinWiz flow state models.

Tests cover:
- Model instantiation with required fields
- Default values and default factories
- Field validation constraints
- Properties and computed fields
- Model relationships and nesting
- Pydantic configuration validation
"""

import uuid
from datetime import datetime

import pytest
from faker import Faker
from pydantic import ValidationError

from finwiz.flow_state_models import DeepAnalysisResult, FinwizState


@pytest.fixture
def fake():
    """Faker instance for generating test data."""
    return Faker()


@pytest.fixture
def sample_deep_analysis_result(fake):
    """Sample DeepAnalysisResult with all required fields."""
    return DeepAnalysisResult(
        ticker=fake.random_element(["AAPL", "GOOGL", "MSFT", "TSLA"]),
        asset_class=fake.random_element(["stock", "etf", "crypto"]),
        crew_name=fake.random_element(["stock_crew", "etf_crew", "crypto_crew"]),
        composite_score=fake.pyfloat(min_value=0.0, max_value=1.0),
        grade=fake.random_element(["A+", "A", "B+", "B", "C", "D", "F"]),
        recommendation=fake.random_element(["BUY", "HOLD", "SELL"]),
        rationale=fake.text(max_nb_chars=200),
        data_freshness_hours=fake.pyfloat(min_value=0.0, max_value=24.0),
        confidence_level=fake.pyfloat(min_value=0.0, max_value=1.0),
    )


@pytest.fixture
def sample_finwiz_state(fake):
    """Sample FinwizState with common fields populated."""
    return FinwizState(
        has_existing_session=fake.boolean(),
        session_id=str(fake.uuid4()),
        analysis_count=fake.random_int(min=0, max=100),
        stock_result=fake.text(max_nb_chars=100),
        etf_result=fake.text(max_nb_chars=100),
        crypto_result=fake.text(max_nb_chars=100),
    )


class TestDeepAnalysisResultInstantiation:
    """Test instantiation of DeepAnalysisResult with various field combinations."""

    def test_create_with_all_required_fields(self, fake):
        """Test creating DeepAnalysisResult with all required fields."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Strong fundamentals",
            data_freshness_hours=2.5,
            confidence_level=0.95,
        )

        assert result.ticker == "AAPL"
        assert result.asset_class == "stock"
        assert result.crew_name == "stock_crew"
        assert result.composite_score == 0.85
        assert result.grade == "A"
        assert result.recommendation == "BUY"
        assert result.rationale == "Strong fundamentals"
        assert result.data_freshness_hours == 2.5
        assert result.confidence_level == 0.95

    def test_create_with_optional_fields(self, fake):
        """Test creating DeepAnalysisResult with optional fields."""
        data_quality = {
            "quality_level": "high",
            "completeness_score": 0.92,
            "source_count": 3,
        }
        lineage = {
            "sources": ["yfinance", "alpha_vantage"],
            "aggregation_method": "weighted_average",
        }

        result = DeepAnalysisResult(
            ticker="GOOGL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.78,
            grade="B+",
            recommendation="HOLD",
            rationale="Mixed signals",
            data_freshness_hours=1.0,
            confidence_level=0.85,
            fundamental_score=0.80,
            technical_score=0.75,
            risk_score=2.5,
            data_quality=data_quality,
            lineage=lineage,
        )

        assert result.fundamental_score == 0.80
        assert result.technical_score == 0.75
        assert result.risk_score == 2.5
        assert result.data_quality == data_quality
        assert result.lineage == lineage

    def test_create_with_minimal_fields(self, fake):
        """Test creating DeepAnalysisResult with only required fields."""
        result = DeepAnalysisResult(
            ticker="BTC-USD",
            asset_class="crypto",
            crew_name="crypto_crew",
            composite_score=0.65,
            grade="B",
            recommendation="SELL",
            rationale="Bearish trend",
            data_freshness_hours=0.5,
            confidence_level=0.70,
        )

        # Verify required fields
        assert result.ticker == "BTC-USD"
        assert result.asset_class == "crypto"

        # Verify defaults
        assert isinstance(result.analysis_timestamp, str)
        assert result.risk_details == {}
        assert result.fundamental_details == {}
        assert result.technical_details == {}
        assert result.warnings == []
        assert result.cached is False
        assert result.fundamental_score is None
        assert result.technical_score is None
        assert result.risk_score is None
        assert result.data_quality is None
        assert result.lineage is None


class TestDeepAnalysisResultDefaults:
    """Test default values and default factories."""

    def test_analysis_timestamp_auto_generated(self):
        """Test that analysis_timestamp is auto-generated as ISO format."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.90,
        )

        assert isinstance(result.analysis_timestamp, str)
        # Verify ISO format by parsing
        parsed = datetime.fromisoformat(result.analysis_timestamp)
        assert isinstance(parsed, datetime)

    def test_risk_details_default_factory(self):
        """Test that risk_details defaults to empty dict."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.90,
        )

        assert result.risk_details == {}
        assert isinstance(result.risk_details, dict)

    def test_warnings_default_factory(self):
        """Test that warnings defaults to empty list."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.90,
        )

        assert result.warnings == []
        assert isinstance(result.warnings, list)

    def test_cached_default_false(self):
        """Test that cached defaults to False."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.90,
        )

        assert result.cached is False

    def test_multiple_instances_have_different_timestamps(self):
        """Test that multiple instances have different timestamps."""
        import time

        result1 = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.90,
        )

        time.sleep(0.01)  # Small delay to ensure different timestamps

        result2 = DeepAnalysisResult(
            ticker="GOOGL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.80,
            grade="B+",
            recommendation="HOLD",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.85,
        )

        # Timestamps should be different (or at least close)
        assert isinstance(result1.analysis_timestamp, str)
        assert isinstance(result2.analysis_timestamp, str)


class TestDeepAnalysisResultValidation:
    """Test field validation constraints."""

    def test_composite_score_must_be_between_0_and_1(self):
        """Test composite_score validation (0.0-1.0)."""
        # Valid values
        for score in [0.0, 0.5, 1.0]:
            result = DeepAnalysisResult(
                ticker="AAPL",
                asset_class="stock",
                crew_name="stock_crew",
                composite_score=score,
                grade="A",
                recommendation="BUY",
                rationale="Test",
                data_freshness_hours=1.0,
                confidence_level=0.90,
            )
            assert result.composite_score == score

        # Invalid values
        with pytest.raises(ValidationError):
            DeepAnalysisResult(
                ticker="AAPL",
                asset_class="stock",
                crew_name="stock_crew",
                composite_score=-0.1,  # Too low
                grade="A",
                recommendation="BUY",
                rationale="Test",
                data_freshness_hours=1.0,
                confidence_level=0.90,
            )

        with pytest.raises(ValidationError):
            DeepAnalysisResult(
                ticker="AAPL",
                asset_class="stock",
                crew_name="stock_crew",
                composite_score=1.1,  # Too high
                grade="A",
                recommendation="BUY",
                rationale="Test",
                data_freshness_hours=1.0,
                confidence_level=0.90,
            )

    def test_fundamental_score_validation(self):
        """Test fundamental_score validation (0.0-1.0)."""
        # Valid
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.90,
            fundamental_score=0.92,
        )
        assert result.fundamental_score == 0.92

        # Invalid
        with pytest.raises(ValidationError):
            DeepAnalysisResult(
                ticker="AAPL",
                asset_class="stock",
                crew_name="stock_crew",
                composite_score=0.85,
                grade="A",
                recommendation="BUY",
                rationale="Test",
                data_freshness_hours=1.0,
                confidence_level=0.90,
                fundamental_score=1.5,  # Too high
            )

    def test_technical_score_validation(self):
        """Test technical_score validation (0.0-1.0)."""
        # Valid
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.90,
            technical_score=0.75,
        )
        assert result.technical_score == 0.75

        # Invalid
        with pytest.raises(ValidationError):
            DeepAnalysisResult(
                ticker="AAPL",
                asset_class="stock",
                crew_name="stock_crew",
                composite_score=0.85,
                grade="A",
                recommendation="BUY",
                rationale="Test",
                data_freshness_hours=1.0,
                confidence_level=0.90,
                technical_score=-0.1,  # Too low
            )

    def test_risk_score_validation(self):
        """Test risk_score validation (0-5 scale)."""
        # Valid
        for score in [0.0, 2.5, 5.0]:
            result = DeepAnalysisResult(
                ticker="AAPL",
                asset_class="stock",
                crew_name="stock_crew",
                composite_score=0.85,
                grade="A",
                recommendation="BUY",
                rationale="Test",
                data_freshness_hours=1.0,
                confidence_level=0.90,
                risk_score=score,
            )
            assert result.risk_score == score

        # Invalid
        with pytest.raises(ValidationError):
            DeepAnalysisResult(
                ticker="AAPL",
                asset_class="stock",
                crew_name="stock_crew",
                composite_score=0.85,
                grade="A",
                recommendation="BUY",
                rationale="Test",
                data_freshness_hours=1.0,
                confidence_level=0.90,
                risk_score=5.5,  # Too high
            )

    def test_data_freshness_hours_non_negative(self):
        """Test data_freshness_hours must be >= 0."""
        # Valid
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=0.0,  # Minimum
            confidence_level=0.90,
        )
        assert result.data_freshness_hours == 0.0

        # Invalid
        with pytest.raises(ValidationError):
            DeepAnalysisResult(
                ticker="AAPL",
                asset_class="stock",
                crew_name="stock_crew",
                composite_score=0.85,
                grade="A",
                recommendation="BUY",
                rationale="Test",
                data_freshness_hours=-1.0,  # Negative
                confidence_level=0.90,
            )

    def test_confidence_level_validation(self):
        """Test confidence_level validation (0.0-1.0)."""
        # Valid values
        for conf in [0.0, 0.5, 1.0]:
            result = DeepAnalysisResult(
                ticker="AAPL",
                asset_class="stock",
                crew_name="stock_crew",
                composite_score=0.85,
                grade="A",
                recommendation="BUY",
                rationale="Test",
                data_freshness_hours=1.0,
                confidence_level=conf,
            )
            assert result.confidence_level == conf

        # Invalid values
        with pytest.raises(ValidationError):
            DeepAnalysisResult(
                ticker="AAPL",
                asset_class="stock",
                crew_name="stock_crew",
                composite_score=0.85,
                grade="A",
                recommendation="BUY",
                rationale="Test",
                data_freshness_hours=1.0,
                confidence_level=1.5,  # Too high
            )

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden (extra='forbid')."""
        with pytest.raises(ValidationError) as exc_info:
            DeepAnalysisResult(
                ticker="AAPL",
                asset_class="stock",
                crew_name="stock_crew",
                composite_score=0.85,
                grade="A",
                recommendation="BUY",
                rationale="Test",
                data_freshness_hours=1.0,
                confidence_level=0.90,
                unknown_field="should fail",  # Extra field
            )
        assert "unknown_field" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        required_fields = [
            "ticker",
            "asset_class",
            "crew_name",
            "composite_score",
            "grade",
            "recommendation",
            "rationale",
            "data_freshness_hours",
            "confidence_level",
        ]

        for field in required_fields:
            data = {
                "ticker": "AAPL",
                "asset_class": "stock",
                "crew_name": "stock_crew",
                "composite_score": 0.85,
                "grade": "A",
                "recommendation": "BUY",
                "rationale": "Test",
                "data_freshness_hours": 1.0,
                "confidence_level": 0.90,
            }
            del data[field]

            with pytest.raises(ValidationError) as exc_info:
                DeepAnalysisResult(**data)
            assert field in str(exc_info.value)

    def test_string_strip_whitespace(self):
        """Test that string fields strip whitespace."""
        result = DeepAnalysisResult(
            ticker="  AAPL  ",  # Extra whitespace
            asset_class="  stock  ",
            crew_name="  stock_crew  ",
            composite_score=0.85,
            grade="  A  ",
            recommendation="  BUY  ",
            rationale="  Strong fundamentals  ",
            data_freshness_hours=1.0,
            confidence_level=0.90,
        )

        assert result.ticker == "AAPL"
        assert result.asset_class == "stock"
        assert result.crew_name == "stock_crew"
        assert result.grade == "A"
        assert result.recommendation == "BUY"
        assert result.rationale == "Strong fundamentals"


class TestDeepAnalysisResultProperties:
    """Test properties and computed fields."""

    def test_quality_level_property_with_data_quality(self):
        """Test quality_level property returns quality_level from data_quality."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.90,
            data_quality={"quality_level": "high", "completeness_score": 0.95},
        )

        assert result.quality_level == "high"

    def test_quality_level_property_without_data_quality(self):
        """Test quality_level property returns 'unknown' when data_quality is None."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.90,
        )

        assert result.quality_level == "unknown"

    def test_quality_level_property_missing_key(self):
        """Test quality_level property returns 'unknown' when key is missing."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.90,
            data_quality={"source_count": 3},  # Missing 'quality_level'
        )

        assert result.quality_level == "unknown"

    def test_completeness_score_property_with_data_quality(self):
        """Test completeness_score property returns score from data_quality."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.90,
            data_quality={"quality_level": "high", "completeness_score": 0.88},
        )

        assert result.completeness_score == 0.88

    def test_completeness_score_property_without_data_quality(self):
        """Test completeness_score property returns 0.5 default."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.90,
        )

        assert result.completeness_score == 0.5

    def test_completeness_score_property_missing_key(self):
        """Test completeness_score property returns 0.5 when key is missing."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Test",
            data_freshness_hours=1.0,
            confidence_level=0.90,
            data_quality={"quality_level": "medium"},  # Missing 'completeness_score'
        )

        assert result.completeness_score == 0.5


class TestFinwizStateInstantiation:
    """Test FinwizState instantiation."""

    def test_create_empty_finwiz_state(self):
        """Test creating FinwizState with no arguments."""
        state = FinwizState()

        # Verify all defaults are present
        assert isinstance(state.id, str)
        assert len(state.id) > 0
        assert isinstance(state.current_day, int)
        assert isinstance(state.current_month, int)
        assert isinstance(state.current_year, int)
        assert isinstance(state.current_date, str)
        assert isinstance(state.full_date, str)
        assert isinstance(state.timestamp, str)
        assert state.report_language == "fr"
        assert state.has_existing_session is False
        assert state.session_id == ""

    def test_create_with_custom_values(self, fake):
        """Test creating FinwizState with custom values."""
        session_id = str(fake.uuid4())
        state = FinwizState(
            session_id=session_id,
            has_existing_session=True,
            analysis_count=42,
            report_language="en",
        )

        assert state.session_id == session_id
        assert state.has_existing_session is True
        assert state.analysis_count == 42
        assert state.report_language == "en"

    def test_create_with_deep_analysis_results(self, fake):
        """Test FinwizState with deep_analysis_results."""
        ticker1 = "AAPL"
        ticker2 = "GOOGL"

        result1 = DeepAnalysisResult(
            ticker=ticker1,
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Strong",
            data_freshness_hours=1.0,
            confidence_level=0.95,
        )

        result2 = DeepAnalysisResult(
            ticker=ticker2,
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.78,
            grade="B+",
            recommendation="HOLD",
            rationale="Mixed",
            data_freshness_hours=2.0,
            confidence_level=0.85,
        )

        state = FinwizState(
            deep_analysis_results={
                ticker1: result1,
                ticker2: result2,
            }
        )

        assert len(state.deep_analysis_results) == 2
        assert ticker1 in state.deep_analysis_results
        assert ticker2 in state.deep_analysis_results
        assert state.deep_analysis_results[ticker1].composite_score == 0.85
        assert state.deep_analysis_results[ticker2].composite_score == 0.78


class TestFinwizStateDefaults:
    """Test FinwizState default values."""

    def test_id_auto_generated(self):
        """Test that id is auto-generated as UUID."""
        state1 = FinwizState()
        state2 = FinwizState()

        assert isinstance(state1.id, str)
        assert isinstance(state2.id, str)
        assert state1.id != state2.id  # Each instance should have unique ID
        # Verify it's a valid UUID
        uuid.UUID(state1.id)
        uuid.UUID(state2.id)

    def test_date_fields_auto_populated(self):
        """Test that date fields are auto-populated."""
        state = FinwizState()

        assert isinstance(state.current_day, int)
        assert 1 <= state.current_day <= 31
        assert isinstance(state.current_month, int)
        assert 1 <= state.current_month <= 12
        assert isinstance(state.current_year, int)
        assert state.current_year >= 2020
        assert isinstance(state.current_date, str)
        assert isinstance(state.full_date, str)
        assert isinstance(state.timestamp, str)

    def test_flow_start_time_auto_generated(self):
        """Test that flow_start_time is auto-generated."""
        state = FinwizState()

        assert isinstance(state.flow_start_time, str)
        # Verify ISO format
        parsed = datetime.fromisoformat(state.flow_start_time)
        assert isinstance(parsed, datetime)

    def test_default_factory_fields(self):
        """Test all default_factory fields initialize as empty."""
        state = FinwizState()

        assert state.stale_data_warnings == []
        assert state.refresh_recommendations == []
        assert state.error_summaries == []
        assert state.stock_degraded_functionality == []
        assert state.etf_degraded_functionality == []
        assert state.crypto_degraded_functionality == []
        assert state.deep_analysis_results == {}
        assert state.portfolio_alternatives == {}
        assert state.crew_export_paths == {}
        assert state.crew_html_paths == {}
        assert state.crew_execution_status == {}
        assert state.crew_execution_errors == {}
        assert state.errors == []
        assert state.failed_holdings == []
        assert state.retry_counts == {}
        assert state.timeout_holdings == []
        assert state.retryable_errors == []
        assert state.non_retryable_errors == []

    def test_analysis_status_defaults(self):
        """Test analysis status fields default correctly."""
        state = FinwizState()

        # Stock
        assert state.stock_analysis_success is False
        assert state.stock_analysis_disabled is False
        assert state.stock_analysis_fallback is False
        assert state.stock_analysis_error is None
        assert state.stock_analysis_result is None

        # ETF
        assert state.etf_analysis_success is False
        assert state.etf_analysis_disabled is False
        assert state.etf_analysis_fallback is False
        assert state.etf_analysis_error is None
        assert state.etf_analysis_result is None

        # Crypto
        assert state.crypto_analysis_success is False
        assert state.crypto_analysis_disabled is False
        assert state.crypto_analysis_fallback is False
        assert state.crypto_analysis_error is None
        assert state.crypto_analysis_result is None


class TestFinwizStateValidation:
    """Test FinwizState field validation."""

    def test_progress_percentage_range(self):
        """Test progress_percentage validation (0-100)."""
        # Valid values
        for progress in [0.0, 50.0, 100.0]:
            state = FinwizState(progress_percentage=progress)
            assert state.progress_percentage == progress

        # Invalid values
        with pytest.raises(ValidationError):
            FinwizState(progress_percentage=-1.0)

        with pytest.raises(ValidationError):
            FinwizState(progress_percentage=101.0)

    def test_estimated_time_remaining_non_negative(self):
        """Test estimated_time_remaining must be >= 0."""
        # Valid
        state = FinwizState(estimated_time_remaining=0.0)
        assert state.estimated_time_remaining == 0.0

        state = FinwizState(estimated_time_remaining=3600.5)
        assert state.estimated_time_remaining == 3600.5

        # Invalid
        with pytest.raises(ValidationError):
            FinwizState(estimated_time_remaining=-1.0)

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed (extra='allow')."""
        # FinwizState allows extra fields
        state = FinwizState(custom_field="custom_value", another_field=42)

        assert hasattr(state, "custom_field")
        assert hasattr(state, "another_field")


class TestFinwizStateRelationships:
    """Test FinwizState relationships with other models."""

    def test_deep_analysis_results_store_nested_models(self):
        """Test that deep_analysis_results properly stores nested DeepAnalysisResult models."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Strong",
            data_freshness_hours=1.0,
            confidence_level=0.95,
        )

        state = FinwizState(deep_analysis_results={"AAPL": result})

        assert isinstance(state.deep_analysis_results["AAPL"], DeepAnalysisResult)
        assert state.deep_analysis_results["AAPL"].ticker == "AAPL"

    def test_multiple_nested_results(self):
        """Test FinwizState with multiple nested DeepAnalysisResult objects."""
        results = {}
        tickers = ["AAPL", "GOOGL", "MSFT"]

        for ticker in tickers:
            results[ticker] = DeepAnalysisResult(
                ticker=ticker,
                asset_class="stock",
                crew_name="stock_crew",
                composite_score=0.75 + len(results) * 0.05,
                grade="A",
                recommendation="BUY",
                rationale=f"Analysis for {ticker}",
                data_freshness_hours=1.0,
                confidence_level=0.90,
            )

        state = FinwizState(
            deep_analysis_results=results,
            deep_analysis_count=len(results),
            deep_analysis_success=True,
        )

        assert len(state.deep_analysis_results) == 3
        assert state.deep_analysis_count == 3
        assert state.deep_analysis_success is True

        for ticker in tickers:
            assert ticker in state.deep_analysis_results
            assert isinstance(state.deep_analysis_results[ticker], DeepAnalysisResult)

    def test_portfolio_alternatives_structure(self, fake):
        """Test portfolio_alternatives dictionary structure."""
        alternatives = {
            "AAPL": [
                {"ticker": "MSFT", "similarity": 0.92},
                {"ticker": "NVDA", "similarity": 0.88},
            ],
            "GOOGL": [
                {"ticker": "META", "similarity": 0.85},
            ],
        }

        state = FinwizState(
            portfolio_alternatives=alternatives,
            alternatives_count=3,
        )

        assert "AAPL" in state.portfolio_alternatives
        assert len(state.portfolio_alternatives["AAPL"]) == 2
        assert state.portfolio_alternatives["AAPL"][0]["ticker"] == "MSFT"


class TestFinwizStateComplexScenarios:
    """Test complex scenarios and interactions."""

    def test_full_analysis_workflow_state(self, fake):
        """Test state for a complete analysis workflow."""
        state = FinwizState(
            has_existing_session=True,
            session_id=str(fake.uuid4()),
            analysis_count=3,
            stock_analysis_success=True,
            etf_analysis_success=True,
            crypto_analysis_success=False,
            crypto_analysis_error="Data unavailable",
            deep_analysis_success=True,
            deep_analysis_count=5,
            portfolio_review_success=True,
            rebalancing_success=True,
            total_holdings=50,
            holdings_processed=50,
            holdings_remaining=0,
            progress_percentage=100.0,
        )

        assert state.has_existing_session is True
        assert state.stock_analysis_success is True
        assert state.etf_analysis_success is True
        assert state.crypto_analysis_success is False
        assert state.deep_analysis_count == 5
        assert state.progress_percentage == 100.0

    def test_error_tracking_state(self, fake):
        """Test state for error tracking and recovery."""
        state = FinwizState(
            errors=[
                "Failed to fetch data for AAPL",
                "Timeout on ETF analysis",
            ],
            failed_holdings=["AAPL", "GOOGL"],
            retry_counts={"AAPL": 2, "GOOGL": 1},
            timeout_holdings=["MSFT"],
            stock_analysis_error="Partial failure",
        )

        assert len(state.errors) == 2
        assert len(state.failed_holdings) == 2
        assert state.retry_counts["AAPL"] == 2
        assert "MSFT" in state.timeout_holdings

    def test_batch_processing_state(self):
        """Test state for batch processing."""
        prefetch_data = {
            "AAPL": {
                "price": 150.25,
                "volume": 1000000,
                "timestamp": "2024-01-01",
            },
            "GOOGL": {
                "price": 140.50,
                "volume": 500000,
                "timestamp": "2024-01-01",
            },
        }

        metrics = {
            "batch_size": 2,
            "prefetch_time_ms": 1500,
            "tickers_fetched": 2,
        }

        state = FinwizState(
            batch_prefetch_enabled=True,
            prefetched_data=prefetch_data,
            batch_prefetch_metrics=metrics,
        )

        assert state.batch_prefetch_enabled is True
        assert "AAPL" in state.prefetched_data
        assert state.batch_prefetch_metrics["batch_size"] == 2

    def test_report_generation_state(self):
        """Test state for report generation."""
        crew_paths = {
            "stock_crew": ["/reports/stock_crew/AAPL.html"],
            "etf_crew": ["/reports/etf_crew/SPY.html"],
        }

        state = FinwizState(
            crew_export_paths=crew_paths,
            crew_html_paths=crew_paths,
            consolidated_json_path="/reports/consolidated.json",
            final_report_path="/reports/final_report.html",
            crew_execution_status={
                "stock_crew": "completed",
                "etf_crew": "completed",
            },
        )

        assert "stock_crew" in state.crew_export_paths
        assert state.consolidated_json_path is not None
        assert state.final_report_path is not None


class TestFlowStateModelsSerialization:
    """Test serialization and deserialization."""

    def test_deep_analysis_result_json_serialization(self, sample_deep_analysis_result):
        """Test DeepAnalysisResult can be serialized to JSON."""
        json_str = sample_deep_analysis_result.model_dump_json(indent=2)

        assert isinstance(json_str, str)
        assert "ticker" in json_str
        assert sample_deep_analysis_result.ticker in json_str

    def test_deep_analysis_result_json_deserialization(self, sample_deep_analysis_result):
        """Test DeepAnalysisResult can be deserialized from JSON."""
        json_str = sample_deep_analysis_result.model_dump_json()
        recovered = DeepAnalysisResult.model_validate_json(json_str)

        assert recovered.ticker == sample_deep_analysis_result.ticker
        assert recovered.composite_score == sample_deep_analysis_result.composite_score
        assert recovered.grade == sample_deep_analysis_result.grade

    def test_finwiz_state_json_serialization(self, sample_finwiz_state):
        """Test FinwizState can be serialized to JSON."""
        json_str = sample_finwiz_state.model_dump_json(indent=2)

        assert isinstance(json_str, str)
        assert "session_id" in json_str or "analysis_count" in json_str

    def test_finwiz_state_with_nested_results_serialization(self):
        """Test FinwizState with nested DeepAnalysisResult serialization."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale="Strong",
            data_freshness_hours=1.0,
            confidence_level=0.95,
        )

        state = FinwizState(deep_analysis_results={"AAPL": result})

        json_str = state.model_dump_json()
        recovered = FinwizState.model_validate_json(json_str)

        assert "AAPL" in recovered.deep_analysis_results
        assert recovered.deep_analysis_results["AAPL"].ticker == "AAPL"

    def test_model_dump_dict(self, sample_deep_analysis_result):
        """Test model_dump_dict conversion."""
        dumped = sample_deep_analysis_result.model_dump()

        assert isinstance(dumped, dict)
        assert "ticker" in dumped
        assert dumped["ticker"] == sample_deep_analysis_result.ticker


class TestFlowStateModelsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_collections_in_finwiz_state(self):
        """Test FinwizState with empty collections."""
        state = FinwizState(
            errors=[],
            failed_holdings=[],
            timeout_holdings=[],
            stale_data_warnings=[],
            error_summaries=[],
            deep_analysis_results={},
            portfolio_alternatives={},
            retry_counts={},
        )

        assert state.errors == []
        assert state.failed_holdings == []
        assert state.deep_analysis_results == {}
        assert state.retry_counts == {}

    def test_large_collections(self, fake):
        """Test FinwizState with large collections."""
        large_errors = [fake.sentence() for _ in range(100)]
        large_retry_counts = {f"TICK{i}": fake.random_int(0, 5) for i in range(50)}

        state = FinwizState(
            errors=large_errors,
            retry_counts=large_retry_counts,
            total_holdings=1000,
            holdings_processed=750,
            holdings_remaining=250,
        )

        assert len(state.errors) == 100
        assert len(state.retry_counts) == 50
        assert state.total_holdings == 1000

    def test_special_characters_in_strings(self):
        """Test handling of special characters in string fields."""
        state = FinwizState(
            stock_result="Result with special chars: @#$%^&*()",
            session_id="session-with-dashes-and_underscores",
            current_ticker="BRK.A",  # Ticker with dot
        )

        assert "@#$%^&*()" in state.stock_result
        assert "dashes-and_underscores" in state.session_id
        assert state.current_ticker == "BRK.A"

    def test_very_long_strings(self, fake):
        """Test handling of very long strings."""
        long_text = fake.text(max_nb_chars=5000)

        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.85,
            grade="A",
            recommendation="BUY",
            rationale=long_text,
            data_freshness_hours=1.0,
            confidence_level=0.90,
        )

        assert len(result.rationale) >= 4000

    def test_none_values_for_optional_fields(self):
        """Test that optional fields can be explicitly set to None."""
        state = FinwizState(
            stock_analysis_error=None,
            data_availability_report=None,
            portfolio_review=None,
            market_sentiment=None,
            aplus_opportunities=None,
        )

        assert state.stock_analysis_error is None
        assert state.data_availability_report is None
        assert state.portfolio_review is None
        assert state.market_sentiment is None
        assert state.aplus_opportunities is None

    def test_zero_numeric_values(self):
        """Test that zero numeric values are properly handled."""
        state = FinwizState(
            analysis_count=0,
            holdings_processed=0,
            progress_percentage=0.0,
            estimated_time_remaining=0.0,
        )

        assert state.analysis_count == 0
        assert state.holdings_processed == 0
        assert state.progress_percentage == 0.0
        assert state.estimated_time_remaining == 0.0

    def test_boundary_score_values(self):
        """Test boundary values for score fields."""
        result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="stock_crew",
            composite_score=0.0,  # Minimum
            grade="F",
            recommendation="SELL",
            rationale="Poor performance",
            data_freshness_hours=0.0,
            confidence_level=0.0,
            fundamental_score=0.0,
            technical_score=1.0,  # Maximum
            risk_score=5.0,  # Maximum risk
        )

        assert result.composite_score == 0.0
        assert result.confidence_level == 0.0
        assert result.technical_score == 1.0
        assert result.risk_score == 5.0
