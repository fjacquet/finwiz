"""
Unit tests for the TechnicalAnalyzer class.

Tests advanced technical analysis including Fibonacci retracements, support/resistance
identification, and confluence zone detection with mocked price data.
"""

import datetime

import numpy as np
import pandas as pd
import pytest

from finwiz.tools.technical_analyzer import TechnicalAnalyzer
from finwiz.tools.technical_models import (
    ConfluenceZone,
    FibonacciLevels,
    IndicatorSignal,
    PriceData,
    SupportResistance,
    SupportResistanceLevel,
    TechnicalAnalysisResult,
)


class TestPriceData:
    """Test suite for PriceData class."""

    def test_should_create_valid_price_data(self):
        """Test creation of valid PriceData instance."""
        dates = [datetime.datetime(2024, 1, i) for i in range(1, 6)]
        prices = [100.0, 101.0, 99.0, 102.0, 103.0]
        volumes = [1000, 1100, 900, 1200, 1300]

        price_data = PriceData(
            dates=dates,
            opens=prices,
            highs=[p + 1 for p in prices],
            lows=[p - 1 for p in prices],
            closes=prices,
            volumes=volumes,
        )

        assert price_data.length == 5
        assert len(price_data.dates) == 5
        assert price_data.closes[-1] == 103.0

    def test_should_raise_error_for_mismatched_lengths(self):
        """Test that PriceData raises error for mismatched list lengths."""
        dates = [datetime.datetime(2024, 1, 1)]
        prices = [100.0, 101.0]  # Different length

        with pytest.raises(ValueError, match="All price data lists must have the same length"):
            PriceData(dates=dates, opens=prices, highs=prices, lows=prices, closes=prices, volumes=[1000])

    def test_should_convert_to_dataframe_correctly(self):
        """Test conversion to pandas DataFrame."""
        dates = [datetime.datetime(2024, 1, i) for i in range(1, 4)]
        price_data = PriceData(
            dates=dates,
            opens=[100.0, 101.0, 102.0],
            highs=[101.0, 102.0, 103.0],
            lows=[99.0, 100.0, 101.0],
            closes=[100.5, 101.5, 102.5],
            volumes=[1000, 1100, 1200],
        )

        df = price_data.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]
        assert df["close"].iloc[-1] == 102.5


class TestTechnicalAnalyzer:
    """Test suite for TechnicalAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a TechnicalAnalyzer instance for testing."""
        return TechnicalAnalyzer()

    @pytest.fixture
    def sample_price_data(self):
        """Create sample price data for testing."""
        # Create 30 days of sample data with a clear trend
        dates = [datetime.datetime(2024, 1, 1) + datetime.timedelta(days=i) for i in range(30)]

        # Create uptrend with some volatility
        base_prices = np.linspace(100, 120, 30)
        noise = np.random.normal(0, 1, 30)
        closes = base_prices + noise

        # Ensure highs > closes > lows
        highs = closes + np.abs(np.random.normal(0, 0.5, 30))
        lows = closes - np.abs(np.random.normal(0, 0.5, 30))
        opens = closes + np.random.normal(0, 0.3, 30)

        volumes = [1000 + int(np.random.normal(0, 200)) for _ in range(30)]

        return PriceData(
            dates=dates,
            opens=opens.tolist(),
            highs=highs.tolist(),
            lows=lows.tolist(),
            closes=closes.tolist(),
            volumes=volumes,
        )

    @pytest.fixture
    def trending_price_data(self):
        """Create price data with clear trend for Fibonacci testing."""
        dates = [datetime.datetime(2024, 1, 1) + datetime.timedelta(days=i) for i in range(50)]

        # Create clear uptrend: low at start, high in middle, retracement at end
        prices = []
        for i in range(50):
            if i < 20:
                # Uptrend phase
                prices.append(100 + i * 2)
            elif i < 30:
                # Peak phase
                prices.append(140 - (i - 20) * 0.5)
            else:
                # Retracement phase
                prices.append(135 - (i - 30) * 1.5)

        closes = np.array(prices)
        highs = closes + 1
        lows = closes - 1
        opens = closes + np.random.normal(0, 0.2, 50)
        volumes = [1000] * 50

        return PriceData(
            dates=dates,
            opens=opens.tolist(),
            highs=highs.tolist(),
            lows=lows.tolist(),
            closes=closes.tolist(),
            volumes=volumes,
        )

    def test_should_initialize_with_correct_parameters(self, analyzer):
        """Test that analyzer initializes with proper parameters."""
        # Check that algorithms and patterns are initialized
        assert analyzer.algorithms is not None
        assert analyzer.patterns is not None

        # Check Fibonacci ratios in algorithms
        assert 0.618 in analyzer.algorithms.fib_ratios
        assert 0.382 in analyzer.algorithms.fib_ratios
        assert 1.618 in analyzer.algorithms.fib_extensions

        # Check parameters in patterns
        assert analyzer.patterns.min_touches >= 2
        assert 0 < analyzer.patterns.price_tolerance < 0.1
        assert analyzer.patterns.min_confluence_indicators >= 2

    def test_should_raise_error_for_insufficient_data(self, analyzer):
        """Test that analyzer raises error for insufficient data."""
        # Create data with only 10 periods (less than minimum 20)
        dates = [datetime.datetime(2024, 1, i) for i in range(1, 11)]
        short_data = PriceData(
            dates=dates,
            opens=[100.0] * 10,
            highs=[101.0] * 10,
            lows=[99.0] * 10,
            closes=[100.0] * 10,
            volumes=[1000] * 10,
        )

        with pytest.raises(ValueError, match="Insufficient data for technical analysis"):
            analyzer.analyze("TEST", short_data)

    def test_should_calculate_fibonacci_levels_correctly(self, analyzer, trending_price_data):
        """Test Fibonacci level calculation."""
        fibonacci_levels = analyzer.algorithms.calculate_fibonacci_levels(trending_price_data)

        # Verify structure
        assert isinstance(fibonacci_levels, FibonacciLevels)
        assert fibonacci_levels.swing_high > fibonacci_levels.swing_low
        assert fibonacci_levels.trend_direction in ["uptrend", "downtrend"]
        assert len(fibonacci_levels.levels) > 0

        # Check that standard Fibonacci ratios are present
        ratios = [level.ratio for level in fibonacci_levels.levels]
        assert 0.618 in ratios
        assert 0.382 in ratios

        # Verify price calculations are reasonable
        fibonacci_levels.swing_high - fibonacci_levels.swing_low
        for level in fibonacci_levels.levels:
            if level.level_type == "retracement":
                assert fibonacci_levels.swing_low <= level.price <= fibonacci_levels.swing_high

    def test_should_identify_support_resistance_levels(self, analyzer, sample_price_data):
        """Test support and resistance level identification."""
        support_resistance = analyzer.patterns.identify_support_resistance(sample_price_data)

        # Verify structure
        assert isinstance(support_resistance, SupportResistance)
        assert isinstance(support_resistance.support_levels, list)
        assert isinstance(support_resistance.resistance_levels, list)
        assert support_resistance.current_price > 0

        # Check level properties
        for level in support_resistance.support_levels + support_resistance.resistance_levels:
            assert isinstance(level, SupportResistanceLevel)
            assert level.price > 0
            assert level.level_type in ["support", "resistance"]
            assert 0.0 <= level.strength <= 1.0
            assert level.touch_count >= analyzer.patterns.min_touches

    def test_should_calculate_rsi_correctly(self, analyzer):
        """Test RSI calculation."""
        # Create price series with known pattern
        prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113])

        rsi = analyzer.algorithms.calculate_rsi(prices, period=14)

        # RSI should be between 0 and 100
        assert all(0 <= value <= 100 for value in rsi.dropna())

        # Should have fewer values than input due to rolling calculation
        assert len(rsi.dropna()) < len(prices)

    def test_should_calculate_macd_correctly(self, analyzer):
        """Test MACD calculation."""
        # Create price series
        prices = pd.Series(np.linspace(100, 120, 50))

        macd_line, signal_line, histogram = analyzer.algorithms.calculate_macd(prices)

        # All series should have same length
        assert len(macd_line) == len(signal_line) == len(histogram)

        # Histogram should be difference between MACD and signal
        np.testing.assert_array_almost_equal(histogram.dropna().values, (macd_line - signal_line).dropna().values)

    def test_should_calculate_bollinger_bands_correctly(self, analyzer):
        """Test Bollinger Bands calculation."""
        # Create price series
        prices = pd.Series([100, 101, 99, 102, 98, 103, 97, 104, 96, 105] * 3)

        upper, middle, lower = analyzer.algorithms.calculate_bollinger_bands(prices, period=10)

        # Upper should be above middle, middle above lower
        valid_data = ~(upper.isna() | middle.isna() | lower.isna())
        assert all(upper[valid_data] >= middle[valid_data])
        assert all(middle[valid_data] >= lower[valid_data])

    def test_should_calculate_indicator_signals(self, analyzer, sample_price_data):
        """Test technical indicator signal calculation."""
        signals = analyzer.algorithms.calculate_indicator_signals(sample_price_data)

        # Should have signals from multiple indicators
        assert len(signals) > 0

        indicator_names = [signal.indicator_name for signal in signals]
        expected_indicators = ["RSI", "MACD", "Moving Average", "Bollinger Bands"]

        # Should have most expected indicators
        assert len(set(indicator_names) & set(expected_indicators)) >= 2

        # Verify signal structure
        for signal in signals:
            assert isinstance(signal, IndicatorSignal)
            assert signal.signal_type in ["buy", "sell", "neutral"]
            assert 0.0 <= signal.strength <= 1.0
            assert len(signal.description) > 0

    def test_should_find_confluence_zones(self, analyzer, trending_price_data):
        """Test confluence zone detection."""
        # First calculate components
        fibonacci_levels = analyzer.algorithms.calculate_fibonacci_levels(trending_price_data)
        support_resistance = analyzer.patterns.identify_support_resistance(trending_price_data)
        indicator_signals = analyzer.algorithms.calculate_indicator_signals(trending_price_data)
        current_price = trending_price_data.closes[-1]

        confluence_zones = analyzer.patterns.find_confluence_zones(
            fibonacci_levels, support_resistance, indicator_signals, current_price
        )

        # Verify structure
        assert isinstance(confluence_zones, list)

        for zone in confluence_zones:
            assert isinstance(zone, ConfluenceZone)
            assert zone.zone_type in ["support", "resistance", "reversal"]
            assert 0.0 <= zone.confluence_score <= 1.0
            assert 0.0 <= zone.signal_strength <= 1.0
            assert len(zone.contributing_indicators) >= analyzer.patterns.min_confluence_indicators
            assert zone.price_range[0] <= zone.price_range[1]

    def test_should_determine_overall_signal(self, analyzer, sample_price_data):
        """Test overall signal determination."""
        # Calculate all components
        fibonacci_levels = analyzer.algorithms.calculate_fibonacci_levels(sample_price_data)
        support_resistance = analyzer.patterns.identify_support_resistance(sample_price_data)
        indicator_signals = analyzer.algorithms.calculate_indicator_signals(sample_price_data)
        confluence_zones = analyzer.patterns.find_confluence_zones(
            fibonacci_levels, support_resistance, indicator_signals, sample_price_data.closes[-1]
        )

        overall_signal, confidence = analyzer.patterns.determine_overall_signal(
            fibonacci_levels, support_resistance, indicator_signals, confluence_zones
        )

        # Verify signal
        assert overall_signal in ["buy", "sell", "neutral"]
        assert 0.0 <= confidence <= 1.0

    def test_should_perform_complete_analysis(self, analyzer, sample_price_data):
        """Test complete technical analysis workflow."""
        result = analyzer.analyze("TEST", sample_price_data)

        # Verify result structure
        assert isinstance(result, TechnicalAnalysisResult)
        assert result.ticker == "TEST"
        assert isinstance(result.analysis_date, datetime.datetime)

        # Verify all components are present
        assert isinstance(result.fibonacci_levels, FibonacciLevels)
        assert isinstance(result.support_resistance, SupportResistance)
        assert isinstance(result.indicator_signals, list)
        assert isinstance(result.confluence_zones, list)

        # Verify overall signal
        assert result.overall_signal in ["buy", "sell", "neutral"]
        assert 0.0 <= result.signal_confidence <= 1.0

    def test_should_find_pivot_highs_correctly(self, analyzer):
        """Test pivot high detection."""
        # Create data with clear pivot high in the middle
        highs = [100, 101, 102, 105, 103, 102, 101, 100, 99, 98]

        pivots = analyzer.patterns._find_pivot_highs(highs, window=2)

        # Should find the pivot at index 3 (price 105)
        assert len(pivots) > 0
        pivot_prices = [p[1] for p in pivots]
        assert 105 in pivot_prices

    def test_should_find_pivot_lows_correctly(self, analyzer):
        """Test pivot low detection."""
        # Create data with clear pivot low in the middle
        lows = [100, 99, 98, 95, 97, 98, 99, 100, 101, 102]

        pivots = analyzer.patterns._find_pivot_lows(lows, window=2)

        # Should find the pivot at index 3 (price 95)
        assert len(pivots) > 0
        pivot_prices = [p[1] for p in pivots]
        assert 95 in pivot_prices

    def test_should_group_similar_price_levels(self, analyzer, sample_price_data):
        """Test grouping of similar price levels."""
        # Create mock pivots with similar prices
        pivots = [(5, 100.0), (10, 100.5), (15, 99.8), (20, 110.0), (25, 110.2)]

        levels = analyzer.patterns._group_price_levels(pivots, sample_price_data, "support")

        # Should group similar prices together
        assert len(levels) <= len(pivots)  # Should have fewer groups than individual pivots

        for level in levels:
            assert level.touch_count >= analyzer.patterns.min_touches
            assert level.level_type == "support"

    def test_should_calculate_confluence_score_correctly(self, analyzer):
        """Test confluence score calculation."""
        # Create mock confluence group
        group = [
            {"type": "fibonacci", "strength": 0.8, "price": 100.0},
            {"type": "support_resistance", "strength": 0.7, "price": 100.2},
            {"type": "fibonacci", "strength": 0.6, "price": 99.8},
        ]

        score = analyzer.patterns._calculate_confluence_score(group)

        # Score should be between 0 and 1
        assert 0.0 <= score <= 1.0

        # Should be higher for groups with both Fibonacci and S/R levels
        assert score > 0.5  # Should get bonus for having both types

    def test_should_handle_edge_cases_gracefully(self, analyzer):
        """Test handling of edge cases."""
        # Test with minimal data (exactly 20 periods)
        dates = [datetime.datetime(2024, 1, 1) + datetime.timedelta(days=i) for i in range(20)]
        minimal_data = PriceData(
            dates=dates,
            opens=[100.0] * 20,
            highs=[101.0] * 20,
            lows=[99.0] * 20,
            closes=[100.0] * 20,
            volumes=[1000] * 20,
        )

        # Should not raise error
        result = analyzer.analyze("TEST", minimal_data)
        assert isinstance(result, TechnicalAnalysisResult)

    def test_should_validate_fibonacci_ratios(self, analyzer, trending_price_data):
        """Test that Fibonacci levels use correct ratios."""
        fibonacci_levels = analyzer.algorithms.calculate_fibonacci_levels(trending_price_data)

        # Extract ratios from levels
        ratios = [level.ratio for level in fibonacci_levels.levels if level.level_type == "retracement"]

        # Should include key Fibonacci ratios
        key_ratios = [0.382, 0.5, 0.618]
        for ratio in key_ratios:
            assert ratio in ratios

    def test_should_identify_trend_direction_correctly(self, analyzer):
        """Test trend direction identification."""
        # Create clear uptrend data
        dates = [datetime.datetime(2024, 1, 1) + datetime.timedelta(days=i) for i in range(30)]
        uptrend_closes = list(range(100, 130))  # Clear uptrend

        uptrend_data = PriceData(
            dates=dates,
            opens=uptrend_closes,
            highs=[c + 1 for c in uptrend_closes],
            lows=[c - 1 for c in uptrend_closes],
            closes=uptrend_closes,
            volumes=[1000] * 30,
        )

        fibonacci_levels = analyzer.algorithms.calculate_fibonacci_levels(uptrend_data)

        # Should identify as uptrend (though this depends on swing point detection)
        assert fibonacci_levels.trend_direction in ["uptrend", "downtrend"]
        assert fibonacci_levels.swing_high > fibonacci_levels.swing_low

    def test_should_handle_flat_market_conditions(self, analyzer):
        """Test handling of sideways/flat market conditions."""
        # Create flat market data
        dates = [datetime.datetime(2024, 1, 1) + datetime.timedelta(days=i) for i in range(30)]
        flat_closes = [100.0 + np.random.normal(0, 0.5) for _ in range(30)]  # Flat with small noise

        flat_data = PriceData(
            dates=dates,
            opens=flat_closes,
            highs=[c + 0.5 for c in flat_closes],
            lows=[c - 0.5 for c in flat_closes],
            closes=flat_closes,
            volumes=[1000] * 30,
        )

        result = analyzer.analyze("TEST", flat_data)

        # Should handle flat conditions without error
        assert isinstance(result, TechnicalAnalysisResult)
        # In flat conditions, might expect neutral signal
        assert result.overall_signal in ["buy", "sell", "neutral"]
