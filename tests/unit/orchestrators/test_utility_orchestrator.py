"""
Unit tests for UtilityOrchestrator.

Tests crew output parsing, grade distribution calculation,
SEC URL extraction, and URL validation/fixing.
"""

import pytest
from pytest import approx

from finwiz.cache.analysis_cache_manager import CrewAnalysisResult
from finwiz.flow_state import FinwizState
from finwiz.orchestrators.utility_orchestrator import UtilityOrchestrator


class TestUtilityOrchestrator:
    """Test suite for UtilityOrchestrator."""

    @pytest.fixture
    def state(self):
        """Create a FinwizState instance for testing."""
        return FinwizState()

    @pytest.fixture
    def orchestrator(self, state):
        """Create a UtilityOrchestrator instance for testing."""
        return UtilityOrchestrator(state)

    def test_parse_crew_output_with_pydantic_data(self, orchestrator, mocker):
        """Test parsing crew output with pydantic data."""
        # Arrange
        crew_result = mocker.Mock()
        crew_result.pydantic = mocker.Mock()
        crew_result.pydantic.fundamental_score = 0.85
        crew_result.pydantic.technical_score = 0.75
        crew_result.pydantic.risk_score = 2.5  # 0-5 scale
        crew_result.pydantic.composite_score = 0.80

        # Act
        result = orchestrator.parse_crew_output_for_holding(
            crew_result=crew_result,
            ticker="AAPL",
            asset_class="stock",
            crew_name="test_crew",
        )

        # Assert
        assert isinstance(result, CrewAnalysisResult)
        assert result.ticker == "AAPL"
        assert result.asset_class == "stock"
        assert result.crew_name == "test_crew"
        assert result.fundamental_score == approx(0.85)
        assert result.technical_score == approx(0.75)
        assert result.risk_score == approx(0.5)  # Normalized from 2.5/5
        assert result.composite_score == approx(0.80)
        assert result.grade in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"]

    def test_parse_crew_output_calculates_composite_when_missing(self, orchestrator, mocker):
        """Test that composite score is calculated when not provided."""
        # Arrange
        crew_result = mocker.Mock()
        pydantic_mock = mocker.Mock(spec=["fundamental_score", "technical_score", "risk_score"])
        pydantic_mock.fundamental_score = 0.80
        pydantic_mock.technical_score = 0.70
        pydantic_mock.risk_score = 1.0  # 0-5 scale
        crew_result.pydantic = pydantic_mock

        # Act
        result = orchestrator.parse_crew_output_for_holding(
            crew_result=crew_result,
            ticker="GOOGL",
            asset_class="stock",
            crew_name="test_crew",
        )

        # Assert
        assert result.composite_score is not None
        # Should be average of fund and tech with risk penalty
        # risk_score is 1.0 (already normalized 0-1 scale), so penalty is 1.0 * 0.10 = 0.10
        expected = (0.80 + 0.70) / 2 * (1.0 - 1.0 * 0.10)  # 0.75 * 0.90 = 0.675
        assert abs(result.composite_score - expected) < 0.01

    def test_parse_crew_output_from_raw_text(self, orchestrator, mocker):
        """Test parsing crew output from raw text."""
        # Arrange
        crew_result = mocker.Mock()
        crew_result.pydantic = None
        crew_result.raw = """
        Analysis complete:
        Fundamental Score: 0.85
        Technical Score: 0.75
        Risk Score: 2.5
        """

        # Act
        result = orchestrator.parse_crew_output_for_holding(
            crew_result=crew_result,
            ticker="MSFT",
            asset_class="stock",
            crew_name="test_crew",
        )

        # Assert
        assert result.fundamental_score == approx(0.85)
        assert result.technical_score == approx(0.75)
        assert result.risk_score == approx(0.5)  # Normalized from 2.5/5
        assert result.composite_score is not None

    def test_parse_crew_output_raises_on_missing_scores(self, orchestrator, mocker):
        """Test that parsing raises ValueError when no scores found."""
        # Arrange
        crew_result = mocker.Mock()
        crew_result.pydantic = None
        crew_result.raw = "No scores here"

        # Act & Assert
        with pytest.raises(ValueError, match="Failed to parse crew output"):
            orchestrator.parse_crew_output_for_holding(
                crew_result=crew_result,
                ticker="INVALID",
                asset_class="stock",
                crew_name="test_crew",
            )

    def test_calculate_grade_distribution_with_dict_holdings(self, orchestrator):
        """Test grade distribution calculation with dict-based holdings."""
        # Arrange
        holdings = [
            {"ticker": "AAPL", "grade": "A+"},
            {"ticker": "GOOGL", "grade": "A"},
            {"ticker": "MSFT", "grade": "A+"},
            {"ticker": "TSLA", "grade": "B"},
            {"ticker": "AMZN", "grade": "A"},
        ]

        # Act
        distribution = orchestrator.calculate_grade_distribution(holdings)

        # Assert
        assert distribution == {"A+": 2, "A": 2, "B": 1}

    def test_calculate_grade_distribution_with_object_holdings(self, orchestrator, mocker):
        """Test grade distribution calculation with object-based holdings."""
        # Arrange
        holdings = [
            mocker.Mock(grade="A+"),
            mocker.Mock(grade="A+"),
            mocker.Mock(grade="A"),
            mocker.Mock(grade="B"),
            mocker.Mock(grade="C"),
        ]

        # Act
        distribution = orchestrator.calculate_grade_distribution(holdings)

        # Assert
        assert distribution == {"A+": 2, "A": 1, "B": 1, "C": 1}

    def test_calculate_grade_distribution_handles_missing_grades(self, orchestrator, mocker):
        """Test that missing grades are counted as N/A."""
        # Arrange
        mock_no_grade = mocker.Mock(spec=[])  # Mock with no attributes
        holdings = [
            {"ticker": "AAPL", "grade": "A+"},
            {"ticker": "GOOGL"},  # Missing grade
            mocker.Mock(grade="A"),
            mock_no_grade,  # No grade attribute
        ]

        # Act
        distribution = orchestrator.calculate_grade_distribution(holdings)

        # Assert
        assert distribution["A+"] == 1
        assert distribution["A"] == 1
        assert distribution["N/A"] == 2

    def test_extract_sec_filing_urls_from_deep_analysis(self, orchestrator, state):
        """Test SEC URL extraction from deep analysis results."""
        # Arrange
        state.deep_analysis_results = {
            "AAPL": {
                "asset_class": "stock",
                "sec_filing_urls": {
                    "10-K": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K",
                    "10-Q": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-Q",
                },
            },
            "GOOGL": {
                "asset_class": "stock",
                "sec_filings": {
                    "10-K": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001652044&type=10-K",
                },
            },
        }

        # Act
        urls = orchestrator.extract_sec_filing_urls(crew_output=None)

        # Assert
        assert "AAPL" in urls
        assert "10-K" in urls["AAPL"]
        assert "10-Q" in urls["AAPL"]
        assert "GOOGL" in urls
        assert "10-K" in urls["GOOGL"]

    def test_extract_sec_filing_urls_skips_non_stock_holdings(self, orchestrator, state):
        """Test that SEC URL extraction skips non-stock holdings."""
        # Arrange
        state.deep_analysis_results = {
            "BTC": {
                "asset_class": "crypto",
                "sec_filing_urls": {"10-K": "https://example.com"},
            },
            "SPY": {
                "asset_class": "etf",
                "sec_filing_urls": {"10-K": "https://example.com"},
            },
        }

        # Act
        urls = orchestrator.extract_sec_filing_urls(crew_output=None)

        # Assert
        assert len(urls) == 0

    def test_validate_and_fix_sec_urls_keeps_valid_urls(self, orchestrator, mocker):
        """Test that valid URLs are kept unchanged."""
        # Arrange
        urls = {
            "10-K": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K",
            "10-Q": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-Q",
        }
        mock_validator = mocker.Mock()
        mock_validator.is_valid_url.return_value = True

        # Act
        validated = orchestrator.validate_and_fix_sec_urls(
            urls=urls,
            ticker="AAPL",
            url_validator=mock_validator,
        )

        # Assert
        assert validated == urls

    def test_validate_and_fix_sec_urls_regenerates_invalid_urls(self, orchestrator, mocker):
        """Test that invalid URLs are regenerated."""
        # Arrange
        urls = {
            "10-K": "invalid-url",
            "10-Q": "",
        }
        mock_validator = mocker.Mock()
        mock_validator.is_valid_url.return_value = False

        mock_generator = mocker.Mock()
        mock_generator.get_filing_metadata.return_value = {"filing_url": "https://www.sec.gov/valid-url"}

        # Act
        validated = orchestrator.validate_and_fix_sec_urls(
            urls=urls,
            ticker="AAPL",
            url_generator=mock_generator,
            url_validator=mock_validator,
        )

        # Assert
        assert validated["10-K"] == "https://www.sec.gov/valid-url"
        assert validated["10-Q"] == "https://www.sec.gov/valid-url"
        assert mock_generator.get_filing_metadata.call_count == 2
