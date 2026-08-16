"""
Backtesting tool for FinWiz investment discovery agents.

This tool provides comprehensive backtesting capabilities for validating A+ investment
candidates through historical analysis across multiple market regimes.
"""

from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Lazy imports to avoid circular dependencies
from finwiz.quantitative.backtesting import minimum_bars_required
from finwiz.quantitative.data import get_historical_data_manager
from finwiz.quantitative.performance import get_performance_analyzer
from finwiz.schemas.tools import BacktestingInput
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class MarketRegime(BaseModel):
    """Market regime analysis result."""

    regime_type: str = Field(..., description="Type of market regime (bull, bear, sideways)")
    start_date: datetime = Field(..., description="Regime start date")
    end_date: datetime = Field(..., description="Regime end date")
    duration_days: int = Field(..., description="Duration in days")
    market_return: float = Field(..., description="Market return during regime")
    strategy_return: float = Field(..., description="Strategy return during regime")
    outperformance: float = Field(..., description="Strategy outperformance vs market")
    sharpe_ratio: float = Field(..., description="Sharpe ratio during regime")
    max_drawdown: float = Field(..., description="Maximum drawdown during regime")


class BacktestingResult(BaseModel):
    """Comprehensive backtesting result with regime analysis."""

    # Basic backtest information
    symbol: str = Field(..., description="Symbol backtested")
    strategy_name: str = Field(..., description="Strategy used")
    backtest_period_years: int = Field(..., description="Backtesting period in years")

    # Overall performance metrics
    total_return: float = Field(..., description="Total return percentage")
    annualized_return: float = Field(..., description="Annualized return percentage")
    benchmark_return: float = Field(..., description="Benchmark total return percentage")
    excess_return: float = Field(..., description="Excess return vs benchmark")

    # Risk-adjusted metrics
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    calmar_ratio: float = Field(..., description="Calmar ratio")
    information_ratio: float = Field(..., description="Information ratio vs benchmark")

    # Risk metrics
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    volatility: float = Field(..., description="Annualized volatility")
    downside_deviation: float = Field(..., description="Downside deviation")
    var_95: float | None = Field(None, description="Value at Risk (95% confidence)")
    cvar_95: float | None = Field(None, description="Conditional Value at Risk (95%)")

    # Trade statistics
    total_trades: int = Field(..., description="Total number of trades")
    win_rate: float = Field(..., description="Win rate percentage")
    profit_factor: float | None = Field(None, description="Profit factor")

    # Multi-regime analysis
    regime_analysis: list[MarketRegime] = Field(default_factory=list, description="Performance across different market regimes")
    regime_consistency: float = Field(default=0.0, description="Consistency score across regimes (0-1)")

    # Validation metrics
    validation_score: float = Field(default=0.0, description="Overall validation score (0-1)")
    validation_passed: bool = Field(default=False, description="Whether the strategy passed validation criteria")
    validation_notes: list[str] = Field(default_factory=list, description="Validation notes and warnings")

    # Execution details
    backtest_start_date: datetime = Field(..., description="Backtest start date")
    backtest_end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(..., description="Initial capital used")
    final_value: float = Field(..., description="Final portfolio value")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")


class BacktestingTool(BaseTool):
    """
    Tool for comprehensive backtesting and historical validation of investment strategies.

    Provides multi-regime backtesting capabilities with risk-adjusted performance metrics
    specifically designed for validating A+ investment candidates.
    """

    name: str = "Backtesting Tool"
    description: str = (
        "Performs comprehensive historical backtesting with multi-regime analysis. "
        "Validates investment strategies across bull, bear, and sideways markets with "
        "risk-adjusted performance metrics including Sharpe, Sortino, and Calmar ratios. "
        "Use this tool to validate A+ investment candidates through rigorous historical analysis."
    )
    args_schema: type[BaseModel] = BacktestingInput

    def _run(
        self,
        symbol: str,
        strategy: str = "sma_crossover",
        backtest_period_years: int = 5,
        benchmark_symbol: str = "SPY",
        initial_capital: float = 100000.0,
        include_regime_analysis: bool = True,
        strategy_params: dict[str, Any] | None = None,
    ) -> str:
        """
        Execute comprehensive backtesting with multi-regime analysis.

        Args:
            symbol: Symbol to backtest
            strategy: Strategy to use for backtesting
            backtest_period_years: Backtesting period in years
            benchmark_symbol: Benchmark for comparison
            initial_capital: Initial capital for backtesting
            include_regime_analysis: Whether to include regime analysis
            strategy_params: Custom strategy parameters

        Returns:
            JSON string with comprehensive backtesting results

        """
        try:
            # Create input data object
            input_data = BacktestingInput(
                symbol=symbol,
                strategy=strategy,
                backtest_period_years=backtest_period_years,
                benchmark_symbol=benchmark_symbol,
                initial_capital=initial_capital,
                include_regime_analysis=include_regime_analysis,
                strategy_params=strategy_params or {},
            )

            logger.info(f"Starting backtesting for {input_data.symbol} with {input_data.strategy} strategy")

            # Initialize components
            from finwiz.quantitative.backtesting import get_backtesting_engine

            backtesting_engine = get_backtesting_engine()
            data_manager = get_historical_data_manager()
            get_performance_analyzer()

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=input_data.backtest_period_years * 365)

            # Run main backtest
            strategy_class = self._get_strategy_class(input_data.strategy)
            strategy_params = {**input_data.strategy_params}

            # Map common parameter name variations to standard names
            # This handles cases where external code uses different naming conventions
            param_mappings = {
                "short_window": "short_period",
                "long_window": "long_period",
                "window": "period",
            }

            for old_name, new_name in param_mappings.items():
                if old_name in strategy_params and new_name not in strategy_params:
                    strategy_params[new_name] = strategy_params.pop(old_name)
                    logger.info(f"Mapped strategy parameter '{old_name}' to '{new_name}'")

            # Note: initial_capital is set on the Cerebro broker, not passed to strategy
            # The backtesting engine handles this via the config

            backtest_result = backtesting_engine.run_strategy_backtest(
                strategy_class=strategy_class,
                symbol=input_data.symbol,
                start_date=start_date,
                end_date=end_date,
                strategy_params=strategy_params,
                benchmark_symbol=input_data.benchmark_symbol,
            )

            # A short series is a refusal, not a failure: the engine returns None
            # because backtrader would never reach the strategy's minperiod. Say
            # so by name -- reading attributes off the None instead produced
            # "Error performing backtesting: 'NoneType' object has no attribute
            # 'strategy_name'", which tells the reading agent nothing.
            if backtest_result is None:
                minimum_bars = minimum_bars_required(strategy_params)
                refusal = (
                    f"Insufficient data for {input_data.symbol}: {input_data.backtest_period_years}y of price history is shorter than the "
                    f"{minimum_bars} bars {strategy_class.__name__} needs (lookback + warm-up buffer). No backtest performed."
                )
                logger.info(refusal)
                return refusal

            # Calculate additional risk-adjusted metrics
            additional_metrics = self._calculate_additional_metrics(backtest_result)

            # Perform regime analysis if requested
            regime_analysis = []
            regime_consistency = 0.0

            if input_data.include_regime_analysis:
                regime_analysis, regime_consistency = self._perform_regime_analysis(
                    input_data.symbol,
                    input_data.benchmark_symbol,
                    start_date,
                    end_date,
                    strategy_class,
                    strategy_params,
                    backtesting_engine,
                    data_manager,
                )

            # Calculate validation score and determine if passed
            validation_score, validation_passed, validation_notes = self._validate_strategy(backtest_result, additional_metrics, regime_analysis)

            # Create comprehensive result
            result = BacktestingResult(
                symbol=input_data.symbol,
                strategy_name=backtest_result.strategy_name,
                backtest_period_years=input_data.backtest_period_years,
                total_return=backtest_result.total_return,
                annualized_return=backtest_result.annualized_return,
                benchmark_return=backtest_result.benchmark_return or 0.0,
                excess_return=backtest_result.total_return - (backtest_result.benchmark_return or 0.0),
                sharpe_ratio=backtest_result.sharpe_ratio,
                sortino_ratio=additional_metrics.get("sortino_ratio", 0.0),
                calmar_ratio=backtest_result.calmar_ratio or 0.0,
                information_ratio=additional_metrics.get("information_ratio", 0.0),
                max_drawdown=backtest_result.max_drawdown,
                volatility=backtest_result.volatility,
                downside_deviation=additional_metrics.get("downside_deviation", 0.0),
                var_95=backtest_result.var_95,
                cvar_95=backtest_result.cvar_95,
                total_trades=backtest_result.total_trades,
                win_rate=backtest_result.win_rate,
                profit_factor=additional_metrics.get("profit_factor"),
                regime_analysis=regime_analysis,
                regime_consistency=regime_consistency,
                validation_score=validation_score,
                validation_passed=validation_passed,
                validation_notes=validation_notes,
                backtest_start_date=backtest_result.start_date,
                backtest_end_date=backtest_result.end_date,
                initial_capital=backtest_result.initial_capital,
                final_value=backtest_result.final_value,
            )

            logger.info(
                f"Backtesting completed for {input_data.symbol}: "
                f"Total Return={result.total_return:.2f}%, "
                f"Sharpe={result.sharpe_ratio:.2f}, "
                f"Validation={'PASSED' if result.validation_passed else 'FAILED'}"
            )

            return result.model_dump_json(indent=2)

        except Exception as e:
            logger.error(f"Error in backtesting: {e}")
            return f"Error performing backtesting: {e!s}"

    def _get_strategy_class(self, strategy_name: str) -> type:
        """Get strategy class based on strategy name."""
        from finwiz.quantitative.backtesting_strategies import SimpleMovingAverageStrategy

        strategy_mapping = {
            "sma_crossover": SimpleMovingAverageStrategy,
            "buy_and_hold": SimpleMovingAverageStrategy,  # Can be extended with BuyAndHoldStrategy
            "momentum": SimpleMovingAverageStrategy,  # Can be extended with MomentumStrategy
        }

        return strategy_mapping.get(strategy_name, SimpleMovingAverageStrategy)

    def _calculate_additional_metrics(self, backtest_result: Any) -> dict[str, Any]:
        """Calculate additional risk-adjusted metrics not in the base result."""
        additional_metrics = {}

        try:
            # Calculate Sortino ratio if not available
            if hasattr(backtest_result, "portfolio_values") and backtest_result.portfolio_values:
                portfolio_df = pd.DataFrame(list(backtest_result.portfolio_values.items()), columns=["date", "value"])
                portfolio_df["date"] = pd.to_datetime(portfolio_df["date"])
                portfolio_df = portfolio_df.set_index("date").sort_index()

                # Calculate returns
                returns = portfolio_df["value"].pct_change().dropna()

                if len(returns) > 0:
                    # Sortino ratio
                    downside_returns = returns[returns < 0]
                    if len(downside_returns) > 0:
                        downside_deviation = downside_returns.std() * (252**0.5)
                        additional_metrics["downside_deviation"] = downside_deviation

                        if downside_deviation > 0:
                            additional_metrics["sortino_ratio"] = (backtest_result.annualized_return / 100 - 0.02) / (downside_deviation / 100)

                    # Information ratio (if benchmark available)
                    if backtest_result.benchmark_return is not None:
                        excess_return = backtest_result.annualized_return - backtest_result.benchmark_return
                        tracking_error = returns.std() * (252**0.5)
                        if tracking_error > 0:
                            additional_metrics["information_ratio"] = excess_return / tracking_error

                    # Profit factor (if trades available)
                    if hasattr(backtest_result, "trades") and backtest_result.trades:
                        winning_trades = [t for t in backtest_result.trades if t.pnl and t.pnl > 0]
                        losing_trades = [t for t in backtest_result.trades if t.pnl and t.pnl < 0]

                        if winning_trades and losing_trades:
                            gross_profit = sum(t.pnl for t in winning_trades)
                            gross_loss = abs(sum(t.pnl for t in losing_trades))
                            if gross_loss > 0:
                                additional_metrics["profit_factor"] = gross_profit / gross_loss

        except Exception as e:
            logger.warning(f"Error calculating additional metrics: {e}")

        return additional_metrics

    def _perform_regime_analysis(
        self,
        symbol: str,
        benchmark_symbol: str,
        start_date: datetime,
        end_date: datetime,
        strategy_class: type,
        strategy_params: dict[str, Any],
        backtesting_engine: Any,
        data_manager: Any,
    ) -> tuple[list[MarketRegime], float]:
        """Perform multi-regime backtesting analysis."""
        try:
            # Get benchmark data to identify regimes
            benchmark_data = data_manager.fetch_historical_data(benchmark_symbol, start_date, end_date)

            if benchmark_data.empty:
                logger.warning("No benchmark data available for regime analysis")
                return [], 0.0

            # Identify market regimes
            regimes = self._identify_market_regimes(benchmark_data)

            regime_results = []
            regime_returns = []

            for regime in regimes:
                try:
                    # Run backtest for this regime period
                    regime_result = backtesting_engine.run_strategy_backtest(
                        strategy_class=strategy_class,
                        symbol=symbol,
                        start_date=regime["start_date"],
                        end_date=regime["end_date"],
                        strategy_params=strategy_params,
                        benchmark_symbol=benchmark_symbol,
                    )

                    # Regimes are sub-periods of the backtest window, so they are
                    # routinely shorter than the strategy's minimum -- this is the
                    # most-hit refusal of the three. Drop the regime and say why:
                    # the surrounding except used to catch the AttributeError from
                    # reading the None and log it as an error, and inventing a 0.0
                    # return instead would report a missing measurement as a real one.
                    if regime_result is None:
                        minimum_bars = minimum_bars_required(strategy_params)
                        logger.info(
                            f"Insufficient data for the {regime['type']} regime of {symbol} "
                            f"({regime['start_date']} to {regime['end_date']}): shorter than the {minimum_bars} bars "
                            f"{strategy_class.__name__} needs. Regime omitted from regime analysis and consistency scoring."
                        )
                        continue

                    # Calculate regime-specific metrics
                    regime_analysis = MarketRegime(
                        regime_type=regime["type"],
                        start_date=regime["start_date"],
                        end_date=regime["end_date"],
                        duration_days=(regime["end_date"] - regime["start_date"]).days,
                        market_return=regime["market_return"],
                        strategy_return=regime_result.total_return,
                        outperformance=regime_result.total_return - regime["market_return"],
                        sharpe_ratio=regime_result.sharpe_ratio,
                        max_drawdown=regime_result.max_drawdown,
                    )

                    regime_results.append(regime_analysis)
                    regime_returns.append(regime_result.total_return)

                except Exception as e:
                    logger.warning(f"Error analyzing {regime['type']} regime: {e}")
                    continue

            # Calculate regime consistency (lower standard deviation = higher consistency)
            regime_consistency = 0.0
            if len(regime_returns) > 1:
                returns_std = pd.Series(regime_returns).std()
                returns_mean = pd.Series(regime_returns).mean()
                if returns_mean != 0:
                    # Coefficient of variation (inverted and normalized)
                    cv = abs(returns_std / returns_mean)
                    regime_consistency = max(0.0, 1.0 - min(cv / 2.0, 1.0))

            return regime_results, regime_consistency

        except Exception as e:
            logger.error(f"Error in regime analysis: {e}")
            return [], 0.0

    def _identify_market_regimes(self, benchmark_data: pd.DataFrame) -> list[dict[str, Any]]:
        """Identify bull, bear, and sideways market regimes."""
        regimes = []

        try:
            # Check if data is empty or missing required columns
            if benchmark_data.empty or "Close" not in benchmark_data.columns:
                logger.warning("Empty or invalid benchmark data for regime analysis")
                return regimes

            # Calculate rolling returns for regime identification
            benchmark_data = benchmark_data.copy()
            benchmark_data["returns"] = benchmark_data["Close"].pct_change()
            benchmark_data["cumulative"] = (1 + benchmark_data["returns"]).cumprod()

            # Simple regime identification based on rolling periods
            window = 252  # 1 year rolling window
            if len(benchmark_data) < window * 2:
                # If not enough data, treat entire period as one regime
                total_return = (benchmark_data["Close"].iloc[-1] / benchmark_data["Close"].iloc[0] - 1) * 100
                regime_type = "bull" if total_return > 10 else "bear" if total_return < -10 else "sideways"

                regimes.append(
                    {
                        "type": regime_type,
                        "start_date": benchmark_data.index[0],
                        "end_date": benchmark_data.index[-1],
                        "market_return": total_return,
                    }
                )
                return regimes

            # Identify regimes based on rolling performance
            benchmark_data["rolling_return"] = benchmark_data["returns"].rolling(window).sum() * 100

            current_regime = None
            regime_start = benchmark_data.index[window]

            for i in range(window, len(benchmark_data)):
                rolling_return = benchmark_data["rolling_return"].iloc[i]

                # Determine regime type
                if rolling_return > 15:  # Bull market threshold
                    regime_type = "bull"
                elif rolling_return < -15:  # Bear market threshold
                    regime_type = "bear"
                else:
                    regime_type = "sideways"

                # Check for regime change
                if current_regime is None:
                    current_regime = regime_type
                elif current_regime != regime_type:
                    # End current regime
                    regime_end = benchmark_data.index[i - 1]
                    regime_return = (benchmark_data["Close"].loc[regime_end] / benchmark_data["Close"].loc[regime_start] - 1) * 100

                    regimes.append(
                        {
                            "type": current_regime,
                            "start_date": regime_start,
                            "end_date": regime_end,
                            "market_return": regime_return,
                        }
                    )

                    # Start new regime
                    current_regime = regime_type
                    regime_start = benchmark_data.index[i]

            # Add final regime
            if current_regime is not None:
                regime_return = (benchmark_data["Close"].iloc[-1] / benchmark_data["Close"].loc[regime_start] - 1) * 100

                regimes.append(
                    {
                        "type": current_regime,
                        "start_date": regime_start,
                        "end_date": benchmark_data.index[-1],
                        "market_return": regime_return,
                    }
                )

            # Ensure we have at least one regime
            if not regimes:
                total_return = (benchmark_data["Close"].iloc[-1] / benchmark_data["Close"].iloc[0] - 1) * 100
                regime_type = "bull" if total_return > 10 else "bear" if total_return < -10 else "sideways"

                regimes.append(
                    {
                        "type": regime_type,
                        "start_date": benchmark_data.index[0],
                        "end_date": benchmark_data.index[-1],
                        "market_return": total_return,
                    }
                )

        except Exception as e:
            logger.error(f"Error identifying market regimes: {e}")
            # Fallback: single regime for entire period (only if data is valid)
            if not benchmark_data.empty and "Close" in benchmark_data.columns and len(benchmark_data) > 0:
                try:
                    total_return = (benchmark_data["Close"].iloc[-1] / benchmark_data["Close"].iloc[0] - 1) * 100
                    regime_type = "bull" if total_return > 10 else "bear" if total_return < -10 else "sideways"

                    regimes.append(
                        {
                            "type": regime_type,
                            "start_date": benchmark_data.index[0],
                            "end_date": benchmark_data.index[-1],
                            "market_return": total_return,
                        }
                    )
                except (KeyError, ValueError, TypeError, IndexError) as e:
                    # If even fallback fails, return empty regimes
                    logger.warning(f"Fallback regime identification also failed: {e}")
                    pass

        return regimes

    def _validate_strategy(
        self,
        backtest_result: Any,
        additional_metrics: dict[str, Any],
        regime_analysis: list[MarketRegime],
    ) -> tuple[float, bool, list[str]]:
        """Validate strategy performance and calculate validation score."""
        validation_notes = []
        score_components = []

        # 1. Minimum return requirement (25% weight)
        min_annual_return = 8.0  # 8% minimum annual return
        return_score = min(1.0, max(0.0, backtest_result.annualized_return / min_annual_return))
        score_components.append(return_score * 0.25)

        if backtest_result.annualized_return < min_annual_return:
            validation_notes.append(f"Annual return {backtest_result.annualized_return:.1f}% below minimum {min_annual_return}%")

        # 2. Sharpe ratio requirement (20% weight)
        min_sharpe = 1.0
        sharpe_score = min(1.0, max(0.0, backtest_result.sharpe_ratio / min_sharpe))
        score_components.append(sharpe_score * 0.20)

        if backtest_result.sharpe_ratio < min_sharpe:
            validation_notes.append(f"Sharpe ratio {backtest_result.sharpe_ratio:.2f} below minimum {min_sharpe}")

        # 3. Maximum drawdown requirement (20% weight)
        max_allowed_drawdown = -25.0  # -25% maximum drawdown
        drawdown_score = min(1.0, max(0.0, 1.0 + backtest_result.max_drawdown / max_allowed_drawdown))
        score_components.append(drawdown_score * 0.20)

        if backtest_result.max_drawdown < max_allowed_drawdown:
            validation_notes.append(f"Max drawdown {backtest_result.max_drawdown:.1f}% exceeds limit {max_allowed_drawdown}%")

        # 4. Win rate requirement (15% weight)
        min_win_rate = 0.45  # 45% minimum win rate
        win_rate_score = min(1.0, max(0.0, backtest_result.win_rate / min_win_rate))
        score_components.append(win_rate_score * 0.15)

        if backtest_result.win_rate < min_win_rate:
            validation_notes.append(f"Win rate {backtest_result.win_rate:.1%} below minimum {min_win_rate:.1%}")

        # 5. Regime consistency requirement (20% weight)
        min_consistency = 0.6  # 60% minimum consistency across regimes
        consistency_score = 0.0
        if regime_analysis:
            # Check if strategy performs reasonably in different regimes
            regime_returns = [r.strategy_return for r in regime_analysis]
            positive_regimes = sum(1 for r in regime_returns if r > 0)
            consistency_score = min(1.0, positive_regimes / len(regime_returns))

            if consistency_score < min_consistency:
                validation_notes.append(f"Regime consistency {consistency_score:.1%} below minimum {min_consistency:.1%}")

        score_components.append(consistency_score * 0.20)

        # Calculate overall validation score
        validation_score = sum(score_components)

        # Determine if validation passed (require 70% overall score)
        validation_threshold = 0.70
        validation_passed = validation_score >= validation_threshold

        if not validation_passed:
            validation_notes.append(f"Overall validation score {validation_score:.1%} below threshold {validation_threshold:.1%}")

        # Add positive notes for good performance
        if not validation_notes:
            validation_notes.append("Strategy passed all validation criteria")

        return validation_score, validation_passed, validation_notes


def get_backtesting_tool() -> BacktestingTool:
    """Create backtesting tool instance."""
    return BacktestingTool()
