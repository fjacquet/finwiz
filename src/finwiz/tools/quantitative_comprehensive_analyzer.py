"""
Comprehensive analysis functions for quantitative analysis tool.

Extracted from quantitative_analysis_tool.py for modularity.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from finwiz.quantitative.backtesting import SimpleMovingAverageStrategy
from finwiz.schemas.quantitative_crew import (
    EnhancedCryptoAnalysis,
    EnhancedETFAnalysis,
    EnhancedStockAnalysis,
    QuantitativeBacktestResult,
    QuantitativePerformanceMetrics,
    QuantitativeRecommendation,
    QuantitativeTechnicalAnalysis,
)
from finwiz.tools.logger import get_logger

if TYPE_CHECKING:
    import pandas as pd

    from finwiz.quantitative.backtesting import BacktestingEngine
    from finwiz.quantitative.performance import PerformanceAnalyzer
    from finwiz.quantitative.technical import TechnicalAnalysisEngine
    from finwiz.schemas.tools import QuantitativeAnalysisInput


def perform_comprehensive_analysis(
    data: pd.DataFrame,
    input_data: QuantitativeAnalysisInput,
    start_date: datetime,
    end_date: datetime,
    technical_engine: TechnicalAnalysisEngine,
    backtesting_engine: BacktestingEngine,
    performance_analyzer: PerformanceAnalyzer,
) -> str:
    """
    Perform comprehensive quantitative analysis.

    Combines technical analysis, backtesting, and performance metrics
    to provide a complete quantitative assessment.

    Args:
        data: Historical price data DataFrame
        input_data: Analysis input parameters
        start_date: Analysis start date
        end_date: Analysis end date
        technical_engine: Technical analysis engine
        backtesting_engine: Backtesting engine
        performance_analyzer: Performance analyzer

    Returns:
        JSON string with comprehensive analysis results

    Technical analysis, backtesting, and performance analysis are three
    independent computations over the same price history -- each is
    attempted separately and a failure or refusal in one does not discard
    the other two. That matters concretely: volatility is read downstream
    from ``performance_metrics``, not from ``backtest_result``
    (``deep_analysis_data_collector.flatten_collected_data``), so a
    backtest-side failure must not take volatility down with it. Before this
    fix, all three lived in one shared try/except, which is the actual
    mechanism behind "a crash drops the holding's entire quantitative
    payload" (Task 15).

    """
    logger = get_logger(__name__)

    tech_result = None
    quant_tech = None
    try:
        tech_result = technical_engine.analyze_symbol(data, input_data.symbol, timeframe="1d")
        quant_tech = _create_technical_result(input_data.symbol, tech_result)
    except Exception as e:
        logger.error(f"Technical analysis failed for {input_data.symbol}: {e}")

    backtest_result = None
    quant_backtest = None
    try:
        backtest_result = backtesting_engine.run_strategy_backtest(
            SimpleMovingAverageStrategy,
            input_data.symbol,
            start_date,
            end_date,
            strategy_params={"short_period": 20, "long_period": 50},
        )
        if backtest_result is not None:
            quant_backtest = _create_backtest_result(input_data.symbol, backtest_result)
    except Exception as e:
        logger.error(f"Backtest failed for {input_data.symbol}: {e}")

    metrics = None
    quant_perf = None
    try:
        returns = data["Close"].pct_change().dropna()
        perf_report = performance_analyzer.analyze_performance(returns, strategy_name=f"{input_data.symbol}_analysis")
        metrics = perf_report.strategy_metrics
        quant_perf = _create_performance_result(input_data.symbol, metrics, len(returns))
    except Exception as e:
        logger.error(f"Performance analysis failed for {input_data.symbol}: {e}")

    if quant_tech is None and quant_backtest is None and quant_perf is None:
        message = f"technical, backtest, and performance analysis all failed for {input_data.symbol}"
        logger.error(f"Comprehensive analysis error: {message}")
        return f"Comprehensive analysis error: {message}"

    try:
        recommendation = generate_recommendation(input_data.symbol, tech_result, backtest_result, metrics)

        # Add ETF-specific metrics if applicable
        etf_specific_data = {}
        if input_data.asset_class.lower() == "etf":
            etf_specific_data = _fetch_etf_specific_data(input_data.symbol, logger)

        # Create comprehensive result based on asset class
        result = _create_asset_specific_result(input_data, quant_tech, quant_backtest, quant_perf, recommendation)

        # Merge ETF-specific data into result dict
        result_dict = json.loads(result.model_dump_json())
        if etf_specific_data:
            result_dict.update(etf_specific_data)

        return json.dumps(result_dict, indent=2, default=str)

    except Exception as e:
        logger.error(f"Error assembling comprehensive analysis for {input_data.symbol}: {e}")
        return f"Comprehensive analysis error: {e!s}"


def _create_technical_result(symbol: str, tech_result) -> QuantitativeTechnicalAnalysis:
    """Create technical analysis result from engine output."""
    return QuantitativeTechnicalAnalysis(
        symbol=symbol,
        timeframe="1d",
        overall_signal=tech_result.overall_signal.value,
        overall_confidence=tech_result.overall_confidence,
        signal_strength=tech_result.signal_strength.value,
        bullish_signals_count=tech_result.bullish_signals,
        bearish_signals_count=tech_result.bearish_signals,
        neutral_signals_count=tech_result.neutral_signals,
    )


def _create_backtest_result(symbol: str, backtest_result) -> QuantitativeBacktestResult:
    """Create backtest result from engine output."""
    return QuantitativeBacktestResult(
        symbol=symbol,
        strategy_name=backtest_result.strategy_name,
        total_return=backtest_result.total_return,
        annualized_return=backtest_result.annualized_return,
        sharpe_ratio=backtest_result.sharpe_ratio,
        max_drawdown=backtest_result.max_drawdown,
        total_trades=backtest_result.total_trades,
        win_rate=backtest_result.win_rate,
        volatility=backtest_result.volatility,
        var_95=backtest_result.var_95,
        backtest_start_date=backtest_result.start_date,
        backtest_end_date=backtest_result.end_date,
        initial_capital=backtest_result.initial_capital,
        final_value=backtest_result.final_value,
    )


def _create_performance_result(symbol: str, metrics, total_days: int) -> QuantitativePerformanceMetrics:
    """Create performance metrics result from analyzer output."""
    return QuantitativePerformanceMetrics(
        symbol=symbol,
        total_return=metrics.total_return,
        annualized_return=metrics.annualized_return,
        sharpe_ratio=metrics.sharpe_ratio,
        sortino_ratio=metrics.sortino_ratio,
        calmar_ratio=metrics.calmar_ratio,
        max_drawdown=metrics.max_drawdown,
        volatility=metrics.volatility,
        var_95=metrics.var_95,
        skewness=metrics.skewness,
        kurtosis=metrics.kurtosis,
        alpha=metrics.alpha if metrics.alpha is not None else 0.0,
        beta=metrics.beta if metrics.beta is not None else 1.0,
        information_ratio=metrics.information_ratio if metrics.information_ratio is not None else 0.0,
        start_date=datetime.now(),
        end_date=datetime.now(),
        total_days=total_days,
    )


def _fetch_etf_specific_data(symbol: str, logger) -> dict:
    """Fetch ETF-specific metrics from Yahoo Finance."""
    etf_specific_data = {}

    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Fetch expense ratio (try multiple fields)
        expense_ratio = info.get("netExpenseRatio") or info.get("annualReportExpenseRatio")
        if expense_ratio is not None:
            expense_ratio_decimal = float(expense_ratio) / 100.0
            etf_specific_data["expense_ratio"] = expense_ratio_decimal
            logger.info(f"✅ Fetched expense_ratio for {symbol}: {expense_ratio}% → {expense_ratio_decimal:.6f}")
        else:
            # Try fallback configuration file
            from finwiz.quantitative.etf.etf_expense_fallback import get_fallback_expense_ratio

            fallback_ratio = get_fallback_expense_ratio(symbol)
            if fallback_ratio is not None:
                etf_specific_data["expense_ratio"] = fallback_ratio
                logger.info(f"✅ Using fallback expense_ratio for {symbol}: {fallback_ratio:.6f}")
            else:
                logger.warning(f"⚠️ No expense_ratio available for {symbol}")

        # Fetch AUM
        total_assets = info.get("totalAssets")
        if total_assets is not None:
            etf_specific_data["aum"] = float(total_assets)
            logger.info(f"✅ Fetched AUM for {symbol}: ${total_assets:,.0f}")
        else:
            logger.warning(f"⚠️ No AUM available for {symbol}")

    except Exception as e:
        logger.error(f"Error fetching ETF-specific data for {symbol}: {e}")

    return etf_specific_data


def _create_asset_specific_result(
    input_data: QuantitativeAnalysisInput,
    quant_tech: QuantitativeTechnicalAnalysis | None,
    quant_backtest: QuantitativeBacktestResult | None,
    quant_perf: QuantitativePerformanceMetrics | None,
    recommendation: QuantitativeRecommendation,
):
    """Create asset-class specific analysis result."""
    if input_data.asset_class.lower() == "stock":
        return EnhancedStockAnalysis(
            ticker=input_data.symbol,
            technical_analysis=quant_tech,
            backtest_result=quant_backtest,
            performance_metrics=quant_perf,
            quantitative_recommendation=recommendation,
        )
    elif input_data.asset_class.lower() == "etf":
        return EnhancedETFAnalysis(
            ticker=input_data.symbol,
            technical_analysis=quant_tech,
            backtest_result=quant_backtest,
            performance_metrics=quant_perf,
            quantitative_recommendation=recommendation,
        )
    else:  # crypto
        return EnhancedCryptoAnalysis(
            symbol=input_data.symbol,
            technical_analysis=quant_tech,
            backtest_result=quant_backtest,
            performance_metrics=quant_perf,
            quantitative_recommendation=recommendation,
        )


def _build_key_indicators(tech_result: Any | None, tech_signal: str, tech_confidence: float) -> dict[str, Any]:
    """Signal counts are omitted (not fabricated as 0) when technical analysis failed."""
    key_indicators: dict[str, Any] = {"technical_signal": tech_signal, "technical_confidence": tech_confidence}
    if tech_result is not None:
        key_indicators["bullish_signals"] = tech_result.bullish_signals
        key_indicators["bearish_signals"] = tech_result.bearish_signals
    return key_indicators


def _build_risk_metrics(max_drawdown: float | None, volatility: float | None, sharpe_ratio: float | None, var_95: float | None) -> dict[str, float]:
    """Omit a risk figure rather than fabricate 0.0 when it could not be computed.

    A fabricated 0.0 here used to leak into the scorer's flat dict (via
    DeepAnalysisDataCollector._flatten_recursive, which walks the whole
    quantitative_analysis payload) and defeat both the Task 4/5 price-history
    volatility fallback and the critical-field gate -- both only act when the
    field is genuinely absent. See Task 15 review round 1.
    """
    risk_metrics: dict[str, float] = {}
    if max_drawdown is not None:
        risk_metrics["max_drawdown"] = max_drawdown
    if volatility is not None:
        risk_metrics["volatility"] = volatility
    if sharpe_ratio is not None:
        risk_metrics["sharpe_ratio"] = sharpe_ratio
    if var_95 is not None:
        risk_metrics["var_95"] = var_95
    return risk_metrics


def generate_recommendation(symbol: str, tech_result: Any | None, backtest_result: Any | None, perf_metrics: Any | None) -> QuantitativeRecommendation:
    """
    Generate investment recommendation based on quantitative analysis.

    Args:
        symbol: Asset symbol
        tech_result: Technical analysis result, or None if that sub-analysis failed
        backtest_result: Backtesting result, or None if refused (short series) or failed
        perf_metrics: Performance metrics, or None if that sub-analysis failed (currently
            unused here -- see note below; kept in the signature for API stability)

    Returns:
        QuantitativeRecommendation with buy/hold/sell signal

    Any of the three inputs may be None -- each of the three sub-analyses in
    perform_comprehensive_analysis is now independent, so the recommendation
    degrades gracefully to whichever subset succeeded rather than crashing.

    Risk figures (drawdown/volatility/sharpe/VaR) are read from backtest_result
    ONLY, never from perf_metrics: BacktestResult.volatility/max_drawdown are
    percent-scaled (backtesting_performance.py:246) while
    PerformanceMetrics.volatility/max_drawdown are fractional
    (performance_metrics.py:90). volatility has a sanctioned normalizer
    (config/critical_fields_config.py:normalize_volatility); max_drawdown does
    not, so mixing the two sources here would silently produce a wrong,
    mis-scaled number (e.g. -3.0 read as -300%) rather than an honestly-absent
    one. When backtest_result is None these fields are simply None/omitted --
    never fabricated as 0.0. A fabricated 0.0 is worse than a missing value:
    downstream, `technical_fallback.fill_volatility` only fills volatility
    when it is genuinely absent (`data.get("volatility") is None`), and the
    critical-field gate (`critical_fields_config.validate_critical_fields`)
    only refuses a holding by name when the field is missing -- a `0.0`
    defeats both, making an unanalyzable holding look like the safest one in
    the portfolio. See Task 15 review round 1.

    """
    tech_signal = tech_result.overall_signal.value if tech_result is not None else "N/A"
    # 0.0 here is a real value, not a fabrication: `confidence` measures how
    # much basis this function had for its recommendation, and with no
    # technical signal to weigh, the honest amount of confidence is none.
    # Contrast with the risk_metrics fields above/below, where a substituted
    # 0.0 would misrepresent an unmeasured quantity (volatility, drawdown)
    # as a measured one of value zero -- that distinction is why those are
    # omitted but this is not. See Task 15 review round 2.
    tech_confidence = tech_result.overall_confidence if tech_result is not None else 0.0

    backtest_return = backtest_result.annualized_return if backtest_result is not None else None
    sharpe_ratio = backtest_result.sharpe_ratio if backtest_result is not None else None
    max_drawdown = backtest_result.max_drawdown if backtest_result is not None else None
    volatility = backtest_result.volatility if backtest_result is not None else None
    var_95 = backtest_result.var_95 if backtest_result is not None else None

    # Simple recommendation logic -- unknown backtest/sharpe inputs simply
    # don't trigger their branch rather than being treated as failing it.
    if tech_signal in ["BUY", "STRONG_BUY"] and backtest_return is not None and backtest_return > 10 and sharpe_ratio is not None and sharpe_ratio > 1.0:
        recommendation = "BUY"
        confidence = min(0.9, tech_confidence + 0.2)
    elif tech_signal in ["SELL", "STRONG_SELL"] or (backtest_return is not None and backtest_return < -5) or (sharpe_ratio is not None and sharpe_ratio < 0):
        recommendation = "SELL"
        confidence = min(0.9, tech_confidence + 0.1)
    else:
        recommendation = "HOLD"
        confidence = tech_confidence

    # Risk assessment -- an honest "unavailable" beats a fabricated "Moderate".
    if max_drawdown is not None and max_drawdown < -20:
        risk_assessment = "High risk due to significant drawdown potential"
    elif volatility is not None and volatility > 30:
        risk_assessment = "Moderate to high risk due to volatility"
    elif max_drawdown is not None or volatility is not None:
        risk_assessment = "Moderate risk profile"
    else:
        risk_assessment = "Risk assessment unavailable: backtest could not run for this series"

    backtest_performance = f"Annualized return: {backtest_return:.1f}%, Sharpe: {sharpe_ratio:.2f}" if backtest_return is not None and sharpe_ratio is not None else None
    key_indicators = _build_key_indicators(tech_result, tech_signal, tech_confidence)
    risk_metrics = _build_risk_metrics(max_drawdown, volatility, sharpe_ratio, var_95)

    return QuantitativeRecommendation(
        symbol=symbol,
        recommendation=recommendation,
        confidence=confidence,
        technical_signal=tech_signal,
        backtest_performance=backtest_performance,
        risk_assessment=risk_assessment,
        target_return=backtest_return if backtest_return is not None and backtest_return > 0 else None,
        target_timeframe="1 year",
        key_indicators=key_indicators,
        risk_metrics=risk_metrics,
    )
