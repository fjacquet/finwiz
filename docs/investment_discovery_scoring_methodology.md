# A+ Investment Scoring Methodology

## Overview

The A+ Investment Scoring system is the core engine that identifies exceptional investment opportunities across ETFs, stocks, and cryptocurrencies. This document provides a comprehensive technical overview of the scoring methodology, criteria, and implementation details.

## Scoring Framework

### Core Principles

1. **Multi-Dimensional Analysis**: Each investment is evaluated across four key dimensions
2. **Dynamic Adaptation**: Criteria adjust based on market conditions and regimes
3. **Asset-Specific Optimization**: Different scoring models for ETFs, stocks, and crypto
4. **Risk-Adjusted Quality**: Emphasis on sustainable, high-quality investments
5. **Quantitative Rigor**: Data-driven approach with statistical validation

### Scoring Components

#### 1. Fundamental Score (Weight: 35%)

**Purpose**: Evaluates the core financial health and attractiveness of the investment.

**ETF Fundamental Scoring**:
```python
def calculate_etf_fundamental_score(data: dict) -> float:
    """
    ETF fundamental scoring based on cost efficiency and structure quality.
    
    Key Metrics:
    - Expense Ratio: Lower is better (target ≤ 0.15%)
    - Assets Under Management: Higher is better (target ≥ $1B)
    - Tracking Error: Lower is better (target ≤ 0.20%)
    - Operating History: Longer is better (target ≥ 3 years)
    """
    expense_score = max(0, 1 - (data['expense_ratio'] / 0.15))
    aum_score = min(1, data['aum'] / 1e9)
    tracking_score = max(0, 1 - (data['tracking_error'] / 0.002))
    history_score = min(1, data['history_years'] / 5)
    
    return (expense_score * 0.4 + aum_score * 0.3 + 
            tracking_score * 0.2 + history_score * 0.1)
```

**Stock Fundamental Scoring**:
```python
def calculate_stock_fundamental_score(data: dict) -> float:
    """
    Stock fundamental scoring based on profitability and growth.
    
    Key Metrics:
    - Return on Equity: Higher is better (target ≥ 20%)
    - Revenue Growth: Higher is better (target ≥ 15%)
    - Debt-to-Equity: Lower is better (target ≤ 0.3)
    - Free Cash Flow: Positive and growing
    - Profit Margins: Higher is better (target ≥ 10%)
    """
    roe_score = min(1, data['roe'] / 0.20)
    growth_score = min(1, data['revenue_growth'] / 0.15)
    debt_score = max(0, 1 - (data['debt_to_equity'] / 0.3))
    fcf_score = 1.0 if data['fcf_positive'] else 0.0
    margin_score = min(1, data['profit_margin'] / 0.10)
    
    return (roe_score * 0.3 + growth_score * 0.25 + debt_score * 0.2 + 
            fcf_score * 0.15 + margin_score * 0.1)
```

**Crypto Fundamental Scoring**:
```python
def calculate_crypto_fundamental_score(data: dict) -> float:
    """
    Crypto fundamental scoring based on adoption and utility.
    
    Key Metrics:
    - Market Capitalization: Higher is better (target ≥ $10B)
    - Daily Volume: Higher is better (target ≥ $500M)
    - Age/Maturity: Older is better (target ≥ 36 months)
    - Institutional Adoption: Binary factor
    - Real Utility: Binary factor
    """
    mcap_score = min(1, data['market_cap'] / 10e9)
    volume_score = min(1, data['daily_volume'] / 500e6)
    age_score = min(1, data['age_months'] / 36)
    adoption_score = 1.0 if data['institutional_adoption'] else 0.0
    utility_score = 1.0 if data['real_utility'] else 0.0
    
    return (mcap_score * 0.3 + volume_score * 0.2 + age_score * 0.2 + 
            adoption_score * 0.15 + utility_score * 0.15)
```

#### 2. Technical Score (Weight: 20%)

**Purpose**: Evaluates momentum, trend strength, and technical indicators.

**Common Technical Indicators**:
- **Momentum**: 12-month price momentum vs benchmark
- **Volatility**: Risk-adjusted returns (Sharpe ratio)
- **Trend Strength**: Moving average convergence/divergence
- **Support/Resistance**: Technical levels and breakouts

```python
def calculate_technical_score(price_data: dict) -> float:
    """
    Technical scoring based on momentum and trend analysis.
    """
    momentum_score = calculate_momentum_score(price_data)
    volatility_score = calculate_volatility_score(price_data)
    trend_score = calculate_trend_strength(price_data)
    
    return (momentum_score * 0.4 + volatility_score * 0.3 + trend_score * 0.3)
```

#### 3. Quality Score (Weight: 30%)

**Purpose**: Evaluates management quality, governance, and structural advantages.

**ETF Quality Factors**:
- Issuer reputation and track record
- Index methodology quality
- Securities lending practices
- Liquidity and bid-ask spreads

**Stock Quality Factors**:
- Management quality and track record
- Competitive moat strength
- ESG factors and sustainability
- Corporate governance ratings

**Crypto Quality Factors**:
- Development team activity and transparency
- Community engagement and adoption
- Protocol security and audit history
- Regulatory compliance status

#### 4. Risk Score (Weight: 15%)

**Purpose**: Evaluates downside risk and risk-adjusted returns.

**Risk Metrics**:
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Value at Risk (VaR)**: Potential loss at 95% confidence
- **Beta**: Systematic risk vs market
- **Correlation**: Diversification benefits

```python
def calculate_risk_score(returns_data: dict, market_context: dict) -> float:
    """
    Risk scoring with market regime adjustments.
    """
    base_risk_score = calculate_base_risk_metrics(returns_data)
    
    # Adjust for market regime
    if market_context.get('regime') == 'high_volatility':
        # Penalize high-risk investments more in volatile markets
        base_risk_score *= 0.8
    elif market_context.get('regime') == 'bear_market':
        # Emphasize defensive characteristics
        base_risk_score *= 0.9
        
    return base_risk_score
```

## Market Regime Adaptation

### Regime Detection

The system automatically detects market regimes using multiple indicators:

```python
class MarketRegimeDetector:
    def detect_current_regime(self) -> MarketRegime:
        """Detect current market regime based on multiple indicators."""
        vix = self.get_vix_level()
        yield_curve = self.get_yield_curve_slope()
        market_momentum = self.get_market_momentum()
        
        if vix > 25:
            return MarketRegime.HIGH_VOLATILITY
        elif yield_curve < 0:
            return MarketRegime.BEAR_MARKET
        elif market_momentum > 0.15:
            return MarketRegime.BULL_MARKET
        else:
            return MarketRegime.SIDEWAYS_MARKET
```

### Criteria Adjustments by Regime

#### High Volatility Markets (VIX > 25)
- **Quality Weight**: Increased by 20%
- **Risk Penalty**: Increased by 50%
- **Minimum Thresholds**: Tightened across all metrics
- **Focus**: Defensive, high-quality investments

#### Bear Markets (Yield Curve Inverted)
- **Dividend Yield Bonus**: Increased by 30%
- **Debt Penalty**: Increased by 40%
- **Cash Flow Requirements**: Stricter positive FCF requirements
- **Focus**: Dividend-paying, low-debt investments

#### Bull Markets (Strong Momentum)
- **Growth Weight**: Increased by 15%
- **Risk Tolerance**: Slightly relaxed
- **Innovation Bonus**: Higher weight for disruptive technologies
- **Focus**: Growth and momentum investments

#### High Inflation (>4%)
- **Real Asset Bonus**: Increased weight for commodities, REITs
- **Pricing Power**: Higher weight for companies with pricing power
- **Fixed Income Penalty**: Reduced weight for bonds and utilities
- **Focus**: Inflation-protected assets

## A+ Threshold Determination

### Base Thresholds

```python
A_PLUS_THRESHOLDS = {
    'composite_score': 0.95,      # Overall score threshold
    'minimum_component': 0.70,    # No component below this level
    'confidence_level': 0.80,     # Minimum confidence in analysis
    'data_quality': 0.90          # Minimum data completeness
}
```

### Dynamic Threshold Adjustment

```python
def adjust_thresholds_for_market(base_thresholds: dict, 
                                market_regime: MarketRegime) -> dict:
    """Adjust A+ thresholds based on market conditions."""
    adjusted = base_thresholds.copy()
    
    if market_regime == MarketRegime.HIGH_VOLATILITY:
        # Raise the bar during volatile times
        adjusted['composite_score'] = 0.97
        adjusted['minimum_component'] = 0.75
        
    elif market_regime == MarketRegime.BEAR_MARKET:
        # Focus on quality during downturns
        adjusted['quality_minimum'] = 0.85
        adjusted['risk_maximum'] = 0.60
        
    return adjusted
```

## Scoring Validation and Backtesting

### Historical Validation

All A+ scoring criteria are validated against historical data:

```python
class ScoringValidator:
    def validate_criteria(self, lookback_years: int = 10) -> ValidationResult:
        """Validate scoring criteria against historical performance."""
        
        # Get historical A+ candidates
        historical_candidates = self.get_historical_a_plus_candidates(lookback_years)
        
        # Calculate forward returns
        forward_returns = self.calculate_forward_returns(historical_candidates)
        
        # Validate performance
        validation_metrics = {
            'hit_rate': self.calculate_hit_rate(forward_returns),
            'excess_return': self.calculate_excess_return(forward_returns),
            'sharpe_ratio': self.calculate_sharpe_ratio(forward_returns),
            'max_drawdown': self.calculate_max_drawdown(forward_returns)
        }
        
        return ValidationResult(metrics=validation_metrics)
```

### Performance Tracking

```python
class PerformanceTracker:
    def track_a_plus_performance(self, symbol: str, 
                                discovery_date: datetime) -> PerformanceMetrics:
        """Track performance of A+ discoveries over time."""
        
        current_date = datetime.now()
        holding_period = (current_date - discovery_date).days
        
        if holding_period >= 30:  # Minimum 1 month tracking
            returns = self.calculate_returns(symbol, discovery_date, current_date)
            benchmark_returns = self.calculate_benchmark_returns(discovery_date, current_date)
            
            return PerformanceMetrics(
                symbol=symbol,
                holding_period_days=holding_period,
                total_return=returns['total'],
                annualized_return=returns['annualized'],
                excess_return=returns['total'] - benchmark_returns['total'],
                volatility=returns['volatility'],
                sharpe_ratio=returns['sharpe'],
                max_drawdown=returns['max_drawdown']
            )
```

## Implementation Details

### Caching Strategy

```python
from functools import lru_cache
from finwiz.utils.cache_manager import cache_with_ttl

class APlusScoringTool:
    @cache_with_ttl(hours=1)
    def get_market_regime(self) -> MarketRegime:
        """Cache market regime for 1 hour."""
        return self.market_analyzer.detect_current_regime()
    
    @lru_cache(maxsize=1000)
    def calculate_component_score(self, asset_type: str, 
                                 component: str, 
                                 data_hash: str) -> float:
        """Cache component scores to avoid recalculation."""
        return self._calculate_component_score_impl(asset_type, component, data_hash)
```

### Error Handling

```python
class ScoringError(Exception):
    """Base exception for scoring errors."""
    pass

class InsufficientDataError(ScoringError):
    """Raised when insufficient data for scoring."""
    pass

class InvalidAssetTypeError(ScoringError):
    """Raised when unsupported asset type provided."""
    pass

def safe_score_calculation(func):
    """Decorator for safe scoring calculations with fallbacks."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InsufficientDataError:
            # Return partial score with reduced confidence
            return {'score': 0.5, 'confidence': 0.3, 'warning': 'Insufficient data'}
        except Exception as e:
            # Log error and return safe default
            logger.error(f"Scoring error: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'error': str(e)}
    return wrapper
```

### Performance Optimization

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelScoringEngine:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def score_multiple_assets(self, candidates: List[dict]) -> List[dict]:
        """Score multiple assets in parallel."""
        
        # Split into batches for parallel processing
        batch_size = 10
        batches = [candidates[i:i+batch_size] 
                  for i in range(0, len(candidates), batch_size)]
        
        # Process batches in parallel
        tasks = [self._score_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*tasks)
        
        # Flatten results
        return [result for batch in batch_results for result in batch]
    
    async def _score_batch(self, batch: List[dict]) -> List[dict]:
        """Score a batch of assets."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._score_batch_sync, 
            batch
        )
```

## Configuration and Customization

### Configuration File Structure

```yaml
# config/a_plus_scoring.yaml
scoring:
  weights:
    fundamental: 0.35
    technical: 0.20
    quality: 0.30
    risk: 0.15
  
  thresholds:
    a_plus_minimum: 0.95
    component_minimum: 0.70
    confidence_minimum: 0.80
  
  etf_criteria:
    max_expense_ratio: 0.15
    min_aum_billions: 1.0
    max_tracking_error: 0.002
    min_history_years: 3
  
  stock_criteria:
    min_roe: 0.20
    min_revenue_growth: 0.15
    max_debt_to_equity: 0.30
    min_market_cap_billions: 1.0
  
  crypto_criteria:
    min_market_cap_billions: 10.0
    min_daily_volume_millions: 500.0
    min_age_months: 36
    require_institutional_adoption: true

market_regimes:
  high_volatility:
    vix_threshold: 25
    quality_weight_multiplier: 1.2
    risk_penalty_multiplier: 1.5
  
  bear_market:
    yield_curve_threshold: 0
    dividend_bonus_multiplier: 1.3
    debt_penalty_multiplier: 1.4
```

### Custom Scoring Models

```python
class CustomScoringModel:
    """Allows users to define custom scoring models."""
    
    def __init__(self, config: dict):
        self.config = config
        self.weights = config.get('weights', {})
        self.criteria = config.get('criteria', {})
    
    def score_investment(self, symbol: str, data: dict) -> dict:
        """Score investment using custom model."""
        
        # Apply custom weights
        component_scores = {
            'fundamental': self.calculate_fundamental_score(data) * self.weights.get('fundamental', 0.35),
            'technical': self.calculate_technical_score(data) * self.weights.get('technical', 0.20),
            'quality': self.calculate_quality_score(data) * self.weights.get('quality', 0.30),
            'risk': self.calculate_risk_score(data) * self.weights.get('risk', 0.15)
        }
        
        composite_score = sum(component_scores.values())
        
        return {
            'symbol': symbol,
            'composite_score': composite_score,
            'component_scores': component_scores,
            'grade': self.score_to_grade(composite_score),
            'is_a_plus': composite_score >= self.criteria.get('a_plus_threshold', 0.95)
        }
```

## Quality Assurance

### Unit Testing

```python
class TestAPlusScoring:
    def test_etf_scoring_with_excellent_metrics(self):
        """Test ETF scoring with A+ quality metrics."""
        data = {
            'expense_ratio': 0.03,
            'aum': 50e9,
            'tracking_error': 0.0005,
            'history_years': 10
        }
        
        score = self.scorer.calculate_etf_fundamental_score(data)
        assert score >= 0.95
    
    def test_market_regime_adaptation(self):
        """Test scoring adaptation to market regimes."""
        base_criteria = self.scorer.get_base_criteria()
        
        # High volatility should tighten criteria
        volatile_criteria = self.scorer.adjust_criteria_for_regime(
            base_criteria, MarketRegime.HIGH_VOLATILITY
        )
        
        assert volatile_criteria['quality_weight'] > base_criteria['quality_weight']
        assert volatile_criteria['risk_penalty'] > base_criteria['risk_penalty']
```

### Integration Testing

```python
class TestScoringIntegration:
    def test_end_to_end_scoring_workflow(self):
        """Test complete scoring workflow from data to grade."""
        
        # Mock market data
        mock_data = self.get_mock_etf_data()
        
        # Run scoring
        result = self.scoring_tool._run(
            symbol='VTI',
            asset_type='etf',
            fundamental_data=mock_data
        )
        
        # Validate result structure
        assert 'grade' in result
        assert 'composite_score' in result
        assert 'component_scores' in result
        assert result['grade'] in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
```

## Monitoring and Maintenance

### Performance Monitoring

```python
class ScoringMonitor:
    def monitor_scoring_performance(self):
        """Monitor scoring system performance and accuracy."""
        
        metrics = {
            'daily_scores_calculated': self.get_daily_score_count(),
            'average_scoring_time': self.get_average_scoring_time(),
            'error_rate': self.get_error_rate(),
            'cache_hit_rate': self.get_cache_hit_rate(),
            'a_plus_discovery_rate': self.get_a_plus_discovery_rate()
        }
        
        # Alert if metrics exceed thresholds
        if metrics['error_rate'] > 0.05:
            self.send_alert('High scoring error rate detected')
        
        if metrics['average_scoring_time'] > 5.0:
            self.send_alert('Scoring performance degradation detected')
        
        return metrics
```

### Model Validation

```python
class ModelValidator:
    def validate_scoring_model(self, validation_period_months: int = 6):
        """Validate scoring model accuracy over time."""
        
        # Get A+ predictions from validation period
        predictions = self.get_historical_predictions(validation_period_months)
        
        # Calculate actual performance
        actual_performance = self.calculate_actual_performance(predictions)
        
        # Validation metrics
        validation_results = {
            'precision': self.calculate_precision(predictions, actual_performance),
            'recall': self.calculate_recall(predictions, actual_performance),
            'f1_score': self.calculate_f1_score(predictions, actual_performance),
            'excess_return': self.calculate_excess_return(predictions, actual_performance)
        }
        
        # Recommend model updates if performance degrades
        if validation_results['precision'] < 0.70:
            self.recommend_model_update('Low precision detected')
        
        return validation_results
```

---

This methodology document provides the technical foundation for understanding and extending the A+ Investment Scoring system. For implementation details, see the [Developer Guide](investment_discovery_developer_guide.md) and [API Reference](investment_discovery_api_reference.md).