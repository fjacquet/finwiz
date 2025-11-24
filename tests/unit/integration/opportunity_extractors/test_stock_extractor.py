"""
Unit tests for StockOpportunityExtractor.

Tests stock-specific extraction logic using the Template Method pattern.
"""

from pytest import approx
import pytest

from finwiz.integration.opportunity_extractors import StockOpportunityExtractor


class TestStockOpportunityExtractor:
    """Test suite for StockOpportunityExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create StockOpportunityExtractor instance."""
        return StockOpportunityExtractor()

    @pytest.fixture
    def valid_stock_candidate(self):
        """Create valid stock candidate for testing."""
        return {
            "symbol": "NVDA",
            "name": "NVIDIA Corporation",
            "grade": "A+",
            "fundamentals": {"roe_3y_avg": 0.45, "revenue_cagr_5y": 0.36, "debt_to_equity": 0.15},
            "risk_assessment": {"score": 3.5},
            "moat_analysis": {"moat_type": "Technology", "moat_strength": "Wide", "competitive_advantage": "GPU dominance"},
            "implementation": {"entry_strategy": "Dollar-cost averaging"},
            "market_cap_usd": 1100000000000,
        }

    @pytest.fixture
    def stock_candidate_with_string_moat(self):
        """Create stock candidate with moat_analysis as string."""
        return {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "grade": "A",
            "fundamentals": {"roe_3y_avg": 0.40, "revenue_cagr_5y": 0.10, "debt_to_equity": 0.20},
            "risk_assessment": {"score": 2.5},
            "moat_analysis": "Strong brand and ecosystem",
            "implementation": {"entry_strategy": "Buy on dips"},
            "market_cap_usd": 2800000000000,
        }

    def test_should_include_aplus_grade_stock(self, extractor, valid_stock_candidate):
        """Test that A+ grade stocks are included."""
        # Act
        result = extractor._should_include(valid_stock_candidate)

        # Assert
        assert result is True

    def test_should_include_a_grade_stock(self, extractor, valid_stock_candidate):
        """Test that A grade stocks are included."""
        # Arrange
        valid_stock_candidate["grade"] = "A"

        # Act
        result = extractor._should_include(valid_stock_candidate)

        # Assert
        assert result is True

    def test_should_exclude_b_grade_stock(self, extractor, valid_stock_candidate):
        """Test that B grade stocks are excluded."""
        # Arrange
        valid_stock_candidate["grade"] = "B"

        # Act
        result = extractor._should_include(valid_stock_candidate)

        # Assert
        assert result is False

    def test_should_exclude_stock_without_symbol(self, extractor, valid_stock_candidate):
        """Test that stocks without symbol are excluded."""
        # Arrange
        valid_stock_candidate["symbol"] = ""

        # Act
        result = extractor._should_include(valid_stock_candidate)

        # Assert
        assert result is False

    def test_should_exclude_stock_without_name(self, extractor, valid_stock_candidate):
        """Test that stocks without name are excluded."""
        # Arrange
        valid_stock_candidate["name"] = ""

        # Act
        result = extractor._should_include(valid_stock_candidate)

        # Assert
        assert result is False

    def test_should_build_opportunity_with_dict_moat_analysis(self, extractor, valid_stock_candidate):
        """Test building opportunity with moat_analysis as dict."""
        # Act
        opportunity = extractor._build_opportunity(valid_stock_candidate, 0)

        # Assert
        assert opportunity is not None
        assert opportunity["symbol"] == "NVDA"
        assert opportunity["name"] == "NVIDIA Corporation"
        assert opportunity["grade"] == "A+"
        assert opportunity["composite_score"] > 0
        assert opportunity["confidence"] == approx(0.85)  # A+ confidence
        assert opportunity["risk_score"] == approx(3.5)
        assert "Moat: Technology" in opportunity["rationale"]
        assert "Strength: Wide" in opportunity["rationale"]
        assert opportunity["allocation_recommendation"] == "GPU dominance"
        assert opportunity["replacement_note"] == "Dollar-cost averaging"
        assert "roe_3y_avg" in opportunity["key_metrics"]
        assert opportunity["key_metrics"]["roe_3y_avg"] == approx(0.45)

    def test_should_build_opportunity_with_string_moat_analysis(self, extractor, stock_candidate_with_string_moat):
        """Test building opportunity with moat_analysis as string."""
        # Act
        opportunity = extractor._build_opportunity(stock_candidate_with_string_moat, 0)

        # Assert
        assert opportunity is not None
        assert opportunity["symbol"] == "AAPL"
        assert opportunity["name"] == "Apple Inc."
        assert opportunity["grade"] == "A"
        assert opportunity["confidence"] == approx(0.75)  # A confidence
        assert "Strong brand and ecosystem" in opportunity["rationale"]
        assert opportunity["allocation_recommendation"] == ""

    def test_should_calculate_composite_score_correctly(self, extractor, valid_stock_candidate):
        """Test composite score calculation from fundamentals."""
        # Act
        opportunity = extractor._build_opportunity(valid_stock_candidate, 0)

        # Assert
        # Score = (ROE/20 * 0.4) + (revenue_growth/15 * 0.4) + ((1 - debt_ratio) * 0.2)
        # Score = (0.45/20 * 0.4) + (0.36/15 * 0.4) + ((1 - 0.15) * 0.2)
        # Score = (0.0225 * 0.4) + (0.024 * 0.4) + (0.85 * 0.2)
        # Score = 0.009 + 0.0096 + 0.17 = 0.1886
        expected_score = min((0.45 / 20 * 0.4) + (0.36 / 15 * 0.4) + ((1 - min(0.15, 1)) * 0.2), 1.0)
        assert abs(opportunity["composite_score"] - expected_score) < 0.01

    def test_should_extract_multiple_stocks(self, extractor, valid_stock_candidate, stock_candidate_with_string_moat):
        """Test extracting multiple stock opportunities."""
        # Arrange
        candidates = [valid_stock_candidate, stock_candidate_with_string_moat]

        # Act
        opportunities = extractor.extract(candidates)

        # Assert
        assert len(opportunities) == 2
        assert opportunities[0]["symbol"] == "NVDA"
        assert opportunities[1]["symbol"] == "AAPL"

    def test_should_handle_missing_fundamentals_gracefully(self, extractor, valid_stock_candidate):
        """Test handling of missing fundamentals data."""
        # Arrange
        valid_stock_candidate["fundamentals"] = {}

        # Act
        opportunity = extractor._build_opportunity(valid_stock_candidate, 0)

        # Assert
        assert opportunity is not None
        assert opportunity["composite_score"] >= 0
        assert opportunity["key_metrics"]["roe_3y_avg"] == 0

    def test_should_handle_missing_risk_assessment_gracefully(self, extractor, valid_stock_candidate):
        """Test handling of missing risk assessment."""
        # Arrange
        del valid_stock_candidate["risk_assessment"]

        # Act
        opportunity = extractor._build_opportunity(valid_stock_candidate, 0)

        # Assert
        assert opportunity is not None
        assert opportunity["risk_score"] == approx(5.0)  # Default

    def test_should_return_empty_list_for_empty_candidates(self, extractor):
        """Test extraction with empty candidates list."""
        # Act
        opportunities = extractor.extract([])

        # Assert
        assert opportunities == []

    def test_should_filter_out_low_grade_stocks(self, extractor, valid_stock_candidate):
        """Test that low-grade stocks are filtered out."""
        # Arrange
        valid_stock_candidate["grade"] = "C"

        # Act
        opportunities = extractor.extract([valid_stock_candidate])

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