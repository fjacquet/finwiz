"""
Unit tests for Technical Indicator Fallback Calculator.

Tests cover:
- Missing indicator detection and calculation
- RSI calculation from price history
- MACD calculation from price history
- Moving average calculation from price history
- Beta fallback to neutral value
- Graceful degradation with insufficient data
- Price history extraction from various formats
"""

import pandas as pd
import pytest
from faker import Faker
from pytest import approx

from finwiz.scoring.technical_fallback import (
    calculate_missing_technical_indicators,
    get_price_history_from_data,
)


class TestCalculateMissingTechnicalIndicators:
    """Test cases for calculate_missing_technical_indicators function."""

    @pytest.fixture
    def fake(self):
        """Faker instance for generating test data."""
        return Faker()

    @pytest.fixture
    def sample_prices(self, fake):
        """Generate realistic price series for testing."""
        # Generate 250 days of price data with realistic random walk
        dates = pd.date_range(end=pd.Timestamp.now(), periods=250, freq="D")

        # Start at 100 and apply random daily returns
        returns = [fake.pyfloat(min_value=-0.03, max_value=0.03) for _ in range(250)]
        prices = [100.0]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        return pd.Series(prices, index=dates)

    def test_should_calculate_missing_moving_averages(self, sample_prices):
        """Test calculation of missing moving averages from price history."""
        # Arrange
        current_price = float(sample_prices.iloc[-1])
        data = {
            "current_price": current_price,
            # moving_avg_50 and moving_avg_200 are missing
        }

        # Act
        result = calculate_missing_technical_indicators(data, sample_prices)

        # Assert
        assert "moving_avg_50" in result
        assert "moving_avg_200" in result
        assert result["moving_avg_50"] is not None
        assert result["moving_avg_200"] is not None

        # MA50 should be close to but not exactly current price
        assert result["moving_avg_50"] != current_price
        # MA200 should be different from MA50
        assert result["moving_avg_200"] != result["moving_avg_50"]

    def test_should_calculate_missing_rsi(self, sample_prices):
        """Test calculation of missing RSI from price history."""
        # Arrange
        data = {
            "current_price": float(sample_prices.iloc[-1]),
            # rsi is missing
        }

        # Act
        result = calculate_missing_technical_indicators(data, sample_prices)

        # Assert
        assert "rsi" in result
        assert result["rsi"] is not None
        assert 0.0 <= result["rsi"] <= 100.0  # RSI must be in valid range

    def test_should_calculate_missing_macd(self, sample_prices):
        """Test calculation of missing MACD and signal from price history."""
        # Arrange
        data = {
            "current_price": float(sample_prices.iloc[-1]),
            # macd and macd_signal are missing
        }

        # Act
        result = calculate_missing_technical_indicators(data, sample_prices)

        # Assert
        assert "macd" in result
        assert "macd_signal" in result
        assert result["macd"] is not None
        assert result["macd_signal"] is not None

    def test_should_default_beta_when_missing(self, sample_prices):
        """Test that beta defaults to 1.0 (neutral) when missing."""
        # Arrange
        data = {
            "current_price": float(sample_prices.iloc[-1]),
            # beta is missing
        }

        # Act
        result = calculate_missing_technical_indicators(data, sample_prices)

        # Assert
        assert "beta" in result
        assert result["beta"] == approx(1.0)  # Neutral beta

    def test_should_not_overwrite_existing_indicators(self, sample_prices):
        """Test that existing indicators are not overwritten."""
        # Arrange
        data = {
            "current_price": 150.0,
            "rsi": 65.0,  # Already present
            "macd": 2.5,  # Already present
            "moving_avg_50": 145.0,  # Already present
        }

        # Act
        result = calculate_missing_technical_indicators(data, sample_prices)

        # Assert - original values preserved
        assert result["rsi"] == approx(65.0)
        assert result["macd"] == approx(2.5)
        assert result["moving_avg_50"] == approx(145.0)

    def test_should_use_current_price_fallback_without_history(self):
        """Test fallback to current price when no price history available."""
        # Arrange
        data = {
            "current_price": 150.0,
            # No indicators, no price history
        }

        # Act
        result = calculate_missing_technical_indicators(data, price_history=None)

        # Assert - uses current_price or neutral values
        assert result["moving_avg_50"] == approx(150.0)  # Current price
        assert result["moving_avg_200"] == approx(150.0)  # Current price
        assert result["rsi"] == approx(50.0)  # Neutral
        assert result["macd"] == approx(0.0)  # Neutral
        assert result["macd_signal"] == approx(0.0)  # Neutral
        assert result["beta"] == approx(1.0)  # Neutral

    def test_should_handle_insufficient_data_for_ma50(self):
        """Test graceful handling when insufficient data for 50-day MA."""
        # Arrange
        short_prices = pd.Series([100, 101, 102, 103, 104])  # Only 5 days
        current_price = 104.0
        data = {"current_price": current_price}

        # Act
        result = calculate_missing_technical_indicators(data, short_prices)

        # Assert - uses current_price fallback
        assert result["moving_avg_50"] == current_price
        assert result["moving_avg_200"] == current_price

    def test_should_handle_insufficient_data_for_rsi(self):
        """Test graceful handling when insufficient data for RSI."""
        # Arrange
        short_prices = pd.Series([100, 101, 102])  # Only 3 days, need 15+
        data = {"current_price": 102.0}

        # Act
        result = calculate_missing_technical_indicators(data, short_prices)

        # Assert - uses neutral RSI
        assert result["rsi"] == approx(50.0)

    def test_should_skip_when_no_current_price(self, sample_prices):
        """Test that calculation is skipped when current_price is missing."""
        # Arrange
        data = {}  # No current_price

        # Act
        result = calculate_missing_technical_indicators(data, sample_prices)

        # Assert - data unchanged, no indicators added
        assert "moving_avg_50" not in result
        assert "rsi" not in result
        assert "macd" not in result

    def test_should_calculate_valid_rsi_range(self, fake):
        """Test that calculated RSI is always in valid range (0-100)."""
        # Arrange - create price series with extreme movements
        prices = pd.Series(
            [
                100,
                110,
                120,
                130,
                140,  # Strong uptrend
                130,
                120,
                110,
                100,
                90,  # Strong downtrend
                95,
                100,
                105,
                100,
                95,  # Sideways
            ]
        )
        data = {"current_price": 95.0}

        # Act
        result = calculate_missing_technical_indicators(data, prices)

        # Assert
        assert 0.0 <= result["rsi"] <= 100.0

    def test_should_handle_macd_crossover_scenarios(self):
        """Test MACD calculation in bullish and bearish scenarios."""
        # Arrange - bullish scenario (prices trending up)
        bullish_prices = pd.Series(range(100, 150))  # Steady uptrend
        data_bullish = {"current_price": 149.0}

        # Act
        result_bullish = calculate_missing_technical_indicators(data_bullish, bullish_prices)

        # Assert - MACD should be positive in uptrend
        assert result_bullish["macd"] > 0

        # Arrange - bearish scenario (prices trending down)
        bearish_prices = pd.Series(range(150, 100, -1))  # Steady downtrend
        data_bearish = {"current_price": 101.0}

        # Act
        result_bearish = calculate_missing_technical_indicators(data_bearish, bearish_prices)

        # Assert - MACD should be negative in downtrend
        assert result_bearish["macd"] < 0


class TestVolatilityFallback:
    """Test cases for volatility derivation in calculate_missing_technical_indicators."""

    @staticmethod
    def _price_series() -> pd.Series:
        return pd.Series([100.0, 101.5, 99.8, 102.3, 101.1, 103.4, 102.0, 104.2, 103.1, 105.0])

    def test_derives_volatility_from_price_history_when_missing(self):
        """Test that volatility is derived from price history when the quant tool didn't supply it."""
        # Arrange
        data = {"current_price": 105.0}

        # Act
        result = calculate_missing_technical_indicators(data, self._price_series())

        # Assert
        assert "volatility" in result
        assert 0.0 < result["volatility"] < 5.0

    def test_does_not_overwrite_existing_volatility(self):
        """Test that a volatility value already supplied by the quant tool is never overwritten."""
        # Arrange
        data = {"current_price": 105.0, "volatility": 0.42}

        # Act
        result = calculate_missing_technical_indicators(data, self._price_series())

        # Assert
        assert result["volatility"] == approx(0.42)

    def test_leaves_volatility_absent_when_no_price_history(self):
        """Test that volatility stays absent when there is no price history to derive it from."""
        # Arrange
        data = {"current_price": 105.0}

        # Act
        result = calculate_missing_technical_indicators(data, None)

        # Assert
        assert "volatility" not in result

    def test_leaves_volatility_absent_when_history_too_short(self):
        """Test that volatility stays absent when price history has fewer than 2 points."""
        # Arrange
        data = {"current_price": 105.0}

        # Act
        result = calculate_missing_technical_indicators(data, pd.Series([100.0]))

        # Assert
        assert "volatility" not in result


class TestGetPriceHistoryFromData:
    """Test cases for get_price_history_from_data function."""

    def test_should_extract_price_history_as_series(self):
        """Test extraction when price_history is a pandas Series."""
        # Arrange
        prices = pd.Series([100, 101, 102, 103, 104])
        data = {"price_history": prices}

        # Act
        result = get_price_history_from_data(data)

        # Assert
        assert result is not None
        assert isinstance(result, pd.Series)
        assert len(result) == 5

    def test_should_extract_price_history_from_dataframe_close(self):
        """Test extraction when price_history is DataFrame with 'Close' column."""
        # Arrange
        prices_df = pd.DataFrame(
            {
                "Open": [99, 100, 101, 102, 103],
                "High": [101, 102, 103, 104, 105],
                "Low": [98, 99, 100, 101, 102],
                "Close": [100, 101, 102, 103, 104],
                "Volume": [1000, 1100, 1200, 1300, 1400],
            }
        )
        data = {"price_history": prices_df}

        # Act
        result = get_price_history_from_data(data)

        # Assert
        assert result is not None
        assert isinstance(result, pd.Series)
        assert list(result) == [100, 101, 102, 103, 104]

    def test_should_extract_price_history_from_dataframe_lowercase(self):
        """Test extraction when DataFrame has 'close' (lowercase) column."""
        # Arrange
        prices_df = pd.DataFrame(
            {
                "open": [99, 100, 101],
                "close": [100, 101, 102],
            }
        )
        data = {"price_history": prices_df}

        # Act
        result = get_price_history_from_data(data)

        # Assert
        assert result is not None
        assert list(result) == [100, 101, 102]

    def test_should_extract_historical_prices(self):
        """Test extraction from 'historical_prices' field."""
        # Arrange
        prices = pd.Series([100, 101, 102])
        data = {"historical_prices": prices}

        # Act
        result = get_price_history_from_data(data)

        # Assert
        assert result is not None
        assert len(result) == 3

    def test_should_return_none_when_no_price_history(self):
        """Test that None is returned when no price history available."""
        # Arrange
        data = {"current_price": 150.0}  # No price history

        # Act
        result = get_price_history_from_data(data)

        # Assert
        assert result is None

    def test_should_extract_from_single_column_dataframe(self):
        """Test extraction when DataFrame has single column."""
        # Arrange
        prices_df = pd.DataFrame({"Price": [100, 101, 102]})
        data = {"price_history": prices_df}

        # Act
        result = get_price_history_from_data(data)

        # Assert
        assert result is not None
        assert len(result) == 3


class TestTechnicalIndicatorAccuracy:
    """Test accuracy of calculated technical indicators against known values."""

    def test_rsi_calculation_accuracy(self):
        """Test RSI calculation against known test case."""
        # Arrange - known RSI test case
        # Prices that should produce RSI around 60 (moderate uptrend)
        prices = pd.Series([44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64])
        data = {"current_price": 45.64}

        # Act
        result = calculate_missing_technical_indicators(data, prices)

        # Assert - RSI should be in moderate uptrend territory
        assert result["rsi"] > 55.0  # Uptrend should show elevated RSI
        assert result["rsi"] < 80.0  # But not extreme

    def test_moving_average_calculation_accuracy(self):
        """Test moving average calculation is accurate."""
        # Arrange - simple price series
        prices = pd.Series([100] * 50 + [110] * 50)  # 50 at 100, then 50 at 110
        data = {"current_price": 110.0}

        # Act
        result = calculate_missing_technical_indicators(data, prices)

        # Assert
        # MA50 uses last 50 values which are all 110
        assert result["moving_avg_50"] == approx(110.0)

        # MA200 is not available (only 100 days), should use current_price
        assert result["moving_avg_200"] == approx(110.0)

    def test_macd_signal_relationship(self):
        """Test that MACD and signal line have correct relationship."""
        # Arrange
        prices = pd.Series(range(100, 150))  # Steady uptrend
        data = {"current_price": 149.0}

        # Act
        result = calculate_missing_technical_indicators(data, prices)

        # Assert
        # In an uptrend, MACD should be above signal line
        assert result["macd"] > result["macd_signal"]
