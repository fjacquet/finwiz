"""
Quantitative analysis tool for FinWiz crews.

This tool provides quantitative analysis capabilities including backtesting,
technical analysis, and performance metrics calculation for integration
into Stock, ETF, and Crypto crews.
"""

from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from crewai.tools import BaseTool
from pydantic import BaseModel

from finwiz.quantitative.backtesting import (
    BacktestingEngine,
    SimpleMovingAverageStrategy,
    get_backtesting_engine,
)
from finwiz.quantitative.data import get_historical_data_manager
from finwiz.quantitative.performance import (
    PerformanceAnalyzer,
    get_performance_analyzer,
)
from finwiz.quantitative.technical import TechnicalAnalysisEngine
from finwiz.schemas.quantitative_crew import (
    EnhancedCryptoAnalysis,
    EnhancedETFAnalysis,
    EnhancedStockAnalysis,
    QuantitativeBacktestResult,
    QuantitativePerformanceMetrics,
    QuantitativeRecommendation,
    QuantitativeTechnicalAnalysis,
)
from finwiz.schemas.tools import QuantitativeAnalysisInput
from finwiz.tools.logger import get_logger


class QuantitativeAnalysisTool(BaseTool):
    """
    Tool for performing quantitative analysis on financial instruments.

    Provides comprehensive quantitative analysis including:
    - Technical analysis with multiple indicators
    - Strategy backtesting with performance metrics
    - Risk-adjusted performance analysis
    - Investment recommendations based on quantitative signals
    """

    name: str = "Quantitative Analysis Tool"
    description: str = (
        "Performs comprehensive quantitative analysis including technical analysis, "
        "backtesting, and performance metrics calculation. Supports stocks, ETFs, and cryptocurrencies. "
        "Use this tool to get data-driven investment insights and recommendations."
    )
    args_schema: type[BaseModel] = QuantitativeAnalysisInput

    def _run(
        self,
        symbol: str,
        asset_class: str,
        analysis_type: str = "comprehensive",
        timeframe: str = "1y",
        strategy: str = "sma_crossover",
        benchmark: str | None = None,
        prefetched_data: pd.DataFrame | None = None,
    ) -> str:
        """
        Execute quantitative analysis.

        Args:
            symbol: Symbol to analyze (e.g., AAPL, SPY, BTC-USD)
            asset_class: Asset class: 'stock', 'etf', or 'crypto'
            analysis_type: Type of analysis: 'technical', 'backtest', 'performance', or 'comprehensive'
            timeframe: Analysis timeframe (e.g., '1y', '2y', '5y')
            strategy: Strategy for backtesting
            benchmark: Benchmark symbol for comparison
            prefetched_data: Optional pre-fetched historical data from batch operation

        Returns:
            JSON string with quantitative analysis results

        """
        try:
            # Create input data object
            input_data = QuantitativeAnalysisInput(
                symbol=symbol,
                asset_class=asset_class,
                analysis_type=analysis_type,
                timeframe=timeframe,
                strategy=strategy,
                benchmark=benchmark,
            )

            # Initialize components
            data_manager = get_historical_data_manager()
            backtesting_engine = get_backtesting_engine()
            performance_analyzer = get_performance_analyzer()
            technical_engine = TechnicalAnalysisEngine()
            logger = get_logger(f"{__name__}.{self.__class__.__name__}")

            logger.info(f"Starting quantitative analysis for {input_data.symbol}")

            # Determine date range
            end_date = datetime.now()
            if input_data.timeframe == "1y":
                start_date = end_date - timedelta(days=365)
            elif input_data.timeframe == "2y":
                start_date = end_date - timedelta(days=730)
            elif input_data.timeframe == "5y":
                start_date = end_date - timedelta(days=1825)
            else:
                start_date = end_date - timedelta(days=365)  # Default to 1 year

            # Use pre-fetched data if available, otherwise fetch from API
            if prefetched_data is not None and not prefetched_data.empty:
                logger.debug(f"Using pre-fetched data for {input_data.symbol} (source: batch)")
                data = prefetched_data
            else:
                # Fetch historical data from API
                logger.debug(f"Fetching live data for {input_data.symbol} (source: API)")
                try:
                    data = data_manager.fetch_historical_data(input_data.symbol, start_date, end_date)
                    if data.empty:
                        return f"No data available for {input_data.symbol}"
                except Exception as e:
                    logger.error(f"Error fetching data for {input_data.symbol}: {e}")
                    return f"Error fetching data: {str(e)}"

            # Perform analysis based on type
            if input_data.analysis_type == "technical":
                result = self._perform_technical_analysis(data, input_data, technical_engine)
            elif input_data.analysis_type == "backtest":
                result = self._perform_backtesting(data, input_data, start_date, end_date, backtesting_engine)
            elif input_data.analysis_type == "performance":
                result = self._perform_performance_analysis(data, input_data, performance_analyzer)
            else:  # comprehensive
                result = self._perform_comprehensive_analysis(data, input_data, start_date, end_date, technical_engine, backtesting_engine, performance_analyzer)

            logger.info(f"Quantitative analysis completed for {input_data.symbol}")
            return result

        except Exception as e:
            logger.error(f"Error in quantitative analysis: {e}")
            return f"Error performing quantitative analysis: {str(e)}"

    def _perform_technical_analysis(self, data: pd.DataFrame, input_data: QuantitativeAnalysisInput, technical_engine: TechnicalAnalysisEngine) -> str:
        """Perform technical analysis."""
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

            return quant_tech.model_dump_json(indent=2)

        except Exception as e:
            logger = get_logger(f"{__name__}.{self.__class__.__name__}")
            logger.error(f"Error in technical analysis: {e}")
            return f"Technical analysis error: {str(e)}"

    def _perform_backtesting(
        self,
        data: pd.DataFrame,
        input_data: QuantitativeAnalysisInput,
        start_date: datetime,
        end_date: datetime,
        backtesting_engine: BacktestingEngine,
    ) -> str:
        """Perform backtesting analysis."""
        try:
            # Run backtest with simple moving average strategy
            backtest_result = backtesting_engine.run_strategy_backtest(
                SimpleMovingAverageStrategy,
                input_data.symbol,
                start_date,
                end_date,
                strategy_params={"short_period": 20, "long_period": 50},
            )

            # Convert to simplified schema
            quant_backtest = QuantitativeBacktestResult(
                symbol=input_data.symbol,
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

            return quant_backtest.model_dump_json(indent=2)

        except Exception as e:
            logger = get_logger(f"{__name__}.{self.__class__.__name__}")
            logger.error(f"Error in backtesting: {e}")
            return f"Backtesting error: {str(e)}"

    def _perform_performance_analysis(self, data: pd.DataFrame, input_data: QuantitativeAnalysisInput, performance_analyzer: PerformanceAnalyzer) -> str:
        """Perform performance analysis."""
        try:
            # Calculate returns
            returns = data["Close"].pct_change().dropna()

            # Run performance analysis
            perf_report = performance_analyzer.analyze_performance(returns, strategy_name=f"{input_data.symbol}_analysis")

            # Convert to simplified schema
            metrics = perf_report.strategy_metrics
            quant_perf = QuantitativePerformanceMetrics(
                symbol=input_data.symbol,
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
                total_days=len(returns),
            )

            return quant_perf.model_dump_json(indent=2)

        except Exception as e:
            logger = get_logger(f"{__name__}.{self.__class__.__name__}")
            logger.error(f"Error in performance analysis: {e}")
            return f"Performance analysis error: {str(e)}"

    def _perform_comprehensive_analysis(
        self,
        data: pd.DataFrame,
        input_data: QuantitativeAnalysisInput,
        start_date: datetime,
        end_date: datetime,
        technical_engine: TechnicalAnalysisEngine,
        backtesting_engine: BacktestingEngine,
        performance_analyzer: PerformanceAnalyzer,
    ) -> str:
        """Perform comprehensive quantitative analysis."""
        try:
            # Technical analysis
            tech_result = technical_engine.analyze_symbol(data, input_data.symbol, timeframe="1d")

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

            # Backtesting
            backtest_result = backtesting_engine.run_strategy_backtest(
                SimpleMovingAverageStrategy,
                input_data.symbol,
                start_date,
                end_date,
                strategy_params={"short_period": 20, "long_period": 50},
            )

            quant_backtest = QuantitativeBacktestResult(
                symbol=input_data.symbol,
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

            # Performance analysis
            returns = data["Close"].pct_change().dropna()
            perf_report = performance_analyzer.analyze_performance(returns, strategy_name=f"{input_data.symbol}_analysis")

            metrics = perf_report.strategy_metrics
            quant_perf = QuantitativePerformanceMetrics(
                symbol=input_data.symbol,
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
                start_date=datetime.now(),
                end_date=datetime.now(),
                total_days=len(returns),
            )

            # Generate recommendation
            recommendation = self._generate_recommendation(input_data.symbol, tech_result, backtest_result, metrics)

            # Create comprehensive result based on asset class
            if input_data.asset_class.lower() == "stock":
                result = EnhancedStockAnalysis(
                    ticker=input_data.symbol,
                    technical_analysis=quant_tech,
                    backtest_result=quant_backtest,
                    performance_metrics=quant_perf,
                    quantitative_recommendation=recommendation,
                )
            elif input_data.asset_class.lower() == "etf":
                result = EnhancedETFAnalysis(
                    ticker=input_data.symbol,
                    technical_analysis=quant_tech,
                    backtest_result=quant_backtest,
                    performance_metrics=quant_perf,
                    quantitative_recommendation=recommendation,
                )
            else:  # crypto
                result = EnhancedCryptoAnalysis(
                    symbol=input_data.symbol,
                    technical_analysis=quant_tech,
                    backtest_result=quant_backtest,
                    performance_metrics=quant_perf,
                    quantitative_recommendation=recommendation,
                )

            return result.model_dump_json(indent=2)

        except Exception as e:
            logger = get_logger(f"{__name__}.{self.__class__.__name__}")
            logger.error(f"Error in comprehensive analysis: {e}")
            return f"Comprehensive analysis error: {str(e)}"

    def _generate_recommendation(self, symbol: str, tech_result: Any, backtest_result: Any, perf_metrics: Any) -> QuantitativeRecommendation:
        """Generate investment recommendation based on quantitative analysis."""
        # Determine recommendation based on signals
        tech_signal = tech_result.overall_signal.value
        backtest_return = backtest_result.annualized_return
        sharpe_ratio = backtest_result.sharpe_ratio

        # Simple recommendation logic
        if tech_signal in ["BUY", "STRONG_BUY"] and backtest_return > 10 and sharpe_ratio > 1.0:
            recommendation = "BUY"
            confidence = min(0.9, tech_result.overall_confidence + 0.2)
        elif tech_signal in ["SELL", "STRONG_SELL"] or backtest_return < -5 or sharpe_ratio < 0:
            recommendation = "SELL"
            confidence = min(0.9, tech_result.overall_confidence + 0.1)
        else:
            recommendation = "HOLD"
            confidence = tech_result.overall_confidence

        # Risk assessment
        if backtest_result.max_drawdown < -20:
            risk_assessment = "High risk due to significant drawdown potential"
        elif backtest_result.volatility > 30:
            risk_assessment = "Moderate to high risk due to volatility"
        else:
            risk_assessment = "Moderate risk profile"

        return QuantitativeRecommendation(
            symbol=symbol,
            recommendation=recommendation,
            confidence=confidence,
            technical_signal=tech_signal,
            backtest_performance=f"Annualized return: {backtest_return:.1f}%, Sharpe: {sharpe_ratio:.2f}",
            risk_assessment=risk_assessment,
            target_return=backtest_return if backtest_return > 0 else None,
            target_timeframe="1 year",
            key_indicators={
                "technical_signal": tech_signal,
                "technical_confidence": tech_result.overall_confidence,
                "bullish_signals": tech_result.bullish_signals,
                "bearish_signals": tech_result.bearish_signals,
            },
            risk_metrics={
                "max_drawdown": backtest_result.max_drawdown,
                "volatility": backtest_result.volatility,
                "sharpe_ratio": sharpe_ratio,
                "var_95": backtest_result.var_95 or 0,
            },
        )


def get_quantitative_analysis_tool() -> QuantitativeAnalysisTool:
    """Create quantitative analysis tool."""
    return QuantitativeAnalysisTool()
