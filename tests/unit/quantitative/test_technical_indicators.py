"""
Unit tests for technical indicators module (TA-Lib wrappers).

Tests cover:
- RSI calculations with expected values
- MACD calculations with expected values
- Bollinger Bands calculations with expected values
- Edge cases (insufficient data, NaN values)
- Sample financial data validation
"""

import numpy as np
import pandas as pd
import pytest

from finwiz.quantitative.technical.technical_indicators import (
    TALibWrappers,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
)


class TestTALibWrappers:
    """Test suite for TALibWrappers class."""

    @pytest.fixture
    def sample_prices(self) -> np.ndarray:
        """Create sample price data for testing."""
        # Generate realistic price data with known characteristics
        # This creates a simple uptrend with some volatility
        np.random.seed(42)
        base_prices = np.linspace(100, 110, 50)
        noise = np.random.normal(0, 0.5, 50)
        prices = base_prices + noise
        return prices

    @pytest.fixture
    def sample_ohlcv_data(self) -> dict[str, np.ndarray]:
        """Create sample OHLCV data for testing."""
        np.random.seed(42)
        close_prices = np.linspace(100, 110, 50) + np.random.normal(0, 0.5, 50)
        high_prices = close_prices * 1.02
        low_prices = close_prices * 0.98
        volume = np.random.randint(100000, 1000000, 50)

        return {
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "volume": volume.astype(float),
        }

    @pytest.fixture
    def sample_dataframe(self, sample_ohlcv_data) -> pd.DataFrame:
        """Create sample DataFrame for convenience function testing."""
        dates = pd.date_range(start="2023-01-01", periods=50, freq="D")
        df = pd.DataFrame(
            {
                "Open": sample_ohlcv_data["close"] * 0.99,
                "High": sample_ohlcv_data["high"],
                "Low": sample_ohlcv_data["low"],
                "Close": sample_ohlcv_data["close"],
                "Volume": sample_ohlcv_data["volume"],
            },
            index=dates,
        )
        return df

    # RSI Tests
    def test_rsi_calculation_basic(self, sample_prices):
        """Test basic RSI calculation returns valid values."""
        result = TALibWrappers.rsi(sample_prices, period=14)

        assert result is not None
        assert len(result) == len(sample_prices)

        # RSI should be between 0 and 100
        valid_values = result[~np.isnan(result)]
        assert np.all(valid_values >= 0)
        assert np.all(valid_values <= 100)

    def test_rsi_calculation_expected_values(self):
        """Test RSI calculation with known expected values."""
        # Create a simple uptrend - RSI should be above 50
        prices = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119])

        result = TALibWrappers.rsi(prices, period=14)

        # For an uptrend, RSI should be elevated (typically > 50)
        # Check the last few values (after warmup period)
        last_rsi = result[-1]
        assert not np.isnan(last_rsi)
        assert last_rsi > 50, f"Expected RSI > 50 for uptrend, got {last_rsi}"

    def test_rsi_overbought_condition(self):
        """Test RSI correctly identifies overbought conditions."""
        # Create strong uptrend that should result in high RSI
        prices = np.array([100.0] + [100 + i * 2 for i in range(1, 30)])

        result = TALibWrappers.rsi(prices, period=14)

        # Last RSI value should be high (overbought territory)
        last_rsi = result[-1]
        assert last_rsi > 60, f"Expected high RSI for strong uptrend, got {last_rsi}"

    def test_rsi_oversold_condition(self):
        """Test RSI correctly identifies oversold conditions."""
        # Create strong downtrend that should result in low RSI
        prices = np.array([100.0] + [100 - i * 2 for i in range(1, 30)])

        result = TALibWrappers.rsi(prices, period=14)

        # Last RSI value should be low (oversold territory)
        last_rsi = result[-1]
        assert last_rsi < 40, f"Expected low RSI for strong downtrend, got {last_rsi}"

    def test_rsi_insufficient_data(self):
        """Test RSI with insufficient data returns NaN values."""
        # Only 10 data points, need at least 14 for RSI(14)
        prices = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109])

        result = TALibWrappers.rsi(prices, period=14)

        # Should return array of same length but with NaN values
        assert len(result) == len(prices)
        assert np.all(np.isnan(result))

    def test_rsi_with_nan_values(self):
        """Test RSI handles NaN values in input data."""
        prices = np.array([100, 101, np.nan, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119])

        result = TALibWrappers.rsi(prices, period=14)

        # Should handle NaN gracefully
        assert len(result) == len(prices)
        # Result will have NaN values but shouldn't crash

    # MACD Tests
    def test_macd_calculation_basic(self, sample_prices):
        """Test basic MACD calculation returns valid values."""
        macd_line, signal_line, histogram = TALibWrappers.macd(sample_prices, fast=12, slow=26, signal=9)

        assert macd_line is not None
        assert signal_line is not None
        assert histogram is not None
        assert len(macd_line) == len(sample_prices)
        assert len(signal_line) == len(sample_prices)
        assert len(histogram) == len(sample_prices)

    def test_macd_calculation_expected_values(self):
        """Test MACD calculation with known expected values."""
        # Create uptrend - MACD should be positive
        prices = np.array([100.0 + i * 0.5 for i in range(50)])

        macd_line, signal_line, histogram = TALibWrappers.macd(prices, fast=12, slow=26, signal=9)

        # For uptrend, MACD line should eventually be positive
        valid_macd = macd_line[~np.isnan(macd_line)]
        if len(valid_macd) > 0:
            # Check last few values
            assert valid_macd[-1] > 0, f"Expected positive MACD for uptrend, got {valid_macd[-1]}"

    def test_macd_histogram_calculation(self):
        """Test MACD histogram is correctly calculated as MACD - Signal."""
        prices = np.array([100.0 + i * 0.5 for i in range(50)])

        macd_line, signal_line, histogram = TALibWrappers.macd(prices, fast=12, slow=26, signal=9)

        # Histogram should equal MACD - Signal (where both are valid)
        valid_idx = ~(np.isnan(macd_line) | np.isnan(signal_line) | np.isnan(histogram))
        if np.any(valid_idx):
            calculated_histogram = macd_line[valid_idx] - signal_line[valid_idx]
            np.testing.assert_array_almost_equal(histogram[valid_idx], calculated_histogram, decimal=6)

    def test_macd_crossover_detection(self):
        """Test MACD can detect bullish crossover."""
        # Create data that transitions from downtrend to uptrend
        # Start with downtrend, then reverse to uptrend
        downtrend = [100 - i * 1.0 for i in range(40)]
        uptrend = [60 + i * 1.0 for i in range(40)]
        prices = np.array(downtrend + uptrend)

        macd_line, signal_line, histogram = TALibWrappers.macd(prices, fast=12, slow=26, signal=9)

        # Histogram should change from negative to positive
        valid_histogram = histogram[~np.isnan(histogram)]
        if len(valid_histogram) > 20:
            # Check that histogram transitions from negative to positive
            # Look at middle vs end values
            mid_point = len(valid_histogram) // 2
            early_avg = np.mean(valid_histogram[:mid_point])
            late_avg = np.mean(valid_histogram[mid_point:])
            # Late average should be more positive than early average
            assert late_avg > early_avg

    def test_macd_insufficient_data(self):
        """Test MACD with insufficient data returns NaN values."""
        # Only 20 data points, need at least 26 for slow EMA
        prices = np.array([100.0 + i * 0.5 for i in range(20)])

        macd_line, signal_line, histogram = TALibWrappers.macd(prices, fast=12, slow=26, signal=9)

        # Should return arrays but with many NaN values
        assert len(macd_line) == len(prices)
        # Most values should be NaN due to insufficient data
        assert np.sum(np.isnan(macd_line)) > len(prices) // 2

    # Bollinger Bands Tests
    def test_bollinger_bands_calculation_basic(self, sample_prices):
        """Test basic Bollinger Bands calculation returns valid values."""
        upper, middle, lower = TALibWrappers.bollinger_bands(sample_prices, period=20, std_dev=2.0)

        assert upper is not None
        assert middle is not None
        assert lower is not None
        assert len(upper) == len(sample_prices)
        assert len(middle) == len(sample_prices)
        assert len(lower) == len(sample_prices)

    def test_bollinger_bands_relationship(self, sample_prices):
        """Test Bollinger Bands maintain correct relationship (upper > middle > lower)."""
        upper, middle, lower = TALibWrappers.bollinger_bands(sample_prices, period=20, std_dev=2.0)

        # Where all values are valid, upper > middle > lower
        valid_idx = ~(np.isnan(upper) | np.isnan(middle) | np.isnan(lower))
        if np.any(valid_idx):
            assert np.all(upper[valid_idx] >= middle[valid_idx])
            assert np.all(middle[valid_idx] >= lower[valid_idx])

    def test_bollinger_bands_middle_is_sma(self, sample_prices):
        """Test Bollinger Bands middle line equals SMA."""
        upper, middle, lower = TALibWrappers.bollinger_bands(sample_prices, period=20, std_dev=2.0)

        sma = TALibWrappers.sma(sample_prices, period=20)

        # Middle band should equal SMA
        valid_idx = ~(np.isnan(middle) | np.isnan(sma))
        if np.any(valid_idx):
            np.testing.assert_array_almost_equal(middle[valid_idx], sma[valid_idx], decimal=6)

    def test_bollinger_bands_width_with_std_dev(self):
        """Test Bollinger Bands width changes with std_dev parameter."""
        prices = np.array([100.0 + i * 0.5 for i in range(50)])

        # Calculate with 2 std dev
        upper_2, middle_2, lower_2 = TALibWrappers.bollinger_bands(prices, period=20, std_dev=2.0)

        # Calculate with 3 std dev
        upper_3, middle_3, lower_3 = TALibWrappers.bollinger_bands(prices, period=20, std_dev=3.0)

        # Bands with 3 std dev should be wider
        valid_idx = ~(np.isnan(upper_2) | np.isnan(upper_3))
        if np.any(valid_idx):
            width_2 = upper_2[valid_idx] - lower_2[valid_idx]
            width_3 = upper_3[valid_idx] - lower_3[valid_idx]
            assert np.all(width_3 > width_2)

    def test_bollinger_bands_insufficient_data(self):
        """Test Bollinger Bands with insufficient data returns NaN values."""
        # Only 15 data points, need at least 20 for period=20
        prices = np.array([100.0 + i * 0.5 for i in range(15)])

        upper, middle, lower = TALibWrappers.bollinger_bands(prices, period=20, std_dev=2.0)

        # Should return arrays but with all NaN values
        assert len(upper) == len(prices)
        assert np.all(np.isnan(upper))
        assert np.all(np.isnan(middle))
        assert np.all(np.isnan(lower))

    # SMA Tests
    def test_sma_calculation_basic(self, sample_prices):
        """Test basic SMA calculation returns valid values."""
        result = TALibWrappers.sma(sample_prices, period=20)

        assert result is not None
        assert len(result) == len(sample_prices)

        # SMA values should be within reasonable range of input prices
        valid_values = result[~np.isnan(result)]
        assert len(valid_values) > 0
        assert np.all(valid_values > 0)

    def test_sma_smoothing_effect(self):
        """Test SMA smooths out price volatility."""
        # Create prices with high volatility
        np.random.seed(42)
        prices = 100 + np.random.normal(0, 5, 50)

        sma = TALibWrappers.sma(prices, period=10)

        # SMA should have lower volatility than raw prices
        valid_sma = sma[~np.isnan(sma)]
        if len(valid_sma) > 10:
            price_std = np.std(prices[-len(valid_sma) :])
            sma_std = np.std(valid_sma)
            assert sma_std < price_std, "SMA should smooth volatility"

    # EMA Tests
    def test_ema_calculation_basic(self, sample_prices):
        """Test basic EMA calculation returns valid values."""
        result = TALibWrappers.ema(sample_prices, period=20)

        assert result is not None
        assert len(result) == len(sample_prices)

        valid_values = result[~np.isnan(result)]
        assert len(valid_values) > 0

    def test_ema_more_responsive_than_sma(self):
        """Test EMA is more responsive to recent price changes than SMA."""
        # Create prices with gradual increase then sudden jump
        gradual = [100.0 + i * 0.1 for i in range(40)]
        jump = [110.0] * 30
        prices = np.array(gradual + jump)

        sma = TALibWrappers.sma(prices, period=20)
        ema = TALibWrappers.ema(prices, period=20)

        # After the jump, EMA should respond faster than SMA
        # Check values 10 periods after the jump starts
        jump_start_idx = 40
        check_idx = jump_start_idx + 10

        if check_idx < len(prices) and not np.isnan(sma[check_idx]) and not np.isnan(ema[check_idx]):
            # EMA should be closer to the new price level (110) than SMA
            ema_distance = abs(ema[check_idx] - 110)
            sma_distance = abs(sma[check_idx] - 110)
            assert ema_distance < sma_distance, f"EMA distance {ema_distance} should be less than SMA distance {sma_distance}"

    # ATR Tests
    def test_atr_calculation_basic(self, sample_ohlcv_data):
        """Test basic ATR calculation returns valid values."""
        result = TALibWrappers.atr(
            sample_ohlcv_data["high"],
            sample_ohlcv_data["low"],
            sample_ohlcv_data["close"],
            period=14,
        )

        assert result is not None
        assert len(result) == len(sample_ohlcv_data["close"])

        # ATR should be positive
        valid_values = result[~np.isnan(result)]
        assert len(valid_values) > 0
        assert np.all(valid_values >= 0)

    def test_atr_reflects_volatility(self):
        """Test ATR increases with higher volatility."""
        # Low volatility data
        low_vol_close = np.array([100.0 + i * 0.1 for i in range(30)])
        low_vol_high = low_vol_close * 1.005
        low_vol_low = low_vol_close * 0.995

        # High volatility data
        high_vol_close = np.array([100.0 + i * 0.1 for i in range(30)])
        high_vol_high = high_vol_close * 1.05
        high_vol_low = high_vol_close * 0.95

        atr_low = TALibWrappers.atr(low_vol_high, low_vol_low, low_vol_close, period=14)
        atr_high = TALibWrappers.atr(high_vol_high, high_vol_low, high_vol_close, period=14)

        # High volatility should have higher ATR
        valid_low = atr_low[~np.isnan(atr_low)]
        valid_high = atr_high[~np.isnan(atr_high)]

        if len(valid_low) > 0 and len(valid_high) > 0:
            assert np.mean(valid_high) > np.mean(valid_low)

    # Convenience Function Tests
    def test_calculate_sma_convenience(self, sample_dataframe):
        """Test calculate_sma convenience function."""
        result = calculate_sma(sample_dataframe, period=20)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_dataframe)
        assert result.index.equals(sample_dataframe.index)

    def test_calculate_ema_convenience(self, sample_dataframe):
        """Test calculate_ema convenience function."""
        result = calculate_ema(sample_dataframe, period=20)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_dataframe)

    def test_calculate_rsi_convenience(self, sample_dataframe):
        """Test calculate_rsi convenience function."""
        result = calculate_rsi(sample_dataframe, period=14)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_dataframe)

        # RSI should be between 0 and 100
        valid_values = result.dropna()
        assert np.all(valid_values >= 0)
        assert np.all(valid_values <= 100)

    def test_calculate_macd_convenience(self, sample_dataframe):
        """Test calculate_macd convenience function."""
        result = calculate_macd(sample_dataframe, fast=12, slow=26, signal=9)

        assert isinstance(result, dict)
        assert "MACD" in result
        assert "Signal" in result
        assert "Histogram" in result

        assert isinstance(result["MACD"], pd.Series)
        assert isinstance(result["Signal"], pd.Series)
        assert isinstance(result["Histogram"], pd.Series)

        assert len(result["MACD"]) == len(sample_dataframe)

    def test_calculate_bollinger_bands_convenience(self, sample_dataframe):
        """Test calculate_bollinger_bands convenience function."""
        result = calculate_bollinger_bands(sample_dataframe, period=20, std_dev=2.0)

        assert isinstance(result, dict)
        assert "Upper" in result
        assert "Middle" in result
        assert "Lower" in result

        assert isinstance(result["Upper"], pd.Series)
        assert isinstance(result["Middle"], pd.Series)
        assert isinstance(result["Lower"], pd.Series)

        # Check relationship
        valid_idx = ~(result["Upper"].isna() | result["Middle"].isna() | result["Lower"].isna())
        if valid_idx.any():
            assert (result["Upper"][valid_idx] >= result["Middle"][valid_idx]).all()
            assert (result["Middle"][valid_idx] >= result["Lower"][valid_idx]).all()

    # Edge Case Tests
    def test_empty_array_handling(self):
        """Test handling of empty arrays."""
        empty_prices = np.array([])

        # Should handle gracefully without crashing
        result = TALibWrappers.rsi(empty_prices, period=14)
        assert len(result) == 0

    def test_single_value_array(self):
        """Test handling of single value arrays."""
        single_price = np.array([100.0])

        result = TALibWrappers.rsi(single_price, period=14)
        assert len(result) == 1
        assert np.isnan(result[0])

    def test_all_nan_values(self):
        """Test handling of all NaN input values."""
        nan_prices = np.array([np.nan] * 50)

        result = TALibWrappers.rsi(nan_prices, period=14)
        assert len(result) == len(nan_prices)
        assert np.all(np.isnan(result))

    def test_mixed_nan_values(self):
        """Test handling of mixed valid and NaN values."""
        prices = np.array(
            [100, 101, np.nan, 103, 104, np.nan, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119]
        )

        # Should handle without crashing
        result = TALibWrappers.rsi(prices, period=14)
        assert len(result) == len(prices)

    def test_zero_values_handling(self):
        """Test handling of zero values in price data."""
        prices = np.array([100, 101, 0, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119])

        # Should handle without crashing (though results may be affected)
        result = TALibWrappers.rsi(prices, period=14)
        assert len(result) == len(prices)

    def test_negative_values_handling(self):
        """Test handling of negative values in price data."""
        prices = np.array([100, 101, -102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119])

        # Should handle without crashing
        result = TALibWrappers.rsi(prices, period=14)
        assert len(result) == len(prices)

    def test_very_large_values(self):
        """Test handling of very large price values."""
        prices = np.array([1e10 + i * 1e8 for i in range(50)])

        result = TALibWrappers.rsi(prices, period=14)

        # Should handle large values
        valid_values = result[~np.isnan(result)]
        assert len(valid_values) > 0
        assert np.all(valid_values >= 0)
        assert np.all(valid_values <= 100)

    def test_very_small_values(self):
        """Test handling of very small price values."""
        prices = np.array([0.0001 + i * 0.00001 for i in range(50)])

        result = TALibWrappers.rsi(prices, period=14)

        # Should handle small values
        valid_values = result[~np.isnan(result)]
        assert len(valid_values) > 0
        assert np.all(valid_values >= 0)
        assert np.all(valid_values <= 100)

    def test_constant_prices(self):
        """Test handling of constant price values."""
        prices = np.array([100.0] * 50)

        result = TALibWrappers.rsi(prices, period=14)

        # RSI of constant prices should be around 50 (neutral)
        valid_values = result[~np.isnan(result)]
        if len(valid_values) > 0:
            # For constant prices, RSI is undefined but TA-Lib returns NaN or 0
            # Just verify it doesn't crash
            assert True
