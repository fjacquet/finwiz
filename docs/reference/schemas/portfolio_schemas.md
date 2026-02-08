# Portfolio Schemas

Schemas for portfolio management, analysis, and optimization.

## PortfolioReview

Comprehensive portfolio analysis with holdings evaluation and recommendations.

### Schema Definition

```python
class PortfolioReview(BaseModel):
    portfolio_id: str = Field(..., description="Unique portfolio identifier")
    analysis_date: datetime = Field(default_factory=datetime.now)

    # Portfolio overview
    total_value: float = Field(..., gt=0, description="Total portfolio value")
    currency: str = Field(default="USD", description="Portfolio currency")

    # Holdings analysis
    holdings: List[HoldingDecision] = Field(default_factory=list)
    total_holdings: int = Field(..., ge=0)

    # Performance metrics
    ytd_return: Optional[float] = None
    one_year_return: Optional[float] = None
    three_year_return: Optional[float] = None

    # Risk metrics
    portfolio_risk_score: int = Field(..., ge=1, le=10)
    portfolio_volatility: Optional[float] = Field(None, ge=0.0)
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = Field(None, le=0.0)

    # Diversification analysis
    sector_diversification: Dict[str, float] = Field(default_factory=dict)
    geographic_diversification: Dict[str, float] = Field(default_factory=dict)
    asset_class_allocation: Dict[str, float] = Field(default_factory=dict)

    # Recommendations
    overall_grade: str = Field(..., pattern=r'^[A-F][+-]?$')
    improvement_potential: float = Field(..., ge=0.0, le=1.0)
    rebalancing_needed: bool = Field(default=False)

    # Alternative suggestions
    alternatives: List[Alternative] = Field(default_factory=list)

    # Summary
    executive_summary: str = Field(..., min_length=200)
    key_recommendations: List[str] = Field(default_factory=list)

    # Data quality
    data_freshness: datetime = Field(default_factory=datetime.now)
    confidence_level: float = Field(..., ge=0.0, le=1.0)

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True
    }
```

### Example

```json
{
  "portfolio_id": "user_portfolio_001",
  "analysis_date": "2025-01-15T10:30:00Z",
  "total_value": 250000.00,
  "currency": "USD",
  "holdings": [
    {
      "ticker": "AAPL",
      "decision": "KEEP",
      "current_allocation": 0.25,
      "recommended_allocation": 0.20,
      "rationale": "Strong fundamentals but overweight"
    }
  ],
  "total_holdings": 15,
  "ytd_return": 0.12,
  "one_year_return": 0.18,
  "portfolio_risk_score": 6,
  "portfolio_volatility": 0.16,
  "sharpe_ratio": 1.25,
  "sector_diversification": {
    "Technology": 0.35,
    "Healthcare": 0.20,
    "Financial Services": 0.15,
    "Consumer Goods": 0.30
  },
  "asset_class_allocation": {
    "Stocks": 0.70,
    "ETFs": 0.25,
    "Crypto": 0.05
  },
  "overall_grade": "B+",
  "improvement_potential": 0.15,
  "rebalancing_needed": true,
  "alternatives": [
    {
      "ticker": "MSFT",
      "reason": "Better risk-adjusted returns",
      "confidence": 0.80
    }
  ],
  "executive_summary": "Portfolio shows strong performance with room for improvement through diversification and rebalancing.",
  "key_recommendations": [
    "Reduce technology sector concentration",
    "Add international exposure",
    "Consider rebalancing quarterly"
  ],
  "confidence_level": 0.85
}
```

## HoldingDecision

Individual holding analysis with keep/sell/rebalance recommendations.

### Schema Definition

```python
class HoldingDecision(BaseModel):
    ticker: str = Field(..., description="Asset ticker symbol")
    asset_class: str = Field(..., description="Asset class (stock, etf, crypto)")

    # Current position
    current_shares: float = Field(..., gt=0)
    current_value: float = Field(..., gt=0)
    current_allocation: float = Field(..., ge=0.0, le=1.0)
    average_cost: Optional[float] = Field(None, gt=0)

    # Analysis results
    decision: Literal["KEEP", "SELL", "REDUCE", "INCREASE"] = Field(...)
    recommended_allocation: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Performance metrics
    unrealized_gain_loss: Optional[float] = None
    unrealized_gain_loss_pct: Optional[float] = None

    # Analysis details
    grade: Optional[str] = Field(None, pattern=r'^[A-F][+-]?$')
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str = Field(..., min_length=50)

    # Risk assessment
    risk_score: int = Field(..., ge=1, le=10)
    risk_contribution: float = Field(..., ge=0.0, le=1.0)

    # Recommendations
    action_priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(default="MEDIUM")
    time_horizon: Literal["IMMEDIATE", "SHORT", "MEDIUM", "LONG"] = Field(default="MEDIUM")

    # Alternative suggestions
    alternatives: List[str] = Field(default_factory=list)

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True
    }
```

### Example

```json
{
  "ticker": "AAPL",
  "asset_class": "stock",
  "current_shares": 100,
  "current_value": 15000.00,
  "current_allocation": 0.25,
  "average_cost": 120.00,
  "decision": "REDUCE",
  "recommended_allocation": 0.20,
  "unrealized_gain_loss": 3000.00,
  "unrealized_gain_loss_pct": 0.25,
  "grade": "A-",
  "confidence": 0.85,
  "rationale": "Strong fundamentals but position is overweight relative to optimal portfolio allocation",
  "risk_score": 4,
  "risk_contribution": 0.30,
  "action_priority": "MEDIUM",
  "time_horizon": "SHORT",
  "alternatives": ["MSFT", "GOOGL"]
}
```

## Alternative

Alternative investment suggestion to replace or complement existing holdings.

### Schema Definition

```python
class Alternative(BaseModel):
    ticker: str = Field(..., description="Alternative asset ticker")
    name: str = Field(..., description="Asset name")
    asset_class: str = Field(..., description="Asset class")

    # Replacement context
    replaces: Optional[str] = Field(None, description="Ticker being replaced")
    reason: str = Field(..., min_length=50, description="Why this alternative")

    # Expected benefits
    expected_return: Optional[float] = Field(None, description="Expected annual return")
    risk_improvement: Optional[float] = Field(None, description="Risk reduction")
    diversification_benefit: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Recommendation strength
    confidence: float = Field(..., ge=0.0, le=1.0)
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(default="MEDIUM")

    # Implementation
    suggested_allocation: Optional[float] = Field(None, ge=0.0, le=1.0)
    implementation_timeline: Literal["IMMEDIATE", "SHORT", "MEDIUM", "LONG"] = Field(default="MEDIUM")

    # Analysis
    key_advantages: List[str] = Field(default_factory=list)
    potential_risks: List[str] = Field(default_factory=list)

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True
    }
```

### Example

```json
{
  "ticker": "MSFT",
  "name": "Microsoft Corporation",
  "asset_class": "stock",
  "replaces": "IBM",
  "reason": "Microsoft offers better growth prospects, stronger cloud business, and superior financial metrics compared to IBM",
  "expected_return": 0.15,
  "risk_improvement": 0.02,
  "diversification_benefit": 0.15,
  "confidence": 0.85,
  "priority": "HIGH",
  "suggested_allocation": 0.08,
  "implementation_timeline": "SHORT",
  "key_advantages": [
    "Strong cloud growth",
    "Excellent margins",
    "Diversified revenue streams"
  ],
  "potential_risks": [
    "High valuation",
    "Regulatory scrutiny",
    "Competition in cloud"
  ]
}
```

## OptimizationResult

Portfolio optimization results with recommended allocation changes.

### Schema Definition

```python
class OptimizationResult(BaseModel):
    optimization_date: datetime = Field(default_factory=datetime.now)
    optimization_method: str = Field(..., description="Optimization method used")

    # Current vs optimized portfolio
    current_portfolio: Dict[str, float] = Field(..., description="Current allocations")
    optimized_portfolio: Dict[str, float] = Field(..., description="Optimal allocations")

    # Expected improvements
    expected_return_improvement: float = Field(..., description="Expected return increase")
    expected_risk_reduction: float = Field(..., description="Expected risk decrease")
    expected_sharpe_improvement: float = Field(..., description="Sharpe ratio improvement")

    # Implementation details
    trades_required: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_transaction_costs: float = Field(default=0.0, ge=0.0)
    net_expected_benefit: float = Field(..., description="Benefit after costs")

    # Constraints applied
    constraints: Dict[str, Any] = Field(default_factory=dict)

    # Confidence and validation
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    backtesting_results: Optional[Dict[str, float]] = Field(None)

    model_config = {
        "extra": "forbid"
    }
```

## PortfolioImprovement

Specific improvement suggestions for portfolio enhancement.

### Schema Definition

```python
class PortfolioImprovement(BaseModel):
    improvement_type: Literal["DIVERSIFICATION", "RISK_REDUCTION", "RETURN_ENHANCEMENT", "COST_REDUCTION"]
    priority: Literal["HIGH", "MEDIUM", "LOW"]

    # Description
    title: str = Field(..., min_length=10)
    description: str = Field(..., min_length=50)

    # Expected impact
    expected_benefit: float = Field(..., ge=0.0, le=1.0)
    implementation_difficulty: Literal["EASY", "MODERATE", "DIFFICULT"]

    # Implementation
    action_items: List[str] = Field(default_factory=list)
    timeline: str = Field(..., description="Implementation timeline")

    # Metrics
    current_metric: Optional[float] = None
    target_metric: Optional[float] = None

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True
    }
```

## Validation Rules

### Portfolio-Level Validation

```python
@field_validator('holdings')
@classmethod
def validate_holdings_allocation(cls, v: List[HoldingDecision]) -> List[HoldingDecision]:
    total_allocation = sum(holding.current_allocation for holding in v)
    if abs(total_allocation - 1.0) > 0.01:  # Allow 1% tolerance
        raise ValueError(f'Holdings allocations sum to {total_allocation}, should be 1.0')
    return v

@field_validator('overall_grade')
@classmethod
def validate_grade_format(cls, v: str) -> str:
    if not re.match(r'^[A-F][+-]?$', v):
        raise ValueError('Grade must be A-F with optional + or -')
    return v
```

### Holding-Level Validation

```python
@field_validator('decision')
@classmethod
def validate_decision_consistency(cls, v: str, info: ValidationInfo) -> str:
    if 'recommended_allocation' in info.data:
        current = info.data.get('current_allocation', 0)
        recommended = info.data['recommended_allocation']

        if v == "KEEP" and abs(current - recommended) > 0.05:
            raise ValueError('KEEP decision inconsistent with allocation change')
    return v
```

## Usage Examples

### Creating Portfolio Review

```python
from finwiz.schemas.portfolio import PortfolioReview, HoldingDecision, Alternative

# Create holding decisions
holdings = [
    HoldingDecision(
        ticker="AAPL",
        asset_class="stock",
        current_shares=100,
        current_value=15000,
        current_allocation=0.25,
        decision="REDUCE",
        recommended_allocation=0.20,
        confidence=0.85,
        rationale="Strong stock but overweight",
        risk_score=4,
        risk_contribution=0.30
    )
]

# Create alternatives
alternatives = [
    Alternative(
        ticker="MSFT",
        name="Microsoft Corporation",
        asset_class="stock",
        reason="Better growth prospects",
        confidence=0.80,
        expected_return=0.15
    )
]

# Create portfolio review
portfolio = PortfolioReview(
    portfolio_id="user_001",
    total_value=100000,
    holdings=holdings,
    total_holdings=len(holdings),
    overall_grade="B+",
    improvement_potential=0.15,
    alternatives=alternatives,
    executive_summary="Portfolio shows good performance with room for improvement",
    confidence_level=0.85
)
```

### Validation

```python
from pydantic import ValidationError

try:
    portfolio = PortfolioReview.model_validate(portfolio_data)
    print(f"Portfolio {portfolio.portfolio_id} is valid")
except ValidationError as e:
    for error in e.errors():
        print(f"Validation error in {error['loc']}: {error['msg']}")
```

## Related Documentation

- [Analysis Schemas](analysis_schemas.md) - Individual asset analysis schemas
- [Discovery Schemas](discovery_schemas.md) - Investment discovery schemas
- [Validation Schemas](validation_schemas.md) - Input validation schemas
- [Schema Relationships](relationships.md) - How schemas relate to each other
