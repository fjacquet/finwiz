"""
Quantitative analysis tool for FinWiz crews.

This tool provides quantitative analysis capabilities including backtesting,
technical analysis, and performance metrics calculation for integration
into Stock, ETF, and Crypto crews.
"""

import json
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

            # Build complete technical data dict with numeric indicator values
            tech_data = quant_tech.model_dump()

            # Add numeric MACD values from raw_values
            # Note: This overwrites macd_signal string description with numeric value
            # The numeric value is needed by the scorer for calculations
            logger = get_logger(f"{__name__}.{self.__class__.__name__}")
            if "MACD" in tech_result.indicator_results:
                macd_result = tech_result.indicator_results["MACD"]
                if "MACD_line" in macd_result.raw_values and "MACD_signal" in macd_result.raw_values:
                    macd_line_values = macd_result.raw_values["MACD_line"]
                    macd_signal_values = macd_result.raw_values["MACD_signal"]

                    if isinstance(macd_line_values, list) and macd_line_values:
                        try:
                            macd_value = float(macd_line_values[-1])
                            # Check for NaN
                            if not (macd_value != macd_value):  # NaN check
                                tech_data["macd"] = macd_value
                                logger.debug(f"✅ Extracted MACD line: {macd_value}")
                            else:
                                logger.warning(f"⚠️ MACD line is NaN for {input_data.symbol}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"⚠️ Failed to convert MACD line for {input_data.symbol}: {e}")

                    if isinstance(macd_signal_values, list) and macd_signal_values:
                        try:
                            macd_signal_value = float(macd_signal_values[-1])
                            # Check for NaN
                            if not (macd_signal_value != macd_signal_value):  # NaN check
                                # Overwrite string description with numeric value (needed by scorer)
                                tech_data["macd_signal"] = macd_signal_value
                                logger.debug(f"✅ Extracted MACD signal: {macd_signal_value}")
                            else:
                                logger.warning(f"⚠️ MACD signal is NaN for {input_data.symbol}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"⚠️ Failed to convert MACD signal for {input_data.symbol}: {e}")

                    # Store description separately if needed
                    if macd_result.signals:
                        tech_data["macd_description"] = macd_result.signals[0].description
                else:
                    logger.warning(f"⚠️ MACD raw_values missing for {input_data.symbol}")

            # Add RSI numeric value
            if "RSI" in tech_result.indicator_results:
                rsi_result = tech_result.indicator_results["RSI"]
                if "RSI" in rsi_result.values:
                    rsi_values = rsi_result.values["RSI"]
                    if isinstance(rsi_values, list) and rsi_values:
                        tech_data["rsi"] = float(rsi_values[-1])

            # Add moving averages if available
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

            # Serialize with proper datetime handling
            return json.dumps(tech_data, indent=2, default=str)

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

            # Convert to dict for adding ETF-specific fields
            perf_dict = json.loads(quant_perf.model_dump_json())

            # Add ETF-specific metrics from Yahoo Finance
            if input_data.asset_class == "etf":
                logger = get_logger(f"{__name__}.{self.__class__.__name__}")
                try:
                    import yfinance as yf
                    
                    ticker = yf.Ticker(input_data.symbol)
                    info = ticker.info
                    
                    # Fetch expense ratio (try multiple fields)
                    expense_ratio = info.get("netExpenseRatio") or info.get("annualReportExpenseRatio")
                    if expense_ratio is not None:
                        # Yahoo Finance returns as percentage (0.0945 = 0.0945%)
                        # Scorer expects percentage as decimal (0.0945% → 0.000945 decimal)
                        # So we divide by 100: 0.0945 / 100 = 0.000945
                        expense_ratio_decimal = float(expense_ratio) / 100.0
                        perf_dict["expense_ratio"] = expense_ratio_decimal
                        logger.info(f"✅ Fetched expense_ratio for {input_data.symbol}: {expense_ratio}% → {expense_ratio_decimal:.6f} (as decimal)")
                    else:
                        # Try fallback configuration file
                        from finwiz.utils.etf_expense_fallback import get_fallback_expense_ratio
                        
                        fallback_ratio = get_fallback_expense_ratio(input_data.symbol)
                        if fallback_ratio is not None:
                            perf_dict["expense_ratio"] = fallback_ratio
                            logger.info(f"✅ Using fallback expense_ratio for {input_data.symbol}: {fallback_ratio:.6f} (as decimal)")
                        else:
                            logger.warning(f"⚠️ No expense_ratio available for {input_data.symbol} (Yahoo Finance or fallback)")
                    
                    # Fetch AUM (totalAssets)
                    total_assets = info.get("totalAssets")
                    if total_assets is not None:
                        perf_dict["aum"] = float(total_assets)
                        logger.info(f"✅ Fetched AUM for {input_data.symbol}: ${total_assets:,.0f}")
                    else:
                        logger.warning(f"⚠️ No AUM available for {input_data.symbol}")
                    
                    # Calculate tracking error using historical data
                    try:
                        # Determine appropriate benchmark based on ETF category
                        category = info.get("category", "").lower()
                        
                        # Map ETF category to benchmark
                        benchmark_map = {
                            "large blend": "SPY",  # S&P 500
                            "large growth": "QQQ",  # Nasdaq-100
                            "large value": "IVE",  # S&P 500 Value
                            "mid-cap blend": "MDY",  # S&P MidCap 400
                            "small blend": "IJR",  # S&P SmallCap 600
                            "foreign large blend": "VEA",  # Developed Markets
                            "diversified emerging mkts": "VWO",  # Emerging Markets
                            "intermediate core bond": "AGG",  # US Aggregate Bond
                        }
                        
                        # Default to SPY if category not found
                        benchmark_symbol = benchmark_map.get(category, "SPY")
                        
                        logger.info(f"Calculating tracking error for {input_data.symbol} vs {benchmark_symbol} (category: {category or 'unknown'})")
                        
                        # Fetch benchmark data
                        import yfinance as yf
                        benchmark = yf.Ticker(benchmark_symbol)
                        
                        # Get 1 year of historical data for both
                        etf_hist = ticker.history(period="1y")
                        benchmark_hist = benchmark.history(period="1y")
                        
                        if not etf_hist.empty and not benchmark_hist.empty:
                            # Calculate daily returns
                            etf_returns = etf_hist["Close"].pct_change().dropna()
                            benchmark_returns = benchmark_hist["Close"].pct_change().dropna()
                            
                            # Align dates (in case of different trading days)
                            aligned_etf, aligned_benchmark = etf_returns.align(benchmark_returns, join="inner")
                            
                            if len(aligned_etf) > 20:  # Need at least 20 days of data
                                # Calculate tracking difference
                                tracking_diff = aligned_etf - aligned_benchmark
                                
                                # Annualized tracking error (standard deviation of tracking difference)
                                tracking_error = tracking_diff.std() * (252 ** 0.5)
                                
                                perf_dict["tracking_error"] = float(tracking_error)
                                logger.info(f"✅ Calculated tracking_error for {input_data.symbol}: {tracking_error:.4f} ({tracking_error*100:.2f}%)")
                            else:
                                logger.warning(f"⚠️ Insufficient aligned data for tracking error calculation: {len(aligned_etf)} days")
                        else:
                            logger.warning(f"⚠️ No historical data available for tracking error calculation")
                            
                    except Exception as e:
                        logger.error(f"Error calculating tracking error for {input_data.symbol}: {e}")
                    
                except Exception as e:
                    logger.error(f"Error fetching ETF-specific data for {input_data.symbol}: {e}")

            return json.dumps(perf_dict, indent=2, default=str)

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

            # Add ETF-specific metrics if applicable
            etf_specific_data = {}
            if input_data.asset_class.lower() == "etf":
                logger = get_logger(f"{__name__}.{self.__class__.__name__}")
                try:
                    import yfinance as yf
                    
                    ticker = yf.Ticker(input_data.symbol)
                    info = ticker.info
                    
                    # Fetch expense ratio (try multiple fields)
                    expense_ratio = info.get("netExpenseRatio") or info.get("annualReportExpenseRatio")
                    if expense_ratio is not None:
                        expense_ratio_decimal = float(expense_ratio) / 100.0
                        etf_specific_data["expense_ratio"] = expense_ratio_decimal
                        logger.info(f"✅ Fetched expense_ratio for {input_data.symbol}: {expense_ratio}% → {expense_ratio_decimal:.6f}")
                    else:
                        # Try fallback configuration file
                        from finwiz.utils.etf_expense_fallback import get_fallback_expense_ratio
                        
                        fallback_ratio = get_fallback_expense_ratio(input_data.symbol)
                        if fallback_ratio is not None:
                            etf_specific_data["expense_ratio"] = fallback_ratio
                            logger.info(f"✅ Using fallback expense_ratio for {input_data.symbol}: {fallback_ratio:.6f}")
                        else:
                            logger.warning(f"⚠️ No expense_ratio available for {input_data.symbol}")
                    
                    # Fetch AUM
                    total_assets = info.get("totalAssets")
                    if total_assets is not None:
                        etf_specific_data["aum"] = float(total_assets)
                        logger.info(f"✅ Fetched AUM for {input_data.symbol}: ${total_assets:,.0f}")
                    else:
                        logger.warning(f"⚠️ No AUM available for {input_data.symbol}")
                        
                except Exception as e:
                    logger.error(f"Error fetching ETF-specific data for {input_data.symbol}: {e}")

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

            # Merge ETF-specific data into result dict
            result_dict = json.loads(result.model_dump_json())
            if etf_specific_data:
                result_dict.update(etf_specific_data)
            
            return json.dumps(result_dict, indent=2, default=str)

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
