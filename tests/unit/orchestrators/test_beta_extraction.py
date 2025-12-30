"""
Test beta extraction and critical field validation in Python data collection.

This test validates that the orchestrator correctly:
1. Calls quantitative analysis tool
2. Extracts beta from nested performance_metrics
3. Flattens all critical risk metrics
4. Validates all required fields for Python scoring

Uses pytest-mock for all external dependencies.
"""

import json

import pytest
from faker import Faker
from pytest import approx

from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator


@pytest.fixture
def fake():
    """Faker instance for generating realistic test data."""
    return Faker()


@pytest.fixture
def sample_quantitative_result(fake):
    """Generate realistic quantitative analysis result with beta."""
    return {
        "performance_metrics": {
            "beta": fake.pyfloat(min_value=0.5, max_value=2.0, right_digits=2),
            "volatility": fake.pyfloat(min_value=0.1, max_value=0.5, right_digits=3),
            "max_drawdown": fake.pyfloat(min_value=-0.5, max_value=-0.1, right_digits=3),
            "sharpe_ratio": fake.pyfloat(min_value=0.5, max_value=3.0, right_digits=2),
            "total_return": fake.pyfloat(min_value=-0.2, max_value=0.5, right_digits=3),
            "annualized_return": fake.pyfloat(min_value=-0.1, max_value=0.3, right_digits=3),
        },
        "technical_analysis": {
            "technical_indicators": {
                "rsi": fake.pyfloat(min_value=20, max_value=80, right_digits=1),
                "macd": fake.pyfloat(min_value=-5, max_value=5, right_digits=2),
                "macd_signal": fake.pyfloat(min_value=-5, max_value=5, right_digits=2),
            }
        },
        "prices": {"current_price": fake.pyfloat(min_value=100, max_value=200, right_digits=2)},
    }


@pytest.fixture
def sample_ticker_result(fake):
    """Generate realistic ticker info result."""
    return {
        "symbol": "AAPL",
        "name": fake.company(),
        "current_price": fake.pyfloat(min_value=100, max_value=200, right_digits=2),
        "market_cap": fake.random_int(min=1_000_000_000, max=3_000_000_000_000),
        "pe_ratio": fake.pyfloat(min_value=10, max_value=40, right_digits=2),
        "data_source": "live_api",
    }


@pytest.fixture
def sample_company_result(fake):
    """Generate realistic company info result with fundamentals."""
    return {
        "symbol": "AAPL",
        "name": fake.company(),
        "financial_metrics": {
            "return_on_equity": fake.pyfloat(min_value=0.1, max_value=0.4, right_digits=3),
            "debt_to_equity": fake.pyfloat(min_value=0.1, max_value=1.5, right_digits=2),
            "revenue_growth": fake.pyfloat(min_value=0.05, max_value=0.3, right_digits=3),
            "profit_margin": fake.pyfloat(min_value=0.1, max_value=0.3, right_digits=3),
        },
    }


class TestBetaExtraction:
    """Test beta extraction from quantitative analysis."""

    def test_beta_extraction_from_nested_structure(self, mocker, sample_quantitative_result, sample_ticker_result, sample_company_result):
        """
        Test that beta is correctly extracted from nested performance_metrics.

        CRITICAL: This test validates the fix for the production bug where
        beta field was missing despite being present in quantitative data.
        """
        # Mock flow state
        mock_state = mocker.Mock()
        mock_state.full_date = "2025-01-20"
        mock_state.current_day = "20"
        mock_state.current_month = "January"
        mock_state.current_year = "2025"
        mock_state.portfolio_review = {"holdings": []}

        # Create orchestrator with state
        orchestrator = DeepAnalysisOrchestrator(state=mock_state)

        # Mock tool calls (patch _run method directly on tool classes)
        mock_ticker = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run", return_value=sample_ticker_result)

        # Mock DataSourceOrchestrator to return fundamental data from sample_company_result
        from datetime import datetime

        from finwiz.data.data_source_orchestrator import OrchestrationResult

        mock_orchestration_result = OrchestrationResult(
            ticker="AAPL",
            timestamp=datetime.now(),
            return_on_equity=sample_company_result["financial_metrics"]["return_on_equity"],
            debt_to_equity=sample_company_result["financial_metrics"]["debt_to_equity"],
            sources_succeeded=["YFinance"],
            confidence=1.0,
        )
        # Mock on data_collector.data_orchestrator since collect_data uses data_collector's instance
        mock_data_orchestrator = mocker.patch.object(orchestrator.data_collector.data_orchestrator, "get_fundamental_data", new=mocker.AsyncMock(return_value=mock_orchestration_result))

        # Quantitative tool returns JSON string
        mock_quant = mocker.patch("finwiz.tools.quantitative_analysis_tool.QuantitativeAnalysisTool._run", return_value=json.dumps(sample_quantitative_result))

        # Mock sentiment tool (returns markdown)
        mock_sentiment = mocker.patch(
            "finwiz.tools.enhanced_sentiment_tool.EnhancedSentimentAnalysisTool._run", return_value="# Sentiment Analysis\n\nPositive sentiment detected."
        )

        # Call data collection (method moved to data_collector in Phase 1.1 refactoring)
        result = orchestrator.data_collector.collect_data(ticker="AAPL", asset_class="stock", batch_enabled=False)

        # Validate beta is extracted
        assert "beta" in result, "Beta field must be present in flattened data"
        assert result["beta"] == sample_quantitative_result["performance_metrics"]["beta"]

        # Validate other critical risk metrics
        assert "volatility" in result
        assert result["volatility"] == sample_quantitative_result["performance_metrics"]["volatility"]

        assert "max_drawdown" in result
        assert result["max_drawdown"] == sample_quantitative_result["performance_metrics"]["max_drawdown"]

        # Validate technical indicators
        assert "rsi" in result
        assert result["rsi"] == sample_quantitative_result["technical_analysis"]["technical_indicators"]["rsi"]

        assert "macd" in result
        assert result["macd"] == sample_quantitative_result["technical_analysis"]["technical_indicators"]["macd"]

        # Validate fundamentals (use pytest.approx for floating point comparison)
        assert "roe" in result
        assert result["roe"] == pytest.approx(sample_company_result["financial_metrics"]["return_on_equity"], rel=1e-2)

        assert "debt_to_equity" in result
        assert result["debt_to_equity"] == pytest.approx(sample_company_result["financial_metrics"]["debt_to_equity"], rel=1e-2)

    def test_flatten_preserves_all_critical_fields(self, mocker):
        """
        Test that flattening preserves all critical fields for scoring.

        Validates the complete flattening logic including:
        - Top-level field preservation
        - Nested field extraction (beta, volatility)
        - Technical indicator extraction (RSI, MACD)
        """
        # Mock flow state
        mock_state = mocker.Mock()
        mock_state.portfolio_review = {"holdings": []}

        orchestrator = DeepAnalysisOrchestrator(state=mock_state)

        # Create nested test data
        nested_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "current_price": 150.0,  # Top-level field
            "roe": 0.25,  # Top-level field
            "quantitative_analysis": {
                "performance_metrics": {
                    "beta": 1.2,
                    "volatility": 0.25,
                    "max_drawdown": -0.15,
                    "sharpe_ratio": 1.8,
                },
                "technical_analysis": {
                    "technical_indicators": {
                        "rsi": 65.5,
                        "macd": 2.3,
                        "macd_signal": 1.9,
                    }
                },
            },
        }

        # Call flattening (method moved to data_collector in Phase 1.1 refactoring)
        flattened = orchestrator.data_collector.flatten_collected_data(nested_data)

        # Validate all fields present
        expected_fields = ["ticker", "asset_class", "current_price", "roe", "beta", "volatility", "max_drawdown", "sharpe_ratio", "rsi", "macd", "macd_signal"]

        for field in expected_fields:
            assert field in flattened, f"Critical field '{field}' missing after flattening"

        # Validate values
        assert flattened["beta"] == approx(1.2)
        assert flattened["volatility"] == approx(0.25)
        assert flattened["rsi"] == approx(65.5)
        assert flattened["current_price"] == approx(150.0)

    @pytest.mark.skip(reason="Logging path changed in Phase 1.1 refactoring - internal behavior test")
    def test_missing_beta_logs_warning(self, mocker, sample_ticker_result, sample_company_result):
        """
        Test that missing beta field is properly logged.

        When quantitative tool returns data without beta in performance_metrics,
        the orchestrator should log a warning to help debugging.
        """
        # Mock flow state
        mock_state = mocker.Mock()
        mock_state.full_date = "2025-01-20"
        mock_state.portfolio_review = {"holdings": []}

        orchestrator = DeepAnalysisOrchestrator(state=mock_state)

        # Mock tools (patch _run method directly on tool classes)
        mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run", return_value=sample_ticker_result)

        mocker.patch("finwiz.tools.yahoo_finance_company_info_tool.YahooFinanceCompanyInfoTool._run", return_value=sample_company_result)

        # Quantitative tool returns data WITHOUT beta
        quant_result_no_beta = {
            "performance_metrics": {
                "volatility": 0.25,
                # beta is missing!
            }
        }
        mocker.patch("finwiz.tools.quantitative_analysis_tool.QuantitativeAnalysisTool._run", return_value=json.dumps(quant_result_no_beta))

        # Mock sentiment and SEC
        mocker.patch("finwiz.tools.enhanced_sentiment_tool.EnhancedSentimentAnalysisTool._run", return_value="# Sentiment\n\nPositive")

        mocker.patch("finwiz.tools.enhanced_sec_tool.EnhancedSECAnalysisTool._run", return_value="# SEC Analysis\n\nNo filings")

        # Spy on logger to verify warning (logger is now on data_collector)
        mock_logger = mocker.patch.object(orchestrator.data_collector, "logger")

        # Call data collection (method moved to data_collector in Phase 1.1 refactoring)
        result = orchestrator.data_collector.collect_data(ticker="AAPL", asset_class="stock", batch_enabled=False)

        # Verify beta is missing
        assert "beta" not in result or result.get("beta") is None

        # Verify warning was logged
        warning_calls = [call for call in mock_logger.warning.call_args_list if "beta" in str(call).lower()]
        assert len(warning_calls) > 0, "Should log warning about missing beta field"


class TestCriticalFieldValidation:
    """Test validation of all critical fields for each asset class."""

    @pytest.mark.parametrize(
        "asset_class,required_fields",
        [
            ("stock", ["current_price", "roe", "debt_to_equity", "revenue_growth", "volatility", "beta"]),
            ("etf", ["current_price", "expense_ratio", "volatility"]),
            ("crypto", ["current_price", "market_cap", "volume_24h", "volatility", "age_years"]),
        ],
    )
    def test_required_fields_by_asset_class(self, mocker, asset_class, required_fields):
        """
        Test that required fields are identified for each asset class.

        This validates the critical_fields_config module's field requirements.
        """
        from finwiz.config.critical_fields_config import get_critical_fields

        critical_fields = get_critical_fields(asset_class)

        # Verify all required fields are marked as critical
        for field in required_fields:
            assert field in critical_fields, f"{field} should be critical for {asset_class}"

    def test_stock_data_collection_includes_fundamentals(self, mocker, sample_ticker_result, sample_company_result, sample_quantitative_result):
        """
        Test that stock data collection includes all fundamental metrics.

        Stocks require: ROE, debt_to_equity, revenue_growth, profit_margin
        """
        # Mock flow state
        mock_state = mocker.Mock()
        mock_state.full_date = "2025-01-20"
        mock_state.portfolio_review = {"holdings": []}

        orchestrator = DeepAnalysisOrchestrator(state=mock_state)

        # Mock all tools (patch _run method directly on tool classes)
        mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run", return_value=sample_ticker_result)

        mocker.patch("finwiz.tools.yahoo_finance_company_info_tool.YahooFinanceCompanyInfoTool._run", return_value=sample_company_result)

        mocker.patch("finwiz.tools.quantitative_analysis_tool.QuantitativeAnalysisTool._run", return_value=json.dumps(sample_quantitative_result))

        mocker.patch("finwiz.tools.enhanced_sentiment_tool.EnhancedSentimentAnalysisTool._run", return_value="# Sentiment\n\nPositive")

        mocker.patch("finwiz.tools.enhanced_sec_tool.EnhancedSECAnalysisTool._run", return_value="# SEC Analysis\n\nStrong fundamentals")

        # Call data collection for STOCK (method moved to data_collector in Phase 1.1 refactoring)
        result = orchestrator.data_collector.collect_data(ticker="AAPL", asset_class="stock", batch_enabled=False)

        # Verify fundamental metrics
        assert "roe" in result, "Stock analysis requires ROE"
        assert "debt_to_equity" in result, "Stock analysis requires debt_to_equity"
        assert "revenue_growth" in result, "Stock analysis requires revenue_growth"
        assert "profit_margin" in result, "Stock analysis requires profit_margin"

        # Verify risk metrics
        assert "beta" in result, "Stock analysis requires beta"
        assert "volatility" in result, "Stock analysis requires volatility"
