"""
Technical analysis functions for quantitative analysis tool.

Extracted from quantitative_analysis_tool.py for modularity.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from finwiz.schemas.quantitative_crew import QuantitativeTechnicalAnalysis
from finwiz.tools.logger import get_logger

if TYPE_CHECKING:
    import pandas as pd

    from finwiz.quantitative.technical import TechnicalAnalysisEngine
    from finwiz.schemas.tools import QuantitativeAnalysisInput


def perform_technical_analysis(
    data: pd.DataFrame,
    input_data: QuantitativeAnalysisInput,
    technical_engine: TechnicalAnalysisEngine,
) -> str:
    """
    Perform technical analysis on price data.

    Args:
        data: Historical price data DataFrame
        input_data: Analysis input parameters
        technical_engine: Technical analysis engine instance

    Returns:
        JSON string with technical analysis results

    """
    logger = get_logger(__name__)

    try:
        # Run technical analysis
        tech_result = technical_engine.analyze_symbol(data, input_data.symbol, timeframe="1d")

        # Convert to simplified schema
        quant_tech = QuantitativeTechnicalAnalysis(
            symbol=input_data.symbol,
            timeframe="1d",
            overall_signal=tech_result.overall_signal.value,
            overall_confidence=tech_result.overall_confidence,
            signal_strength=tech_result.signal_strength.value,
            bullish_signals_count=tech_result.bullish_signals,
            bearish_signals_count=tech_result.bearish_signals,
            neutral_signals_count=tech_result.neutral_signals,
        )

        # Extract key indicator values
        quant_tech = _extract_indicator_values(quant_tech, tech_result)

        # Build complete technical data dict with numeric indicator values
        tech_data = quant_tech.model_dump()

        # Add numeric MACD values from raw_values
        tech_data = _add_macd_values(tech_data, tech_result, input_data.symbol, logger)

        # Add RSI numeric value
        tech_data = _add_rsi_values(tech_data, tech_result)

        # Add moving averages if available
        tech_data = _add_moving_averages(tech_data, tech_result)

        # Serialize with proper datetime handling
        return json.dumps(tech_data, indent=2, default=str)

    except Exception as e:
        logger.error(f"Error in technical analysis: {e}")
        return f"Technical analysis error: {str(e)}"


def _extract_indicator_values(
    quant_tech: QuantitativeTechnicalAnalysis,
    tech_result,
) -> QuantitativeTechnicalAnalysis:
    """Extract key indicator values from technical result."""
    if "RSI" in tech_result.indicator_results:
        rsi_result = tech_result.indicator_results["RSI"]
        if "RSI" in rsi_result.values:
            rsi_values = rsi_result.values["RSI"]
            if isinstance(rsi_values, list) and rsi_values:
                quant_tech.rsi_value = rsi_values[-1]

    if "MACD" in tech_result.indicator_results:
        macd_result = tech_result.indicator_results["MACD"]
        if macd_result.signals:
            quant_tech.macd_signal = macd_result.signals[0].description

    if "Bollinger_Bands" in tech_result.indicator_results:
        bb_result = tech_result.indicator_results["Bollinger_Bands"]
        if bb_result.signals:
            quant_tech.bollinger_position = bb_result.signals[0].description

    return quant_tech


def _add_macd_values(tech_data: dict, tech_result, symbol: str, logger) -> dict:
    """Add numeric MACD values to technical data."""
    if "MACD" not in tech_result.indicator_results:
        return tech_data

    macd_result = tech_result.indicator_results["MACD"]
    if "MACD_line" not in macd_result.raw_values or "MACD_signal" not in macd_result.raw_values:
        logger.warning(f"⚠️ MACD raw_values missing for {symbol}")
        return tech_data

    macd_line_values = macd_result.raw_values["MACD_line"]
    macd_signal_values = macd_result.raw_values["MACD_signal"]

    if isinstance(macd_line_values, list) and macd_line_values:
        try:
            macd_value = float(macd_line_values[-1])
            if not (macd_value != macd_value):  # NaN check
                tech_data["macd"] = macd_value
                logger.debug(f"✅ Extracted MACD line: {macd_value}")
            else:
                logger.warning(f"⚠️ MACD line is NaN for {symbol}")
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ Failed to convert MACD line for {symbol}: {e}")

    if isinstance(macd_signal_values, list) and macd_signal_values:
        try:
            macd_signal_value = float(macd_signal_values[-1])
            if not (macd_signal_value != macd_signal_value):  # NaN check
                tech_data["macd_signal"] = macd_signal_value
                logger.debug(f"✅ Extracted MACD signal: {macd_signal_value}")
            else:
                logger.warning(f"⚠️ MACD signal is NaN for {symbol}")
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ Failed to convert MACD signal for {symbol}: {e}")

    # Store description separately if needed
    if macd_result.signals:
        tech_data["macd_description"] = macd_result.signals[0].description

    return tech_data


def _add_rsi_values(tech_data: dict, tech_result) -> dict:
    """Add RSI numeric value to technical data."""
    if "RSI" not in tech_result.indicator_results:
        return tech_data

    rsi_result = tech_result.indicator_results["RSI"]
    if "RSI" in rsi_result.values:
        rsi_values = rsi_result.values["RSI"]
        if isinstance(rsi_values, list) and rsi_values:
            tech_data["rsi"] = float(rsi_values[-1])

    return tech_data


def _add_moving_averages(tech_data: dict, tech_result) -> dict:
    """Add moving average values to technical data."""
    if "SMA_50" in tech_result.indicator_results:
        sma_50_result = tech_result.indicator_results["SMA_50"]
        if "SMA" in sma_50_result.values:
            sma_50_values = sma_50_result.values["SMA"]
            if isinstance(sma_50_values, list) and sma_50_values:
                tech_data["sma_50"] = float(sma_50_values[-1])

    if "SMA_200" in tech_result.indicator_results:
        sma_200_result = tech_result.indicator_results["SMA_200"]
        if "SMA" in sma_200_result.values:
            sma_200_values = sma_200_result.values["SMA"]
            if isinstance(sma_200_values, list) and sma_200_values:
                tech_data["sma_200"] = float(sma_200_values[-1])

    return tech_data
