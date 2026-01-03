"""
Unit tests for ETFOpportunityExtractor.

Tests ETF-specific extraction logic using the Template Method pattern.
"""

import pytest
from pytest import approx

from finwiz.orchestrators.discovery.extractors import ETFOpportunityExtractor


class TestETFOpportunityExtractor:
    """Test suite for ETFOpportunityExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create ETFOpportunityExtractor instance."""
        return ETFOpportunityExtractor()

    @pytest.fixture
    def valid_etf_candidate(self):
        """Create valid ETF candidate for testing."""
        return {
            "symbol": "VWCE",
            "name": "Vanguard FTSE All-World UCITS ETF",
            "grade": "A+",
            "cost_metrics": {"ter": 0.0022, "aum_usd": 17500000000, "tracking_error_3y": 0.05},
            "risk_assessment": {"score": 3.0},
            "diversification": {"holdings_count": 3500, "top_10_concentration_pct": 15.5, "sector_breakdown": "Global diversification"},
            "implementation": {"entry_strategy": "Core holding"},
        }

    @pytest.fixture
    def etf_candidate_with_string_diversification(self):
        """Create ETF candidate with diversification as string."""
        return {
            "symbol": "IWDA",
            "name": "iShares Core MSCI World UCITS ETF",
            "grade": "A",
            "cost_metrics": {"ter": 0.0020, "aum_usd": 60000000000, "tracking_error_3y": 0.03},
            "risk_assessment": {"score": 2.5},
            "diversification": "Broad developed markets exposure",
            "implementation": {"entry_strategy": "Buy and hold"},
        }

    def test_should_include_aplus_grade_etf_with_low_ter(self, extractor, valid_etf_candidate):
        """Test that A+ grade ETFs with low TER are included."""
        # Act
        result = extractor._should_include(valid_etf_candidate)

        # Assert
        assert result is True

    def test_should_include_a_grade_etf_with_low_ter(self, extractor, valid_etf_candidate):
        """Test that A grade ETFs with low TER are included."""
        # Arrange
        valid_etf_candidate["grade"] = "A"

        # Act
        result = extractor._should_include(valid_etf_candidate)

        # Assert
        assert result is True

    def test_should_exclude_etf_with_high_ter(self, extractor, valid_etf_candidate):
        """Test that ETFs with high TER are excluded."""
        # Arrange
        valid_etf_candidate["cost_metrics"]["ter"] = 0.20  # 20% TER (too high)

        # Act
        result = extractor._should_include(valid_etf_candidate)

        # Assert
        assert result is False

    def test_should_exclude_b_grade_etf(self, extractor, valid_etf_candidate):
        """Test that B grade ETFs are excluded."""
        # Arrange
        valid_etf_candidate["grade"] = "B"

        # Act
        result = extractor._should_include(valid_etf_candidate)

        # Assert
        assert result is False

    def test_should_exclude_etf_without_symbol(self, extractor, valid_etf_candidate):
        """Test that ETFs without symbol are excluded."""
        # Arrange
        valid_etf_candidate["symbol"] = ""

        # Act
        result = extractor._should_include(valid_etf_candidate)

        # Assert
        assert result is False

    def test_should_exclude_etf_without_name(self, extractor, valid_etf_candidate):
        """Test that ETFs without name are excluded."""
        # Arrange
        valid_etf_candidate["name"] = ""

        # Act
        result = extractor._should_include(valid_etf_candidate)

        # Assert
        assert result is False

    def test_should_build_opportunity_with_dict_diversification(self, extractor, valid_etf_candidate):
        """Test building opportunity with diversification as dict."""
        # Act
        opportunity = extractor._build_opportunity(valid_etf_candidate, 0)

        # Assert
        assert opportunity is not None
        assert opportunity["symbol"] == "VWCE"
        assert opportunity["name"] == "Vanguard FTSE All-World UCITS ETF"
        assert opportunity["grade"] == "A+"
        assert opportunity["composite_score"] > 0
        assert opportunity["confidence"] == approx(0.90)  # A+ confidence for ETF
        assert opportunity["risk_score"] == approx(3.0)
        assert "Holdings: 3500" in opportunity["rationale"]
        assert "Top 10 concentration: 15.5%" in opportunity["rationale"]
        assert opportunity["allocation_recommendation"] == "Global diversification"
        assert opportunity["replacement_note"] == "Core holding"
        assert "ter" in opportunity["key_metrics"]
        assert opportunity["key_metrics"]["ter"] == approx(0.0022)

    def test_should_build_opportunity_with_string_diversification(self, extractor, etf_candidate_with_string_diversification):
        """Test building opportunity with diversification as string."""
        # Act
        opportunity = extractor._build_opportunity(etf_candidate_with_string_diversification, 0)

        # Assert
        assert opportunity is not None
        assert opportunity["symbol"] == "IWDA"
        assert opportunity["name"] == "iShares Core MSCI World UCITS ETF"
        assert opportunity["grade"] == "A"
        assert opportunity["confidence"] == approx(0.80)  # A confidence for ETF
        assert "Broad developed markets exposure" in opportunity["rationale"]
        assert opportunity["allocation_recommendation"] == ""

    def test_should_format_aum_correctly(self, extractor, valid_etf_candidate):
        """Test AUM formatting for different sizes."""
        # Test billions
        valid_etf_candidate["cost_metrics"]["aum_usd"] = 17500000000
        opportunity = extractor._build_opportunity(valid_etf_candidate, 0)
        assert opportunity["key_metrics"]["aum_formatted"] == "$17.5B"

        # Test millions
        valid_etf_candidate["cost_metrics"]["aum_usd"] = 500000000
        opportunity = extractor._build_opportunity(valid_etf_candidate, 0)
        assert opportunity["key_metrics"]["aum_formatted"] == "$500.0M"

        # Test smaller amounts
        valid_etf_candidate["cost_metrics"]["aum_usd"] = 50000
        opportunity = extractor._build_opportunity(valid_etf_candidate, 0)
        assert opportunity["key_metrics"]["aum_formatted"] == "$50,000"

    def test_should_calculate_composite_score_correctly(self, extractor, valid_etf_candidate):
        """Test composite score calculation from cost metrics."""
        # Act
        opportunity = extractor._build_opportunity(valid_etf_candidate, 0)

        # Assert
        # Score = (1 - TER) * 0.4 + (1 - tracking_error) * 0.4 + 0.2
        # Score = (1 - 0.0022) * 0.4 + (1 - 0.05) * 0.4 + 0.2
        # Score = 0.9978 * 0.4 + 0.95 * 0.4 + 0.2
        # Score = 0.39912 + 0.38 + 0.2 = 0.97912
        expected_score = min((1 - 0.0022) * 0.4 + (1 - 0.05) * 0.4 + 0.2, 1.0)
        assert abs(opportunity["composite_score"] - expected_score) < 0.01

    def test_should_extract_multiple_etfs(self, extractor, valid_etf_candidate, etf_candidate_with_string_diversification):
        """Test extracting multiple ETF opportunities."""
        # Arrange
        candidates = [valid_etf_candidate, etf_candidate_with_string_diversification]

        # Act
        opportunities = extractor.extract(candidates)

        # Assert
        assert len(opportunities) == 2
        assert opportunities[0]["symbol"] == "VWCE"
        assert opportunities[1]["symbol"] == "IWDA"

    def test_should_handle_missing_cost_metrics_gracefully(self, extractor, valid_etf_candidate):
        """Test handling of missing cost metrics."""
        # Arrange
        valid_etf_candidate["cost_metrics"] = {}

        # Act
        opportunity = extractor._build_opportunity(valid_etf_candidate, 0)

        # Assert
        assert opportunity is not None
        assert opportunity["composite_score"] >= 0
        assert opportunity["key_metrics"]["ter"] == approx(0.0)

    def test_should_handle_missing_risk_assessment_gracefully(self, extractor, valid_etf_candidate):
        """Test handling of missing risk assessment."""
        # Arrange
        del valid_etf_candidate["risk_assessment"]

        # Act
        opportunity = extractor._build_opportunity(valid_etf_candidate, 0)

        # Assert
        assert opportunity is not None
        assert opportunity["risk_score"] == approx(3.0)  # Default for ETF

    def test_should_return_empty_list_for_empty_candidates(self, extractor):
        """Test extraction with empty candidates list."""
        # Act
        opportunities = extractor.extract([])

        # Assert
        assert opportunities == []

    def test_should_filter_out_low_grade_etfs(self, extractor, valid_etf_candidate):
        """Test that low-grade ETFs are filtered out."""
        # Arrange
        valid_etf_candidate["grade"] = "C"

        # Act
        opportunities = extractor.extract([valid_etf_candidate])

        # Assert
        assert len(opportunities) == 0

    def test_should_filter_out_high_ter_etfs(self, extractor, valid_etf_candidate):
        """Test that high TER ETFs are filtered out even with A+ grade."""
        # Arrange
        valid_etf_candidate["cost_metrics"]["ter"] = 0.25  # 25% TER

        # Act
        opportunities = extractor.extract([valid_etf_candidate])

        # Assert
        assert len(opportunities) == 0

    def test_should_handle_extraction_errors_gracefully(self, extractor):
        """Test handling of extraction errors."""
        # Arrange
        invalid_candidate = {"symbol": "TEST"}  # Missing required fields

        # Act
        opportunity = extractor._build_opportunity(invalid_candidate, 0)

        # Assert
        # Should return opportunity with default values (Python doesn't raise on missing dict keys with .get())
        assert opportunity is not None
        assert opportunity["symbol"] == "TEST"
        assert opportunity["composite_score"] >= 0
