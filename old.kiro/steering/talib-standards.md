---
title: TA-Lib Standards for FinWiz
inclusion: always
---

# TA-Lib Standards for FinWiz

## Overview

TA-Lib (Technical Analysis Library) is our standard library for calculating technical indicators. We use the Python wrapper (`ta-lib`) which provides fast, battle-tested implementations of 200+ technical indicators.

**Library**: `/ta-lib/ta-lib-python`  
**Documentation**: https://github.com/ta-lib/ta-lib-python  
**Current Version**: 0.6.6+

## Core Principles

1. **Use TA-Lib for ALL technical indicator calculations** - Don't implement custom RSI, MACD, etc.
2. **Wrap TA-Lib calls** - Use our `TALibWrappers` class for consistent error handling
3. **NumPy arrays required** - TA-Lib expects `np.float64` arrays
4. **Handle NaN values** - Early periods return NaN, handle gracefully

## Standard Usage Patterns

### Basic Indicators

```python
import numpy as np
import talib

# Prepare data (TA-Lib requires np.float64)
close_prices = np.array([44.34, 44.09, 44.15, 43.61, 44.33]).astype(np.float64)

# RSI - Relative Strength Index
rsi = talib.RSI(close_prices, timeperiod=14)
print(f"Current RSI: {rsi[-1]:.2f}")

# MACD - Moving Average Convergence Divergence
macd, macd_signal, macd_hist = talib.MACD(
    close_prices, 
    fastperiod=12, 
    slowperiod=26, 
    signalperiod=9
)

# Simple Moving Average
sma_20 = talib.SMA(close_prices, timeperiod=20)

# Exponential Moving Average
ema_12 = talib.EMA(close_prices, timeperiod=12)
```

### Bollinger Bands

```python
# Bollinger Bands with 20-period, 2 standard deviations
upper, middle, lower = talib.BBANDS(
    close_prices, 
    timeperiod=20, 
    nbdevup=2.0, 
    nbdevdn=2.0, 
    matype=0  # Simple Moving Average
)

# Using T3 (Triple Exponential) Moving Average
from talib import MA_Type
upper, middle, lower = talib.BBANDS(close_prices, matype=MA_Type.T3)
```

### Multi-Input Indicators

```python
# Indicators requiring OHLC data
high = np.array([...]).astype(np.float64)
low = np.array([...]).astype(np.float64)
close = np.array([...]).astype(np.float64)

# Average True Range (volatility)
atr = talib.ATR(high, low, close, timeperiod=14)

# Commodity Channel Index
cci = talib.CCI(high, low, close, timeperiod=14)

# Stochastic Oscillator
slowk, slowd = talib.STOCH(
    high, low, close,
    fastk_period=5,
    slowk_period=3,
    slowk_matype=0,
    slowd_period=3,
    slowd_matype=0
)
```

## FinWiz Integration Pattern

### Using TALibWrappers (Recommended)

```python
from finwiz.quantitative.technical.technical_indicators import TALibWrappers

# Use our wrapper for consistent error handling
close_prices = np.array([...])

# Calculate indicators through wrapper
rsi = TALibWrappers.rsi(close_prices, period=14)
macd, signal, hist = TALibWrappers.macd(close_prices)
upper, middle, lower = TALibWrappers.bollinger_bands(close_prices, period=20)
```

### Pandas/Polars Integration

```python
import pandas as pd
import talib

# TA-Lib detects Pandas Series and returns Pandas Series
df = pd.DataFrame({'close': [44.34, 44.09, 44.15, 43.61, 44.33]})

df['sma_20'] = talib.SMA(df['close'], timeperiod=20)
df['rsi'] = talib.RSI(df['close'], timeperiod=14)
df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'])

# Works with Polars too
import polars as pl
df_polars = pl.DataFrame({'close': [...]})
df_polars = df_polars.with_columns([
    talib.SMA(df_polars['close'], timeperiod=20).alias('sma_20'),
    talib.RSI(df_polars['close'], timeperiod=14).alias('rsi')
])
```

## Common Indicators Reference

### Momentum Indicators

| Indicator | Function | Typical Period | Output Range |
|-----------|----------|----------------|--------------|
| RSI | `talib.RSI(close, 14)` | 14 | 0-100 |
| MACD | `talib.MACD(close, 12, 26, 9)` | 12/26/9 | Unbounded |
| Stochastic | `talib.STOCH(high, low, close, 5, 3, 0, 3, 0)` | 5/3/3 | 0-100 |
| CCI | `talib.CCI(high, low, close, 14)` | 14 | Unbounded |

### Trend Indicators

| Indicator | Function | Typical Period |
|-----------|----------|----------------|
| SMA | `talib.SMA(close, 20)` | 20, 50, 200 |
| EMA | `talib.EMA(close, 12)` | 12, 26 |
| DEMA | `talib.DEMA(close, 30)` | 30 |
| TEMA | `talib.TEMA(close, 30)` | 30 |

### Volatility Indicators

| Indicator | Function | Typical Period |
|-----------|----------|----------------|
| ATR | `talib.ATR(high, low, close, 14)` | 14 |
| Bollinger Bands | `talib.BBANDS(close, 20, 2, 2)` | 20 |
| NATR | `talib.NATR(high, low, close, 14)` | 14 |

## Error Handling

### Handle NaN Values

```python
import numpy as np
import talib

close = np.array([44.34, 44.09, 44.15, 43.61, 44.33])

# RSI with 14-period needs 14+ data points
rsi = talib.RSI(close, timeperiod=14)

# Early values will be NaN
if np.isnan(rsi[-1]):
    # Not enough data yet
    print("Insufficient data for RSI calculation")
else:
    print(f"RSI: {rsi[-1]:.2f}")
```

### Type Conversion

```python
# TA-Lib requires np.float64
close = np.array([44.34, 44.09, 44.15]).astype(np.float64)

# Or use our wrapper which handles this
from finwiz.quantitative.technical.technical_indicators import TALibWrappers
rsi = TALibWrappers.rsi(close, period=14)  # Handles type conversion
```

## Best Practices

### DO ✅

- Use TA-Lib for all technical indicator calculations
- Use `TALibWrappers` for consistent error handling
- Convert data to `np.float64` before passing to TA-Lib
- Handle NaN values in early periods
- Use standard periods (RSI=14, MACD=12/26/9, etc.)
- Document any non-standard periods used

### DON'T ❌

- Implement custom RSI, MACD, or other standard indicators
- Pass non-NumPy arrays directly to TA-Lib
- Ignore NaN values in results
- Use TA-Lib for non-technical calculations (use it for indicators only)

## Scoring Integration

### Technical Scoring Pattern

```python
# Calculate indicators using TA-Lib
rsi = talib.RSI(close_prices, timeperiod=14)
macd, macd_signal, _ = talib.MACD(close_prices)

# Apply business logic scoring (custom to FinWiz)
if 40 <= rsi[-1] <= 60:
    rsi_score = 1.0  # Neutral zone (excellent)
elif 30 <= rsi[-1] <= 70:
    rsi_score = 0.8  # Good range
else:
    rsi_score = 0.6  # Acceptable

# TA-Lib calculates indicators, we apply scoring thresholds
```

## Performance Considerations

- TA-Lib is implemented in C, extremely fast
- Vectorized operations on NumPy arrays
- Minimal overhead for large datasets
- Use for batch calculations when possible

## Testing

```python
import pytest
import numpy as np
import talib

def test_rsi_calculation():
    """Test RSI calculation with known values."""
    close = np.array([44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 
                      45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 
                      45.61, 46.28, 46.28]).astype(np.float64)
    
    rsi = talib.RSI(close, timeperiod=14)
    
    # RSI should be between 0 and 100
    assert 0 <= rsi[-1] <= 100
    
    # Early values should be NaN
    assert np.isnan(rsi[0])
```

## Resources

- **Official Docs**: https://github.com/ta-lib/ta-lib-python
- **Function Reference**: https://github.com/ta-lib/ta-lib-python/blob/master/docs/func.md
- **FinWiz Wrappers**: `src/finwiz/quantitative/technical/technical_indicators.py`

---

**Version**: 1.0  
**Created**: 2025-11-14  
**Purpose**: Standardize TA-Lib usage across FinWiz for technical analysis
