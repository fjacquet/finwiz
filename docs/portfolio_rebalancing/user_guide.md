# Portfolio Rebalancing User Guide

## Overview

The FinWiz Portfolio Rebalancing system provides intelligent buy/sell quantity recommendations to help maintain optimal portfolio allocations. This guide covers how to use the system effectively, best practices, and common scenarios.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Configuration Options](#configuration-options)
4. [Rebalancing Methods](#rebalancing-methods)
5. [Understanding Reports](#understanding-reports)
6. [Best Practices](#best-practices)
7. [Common Scenarios](#common-scenarios)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.10 or higher
- FinWiz installed and configured
- Valid API keys for price data providers

### Basic Setup

```python
from finwiz.orchestrators.portfolio_rebalancing import PortfolioRebalancingOrchestrator
from finwiz.schemas.portfolio_rebalancing import PortfolioConfiguration, Holding

# Create your portfolio configuration
config = PortfolioConfiguration(
    holdings=[
        Holding(symbol="AAPL", shares=100.0),
        Holding(symbol="GOOGL", shares=10.0),
        Holding(symbol="MSFT", shares=50.0),
    ],
    target_weights={
        "AAPL": 0.4,   # 40%
        "GOOGL": 0.35, # 35%
        "MSFT": 0.25,  # 25%
    }
)

# Initialize the orchestrator
orchestrator = PortfolioRebalancingOrchestrator()

# Run rebalancing analysis
result = await orchestrator.rebalance_portfolio(config)
```

## Basic Usage

### Creating a Portfolio Configuration

The `PortfolioConfiguration` is the main input to the rebalancing system:

```python
from finwiz.schemas.portfolio_rebalancing import (
    PortfolioConfiguration, 
    Holding, 
    RebalancingMethod
)

config = PortfolioConfiguration(
    # Current holdings
    holdings=[
        Holding(symbol="AAPL", shares=150.0, cost_basis=120.0),
        Holding(symbol="GOOGL", shares=25.0, cost_basis=2200.0),
        Holding(symbol="MSFT", shares=100.0, cost_basis=280.0),
    ],
    
    # Target allocation percentages (must sum to ≤ 100%)
    target_weights={
        "AAPL": 0.33,  # 33%
        "GOOGL": 0.33, # 33%
        "MSFT": 0.34,  # 34%
    },
    
    # Optional: Position-specific tolerance bands
    tolerance_bands={
        "AAPL": 0.03,  # ±3%
        "GOOGL": 0.05, # ±5%
        "MSFT": 0.03,  # ±3%
    },
    
    # Global settings
    global_tolerance=0.05,           # Default ±5% tolerance
    available_capital=5000.0,        # Additional capital available
    transaction_cost_rate=0.001,     # 0.1% transaction cost
    min_trade_size=100.0,           # Minimum trade size
    rebalancing_method=RebalancingMethod.MINIMIZE_TRADES
)
```

### Running Rebalancing Analysis

```python
# Basic rebalancing
result = await orchestrator.rebalance_portfolio(config)

# With portfolio ID for tracking
result = await orchestrator.rebalance_portfolio(
    config, 
    portfolio_id="my-retirement-portfolio"
)

# Generate HTML report
html_report = await orchestrator.generate_rebalancing_report(result)

# Generate French report
html_report_fr = await orchestrator.generate_rebalancing_report(
    result, 
    language="fr"
)
```

## Configuration Options

### Holdings Configuration

```python
# Basic holding
Holding(symbol="AAPL", shares=100.0)

# With cost basis for tax analysis
Holding(
    symbol="AAPL", 
    shares=100.0, 
    cost_basis=150.0,
    acquisition_date=datetime(2023, 1, 15)
)

# Fractional shares supported
Holding(symbol="GOOGL", shares=12.5)
```

### Target Weights

```python
# Equal weighting
target_weights = {
    "AAPL": 0.25,
    "GOOGL": 0.25,
    "MSFT": 0.25,
    "TSLA": 0.25,
}

# Market cap weighting (example)
target_weights = {
    "AAPL": 0.30,
    "GOOGL": 0.25,
    "MSFT": 0.25,
    "TSLA": 0.20,
}

# Conservative allocation
target_weights = {
    "VTI": 0.60,   # Total stock market
    "BND": 0.30,   # Total bond market
    "VXUS": 0.10,  # International stocks
}
```

### Tolerance Bands

```python
# Global tolerance for all positions
config = PortfolioConfiguration(
    holdings=holdings,
    target_weights=target_weights,
    global_tolerance=0.05  # ±5% for all positions
)

# Position-specific tolerances
config = PortfolioConfiguration(
    holdings=holdings,
    target_weights=target_weights,
    tolerance_bands={
        "AAPL": 0.03,   # ±3% (tighter control)
        "TSLA": 0.10,   # ±10% (looser for volatile stock)
        "VTI": 0.02,    # ±2% (very tight for core holding)
    },
    global_tolerance=0.05  # Default for positions not specified
)
```

## Rebalancing Methods

### MINIMIZE_TRADES (Default)

Prioritizes reducing the number of transactions:

```python
config.rebalancing_method = RebalancingMethod.MINIMIZE_TRADES
```

**Best for:**

- Accounts with high transaction costs
- Taxable accounts (fewer taxable events)
- Portfolios where simplicity is preferred

### MINIMIZE_COSTS

Optimizes for lowest total transaction costs:

```python
config.rebalancing_method = RebalancingMethod.MINIMIZE_COSTS
```

**Best for:**

- Large portfolios where cost efficiency matters
- Frequent rebalancing strategies
- Professional portfolio management

### RISK_AWARE

Considers risk metrics and concentration limits:

```python
config.rebalancing_method = RebalancingMethod.RISK_AWARE
```

**Best for:**

- Risk-conscious investors
- Portfolios with concentration concerns
- Institutional requirements

## Understanding Reports

### Rebalancing Result Structure

```python
result = await orchestrator.rebalance_portfolio(config)

# Current portfolio analysis
print(f"Total Value: ${result.current_portfolio.total_value:,.2f}")
print(f"Current Weights: {result.current_portfolio.weightings}")
print(f"Deviations: {result.current_portfolio.deviations_from_target}")

# Trade recommendations
for trade in result.trade_recommendations:
    print(f"{trade.action} {trade.quantity} shares of {trade.symbol}")
    print(f"  Current weight: {trade.current_weight:.1%}")
    print(f"  Target weight: {trade.target_weight:.1%}")
    print(f"  Estimated cost: ${trade.total_estimated_cost:.2f}")

# Overall recommendation
print(f"Recommendation: {result.overall_recommendation}")

# Cost analysis
print(f"Total transaction costs: ${result.cost_analysis.total_transaction_costs:.2f}")
print(f"Cost as % of portfolio: {result.cost_analysis.cost_as_percentage:.2f}%")
```

### HTML Report Sections

The generated HTML report includes:

1. **Executive Summary** - Overall recommendation and key metrics
2. **Current Portfolio Analysis** - Holdings, weights, and deviations
3. **Trade Recommendations** - Specific buy/sell instructions
4. **Cost Analysis** - Transaction costs and cost-benefit analysis
5. **Risk Analysis** - Portfolio risk metrics and improvements
6. **Alternative Scenarios** - What-if analysis with different parameters

## Best Practices

### 1. Setting Appropriate Tolerances

```python
# Conservative approach (frequent small adjustments)
tolerance_bands = {symbol: 0.02 for symbol in target_weights}  # ±2%

# Balanced approach (moderate adjustments)
tolerance_bands = {symbol: 0.05 for symbol in target_weights}  # ±5%

# Relaxed approach (infrequent large adjustments)
tolerance_bands = {symbol: 0.10 for symbol in target_weights}  # ±10%

# Volatility-based tolerances
tolerance_bands = {
    "AAPL": 0.03,   # Stable large cap
    "TSLA": 0.08,   # Volatile growth stock
    "BND": 0.02,    # Stable bond fund
}
```

### 2. Managing Transaction Costs

```python
# For high-cost brokers
config.transaction_cost_rate = 0.01  # 1%
config.min_trade_size = 1000.0       # Avoid small trades

# For low-cost brokers
config.transaction_cost_rate = 0.0005  # 0.05%
config.min_trade_size = 50.0           # Allow smaller trades

# Commission-free trading
config.transaction_cost_rate = 0.0
config.min_trade_size = 1.0
```

### 3. Tax-Efficient Rebalancing

```python
# Include cost basis for tax analysis
holdings = [
    Holding(
        symbol="AAPL", 
        shares=100.0, 
        cost_basis=120.0,  # For capital gains calculation
        acquisition_date=datetime(2023, 1, 15)
    )
]

# Use tax-aware method (when available)
config.rebalancing_method = RebalancingMethod.TAX_EFFICIENT
```

### 4. Regular Rebalancing Schedule

```python
# Monthly rebalancing
async def monthly_rebalancing():
    result = await orchestrator.rebalance_portfolio(config)
    
    if result.overall_recommendation in [
        RebalancingRecommendation.REBALANCE_NOW,
        RebalancingRecommendation.REBALANCE_SOON
    ]:
        # Execute trades or alert user
        return result.trade_recommendations
    
    return None

# Threshold-based rebalancing
async def threshold_rebalancing():
    result = await orchestrator.rebalance_portfolio(config)
    
    # Only rebalance if any position deviates by more than 5%
    max_deviation = max(
        abs(dev) for dev in result.current_portfolio.deviations_from_target.values()
    )
    
    if max_deviation > 0.05:
        return result.trade_recommendations
    
    return None
```

## Common Scenarios

### Scenario 1: Three-Fund Portfolio

```python
# Simple three-fund portfolio
config = PortfolioConfiguration(
    holdings=[
        Holding(symbol="VTI", shares=600.0),   # US Total Market
        Holding(symbol="VXUS", shares=200.0),  # International
        Holding(symbol="BND", shares=400.0),   # Bonds
    ],
    target_weights={
        "VTI": 0.60,   # 60% US stocks
        "VXUS": 0.20,  # 20% international
        "BND": 0.20,   # 20% bonds
    },
    global_tolerance=0.05,
    rebalancing_method=RebalancingMethod.MINIMIZE_TRADES
)
```

### Scenario 2: Growth Portfolio with Individual Stocks

```python
config = PortfolioConfiguration(
    holdings=[
        Holding(symbol="AAPL", shares=50.0),
        Holding(symbol="GOOGL", shares=15.0),
        Holding(symbol="MSFT", shares=40.0),
        Holding(symbol="TSLA", shares=25.0),
        Holding(symbol="NVDA", shares=30.0),
    ],
    target_weights={
        "AAPL": 0.25,
        "GOOGL": 0.20,
        "MSFT": 0.25,
        "TSLA": 0.15,
        "NVDA": 0.15,
    },
    tolerance_bands={
        "AAPL": 0.03,   # Tighter tolerance for large positions
        "GOOGL": 0.03,
        "MSFT": 0.03,
        "TSLA": 0.08,   # Looser for volatile stocks
        "NVDA": 0.06,
    },
    available_capital=5000.0,
    rebalancing_method=RebalancingMethod.RISK_AWARE
)
```

### Scenario 3: Adding New Capital

```python
# Monthly contribution scenario
config = PortfolioConfiguration(
    holdings=current_holdings,
    target_weights=target_weights,
    available_capital=2000.0,  # Monthly contribution
    rebalancing_method=RebalancingMethod.MINIMIZE_COSTS
)

result = await orchestrator.rebalance_portfolio(config)

# Use new capital to rebalance toward targets
for trade in result.trade_recommendations:
    if trade.action == TradeAction.BUY:
        print(f"Invest ${trade.trade_value:.2f} in {trade.symbol}")
```

### Scenario 4: Retirement Withdrawal

```python
# Need to withdraw $5,000
config = PortfolioConfiguration(
    holdings=current_holdings,
    target_weights=target_weights,
    available_capital=-5000.0,  # Negative for withdrawal
    rebalancing_method=RebalancingMethod.TAX_EFFICIENT
)

result = await orchestrator.rebalance_portfolio(config)

# Sell positions to raise cash while maintaining allocation
for trade in result.trade_recommendations:
    if trade.action == TradeAction.SELL:
        print(f"Sell ${trade.trade_value:.2f} of {trade.symbol}")
```

## Troubleshooting

### Common Issues

#### 1. "Insufficient Price Data" Error

```python
# Ensure all symbols are valid
holdings = [
    Holding(symbol="AAPL", shares=100.0),  # Valid
    # Holding(symbol="INVALID", shares=50.0),  # Remove invalid symbols
]

# Check API key configuration
# Verify network connectivity
```

#### 2. "Target Weights Sum Exceeds 100%" Error

```python
# Ensure target weights sum to ≤ 1.0
target_weights = {
    "AAPL": 0.40,
    "GOOGL": 0.35,
    "MSFT": 0.25,  # Total = 1.00 ✓
}

# Not this:
# target_weights = {
#     "AAPL": 0.50,
#     "GOOGL": 0.40,
#     "MSFT": 0.30,  # Total = 1.20 ✗
# }
```

#### 3. No Trade Recommendations Generated

```python
# Check if portfolio is already balanced
result = await orchestrator.rebalance_portfolio(config)

if len(result.trade_recommendations) == 0:
    print("Portfolio is already within tolerance bands")
    print("Current deviations:", result.current_portfolio.deviations_from_target)
    
    # Consider tightening tolerances if needed
    config.global_tolerance = 0.02  # Tighter tolerance
```

#### 4. High Transaction Costs Warning

```python
# Reduce transaction costs by:
# 1. Increasing tolerance bands
config.global_tolerance = 0.08  # Wider tolerance

# 2. Increasing minimum trade size
config.min_trade_size = 500.0

# 3. Using new capital for rebalancing
config.available_capital = 1000.0

# 4. Choosing cost-optimized method
config.rebalancing_method = RebalancingMethod.MINIMIZE_COSTS
```

### Performance Optimization

#### For Large Portfolios (50+ positions)

```python
# Use appropriate rebalancing method
config.rebalancing_method = RebalancingMethod.MINIMIZE_TRADES

# Set reasonable tolerances
config.global_tolerance = 0.05  # Not too tight

# Consider position limits
# Limit to top 20-30 positions for active management
```

#### For Frequent Rebalancing

```python
# Cache orchestrator instance
orchestrator = PortfolioRebalancingOrchestrator()

# Reuse for multiple analyses
result1 = await orchestrator.rebalance_portfolio(config1)
result2 = await orchestrator.rebalance_portfolio(config2)

# Clean up when done
await orchestrator.close()
```

### Getting Help

1. **Check Logs**: Enable debug logging to see detailed execution information
2. **Validate Input**: Ensure all symbols are valid and holdings are positive
3. **Test with Simple Portfolio**: Start with 2-3 positions to verify setup
4. **Review Documentation**: Check API documentation for advanced features

## Advanced Features

### Custom Constraints

```python
from finwiz.quantitative.rebalancing_engine import OptimizationConstraint

# Maximum position size constraint
max_position_constraint = OptimizationConstraint(
    name="max_position",
    constraint_type="max_position",
    value=0.25,  # No position > 25%
    description="Maximum 25% in any single position"
)

# Custom constraints can be added to optimization
```

### Scenario Analysis

```python
# Compare different rebalancing approaches
methods = [
    RebalancingMethod.MINIMIZE_TRADES,
    RebalancingMethod.MINIMIZE_COSTS,
    RebalancingMethod.RISK_AWARE
]

results = {}
for method in methods:
    config.rebalancing_method = method
    results[method] = await orchestrator.rebalance_portfolio(config)

# Compare results
for method, result in results.items():
    print(f"{method}: {len(result.trade_recommendations)} trades, "
          f"${result.cost_analysis.total_transaction_costs:.2f} cost")
```

This user guide provides comprehensive coverage of the portfolio rebalancing system, from basic usage to advanced scenarios. Users can reference specific sections based on their needs and experience level.
