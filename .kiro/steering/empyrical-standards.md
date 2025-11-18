---
title: Empyrical Standards for FinWiz
inclusion: always
---

# Empyrical Standards for FinWiz

## Overview

Empyrical-Reloaded is our standard library for calculating financial risk and performance metrics. It provides battle-tested implementations of common metrics like Sharpe ratio, maximum drawdown, alpha, and beta.

**Library**: `/stefan-jansen/empyrical-reloaded`  
**Documentation**: https://github.com/stefan-jansen/empyrical-reloaded  
**Current Version**: 0.5.12+  
**Status**: ✅ Installed and ready to use

**Note**: We use `empyrical-reloaded` (the maintained fork) instead of the original `empyrical` which has Python 3.12 compatibility issues.

## Core Principles

1. **Use Empyrical for risk/performance metrics** - Don't implement custom Sharpe ratio, drawdown, etc.
2. **Works with NumPy and Pandas** - Accepts both arrays and Series
3. **Returns-based calculations** - All functions work on return series, not prices
4. **Benchmark comparisons** - Supports alpha/beta calculations against benchmarks

## Key Metrics Available

### Risk Metrics

```python
import numpy as np
from empyrical import (
    max_drawdown,
    annual_volatility,
    downside_risk,
    value_at_risk,
    conditional_value_at_risk
)

returns = np.array([.01, .02, .03, -.4, -.06, -.02])

# Maximum Drawdown (peak-to-trough decline)
max_dd = max_drawdown(returns)
print(f"Max Drawdown: {max_dd:.2%}")  # e.g., -40.00%

# Annual Volatility (standard deviation of returns)
vol = annual_volatility(returns, period='daily')
print(f"Annual Volatility: {vol:.2%}")

# Downside Risk (volatility of negative returns)
downside = downside_risk(returns)
print(f"Downside Risk: {downside:.2%}")

# Value at Risk (95% confidence)
var_95 = value_at_risk(returns, cutoff=0.05)
print(f"VaR (95%): {var_95:.2%}")

# Conditional VaR (Expected Shortfall)
cvar_95 = conditional_value_at_risk(returns, cutoff=0.05)
print(f"CVaR (95%): {cvar_95:.2%}")
```

### Performance Metrics

```python
from empyrical import (
    sharpe_ratio,
    sortino_ratio,
    calmar_ratio,
    omega_ratio,
    alpha_beta
)

returns = np.array([.01, .02, .03, -.4, -.06, -.02])
benchmark_returns = np.array([.02, .02, .03, -.35, -.05, -.01])

# Sharpe Ratio (risk-adjusted return)
sharpe = sharpe_ratio(returns, risk_free=0.02, period='daily')
print(f"Sharpe Ratio: {sharpe:.2f}")

# Sortino Ratio (downside risk-adjusted return)
sortino = sortino_ratio(returns, required_return=0.0, period='daily')
print(f"Sortino Ratio: {sortino:.2f}")

# Calmar Ratio (return / max drawdown)
calmar = calmar_ratio(returns, period='daily')
print(f"Calmar Ratio: {calmar:.2f}")

# Alpha and Beta (vs benchmark)
alpha, beta = alpha_beta(returns, benchmark_returns, risk_free=0.02)
print(f"Alpha: {alpha:.4f}, Beta: {beta:.2f}")
```

### Rolling Metrics

```python
from empyrical import (
    roll_max_drawdown,
    roll_sharpe_ratio,
    roll_up_capture,
    roll_down_capture
)

returns = np.array([.01, .02, .03, -.4, -.06, -.02, .01, .03, .02, -.01])

# Rolling Maximum Drawdown (3-period window)
rolling_dd = roll_max_drawdown(returns, window=3)
print(f"Rolling Max DD: {rolling_dd}")

# Rolling Sharpe Ratio (60-day window)
rolling_sharpe = roll_sharpe_ratio(returns, window=60)

# Up/Down Capture Ratios
up_capture = roll_up_capture(returns, window=60)
down_capture = roll_down_capture(returns, window=60)
```

## Pandas Integration

```python
import pandas as pd
from empyrical import max_drawdown, sharpe_ratio, alpha_beta

# Works seamlessly with Pandas Series
returns = pd.Series([.01, .02, .03, -.4, -.06, -.02])
benchmark = pd.Series([.02, .02, .03, -.35, -.05, -.01])

# Calculate metrics
max_dd = max_drawdown(returns)
sharpe = sharpe_ratio(returns, risk_free=0.02)
alpha, beta = alpha_beta(returns, benchmark)

print(f"Max Drawdown: {max_dd:.2%}")
print(f"Sharpe Ratio: {sharpe:.2f}")
print(f"Alpha: {alpha:.4f}, Beta: {beta:.2f}")
```

## FinWiz Integration Pattern

### Risk Scoring with Empyrical

```python
from empyrical import max_drawdown, annual_volatility, alpha_beta
import numpy as np

class RiskScorer:
    """Risk assessment using Empyrical metrics."""
    
    def calculate_risk_metrics(self, returns: np.ndarray, benchmark_returns: np.ndarray = None):
        """Calculate risk metrics using Empyrical."""
        
        # Volatility (annualized)
        volatility = annual_volatility(returns, period='daily')
        
        # Maximum Drawdown
        max_dd = abs(max_drawdown(returns))
        
        # Beta (if benchmark provided)
        if benchmark_returns is not None:
            alpha, beta = alpha_beta(returns, benchmark_returns)
        else:
            beta = 1.0
        
        return {
            'volatility': volatility,
            'max_drawdown': max_dd,
            'beta': beta
        }
    
    def score_risk_metrics(self, metrics: dict) -> float:
        """Apply FinWiz scoring thresholds to Empyrical metrics."""
        
        # Volatility scoring (FinWiz business logic)
        vol = metrics['volatility']
        if vol <= 0.10:
            vol_score = 1.0
        elif vol <= 0.15:
            vol_score = 0.8
        elif vol <= 0.25:
            vol_score = 0.6
        else:
            vol_score = 0.4
        
        # Drawdown scoring (FinWiz business logic)
        dd = metrics['max_drawdown']
        if dd <= 0.10:
            dd_score = 1.0
        elif dd <= 0.20:
            dd_score = 0.8
        else:
            dd_score = 0.6
        
        # Beta scoring (FinWiz business logic)
        beta = metrics['beta']
        beta_deviation = abs(beta - 1.0)
        if beta_deviation <= 0.20:
            beta_score = 1.0
        else:
            beta_score = 0.8
        
        # Weighted composite (FinWiz weights)
        risk_score = 0.50 * vol_score + 0.30 * dd_score + 0.20 * beta_score
        
        return risk_score
```

### Backtesting Integration

```python
from empyrical import (
    sharpe_ratio,
    max_drawdown,
    annual_return,
    calmar_ratio
)

def analyze_backtest_results(returns: np.ndarray) -> dict:
    """Analyze backtest using Empyrical metrics."""
    
    return {
        'annual_return': annual_return(returns, period='daily'),
        'sharpe_ratio': sharpe_ratio(returns, period='daily'),
        'max_drawdown': max_drawdown(returns),
        'calmar_ratio': calmar_ratio(returns, period='daily'),
        'volatility': annual_volatility(returns, period='daily')
    }
```

## Metric Definitions

### Sharpe Ratio

**Formula**: `(Return - Risk-Free Rate) / Volatility`

**Interpretation**:
- > 1.0: Good risk-adjusted returns
- > 2.0: Very good
- > 3.0: Excellent

```python
sharpe = sharpe_ratio(returns, risk_free=0.02, period='daily')
```

### Maximum Drawdown

**Definition**: Largest peak-to-trough decline

**Interpretation**:
- < 10%: Low risk
- 10-20%: Moderate risk
- > 20%: High risk

```python
max_dd = max_drawdown(returns)  # Returns negative value
```

### Alpha & Beta

**Alpha**: Excess return vs benchmark (after adjusting for risk)  
**Beta**: Sensitivity to benchmark movements

**Interpretation**:
- Beta = 1.0: Moves with market
- Beta > 1.0: More volatile than market
- Beta < 1.0: Less volatile than market

```python
alpha, beta = alpha_beta(returns, benchmark_returns, risk_free=0.02)
```

### Sortino Ratio

**Formula**: `(Return - Target) / Downside Deviation`

**Advantage**: Only penalizes downside volatility

```python
sortino = sortino_ratio(returns, required_return=0.0, period='daily')
```

## Period Specifications

Empyrical supports different return periods:

```python
# Daily returns (252 trading days/year)
sharpe_daily = sharpe_ratio(returns, period='daily')

# Weekly returns (52 weeks/year)
sharpe_weekly = sharpe_ratio(returns, period='weekly')

# Monthly returns (12 months/year)
sharpe_monthly = sharpe_ratio(returns, period='monthly')

# Annual returns
sharpe_annual = sharpe_ratio(returns, period='yearly')
```

## Best Practices

### DO ✅

- Use Empyrical for standard risk/performance metrics
- Work with return series (not prices)
- Specify the period correctly ('daily', 'weekly', etc.)
- Use Pandas Series for time-indexed data
- Apply FinWiz scoring thresholds on top of Empyrical metrics

### DON'T ❌

- Implement custom Sharpe ratio, drawdown calculations
- Pass price series (convert to returns first)
- Ignore the period parameter
- Use Empyrical for technical indicators (use TA-Lib)

## Converting Prices to Returns

```python
import numpy as np
import pandas as pd

# NumPy array
prices = np.array([100, 102, 101, 103, 105])
returns = np.diff(prices) / prices[:-1]

# Pandas Series (preferred)
prices_series = pd.Series([100, 102, 101, 103, 105])
returns_series = prices_series.pct_change().dropna()

# Then use with Empyrical
from empyrical import sharpe_ratio
sharpe = sharpe_ratio(returns_series, period='daily')
```

## Testing

```python
import pytest
import numpy as np
from empyrical import max_drawdown, sharpe_ratio

def test_max_drawdown_calculation():
    """Test max drawdown with known values."""
    # Returns with 40% drawdown
    returns = np.array([.01, .02, .03, -.4, -.06, -.02])
    
    max_dd = max_drawdown(returns)
    
    # Should be negative
    assert max_dd < 0
    
    # Should be around -40%
    assert abs(max_dd + 0.40) < 0.05

def test_sharpe_ratio_calculation():
    """Test Sharpe ratio calculation."""
    returns = np.array([.01, .02, .01, .02, .01])
    
    sharpe = sharpe_ratio(returns, risk_free=0.0, period='daily')
    
    # Should be positive for positive returns
    assert sharpe > 0
```

## Migration Path

### Current State (Custom Implementation)

```python
# Current: Custom volatility calculation
volatility = np.std(returns) * np.sqrt(252)

# Current: Custom max drawdown
cumulative = (1 + returns).cumprod()
running_max = np.maximum.accumulate(cumulative)
drawdown = (cumulative - running_max) / running_max
max_dd = drawdown.min()
```

### Future State (Using Empyrical)

```python
from empyrical import annual_volatility, max_drawdown

# Better: Use Empyrical
volatility = annual_volatility(returns, period='daily')
max_dd = max_drawdown(returns)
```

## Installation

```bash
# Use the maintained fork (already installed)
uv add empyrical-reloaded

# Import in code
from empyrical import sharpe_ratio, max_drawdown, alpha_beta
```

**Important**: Do NOT use the original `empyrical` package - it has Python 3.12 compatibility issues. Always use `empyrical-reloaded`.

## Resources

- **Official Docs**: https://github.com/quantopian/empyrical
- **Maintained Fork**: https://github.com/stefan-jansen/empyrical-reloaded
- **API Reference**: https://empyrical.ml4trading.io/

---

**Version**: 1.0  
**Created**: 2025-11-14  
**Purpose**: Standardize risk/performance metric calculations using Empyrical  
**Status**: Recommended for future implementation
