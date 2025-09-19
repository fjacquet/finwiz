"""
Integration tests for technical analysis engine.

These tests verify the technical analysis engine works with realistic data
and integrates properly with the quantitative analysis framework.
"""

import numpy as np
import pandas as pd
import pytest

from finwiz.quantitative.config import TechnicalIndicator
from finwiz.quantitative.technical import (
    SignalType,
    TechnicalAnalysisEngine,
    calculate_technical_indicators,
    get_confluence_signals,
)


@pytest.mark.integration
class TestTechnicalAnalysisIntegration:
    """Integration tests for technical analysis engine."""

    @pytest.fixture
    def realistic_stock_data(self) -> pd.DataFrame:
        """Generate realistic stock price data for testing."""
        np.random.seed(42)  # For reproducible tests

        # Generate 6 months of daily data
        dates = pd.date_range(start="2023-01-01", periods=180, freq="D")

        # Simulate realistic stock price movement
        base_price = 150.0
        volatility = 0.02
        trend = 0.0005  # Small upward trend

        prices = []
        current_price = base_price

        for i in range(180):
            # Add trend and random walk
            daily_return = np.random.normal(trend, volatility)
            current_price *= 1 + daily_return

            # Ensure price stays positive
            current_price = max(current_price, 1.0)
            prices.append(current_price)

        # Generate OHLC from close prices
        data = []
        for i, close in enumerate(prices):
            # Generate realistic OHLC relationships
            daily_range = close * np.random.uniform(0.01, 0.04)  # 1-4% daily range

            high = close + np.random.uniform(0, daily_range * 0.7)
            low = close - np.random.uniform(0, daily_range * 0.7)
            open_price = low + (high - low) * np.random.random()

            # Ensure OHLC relationships are valid
            high = max(high, open_price, close)
            low = min(low, open_price, close)

            volume = int(np.random.uniform(500000, 2000000))

            data.append(
                {
                    "Open": open_price,
                    "High": high,
                    "Low": low,
                    "Close": close,
                    "Volume": volume,
                }
            )

        return pd.DataFrame(data, index=dates)

    def test_comprehensive_technical_analysis(self, realistic_stock_data):
        """Test comprehensive technical analysis with multiple indicators."""
        engine = TechnicalAnalysisEngine()

        indicators = [
            TechnicalIndicator.SMA,
            TechnicalIndicator.EMA,
            TechnicalIndicator.RSI,
            TechnicalIndicator.MACD,
            TechnicalIndicator.BOLLINGER_BANDS,
            TechnicalIndicator.STOCHASTIC,
            TechnicalIndicator.ATR,
            TechnicalIndicator.ADX,
            TechnicalIndicator.CCI,
            TechnicalIndicator.WILLIAMS_R,
            TechnicalIndicator.FIBONACCI,
        ]

        result = engine.analyze_symbol(realistic_stock_data, "AAPL", "1d", indicators)

        # Verify comprehensive analysis results
        assert result.symbol == "AAPL"
        assert result.timeframe == "1d"
        assert len(result.indicator_results) == len(indicators)

        # Verify all indicators were calculated
        for indicator in indicators:
            assert indicator.value in result.indicator_results
            indicator_result = result.indicator_results[indicator.value]
            assert len(indicator_result.values) > 0

        # Verify overall signal is generated
        assert result.overall_signal in [
            SignalType.BUY,
            SignalType.SELL,
            SignalType.HOLD,
            SignalType.STRONG_BUY,
            SignalType.STRONG_SELL,
        ]
        assert 0.0 <= result.overall_confidence <= 1.0

        # Verify signal counts
        total_signals = result.bullish_signals_count + result.bearish_signals_count + result.neutral_signals_count
        assert total_signals > 0

    def test_advanced_indicators_integration(self, realistic_stock_data):
        """Test integration of advanced technical indicators."""
        engine = TechnicalAnalysisEngine()

        # Test ADX trend analysis
        adx_result = engine.calculate_adx(realistic_stock_data)
        assert "ADX" in adx_result.values
        assert "PLUS_DI" in adx_result.values
        assert "MINUS_DI" in adx_result.values

        # Test CCI momentum analysis
        cci_result = engine.calculate_cci(realistic_stock_data)
        assert "CCI" in cci_result.values

        # Test Williams %R analysis
        willr_result = engine.calculate_williams_r(realistic_stock_data)
        assert "Williams_R" in willr_result.values

        # Test Fibonacci retracements
        fib_result = engine.calculate_fibonacci_retracements(realistic_stock_data)
        assert "0.0" in fib_result.values
        assert "61.8" in fib_result.values
        assert "100.0" in fib_result.values

    def test_sma_crossover_strategy(self, realistic_stock_data):
        """Test SMA crossover strategy detection."""
        engine = TechnicalAnalysisEngine()

        # Calculate multiple SMA periods (use shorter periods for 180-day dataset)
        result = engine.calculate_sma(realistic_stock_data, [20, 50, 100])

        # Verify SMA values are calculated
        assert "SMA_20" in result.values
        assert "SMA_50" in result.values
        assert "SMA_100" in result.values

        # Verify signals are generated
        assert len(result.signals) > 0

        # Check signal properties
        for signal in result.signals:
            assert signal.indicator.startswith("SMA_")
            assert signal.signal_type in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
            assert 0.0 <= signal.confidence <= 1.0
            assert signal.price_level > 0

    def test_rsi_divergence_detection(self, realistic_stock_data):
        """Test RSI calculation and signal generation."""
        engine = TechnicalAnalysisEngine()

        result = engine.calculate_rsi(realistic_stock_data, period=14)

        # Verify RSI calculation
        assert "RSI" in result.values
        rsi_values = result.values["RSI"]

        # RSI should be between 0 and 100
        valid_rsi_values = [v for v in rsi_values if not np.isnan(v)]
        assert all(0 <= v <= 100 for v in valid_rsi_values)

        # Verify signals
        assert len(result.signals) > 0
        signal = result.signals[0]
        assert signal.indicator == "RSI"
        assert "rsi_value" in signal.metadata

    def test_macd_momentum_analysis(self, realistic_stock_data):
        """Test MACD momentum analysis."""
        engine = TechnicalAnalysisEngine()

        result = engine.calculate_macd(realistic_stock_data)

        # Verify MACD components
        assert "MACD_line" in result.values
        assert "MACD_signal" in result.values
        assert "MACD_histogram" in result.values

        # Verify signals
        if len(result.signals) > 0:
            signal = result.signals[0]
            assert signal.indicator == "MACD"
            assert "macd_line" in signal.metadata
            assert "signal_line" in signal.metadata
            assert "histogram" in signal.metadata

    def test_bollinger_bands_volatility_analysis(self, realistic_stock_data):
        """Test Bollinger Bands volatility analysis."""
        engine = TechnicalAnalysisEngine()

        result = engine.calculate_bollinger_bands(realistic_stock_data)

        # Verify Bollinger Bands components
        assert "upper_band" in result.values
        assert "middle_band" in result.values
        assert "lower_band" in result.values

        # Verify band relationships (upper > middle > lower)
        upper_band = result.values["upper_band"]
        middle_band = result.values["middle_band"]
        lower_band = result.values["lower_band"]

        # Check relationships for valid values
        for i in range(len(upper_band)):
            if not (np.isnan(upper_band[i]) or np.isnan(middle_band[i]) or np.isnan(lower_band[i])):
                assert upper_band[i] >= middle_band[i] >= lower_band[i]

    def test_confluence_zone_detection(self, realistic_stock_data):
        """Test confluence zone detection with multiple indicators."""
        result = calculate_technical_indicators(
            realistic_stock_data, "AAPL", [TechnicalIndicator.RSI, TechnicalIndicator.MACD, TechnicalIndicator.SMA]
        )

        # Check if confluence zones were detected
        if len(result.confluence_zones) > 0:
            for zone in result.confluence_zones:
                assert len(zone.contributing_signals) >= 2
                assert zone.signal_type in [SignalType.BUY, SignalType.SELL, SignalType.STRONG_BUY, SignalType.STRONG_SELL]
                assert 0.0 <= zone.confidence <= 1.0
                assert zone.zone_range[0] <= zone.zone_range[1]

    def test_convenience_functions(self, realistic_stock_data):
        """Test convenience functions for technical analysis."""
        # Test calculate_technical_indicators function
        result = calculate_technical_indicators(realistic_stock_data, "TEST", [TechnicalIndicator.SMA, TechnicalIndicator.RSI])

        assert result.symbol == "TEST"
        assert len(result.indicator_results) == 2

        # Test get_confluence_signals function
        confluence_zones = get_confluence_signals(realistic_stock_data, "TEST", min_confluence=2)

        # All returned zones should meet minimum confluence requirement
        for zone in confluence_zones:
            assert len(zone.contributing_signals) >= 2

    def test_error_handling_with_invalid_data(self):
        """Test error handling with various invalid data scenarios."""
        engine = TechnicalAnalysisEngine()

        # Test with insufficient data
        insufficient_data = pd.DataFrame(
            {
                "Open": [100] * 10,
                "High": [105] * 10,
                "Low": [95] * 10,
                "Close": [102] * 10,
                "Volume": [100000] * 10,
            }
        )

        with pytest.raises(ValueError, match="Insufficient data points"):
            engine.analyze_symbol(insufficient_data, "TEST")

        # Test with missing columns
        invalid_data = pd.DataFrame(
            {
                "Close": [100, 101, 102],
            }
        )

        with pytest.raises(ValueError, match="Missing required columns"):
            engine.analyze_symbol(invalid_data, "TEST")

    def test_signal_accuracy_with_trending_data(self):
        """Test signal accuracy with clearly trending data."""
        # Create strongly trending upward data
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")

        trending_data = []
        for i in range(100):
            close = 100 + i * 0.5  # Clear uptrend
            high = close * 1.02
            low = close * 0.98
            open_price = close * 1.01

            trending_data.append(
                {
                    "Open": open_price,
                    "High": high,
                    "Low": low,
                    "Close": close,
                    "Volume": 100000,
                }
            )

        df = pd.DataFrame(trending_data, index=dates)

        result = calculate_technical_indicators(
            df, "TREND_TEST", [TechnicalIndicator.SMA, TechnicalIndicator.RSI, TechnicalIndicator.MACD]
        )

        # With clear uptrend, should have more bullish signals
        assert result.bullish_signals_count >= result.bearish_signals_count

        # Overall signal should be bullish or neutral (not bearish)
        assert result.overall_signal in [SignalType.BUY, SignalType.STRONG_BUY, SignalType.HOLD]

    def test_performance_with_large_dataset(self):
        """Test performance with larger dataset."""
        # Generate 2 years of data
        dates = pd.date_range(start="2022-01-01", periods=500, freq="D")

        large_data = []
        for i in range(500):
            close = 100 + np.random.normal(0, 5)
            high = close + abs(np.random.normal(0, 2))
            low = close - abs(np.random.normal(0, 2))
            open_price = low + (high - low) * np.random.random()

            large_data.append(
                {
                    "Open": open_price,
                    "High": high,
                    "Low": low,
                    "Close": close,
                    "Volume": int(np.random.uniform(100000, 1000000)),
                }
            )

        df = pd.DataFrame(large_data, index=dates)

        # Should complete analysis in reasonable time
        import time

        start_time = time.time()

        result = calculate_technical_indicators(
            df,
            "PERF_TEST",
            [
                TechnicalIndicator.SMA,
                TechnicalIndicator.EMA,
                TechnicalIndicator.RSI,
                TechnicalIndicator.MACD,
                TechnicalIndicator.BOLLINGER_BANDS,
            ],
        )

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete within reasonable time (less than 5 seconds)
        assert execution_time < 5.0

        # Verify results
        assert result.symbol == "PERF_TEST"
        assert len(result.indicator_results) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
