"""
Unit tests for the Enhanced Twelve Data Tool.

Tests technical indicator calculations, API integration, rate limiting,
and error handling with mocked API responses.
"""

import asyncio

import pytest

from finwiz.tools.enhanced_twelve_data_tool import (
    BollingerBandsData,
    MACDData,
    RSIData,
    StochasticData,
    TechnicalIndicatorSummary,
    TwelveDataTool,
)
from tests.fixtures.api_test_mocks import APITestMocks


class TestTwelveDataTool:
    """Test suite for TwelveDataTool class."""

    @pytest.fixture
    def tool(self):
        """Create a TwelveDataTool instance for testing."""
        return TwelveDataTool()

    @pytest.fixture
    def mock_rsi_response(self):
        """Mock RSI API response."""
        return {
            "meta": {"symbol": "AAPL", "interval": "1day", "time_period": 14},
            "values": [
                {"datetime": "2024-01-15", "rsi": "65.5"},
                {"datetime": "2024-01-14", "rsi": "62.3"},
                {"datetime": "2024-01-13", "rsi": "58.7"},
                {"datetime": "2024-01-12", "rsi": "55.2"},
                {"datetime": "2024-01-11", "rsi": "52.8"},
            ],
        }

    @pytest.fixture
    def mock_macd_response(self):
        """Mock MACD API response."""
        return {
            "meta": {"symbol": "AAPL", "interval": "1day"},
            "values": [
                {"datetime": "2024-01-15", "macd": "2.45", "macd_signal": "2.12", "macd_hist": "0.33"},
                {"datetime": "2024-01-14", "macd": "2.18", "macd_signal": "2.25", "macd_hist": "-0.07"},
                {"datetime": "2024-01-13", "macd": "1.95", "macd_signal": "2.35", "macd_hist": "-0.40"},
            ],
        }

    @pytest.fixture
    def mock_bollinger_response(self):
        """Mock Bollinger Bands API response."""
        return {
            "meta": {"symbol": "AAPL", "interval": "1day"},
            "values": [
                {
                    "datetime": "2024-01-15",
                    "upper_band": "185.50",
                    "middle_band": "180.00",
                    "lower_band": "174.50",
                },
                {
                    "datetime": "2024-01-14",
                    "upper_band": "184.20",
                    "middle_band": "179.50",
                    "lower_band": "174.80",
                },
                {
                    "datetime": "2024-01-13",
                    "upper_band": "183.10",
                    "middle_band": "179.00",
                    "lower_band": "174.90",
                },
            ],
        }

    @pytest.fixture
    def mock_stochastic_response(self):
        """Mock Stochastic API response."""
        return {
            "meta": {"symbol": "AAPL", "interval": "1day"},
            "values": [
                {"datetime": "2024-01-15", "slow_k": "75.5", "slow_d": "72.3"},
                {"datetime": "2024-01-14", "slow_k": "68.2", "slow_d": "70.1"},
                {"datetime": "2024-01-13", "slow_k": "65.8", "slow_d": "68.5"},
            ],
        }

    def test_should_initialize_with_correct_parameters(self, tool):
        """Test that tool initializes with proper configuration."""
        assert tool.base_url == "https://api.twelvedata.com"
        assert tool.default_outputsize == 100
        assert tool.timeout == 30
        assert tool.cache_ttl == 300

    def test_should_raise_error_without_api_key(self, tool, mocker):
        """Test that tool raises error when API key is missing."""
        mocker.patch.dict("os.environ", {}, clear=True)
        tool_no_key = TwelveDataTool()

        with pytest.raises(ValueError, match="TWELVE_DATA_API_KEY environment variable not set"):
            asyncio.run(tool_no_key._make_api_call("rsi", {"symbol": "AAPL"}))

    @pytest.mark.asyncio
    async def test_should_fetch_rsi_successfully(self, mock_rsi_response, mocker):
        """Test successful RSI data fetching."""
        # Set API key before creating tool instance
        mocker.patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test_key"})
        tool = TwelveDataTool()

        # Use APITestMocks for standardized mock setup
        APITestMocks.setup_twelve_data_mock(mocker, indicator="rsi", values=mock_rsi_response["values"])

        rsi_data = await tool.get_rsi("AAPL", "1day", 14)

        # Verify RSI data structure
        assert isinstance(rsi_data, RSIData)
        assert rsi_data.symbol == "AAPL"
        assert rsi_data.interval == "1day"
        assert rsi_data.time_period == 14
        assert len(rsi_data.values) == 5
        assert rsi_data.current_value == 65.5
        assert rsi_data.signal in ["overbought", "oversold", "neutral"]
        assert 0.0 <= rsi_data.signal_strength <= 1.0

    @pytest.mark.asyncio
    async def test_should_fetch_macd_successfully(self, mock_macd_response, mocker):
        """Test successful MACD data fetching."""
        mocker.patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test_key"})
        tool = TwelveDataTool()  # Create tool after patching environment

        # Use APITestMocks for standardized mock setup
        APITestMocks.setup_twelve_data_mock(mocker, indicator="macd", values=mock_macd_response["values"])

        macd_data = await tool.get_macd("AAPL", "1day")

        # Verify MACD data structure
        assert isinstance(macd_data, MACDData)
        assert macd_data.symbol == "AAPL"
        assert macd_data.interval == "1day"
        assert len(macd_data.values) == 3
        assert macd_data.current_macd == 2.45
        assert macd_data.current_signal == 2.12
        assert macd_data.current_histogram == 0.33
        assert macd_data.crossover_signal in ["bullish", "bearish", "neutral"]

    @pytest.mark.asyncio
    async def test_should_fetch_bollinger_bands_successfully(self, mock_bollinger_response, mocker):
        """Test successful Bollinger Bands data fetching."""
        mocker.patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test_key"})
        tool = TwelveDataTool()  # Create tool after patching environment

        # Use APITestMocks for standardized mock setup
        APITestMocks.setup_twelve_data_mock(mocker, indicator="bbands", values=mock_bollinger_response["values"])

        bb_data = await tool.get_bollinger_bands("AAPL", "1day")

        # Verify Bollinger Bands data structure
        assert isinstance(bb_data, BollingerBandsData)
        assert bb_data.symbol == "AAPL"
        assert bb_data.interval == "1day"
        assert len(bb_data.values) == 3
        assert bb_data.current_upper == 185.50
        assert bb_data.current_middle == 180.00
        assert bb_data.current_lower == 174.50
        assert bb_data.squeeze_signal in ["squeeze", "expansion", "normal"]

    @pytest.mark.asyncio
    async def test_should_fetch_stochastic_successfully(self, mock_stochastic_response, mocker):
        """Test successful Stochastic data fetching."""
        mocker.patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test_key"})
        tool = TwelveDataTool()  # Create tool after patching environment

        # Use APITestMocks for standardized mock setup
        APITestMocks.setup_twelve_data_mock(mocker, indicator="stoch", values=mock_stochastic_response["values"])

        stoch_data = await tool.get_stochastic("AAPL", "1day")

        # Verify Stochastic data structure
        assert isinstance(stoch_data, StochasticData)
        assert stoch_data.symbol == "AAPL"
        assert stoch_data.interval == "1day"
        assert len(stoch_data.values) == 3
        assert stoch_data.current_k == 75.5
        assert stoch_data.current_d == 72.3
        assert stoch_data.signal in ["overbought", "oversold", "neutral"]

    @pytest.mark.asyncio
    async def test_should_handle_api_error_response(self, mocker):
        """Test handling of API error responses."""
        mocker.patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test_key"})
        tool = TwelveDataTool()  # Create tool after patching environment

        # Use APITestMocks for error scenario
        APITestMocks.setup_http_error_mock(mocker, status_code=400, error_message="Bad Request")

        with pytest.raises(RuntimeError, match="API error 400"):
            await tool.get_rsi("INVALID", "1day")

    @pytest.mark.asyncio
    async def test_should_handle_api_timeout(self, mocker):
        """Test handling of API timeouts."""
        mocker.patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test_key"})
        tool = TwelveDataTool()  # Create tool after patching environment

        # Mock the rate limiting system to raise TimeoutError
        mock_rate_limit = mocker.patch("finwiz.tools.enhanced_twelve_data_tool.with_rate_limit")
        mock_rate_limit.side_effect = TimeoutError("Request timeout")

        with pytest.raises(TimeoutError):
            await tool.get_rsi("AAPL", "1day")

    @pytest.mark.asyncio
    async def test_should_use_cache_for_repeated_requests(self, mock_rsi_response, mocker):
        """Test that cache is used for repeated requests."""
        mocker.patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test_key"})
        tool = TwelveDataTool()  # Create tool after patching environment

        # Use APITestMocks for standardized mock setup
        mock_get = APITestMocks.setup_twelve_data_mock(mocker, indicator="rsi", values=mock_rsi_response["values"])

        # First request
        await tool.get_rsi("AAPL", "1day", 14)

        # Second request should use cache
        await tool.get_rsi("AAPL", "1day", 14)

        # Should only make one API call
        assert mock_get.call_count == 1

    def test_should_analyze_rsi_signal_correctly(self, tool):
        """Test RSI signal analysis."""
        # Test overbought
        signal, strength = tool._analyze_rsi_signal(75.0)
        assert signal == "overbought"
        assert strength > 0

        # Test oversold
        signal, strength = tool._analyze_rsi_signal(25.0)
        assert signal == "oversold"
        assert strength > 0

        # Test neutral
        signal, strength = tool._analyze_rsi_signal(50.0)
        assert signal == "neutral"
        assert strength == 0.3

        # Test None value
        signal, strength = tool._analyze_rsi_signal(None)
        assert signal == "neutral"
        assert strength == 0.0

    def test_should_analyze_macd_crossover_correctly(self, tool):
        """Test MACD crossover analysis."""
        from finwiz.tools.enhanced_twelve_data_tool import MACDValue

        # Test bullish crossover
        macd_values = [
            MACDValue(datetime="2024-01-15", macd=2.5, macd_signal=2.0, macd_hist=0.5),
            MACDValue(datetime="2024-01-14", macd=1.8, macd_signal=2.2, macd_hist=-0.4),
        ]

        signal, strength = tool._analyze_macd_signal(macd_values)
        assert signal == "bullish"
        assert strength > 0

        # Test bearish crossover
        macd_values = [
            MACDValue(datetime="2024-01-15", macd=1.5, macd_signal=2.0, macd_hist=-0.5),
            MACDValue(datetime="2024-01-14", macd=2.2, macd_signal=1.8, macd_hist=0.4),
        ]

        signal, strength = tool._analyze_macd_signal(macd_values)
        assert signal == "bearish"
        assert strength > 0

    def test_should_analyze_stochastic_signal_correctly(self, tool):
        """Test Stochastic signal analysis."""
        # Test overbought
        signal = tool._analyze_stochastic_signal(85.0, 82.0)
        assert signal == "overbought"

        # Test oversold
        signal = tool._analyze_stochastic_signal(15.0, 18.0)
        assert signal == "oversold"

        # Test neutral
        signal = tool._analyze_stochastic_signal(50.0, 45.0)
        assert signal == "neutral"

        # Test None values
        signal = tool._analyze_stochastic_signal(None, None)
        assert signal == "neutral"

    def test_should_analyze_bollinger_squeeze_correctly(self, tool):
        """Test Bollinger Bands squeeze analysis."""
        from finwiz.tools.enhanced_twelve_data_tool import BollingerBandsValue

        # Create mock Bollinger Bands data with varying band widths
        bb_values = []

        # Recent narrow bands (squeeze)
        for i in range(10):
            bb_values.append(BollingerBandsValue(datetime=f"2024-01-{15 - i:02d}", upper_band=102.0, middle_band=100.0, lower_band=98.0))

        # Historical wider bands
        for i in range(10, 25):
            bb_values.append(BollingerBandsValue(datetime=f"2024-01-{15 - i:02d}", upper_band=105.0, middle_band=100.0, lower_band=95.0))

        squeeze_signal = tool._analyze_bollinger_squeeze(bb_values)
        assert squeeze_signal == "squeeze"

    @pytest.mark.asyncio
    async def test_should_perform_comprehensive_analysis(self, mocker):
        """Test comprehensive technical indicator analysis."""
        mocker.patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test_key"})
        tool = TwelveDataTool()  # Create tool after patching environment

        # Mock all indicator methods using mocker
        tool.get_rsi = mocker.AsyncMock(
            return_value=RSIData(
                symbol="AAPL",
                interval="1day",
                time_period=14,
                values=[],
                current_value=65.0,
                signal="neutral",
                signal_strength=0.3,
            )
        )

        tool.get_macd = mocker.AsyncMock(
            return_value=MACDData(
                symbol="AAPL",
                interval="1day",
                fast_period=12,
                slow_period=26,
                signal_period=9,
                values=[],
                current_macd=2.5,
                current_signal=2.0,
                current_histogram=0.5,
                crossover_signal="bullish",
                signal_strength=0.7,
            )
        )

        tool.get_bollinger_bands = mocker.AsyncMock(
            return_value=BollingerBandsData(
                symbol="AAPL",
                interval="1day",
                time_period=20,
                std_dev=2,
                values=[],
                current_upper=185.0,
                current_middle=180.0,
                current_lower=175.0,
                band_width=0.055,
                squeeze_signal="normal",
                position_signal="within_bands",
            )
        )

        tool.get_stochastic = mocker.AsyncMock(
            return_value=StochasticData(
                symbol="AAPL",
                interval="1day",
                k_period=14,
                d_period=3,
                values=[],
                current_k=75.0,
                current_d=72.0,
                signal="neutral",
                crossover_signal="neutral",
            )
        )

        summary = await tool.get_comprehensive_analysis("AAPL", "1day")

        # Verify comprehensive analysis structure
        assert isinstance(summary, TechnicalIndicatorSummary)
        assert summary.symbol == "AAPL"
        assert summary.interval == "1day"
        assert summary.rsi_data is not None
        assert summary.macd_data is not None
        assert summary.bollinger_data is not None
        assert summary.stochastic_data is not None
        assert summary.overall_signal in ["buy", "sell", "neutral"]
        assert 0.0 <= summary.signal_confidence <= 1.0
        assert summary.consensus_indicators >= 0

    def test_should_determine_overall_signal_correctly(self, tool):
        """Test overall signal determination from multiple indicators."""
        # Create bullish indicators
        rsi_data = RSIData(
            symbol="AAPL",
            interval="1day",
            time_period=14,
            values=[],
            current_value=25.0,  # Oversold - bullish
            signal="oversold",
            signal_strength=0.8,
        )

        macd_data = MACDData(
            symbol="AAPL",
            interval="1day",
            fast_period=12,
            slow_period=26,
            signal_period=9,
            values=[],
            current_macd=2.5,
            current_signal=2.0,
            current_histogram=0.5,
            crossover_signal="bullish",
            signal_strength=0.7,
        )

        signal, confidence, consensus = tool._determine_overall_signal(rsi_data, macd_data, None, None)

        # Should be bullish with good confidence
        assert signal == "buy"
        assert confidence > 0.5
        assert consensus == 2

    @pytest.mark.asyncio
    async def test_should_handle_partial_indicator_failures(self, mocker):
        """Test handling when some indicators fail to fetch."""
        mocker.patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test_key"})
        tool = TwelveDataTool()  # Create tool after patching environment

        # Mock some indicators to succeed and others to fail using mocker
        tool.get_rsi = mocker.AsyncMock(side_effect=RuntimeError("RSI API error"))
        tool.get_macd = mocker.AsyncMock(
            return_value=MACDData(
                symbol="AAPL",
                interval="1day",
                fast_period=12,
                slow_period=26,
                signal_period=9,
                values=[],
                current_macd=2.5,
                current_signal=2.0,
                current_histogram=0.5,
                crossover_signal="bullish",
                signal_strength=0.7,
            )
        )
        tool.get_bollinger_bands = mocker.AsyncMock(side_effect=RuntimeError("BB API error"))
        tool.get_stochastic = mocker.AsyncMock(
            return_value=StochasticData(
                symbol="AAPL",
                interval="1day",
                k_period=14,
                d_period=3,
                values=[],
                current_k=75.0,
                current_d=72.0,
                signal="neutral",
                crossover_signal="neutral",
            )
        )

        summary = await tool.get_comprehensive_analysis("AAPL", "1day")

        # Should handle partial failures gracefully
        assert summary.rsi_data is None  # Failed
        assert summary.macd_data is not None  # Succeeded
        assert summary.bollinger_data is None  # Failed
        assert summary.stochastic_data is not None  # Succeeded
        assert summary.overall_signal in ["buy", "sell", "neutral"]

    @pytest.mark.asyncio
    async def test_should_respect_rate_limiting(self, mocker):
        """Test that rate limiting is applied to API calls."""
        mocker.patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test_key"})
        tool = TwelveDataTool()

        # Mock the centralized rate limiting system
        mock_rate_limit = mocker.patch("finwiz.tools.enhanced_twelve_data_tool.with_rate_limit")
        mock_rate_limit.return_value = {"values": []}

        await tool._make_api_call("rsi", {"symbol": "AAPL"})

        # Rate limiter should have been called
        mock_rate_limit.assert_called_once()

    def test_should_validate_signal_strength_ranges(self, tool):
        """Test that all signal strengths are within valid ranges."""
        # Test RSI signal strengths
        for rsi_value in [10, 30, 50, 70, 90]:
            signal, strength = tool._analyze_rsi_signal(rsi_value)
            assert 0.0 <= strength <= 1.0

        # Test Stochastic signals
        for k, d in [(10, 15), (50, 45), (85, 90)]:
            signal = tool._analyze_stochastic_signal(k, d)
            assert signal in ["overbought", "oversold", "neutral"]

    @pytest.mark.asyncio
    async def test_should_handle_empty_api_response(self, mocker):
        """Test handling of empty API responses."""
        mocker.patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test_key"})
        tool = TwelveDataTool()  # Create tool after patching environment

        # Mock the rate limiting system to return empty response
        mock_rate_limit = mocker.patch("finwiz.tools.enhanced_twelve_data_tool.with_rate_limit")
        mock_rate_limit.return_value = {"meta": {}, "values": []}

        rsi_data = await tool.get_rsi("AAPL", "1day")

        # Should handle empty response gracefully
        assert isinstance(rsi_data, RSIData)
        assert len(rsi_data.values) == 0
        assert rsi_data.current_value is None
        assert rsi_data.signal == "neutral"

    @pytest.mark.asyncio
    async def test_should_handle_api_error_in_response_body(self, mocker):
        """Test handling of API errors returned in response body."""
        mocker.patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test_key"})
        tool = TwelveDataTool()  # Create tool after patching environment

        # Mock the rate limiting system to return error response
        mock_rate_limit = mocker.patch("finwiz.tools.enhanced_twelve_data_tool.with_rate_limit")
        mock_rate_limit.side_effect = RuntimeError("API error: Invalid symbol")

        with pytest.raises(RuntimeError, match="API error: Invalid symbol"):
            await tool._make_api_call("rsi", {"symbol": "INVALID"})
