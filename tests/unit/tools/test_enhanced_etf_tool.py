"""
Unit tests for Enhanced ETF Analysis Tool.

Tests the enhanced ETF factsheet parsing, holdings extraction,
tracking analysis, and standardized risk assessment capabilities.
"""

from datetime import date

import pytest
from bs4 import BeautifulSoup
from crewai_custom_tools.core.results import err, ok
from pytest import approx

from finwiz.tools.enhanced_etf_tool import EnhancedETFAnalysisInput, EnhancedETFAnalysisTool
from finwiz.tools.etf.etf_analyzers import ETFAnalyzer
from finwiz.tools.etf.etf_data_fetchers import ETFDataFetcher

_CENTRAL_RUN_PATH = "crewai_custom_tools.tools.finance.enhanced.EnhancedETFAnalysisTool._run"


class TestEnhancedETFAnalysisInput:
    """Test the input schema for Enhanced ETF Analysis Tool."""

    def test_should_create_valid_input_with_defaults(self):
        """Test creating input with default values."""
        # Arrange & Act
        input_data = EnhancedETFAnalysisInput(ticker="SPY")

        # Assert
        assert input_data.ticker == "SPY"
        assert input_data.include_holdings is True
        assert input_data.include_risk_assessment is True
        assert input_data.max_holdings == 10

    def test_should_create_valid_input_with_custom_values(self):
        """Test creating input with custom values."""
        # Arrange & Act
        input_data = EnhancedETFAnalysisInput(ticker="VTI", include_holdings=False, include_risk_assessment=False, max_holdings=5)

        # Assert
        assert input_data.ticker == "VTI"
        assert input_data.include_holdings is False
        assert input_data.include_risk_assessment is False
        assert input_data.max_holdings == 5

    def test_should_validate_max_holdings_range(self):
        """Test validation of max_holdings parameter."""
        # Test valid range
        valid_input = EnhancedETFAnalysisInput(ticker="SPY", max_holdings=25)
        assert valid_input.max_holdings == 25

        # Test invalid range should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            EnhancedETFAnalysisInput(ticker="SPY", max_holdings=0)

        with pytest.raises(Exception):  # Pydantic validation error
            EnhancedETFAnalysisInput(ticker="SPY", max_holdings=100)


class TestEnhancedETFAnalysisTool:
    """Test the Enhanced ETF Analysis Tool functionality."""

    @pytest.fixture
    def tool(self):
        """Create an instance of the Enhanced ETF Analysis Tool."""
        return EnhancedETFAnalysisTool()

    @pytest.fixture
    def mock_yahoo_html(self):
        """Mock Yahoo Finance HTML content for ETF page."""
        return """
        <html>
        <body>
        <h1>SPDR S&P 500 ETF Trust (SPY)</h1>
        <div>Expense Ratio: 0.09%</div>
        <div>Total Assets: $400B</div>
        <div>Inception Date: 1993</div>
        <table>
        <tr><th>Symbol</th><th>Weight</th></tr>
        <tr><td>AAPL</td><td>7.2%</td></tr>
        <tr><td>MSFT</td><td>6.8%</td></tr>
        <tr><td>NVDA</td><td>6.1%</td></tr>
        </table>
        </body>
        </html>
        """

    def test_should_normalize_ticker_input(self, tool, mocker):
        """Test ticker normalization."""
        # Arrange — mock the network boundaries so no real HTTP calls are made
        mock_factsheet = mocker.patch.object(tool, "_extract_factsheet_data")
        mock_factsheet.return_value = {
            "issuer": "SPDR",
            "expense_ratio": 0.09,
            "factsheet_url": "https://test.com",
            "as_of": "2024-01-01",
            "factsheet_highlights": [],
        }
        mocker.patch.object(tool, "_get_perplexity_integration", return_value=None)

        # Act
        result = tool._run(ticker="  spy  ", include_holdings=False, include_risk_assessment=False)

        # Assert
        assert result["ticker"] == "SPY"

    def test_should_extract_issuer_from_ticker_patterns(self, tool):
        """Test issuer extraction from common ticker patterns."""
        # Arrange
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")

        # Act & Assert
        assert ETFDataFetcher.extract_issuer(soup, "SPY") == "SPDR"
        assert ETFDataFetcher.extract_issuer(soup, "VTI") == "Vanguard"
        assert ETFDataFetcher.extract_issuer(soup, "QQQ") == "Invesco"
        assert ETFDataFetcher.extract_issuer(soup, "IWM") == "iShares"
        assert ETFDataFetcher.extract_issuer(soup, "UNKNOWN") == "Unknown"

    def test_should_extract_expense_ratio_from_html(self, tool, mock_yahoo_html):
        """Test expense ratio extraction from HTML content."""
        # Arrange
        soup = BeautifulSoup(mock_yahoo_html, "html.parser")

        # Act
        expense_ratio = ETFDataFetcher.extract_expense_ratio(soup)

        # Assert
        assert expense_ratio == approx(0.09)

    def test_should_handle_expense_ratio_edge_cases(self, tool):
        """Test expense ratio extraction edge cases."""
        # Test basis points conversion
        html_bp = "<div>Total Expense: 95 basis points</div>"
        soup_bp = BeautifulSoup(html_bp, "html.parser")
        assert ETFDataFetcher.extract_expense_ratio(soup_bp) == approx(0.95)

        # Test fallback default
        html_empty = "<div>No expense info</div>"
        soup_empty = BeautifulSoup(html_empty, "html.parser")
        assert ETFDataFetcher.extract_expense_ratio(soup_empty) == approx(0.20)

    def test_should_extract_tracking_difference(self, tool):
        """Test tracking difference extraction."""
        # Test positive tracking difference
        html_pos = "<div>Tracking Error: 0.15%</div>"
        soup_pos = BeautifulSoup(html_pos, "html.parser")
        result_pos = ETFDataFetcher.extract_tracking_difference(soup_pos)
        assert result_pos == approx(0.15)

        # Test negative tracking difference
        html_neg = "<div>Tracking Difference: -0.05%</div>"
        soup_neg = BeautifulSoup(html_neg, "html.parser")
        result_neg = ETFDataFetcher.extract_tracking_difference(soup_neg)
        assert result_neg == approx(-0.05)

        # Test no tracking info
        html_none = "<div>No tracking info</div>"
        soup_none = BeautifulSoup(html_none, "html.parser")
        result_none = ETFDataFetcher.extract_tracking_difference(soup_none)
        assert result_none is None

    def test_should_determine_replication_method(self, tool):
        """Test replication method determination."""
        # Test physical replication
        html_physical = "<div>Full replication strategy</div>"
        soup_physical = BeautifulSoup(html_physical, "html.parser")
        assert ETFDataFetcher.determine_replication_method(soup_physical) == "physical"

        # Test synthetic replication
        html_synthetic = "<div>Uses swap-based synthetic replication</div>"
        soup_synthetic = BeautifulSoup(html_synthetic, "html.parser")
        assert ETFDataFetcher.determine_replication_method(soup_synthetic) == "synthetic"

        # Test optimized replication
        html_optimized = "<div>Optimized sampling approach</div>"
        soup_optimized = BeautifulSoup(html_optimized, "html.parser")
        assert ETFDataFetcher.determine_replication_method(soup_optimized) == "optimized"

        # Test unknown method
        html_unknown = "<div>No replication info</div>"
        soup_unknown = BeautifulSoup(html_unknown, "html.parser")
        assert ETFDataFetcher.determine_replication_method(soup_unknown) == "other"

    def test_should_extract_highlights_from_html(self, tool, mock_yahoo_html):
        """Test highlights extraction from HTML."""
        # Arrange
        soup = BeautifulSoup(mock_yahoo_html, "html.parser")

        # Act
        highlights = ETFDataFetcher.extract_highlights(soup)

        # Assert
        assert isinstance(highlights, list)
        assert len(highlights) > 0
        assert len(highlights) <= 20

    def test_should_create_sample_holdings_for_common_etfs(self, tool):
        """Test sample holdings creation for common ETFs."""
        # Test SPY holdings
        spy_holdings = ETFDataFetcher.create_sample_holdings("SPY", "https://test.com")
        assert len(spy_holdings) > 0
        assert any(h["ticker"] == "AAPL" for h in spy_holdings)
        assert all("weight_pct" in h for h in spy_holdings)
        assert all("source_url" in h for h in spy_holdings)
        assert all("as_of" in h for h in spy_holdings)

        # Test QQQ holdings
        qqq_holdings = ETFDataFetcher.create_sample_holdings("QQQ", "https://test.com")
        assert len(qqq_holdings) > 0
        assert any(h["ticker"] == "AAPL" for h in qqq_holdings)

        # Test unknown ETF
        unknown_holdings = ETFDataFetcher.create_sample_holdings("UNKNOWN", "https://test.com")
        assert len(unknown_holdings) > 0
        assert all(h["ticker"].startswith("SAMPLE") for h in unknown_holdings)

    def test_should_extract_top_holdings_from_yahoo(self, tool, mock_yahoo_html, mocker):
        """Test top holdings extraction from Yahoo Finance."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.content = mock_yahoo_html.encode()
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch("requests.get", return_value=mock_response)

        # Act
        holdings = tool._extract_top_holdings("SPY", max_holdings=5)

        # Assert
        assert len(holdings) > 0
        assert len(holdings) <= 5
        for holding in holdings:
            assert "ticker" in holding
            assert "weight_pct" in holding
            assert "source_url" in holding
            assert "as_of" in holding

    def test_should_get_top_holdings_from_central_successfully(self, tool, mocker):
        """Central's top_holdings payload (symbol/name/weight) is remapped onto
        the ticker/weight_pct/source_url/as_of shape ETFAnalyzer consumes."""
        # Arrange
        mock_central_run = mocker.patch(
            _CENTRAL_RUN_PATH,
            return_value=ok(
                {
                    "ticker": "SPY",
                    "name": "SPDR S&P 500 ETF Trust",
                    "category": "Large Blend",
                    "expense_ratio": 0.0945,
                    "aum": 400000000000,
                    "top_holdings": [
                        {"symbol": "AAPL", "name": "Apple Inc", "weight": 7.2},
                        {"symbol": "MSFT", "name": "Microsoft Corp", "weight": 6.8},
                    ],
                    "sector_weightings": {"Technology": 30.1},
                    "concentration": {"top_n_weight_pct": 14.0, "hhi": 100.0, "risk_level": "low"},
                }
            ),
        )

        # Act
        holdings = tool._extract_top_holdings("SPY", max_holdings=5)

        # Assert
        assert len(holdings) == 2
        assert holdings[0]["ticker"] == "AAPL"
        assert holdings[0]["weight_pct"] == approx(7.2)
        assert holdings[0]["source_url"].endswith("/quote/SPY/holdings")
        assert holdings[0]["as_of"] == date.today()
        assert holdings[1]["ticker"] == "MSFT"
        assert holdings[1]["weight_pct"] == approx(6.8)

        _, kwargs = mock_central_run.call_args
        assert kwargs["ticker"] == "SPY"
        assert kwargs["max_holdings"] == 5

    def test_should_fallback_to_scraping_when_central_reports_failure(self, tool, mocker):
        """A central envelope failure (bad ticker, no funds_data, network error)
        degrades to the legacy Yahoo Finance scraping path rather than surfacing
        a bare error, matching the tool's prior behavior."""
        # Arrange
        mocker.patch(_CENTRAL_RUN_PATH, return_value=err("No ETF data available for INVALID"))
        mock_fallback = mocker.patch.object(
            ETFDataFetcher, "extract_top_holdings", return_value=[{"ticker": "SAMPLE1", "weight_pct": 5.0, "source_url": "https://test.com", "as_of": date.today()}]
        )

        # Act
        holdings = tool._extract_top_holdings("INVALID", max_holdings=5)

        # Assert
        assert holdings == [{"ticker": "SAMPLE1", "weight_pct": 5.0, "source_url": "https://test.com", "as_of": date.today()}]
        mock_fallback.assert_called_once_with("INVALID", 5)

    def test_should_fallback_to_scraping_when_central_returns_no_holdings(self, tool, mocker):
        """A central success envelope with an empty top_holdings list (no
        funds_data for this ticker) still falls back to scraping."""
        # Arrange
        mocker.patch(_CENTRAL_RUN_PATH, return_value=ok({"ticker": "XYZ", "top_holdings": []}))
        mock_fallback = mocker.patch.object(ETFDataFetcher, "extract_top_holdings", return_value=[])

        # Act
        holdings = tool._extract_top_holdings("XYZ", max_holdings=5)

        # Assert
        assert holdings == []
        mock_fallback.assert_called_once_with("XYZ", 5)

    def test_should_default_weight_to_zero_when_central_weight_is_none(self, tool, mocker):
        """Regression: central always includes `weight` per holding, sometimes
        with an explicit None (non-numeric holding percent from funds_data).
        `.get(key, default)` alone would NOT catch this since the key is
        present — only the value is None. The mapping must degrade to 0.0
        instead of leaking None into weight_pct, which
        ETFAnalyzer.perform_etf_risk_assessment maxes over via `h.get("weight_pct", 0)`."""
        # Arrange
        mocker.patch(
            _CENTRAL_RUN_PATH,
            return_value=ok(
                {
                    "ticker": "SPY",
                    "top_holdings": [{"symbol": "AAPL", "name": "Apple Inc", "weight": None}],
                }
            ),
        )

        # Act
        holdings = tool._extract_top_holdings("SPY", max_holdings=5)

        # Assert — the concentration-scoring-killing case: weight_pct must be numeric, never None
        assert holdings[0]["weight_pct"] == 0.0
        assert holdings[0]["weight_pct"] > -1  # would raise TypeError if None

    def test_should_perform_etf_risk_assessment(self, tool):
        """Test ETF risk assessment functionality."""
        # Arrange
        factsheet_data = {
            "expense_ratio": 1.5,  # High expense ratio
            "tracking_diff": 3.0,  # High tracking error
            "replication_method": "synthetic",  # Counterparty risk
        }

        holdings_data = [
            {"ticker": "AAPL", "weight_pct": 25.0},  # High concentration
            {"ticker": "MSFT", "weight_pct": 15.0},
        ]

        # Act
        risk_assessment = tool._perform_etf_risk_assessment("TEST", factsheet_data, holdings_data)

        # Assert
        assert risk_assessment["ticker"] == "TEST"
        assert risk_assessment["scale"] == "0_5"
        assert 0.0 <= risk_assessment["score"] <= 5.0
        assert risk_assessment["level"] in ["Low", "Medium", "High", "Very High"]
        assert len(risk_assessment["risk_factors"]) <= 10
        assert "High expense ratio" in risk_assessment["risk_factors"]
        assert "High concentration risk" in risk_assessment["risk_factors"]
        assert "High tracking error" in risk_assessment["risk_factors"]

    def test_should_map_risk_score_to_level_correctly(self, tool):
        """Test risk score to level mapping."""
        # Arrange & Act & Assert
        assert ETFAnalyzer.map_score_to_level(1.0) == "Low"
        assert ETFAnalyzer.map_score_to_level(2.0) == "Medium"
        assert ETFAnalyzer.map_score_to_level(3.5) == "High"
        assert ETFAnalyzer.map_score_to_level(4.5) == "Very High"

    def test_should_construct_etf_factsheet_successfully(self, tool):
        """Test ETF factsheet construction."""
        # Arrange
        factsheet_data = {
            "issuer": "Test Issuer",
            "expense_ratio": 0.15,
            "tracking_diff": 0.05,
            "replication_method": "physical",
            "factsheet_url": "https://test.com",
            "as_of": date.today(),
            "factsheet_highlights": ["Low cost", "Broad exposure"],
        }

        holdings_data = [{"ticker": "AAPL", "weight_pct": 7.2, "source_url": "https://test.com", "as_of": date.today()}]

        risk_assessment = {"scale": "0_5", "score": 2.0, "level": "Medium", "risk_factors": ["Market risk"]}

        # Act
        factsheet = tool._construct_etf_factsheet("TEST", factsheet_data, holdings_data, risk_assessment)

        # Assert
        assert factsheet["ticker"] == "TEST"
        assert factsheet["issuer"] == "Test Issuer"
        assert factsheet["expense_ratio"] == approx(0.15)
        assert factsheet["tracking_diff"] == approx(0.05)
        assert factsheet["replication_method"] == "physical"
        assert len(factsheet["top_holdings"]) == 1
        assert factsheet["risk"]["level"] == "Medium"

    def test_should_handle_network_errors_gracefully(self, tool, mocker):
        """Test graceful handling of network errors."""
        # Arrange
        mocker.patch("requests.get", side_effect=Exception("Network error"))

        # Act
        result = tool._run(ticker="SPY")

        # Assert
        assert "error" in result
        assert "Could not extract factsheet data" in result["error"]

    def test_should_handle_factsheet_extraction_errors(self, mocker, tool):
        """Test handling of factsheet extraction errors."""
        # Arrange
        mock_extract = mocker.patch.object(EnhancedETFAnalysisTool, "_extract_factsheet_data")
        mock_extract.return_value = {"error": "Extraction failed"}

        # Act
        result = tool._run(ticker="SPY")

        # Assert
        assert "error" in result
        assert "Extraction failed" in result["error"]


class TestIntegrationScenarios:
    """Test integration scenarios for enhanced ETF analysis."""

    @pytest.fixture
    def tool(self):
        """Create tool instance for integration tests."""
        return EnhancedETFAnalysisTool()

    def test_should_handle_complete_analysis_workflow(self, tool, mocker):
        """Test complete ETF analysis workflow."""
        # Arrange
        mock_factsheet = mocker.patch.object(EnhancedETFAnalysisTool, "_extract_factsheet_data")
        mock_holdings = mocker.patch.object(EnhancedETFAnalysisTool, "_extract_top_holdings")

        mock_factsheet.return_value = {
            "issuer": "Test Issuer",
            "expense_ratio": 0.10,
            "tracking_diff": 0.02,
            "replication_method": "physical",
            "factsheet_url": "https://test.com",
            "as_of": date.today(),
            "factsheet_highlights": ["Low cost ETF"],
            "sources": ["Yahoo Finance"],
        }

        mock_holdings.return_value = [
            {"ticker": "AAPL", "weight_pct": 7.2, "source_url": "https://test.com", "as_of": date.today()},
            {"ticker": "MSFT", "weight_pct": 6.8, "source_url": "https://test.com", "as_of": date.today()},
        ]
        mocker.patch.object(tool, "_get_perplexity_integration", return_value=None)

        # Act
        result = tool._run(ticker="SPY", include_holdings=True, include_risk_assessment=True, max_holdings=10)

        # Assert
        assert "error" not in result
        assert result["ticker"] == "SPY"
        assert "factsheet" in result
        assert result["holdings_count"] == 2
        assert "risk_assessment" in result
        assert "analysis_timestamp" in result

    def test_should_handle_holdings_disabled(self, tool, mocker):
        """Test behavior when holdings extraction is disabled."""
        # Arrange & Act
        mock_factsheet = mocker.patch.object(tool, "_extract_factsheet_data")
        mock_factsheet.return_value = {
            "issuer": "Test",
            "expense_ratio": 0.10,
            "factsheet_url": "https://test.com",
            "as_of": date.today(),
            "factsheet_highlights": [],
        }
        mocker.patch.object(tool, "_get_perplexity_integration", return_value=None)

        result = tool._run(ticker="SPY", include_holdings=False)

        # Assert
        assert "error" not in result
        assert result["holdings_count"] == 0

    def test_should_handle_risk_assessment_disabled(self, tool, mocker):
        """Test behavior when risk assessment is disabled."""
        # Arrange — mock both network boundaries
        mock_factsheet = mocker.patch.object(tool, "_extract_factsheet_data")
        mock_factsheet.return_value = {
            "issuer": "Test",
            "expense_ratio": 0.10,
            "factsheet_url": "https://test.com",
            "as_of": date.today(),
            "factsheet_highlights": [],
        }
        mocker.patch.object(tool, "_extract_top_holdings", return_value=[])
        mocker.patch.object(tool, "_get_perplexity_integration", return_value=None)

        result = tool._run(ticker="SPY", include_risk_assessment=False)

        # Assert
        assert "error" not in result
        assert result["risk_assessment"] is None
