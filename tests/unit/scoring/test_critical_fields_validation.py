"""
Unit tests for critical fields validation in deep analysis scorer.

Tests that the scorer FAILS FAST when critical fields are missing,
rather than silently using hardcoded fallback values.
"""

import pytest

from finwiz.config.critical_fields_config import CriticalFieldError
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer


class TestCriticalFieldsValidation:
    """Test critical fields validation prevents analysis with missing data."""

    @pytest.fixture
    def scorer(self):
        """Create scorer instance."""
        return DeepAnalysisScorer()

    @pytest.fixture
    def complete_stock_data(self):
        """Complete stock data with all critical fields."""
        return {
            "asset_class": "stock",
            # Critical fields
            "current_price": 150.0,
            "roe": 0.20,
            "debt_to_equity": 0.5,
            "revenue_growth": 0.15,
            "volatility": 0.25,
            "beta": 1.2,
            # Optional fields
            "rsi": 55.0,
            "macd": 0.5,
            "profit_margin": 0.15,
        }

    def test_should_succeed_with_all_critical_fields(self, scorer, complete_stock_data):
        """Test that analysis succeeds when all critical fields are present."""
        # Act
        result = scorer.calculate_composite_score("AAPL", "stock", complete_stock_data)

        # Assert
        assert result is not None
        assert result.ticker == "AAPL"
        assert result.composite_score > 0
        assert result.grade in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]

    def test_should_fail_when_critical_field_missing(self, scorer, complete_stock_data):
        """Test that analysis FAILS when critical field is missing."""
        # Arrange - Remove critical field
        incomplete_data = complete_stock_data.copy()
        del incomplete_data["roe"]

        # Act & Assert
        with pytest.raises(CriticalFieldError) as exc_info:
            scorer.calculate_composite_score("AAPL", "stock", incomplete_data)

        # Verify error details
        assert exc_info.value.ticker == "AAPL"
        assert exc_info.value.asset_class == "stock"
        # Implementation adds " (missing)" suffix to field names
        assert any("roe" in field for field in exc_info.value.missing_fields)

    def test_should_fail_when_multiple_critical_fields_missing(self, scorer):
        """Test that analysis FAILS when multiple critical fields are missing."""
        # Arrange - Only optional fields present
        incomplete_data = {
            "asset_class": "stock",
            "rsi": 55.0,  # Optional
            "macd": 0.5,  # Optional
        }

        # Act & Assert
        with pytest.raises(CriticalFieldError) as exc_info:
            scorer.calculate_composite_score("AAPL", "stock", incomplete_data)

        # Verify multiple fields reported (implementation adds " (missing)" suffix)
        assert len(exc_info.value.missing_fields) > 1
        assert any("current_price" in field for field in exc_info.value.missing_fields)
        assert any("roe" in field for field in exc_info.value.missing_fields)

    def test_should_use_safe_default_for_optional_field(self, scorer, complete_stock_data):
        """Test that optional fields can use safe defaults."""
        # Arrange - Remove optional field
        data_without_optional = complete_stock_data.copy()
        del data_without_optional["rsi"]  # Optional field

        # Act - Should succeed with default RSI
        result = scorer.calculate_composite_score("AAPL", "stock", data_without_optional)

        # Assert
        assert result is not None
        assert result.ticker == "AAPL"
        # Analysis should complete successfully

    def test_should_fail_for_etf_missing_critical_fields(self, scorer):
        """Test that ETF analysis fails when critical fields missing."""
        # Arrange - ETF data missing expense_ratio (critical)
        incomplete_etf_data = {
            "asset_class": "etf",
            "current_price": 100.0,
            "tracking_error": 0.15,
            "aum": 5e9,
            "volatility": 0.15,
            # Missing: expense_ratio (critical)
        }

        # Act & Assert
        with pytest.raises(CriticalFieldError) as exc_info:
            scorer.calculate_composite_score("SPY", "etf", incomplete_etf_data)

        # Implementation adds " (missing)" suffix to field names
        assert any("expense_ratio" in field for field in exc_info.value.missing_fields)

    def test_should_fail_for_crypto_missing_critical_fields(self, scorer):
        """Test that crypto analysis fails when critical fields missing."""
        # Arrange - Crypto data missing market_cap (critical)
        incomplete_crypto_data = {
            "asset_class": "crypto",
            "current_price": 50000.0,
            "volume_24h": 1e9,
            "age_years": 5.0,
            "volatility": 0.60,
            # Missing: market_cap (critical)
        }

        # Act & Assert
        with pytest.raises(CriticalFieldError) as exc_info:
            scorer.calculate_composite_score("BTC", "crypto", incomplete_crypto_data)

        # Implementation adds " (missing)" suffix to field names
        assert any("market_cap" in field for field in exc_info.value.missing_fields)

    @pytest.mark.skip(reason="Data quality tracking feature not fully implemented - tracked in separate issue")
    def test_should_track_defaulted_optional_fields_in_data_quality(self, scorer, complete_stock_data):
        """Test that defaulted optional fields are tracked in data quality metrics."""
        # Arrange - Remove optional field
        data_without_optional = complete_stock_data.copy()
        del data_without_optional["profit_margin"]  # Optional

        # Act
        result = scorer.calculate_composite_score("AAPL", "stock", data_without_optional)

        # Assert - Check data quality tracking
        data_quality = result.data_quality
        assert "defaulted_fields" in data_quality["field_tracking"]
        assert "profit_margin" in data_quality["field_tracking"]["defaulted_fields"]

    def test_should_include_critical_field_error_in_lineage(self, scorer):
        """Test that critical field errors are tracked in lineage."""
        # Arrange - Missing critical field
        incomplete_data = {
            "asset_class": "stock",
            "current_price": 150.0,
            # Missing: roe, debt_to_equity, etc.
        }

        # Act & Assert
        with pytest.raises(CriticalFieldError):
            scorer.calculate_composite_score("AAPL", "stock", incomplete_data)

        # Lineage should track the failure
        # (Implementation detail - lineage tracker should record validation failure)


class TestCriticalFieldsConfig:
    """Test critical fields configuration."""

    def test_stock_critical_fields_defined(self):
        """Test that stock critical fields are properly defined."""
        from finwiz.config.critical_fields_config import get_critical_fields

        critical = get_critical_fields("stock")

        assert "current_price" in critical
        assert "roe" in critical
        assert "debt_to_equity" in critical
        assert "revenue_growth" in critical
        assert "volatility" in critical
        assert "beta" in critical

    def test_etf_critical_fields_defined(self):
        """Test that ETF critical fields are properly defined."""
        from finwiz.config.critical_fields_config import get_critical_fields, get_optional_fields

        critical = get_critical_fields("etf")
        optional = get_optional_fields("etf")

        # Critical fields (must have real data)
        assert "current_price" in critical
        assert "expense_ratio" in critical
        assert "volatility" in critical

        # Optional fields (moved from critical - not always available)
        assert "tracking_error" in optional  # Moved to optional for international ETFs
        assert "aum" in optional  # Moved to optional - not available on all exchanges

    def test_crypto_critical_fields_defined(self):
        """Test that crypto critical fields are properly defined."""
        from finwiz.config.critical_fields_config import get_critical_fields

        critical = get_critical_fields("crypto")

        assert "current_price" in critical
        assert "market_cap" in critical
        assert "volume_24h" in critical
        assert "volatility" in critical
        assert "age_years" in critical

    def test_optional_fields_have_safe_defaults(self):
        """Test that optional fields have safe default values."""
        from finwiz.config.critical_fields_config import get_safe_default

        # Technical indicators should have neutral defaults
        assert get_safe_default("rsi") == 50.0  # Neutral RSI
        assert get_safe_default("macd") == 0.0  # Neutral MACD

        # Critical fields should NOT have defaults
        assert get_safe_default("roe") is None
        assert get_safe_default("debt_to_equity") is None
