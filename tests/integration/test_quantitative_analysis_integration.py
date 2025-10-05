"""
Integration tests for quantitative analysis workflow in FinWiz crews.

This module tests the integration of quantitative analysis capabilities
into Stock, ETF, and Crypto crews, ensuring proper data flow and
validation of quantitative metrics.
"""

import json
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from finwiz.schemas.quantitative import (
    EnhancedCryptoAnalysis,
    EnhancedETFAnalysis,
    EnhancedStockAnalysis,
    QuantitativeBacktestResult,
    QuantitativePerformanceMetrics,
    QuantitativeTechnicalAnalysis,
)
from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool


class TestQuantitativeAnalysisIntegration:
    """Test quantitative analysis integration with crews."""

    @pytest.fixture
    def mock_historical_data(self):
        """Create mock historical data for testing."""
        dates = pd.date_range(start="2023-01-01", end="2024-01-01", freq="D")
        np.random.seed(42)  # For reproducible tests

        # Generate realistic OHLCV data
        base_price = 100
        returns = np.random.normal(0.001, 0.02, len(dates))  # Daily returns
        prices = base_price * np.exp(np.cumsum(returns))

        data = pd.DataFrame(
            {
                "Open": prices * (1 + np.random.normal(0, 0.005, len(dates))),
                "High": prices * (1 + np.abs(np.random.normal(0, 0.01, len(dates)))),
                "Low": prices * (1 - np.abs(np.random.normal(0, 0.01, len(dates)))),
                "Close": prices,
                "Volume": np.random.randint(1000000, 10000000, len(dates)),
            },
            index=dates,
        )

        # Ensure High >= Close >= Low and High >= Open >= Low
        data["High"] = np.maximum(data["High"], np.maximum(data["Open"], data["Close"]))
        data["Low"] = np.minimum(data["Low"], np.minimum(data["Open"], data["Close"]))

        return data

    @pytest.fixture
    def quantitative_tool(self):
        """Create quantitative analysis tool instance."""
        return QuantitativeAnalysisTool()

    def test_stock_quantitative_analysis_comprehensive(self, quantitative_tool, mock_historical_data, mocker):
        """Test comprehensive quantitative analysis for stocks."""
        with mocker.patch.object(quantitative_tool.data_manager, "fetch_historical_data", return_value=mock_historical_data):
            result_json = quantitative_tool._run(symbol="AAPL", asset_class="stock", analysis_type="comprehensive", timeframe="1y")

            # Parse result
            result_dict = json.loads(result_json)
            stock_analysis = EnhancedStockAnalysis(**result_dict)

            # Validate structure
            assert stock_analysis.ticker == "AAPL"
            assert stock_analysis.quantitative_enabled is True
            assert stock_analysis.technical_analysis is not None
            assert stock_analysis.backtest_result is not None
            assert stock_analysis.performance_metrics is not None
            assert stock_analysis.quantitative_recommendation is not None

            # Validate technical analysis
            tech_analysis = stock_analysis.technical_analysis
            assert tech_analysis.symbol == "AAPL"
            assert tech_analysis.overall_signal in ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"]
            assert 0 <= tech_analysis.overall_confidence <= 1
            assert tech_analysis.bullish_signals_count >= 0
            assert tech_analysis.bearish_signals_count >= 0

            # Validate backtest results
            backtest = stock_analysis.backtest_result
            assert backtest.symbol == "AAPL"
            assert backtest.strategy_name == "SimpleMovingAverageStrategy"
            assert backtest.total_trades >= 0
            assert 0 <= backtest.win_rate <= 1
            assert backtest.initial_capital > 0
            assert backtest.final_value > 0

            # Validate performance metrics
            perf = stock_analysis.performance_metrics
            assert perf.symbol == "AAPL"
            assert isinstance(perf.total_return, float)
            assert isinstance(perf.sharpe_ratio, float)
            assert isinstance(perf.max_drawdown, float)
            assert perf.total_days > 0

            # Validate recommendation
            rec = stock_analysis.quantitative_recommendation
            assert rec.symbol == "AAPL"
            assert rec.recommendation in ["BUY", "SELL", "HOLD"]
            assert 0 <= rec.confidence <= 1
            assert rec.methodology == "quantitative_analysis"

    def test_etf_quantitative_analysis_comprehensive(self, quantitative_tool, mock_historical_data, mocker):
        """Test comprehensive quantitative analysis for ETFs."""
        with mocker.patch.object(quantitative_tool.data_manager, "fetch_historical_data", return_value=mock_historical_data):
            result_json = quantitative_tool._run(symbol="SPY", asset_class="etf", analysis_type="comprehensive", timeframe="2y")

            # Parse result
            result_dict = json.loads(result_json)
            etf_analysis = EnhancedETFAnalysis(**result_dict)

            # Validate structure
            assert etf_analysis.ticker == "SPY"
            assert etf_analysis.quantitative_enabled is True
            assert etf_analysis.technical_analysis is not None
            assert etf_analysis.backtest_result is not None
            assert etf_analysis.performance_metrics is not None
            assert etf_analysis.quantitative_recommendation is not None

            # Validate ETF-specific fields
            assert etf_analysis.tracking_error_analysis is None  # Not implemented in basic version
            assert etf_analysis.benchmark_correlation is None  # Not implemented in basic version

    def test_crypto_quantitative_analysis_comprehensive(self, quantitative_tool, mock_historical_data, mocker):
        """Test comprehensive quantitative analysis for cryptocurrencies."""
        with mocker.patch.object(quantitative_tool.data_manager, "fetch_historical_data", return_value=mock_historical_data):
            result_json = quantitative_tool._run(
                symbol="BTC-USD", asset_class="crypto", analysis_type="comprehensive", timeframe="1y"
            )

            # Parse result
            result_dict = json.loads(result_json)
            crypto_analysis = EnhancedCryptoAnalysis(**result_dict)

            # Validate structure
            assert crypto_analysis.symbol == "BTC-USD"
            assert crypto_analysis.quantitative_enabled is True
            assert crypto_analysis.technical_analysis is not None
            assert crypto_analysis.backtest_result is not None
            assert crypto_analysis.performance_metrics is not None
            assert crypto_analysis.quantitative_recommendation is not None

            # Validate crypto-specific fields
            assert crypto_analysis.volatility_analysis is None  # Not implemented in basic version
            assert crypto_analysis.correlation_analysis is None  # Not implemented in basic version

    def test_technical_analysis_only(self, mocker, quantitative_tool, mock_historical_data):
        """Test technical analysis only mode."""
        with mocker.patch("finwiz.tools.quantitative_analysis_tool.get_historical_data_manager") as mock_data_manager_factory:
            mock_data_manager = mocker.Mock()
            mock_data_manager.fetch_historical_data.return_value = mock_historical_data
            mock_data_manager_factory.return_value = mock_data_manager

            result_json = quantitative_tool._run(symbol="MSFT", asset_class="stock", analysis_type="technical", timeframe="1y")

            # Parse result
            result_dict = json.loads(result_json)
            tech_analysis = QuantitativeTechnicalAnalysis(**result_dict)

            # Validate technical analysis
            assert tech_analysis.symbol == "MSFT"
            assert tech_analysis.overall_signal in ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"]
            assert 0 <= tech_analysis.overall_confidence <= 1
            assert tech_analysis.bullish_signals_count >= 0
            assert tech_analysis.bearish_signals_count >= 0
            assert tech_analysis.neutral_signals_count >= 0

    def test_backtest_analysis_only(self, quantitative_tool, mock_historical_data, mocker):
        """Test backtesting analysis only mode."""
        with mocker.patch.object(quantitative_tool.data_manager, "fetch_historical_data", return_value=mock_historical_data):
            result_json = quantitative_tool._run(symbol="GOOGL", asset_class="stock", analysis_type="backtest", timeframe="1y")

            # Parse result
            result_dict = json.loads(result_json)
            backtest_result = QuantitativeBacktestResult(**result_dict)

            # Validate backtest results
            assert backtest_result.symbol == "GOOGL"
            assert backtest_result.strategy_name == "SimpleMovingAverageStrategy"
            assert backtest_result.total_trades >= 0
            assert 0 <= backtest_result.win_rate <= 1
            assert backtest_result.initial_capital > 0
            assert backtest_result.final_value > 0
            assert isinstance(backtest_result.backtest_start_date, datetime)
            assert isinstance(backtest_result.backtest_end_date, datetime)

    def test_performance_analysis_only(self, quantitative_tool, mock_historical_data, mocker):
        """Test performance analysis only mode."""
        with mocker.patch.object(quantitative_tool.data_manager, "fetch_historical_data", return_value=mock_historical_data):
            result_json = quantitative_tool._run(symbol="TSLA", asset_class="stock", analysis_type="performance", timeframe="1y")

            # Parse result
            result_dict = json.loads(result_json)
            perf_metrics = QuantitativePerformanceMetrics(**result_dict)

            # Validate performance metrics
            assert perf_metrics.symbol == "TSLA"
            assert isinstance(perf_metrics.total_return, float)
            assert isinstance(perf_metrics.annualized_return, float)
            assert isinstance(perf_metrics.sharpe_ratio, float)
            assert isinstance(perf_metrics.sortino_ratio, float)
            assert isinstance(perf_metrics.max_drawdown, float)
            assert isinstance(perf_metrics.volatility, float)
            assert perf_metrics.total_days > 0

    def test_error_handling_no_data(self, quantitative_tool, mocker):
        """Test error handling when no data is available."""
        empty_data = pd.DataFrame()

        with mocker.patch.object(quantitative_tool.data_manager, "fetch_historical_data", return_value=empty_data):
            result = quantitative_tool._run(symbol="INVALID", asset_class="stock", analysis_type="comprehensive", timeframe="1y")

            assert "No data available" in result

    def test_error_handling_invalid_symbol(self, quantitative_tool, mocker):
        """Test error handling for invalid symbols."""
        with mocker.patch.object(
            quantitative_tool.data_manager, "fetch_historical_data", side_effect=Exception("Symbol not found")
        ):
            result = quantitative_tool._run(symbol="INVALID123", asset_class="stock", analysis_type="comprehensive", timeframe="1y")

            assert "Error fetching data" in result

    def test_different_timeframes(self, quantitative_tool, mock_historical_data, mocker):
        """Test analysis with different timeframes."""
        timeframes = ["1y", "2y", "5y"]

        for timeframe in timeframes:
            with mocker.patch.object(quantitative_tool.data_manager, "fetch_historical_data", return_value=mock_historical_data):
                result_json = quantitative_tool._run(
                    symbol="AAPL", asset_class="stock", analysis_type="technical", timeframe=timeframe
                )

                # Should not raise an exception
                result_dict = json.loads(result_json)
                tech_analysis = QuantitativeTechnicalAnalysis(**result_dict)
                assert tech_analysis.symbol == "AAPL"

    def test_recommendation_generation_logic(self, mocker, quantitative_tool, mock_historical_data):
        """Test recommendation generation logic with different scenarios."""
        # Mock technical analysis result with strong buy signal
        mock_tech_result = mocker.Mock()
        mock_tech_result.overall_signal.value = "STRONG_BUY"
        mock_tech_result.overall_confidence = 0.8
        mock_tech_result.bullish_signals_count = 5
        mock_tech_result.bearish_signals_count = 1

        # Mock backtest result with good performance
        mock_backtest_result = mocker.Mock()
        mock_backtest_result.annualized_return = 15.0
        mock_backtest_result.sharpe_ratio = 1.5
        mock_backtest_result.max_drawdown = -10.0
        mock_backtest_result.volatility = 20.0
        mock_backtest_result.var_95 = -2.5

        # Mock performance metrics
        mock_perf_metrics = mocker.Mock()

        # Test recommendation generation
        recommendation = quantitative_tool._generate_recommendation(
            "AAPL", mock_tech_result, mock_backtest_result, mock_perf_metrics
        )

        assert recommendation.symbol == "AAPL"
        assert recommendation.recommendation == "BUY"
        assert recommendation.confidence > 0.8
        assert "STRONG_BUY" in recommendation.technical_signal
        assert recommendation.target_return == 15.0

    def test_schema_validation_comprehensive(self, quantitative_tool, mock_historical_data, mocker):
        """Test comprehensive schema validation for all analysis types."""
        with mocker.patch.object(quantitative_tool.data_manager, "fetch_historical_data", return_value=mock_historical_data):
            # Test all asset classes with comprehensive analysis
            asset_classes = [
                ("AAPL", "stock", EnhancedStockAnalysis),
                ("SPY", "etf", EnhancedETFAnalysis),
                ("BTC-USD", "crypto", EnhancedCryptoAnalysis),
            ]

            for symbol, asset_class, expected_schema in asset_classes:
                result_json = quantitative_tool._run(
                    symbol=symbol, asset_class=asset_class, analysis_type="comprehensive", timeframe="1y"
                )

                # Parse and validate schema
                result_dict = json.loads(result_json)
                analysis = expected_schema(**result_dict)

                # Common validations
                assert analysis.quantitative_enabled is True
                assert analysis.technical_analysis is not None
                assert analysis.backtest_result is not None
                assert analysis.performance_metrics is not None
                assert analysis.quantitative_recommendation is not None
                assert isinstance(analysis.analysis_timestamp, datetime)

    @pytest.mark.integration
    def test_crew_integration_workflow(self, quantitative_tool, mock_historical_data, mocker):
        """Test the complete workflow as it would be used by crews."""
        # Simulate crew workflow: screening -> technical analysis -> risk assessment
        symbols = ["AAPL", "MSFT", "GOOGL"]

        with mocker.patch.object(quantitative_tool.data_manager, "fetch_historical_data", return_value=mock_historical_data):
            results = []

            for symbol in symbols:
                # Step 1: Technical analysis (as used in screening)
                tech_result = quantitative_tool._run(symbol=symbol, asset_class="stock", analysis_type="technical", timeframe="1y")

                # Step 2: Comprehensive analysis (as used in detailed analysis)
                comp_result = quantitative_tool._run(
                    symbol=symbol, asset_class="stock", analysis_type="comprehensive", timeframe="1y"
                )

                # Step 3: Performance analysis (as used in risk assessment)
                perf_result = quantitative_tool._run(
                    symbol=symbol, asset_class="stock", analysis_type="performance", timeframe="1y"
                )

                results.append(
                    {
                        "symbol": symbol,
                        "technical": json.loads(tech_result),
                        "comprehensive": json.loads(comp_result),
                        "performance": json.loads(perf_result),
                    }
                )

            # Validate all results
            assert len(results) == 3

            for result in results:
                # Validate technical analysis
                tech = QuantitativeTechnicalAnalysis(**result["technical"])
                assert tech.symbol == result["symbol"]

                # Validate comprehensive analysis
                comp = EnhancedStockAnalysis(**result["comprehensive"])
                assert comp.ticker == result["symbol"]

                # Validate performance analysis
                perf = QuantitativePerformanceMetrics(**result["performance"])
                assert perf.symbol == result["symbol"]

    def test_quantitative_metrics_consistency(self, quantitative_tool, mock_historical_data, mocker):
        """Test consistency of quantitative metrics across different analysis types."""
        with mocker.patch.object(quantitative_tool.data_manager, "fetch_historical_data", return_value=mock_historical_data):
            # Get comprehensive analysis
            comp_result_json = quantitative_tool._run(
                symbol="AAPL", asset_class="stock", analysis_type="comprehensive", timeframe="1y"
            )

            # Get individual analyses
            tech_result_json = quantitative_tool._run(symbol="AAPL", asset_class="stock", analysis_type="technical", timeframe="1y")

            perf_result_json = quantitative_tool._run(
                symbol="AAPL", asset_class="stock", analysis_type="performance", timeframe="1y"
            )

            # Parse results
            comp_result = json.loads(comp_result_json)
            tech_result = json.loads(tech_result_json)
            perf_result = json.loads(perf_result_json)

            # Check consistency of technical analysis
            comp_tech = comp_result["technical_analysis"]
            assert comp_tech["symbol"] == tech_result["symbol"]
            assert comp_tech["overall_signal"] == tech_result["overall_signal"]
            assert comp_tech["overall_confidence"] == tech_result["overall_confidence"]

            # Check consistency of performance metrics
            comp_perf = comp_result["performance_metrics"]
            assert comp_perf["symbol"] == perf_result["symbol"]
            assert comp_perf["total_return"] == perf_result["total_return"]
            assert comp_perf["sharpe_ratio"] == perf_result["sharpe_ratio"]
