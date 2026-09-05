# Quantitative Module

Quantitative analysis using professional-grade libraries: TA-Lib, PyPortfolioOpt, QuantLib, Backtrader.

## Directory Structure

```
quantitative/
├── __init__.py                      # 35+ exports
│
├── # Core engines
├── backtesting.py                   # BacktestingEngine, get_backtesting_engine()
├── optimization.py                  # PortfolioOptimizer, EfficientFrontier
├── risk_manager.py                  # RiskManager (14 methods)
├── cost_analyzer.py                 # CostAnalyzer (19 methods)
├── performance.py                   # PerformanceAnalyzer, get_performance_analyzer()
├── data.py                          # HistoricalDataManager, DataQualityValidator
├── derivative_pricing.py            # BlackScholesCalculator, QuantLibPricer, SimpleBondPricer
│
├── # Backtesting subsystem
├── backtesting_models.py            # BacktestingResult, PositionSizingMethod
├── backtesting_strategies.py        # StrategyFramework, SimpleMovingAverageStrategy
├── backtesting_performance.py       # Performance analysis
├── backtesting_utils.py             # Backtest utilities
│
├── # Portfolio management
├── rebalancing_engine.py            # RebalancingEngine
├── rebalancing_history_tracker.py   # RebalancingHistoryTracker
├── trade_recommendation_system.py   # TradeRecommendationSystem
├── trade_generation.py              # TradeGenerator
├── execution_engine.py              # ExecutionEngine
├── monitoring_engine.py             # MonitoringEngine
├── scenario_analysis.py             # ScenarioAnalysisEngine
│
├── # Risk, performance, screening
├── risk_calculations.py             # Risk math
├── risk_recommendations.py          # Risk reduction suggestions
├── performance_metrics.py           # PerformanceMetrics
├── screening_criteria.py            # Screening criteria
├── screening_filters.py             # Screening filters
├── tactical_pricing.py              # Tactical price targets (uses central's
│                                     #  calculate_support_resistance_targets)
│
├── # Config
├── config.py                        # Module config entry point
├── config_manager.py                # Config management
├── config_defaults.py               # Default config
│
├── technical/                       # Technical analysis (TA-Lib wrappers)
│   ├── technical_indicators.py      # TALibWrappers (19 methods)
│   ├── engine.py                    # TechnicalAnalysisEngine, calculate_technical_indicators()
│   ├── basic_indicators.py          # SMA, EMA, RSI
│   ├── advanced_indicators.py       # MACD, Bollinger, ATR
│   ├── specialized_indicators.py    # Sector-specific indicators
│   └── models.py                    # Indicator models
│
├── etf/                             # ETF-specific metrics
│   └── etf_expense_fallback.py      # (etf_metrics.py moved to crewai-custom-tools; ETFAnalysisTool is agent-facing only)
│
└── risk/                            # Risk metrics
    └── risk_metrics.py              # calculate_var(), calculate_cvar(), calculate_sharpe_ratio()
```

## Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `backtesting.py` | `BacktestingEngine` | Run strategy backtests |
| `optimization.py` | `PortfolioOptimizer` | Portfolio optimization (mean-variance, etc.) |
| `risk_manager.py` | `RiskManager` | Risk assessment and limits |
| `cost_analyzer.py` | `CostAnalyzer` | Trading cost analysis |
| `performance.py` | `PerformanceAnalyzer` | Performance attribution |
| `technical/engine.py` | `TechnicalAnalysisEngine` | Technical indicator calculation |
| `rebalancing_engine.py` | `RebalancingEngine` | Portfolio rebalancing |
| `scenario_analysis.py` | `ScenarioAnalysisEngine` | What-if analysis |

## Usage

Backtesting is per-symbol and date-bounded; optimization takes a
`PortfolioInputs` object, not a ticker list.

```python
from finwiz.quantitative import BacktestingEngine, PortfolioOptimizer, RiskManager
from finwiz.quantitative.objective_functions import ObjectiveFunction
from finwiz.quantitative.config import OptimizationMethod

engine = BacktestingEngine()
result = engine.run_strategy_backtest(
    strategy_class=MyStrategy,
    symbol="AAPL",
    start_date=start,
    end_date=end,
    strategy_params={...},  # optional
    benchmark_symbol="SPY",  # optional
)  # -> BacktestResult | None

# Several strategies over one symbol
results = engine.run_multi_strategy_backtest(
    strategies=[(MyStrategy, {...}), (OtherStrategy, {...})],
    symbol="AAPL",
    start_date=start,
    end_date=end,
)

optimizer = PortfolioOptimizer()
result = optimizer.optimize_portfolio(
    inputs=portfolio_inputs,
    objective=ObjectiveFunction.MAX_SHARPE,
    method=OptimizationMethod.MEAN_VARIANCE,
)  # -> OptimizationResult
```

## Related Modules

- `finwiz.tools.quantitative_analysis_tool` — CrewAI tool wrapper
- `finwiz.schemas.quantitative` — Pydantic models for quant data
- `finwiz.scoring` — Scoring algorithms using quant metrics
