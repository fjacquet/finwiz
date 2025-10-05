# Investment Discovery Tools API Reference

## Overview

This document provides comprehensive API reference for all tools used in the A+ Investment Discovery system. These tools are designed to work with CrewAI agents and provide specialized functionality for discovering, analyzing, and scoring investment opportunities.

## Core Discovery Tools

### APlusScoringTool

The primary tool for calculating A+ scores across all asset types.

#### Class Definition

```python
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, Literal

class APlusScoringInput(BaseModel):
    symbol: str = Field(..., description="Investment symbol (e.g., AAPL, SPY, BTC-USD)")
    asset_type: Literal["etf", "stock", "crypto"] = Field(..., description="Type of asset to score")
    fundamental_data: Dict[str, Any] = Field(default_factory=dict, description="Fundamental data for the investment")
    market_context: Dict[str, Any] = Field(default_factory=dict, description="Current market context and conditions")
    custom_criteria: Dict[str, float] = Field(default_factory=dict, description="Custom scoring criteria weights")
```

#### Methods

##### `_run(symbol: str, asset_type: str, fundamental_data: dict, market_context: dict = None, custom_criteria: dict = None) -> dict`

**Description**: Calculate comprehensive A+ score for an investment candidate.

**Parameters**:

- `symbol` (str): Investment symbol (e.g., "AAPL", "SPY", "BTC-USD")
- `asset_type` (str): Asset type - "etf", "stock", or "crypto"
- `fundamental_data` (dict): Asset-specific fundamental metrics
- `market_context` (dict, optional): Current market conditions
- `custom_criteria` (dict, optional): Custom scoring criteria overrides

**Returns**: Dictionary containing:

```python
{
    "symbol": "VTI",
    "asset_type": "etf",
    "is_a_plus_candidate": True,
    "grade": "A+",
    "percentage": 96.5,
    "recommendation": "Excellent ETF pour allocation core",
    "analysis_summary": {
        "composite_score": 0.965,
        "component_scores": {
            "fundamental": 0.98,
            "technical": 0.85,
            "quality": 0.97,
            "risk": 0.88
        },
        "top_strengths": ["Frais très bas", "Excellent tracking"],
        "main_concerns": [],
        "confidence": 0.92
    },
    "a_plus_score": {
        # Detailed APlusScore object
        "scoring_criteria": {...},
        "market_regime": "moderate_volatility",
        "rationale": [...]
    }
}
```

**Example Usage**:

```python
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool

scorer = APlusScoringTool()

# Score an ETF
etf_data = {
    'expense_ratio': 0.03,
    'aum': 300e9,
    'tracking_error': 0.0005,
    'history_years': 20
}

result = scorer._run(
    symbol='VTI',
    asset_type='etf',
    fundamental_data=etf_data,
    market_context={'vix': 18, 'inflation': 2.8}
)

print(f"Grade: {result['grade']}")
print(f"A+ Candidate: {result['is_a_plus_candidate']}")
```

#### ETF-Specific Data Fields

```python
etf_fundamental_data = {
    'expense_ratio': float,      # Total expense ratio (decimal, e.g., 0.03 for 3%)
    'aum': float,               # Assets under management in USD
    'tracking_error': float,    # Tracking error vs benchmark (decimal)
    'history_years': int,       # Years of operating history
    'issuer_reputation': float, # Issuer quality score (0-1, optional)
    'dividend_yield': float,    # Current dividend yield (decimal, optional)
    'holdings_count': int,      # Number of holdings (optional)
    'turnover_rate': float,     # Portfolio turnover rate (optional)
    'bid_ask_spread': float,    # Average bid-ask spread (optional)
    'premium_discount': float   # Premium/discount to NAV (optional)
}
```

#### Stock-Specific Data Fields

```python
stock_fundamental_data = {
    'roe': float,                    # Return on equity (decimal)
    'revenue_growth': float,         # Annual revenue growth rate (decimal)
    'debt_to_equity': float,         # Debt-to-equity ratio
    'market_cap': float,             # Market capitalization in USD
    'fcf_positive': bool,            # Free cash flow positive
    'profit_margin': float,          # Net profit margin (decimal)
    'pe_ratio': float,               # Price-to-earnings ratio (optional)
    'peg_ratio': float,              # Price/earnings to growth ratio (optional)
    'current_ratio': float,          # Current ratio (optional)
    'gross_margin': float,           # Gross profit margin (optional)
    'management_quality': float,     # Management quality score (0-1, optional)
    'competitive_moat': str,         # Moat strength: "wide", "narrow", "none" (optional)
    'sector': str,                   # Business sector (optional)
    'beta': float                    # Beta vs market (optional)
}
```

#### Crypto-Specific Data Fields

```python
crypto_fundamental_data = {
    'market_cap': float,                    # Market capitalization in USD
    'daily_volume': float,                  # Average daily trading volume in USD
    'age_months': int,                      # Project age in months
    'institutional_adoption': bool,         # Institutional adoption present
    'real_utility': bool,                   # Real-world utility beyond speculation
    'developer_activity': float,            # Developer activity score (0-1, optional)
    'network_growth': float,                # Network growth rate (optional)
    'regulatory_clarity': str,              # "clear", "unclear", "hostile" (optional)
    'total_supply': float,                  # Total token supply (optional)
    'circulating_supply': float,            # Circulating token supply (optional)
    'staking_yield': float,                 # Staking yield if applicable (optional)
    'transaction_fees': float,              # Average transaction fees (optional)
    'energy_efficiency': float              # Energy efficiency score (0-1, optional)
}
```

#### Market Context Fields

```python
market_context = {
    'vix_level': float,              # VIX volatility index
    'inflation_rate': float,         # Current inflation rate (decimal)
    'interest_rates': float,         # Current interest rate level
    'yield_curve_slope': float,      # Yield curve slope (10Y - 2Y)
    'dollar_strength_index': float,  # Dollar strength index
    'market_momentum': float,        # Market momentum indicator
    'sector_rotation': str,          # Current sector rotation theme
    'regime': str                    # Market regime: "bull", "bear", "sideways", "volatile"
}
```

### MarketScreeningTool

Tool for screening large universes of investments to identify A+ candidates.

#### Class Definition

```python
from finwiz.tools.market_screening_tool import MarketScreeningTool

class MarketScreeningInput(BaseModel):
    asset_type: Literal["etf", "stock", "crypto"] = Field(..., description="Type of assets to screen")
    screening_criteria: Dict[str, Any] = Field(default_factory=dict, description="Custom screening criteria")
    market_region: str = Field(default="global", description="Market region to screen")
    max_candidates: int = Field(default=50, ge=1, le=500, description="Maximum candidates to return")
    min_a_plus_score: float = Field(default=0.85, ge=0.0, le=1.0, description="Minimum A+ score threshold")
    include_detailed_analysis: bool = Field(default=False, description="Include detailed A+ analysis")
```

#### Methods

##### `_run(asset_type: str, screening_criteria: dict = None, market_region: str = "global", max_candidates: int = 50, min_a_plus_score: float = 0.85, include_detailed_analysis: bool = False) -> dict`

**Description**: Screen market for A+ investment candidates.

**Parameters**:

- `asset_type` (str): Asset type to screen - "etf", "stock", or "crypto"
- `screening_criteria` (dict, optional): Custom screening criteria
- `market_region` (str): Market region - "global", "us", "eu", "asia", etc.
- `max_candidates` (int): Maximum number of candidates to return (1-500)
- `min_a_plus_score` (float): Minimum A+ score threshold (0.0-1.0)
- `include_detailed_analysis` (bool): Whether to include full A+ analysis

**Returns**: Dictionary containing:

```python
{
    "asset_type": "etf",
    "screening_criteria": {...},
    "market_region": "global",
    "total_screened": 3247,
    "candidates_found": 23,
    "execution_time_seconds": 45.2,
    "candidates": [
        {
            "symbol": "VTI",
            "name": "Vanguard Total Stock Market ETF",
            "asset_type": "etf",
            "preliminary_score": 0.96,
            "meets_a_plus_criteria": True,
            "key_metrics": {
                "expense_ratio": 0.03,
                "aum": 300e9,
                "tracking_error": 0.0005
            },
            "screening_rationale": "Excellent cost structure and tracking performance",
            "data_source": "yahoo_finance",
            "screened_at": "2025-09-25T10:30:00Z"
        }
        # ... more candidates
    ],
    "screening_summary": {
        "top_sectors": ["Technology", "Healthcare", "Financials"],
        "average_score": 0.89,
        "score_distribution": {...}
    }
}
```

**Example Usage**:

```python
from finwiz.tools.market_screening_tool import MarketScreeningTool

screener = MarketScreeningTool()

# Screen ETFs with custom criteria
custom_criteria = {
    'max_expense_ratio': 0.10,
    'min_aum_billions': 2.0,
    'ucits_compliant': True
}

result = screener._run(
    asset_type='etf',
    screening_criteria=custom_criteria,
    market_region='eu',
    max_candidates=20,
    min_a_plus_score=0.90
)

print(f"Found {result['candidates_found']} A+ candidates")
for candidate in result['candidates'][:5]:
    print(f"  {candidate['symbol']}: {candidate['preliminary_score']:.3f}")
```

#### Default Screening Criteria

##### ETF Screening Criteria

```python
etf_default_criteria = {
    'max_expense_ratio': 0.15,          # Maximum expense ratio (1.5%)
    'min_aum_billions': 1.0,            # Minimum AUM ($1B)
    'max_tracking_error': 0.002,        # Maximum tracking error (0.2%)
    'min_history_years': 3,             # Minimum operating history
    'ucits_compliant': False,           # UCITS compliance required
    'min_daily_volume': 1e6,            # Minimum daily volume ($1M)
    'exclude_leveraged': True,          # Exclude leveraged ETFs
    'exclude_inverse': True,            # Exclude inverse ETFs
    'min_holdings': 50,                 # Minimum number of holdings
    'max_concentration': 0.25           # Maximum single holding concentration
}
```

##### Stock Screening Criteria

```python
stock_default_criteria = {
    'min_roe': 0.20,                    # Minimum ROE (20%)
    'min_revenue_growth': 0.15,         # Minimum revenue growth (15%)
    'max_debt_to_equity': 0.3,          # Maximum debt-to-equity ratio
    'min_market_cap_billions': 1.0,     # Minimum market cap ($1B)
    'require_positive_fcf': True,       # Require positive free cash flow
    'min_profit_margin': 0.10,          # Minimum profit margin (10%)
    'max_pe_ratio': 30,                 # Maximum P/E ratio
    'min_current_ratio': 1.2,           # Minimum current ratio
    'exclude_penny_stocks': True,       # Exclude stocks under $5
    'min_analyst_coverage': 3,          # Minimum analyst coverage
    'sectors_included': [],             # Specific sectors (empty = all)
    'sectors_excluded': ['Utilities']   # Excluded sectors
}
```

##### Crypto Screening Criteria

```python
crypto_default_criteria = {
    'min_market_cap_billions': 10.0,        # Minimum market cap ($10B)
    'min_daily_volume_millions': 500.0,     # Minimum daily volume ($500M)
    'min_age_months': 36,                   # Minimum age (3 years)
    'require_institutional_adoption': True, # Institutional adoption required
    'require_real_utility': True,          # Real utility required
    'max_volatility_90d': 1.0,             # Maximum 90-day volatility
    'min_developer_activity': 0.7,         # Minimum developer activity score
    'exclude_meme_coins': True,            # Exclude meme coins
    'exclude_privacy_coins': False,        # Exclude privacy coins
    'regulatory_clarity_required': False,   # Regulatory clarity required
    'min_network_growth': 0.1             # Minimum network growth rate
}
```

### BacktestingTool

Tool for validating A+ candidates through historical backtesting.

#### Class Definition

```python
from finwiz.tools.backtesting_tool import BacktestingTool

class BacktestingInput(BaseModel):
    symbol: str = Field(..., description="Symbol to backtest")
    backtest_period_years: int = Field(default=5, ge=1, le=20, description="Backtesting period in years")
    benchmark: str = Field(default="SPY", description="Benchmark for comparison")
    include_regime_analysis: bool = Field(default=True, description="Include market regime analysis")
    risk_free_rate: float = Field(default=0.02, description="Risk-free rate for calculations")
```

#### Methods

##### `_run(symbol: str, backtest_period_years: int = 5, benchmark: str = "SPY", include_regime_analysis: bool = True, risk_free_rate: float = 0.02) -> dict`

**Description**: Backtest investment performance and calculate risk-adjusted metrics.

**Parameters**:

- `symbol` (str): Symbol to backtest
- `backtest_period_years` (int): Backtesting period (1-20 years)
- `benchmark` (str): Benchmark symbol for comparison
- `include_regime_analysis` (bool): Include market regime analysis
- `risk_free_rate` (float): Risk-free rate for Sharpe ratio calculation

**Returns**: Dictionary containing:

```python
{
    "symbol": "VTI",
    "backtest_period": "2019-09-25 to 2024-09-25",
    "benchmark": "SPY",
    "performance_metrics": {
        "total_return": 0.85,           # 85% total return
        "annualized_return": 0.13,      # 13% annualized return
        "volatility": 0.18,             # 18% annualized volatility
        "sharpe_ratio": 0.61,           # Sharpe ratio
        "sortino_ratio": 0.89,          # Sortino ratio
        "max_drawdown": -0.34,          # Maximum drawdown
        "calmar_ratio": 0.38,           # Calmar ratio
        "beta": 0.98,                   # Beta vs benchmark
        "alpha": 0.005,                 # Alpha vs benchmark
        "information_ratio": 0.12,      # Information ratio
        "tracking_error": 0.03          # Tracking error vs benchmark
    },
    "regime_analysis": {
        "bull_market_performance": {
            "periods": 3,
            "avg_return": 0.22,
            "volatility": 0.14,
            "max_drawdown": -0.08
        },
        "bear_market_performance": {
            "periods": 1,
            "avg_return": -0.28,
            "volatility": 0.35,
            "max_drawdown": -0.34
        },
        "sideways_market_performance": {
            "periods": 2,
            "avg_return": 0.06,
            "volatility": 0.12,
            "max_drawdown": -0.15
        }
    },
    "risk_metrics": {
        "var_95": -0.025,               # 95% Value at Risk (daily)
        "cvar_95": -0.038,              # 95% Conditional VaR
        "skewness": -0.15,              # Return skewness
        "kurtosis": 3.2,                # Return kurtosis
        "downside_deviation": 0.12      # Downside deviation
    },
    "validation_result": {
        "passes_a_plus_criteria": True,
        "validation_score": 0.87,
        "key_strengths": ["Consistent performance", "Low volatility"],
        "concerns": ["High correlation with market"]
    }
}
```

**Example Usage**:

```python
from finwiz.tools.backtesting_tool import BacktestingTool

backtester = BacktestingTool()

# Backtest an A+ candidate
result = backtester._run(
    symbol='VTI',
    backtest_period_years=10,
    benchmark='SPY',
    include_regime_analysis=True
)

print(f"Annualized Return: {result['performance_metrics']['annualized_return']:.2%}")
print(f"Sharpe Ratio: {result['performance_metrics']['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {result['performance_metrics']['max_drawdown']:.2%}")
print(f"Passes A+ Criteria: {result['validation_result']['passes_a_plus_criteria']}")
```

## Specialized Analysis Tools

### QuantitativeAnalysisTool

Advanced quantitative analysis for investment candidates.

#### Methods

##### `_run(symbol: str, analysis_type: str = "comprehensive", lookback_period: int = 252) -> dict`

**Description**: Perform quantitative analysis including factor exposure, risk attribution, and performance attribution.

**Parameters**:

- `symbol` (str): Symbol to analyze
- `analysis_type` (str): "comprehensive", "risk_only", "performance_only", "factor_exposure"
- `lookback_period` (int): Analysis period in trading days

**Returns**: Dictionary with quantitative metrics, factor exposures, and risk decomposition.

### RiskAssessmentTool

Comprehensive risk analysis for investment candidates.

#### Methods

##### `_run(symbol: str, portfolio_context: dict = None, risk_budget: float = 0.05) -> dict`

**Description**: Assess investment risk including systematic risk, idiosyncratic risk, and portfolio impact.

**Parameters**:

- `symbol` (str): Symbol to assess
- `portfolio_context` (dict, optional): Current portfolio holdings for context
- `risk_budget` (float): Risk budget allocation for this investment

**Returns**: Dictionary with risk metrics, risk attribution, and portfolio impact analysis.

### OptimizationTool

Portfolio optimization tool for integrating A+ discoveries.

#### Methods

##### `_run(current_portfolio: dict, new_investments: list, constraints: dict = None) -> dict`

**Description**: Optimize portfolio allocation incorporating A+ discoveries.

**Parameters**:

- `current_portfolio` (dict): Current portfolio holdings and allocations
- `new_investments` (list): List of A+ investment candidates
- `constraints` (dict, optional): Portfolio constraints (max allocation, sector limits, etc.)

**Returns**: Dictionary with optimized allocations, expected improvements, and implementation plan.

## Tool Integration Patterns

### Sequential Tool Usage

```python
# Typical discovery workflow
from finwiz.tools.market_screening_tool import MarketScreeningTool
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool
from finwiz.tools.backtesting_tool import BacktestingTool

# 1. Screen for candidates
screener = MarketScreeningTool()
candidates = screener._run(asset_type='etf', max_candidates=20)

# 2. Score top candidates
scorer = APlusScoringTool()
scored_candidates = []

for candidate in candidates['candidates'][:10]:
    score_result = scorer._run(
        symbol=candidate['symbol'],
        asset_type=candidate['asset_type'],
        fundamental_data=candidate['key_metrics']
    )
    if score_result['is_a_plus_candidate']:
        scored_candidates.append(score_result)

# 3. Validate with backtesting
backtester = BacktestingTool()
validated_candidates = []

for candidate in scored_candidates:
    backtest_result = backtester._run(
        symbol=candidate['symbol'],
        backtest_period_years=5
    )
    if backtest_result['validation_result']['passes_a_plus_criteria']:
        candidate['backtest_validation'] = backtest_result
        validated_candidates.append(candidate)

print(f"Final A+ candidates: {len(validated_candidates)}")
```

### Parallel Tool Usage

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def parallel_discovery_analysis(symbols: list):
    """Analyze multiple symbols in parallel."""
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Create tools
        scorer = APlusScoringTool()
        backtester = BacktestingTool()
        
        # Prepare tasks
        scoring_tasks = []
        backtesting_tasks = []
        
        for symbol in symbols:
            # Add scoring task
            scoring_task = executor.submit(
                scorer._run, symbol, 'etf', {}
            )
            scoring_tasks.append((symbol, scoring_task))
            
            # Add backtesting task
            backtesting_task = executor.submit(
                backtester._run, symbol, 5
            )
            backtesting_tasks.append((symbol, backtesting_task))
        
        # Collect results
        results = {}
        
        for symbol, task in scoring_tasks:
            results[symbol] = {'scoring': task.result()}
        
        for symbol, task in backtesting_tasks:
            results[symbol]['backtesting'] = task.result()
        
        return results

# Usage
symbols = ['VTI', 'VXUS', 'BND', 'VNQ']
results = asyncio.run(parallel_discovery_analysis(symbols))
```

## Error Handling

### Common Exceptions

```python
from finwiz.tools.exceptions import (
    DiscoveryToolError,
    InsufficientDataError,
    InvalidAssetTypeError,
    MarketDataError,
    ScoringError,
    BacktestingError
)

# Error handling example
try:
    result = scorer._run(
        symbol='INVALID',
        asset_type='etf',
        fundamental_data={}
    )
except InsufficientDataError as e:
    print(f"Insufficient data: {e}")
    # Handle with default values or skip
except InvalidAssetTypeError as e:
    print(f"Invalid asset type: {e}")
    # Handle with supported asset type
except MarketDataError as e:
    print(f"Market data unavailable: {e}")
    # Handle with cached data or alternative source
except ScoringError as e:
    print(f"Scoring calculation failed: {e}")
    # Handle with simplified scoring or skip
```

### Graceful Degradation

```python
from finwiz.utils.graceful_degradation import GracefulDegradation

def robust_scoring(symbol: str, asset_type: str, data: dict):
    """Robust scoring with graceful degradation."""
    
    degradation = GracefulDegradation()
    scorer = APlusScoringTool()
    
    try:
        # Attempt full scoring
        return scorer._run(symbol, asset_type, data)
        
    except InsufficientDataError:
        if degradation.allow_partial_scoring():
            # Use partial data with reduced confidence
            partial_data = degradation.get_minimal_data(data, asset_type)
            result = scorer._run(symbol, asset_type, partial_data)
            result['confidence_level'] *= 0.7  # Reduce confidence
            result['warnings'] = ['Partial data used']
            return result
        else:
            raise
            
    except MarketDataError:
        if degradation.use_cached_data():
            # Use cached market data
            cached_data = degradation.get_cached_data(symbol)
            return scorer._run(symbol, asset_type, cached_data)
        else:
            raise
```

## Performance Optimization

### Caching

```python
from functools import lru_cache
from finwiz.utils.cache_manager import cache_with_ttl

class OptimizedAPlusScoringTool(APlusScoringTool):
    
    @cache_with_ttl(hours=1)
    def get_market_regime(self):
        """Cache market regime for 1 hour."""
        return super().get_market_regime()
    
    @lru_cache(maxsize=1000)
    def calculate_component_score(self, asset_type: str, component: str, data_hash: str):
        """Cache component scores."""
        return super().calculate_component_score(asset_type, component, data_hash)
```

### Batch Processing

```python
class BatchScoringTool:
    """Batch processing for multiple investments."""
    
    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
        self.scorer = APlusScoringTool()
    
    def score_batch(self, candidates: list) -> list:
        """Score multiple candidates efficiently."""
        
        results = []
        
        # Process in batches
        for i in range(0, len(candidates), self.batch_size):
            batch = candidates[i:i + self.batch_size]
            
            # Pre-fetch market context once per batch
            market_context = self.scorer.get_market_context()
            
            # Score batch
            batch_results = []
            for candidate in batch:
                try:
                    result = self.scorer._run(
                        symbol=candidate['symbol'],
                        asset_type=candidate['asset_type'],
                        fundamental_data=candidate['data'],
                        market_context=market_context
                    )
                    batch_results.append(result)
                except Exception as e:
                    print(f"Scoring failed for {candidate['symbol']}: {e}")
            
            results.extend(batch_results)
        
        return results
```

---

This API reference provides comprehensive documentation for all investment discovery tools. For usage examples and integration patterns, see the [Developer Guide](investment_discovery_developer_guide.md) and [User Guide](investment_discovery_user_guide.md).
