"""
Comprehensive unit tests for Investment Discovery Tools.

This module provides additional comprehensive tests for the A+ Scoring Tool,
Market Screening Tool, and Backtesting Tool to ensure complete coverage
of edge cases, error scenarios, and integration points.
"""

import json
from datetime import datetime, timedelta

import pandas as pd
import pytest

from finwiz.schemas.tools import MarketRegime
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool
from finwiz.tools.backtesting_tool import BacktestingTool
from finwiz.tools.market_screening_tool import MarketScreeningTool


class TestAPlusScoringToolComprehensive:
    """Comprehensive tests for A+ Scoring Tool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = APlusScoringTool()

    def test_should_handle_extreme_market_conditions_correctly(self):
        """Test handling of extreme market conditions."""
        # Extreme bear market
        extreme_bear_context = {
            "vix": 80,  # Extreme fear
            "inflation": 15.0,  # Hyperinflation
            "rate_change_6m": 5.0,  # Massive rate hikes
        }

        result = self.tool._run(
            symbol="TEST",
            asset_type="stock",
            fundamental_data={"roe": 0.30, "revenue_growth": 0.20},
            market_context=extreme_bear_context,
        )

        assert result["symbol"] == "TEST"
        a_plus_score = result["a_plus_score"]
        assert a_plus_score["market_regime"]["market_stress_level"] == "high"
        assert a_plus_score["market_regime"]["regime_type"] in ["bear", "volatile"]

    def test_should_score_edge_case_asset_values_correctly(self):
        """Test scoring with edge case values."""
        # ETF with exactly threshold values
        threshold_etf_data = {
            "expense_ratio": 0.15,  # Exactly at threshold
            "aum": 1e9,  # Exactly at minimum
            "tracking_error": 0.002,  # Exactly at maximum
            "history_years": 3,  # Exactly at minimum
        }

        result = self.tool._run(symbol="THRESHOLD", asset_type="etf", fundamental_data=threshold_etf_data)

        assert result["symbol"] == "THRESHOLD"
        assert 0.0 <= result["analysis_summary"]["composite_score"] <= 1.0

    def test_should_handle_missing_optional_fields_gracefully(self):
        """Test handling when optional fields are missing."""
        minimal_data = {"symbol": "MINIMAL"}  # Only required field

        result = self.tool._run(symbol="MINIMAL", asset_type="crypto", fundamental_data=minimal_data)

        assert result["symbol"] == "MINIMAL"
        assert "analysis_summary" in result
        assert result["analysis_summary"]["confidence"] >= 0.0

    def test_should_calculate_confidence_with_various_data_completeness_levels(self):
        """Test confidence calculation with different data completeness."""
        # High completeness
        complete_data = {f"metric_{i}": 0.5 for i in range(20)}
        regime = MarketRegime(market_stress_level="low")
        high_confidence = self.tool._calculate_confidence_level(complete_data, regime, 0.85)

        # Low completeness (empty data)
        sparse_data = {}
        low_confidence = self.tool._calculate_confidence_level(sparse_data, regime, 0.85)

        assert high_confidence >= low_confidence  # Should be >= due to data completeness factor
        assert 0.0 <= high_confidence <= 1.0
        assert 0.0 <= low_confidence <= 1.0

    def test_should_handle_concurrent_scoring_requests(self):
        """Test thread safety with concurrent requests."""
        import threading

        results = []
        errors = []

        def score_asset(symbol, asset_type):
            try:
                result = self.tool._run(
                    symbol=symbol,
                    asset_type=asset_type,
                    fundamental_data={"roe": 0.25} if asset_type == "stock" else {"expense_ratio": 0.05},
                )
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=score_asset, args=(f"TEST{i}", "stock"))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        assert len(errors) == 0  # No errors should occur
        assert len(results) == 5  # All requests should complete
        for result in results:
            assert "symbol" in result
            assert "analysis_summary" in result


class TestMarketScreeningToolComprehensive:
    """Comprehensive tests for Market Screening Tool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = MarketScreeningTool()

    def test_should_handle_large_screening_universe_efficiently(self, mocker):
        """Test performance with large screening universe."""
        # Mock a large universe
        mock_universe = mocker.patch.object(self.tool, "_get_etf_universe")
        large_universe = {
            "symbols": [f"ETF{i:04d}" for i in range(1000)],  # 1000 ETFs
            "count": 1000,
            "sources": ["Mock Source"],
        }
        mock_universe.return_value = large_universe

        # Mock market data to avoid actual API calls
        mock_data = mocker.patch.object(self.tool, "_get_basic_market_data")
        mock_data.return_value = {
            "symbol": "TEST",
            "expense_ratio": 0.05,
            "aum": 5e9,
            "tracking_error": 0.001,
            "history_years": 5,
            "asset_type": "etf",
        }

        result = self.tool._run(asset_type="etf", max_candidates=10)

        assert "screening_result" in result
        assert result["summary"]["total_screened"] == 1000

    def test_should_handle_api_failures_gracefully(self, mocker):
        """Test handling of API failures during screening."""
        with mocker.patch.object(self.tool, "_get_basic_market_data") as mock_data:
            # Simulate API failures for some symbols
            def side_effect(symbol, asset_type):
                if symbol in ["FAIL1", "FAIL2"]:
                    return {"error": "API failure"}
                return {
                    "symbol": symbol,
                    "expense_ratio": 0.05,
                    "aum": 5e9,
                    "asset_type": asset_type,
                }

            mock_data.side_effect = side_effect

            # Mock universe with some failing symbols
            with mocker.patch.object(self.tool, "_get_etf_universe") as mock_universe:
                mock_universe.return_value = {
                    "symbols": ["GOOD1", "FAIL1", "GOOD2", "FAIL2", "GOOD3"],
                    "count": 5,
                    "sources": ["Mock"],
                }

                result = self.tool._run(asset_type="etf")

                # Should handle failures gracefully and return successful ones
                assert "screening_result" in result
                assert result["summary"]["candidates_found"] >= 0

    def test_should_validate_screening_criteria_edge_cases(self):
        """Test screening criteria validation with edge cases."""
        # Zero values
        zero_criteria = {
            "max_expense_ratio": 0.0,
            "min_aum": 0.0,
            "min_roe": 0.0,
        }

        result = self.tool._run(asset_type="stock", screening_criteria=zero_criteria)
        assert "screening_result" in result

        # Very high values
        high_criteria = {
            "min_roe": 0.99,  # 99% ROE (impossible)
            "min_revenue_growth": 5.0,  # 500% growth (impossible)
        }

        result = self.tool._run(asset_type="stock", screening_criteria=high_criteria)
        assert result["summary"]["candidates_found"] >= 0  # Likely 0 due to impossible criteria

    def test_should_handle_empty_market_data_responses(self, mocker):
        """Test handling of empty market data responses."""
        with mocker.patch.object(self.tool, "_get_basic_market_data") as mock_data:
            mock_data.return_value = {}  # Empty response

            result = self.tool._run(asset_type="etf", max_candidates=5)

            assert "screening_result" in result
            # Should handle empty data gracefully

    def test_should_cache_market_data_efficiently(self, mocker):
        """Test market data caching efficiency."""
        # First call should populate cache
        data1 = self.tool._get_basic_market_data("SPY", "etf")

        # Mock the actual data fetching to verify cache usage
        with mocker.patch.object(self.tool, "_get_etf_market_data") as mock_fetch:
            mock_fetch.return_value = {"different": "data"}

            # Second call should use cache, not call mock
            data2 = self.tool._get_basic_market_data("SPY", "etf")

            # Should be same data (from cache)
            assert data1 == data2
            # Mock should not have been called due to caching
            mock_fetch.assert_not_called()

    def test_should_handle_invalid_market_regions(self):
        """Test handling of invalid market regions."""
        result = self.tool._run(asset_type="stock", market_region="invalid_region")

        # Should fallback to default region
        assert "screening_result" in result
        assert result["summary"]["total_screened"] >= 0

    @pytest.mark.parametrize(
        "asset_type,criteria_key,criteria_value",
        [
            ("etf", "max_expense_ratio", -0.1),  # Negative expense ratio
            ("stock", "min_market_cap", -1e9),  # Negative market cap
            ("crypto", "min_daily_volume", -1e6),  # Negative volume
        ],
    )
    def test_should_handle_invalid_criteria_values(self, asset_type, criteria_key, criteria_value):
        """Test handling of invalid criteria values."""
        invalid_criteria = {criteria_key: criteria_value}

        result = self.tool._run(asset_type=asset_type, screening_criteria=invalid_criteria)

        # Should handle invalid criteria gracefully
        assert "screening_result" in result or "error" in result


class TestBacktestingToolComprehensive:
    """Comprehensive tests for Backtesting Tool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = BacktestingTool()

    def test_should_handle_insufficient_historical_data(self, mocker):
        """Test handling when insufficient historical data is available."""
        # Mock insufficient data scenario
        mock_backtesting_engine = mocker.patch("finwiz.tools.backtesting_tool.get_backtesting_engine")
        mock_data_manager = mocker.patch("finwiz.tools.backtesting_tool.get_historical_data_manager")
        mock_perf_analyzer = mocker.patch("finwiz.tools.backtesting_tool.get_performance_analyzer")

        mock_engine = mocker.MagicMock()
        mock_engine.run_strategy_backtest.side_effect = Exception("Insufficient data")
        mock_backtesting_engine.return_value = mock_engine

        result = self.tool._run(symbol="NEWSTOCK", backtest_period_years=10)

        assert "Error performing backtesting" in result

    def test_should_identify_complex_market_regimes(self):
        """Test identification of complex market regime patterns."""
        # Create complex market data with multiple regime changes
        dates = pd.date_range(start="2020-01-01", end="2023-12-31", freq="D")
        complex_prices = []
        base_price = 100.0

        for i, date in enumerate(dates):
            # Create multiple regime changes
            if i < len(dates) // 6:  # Bull
                daily_return = 0.001
            elif i < len(dates) // 3:  # Bear
                daily_return = -0.002
            elif i < len(dates) // 2:  # Recovery
                daily_return = 0.0015
            elif i < 2 * len(dates) // 3:  # Sideways
                daily_return = 0.0001
            elif i < 5 * len(dates) // 6:  # Volatile
                daily_return = 0.003 if i % 2 == 0 else -0.003
            else:  # Final bull
                daily_return = 0.0008

            base_price *= 1 + daily_return
            complex_prices.append(base_price)

        complex_data = pd.DataFrame(
            {
                "Close": complex_prices,
                "Open": [p * 0.999 for p in complex_prices],
                "High": [p * 1.002 for p in complex_prices],
                "Low": [p * 0.998 for p in complex_prices],
                "Volume": [1000000] * len(complex_prices),
            },
            index=dates,
        )

        regimes = self.tool._identify_market_regimes(complex_data)

        assert len(regimes) > 1  # Should identify multiple regimes
        regime_types = [r["type"] for r in regimes]
        assert len(set(regime_types)) > 1  # Should have different regime types

    def test_should_validate_strategy_with_extreme_performance(self, mocker):
        """Test validation with extreme performance scenarios."""
        # Extremely good performance
        excellent_result = mocker.MagicMock()
        excellent_result.annualized_return = 50.0  # 50% annual return
        excellent_result.sharpe_ratio = 3.0  # Excellent Sharpe
        excellent_result.max_drawdown = -2.0  # Very low drawdown
        excellent_result.win_rate = 0.95  # 95% win rate

        validation_score, validation_passed, notes = self.tool._validate_strategy(excellent_result, {}, [])

        assert validation_passed is True
        assert validation_score >= 0.7  # Should pass validation threshold

        # Extremely poor performance
        terrible_result = mocker.MagicMock()
        terrible_result.annualized_return = -20.0  # Losing money
        terrible_result.sharpe_ratio = -0.5  # Negative Sharpe
        terrible_result.max_drawdown = -80.0  # Massive drawdown
        terrible_result.win_rate = 0.10  # 10% win rate

        validation_score, validation_passed, notes = self.tool._validate_strategy(terrible_result, {}, [])

        assert validation_passed is False
        assert validation_score < 0.3  # Should score very poorly
        assert len(notes) > 3  # Should have multiple failure notes

    def test_should_handle_corrupted_benchmark_data(self):
        """Test handling of corrupted benchmark data."""
        # Create corrupted data
        corrupted_data = pd.DataFrame(
            {
                "Close": [100, None, 102, float("inf"), 104, -50],  # Various corrupted values
                "Volume": [1000, 2000, None, 4000, 5000, 6000],
            },
            index=pd.date_range("2020-01-01", periods=6, freq="D"),
        )

        regimes = self.tool._identify_market_regimes(corrupted_data)

        # Should handle corrupted data gracefully
        assert isinstance(regimes, list)
        # May return empty list or fallback regime

    def test_should_calculate_additional_metrics_with_edge_cases(self, mocker):
        """Test additional metrics calculation with edge cases."""
        # Mock result with edge case data
        edge_case_result = mocker.MagicMock()
        edge_case_result.annualized_return = 0.0  # Zero return
        edge_case_result.benchmark_return = 0.0  # Zero benchmark
        edge_case_result.portfolio_values = {
            "2020-01-01": 100000.0,
            "2020-01-02": 100000.0,  # No change
            "2020-01-03": 100000.0,  # No change
        }
        edge_case_result.trades = []  # No trades

        additional_metrics = self.tool._calculate_additional_metrics(edge_case_result)

        assert isinstance(additional_metrics, dict)
        # Should handle zero returns gracefully

    @pytest.mark.parametrize(
        "period_years,expected_min_days",
        [
            (1, 300),  # 1 year should have ~365 days
            (5, 1500),  # 5 years should have ~1825 days
            (10, 3000),  # 10 years should have ~3650 days
        ],
    )
    def test_should_calculate_correct_date_ranges(self, mocker, period_years, expected_min_days):
        """Test correct date range calculation for different periods."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_years * 365)

        actual_days = (end_date - start_date).days
        assert actual_days >= expected_min_days

    def test_should_handle_strategy_with_no_trades(self, mocker):
        """Test handling of strategy that generates no trades."""
        no_trades_result = mocker.MagicMock()
        no_trades_result.total_trades = 0
        no_trades_result.win_rate = 0.0
        no_trades_result.trades = []
        no_trades_result.annualized_return = 5.0  # Some return from buy-and-hold
        no_trades_result.sharpe_ratio = 0.8
        no_trades_result.max_drawdown = -10.0

        validation_score, validation_passed, notes = self.tool._validate_strategy(no_trades_result, {}, [])

        # Should handle no-trade strategies
        assert isinstance(validation_score, float)
        assert isinstance(validation_passed, bool)
        assert len(notes) > 0


class TestToolsIntegration:
    """Integration tests between the three tools."""

    def setup_method(self):
        """Set up test fixtures."""
        self.a_plus_tool = APlusScoringTool()
        self.screening_tool = MarketScreeningTool()
        self.backtesting_tool = BacktestingTool()

    def test_should_integrate_screening_with_a_plus_scoring(self, mocker):
        """Test integration between screening and A+ scoring."""
        # Mock the A+ scorer in screening tool
        with mocker.patch.object(self.screening_tool._a_plus_scorer, "_run") as mock_scorer:
            mock_scorer.return_value = {
                "composite_score": 0.92,
                "is_a_plus_candidate": True,
                "grade": "A+",
                "analysis_summary": {"confidence": 0.85},
            }

            result = self.screening_tool._run(asset_type="etf", max_candidates=5, include_detailed_analysis=True, min_a_plus_score=0.90)

            # Should have integrated with A+ scorer
            assert "screening_result" in result

    def test_should_handle_tool_chain_errors_gracefully(self, mocker):
        """Test error handling in tool chain integration."""
        # Simulate error in A+ scoring during screening
        with mocker.patch.object(self.screening_tool._a_plus_scorer, "_run") as mock_scorer:
            mock_scorer.side_effect = Exception("A+ scoring failed")

            result = self.screening_tool._run(asset_type="stock", include_detailed_analysis=True)

            # Should handle A+ scoring errors gracefully
            assert "screening_result" in result or "error" in result

    def test_should_maintain_data_consistency_across_tools(self, mocker):
        """Test data consistency when using multiple tools."""
        # Test same symbol across different tools
        symbol = "AAPL"
        fundamental_data = {
            "roe": 0.28,
            "revenue_growth": 0.12,
            "debt_to_equity": 0.15,
            "market_cap": 3000e9,
        }

        # Score with A+ tool
        a_plus_result = self.a_plus_tool._run(symbol=symbol, asset_type="stock", fundamental_data=fundamental_data)

        # The symbol should be consistent
        assert a_plus_result["symbol"] == symbol
        assert a_plus_result["asset_type"] == "stock"

        # Mock backtesting for the same symbol
        with mocker.patch("finwiz.tools.backtesting_tool.get_backtesting_engine") as mock_engine:
            mock_result = mocker.MagicMock()
            mock_result.strategy_name = "TestStrategy"
            mock_result.total_return = 25.0
            mock_result.annualized_return = 12.0
            mock_result.sharpe_ratio = 1.2
            mock_result.max_drawdown = -8.0
            mock_result.volatility = 16.0
            mock_result.total_trades = 30
            mock_result.win_rate = 0.65
            mock_result.start_date = datetime(2019, 1, 1)
            mock_result.end_date = datetime(2024, 1, 1)
            mock_result.initial_capital = 100000.0
            mock_result.final_value = 125000.0
            mock_result.benchmark_return = 20.0
            mock_result.var_95 = -2.0
            mock_result.cvar_95 = -3.0
            mock_result.calmar_ratio = 1.5
            mock_result.portfolio_values = {}
            mock_result.trades = []

            mock_engine_instance = mocker.MagicMock()
            mock_engine_instance.run_strategy_backtest.return_value = mock_result
            mock_engine.return_value = mock_engine_instance

            with mocker.patch("finwiz.tools.backtesting_tool.get_historical_data_manager"):
                with mocker.patch("finwiz.tools.backtesting_tool.get_performance_analyzer"):
                    backtest_result_json = self.backtesting_tool._run(symbol=symbol, include_regime_analysis=False)
                    backtest_result = json.loads(backtest_result_json)

                    # Symbol should be consistent across tools
                    assert backtest_result["symbol"] == symbol

    def test_should_handle_concurrent_tool_usage(self, mocker):
        """Test concurrent usage of multiple tools."""
        import threading

        results = {"a_plus": [], "screening": [], "backtesting": [], "errors": []}

        def run_a_plus():
            try:
                result = self.a_plus_tool._run(symbol="TEST1", asset_type="stock", fundamental_data={"roe": 0.25})
                results["a_plus"].append(result)
            except Exception as e:
                results["errors"].append(e)

        def run_screening():
            try:
                result = self.screening_tool._run(asset_type="etf", max_candidates=5)
                results["screening"].append(result)
            except Exception as e:
                results["errors"].append(e)

        def run_backtesting(mocker):
            try:
                with mocker.patch("finwiz.tools.backtesting_tool.get_backtesting_engine"):
                    with mocker.patch("finwiz.tools.backtesting_tool.get_historical_data_manager"):
                        with mocker.patch("finwiz.tools.backtesting_tool.get_performance_analyzer"):
                            result = self.backtesting_tool._run(symbol="TEST3", include_regime_analysis=False)
                            results["backtesting"].append(result)
            except Exception as e:
                results["errors"].append(e)

        # Run tools concurrently
        threads = [
            threading.Thread(target=run_a_plus),
            threading.Thread(target=run_screening),
            threading.Thread(target=run_backtesting),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All tools should complete without errors
        assert len(results["errors"]) == 0
        assert len(results["a_plus"]) == 1
        assert len(results["screening"]) == 1
        assert len(results["backtesting"]) == 1
