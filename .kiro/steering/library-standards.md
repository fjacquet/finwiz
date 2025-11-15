---
title: Library Standards for FinWiz
inclusion: always
---

# Library Standards for FinWiz

Standards and best practices for using key external libraries in the FinWiz codebase.

## aiohttp - Async HTTP Client

**Library**: `/aio-libs/aiohttp`  
**Purpose**: Asynchronous HTTP client/server framework for asyncio  
**Documentation**: https://github.com/aio-libs/aiohttp

### Core Principles

1. **Always use ClientSession** - Session encapsulates connection pooling and keepalives
2. **Use async context managers** - Ensures proper resource cleanup
3. **Reuse sessions** - Don't create a new session for each request

### Standard Usage Pattern

```python
import aiohttp
import asyncio

async def fetch_data(url: str) -> dict:
    """Fetch data from URL using aiohttp."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            assert response.status == 200
            return await response.json()

# Usage
async def main():
    data = await fetch_data('https://api.example.com/data')
    print(data)

asyncio.run(main())
```

### Session Configuration

```python
# Set default headers for all requests
headers = {"Authorization": "Bearer token123"}
async with aiohttp.ClientSession(headers=headers) as session:
    async with session.get("https://api.example.com") as response:
        data = await response.json()
```

### Request Parameters

```python
async def fetch_with_params(session: aiohttp.ClientSession, url: str) -> str:
    """Make request with query parameters and custom headers."""
    params = {'key': 'value', 'limit': 100}
    headers = {'User-Agent': 'FinWiz/1.0'}
    
    async with session.get(url, params=params, headers=headers) as response:
        return await response.text()
```

### Timeout Configuration

```python
# Set timeout for requests (default: 30 seconds)
timeout = aiohttp.ClientTimeout(total=30)
async with aiohttp.ClientSession(timeout=timeout) as session:
    async with session.get(url) as response:
        data = await response.json()
```

### Error Handling

```python
async def fetch_with_error_handling(url: str) -> dict:
    """Fetch data with proper error handling."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()  # Raise for 4xx/5xx
                return await response.json()
    except aiohttp.ClientError as e:
        logger.error(f"HTTP request failed: {e}")
        raise
    except asyncio.TimeoutError:
        logger.error(f"Request timeout for {url}")
        raise
```

### Best Practices

✅ **DO**:
- Use `ClientSession` as async context manager
- Reuse sessions across multiple requests
- Set appropriate timeouts
- Handle errors gracefully
- Use `response.raise_for_status()` to check status codes

❌ **DON'T**:
- Create new session for each request (overhead)
- Forget to await response methods (`.text()`, `.json()`)
- Leave sessions open (use context managers)
- Ignore timeout configuration

---

## yfinance - Yahoo Finance Data

**Library**: `/ranaroussi/yfinance`  
**Purpose**: Pythonic way to fetch financial and market data from Yahoo Finance  
**Documentation**: https://github.com/ranaroussi/yfinance

### Core Principles

1. **Use Ticker objects** - Primary interface for accessing stock data
2. **Cache data appropriately** - Yahoo Finance has rate limits
3. **Handle missing data** - Not all data is available for all tickers

### Standard Usage Pattern

```python
import yfinance as yf

# Single ticker
ticker = yf.Ticker("AAPL")

# Get stock info
info = ticker.info
print(info.get('longName'))
print(info.get('marketCap'))

# Get historical data
history = ticker.history(period="1y", interval="1d")
print(history.head())

# Get dividends and splits
dividends = ticker.dividends
splits = ticker.splits
```

### Multiple Tickers

```python
# Download data for multiple tickers
tickers = yf.Tickers('MSFT AAPL GOOG')

# Access individual ticker info
msft_info = tickers.tickers['MSFT'].info

# Download historical data for all
data = yf.download(['MSFT', 'AAPL', 'GOOG'], period='1mo')
```

### Historical Data Options

```python
# Get historical data with custom parameters
history = ticker.history(
    period="1y",        # Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval="1d",      # Valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    start="2023-01-01", # Alternative to period
    end="2023-12-31"
)
```

### Fast Info vs Full Info

```python
# Fast info (subset of essential data, faster)
fast_info = ticker.fast_info
print(fast_info)  # Current price, volume, daily change

# Full info (comprehensive, slower)
full_info = ticker.info
print(full_info.get('marketCap'))
print(full_info.get('trailingPE'))
```

### Additional Data

```python
# Get news
news = ticker.news
for article in news:
    print(f"Title: {article['title']}")

# Get actions (dividends + splits)
actions = ticker.actions

# Get institutional holders
institutional = ticker.institutional_holders

# Get major holders
major_holders = ticker.major_holders
```

### Error Handling

```python
def get_ticker_data(symbol: str) -> dict:
    """Get ticker data with error handling."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Check if ticker is valid
        if not info or 'regularMarketPrice' not in info:
            raise ValueError(f"Invalid ticker: {symbol}")
        
        return info
    except Exception as e:
        logger.error(f"Failed to fetch data for {symbol}: {e}")
        raise
```

### Best Practices

✅ **DO**:
- Use `fast_info` when you only need basic data
- Cache historical data to avoid repeated API calls
- Check for missing data before accessing
- Use `period` parameter for relative dates
- Handle rate limiting gracefully

❌ **DON'T**:
- Make excessive API calls (respect rate limits)
- Assume all data fields are present
- Use for real-time trading (data may be delayed)
- Ignore error handling

---

## PyPortfolioOpt - Portfolio Optimization

**Library**: `/robertmartin8/pyportfolioopt`  
**Purpose**: Financial portfolio optimization including efficient frontier, Black-Litterman, HRP  
**Documentation**: https://github.com/robertmartin8/pyportfolioopt

### Core Principles

1. **Calculate expected returns first** - Required for optimization
2. **Choose appropriate risk model** - Covariance, semicovariance, or CVaR
3. **Apply constraints** - Weight bounds, sector constraints, etc.
4. **Clean weights** - Round and remove tiny allocations

### Standard Usage Pattern

```python
from pypfopt import expected_returns, risk_models
from pypfopt.efficient_frontier import EfficientFrontier

# Load price data (pandas DataFrame)
prices = ...  # DataFrame with date index and ticker columns

# Calculate expected returns
mu = expected_returns.mean_historical_return(prices)

# Calculate risk model (covariance matrix)
S = risk_models.sample_cov(prices)

# Initialize efficient frontier
ef = EfficientFrontier(mu, S)

# Optimize for maximum Sharpe ratio
weights = ef.max_sharpe()

# Clean weights (round, remove tiny allocations)
cleaned_weights = ef.clean_weights()
print(cleaned_weights)

# Get portfolio performance
performance = ef.portfolio_performance(verbose=True)
# Returns: (expected_return, volatility, sharpe_ratio)
```

### Expected Returns Methods

```python
from pypfopt import expected_returns

# Mean historical return
mu = expected_returns.mean_historical_return(prices)

# Exponentially weighted mean (more weight on recent data)
mu = expected_returns.ema_historical_return(prices)

# CAPM return
mu = expected_returns.capm_return(prices)
```

### Risk Models

```python
from pypfopt import risk_models

# Sample covariance matrix
S = risk_models.sample_cov(prices)

# Semicovariance (downside risk only)
S = risk_models.semicovariance(prices)

# Exponentially weighted covariance
S = risk_models.exp_cov(prices)

# Ledoit-Wolf shrinkage (more stable)
S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()
```

### Optimization Objectives

```python
# Maximum Sharpe ratio
weights = ef.max_sharpe()

# Minimum volatility
weights = ef.min_volatility()

# Efficient return (target return)
weights = ef.efficient_return(target_return=0.20)

# Efficient risk (target volatility)
weights = ef.efficient_risk(target_volatility=0.15)
```

### Adding Constraints

```python
# Weight bounds (default: 0 to 1)
ef = EfficientFrontier(mu, S, weight_bounds=(0, 0.10))  # Max 10% per asset

# Custom constraints
ef.add_constraint(lambda w: w[0] >= 0.2)  # Min 20% in first asset
ef.add_constraint(lambda w: w[2] == 0.15)  # Exactly 15% in third asset
ef.add_constraint(lambda w: w[3] + w[4] <= 0.10)  # Max 10% combined

# Sector constraints
sector_mapper = {'AAPL': 'Tech', 'MSFT': 'Tech', 'JPM': 'Finance'}
sector_lower = {'Tech': 0.1}  # Min 10% in tech
sector_upper = {'Tech': 0.4, 'Finance': 0.3}  # Max allocations
ef.add_sector_constraints(sector_mapper, sector_lower, sector_upper)
```

### Semivariance Optimization (Downside Risk)

```python
from pypfopt import EfficientSemivariance

# Calculate expected returns and historical returns
mu = expected_returns.mean_historical_return(prices)
historical_returns = expected_returns.returns_from_prices(prices)

# Initialize semivariance optimizer
es = EfficientSemivariance(mu, historical_returns)

# Minimize semivariance for target return
es.efficient_return(target_return=0.20)

# Get weights and performance
weights = es.clean_weights()
performance = es.portfolio_performance(verbose=True)
# Returns: (expected_return, semivariance, sortino_ratio)
```

### CVaR Optimization (Conditional Value at Risk)

```python
from pypfopt.efficient_frontier import EfficientCVaR

# Initialize CVaR optimizer
ec = EfficientCVaR(mu, S, returns_data=historical_returns, beta=0.95)

# Minimize CVaR
ec.min_cvar()

# Get weights and performance
weights = ec.clean_weights()
performance = ec.portfolio_performance(verbose=True)
```

### Hierarchical Risk Parity (HRP)

```python
from pypfopt import HRPOpt

# Calculate returns
returns = expected_returns.returns_from_prices(prices)

# Initialize HRP optimizer
hrp = HRPOpt(returns)

# Optimize
hrp.optimize()

# Get weights
weights = hrp.clean_weights()
```

### Discrete Allocation

```python
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices

# Get latest prices
latest_prices = get_latest_prices(prices)

# Allocate portfolio with $10,000
da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=10000)

# Get allocation (number of shares to buy)
allocation, leftover = da.greedy_portfolio()
print(f"Discrete allocation: {allocation}")
print(f"Funds remaining: ${leftover:.2f}")
```

### Best Practices

✅ **DO**:
- Use appropriate risk model for your use case
- Apply realistic constraints (weight bounds, sector limits)
- Clean weights before implementation
- Use discrete allocation for actual trading
- Consider transaction costs
- Validate inputs (no NaN, sufficient history)

❌ **DON'T**:
- Use too short price history (min 1 year recommended)
- Ignore constraints (unconstrained can be extreme)
- Forget to clean weights (tiny allocations are impractical)
- Assume optimization is perfect (use as guidance)
- Over-optimize (in-sample vs out-of-sample)

### FinWiz Integration Pattern

```python
from pypfopt import expected_returns, risk_models
from pypfopt.efficient_frontier import EfficientFrontier

def optimize_portfolio(
    prices: pd.DataFrame,
    target_return: float = None,
    weight_bounds: tuple = (0, 0.10)
) -> dict:
    """
    Optimize portfolio using PyPortfolioOpt.
    
    Args:
        prices: DataFrame of historical prices
        target_return: Target annual return (optional)
        weight_bounds: Min/max weight per asset
        
    Returns:
        dict: Optimized portfolio weights
    """
    # Calculate inputs
    mu = expected_returns.mean_historical_return(prices)
    S = risk_models.sample_cov(prices)
    
    # Initialize optimizer
    ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
    
    # Optimize
    if target_return:
        ef.efficient_return(target_return)
    else:
        ef.max_sharpe()
    
    # Clean and return weights
    weights = ef.clean_weights()
    
    # Log performance
    perf = ef.portfolio_performance(verbose=False)
    logger.info(f"Expected return: {perf[0]:.2%}, Volatility: {perf[1]:.2%}, Sharpe: {perf[2]:.2f}")
    
    return weights
```

---

## Summary

These three libraries form the foundation of FinWiz's data fetching and portfolio optimization capabilities:

- **aiohttp**: Async HTTP requests for API calls
- **yfinance**: Financial data from Yahoo Finance
- **PyPortfolioOpt**: Portfolio optimization and allocation

Always refer to this document when implementing features using these libraries to ensure consistency and best practices across the codebase.

---

**Version**: 1.0  
**Created**: 2025-11-15  
**Source**: Context7 library documentation
