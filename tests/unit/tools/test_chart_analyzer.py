"""
Unit tests for the ChartAnalyzer class.

Tests chart generation, visual pattern recognition, and LLM-based analysis
with mocked API responses and chart data.
"""

import base64

import pytest
import requests

from finwiz.tools.chart_analyzer import (
    ChartAnalysisResult,
    ChartAnalyzer,
    ChartPattern,
    SupportResistanceLine,
    TrendAnalysis,
    VolumeAnalysis,
)


class TestChartAnalyzer:
    """Test suite for ChartAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a ChartAnalyzer instance for testing."""
        return ChartAnalyzer()

    @pytest.fixture
    def mock_chart_response(self):
        """Mock successful chart API response."""
        # Create a simple PNG-like binary content
        mock_image_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        return mock_image_content

    @pytest.fixture
    def mock_llm_analysis(self):
        """Mock LLM analysis response with comprehensive chart analysis."""
        return """
        Chart Analysis for AAPL (6mo):

        TREND ANALYSIS:
        - Primary trend: The chart shows a clear uptrend over the analyzed period
        - Trend strength: Strong upward momentum with higher highs and higher lows
        - Trend duration: Medium-term uptrend lasting several months
        - Breakout potential: High potential for continued upward movement

        PATTERN IDENTIFICATION:
        - Cup and handle pattern forming in recent months with bullish implications
        - Triangle consolidation pattern visible in mid-period, successfully broken to upside
        - Double bottom pattern completed with strong volume confirmation

        SUPPORT AND RESISTANCE:
        - Strong horizontal support at previous resistance level around $150.50
        - Ascending trendline support connecting recent lows
        - Resistance at psychological $200.00 level with multiple touches
        - Dynamic resistance from 50-day moving average at $185.25

        VOLUME ANALYSIS:
        - Volume trend: Increasing volume on up moves, decreasing on pullbacks
        - Volume confirmation: Strong volume confirmation on breakouts
        - Unusual volume: Significant volume spike during recent breakout
        - Volume pattern: Healthy volume distribution supporting price action

        KEY INSIGHTS:
        - Bullish momentum remains intact with strong institutional support
        - Recent consolidation suggests preparation for next leg higher
        - Volume profile supports continued upward movement
        - Technical indicators align with bullish price action
        - Breakout above $200 could trigger significant rally

        RISK FACTORS:
        - Potential resistance at psychological $200 level
        - Overbought conditions on shorter timeframes
        - Market volatility could impact momentum
        - Gap areas below current price may act as support
        - Economic headwinds could pressure growth stocks
        """

    def test_should_initialize_with_correct_parameters(self, analyzer):
        """Test that analyzer initializes with proper configuration."""
        # Check default parameters
        assert analyzer.default_width == 1200
        assert analyzer.default_height == 800
        assert analyzer.default_theme == "light"

        # Check pattern definitions
        assert "cup_and_handle" in analyzer.chart_patterns
        assert "head_and_shoulders" in analyzer.chart_patterns
        assert "double_top" in analyzer.chart_patterns

        # Verify pattern structure
        for pattern_name, pattern_info in analyzer.chart_patterns.items():
            assert "type" in pattern_info
            assert "description" in pattern_info
            assert "keywords" in pattern_info
            assert isinstance(pattern_info["keywords"], list)

    def test_should_raise_error_without_api_key(self, analyzer, mocker):
        """Test that analyzer raises error when API key is missing."""
        mocker.patch.dict("os.environ", {}, clear=True)
        analyzer_no_key = ChartAnalyzer()

        with pytest.raises(ValueError, match="CHART_IMG_API_KEY environment variable not set"):
            analyzer_no_key.analyze_chart("AAPL")

    def test_should_generate_chart_successfully(self, analyzer, mock_chart_response, mocker):
        """Test successful chart generation."""
        mocker.patch.dict("os.environ", {"CHART_IMG_API_KEY": "test_key"})

        # Mock successful API response
        mock_response = mocker.MagicMock()
        mock_response.status_code = 200
        mock_response.content = mock_chart_response
        mock_response.headers = {"Content-Type": "image/png"}
        mock_response.raise_for_status.return_value = None

        mock_get = mocker.patch("requests.get", return_value=mock_response)

        chart_url = analyzer._generate_chart("AAPL", "6mo", "1day", 900, 500)

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "symbol" in call_args[1]["params"]
        assert call_args[1]["params"]["symbol"] == "AAPL"

        # Verify data URL format
        assert chart_url.startswith("data:image/png;base64,")

        # Verify base64 encoding
        base64_part = chart_url.split(",")[1]
        decoded = base64.b64decode(base64_part)
        assert decoded == mock_chart_response

    def test_should_handle_chart_api_failure(self, analyzer, mocker):
        """Test handling of chart API failures."""
        mocker.patch.dict("os.environ", {"CHART_IMG_API_KEY": "test_key"})

        # Mock API failure
        mocker.patch("requests.get", side_effect=requests.RequestException("API Error"))

        chart_url = analyzer._generate_chart("AAPL", "6mo", "1day", 900, 500)

        assert chart_url.startswith("Error generating chart image")

    def test_should_extract_patterns_correctly(self, analyzer, mock_llm_analysis):
        """Test pattern extraction from LLM analysis."""
        patterns = analyzer._extract_patterns(mock_llm_analysis)

        # Should identify multiple patterns
        assert len(patterns) > 0

        pattern_names = [p.pattern_name for p in patterns]

        # Should find cup and handle pattern
        assert any("Cup And Handle" in name for name in pattern_names)

        # Should find triangle pattern
        assert any("Triangle" in name for name in pattern_names)

        # Verify pattern structure
        for pattern in patterns:
            assert isinstance(pattern, ChartPattern)
            assert pattern.pattern_type in ["bullish", "bearish", "neutral", "continuation", "reversal"]
            assert 0.0 <= pattern.confidence <= 1.0
            assert pattern.completion_status in ["forming", "completed", "broken"]
            assert len(pattern.description) > 0

    def test_should_extract_support_resistance_correctly(self, analyzer, mock_llm_analysis):
        """Test support and resistance extraction."""
        sr_lines = analyzer._extract_support_resistance(mock_llm_analysis)

        # Should identify multiple levels
        assert len(sr_lines) > 0

        # Should find some price levels (the exact ones depend on the extraction logic)
        price_levels = [line.price_level for line in sr_lines]
        # At least one of the mentioned levels should be found
        expected_levels = [150.50, 200.00, 185.25]
        found_levels = [level for level in expected_levels if level in price_levels]
        assert len(found_levels) > 0, f"Expected to find at least one of {expected_levels}, but got {price_levels}"

        # Verify line structure
        for line in sr_lines:
            assert isinstance(line, SupportResistanceLine)
            assert line.line_type in ["support", "resistance"]
            assert line.price_level > 0
            assert 0.0 <= line.strength <= 1.0
            assert line.touches >= 1
            assert line.slope in ["horizontal", "ascending", "descending"]

    def test_should_analyze_volume_correctly(self, analyzer, mock_llm_analysis):
        """Test volume analysis extraction."""
        volume_analysis = analyzer._analyze_volume(mock_llm_analysis)

        # Verify volume analysis structure
        assert isinstance(volume_analysis, VolumeAnalysis)
        assert volume_analysis.volume_trend in ["increasing", "decreasing", "stable"]
        assert isinstance(volume_analysis.volume_confirmation, bool)
        assert isinstance(volume_analysis.unusual_volume_periods, list)

        # Should detect increasing volume trend
        assert volume_analysis.volume_trend == "increasing"

        # Should detect volume confirmation
        assert volume_analysis.volume_confirmation is True

        # Should identify unusual volume periods
        assert len(volume_analysis.unusual_volume_periods) > 0

    def test_should_analyze_trend_correctly(self, analyzer, mock_llm_analysis):
        """Test trend analysis extraction."""
        trend_analysis = analyzer._analyze_trend(mock_llm_analysis)

        # Verify trend analysis structure
        assert isinstance(trend_analysis, TrendAnalysis)
        assert trend_analysis.primary_trend in ["uptrend", "downtrend", "sideways"]
        assert 0.0 <= trend_analysis.trend_strength <= 1.0
        assert trend_analysis.trend_duration in ["short-term", "medium-term", "long-term"]
        assert 0.0 <= trend_analysis.breakout_potential <= 1.0

        # Should detect uptrend
        assert trend_analysis.primary_trend == "uptrend"

        # Should detect strong trend
        assert trend_analysis.trend_strength >= 0.7

        # Should detect medium-term duration
        assert trend_analysis.trend_duration == "medium-term"

    def test_should_extract_key_insights(self, analyzer, mock_llm_analysis):
        """Test key insights extraction."""
        insights = analyzer._extract_key_insights(mock_llm_analysis)

        # Should extract multiple insights
        assert len(insights) > 0
        assert len(insights) <= 5  # Should limit to 5

        # Should contain meaningful insights
        insight_text = " ".join(insights).lower()
        assert "bullish" in insight_text or "momentum" in insight_text

    def test_should_extract_risk_factors(self, analyzer, mock_llm_analysis):
        """Test risk factors extraction."""
        risks = analyzer._extract_risk_factors(mock_llm_analysis)

        # Should extract multiple risk factors
        assert len(risks) > 0
        assert len(risks) <= 5  # Should limit to 5

        # Should contain meaningful risks
        risk_text = " ".join(risks).lower()
        assert "resistance" in risk_text or "overbought" in risk_text or "volatility" in risk_text

    def test_should_determine_chart_signal_correctly(self, analyzer):
        """Test overall signal determination from chart components."""
        # Create bullish components
        bullish_patterns = [
            ChartPattern(
                pattern_name="Cup And Handle",
                pattern_type="bullish",
                confidence=0.8,
                description="Bullish cup and handle",
                timeframe="medium-term",
                completion_status="forming",
            )
        ]

        sr_lines = [
            SupportResistanceLine(
                line_type="support",
                price_level=150.0,
                strength=0.7,
                touches=3,
                slope="horizontal",
                description="Strong support",
            )
        ]

        volume_analysis = VolumeAnalysis(
            volume_trend="increasing",
            volume_confirmation=True,
            unusual_volume_periods=["Recent spike"],
            volume_pattern="Healthy distribution",
        )

        trend_analysis = TrendAnalysis(
            primary_trend="uptrend",
            trend_strength=0.8,
            trend_duration="medium-term",
            trend_channels=["Ascending channel"],
            breakout_potential=0.7,
        )

        signal, confidence = analyzer._determine_chart_signal(bullish_patterns, sr_lines, volume_analysis, trend_analysis)

        # Should generate bullish signal
        assert signal == "buy"
        assert 0.0 <= confidence <= 1.0

    def test_should_determine_bearish_signal(self, analyzer):
        """Test bearish signal determination."""
        # Create bearish components
        bearish_patterns = [
            ChartPattern(
                pattern_name="Head And Shoulders",
                pattern_type="bearish",
                confidence=0.9,
                description="Bearish head and shoulders",
                timeframe="medium-term",
                completion_status="completed",
            )
        ]

        trend_analysis = TrendAnalysis(
            primary_trend="downtrend",
            trend_strength=0.8,
            trend_duration="medium-term",
            trend_channels=[],
            breakout_potential=0.3,
        )

        volume_analysis = VolumeAnalysis(
            volume_trend="decreasing",
            volume_confirmation=False,
            unusual_volume_periods=[],
            volume_pattern="Weak volume",
        )

        signal, confidence = analyzer._determine_chart_signal(bearish_patterns, [], volume_analysis, trend_analysis)

        # Should generate bearish signal
        assert signal == "sell"
        assert confidence > 0.0

    def test_should_determine_neutral_signal(self, analyzer):
        """Test neutral signal determination."""
        # Create neutral/mixed components
        neutral_patterns = []

        trend_analysis = TrendAnalysis(
            primary_trend="sideways",
            trend_strength=0.3,
            trend_duration="short-term",
            trend_channels=[],
            breakout_potential=0.5,
        )

        volume_analysis = VolumeAnalysis(
            volume_trend="stable",
            volume_confirmation=False,
            unusual_volume_periods=[],
            volume_pattern="Normal distribution",
        )

        signal, confidence = analyzer._determine_chart_signal(neutral_patterns, [], volume_analysis, trend_analysis)

        # Should generate neutral signal
        assert signal == "neutral"

    def test_should_perform_complete_analysis(self, analyzer, mock_chart_response, mocker):
        """Test complete chart analysis workflow."""
        mocker.patch.dict("os.environ", {"CHART_IMG_API_KEY": "test_key"})

        # Mock chart generation
        mock_response = mocker.MagicMock()
        mock_response.status_code = 200
        mock_response.content = mock_chart_response
        mock_response.headers = {"Content-Type": "image/png"}
        mock_response.raise_for_status.return_value = None

        mocker.patch("requests.get", return_value=mock_response)

        # Mock LLM analysis (already mocked in the class)
        result = analyzer.analyze_chart("AAPL", "6mo", "1day")

        # Verify result structure
        assert isinstance(result, ChartAnalysisResult)
        assert result.ticker == "AAPL"
        assert result.timeframe == "6mo"
        assert result.chart_url.startswith("data:image/png;base64,")

        # Verify analysis components
        assert isinstance(result.identified_patterns, list)
        assert isinstance(result.support_resistance_lines, list)
        assert isinstance(result.volume_analysis, VolumeAnalysis)
        assert isinstance(result.trend_analysis, TrendAnalysis)

        # Verify overall assessment
        assert result.overall_signal in ["buy", "sell", "neutral"]
        assert 0.0 <= result.signal_confidence <= 1.0
        assert isinstance(result.key_insights, list)
        assert isinstance(result.risk_factors, list)

    def test_should_handle_chart_generation_failure_in_analysis(self, analyzer, mocker):
        """Test handling of chart generation failure during analysis."""
        mocker.patch.dict("os.environ", {"CHART_IMG_API_KEY": "test_key"})

        # Mock chart generation failure
        analyzer._generate_chart = mocker.MagicMock(return_value="Error: API failure")

        with pytest.raises(RuntimeError, match="Failed to generate chart"):
            analyzer.analyze_chart("AAPL")

    def test_should_get_price_context_correctly(self, analyzer):
        """Test price context extraction for classification."""
        text = "Strong support at $150.50 level. Resistance near $200.00 psychological level."

        context_150 = analyzer._get_price_context(text, "150.50")
        context_200 = analyzer._get_price_context(text, "200.00")

        # The method should return the sentence containing the price
        assert context_150 is not None, f"Expected to find context for 150.50 in: {text}"
        assert context_200 is not None, f"Expected to find context for 200.00 in: {text}"

        assert "support" in context_150.lower()
        assert "resistance" in context_200.lower()

    def test_should_generate_chart_url_convenience_method(self, analyzer, mocker):
        """Test convenience method for chart URL generation."""
        mocker.patch.dict("os.environ", {"CHART_IMG_API_KEY": "test_key"})

        # Mock the internal method
        analyzer._generate_chart = mocker.MagicMock(return_value="data:image/png;base64,test")

        url = analyzer.generate_chart_url("AAPL", "1y", "1day", 800, 600, "dark")

        # Verify method was called with correct parameters
        analyzer._generate_chart.assert_called_once_with("AAPL", "1y", "1day", 800, 600)
        assert url == "data:image/png;base64,test"

    def test_should_handle_empty_analysis_text(self, analyzer):
        """Test handling of empty or minimal analysis text."""
        empty_analysis = ""
        minimal_analysis = "Chart shows price movement."

        # Should not crash with empty analysis
        patterns = analyzer._extract_patterns(empty_analysis)
        assert patterns == []

        sr_lines = analyzer._extract_support_resistance(empty_analysis)
        assert sr_lines == []

        # Should handle minimal analysis gracefully
        volume_analysis = analyzer._analyze_volume(minimal_analysis)
        assert isinstance(volume_analysis, VolumeAnalysis)

        trend_analysis = analyzer._analyze_trend(minimal_analysis)
        assert isinstance(trend_analysis, TrendAnalysis)

    def test_should_validate_pattern_confidence_ranges(self, analyzer):
        """Test that pattern confidence values are within valid ranges."""
        # Test with analysis containing multiple pattern mentions
        analysis_with_patterns = """
        Cup and handle pattern with strong bullish implications.
        Triangle consolidation pattern visible.
        Head and shoulders reversal pattern forming.
        Double bottom pattern completed successfully.
        """

        patterns = analyzer._extract_patterns(analysis_with_patterns)

        # All confidence values should be within range
        for pattern in patterns:
            assert 0.0 <= pattern.confidence <= 1.0
            assert pattern.pattern_type in ["bullish", "bearish", "neutral", "continuation", "reversal"]

    def test_should_handle_different_chart_parameters(self, analyzer, mock_chart_response, mocker):
        """Test chart generation with different parameters."""
        mocker.patch.dict("os.environ", {"CHART_IMG_API_KEY": "test_key"})

        # Mock successful response
        mock_response = mocker.MagicMock()
        mock_response.status_code = 200
        mock_response.content = mock_chart_response
        mock_response.headers = {"Content-Type": "image/png"}
        mock_response.raise_for_status.return_value = None

        mock_get = mocker.patch("requests.get", return_value=mock_response)

        # Test with custom parameters
        result = analyzer.analyze_chart(ticker="MSFT", timeframe="1y", interval="1h", width=1600, height=1000)

        # Verify API was called with correct parameters
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert params["symbol"] == "MSFT"
        assert params["range"] == "1y"
        assert params["interval"] == "1h"
        assert params["width"] == 1600
        assert params["height"] == 1000

        # Verify result
        assert result.ticker == "MSFT"
        assert result.timeframe == "1y"
