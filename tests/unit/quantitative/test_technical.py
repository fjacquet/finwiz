"""
Unit tests for technical analysis engine with TA-Lib integration.

Tests cover:
- Individual technical indicator calculations
- Signal generation and accuracy
- Confluence detection capabilities
- Error handling and edge cases
- Data validation and input sanitization
"""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from pytest import approx

from finwiz.quantitative.config import TechnicalIndicator
from finwiz.quantitative.technical import (
    ConfluenceZone,
    SignalStrength,
    SignalType,
    TechnicalAnalysisEngine,
    TechnicalAnalysisResult,
    TechnicalSignal,
    calculate_technical_indicators,
    get_confluence_signals,
)


class TestTechnicalAnalysisEngine:
    """Test suite for TechnicalAnalysisEngine class."""

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        np.random.seed(42)  # For reproducible tests

        # Generate realistic price data with trend
        base_price = 100.0
        prices = []
        for i in range(100):
            # Add some trend and volatility
            trend = i * 0.1
            noise = np.random.normal(0, 2)
            price = base_price + trend + noise
            prices.append(max(price, 1.0))  # Ensure positive prices

        # Generate OHLC from close prices
        data = []
        for i, close in enumerate(prices):
            high = close * (1 + abs(np.random.normal(0, 0.02)))
            low = close * (1 - abs(np.random.normal(0, 0.02)))
            open_price = low + (high - low) * np.random.random()
            volume = int(np.random.uniform(100000, 1000000))

            data.append(
                {
                    "Open": open_price,
                    "High": high,
                    "Low": low,
                    "Close": close,
                    "Volume": volume,
                }
            )

        df = pd.DataFrame(data, index=dates)
        return df

    @pytest.fixture
    def engine(self) -> TechnicalAnalysisEngine:
        """Create TechnicalAnalysisEngine instance for testing."""
        return TechnicalAnalysisEngine()

    def test_engine_initialization(self, engine):
        """Test engine initialization with default configuration."""
        assert engine is not None
        assert hasattr(engine, "config")
        assert hasattr(engine, "default_indicators")
        assert TechnicalIndicator.SMA in engine.default_indicators
        assert TechnicalIndicator.RSI in engine.default_indicators

    def test_calculate_sma_basic(self, engine, sample_data):
        """Test basic SMA calculation."""
        periods = [20, 50]
        result = engine.basic_indicators.calculate_sma(sample_data, periods)

        assert result.indicator_name == "SMA"
        assert "SMA_20" in result.raw_values
        assert "SMA_50" in result.raw_values
        assert len(result.signals) >= 0  # Should generate at least some signals
        assert result.metadata["periods"] == periods

    def test_calculate_sma_signals(self, engine, sample_data):
        """Test SMA signal generation logic."""
        periods = [20]
        result = engine.basic_indicators.calculate_sma(sample_data, periods)

        # Should have at least one signal
        assert len(result.signals) > 0

        signal = result.signals[0]
        assert isinstance(signal, TechnicalSignal)
        assert signal.indicator == "SMA_20"
        assert signal.signal_type in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
        assert 0.0 <= signal.confidence <= 1.0
        assert signal.price_level > 0

    def test_calculate_sma_insufficient_data(self, engine):
        """Test SMA calculation with insufficient data."""
        # Create data with only 10 rows
        short_data = pd.DataFrame(
            {
                "Open": [100] * 10,
                "High": [105] * 10,
                "Low": [95] * 10,
                "Close": [102] * 10,
                "Volume": [100000] * 10,
            }
        )

        periods = [20]  # Need 20 periods but only have 10
        result = engine.basic_indicators.calculate_sma(short_data, periods)

        # Should handle gracefully and not crash
        assert result.indicator_name == "SMA"
        assert len(result.raw_values) == 0  # No values calculated

    def test_calculate_ema_basic(self, engine, sample_data):
        """Test basic EMA calculation."""
        periods = [12, 26]
        result = engine.basic_indicators.calculate_ema(sample_data, periods)

        assert result.indicator_name == "EMA"
        assert "EMA_12" in result.raw_values
        assert "EMA_26" in result.raw_values
        assert len(result.signals) >= 0
        assert result.metadata["periods"] == periods

    def test_calculate_rsi_basic(self, engine, sample_data):
        """Test basic RSI calculation."""
        result = engine.basic_indicators.calculate_rsi(sample_data, period=14, overbought=70, oversold=30)

        assert result.indicator_name == "RSI"
        assert "RSI" in result.raw_values
        assert len(result.signals) > 0
        assert result.metadata["period"] == 14
        assert result.metadata["overbought"] == 70
        assert result.metadata["oversold"] == 30

    def test_calculate_rsi_signals(self, engine):
        """Test RSI signal generation for different conditions."""
        # Create data that should generate overbought signal
        overbought_data = pd.DataFrame(
            {
                "Open": [100 + i for i in range(20)],
                "High": [105 + i for i in range(20)],
                "Low": [95 + i for i in range(20)],
                "Close": [100 + i * 2 for i in range(20)],  # Strong uptrend
                "Volume": [100000] * 20,
            }
        )

        result = engine.basic_indicators.calculate_rsi(overbought_data, period=14)

        assert len(result.signals) > 0
        signal = result.signals[0]

        # With strong uptrend, should likely be overbought
        assert signal.signal_type in [SignalType.SELL, SignalType.HOLD]
        assert "rsi_value" in signal.metadata

    def test_calculate_rsi_insufficient_data(self, engine):
        """Test RSI calculation with insufficient data."""
        short_data = pd.DataFrame(
            {
                "Close": [100, 101, 102],  # Only 3 data points
            }
        )

        with pytest.raises(ValueError, match="Insufficient data for RSI"):
            engine.basic_indicators.calculate_rsi(short_data, period=14)

    def test_calculate_macd_basic(self, engine, sample_data):
        """Test basic MACD calculation."""
        result = engine.advanced_indicators.calculate_macd(sample_data, fast=12, slow=26, signal=9)

        assert result.indicator_name == "MACD"
        assert "MACD_line" in result.raw_values
        assert "MACD_signal" in result.raw_values
        assert "MACD_histogram" in result.raw_values
        assert len(result.signals) >= 0
        assert result.metadata["fast"] == 12
        assert result.metadata["slow"] == 26
        assert result.metadata["signal"] == 9

    def test_calculate_macd_signals(self, engine, sample_data):
        """Test MACD signal generation."""
        result = engine.advanced_indicators.calculate_macd(sample_data)

        if len(result.signals) > 0:
            signal = result.signals[0]
            assert signal.indicator == "MACD"
            assert signal.signal_type in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
            assert "macd_line" in signal.metadata
            assert "signal_line" in signal.metadata
            assert "histogram" in signal.metadata

    def test_calculate_bollinger_bands_basic(self, engine, sample_data):
        """Test basic Bollinger Bands calculation."""
        result = engine.advanced_indicators.calculate_bollinger_bands(sample_data, period=20, std_dev=2.0)

        assert result.indicator_name == "Bollinger_Bands"
        assert "upper_band" in result.raw_values
        assert "middle_band" in result.raw_values
        assert "lower_band" in result.raw_values
        assert len(result.signals) >= 0
        assert result.metadata["period"] == 20
        assert result.metadata["std_dev"] == approx(2.0)

    def test_calculate_bollinger_bands_signals(self, engine):
        """Test Bollinger Bands signal generation for extreme conditions."""
        # Create data where price breaks above upper band
        base_price = 100
        data = []
        for i in range(25):
            if i < 20:
                close = base_price + np.random.normal(0, 1)
            else:
                close = base_price + 10  # Price spike above bands

            data.append(
                {
                    "Open": close,
                    "High": close * 1.01,
                    "Low": close * 0.99,
                    "Close": close,
                    "Volume": 100000,
                }
            )

        df = pd.DataFrame(data)
        result = engine.advanced_indicators.calculate_bollinger_bands(df, period=20)

        if len(result.signals) > 0:
            signal = result.signals[0]
            assert signal.indicator == "Bollinger_Bands"
            assert "upper_band" in signal.metadata
            assert "lower_band" in signal.metadata
            assert "price_position" in signal.metadata

    def test_calculate_atr_basic(self, engine, sample_data):
        """Test basic ATR calculation."""
        result = engine.specialized_indicators.calculate_atr(sample_data, period=14)

        assert result.indicator_name == "ATR"
        assert "ATR" in result.raw_values
        assert len(result.signals) >= 0
        assert result.metadata["period"] == 14

    def test_calculate_atr_volatility_detection(self, engine):
        """Test ATR volatility detection."""
        # Create high volatility data
        high_vol_data = []
        for i in range(20):
            base = 100
            volatility = 10  # High volatility
            close = base + np.random.normal(0, volatility)
            high = close + abs(np.random.normal(0, volatility))
            low = close - abs(np.random.normal(0, volatility))

            high_vol_data.append(
                {
                    "Open": close,
                    "High": high,
                    "Low": low,
                    "Close": close,
                    "Volume": 100000,
                }
            )

        df = pd.DataFrame(high_vol_data)
        result = engine.specialized_indicators.calculate_atr(df, period=14)

        if len(result.signals) > 0:
            signal = result.signals[0]
            assert signal.indicator == "ATR"
            assert "atr_value" in signal.metadata
            assert "atr_percentage" in signal.metadata
            # High volatility should be detected
            assert signal.metadata["atr_percentage"] > 2.0

    def test_calculate_fibonacci_retracements_basic(self, engine, sample_data):
        """Test basic Fibonacci retracements calculation."""
        result = engine.specialized_indicators.calculate_fibonacci_retracements(sample_data, lookback_period=50)

        assert result.indicator_name == "Fibonacci"
        assert "0.0" in result.raw_values
        assert "23.6" in result.raw_values
        assert "38.2" in result.raw_values
        assert "50.0" in result.raw_values
        assert "61.8" in result.raw_values
        assert "100.0" in result.raw_values
        assert result.metadata["lookback_period"] == 50

    def test_calculate_fibonacci_retracements_signals(self, engine):
        """Test Fibonacci retracements signal generation."""
        # Create data with clear swing high and low
        swing_data = []
        for i in range(60):
            if i < 20:
                close = 100 + i * 2  # Uptrend to swing high
            elif i < 40:
                close = 140 - (i - 20) * 1.5  # Retracement
            else:
                close = 110 + (i - 40) * 0.5  # Continuation

            high = close * 1.01
            low = close * 0.99

            swing_data.append(
                {
                    "Open": close,
                    "High": high,
                    "Low": low,
                    "Close": close,
                    "Volume": 100000,
                }
            )

        df = pd.DataFrame(swing_data)
        result = engine.specialized_indicators.calculate_fibonacci_retracements(df, lookback_period=50)

        # Should have calculated Fibonacci levels
        assert "swing_high" in result.metadata
        assert "swing_low" in result.metadata
        assert result.metadata["swing_high"] > result.metadata["swing_low"]

    def test_calculate_fibonacci_insufficient_data(self, engine):
        """Test Fibonacci calculation with insufficient data."""
        short_data = pd.DataFrame(
            {
                "Open": [100] * 10,
                "High": [105] * 10,
                "Low": [95] * 10,
                "Close": [102] * 10,
                "Volume": [100000] * 10,
            }
        )

        with pytest.raises(ValueError, match="Insufficient data for Fibonacci"):
            engine.specialized_indicators.calculate_fibonacci_retracements(short_data, lookback_period=50)

    def test_confluence_detection(self, engine):
        """Test confluence zone detection."""
        # Create signals that should form confluence
        signals = [
            TechnicalSignal(
                indicator="RSI",
                signal_type=SignalType.BUY,
                strength=SignalStrength.STRONG,
                confidence=0.8,
                timestamp=datetime.now(),
                price_level=100.0,
                description="RSI oversold",
                metadata={},
            ),
            TechnicalSignal(
                indicator="MACD",
                signal_type=SignalType.BUY,
                strength=SignalStrength.MODERATE,
                confidence=0.7,
                timestamp=datetime.now(),
                price_level=100.0,
                description="MACD bullish crossover",
                metadata={},
            ),
        ]

        # Create sample data for confluence detection
        data = pd.DataFrame(
            {
                "Close": [100.0],
            }
        )

        confluence_zones = engine._detect_confluence_zones(signals, data)

        assert len(confluence_zones) > 0
        zone = confluence_zones[0]
        assert isinstance(zone, ConfluenceZone)
        assert zone.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]
        assert len(zone.contributing_signals) == 2
        assert zone.confidence > 0.7  # Should be boosted for confluence

    def test_overall_signal_generation(self, engine):
        """Test overall signal generation from multiple indicators."""
        # Create mixed signals
        signals = [
            TechnicalSignal(
                indicator="RSI",
                signal_type=SignalType.BUY,
                strength=SignalStrength.STRONG,
                confidence=0.8,
                timestamp=datetime.now(),
                price_level=100.0,
                description="Test signal",
                metadata={},
            ),
            TechnicalSignal(
                indicator="MACD",
                signal_type=SignalType.SELL,
                strength=SignalStrength.MODERATE,
                confidence=0.6,
                timestamp=datetime.now(),
                price_level=100.0,
                description="Test signal",
                metadata={},
            ),
            TechnicalSignal(
                indicator="SMA",
                signal_type=SignalType.BUY,
                strength=SignalStrength.MODERATE,
                confidence=0.7,
                timestamp=datetime.now(),
                price_level=100.0,
                description="Test signal",
                metadata={},
            ),
        ]

        overall_signal, confidence, strength = engine._generate_overall_signal(signals)

        assert overall_signal in [SignalType.BUY, SignalType.SELL, SignalType.HOLD, SignalType.STRONG_BUY, SignalType.STRONG_SELL]
        assert 0.0 <= confidence <= 1.0
        assert strength in [
            SignalStrength.VERY_WEAK,
            SignalStrength.WEAK,
            SignalStrength.MODERATE,
            SignalStrength.STRONG,
            SignalStrength.VERY_STRONG,
        ]

    @pytest.fixture
    def simple_ohlcv_data(self) -> pd.DataFrame:
        """Create simple OHLCV data for convenience function testing."""
        return pd.DataFrame(
            {
                "Open": [100 + i for i in range(50)],
                "High": [105 + i for i in range(50)],
                "Low": [95 + i for i in range(50)],
                "Close": [102 + i for i in range(50)],
                "Volume": [100000] * 50,
            }
        )

    def test_calculate_technical_indicators_function(self, simple_ohlcv_data):
        """Test calculate_technical_indicators convenience function."""
        result = calculate_technical_indicators(simple_ohlcv_data, "AAPL", "1d")

        assert isinstance(result, TechnicalAnalysisResult)
        assert result.symbol == "AAPL"
        assert result.timeframe == "1d"
        assert len(result.indicator_results) > 0  # Should have default indicators

    def test_get_confluence_signals_function(self, simple_ohlcv_data):
        """Test get_confluence_signals convenience function."""
        confluence_zones = get_confluence_signals(simple_ohlcv_data, "AAPL", min_confluence=2)

        assert isinstance(confluence_zones, list)
        # All returned zones should have at least min_confluence signals
        for zone in confluence_zones:
            assert len(zone.contributing_signals) >= 2


class TestSignalAccuracy:
    """Test suite for signal accuracy and edge cases."""

    def test_rsi_overbought_signal_accuracy(self):
        """Test RSI generates correct overbought signals."""
        engine = TechnicalAnalysisEngine()

        # Create strongly trending up data that should result in overbought RSI
        trending_data = []
        for i in range(30):
            close = 100 + i * 2  # Strong uptrend
            trending_data.append(
                {
                    "Open": close,
                    "High": close * 1.01,
                    "Low": close * 0.99,
                    "Close": close,
                    "Volume": 100000,
                }
            )

        df = pd.DataFrame(trending_data)
        result = engine.basic_indicators.calculate_rsi(df, period=14, overbought=70, oversold=30)

        # Should generate at least one signal
        assert len(result.signals) > 0

        # With strong uptrend, RSI should be high and potentially overbought
        rsi_value = result.signals[0].metadata["rsi_value"]
        assert rsi_value > 50  # Should be above midline with uptrend

    def test_macd_crossover_detection(self):
        """Test MACD crossover detection accuracy."""
        engine = TechnicalAnalysisEngine()

        # Create data with a clear trend change that should generate MACD crossover
        crossover_data = []
        for i in range(50):
            if i < 25:
                close = 100 - i * 0.5  # Downtrend first
            else:
                close = 87.5 + (i - 25) * 1.0  # Then uptrend

            crossover_data.append(
                {
                    "Open": close,
                    "High": close * 1.01,
                    "Low": close * 0.99,
                    "Close": close,
                    "Volume": 100000,
                }
            )

        df = pd.DataFrame(crossover_data)
        result = engine.advanced_indicators.calculate_macd(df, fast=12, slow=26, signal=9)

        # Should generate signals
        assert len(result.signals) > 0

        # Verify MACD values are calculated
        assert "MACD_line" in result.raw_values
        assert "MACD_signal" in result.raw_values
        assert "MACD_histogram" in result.raw_values

    def test_bollinger_bands_squeeze_detection(self):
        """Test Bollinger Bands squeeze and breakout detection."""
        engine = TechnicalAnalysisEngine()

        # Create data with low volatility followed by breakout
        squeeze_data = []
        for i in range(30):
            if i < 20:
                close = 100 + np.random.normal(0, 0.1)  # Low volatility
            else:
                close = 100 + (i - 20) * 2  # Breakout

            squeeze_data.append(
                {
                    "Open": close,
                    "High": close * 1.005,
                    "Low": close * 0.995,
                    "Close": close,
                    "Volume": 100000,
                }
            )

        df = pd.DataFrame(squeeze_data)
        result = engine.advanced_indicators.calculate_bollinger_bands(df, period=20, std_dev=2.0)

        # Should generate signals
        assert len(result.signals) > 0

        # Verify bands are calculated
        assert "upper_band" in result.raw_values
        assert "middle_band" in result.raw_values
        assert "lower_band" in result.raw_values

    def test_signal_strength_consistency(self):
        """Test that signal strength is consistent with confidence levels."""
        engine = TechnicalAnalysisEngine()

        # Create sample data
        data = pd.DataFrame(
            {
                "Open": [100 + i for i in range(30)],
                "High": [105 + i for i in range(30)],
                "Low": [95 + i for i in range(30)],
                "Close": [102 + i for i in range(30)],
                "Volume": [100000] * 30,
            }
        )

        result = engine.analyze_symbol(data, "TEST", "1d")

        # Check that signal strength correlates with confidence
        for indicator_result in result.indicator_results.values():
            for signal in indicator_result.signals:
                if signal.strength == SignalStrength.VERY_STRONG:
                    assert signal.confidence >= 0.7
                elif signal.strength == SignalStrength.STRONG:
                    assert signal.confidence >= 0.5
                # Weak signals can have any confidence level


if __name__ == "__main__":
    pytest.main([__file__])
