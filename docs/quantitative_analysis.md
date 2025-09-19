# Quantitative Analysis Framework

FinWiz includes a comprehensive quantitative analysis framework that provides professional-grade financial modeling, backtesting, and analytics capabilities. This framework is built on industry-standard libraries and follows best practices for quantitative finance.

## Overview

The quantitative analysis framework consists of several interconnected modules:

- **Backtesting Engine**: Strategy development and backtesting using Backtrader
- **Technical Analysis**: Technical indicator calculation and signal generation using TA-Lib
- **Performance Analytics**: Risk-adjusted performance metrics and portfolio optimization
- **Derivatives Pricing**: Options and bond pricing using QuantLib
- **Portfolio Optimization**: Modern portfolio theory implementation
- **Stock Screening**: Multi-criteria stock filtering and ranking

## Architecture

### Core Modules

```
src/finwiz/quantitative/
├── __init__.py              # Module exports and factory functions
├── config.py                # Configuration classes and settings
├── data.py                  # Historical data management
├── backtesting.py           # Backtrader-based backtesting engine
├── technical.py             # TA-Lib technical analysis engine
├── performance.py           # Performance analytics and optimization
├── derivatives.py           # QuantLib derivatives pricing
├── optimization.py          # Portfolio optimization algorithms
└── screening.py             # Stock screening and filtering
```

### Integration Points

The quantitative framework integrates with the existing FinWiz architecture through:

1. **QuantitativeAnalysisTool**: CrewAI tool for crew integration
2. **Quantitative Schemas**: Pydantic models in `src/finwiz/schemas/quantitative.py`
3. **Configuration System**: Environment variables and config classes
4. **Caching Layer**: Intelligent caching for expensive computations

## Backtesting Engine

### Features

- **Strategy Framework**: Base class for custom trading strategies
- **Risk Management**: Built-in stop-loss, take-profit, and position sizing
- **Performance Metrics**: Comprehensive analysis including Sharpe ratio, drawdown
- **Multi-Strategy Support**: Compare multiple strategies simultaneously
- **Trade Analysis**: Detailed trade-by-trade analysis and statistics

### Usage Example

```python
from finwiz.quantitative import get_backtesting_engine, SimpleMovingAverageStrategy
from datetime import datetime

# Initialize backtesting engine
engine = get_backtesting_engine()

# Run backtest
result = engine.run_strategy_backtest(
    strategy_class=SimpleMovingAverageStrategy,
    symbol="AAPL",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2024, 1, 1),
    strategy_params={"short_period": 20, "long_period": 50}
)

print(f"Total Return: {result.total_return:.2f}%")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.2f}%")
```

### Custom Strategy Development

```python
from finwiz.quantitative.backtesting import StrategyFramework
import backtrader as bt

class CustomStrategy(StrategyFramework):
    params = (
        ("period", 20),
        ("stop_loss_pct", 0.05),
        ("take_profit_pct", 0.15),
    )
    
    def __init__(self):
        super().__init__()
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.period
        )
    
    def next(self):
        super().next()
        
        if not self.position:
            if self.datas[0].close[0] > self.sma[0]:
                size = self.calculate_position_size(self.datas[0].close[0])
                self.buy(size=size)
        else:
            if self.datas[0].close[0] < self.sma[0]:
                self.sell(size=self.position.size)
```

## Technical Analysis Engine

### Supported Indicators

- **Trend Indicators**: SMA, EMA, MACD, ADX
- **Momentum Indicators**: RSI, Stochastic, CCI, Williams %R
- **Volatility Indicators**: Bollinger Bands, ATR
- **Support/Resistance**: Fibonacci retracements, pivot points

### Signal Generation

```python
from finwiz.quantitative.technical import TechnicalAnalysisEngine, TechnicalIndicator

engine = TechnicalAnalysisEngine()

# Analyze with multiple indicators
result = engine.analyze_symbol(
    data=price_data,
    symbol="AAPL",
    timeframe="1d",
    indicators=[
        TechnicalIndicator.RSI,
        TechnicalIndicator.MACD,
        TechnicalIndicator.BOLLINGER_BANDS
    ]
)

print(f"Overall Signal: {result.overall_signal}")
print(f"Confidence: {result.overall_confidence:.2f}")
print(f"Bullish Signals: {result.bullish_signals_count}")
print(f"Bearish Signals: {result.bearish_signals_count}")
```

### Confluence Detection

The engine automatically detects confluence zones where multiple indicators provide similar signals:

```python
# Confluence zones are included in the analysis result
for zone in result.confluence_zones:
    print(f"Confluence at {zone.price_level}: {zone.signal_type}")
    print(f"Contributing signals: {len(zone.contributing_signals)}")
    print(f"Confidence: {zone.confidence:.2f}")
```

## Performance Analytics

### Risk-Adjusted Metrics

```python
from finwiz.quantitative import get_performance_analyzer

analyzer = get_performance_analyzer()

# Analyze strategy performance
report = analyzer.analyze_performance(
    returns=strategy_returns,
    benchmark_returns=benchmark_returns,
    strategy_name="My Strategy",
    benchmark_name="S&P 500"
)

# Access comprehensive metrics
metrics = report.performance_metrics
print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"Sortino Ratio: {metrics.sortino_ratio:.2f}")
print(f"Maximum Drawdown: {metrics.max_drawdown:.2f}%")
print(f"VaR (95%): {metrics.var_95:.2f}%")
```

### Portfolio Optimization

```python
# Optimize portfolio using modern portfolio theory
optimization_result = analyzer.optimize_portfolio(
    price_data=price_data,
    method="max_sharpe",
    total_portfolio_value=100000
)

print("Optimal Weights:")
for asset, weight in optimization_result.weights.items():
    print(f"  {asset}: {weight:.2%}")

print(f"Expected Return: {optimization_result.expected_annual_return:.2%}")
print(f"Volatility: {optimization_result.annual_volatility:.2%}")
print(f"Sharpe Ratio: {optimization_result.sharpe_ratio:.2f}")
```

## Derivatives Pricing

### Options Pricing

```python
from finwiz.quantitative.derivatives import (
    DerivativesPricer, OptionParameters, OptionType, PricingModel
)

pricer = DerivativesPricer()

# Define option parameters
option_params = OptionParameters(
    underlying_price=100.0,
    strike_price=105.0,
    time_to_expiry=0.25,  # 3 months
    risk_free_rate=0.05,
    volatility=0.20,
    option_type=OptionType.CALL
)

# Price the option
result = pricer.price_option(option_params, PricingModel.BLACK_SCHOLES)

print(f"Option Price: ${result.option_price:.2f}")
print(f"Delta: {result.greeks.delta:.3f}")
print(f"Gamma: {result.greeks.gamma:.3f}")
print(f"Theta: {result.greeks.theta:.3f}")
print(f"Vega: {result.greeks.vega:.3f}")
```

### Implied Volatility

```python
# Calculate implied volatility from market price
market_price = 3.50
implied_vol = pricer.calculate_implied_volatility(market_price, option_params)
print(f"Implied Volatility: {implied_vol:.2%}")
```

### Bond Analytics

```python
from finwiz.quantitative.derivatives import BondParameters

bond_params = BondParameters(
    face_value=1000.0,
    coupon_rate=0.05,
    years_to_maturity=5.0,
    yield_to_maturity=0.04,
    coupon_frequency=2
)

bond_result = pricer.price_bond(bond_params)

print(f"Bond Price: ${bond_result.bond_price:.2f}")
print(f"Duration: {bond_result.duration:.2f}")
print(f"Convexity: {bond_result.convexity:.2f}")
```

## Portfolio Optimization

### Modern Portfolio Theory

```python
from finwiz.quantitative.optimization import (
    PortfolioOptimizer, PortfolioInputs, ObjectiveFunction, OptimizationMethod
)

optimizer = PortfolioOptimizer()

# Define portfolio inputs
inputs = PortfolioInputs(
    symbols=["AAPL", "MSFT", "GOOGL", "AMZN"],
    expected_returns=[0.12, 0.10, 0.15, 0.14],
    covariance_matrix=covariance_matrix,
    risk_free_rate=0.03
)

# Optimize for maximum Sharpe ratio
result = optimizer.optimize_portfolio(
    inputs=inputs,
    objective=ObjectiveFunction.MAX_SHARPE,
    method=OptimizationMethod.MEAN_VARIANCE
)

print("Optimal Portfolio:")
for symbol, weight in zip(inputs.symbols, result.optimal_weights):
    print(f"  {symbol}: {weight:.2%}")
```

### Efficient Frontier

```python
# Generate efficient frontier
frontier = optimizer.generate_efficient_frontier(inputs, num_points=50)

print(f"Number of efficient portfolios: {len(frontier.points)}")
print(f"Max Sharpe portfolio return: {frontier.max_sharpe_portfolio.expected_return:.2%}")
print(f"Min volatility portfolio risk: {frontier.min_volatility_portfolio.volatility:.2%}")
```

## Stock Screening

### Multi-Criteria Screening

```python
from finwiz.quantitative.screening import (
    StockScreener, ScreeningFilter, ScreeningCriteria, ScreeningUniverse
)

screener = StockScreener()

# Define screening criteria
filters = [
    ScreeningFilter(
        criteria=ScreeningCriteria.PE_RATIO,
        min_value=5.0,
        max_value=20.0,
        weight=1.0
    ),
    ScreeningFilter(
        criteria=ScreeningCriteria.ROE,
        min_value=0.15,
        weight=1.5
    ),
    ScreeningFilter(
        criteria=ScreeningCriteria.DEBT_TO_EQUITY,
        max_value=0.5,
        weight=1.0
    )
]

# Screen S&P 500 stocks
results, summary = screener.screen_stocks(
    filters=filters,
    universe=ScreeningUniverse.SP500,
    max_results=20
)

print(f"Screened {summary.total_stocks_screened} stocks")
print(f"Found {len(results)} qualifying stocks")

for result in results[:5]:
    print(f"{result.symbol}: Score {result.screening_score.total_score:.1f}, "
          f"Recommendation: {result.recommendation}")
```

### Predefined Screens

```python
# Use predefined screening strategies
predefined_screens = screener.get_predefined_screens()

# Value stocks screen
value_results, _ = screener.screen_stocks(
    filters=predefined_screens["value_stocks"],
    universe=ScreeningUniverse.SP500
)

# Growth stocks screen
growth_results, _ = screener.screen_stocks(
    filters=predefined_screens["growth_stocks"],
    universe=ScreeningUniverse.SP500
)
```

## Configuration

### Environment Variables

```bash
# Quantitative analysis configuration
QUANTITATIVE_ENABLED=true
BACKTEST_INITIAL_CAPITAL=100000
BACKTEST_COMMISSION=0.001
RISK_FREE_RATE=0.02

# Data provider settings
YFINANCE_ENABLED=true
DATA_CACHE_TTL=3600

# Optional library features
QUANTLIB_ENABLED=false
PYPFOPT_ENABLED=false
PLOTLY_ENABLED=false
```

### Configuration Classes

```python
from finwiz.quantitative.config import BacktestConfig, QuantConfig

# Backtesting configuration
backtest_config = BacktestConfig(
    initial_capital=100000.0,
    commission_pct=0.001,
    stop_loss_pct=0.05,
    take_profit_pct=0.15,
    max_drawdown_limit=0.20
)

# General quantitative configuration
quant_config = QuantConfig(
    risk_free_rate=0.02,
    confidence_level=0.95,
    lookback_period=252,
    min_data_points=50
)
```

## Integration with Crews

### Using QuantitativeAnalysisTool

```python
from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool

# Add to crew tools
tools = [
    QuantitativeAnalysisTool(),
    # ... other tools
]

# Use in agent task
result = quantitative_tool.run(
    symbol="AAPL",
    asset_class="stock",
    analysis_type="comprehensive",
    timeframe="1y"
)
```

### Enhanced Schemas

The quantitative framework provides enhanced schemas for crew outputs:

```python
from finwiz.schemas.quantitative import (
    EnhancedStockAnalysis,
    QuantitativeRecommendation,
    QuantitativeBacktestResult
)

# Enhanced stock analysis with quantitative data
enhanced_analysis = EnhancedStockAnalysis(
    ticker="AAPL",
    company_name="Apple Inc.",
    technical_analysis=technical_result,
    backtest_result=backtest_result,
    performance_metrics=performance_metrics,
    quantitative_recommendation=recommendation
)
```

## Testing

The quantitative framework includes comprehensive test coverage:

### Unit Tests

```bash
# Run quantitative unit tests
uv run pytest tests/unit/quantitative/ -v

# Run specific module tests
uv run pytest tests/unit/quantitative/test_backtesting.py -v
uv run pytest tests/unit/quantitative/test_technical.py -v
uv run pytest tests/unit/quantitative/test_performance.py -v
```

### Integration Tests

```bash
# Run quantitative integration tests
uv run pytest tests/integration/test_quantitative_analysis_integration.py -v
```

### Test Structure

- **Unit Tests**: Test individual components in isolation with mocked dependencies
- **Integration Tests**: Test end-to-end workflows with real data
- **Performance Tests**: Validate computational performance and accuracy
- **Mock Strategy**: All external data sources are mocked for deterministic testing

## Dependencies

### Required Dependencies

- **backtrader**: Strategy backtesting framework
- **ta-lib**: Technical analysis library
- **numpy**: Numerical computing
- **pandas**: Data manipulation
- **yfinance**: Historical data provider

### Optional Dependencies

- **QuantLib**: Advanced derivatives pricing
- **PyPortfolioOpt**: Portfolio optimization
- **plotly**: Interactive visualizations
- **scipy**: Statistical functions

### Installation

```bash
# Install required dependencies
uv pip install backtrader ta-lib numpy pandas yfinance

# Install optional dependencies
uv pip install QuantLib PyPortfolioOpt plotly scipy

# Note: TA-Lib may require system-level installation
# macOS: brew install ta-lib
# Ubuntu: sudo apt-get install libta-lib-dev
```

## Performance Considerations

### Caching

The quantitative framework leverages FinWiz's intelligent caching system:

- **Data Caching**: Historical price data cached with configurable TTL
- **Computation Caching**: Expensive calculations cached across sessions
- **Result Caching**: Analysis results cached for repeated queries

### Optimization

- **Vectorized Operations**: Use NumPy and Pandas for efficient computation
- **Parallel Processing**: Multi-threading for independent calculations
- **Memory Management**: Efficient data structures and garbage collection
- **Lazy Loading**: Load data and libraries only when needed

## Best Practices

### Strategy Development

1. **Start Simple**: Begin with basic strategies before adding complexity
2. **Validate Logic**: Test strategy logic with known market conditions
3. **Risk Management**: Always implement stop-loss and position sizing
4. **Out-of-Sample Testing**: Reserve data for final validation
5. **Walk-Forward Analysis**: Test strategy robustness over time

### Technical Analysis

1. **Multiple Timeframes**: Analyze across different timeframes
2. **Confluence**: Look for agreement between multiple indicators
3. **Context**: Consider market regime and volatility environment
4. **Validation**: Backtest technical signals before implementation
5. **Overfitting**: Avoid over-optimization of parameters

### Performance Analysis

1. **Risk-Adjusted Metrics**: Focus on risk-adjusted returns
2. **Benchmark Comparison**: Always compare to relevant benchmarks
3. **Statistical Significance**: Ensure sufficient data for valid conclusions
4. **Regime Analysis**: Analyze performance across different market conditions
5. **Transaction Costs**: Include realistic transaction costs in analysis

## Troubleshooting

### Common Issues

1. **TA-Lib Installation**: Requires system-level library installation
2. **Data Quality**: Ensure clean, complete price data
3. **Memory Usage**: Large datasets may require chunking
4. **Numerical Precision**: Be aware of floating-point precision issues
5. **Library Compatibility**: Ensure compatible versions of dependencies

### Debugging

```python
# Enable detailed logging
import logging
logging.getLogger('finwiz.quantitative').setLevel(logging.DEBUG)

# Validate data quality
from finwiz.quantitative.data import DataQualityValidator
validator = DataQualityValidator()
quality_report = validator.validate_data(price_data)

# Check configuration
from finwiz.quantitative.config import get_quant_config
config = get_quant_config()
print(f"Risk-free rate: {config.risk_free_rate}")
```

## Future Enhancements

### Planned Features

- **Machine Learning Integration**: ML-based signal generation
- **Alternative Data**: Integration with alternative data sources
- **Real-Time Analysis**: Live market data integration
- **Advanced Strategies**: More sophisticated trading strategies
- **Risk Models**: Advanced risk modeling and stress testing

### Extensibility

The framework is designed for easy extension:

- **Custom Indicators**: Add new technical indicators
- **Strategy Templates**: Create strategy templates for common patterns
- **Data Providers**: Integrate additional data sources
- **Optimization Methods**: Implement new optimization algorithms
- **Risk Models**: Add custom risk models and metrics

For questions or contributions, please refer to the main FinWiz documentation and development guidelines.