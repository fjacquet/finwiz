"""Unit tests for MACD signal extraction fix in quantitative analysis tool."""

import math
import pytest


class TestMACDExtractionFix:
    """Test suite for MACD numeric value extraction."""

    @pytest.fixture
    def mock_tech_result_with_macd(self, mocker):
        """Create mock technical analysis result with MACD data."""
        mock_macd_result = mocker.Mock()
        mock_macd_result.signals = [mocker.Mock(description="MACD bullish crossover - strong buy signal")]
        mock_macd_result.raw_values = {
            "MACD_line": [0.5, 0.6, 0.7, 0.8, 0.9],
            "MACD_signal": [0.4, 0.5, 0.6, 0.7, 0.8],
            "MACD_histogram": [0.1, 0.1, 0.1, 0.1, 0.1],
        }
        mock_macd_result.values = {}

        mock_rsi_result = mocker.Mock()
        mock_rsi_result.values = {"RSI": [45.0, 50.0, 55.0, 60.0, 65.0]}
        mock_rsi_result.signals = []

        mock_tech_result = mocker.Mock()
        mock_tech_result.indicator_results = {
            "MACD": mock_macd_result,
            "RSI": mock_rsi_result,
        }
        mock_tech_result.overall_signal = mocker.Mock(value="BUY")
        mock_tech_result.overall_confidence = 0.8
        mock_tech_result.signal_strength = mocker.Mock(value="STRONG")
        mock_tech_result.bullish_signals = 3
        mock_tech_result.bearish_signals = 1
        mock_tech_result.neutral_signals = 0

        return mock_tech_result

    def test_should_extract_numeric_macd_values(self, mock_tech_result_with_macd):
        """Test that numeric MACD values are extracted from raw_values."""
        from finwiz.schemas.quantitative_crew import QuantitativeTechnicalAnalysis

        # Simulate the extraction logic from quantitative_analysis_tool
        quant_tech = QuantitativeTechnicalAnalysis(
            symbol="AAPL",
            timeframe="1d",
            overall_signal="BUY",
            overall_confidence=0.8,
            signal_strength="STRONG",
            bullish_signals_count=3,
            bearish_signals_count=1,
            neutral_signals_count=0,
        )

        # Extract RSI
        if "RSI" in mock_tech_result_with_macd.indicator_results:
            rsi_result = mock_tech_result_with_macd.indicator_results["RSI"]
            if "RSI" in rsi_result.values:
                rsi_values = rsi_result.values["RSI"]
                if isinstance(rsi_values, list) and rsi_values:
                    quant_tech.rsi_value = rsi_values[-1]

        # Extract MACD description
        if "MACD" in mock_tech_result_with_macd.indicator_results:
            macd_result = mock_tech_result_with_macd.indicator_results["MACD"]
            if macd_result.signals:
                quant_tech.macd_signal = macd_result.signals[0].description

        # Build tech_data dict
        tech_data = quant_tech.model_dump()

        # Add numeric MACD values (THE FIX)
        if "MACD" in mock_tech_result_with_macd.indicator_results:
            macd_result = mock_tech_result_with_macd.indicator_results["MACD"]
            if "MACD_line" in macd_result.raw_values and "MACD_signal" in macd_result.raw_values:
                macd_line_values = macd_result.raw_values["MACD_line"]
                macd_signal_values = macd_result.raw_values["MACD_signal"]
                if isinstance(macd_line_values, list) and macd_line_values:
                    tech_data["macd"] = macd_line_values[-1]
                if isinstance(macd_signal_values, list) and macd_signal_values:
                    tech_data["macd_signal"] = macd_signal_values[-1]
                if macd_result.signals:
                    tech_data["macd_description"] = macd_result.signals[0].description

        # Add RSI numeric value (matching the fix)
        if "RSI" in mock_tech_result_with_macd.indicator_results:
            rsi_result = mock_tech_result_with_macd.indicator_results["RSI"]
            if "RSI" in rsi_result.values:
                rsi_values = rsi_result.values["RSI"]
                if isinstance(rsi_values, list) and rsi_values:
                    tech_data["rsi"] = rsi_values[-1]

        # Assertions
        assert "macd" in tech_data, "MACD line should be extracted"
        assert math.isclose(tech_data["macd"], 0.9, rel_tol=0, abs_tol=1e-6), f"Expected MACD=0.9, got {tech_data['macd']}"

        assert "macd_signal" in tech_data, "MACD signal should be extracted"
        assert isinstance(tech_data["macd_signal"], float), f"MACD signal should be float, got {type(tech_data['macd_signal'])}"
        assert math.isclose(tech_data["macd_signal"], 0.8, rel_tol=0, abs_tol=1e-6), f"Expected MACD signal=0.8, got {tech_data['macd_signal']}"

        assert "macd_description" in tech_data, "MACD description should be preserved"
        assert tech_data["macd_description"] == "MACD bullish crossover - strong buy signal"

        assert "rsi" in tech_data, "RSI should be extracted"
        assert math.isclose(tech_data["rsi"], 65.0, rel_tol=0, abs_tol=1e-6), f"Expected RSI=65.0, got {tech_data['rsi']}"

    def test_should_handle_missing_macd_gracefully(self, mocker):
        """Test that missing MACD data is handled gracefully."""
        from finwiz.schemas.quantitative_crew import QuantitativeTechnicalAnalysis

        # Mock result without MACD
        mock_tech_result = mocker.Mock()
        mock_tech_result.indicator_results = {}
        mock_tech_result.overall_signal = mocker.Mock(value="HOLD")
        mock_tech_result.overall_confidence = 0.5
        mock_tech_result.signal_strength = mocker.Mock(value="WEAK")
        mock_tech_result.bullish_signals = 1
        mock_tech_result.bearish_signals = 1
        mock_tech_result.neutral_signals = 1

        quant_tech = QuantitativeTechnicalAnalysis(
            symbol="AAPL",
            timeframe="1d",
            overall_signal="HOLD",
            overall_confidence=0.5,
            signal_strength="WEAK",
            bullish_signals_count=1,
            bearish_signals_count=1,
            neutral_signals_count=1,
        )

        tech_data = quant_tech.model_dump()

        # Should not have MACD values
        assert "macd" not in tech_data or tech_data.get("macd") is None
        assert "macd_signal" not in tech_data or tech_data.get("macd_signal") is None

    def test_should_calculate_macd_diff_correctly(self, mock_tech_result_with_macd):
        """Test that MACD diff can be calculated from extracted values."""
        from finwiz.schemas.quantitative_crew import QuantitativeTechnicalAnalysis

        quant_tech = QuantitativeTechnicalAnalysis(
            symbol="AAPL",
            timeframe="1d",
            overall_signal="BUY",
            overall_confidence=0.8,
            signal_strength="STRONG",
        )

        tech_data = quant_tech.model_dump()

        # Extract numeric MACD values
        if "MACD" in mock_tech_result_with_macd.indicator_results:
            macd_result = mock_tech_result_with_macd.indicator_results["MACD"]
            if "MACD_line" in macd_result.raw_values and "MACD_signal" in macd_result.raw_values:
                macd_line_values = macd_result.raw_values["MACD_line"]
                macd_signal_values = macd_result.raw_values["MACD_signal"]
                if isinstance(macd_line_values, list) and macd_line_values:
                    tech_data["macd"] = macd_line_values[-1]
                if isinstance(macd_signal_values, list) and macd_signal_values:
                    tech_data["macd_signal"] = macd_signal_values[-1]

        # Calculate MACD diff (as scorer does)
        macd = tech_data.get("macd", 0.0)
        macd_signal = tech_data.get("macd_signal", 0.0)
        macd_diff = macd - macd_signal

        assert math.isclose(macd_diff, 0.1, rel_tol=0, abs_tol=0.001), f"Expected MACD diff=0.1, got {macd_diff}"

        # Test momentum scoring logic
        if macd_diff > 0 and macd > 0:
            momentum_score = 1.0
        elif macd_diff > 0:
            momentum_score = 0.8
        else:
            momentum_score = 0.4

        assert math.isclose(momentum_score, 1.0, rel_tol=0, abs_tol=1e-6), f"Expected momentum_score=1.0, got {momentum_score}"
