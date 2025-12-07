# Quantitative Module

This directory contains all quantitative analysis functionality using professional-grade libraries: Backtrader, TA-Lib, QuantLib, and PyPortfolioOpt.

## Directory Structure

```
quantitative/
├── technical/                 # Technical analysis (decomposed)
│   ├── advanced_indicators.py # MACD, Bollinger, ATR
│   ├── basic_indicators.py    # SMA, EMA, RSI
│   ├── engine.py              # Technical analysis engine
│   ├── models.py              # Indicator models
│   ├── specialized_indicators.py # Sector-specific
│   └── technical_indicators.py   # Main indicator interface
│
├── backtesting.py             # MAIN: Backtrader integration
├── backtesting_models.py      # Backtest result models
├── backtesting_performance.py # Performance analysis
├── backtesting_strategies.py  # Trading strategies
├── backtesting_utils.py       # Backtest utilities
│
├── optimization.py            # MAIN: Portfolio optimization
├── optimization_algorithms.py # Optimization algorithms
├── objective_functions.py     # Optimization objectives
├── constraint_handlers.py     # Constraint handling
│
├── derivatives.py             # MAIN: QuantLib derivatives
├── derivative_pricing.py      # Option pricing
├── derivative_risk.py         # Greeks calculation
│
├── screening.py               # MAIN: Stock screening
├── screening_criteria.py      # Screening criteria
├── screening_filters.py       # Screening filters
├── screening_universes.py     # Stock universes
│
├── portfolio_analyzer.py      # Portfolio analysis
├── portfolio_monitor.py       # Real-time monitoring
├── portfolio_*.py             # Portfolio management
│
├── risk_*.py                  # Risk management
├── performance_*.py           # Performance metrics
├── scenario_*.py              # Scenario analysis
│
├── config.py                  # Main config entry point
├── config_manager.py          # Configuration management
├── config_validators.py       # Config validation
└── data.py                    # Data loading utilities
```

## Major Entry Points

### Backtesting (Backtrader)

| File | Class/Function | Purpose |
|------|---------------|---------|
| `backtesting.py` | `BacktestEngine` | Main backtest execution |
| `backtesting.py` | `run_backtest()` | Run strategy backtest |
| `backtesting_strategies.py` | `MomentumStrategy` | Momentum trading |
| `backtesting_strategies.py` | `MeanReversionStrategy` | Mean reversion |
| `backtesting_performance.py` | `calculate_metrics()` | Performance analysis |

### Portfolio Optimization (PyPortfolioOpt)

| File | Class/Function | Purpose |
|------|---------------|---------|
| `optimization.py` | `PortfolioOptimizer` | Main optimization |
| `optimization.py` | `optimize_portfolio()` | Run optimization |
| `optimization_algorithms.py` | `mean_variance()` | Mean-variance optimization |
| `optimization_algorithms.py` | `min_volatility()` | Minimum volatility |
| `optimization_algorithms.py` | `max_sharpe()` | Maximum Sharpe ratio |
| `objective_functions.py` | `sharpe_ratio()` | Sharpe objective |
| `objective_functions.py` | `sortino_ratio()` | Sortino objective |

### Technical Analysis (TA-Lib)

| File | Class/Function | Purpose |
|------|---------------|---------|
| `technical/engine.py` | `TechnicalAnalysisEngine` | Main technical engine |
| `technical/basic_indicators.py` | `calculate_sma()` | Simple moving average |
| `technical/basic_indicators.py` | `calculate_rsi()` | RSI indicator |
| `technical/advanced_indicators.py` | `calculate_macd()` | MACD indicator |
| `technical/advanced_indicators.py` | `calculate_bollinger()` | Bollinger bands |

### Derivatives (QuantLib)

| File | Class/Function | Purpose |
|------|---------------|---------|
| `derivatives.py` | `DerivativesPricer` | Main derivatives engine |
| `derivative_pricing.py` | `price_option()` | Option pricing |
| `derivative_pricing.py` | `price_bond()` | Bond pricing |
| `derivative_risk.py` | `calculate_greeks()` | Greeks calculation |

### Stock Screening

| File | Class/Function | Purpose |
|------|---------------|---------|
| `screening.py` | `StockScreener` | Main screening engine |
| `screening.py` | `screen_stocks()` | Run stock screen |
| `screening_criteria.py` | `ValueCriteria` | Value investing |
| `screening_criteria.py` | `GrowthCriteria` | Growth investing |
| `screening_filters.py` | `apply_filters()` | Apply screen filters |

### Risk Management

| File | Class/Function | Purpose |
|------|---------------|---------|
| `risk_manager.py` | `RiskManager` | Main risk engine |
| `risk_metrics.py` | `calculate_var()` | Value at Risk |
| `risk_metrics.py` | `calculate_cvar()` | Conditional VaR |
| `risk_calculations.py` | `volatility()` | Volatility calc |
| `risk_recommendations.py` | `get_recommendations()` | Risk reduction |

## Usage Examples

### Backtesting

```python
from finwiz.quantitative.backtesting import BacktestEngine
from finwiz.quantitative.backtesting_strategies import MomentumStrategy

engine = BacktestEngine()
result = engine.run(
    strategy=MomentumStrategy(lookback=20),
    tickers=["AAPL", "GOOGL", "MSFT"],
    start_date="2020-01-01",
    end_date="2023-12-31",
    initial_capital=100000
)
print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

### Portfolio Optimization

```python
from finwiz.quantitative.optimization import PortfolioOptimizer

optimizer = PortfolioOptimizer()
weights = optimizer.optimize(
    tickers=["AAPL", "GOOGL", "MSFT", "BND"],
    objective="max_sharpe",
    constraints={"max_position": 0.4, "min_position": 0.05}
)
print(weights)
# {'AAPL': 0.35, 'GOOGL': 0.25, 'MSFT': 0.30, 'BND': 0.10}
```

### Technical Analysis

```python
from finwiz.quantitative.technical.engine import TechnicalAnalysisEngine

engine = TechnicalAnalysisEngine()
indicators = engine.analyze(
    ticker="AAPL",
    indicators=["RSI", "MACD", "Bollinger"]
)
print(f"RSI: {indicators['RSI']:.2f}")
print(f"Signal: {indicators['signal']}")  # BUY/HOLD/SELL
```

### Stock Screening

```python
from finwiz.quantitative.screening import StockScreener
from finwiz.quantitative.screening_criteria import ValueCriteria

screener = StockScreener()
results = screener.screen(
    universe="SP500",
    criteria=ValueCriteria(
        max_pe=15,
        min_dividend_yield=0.02,
        max_debt_equity=0.5
    )
)
print(f"Found {len(results)} stocks matching criteria")
```

## Configuration

```python
from finwiz.quantitative.config_manager import QuantitativeConfigManager
from finwiz.schemas.quantitative.config_models import BacktestConfig

config = QuantitativeConfigManager()

# Load backtest config
backtest_config = config.get_backtest_config()

# Custom config
custom_config = BacktestConfig(
    initial_capital=100000,
    commission=0.001,
    slippage=0.0005,
    data_frequency="daily"
)
```

## Testing

```bash
# Test all quantitative modules
uv run pytest tests/unit/quantitative/ -v

# Test backtesting
uv run pytest tests/unit/quantitative/test_backtesting.py -v

# Test optimization
uv run pytest tests/unit/quantitative/test_optimization.py -v

# Performance tests
uv run pytest tests/unit/quantitative/ -m performance -v
```

## Related Modules

- `finwiz.tools.quantitative_analysis_tool` - CrewAI tool wrapper
- `finwiz.schemas.quantitative` - Pydantic models
- `finwiz.data.adapters` - Data source adapters
- `finwiz.scoring` - Scoring algorithms using quant metrics
