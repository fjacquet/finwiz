---
title: Financial Libraries Strategy for FinWiz
inclusion: always
---

# Financial Libraries Strategy for FinWiz

## Overview

This document clarifies when to use standard libraries vs custom code for financial calculations in FinWiz.

## Library Usage Matrix

| Calculation Type | Library | Custom Code | Rationale |
|------------------|---------|-------------|-----------|
| **Technical Indicators** | ✅ TA-Lib | ❌ | Battle-tested, C-optimized, 200+ indicators |
| **Risk Metrics** | ✅ Empyrical-Reloaded | ❌ | Standard financial metrics (Sharpe, drawdown, etc.) |
| **Scoring Thresholds** | ❌ | ✅ | FinWiz-specific business logic |
| **Grading System** | ❌ | ✅ | Custom A+/A/B/C/D/F scale |
| **Fundamental Analysis** | ❌ | ✅ | Custom ROE/debt/growth thresholds |
| **Backtesting** | ✅ Backtrader | ❌ | Industry-standard backtesting framework |

## The Separation of Concerns

### What Libraries Do (Calculation)

```python
import talib
import empyrical

# TA-Lib calculates RSI (standard algorithm)
rsi = talib.RSI(close_prices, timeperiod=14)

# Empyrical calculates Sharpe ratio (standard formula)
sharpe = empyrical.sharpe_ratio(returns, risk_free=0.02)

# Empyrical calculates max drawdown (standard definition)
max_dd = empyrical.max_drawdown(returns)
```

### What Custom Code Does (Business Logic)

```python
# FinWiz applies custom scoring thresholds
if 40 <= rsi <= 60:
    rsi_score = 1.0  # YOUR business rule
elif 30 <= rsi <= 70:
    rsi_score = 0.8  # YOUR business rule
else:
    rsi_score = 0.6

# FinWiz applies custom risk scoring
if sharpe >= 2.0:
    sharpe_score = 1.0  # YOUR threshold
elif sharpe >= 1.0:
    sharpe_score = 0.8
else:
    sharpe_score = 0.6

# FinWiz assigns custom grades
if composite_score >= 0.90:
    grade = "A+"  # YOUR grading scale
elif composite_score >= 0.80:
    grade = "A"
```

## Why This Approach?

### ✅ Use Libraries For:

1. **Standard Calculations**
   - RSI, MACD, Bollinger Bands (TA-Lib)
   - Sharpe ratio, max drawdown, volatility (Empyrical)
   - These have universally accepted formulas

2. **Performance**
   - TA-Lib is C-optimized (100x faster than Python)
   - Empyrical is battle-tested by Quantopian

3. **Correctness**
   - Thousands of users have validated these implementations
   - Edge cases are handled properly

4. **Maintenance**
   - No need to maintain calculation code
   - Automatic bug fixes and improvements

### ✅ Use Custom Code For:

1. **Business Logic**
   - "RSI between 40-60 = score 1.0" is YOUR strategy
   - "ROE > 20% = excellent" is YOUR threshold
   - "Composite score > 0.90 = A+" is YOUR grading

2. **Competitive Advantage**
   - Your scoring methodology is unique
   - Your thresholds are based on your research
   - Your grading scale differentiates you

3. **Flexibility**
   - Easy to adjust thresholds based on market conditions
   - Can A/B test different scoring approaches
   - Can customize per asset class

## Current Implementation

### Phase 2A Refactoring (In Progress)

We're refactoring the **scoring logic** (custom business rules), NOT the **calculation logic** (which should use libraries).

```python
# BEFORE: Monolithic DeepAnalysisScorer (1,301 lines)
class DeepAnalysisScorer:
    def calculate_fundamental_score(self, ...):
        # 300 lines of stock/ETF/crypto scoring logic
    
    def calculate_technical_score(self, ...):
        # 200 lines of RSI/MACD/trend scoring logic
    
    def calculate_risk_score(self, ...):
        # 200 lines of volatility/drawdown/beta scoring logic

# AFTER: Focused component scorers (945 lines total)
class FundamentalScorer:
    # 344 lines - focused on fundamental scoring thresholds

class TechnicalScorer:
    # 138 lines - focused on technical scoring thresholds

class RiskScorer:
    # 125 lines - focused on risk scoring thresholds

class DeepAnalysisScorer:
    # 945 lines - orchestrates component scorers
```

### What We're NOT Changing

- ✅ We already use TA-Lib for technical indicators
- ✅ We already use Backtrader for backtesting
- ✅ We now have Empyrical-Reloaded for risk metrics

### What We're Refactoring

- ✅ Organizing custom scoring thresholds into focused classes
- ✅ Separating stock/ETF/crypto scoring logic
- ✅ Making business rules easier to maintain and test

## Future Enhancements

### Consider Using Empyrical For:

Currently, we have custom implementations for:
- Volatility calculation
- Maximum drawdown calculation
- Beta calculation

**Recommendation**: Migrate to Empyrical-Reloaded for these calculations, but keep our custom scoring thresholds.

```python
# CURRENT (custom calculation)
volatility = np.std(returns) * np.sqrt(252)

# FUTURE (use Empyrical for calculation)
from empyrical import annual_volatility
volatility = annual_volatility(returns, period='daily')

# KEEP (custom scoring threshold)
if volatility <= 0.10:
    vol_score = 1.0  # FinWiz business logic
elif volatility <= 0.15:
    vol_score = 0.8
```

## Decision Framework

When implementing new financial calculations, ask:

### 1. Is this a standard calculation?

**YES** → Use a library (TA-Lib, Empyrical, Backtrader)  
**NO** → Implement custom code

### 2. Is this a business rule/threshold?

**YES** → Custom code (this is your competitive advantage)  
**NO** → Check if a library exists

### 3. Does a library exist for this?

**YES** → Use the library  
**NO** → Implement custom code with proper documentation

## Examples

### ✅ CORRECT: Use Library + Custom Scoring

```python
import talib
from empyrical import sharpe_ratio

# Library calculates the metric
rsi = talib.RSI(close_prices, timeperiod=14)
sharpe = sharpe_ratio(returns, risk_free=0.02)

# Custom code applies business logic
if 40 <= rsi <= 60 and sharpe >= 1.5:
    recommendation = "BUY"  # FinWiz logic
elif rsi > 70 or sharpe < 0.5:
    recommendation = "SELL"  # FinWiz logic
else:
    recommendation = "HOLD"  # FinWiz logic
```

### ❌ WRONG: Reimplement Standard Calculations

```python
# DON'T DO THIS - TA-Lib already has RSI
def calculate_rsi(prices, period=14):
    gains = []
    losses = []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
        else:
            losses.append(abs(change))
    # ... complex RSI calculation ...
```

## Summary

**Libraries** = Standard calculations (RSI, Sharpe, drawdown)  
**Custom Code** = Business logic (scoring thresholds, grading scale)

**Phase 2A** = Refactoring custom business logic, NOT replacing standard calculations

**Future** = Consider migrating risk metric calculations to Empyrical-Reloaded

---

**Version**: 1.0  
**Created**: 2025-11-14  
**Purpose**: Clarify library vs custom code strategy for FinWiz
