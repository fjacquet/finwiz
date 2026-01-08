# Backtrader Standards for FinWiz

Comprehensive standards for using backtrader in FinWiz quantitative analysis and backtesting.

## Core Principles

**Backtrader** is a Python framework for backtesting trading strategies with support for:

- Multiple data feeds and timeframes
- Built-in indicators and custom indicator development
- Strategy optimization and parameter tuning
- Performance analysis with analyzers and observers
- Live trading capabilities

## Cerebro Engine (Required)

All backtrader operations use the `Cerebro` engine as the central orchestrator.

### Standard Cerebro Initialization

```python
import backtrader as bt

cerebro = bt.Cerebro(
    preload=True,          # Preload data feeds for faster execution
    runonce=True,          # Run indicators in vectorized mode (faster)
    stdstats=True,         # Add default observers (Broker, Trades, BuySell)
    maxcpus=None,          # Use all cores for optimization
    exactbars=False,       # Keep all data in memory
    optdatas=True,         # Optimize data preloading
    optreturn=True         # Return optimization results
)
```

### Required Cerebro Configuration

```python
# Set initial cash
cerebro.broker.set_cash(100000.0)

# Set commission (e.g., 0.1% per trade)
cerebro.broker.setcommission(commission=0.001)

# Add data feed
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data, name='AAPL')

# Add strategy
cerebro.addstrategy(MyStrategy, period=20)

# Add analyzers
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

# Run backtest
results = cerebro.run()

# Access results
strategy = results[0]
sharpe = strategy.analyzers.sharpe.get_analysis()
drawdown = strategy.analyzers.drawdown.get_analysis()
```

## Strategy Development (Required)

### Standard Strategy Pattern

```python
class MyStrategy(bt.Strategy):
    """
    Standard backtrader strategy template.
    
    Attributes:
        params: Strategy parameters (tuples)
        order: Current order reference
        buyprice: Price at which position was opened
        buycomm: Commission paid on buy
    """
    
    params = (
        ('period', 20),           # SMA period
        ('stake', 100),           # Position size
        ('printlog', False),      # Print log messages
    )
    
    def __init__(self):
        """Initialize indicators and variables."""
        # Keep reference to close line
        self.dataclose = self.datas[0].close
        
        # Track pending orders
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # Add indicators
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], 
            period=self.params.period
        )
        
        # Create buy/sell signals
        self.crossover = bt.indicators.CrossOver(
            self.dataclose, 
            self.sma
        )
    
    def notify_order(self, order):
        """Handle order notifications."""
        if order.status in [order.Submitted, order.Accepted]:
            # Order submitted/accepted - no action
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                    f'Cost: {order.executed.value:.2f}, '
                    f'Comm: {order.executed.comm:.2f}'
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log(
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                    f'Cost: {order.executed.value:.2f}, '
                    f'Comm: {order.executed.comm:.2f}'
                )
            
            self.bar_executed = len(self)
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        
        # Reset order reference
        self.order = None
    
    def notify_trade(self, trade):
        """Handle trade notifications."""
        if not trade.isclosed:
            return
        
        self.log(
            f'OPERATION PROFIT, GROSS: {trade.pnl:.2f}, '
            f'NET: {trade.pnlcomm:.2f}'
        )
    
    def next(self):
        """Execute strategy logic on each bar."""
        # Log current close
        self.log(f'Close: {self.dataclose[0]:.2f}')
        
        # Check if order is pending
        if self.order:
            return
        
        # Check if we are in the market
        if not self.position:
            # Not in market - check for buy signal
            if self.crossover > 0:
                self.log(f'BUY CREATE, {self.dataclose[0]:.2f}')
                self.order = self.buy(size=self.params.stake)
        else:
            # In market - check for sell signal
            if self.crossover < 0:
                self.log(f'SELL CREATE, {self.dataclose[0]:.2f}')
                self.order = self.sell(size=self.params.stake)
    
    def log(self, txt, dt=None):
        """Logging function."""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
```

### Strategy Best Practices

**DO**:

- ✅ Initialize indicators in `__init__`
- ✅ Use `notify_order` and `notify_trade` for order/trade tracking
- ✅ Check `self.order` before creating new orders
- ✅ Use `self.position` to check market status
- ✅ Access data with `self.datas[0]` or `self.data`
- ✅ Use parameters for configurable values
- ✅ Log important events for debugging

**DON'T**:

- ❌ Create indicators in `next()` (performance issue)
- ❌ Place orders without checking pending orders
- ❌ Access future data (look-ahead bias)
- ❌ Hardcode values (use params instead)
- ❌ Ignore order/trade notifications

## Data Feeds (Required)

### Pandas Data Feed (Recommended for FinWiz)

```python
import backtrader as bt
import pandas as pd

# Create DataFrame with required columns
df = pd.DataFrame({
    'datetime': pd.date_range('2020-01-01', periods=100),
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...],
})
df.set_index('datetime', inplace=True)

# Create data feed
data = bt.feeds.PandasData(
    dataname=df,
    fromdate=pd.Timestamp('2020-01-01'),
    todate=pd.Timestamp('2020-12-31'),
    timeframe=bt.TimeFrame.Days
)

# Add to cerebro
cerebro.adddata(data, name='AAPL')
```

### Multiple Data Feeds

```python
# Add multiple tickers
data_aapl = bt.feeds.PandasData(dataname=df_aapl)
data_googl = bt.feeds.PandasData(dataname=df_googl)

cerebro.adddata(data_aapl, name='AAPL')
cerebro.adddata(data_googl, name='GOOGL')

# Access in strategy
class MultiDataStrategy(bt.Strategy):
    def __init__(self):
        self.sma_aapl = bt.indicators.SMA(self.datas[0], period=20)
        self.sma_googl = bt.indicators.SMA(self.datas[1], period=20)
```

### Resampling Data

```python
# Daily data resampled to weekly
data_daily = bt.feeds.PandasData(dataname=df_daily)
cerebro.adddata(data_daily, name='daily')
cerebro.resampledata(
    data_daily, 
    timeframe=bt.TimeFrame.Weeks,
    name='weekly'
)
```

## Indicators (Required)

### Built-in Indicators

```python
import backtrader.indicators as btind

class IndicatorStrategy(bt.Strategy):
    def __init__(self):
        # Moving averages
        self.sma = btind.SimpleMovingAverage(self.data, period=20)
        self.ema = btind.ExponentialMovingAverage(self.data, period=20)
        
        # Momentum indicators
        self.rsi = btind.RSI(self.data, period=14)
        self.macd = btind.MACD(self.data)
        
        # Volatility indicators
        self.bbands = btind.BollingerBands(self.data, period=20)
        self.atr = btind.ATR(self.data, period=14)
        
        # Volume indicators
        self.volume_sma = btind.SMA(self.data.volume, period=20)
        
        # Crossover signals
        self.crossover = btind.CrossOver(self.data.close, self.sma)
```

### Custom Indicators

```python
class CustomIndicator(bt.Indicator):
    """
    Custom indicator template.
    
    Lines define the output values.
    Params define configurable parameters.
    """
    
    lines = ('custom_line',)
    params = (
        ('period', 20),
        ('factor', 1.5),
    )
    
    def __init__(self):
        """Initialize indicator calculations."""
        # Use self.data to access input data
        # Use self.params to access parameters
        pass
    
    def next(self):
        """Calculate indicator value for current bar."""
        # Calculate and assign to line
        datasum = sum(self.data.get(size=self.params.period))
        self.lines.custom_line[0] = datasum / self.params.period
```

### Indicator Chaining

```python
class ChainedIndicators(bt.Strategy):
    def __init__(self):
        # Chain indicators
        sma1 = btind.SMA(self.data, period=20)
        sma2 = btind.SMA(sma1, period=10)  # SMA of SMA
        
        # Arithmetic operations
        diff = self.data.close - sma1
        ratio = self.data.close / sma1
        
        # Use results in other indicators
        sma_diff = btind.SMA(diff, period=5)
```

## Analyzers (Required)

### Standard Analyzers

```python
# Add analyzers to cerebro
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')

# Run and get results
results = cerebro.run()
strategy = results[0]

# Access analyzer results
sharpe = strategy.analyzers.sharpe.get_analysis()
drawdown = strategy.analyzers.drawdown.get_analysis()
returns = strategy.analyzers.returns.get_analysis()
trades = strategy.analyzers.trades.get_analysis()

print(f"Sharpe Ratio: {sharpe.get('sharperatio', 'N/A')}")
print(f"Max Drawdown: {drawdown.get('max', {}).get('drawdown', 'N/A'):.2f}%")
print(f"Total Return: {returns.get('rtot', 'N/A'):.2%}")
```

### TimeReturn Analyzer (for Benchmarking)

```python
# Track yearly returns
cerebro.addanalyzer(
    bt.analyzers.TimeReturn,
    timeframe=bt.TimeFrame.Years,
    _name='yearly_returns'
)

# Track returns for specific data feed
cerebro.addanalyzer(
    bt.analyzers.TimeReturn,
    timeframe=bt.TimeFrame.Years,
    data=data_benchmark,
    _name='benchmark_returns'
)

# Get results
results = cerebro.run()
strategy = results[0]
yearly = strategy.analyzers.yearly_returns.get_analysis()
benchmark = strategy.analyzers.benchmark_returns.get_analysis()
```

## Observers (Optional)

### Standard Observers

```python
# Observers are added automatically with stdstats=True
# To add custom observers:
cerebro.addobserver(bt.observers.Broker)
cerebro.addobserver(bt.observers.Trades)
cerebro.addobserver(bt.observers.BuySell)
cerebro.addobserver(bt.observers.DrawDown)
```

## Optimization (Advanced)

### Parameter Optimization

```python
# Use optstrategy instead of addstrategy
cerebro.optstrategy(
    MyStrategy,
    period=range(10, 31, 5),  # Test periods 10, 15, 20, 25, 30
    stake=range(50, 201, 50)  # Test stakes 50, 100, 150, 200
)

# Run optimization
results = cerebro.run(maxcpus=4)  # Use 4 cores

# Process results
for result in results:
    strategy = result[0]
    sharpe = strategy.analyzers.sharpe.get_analysis()
    print(f"Period: {strategy.params.period}, "
          f"Stake: {strategy.params.stake}, "
          f"Sharpe: {sharpe.get('sharperatio', 'N/A')}")
```

## FinWiz Integration Patterns

### Backtesting Tool Integration

```python
from finwiz.quantitative.backtesting import BacktestEngine
import backtrader as bt

class FinWizBacktestStrategy(bt.Strategy):
    """Strategy integrated with FinWiz backtesting."""
    
    params = (
        ('ticker', 'AAPL'),
        ('period', 20),
    )
    
    def __init__(self):
        self.sma = bt.indicators.SMA(self.data, period=self.params.period)
        self.crossover = bt.indicators.CrossOver(self.data.close, self.sma)
    
    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        else:
            if self.crossover < 0:
                self.sell()

# Use in FinWiz
def run_finwiz_backtest(ticker: str, df: pd.DataFrame) -> dict:
    """Run backtest using FinWiz data."""
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(100000.0)
    cerebro.broker.setcommission(commission=0.001)
    
    # Add data
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data, name=ticker)
    
    # Add strategy
    cerebro.addstrategy(FinWizBacktestStrategy, ticker=ticker)
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    # Run
    results = cerebro.run()
    strategy = results[0]
    
    # Extract results
    return {
        'ticker': ticker,
        'final_value': cerebro.broker.getvalue(),
        'sharpe_ratio': strategy.analyzers.sharpe.get_analysis().get('sharperatio'),
        'max_drawdown': strategy.analyzers.drawdown.get_analysis().get('max', {}).get('drawdown'),
        'total_return': strategy.analyzers.returns.get_analysis().get('rtot'),
    }
```

### Data Lineage Integration

```python
from finwiz.schemas.data_lineage import DataSource, CalculationStep
import backtrader as bt

class LineageAwareStrategy(bt.Strategy):
    """Strategy that tracks data lineage."""
    
    def __init__(self):
        self.sma = bt.indicators.SMA(self.data, period=20)
        
        # Track data source
        self.data_source = DataSource(
            provider="backtrader",
            endpoint="PandasData",
            timestamp=datetime.now(UTC),
            parameters={"ticker": self.params.ticker}
        )
    
    def next(self):
        # Track calculation steps
        calculation = CalculationStep(
            operation="sma_crossover_check",
            inputs={
                "close": float(self.data.close[0]),
                "sma": float(self.sma[0])
            },
            output=bool(self.data.close[0] > self.sma[0]),
            formula="close > sma",
            timestamp=datetime.now(UTC)
        )
        
        # Use in trading logic
        if not self.position and self.data.close[0] > self.sma[0]:
            self.buy()
```

## Testing Standards

### Unit Testing Strategies

```python
import pytest
import backtrader as bt
import pandas as pd

def test_strategy_initialization(mocker):
    """Test strategy initializes correctly."""
    # Create test data
    df = pd.DataFrame({
        'datetime': pd.date_range('2020-01-01', periods=100),
        'open': [100] * 100,
        'high': [105] * 100,
        'low': [95] * 100,
        'close': [100] * 100,
        'volume': [1000] * 100,
    })
    df.set_index('datetime', inplace=True)
    
    # Setup cerebro
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(MyStrategy, period=20)
    
    # Run
    results = cerebro.run()
    
    # Verify
    assert len(results) == 1
    assert results[0].params.period == 20

def test_strategy_performance(mocker):
    """Test strategy generates expected performance."""
    # Create test data with trend
    df = create_trending_data()
    
    # Setup and run
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(100000.0)
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(MyStrategy)
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    results = cerebro.run()
    strategy = results[0]
    returns = strategy.analyzers.returns.get_analysis()
    
    # Verify positive returns on trending data
    assert returns['rtot'] > 0
```

## Performance Best Practices

### Optimization Tips

1. **Use `runonce=True`**: Vectorized indicator calculation (faster)
2. **Use `preload=True`**: Preload all data (faster)
3. **Minimize logging**: Only log in debug mode
4. **Use built-in indicators**: Optimized C implementations
5. **Avoid complex calculations in `next()`**: Do in `__init__` when possible

### Memory Management

```python
# For large datasets, use exactbars
cerebro = bt.Cerebro(exactbars=True)  # Only keep necessary bars

# For optimization, limit data
cerebro = bt.Cerebro(optdatas=True)  # Optimize data handling
```

## Common Patterns

### Buy and Hold Strategy

```python
class BuyAndHold(bt.Strategy):
    def __init__(self):
        self.order = None
    
    def next(self):
        if not self.position and not self.order:
            self.order = self.buy()
```

### Mean Reversion Strategy

```python
class MeanReversion(bt.Strategy):
    params = (('period', 20), ('devfactor', 2))
    
    def __init__(self):
        self.bbands = bt.indicators.BollingerBands(
            self.data,
            period=self.params.period,
            devfactor=self.params.devfactor
        )
    
    def next(self):
        if not self.position:
            if self.data.close < self.bbands.lines.bot:
                self.buy()
        else:
            if self.data.close > self.bbands.lines.top:
                self.sell()
```

### Momentum Strategy

```python
class Momentum(bt.Strategy):
    params = (('period', 14),)
    
    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data, period=self.params.period)
    
    def next(self):
        if not self.position:
            if self.rsi < 30:  # Oversold
                self.buy()
        else:
            if self.rsi > 70:  # Overbought
                self.sell()
```

## Anti-Patterns (Avoid)

❌ **Creating indicators in `next()`** - Performance killer
❌ **Not checking pending orders** - Multiple order issues
❌ **Hardcoding parameters** - Use `params` instead
❌ **Look-ahead bias** - Don't access future data
❌ **Ignoring commissions** - Unrealistic results
❌ **Not using analyzers** - Missing performance metrics
❌ **Complex logic in `next()`** - Move to `__init__` or helpers
❌ **Not handling order notifications** - Lost order tracking

## Checklist

Before deploying a backtrader strategy:

- [ ] **Strategy inherits from `bt.Strategy`**
- [ ] **Parameters defined in `params` tuple**
- [ ] **Indicators initialized in `__init__`**
- [ ] **Order tracking in `notify_order`**
- [ ] **Trade tracking in `notify_trade`**
- [ ] **Pending orders checked before new orders**
- [ ] **Commission configured realistically**
- [ ] **Analyzers added for performance metrics**
- [ ] **Data feed properly formatted (OHLCV)**
- [ ] **No look-ahead bias in logic**
- [ ] **Logging available for debugging**
- [ ] **Unit tests cover strategy logic**

---

**Version**: 1.0  
**Created**: 2025-11-14  
**Purpose**: Standardize backtrader usage in FinWiz quantitative analysis
**Source**: Context7 backtrader documentation
