# Discovery Schemas

Schemas for investment discovery, opportunity identification, and alternative suggestions.

## APlusDiscoveryResult

Results from A+ investment opportunity discovery across asset classes.

### Schema Definition

```python
class APlusDiscoveryResult(BaseModel):
    discovery_date: datetime = Field(default_factory=datetime.now)
    discovery_criteria: Dict[str, Any] = Field(default_factory=dict)
    
    # Discovery summary
    total_opportunities: int = Field(..., ge=0)
    asset_breakdown: Dict[str, int] = Field(default_factory=dict)
    
    # Opportunities by category
    stock_opportunities: List[InvestmentCandidate] = Field(default_factory=list)
    etf_opportunities: List[InvestmentCandidate] = Field(default_factory=list)
    crypto_opportunities: List[InvestmentCandidate] = Field(default_factory=list)
    
    # Categorized opportunities
    opportunity_sections: List[APlusOpportunitySection] = Field(default_factory=list)
    
    # Discovery quality metrics
    screening_universe_size: int = Field(..., ge=0)
    pass_rate: float = Field(..., ge=0.0, le=1.0)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    
    # Market context
    market_conditions: Dict[str, Any] = Field(default_factory=dict)
    discovery_notes: str = Field(default="")
    
    # Data sources and freshness
    data_sources: List[str] = Field(default_factory=list)
    data_freshness: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True
    }
```

### Example

```json
{
  "discovery_date": "2025-01-15T10:30:00Z",
  "discovery_criteria": {
    "min_market_cap": 1000000000,
    "min_volume": 1000000,
    "max_risk_score": 7,
    "asset_classes": ["stock", "etf", "crypto"]
  },
  "total_opportunities": 25,
  "asset_breakdown": {
    "stock": 15,
    "etf": 7,
    "crypto": 3
  },
  "stock_opportunities": [
    {
      "ticker": "MSFT",
      "name": "Microsoft Corporation",
      "asset_class": "stock",
      "grade": "A+",
      "confidence": 0.92,
      "key_strengths": ["Strong cloud growth", "Excellent margins"]
    }
  ],
  "opportunity_sections": [
    {
      "category": "Technology Leaders",
      "description": "Established technology companies with strong fundamentals",
      "opportunities": ["MSFT", "GOOGL", "NVDA"]
    }
  ],
  "screening_universe_size": 5000,
  "pass_rate": 0.005,
  "confidence_level": 0.88,
  "market_conditions": {
    "market_regime": "BULL",
    "volatility_level": "MODERATE",
    "sector_rotation": "TECHNOLOGY_FAVORED"
  }
}
```

## InvestmentCandidate

Individual investment opportunity identified through discovery process.

### Schema Definition

```python
class InvestmentCandidate(BaseModel):
    ticker: str = Field(..., description="Asset ticker symbol")
    name: str = Field(..., description="Asset name")
    asset_class: Literal["stock", "etf", "crypto"]
    
    # Grading and scoring
    grade: str = Field(..., pattern=r'^A\+$|^[A-F][+-]?$')
    composite_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    # Key metrics (asset-class specific)
    key_metrics: Dict[str, float] = Field(default_factory=dict)
    
    # Strengths and opportunities
    key_strengths: List[str] = Field(default_factory=list)
    growth_catalysts: List[str] = Field(default_factory=list)
    
    # Risk assessment
    risk_score: int = Field(..., ge=1, le=10)
    risk_factors: List[str] = Field(default_factory=list)
    
    # Market context
    current_price: Optional[float] = Field(None, gt=0)
    price_target: Optional[float] = Field(None, gt=0)
    upside_potential: Optional[float] = Field(None, ge=0.0)
    
    # Discovery context
    discovery_reason: str = Field(..., min_length=50)
    category: Optional[str] = Field(None, description="Opportunity category")
    
    # Data quality
    data_completeness: float = Field(..., ge=0.0, le=1.0)
    analysis_depth: Literal["BASIC", "STANDARD", "COMPREHENSIVE"] = Field(default="STANDARD")
    
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
  "grade": "A+",
  "composite_score": 0.92,
  "confidence": 0.89,
  "key_metrics": {
    "pe_ratio": 28.5,
    "revenue_growth": 0.18,
    "profit_margin": 0.36,
    "roe": 0.42,
    "debt_to_equity": 0.35
  },
  "key_strengths": [
    "Dominant cloud platform position",
    "Strong recurring revenue model",
    "Excellent capital allocation",
    "Diversified product portfolio"
  ],
  "growth_catalysts": [
    "AI integration across products",
    "Cloud market expansion",
    "Enterprise digital transformation"
  ],
  "risk_score": 4,
  "risk_factors": [
    "High valuation multiples",
    "Regulatory scrutiny",
    "Cloud competition"
  ],
  "current_price": 420.00,
  "price_target": 480.00,
  "upside_potential": 0.14,
  "discovery_reason": "Microsoft demonstrates exceptional fundamentals with strong cloud growth, excellent margins, and dominant market position in enterprise software",
  "category": "Technology Leaders",
  "data_completeness": 0.95,
  "analysis_depth": "COMPREHENSIVE"
}
```

## APlusOpportunitySection

Categorized grouping of A+ investment opportunities.

### Schema Definition

```python
class APlusOpportunitySection(BaseModel):
    category: str = Field(..., min_length=5, description="Opportunity category name")
    description: str = Field(..., min_length=20, description="Category description")
    
    # Opportunities in this category
    opportunities: List[str] = Field(..., min_items=1, description="Ticker symbols")
    opportunity_count: int = Field(..., ge=1)
    
    # Category characteristics
    avg_grade: str = Field(..., pattern=r'^A\+$|^[A-F][+-]?$')
    avg_confidence: float = Field(..., ge=0.0, le=1.0)
    avg_risk_score: float = Field(..., ge=1.0, le=10.0)
    
    # Category themes
    common_strengths: List[str] = Field(default_factory=list)
    shared_catalysts: List[str] = Field(default_factory=list)
    category_risks: List[str] = Field(default_factory=list)
    
    # Investment thesis
    category_thesis: str = Field(..., min_length=100)
    
    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True
    }
```

### Example

```json
{
  "category": "Technology Leaders",
  "description": "Established technology companies with dominant market positions and strong growth prospects",
  "opportunities": ["MSFT", "GOOGL", "NVDA", "AAPL"],
  "opportunity_count": 4,
  "avg_grade": "A+",
  "avg_confidence": 0.87,
  "avg_risk_score": 4.5,
  "common_strengths": [
    "Strong competitive moats",
    "Excellent profit margins",
    "Robust cash generation",
    "Innovation leadership"
  ],
  "shared_catalysts": [
    "AI technology adoption",
    "Digital transformation trends",
    "Cloud computing growth"
  ],
  "category_risks": [
    "Regulatory scrutiny",
    "High valuations",
    "Technology disruption"
  ],
  "category_thesis": "Technology leaders represent the highest quality investment opportunities with sustainable competitive advantages, strong financial metrics, and exposure to long-term growth trends in artificial intelligence and digital transformation."
}
```

## APlusImprovementSuggestion

Specific suggestions for improving portfolio through A+ opportunities.

### Schema Definition

```python
class APlusImprovementSuggestion(BaseModel):
    suggestion_type: Literal["REPLACE", "ADD", "INCREASE", "DIVERSIFY"]
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    
    # Current situation
    current_holding: Optional[str] = Field(None, description="Current ticker to replace/modify")
    current_allocation: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Suggested action
    suggested_ticker: str = Field(..., description="A+ opportunity ticker")
    suggested_allocation: float = Field(..., ge=0.0, le=1.0)
    
    # Expected benefits
    expected_return_improvement: Optional[float] = Field(None)
    expected_risk_improvement: Optional[float] = Field(None)
    diversification_benefit: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Rationale
    improvement_rationale: str = Field(..., min_length=100)
    key_advantages: List[str] = Field(default_factory=list)
    
    # Implementation
    implementation_timeline: Literal["IMMEDIATE", "SHORT", "MEDIUM", "LONG"]
    implementation_notes: str = Field(default="")
    
    # Confidence
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True
    }
```

## Validation Rules

### Discovery-Specific Validation

```python
@field_validator('grade')
@classmethod
def validate_aplus_grade(cls, v: str) -> str:
    valid_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F']
    if v not in valid_grades:
        raise ValueError(f'Invalid grade: {v}')
    return v

@field_validator('opportunities')
@classmethod
def validate_opportunity_tickers(cls, v: List[str]) -> List[str]:
    for ticker in v:
        if not ticker.replace('-', '').replace('.', '').isalnum():
            raise ValueError(f'Invalid ticker format: {ticker}')
    return [ticker.upper() for ticker in v]

@field_validator('pass_rate')
@classmethod
def validate_pass_rate(cls, v: float) -> float:
    if not 0.0 <= v <= 1.0:
        raise ValueError('Pass rate must be between 0.0 and 1.0')
    return v
```

### Consistency Validation

```python
@model_validator(mode='after')
def validate_opportunity_consistency(self) -> 'APlusDiscoveryResult':
    # Validate total opportunities matches breakdown
    calculated_total = sum(self.asset_breakdown.values())
    if calculated_total != self.total_opportunities:
        raise ValueError('Asset breakdown does not sum to total opportunities')
    
    # Validate opportunity lists match breakdown
    actual_stocks = len(self.stock_opportunities)
    expected_stocks = self.asset_breakdown.get('stock', 0)
    if actual_stocks != expected_stocks:
        raise ValueError(f'Stock opportunities count mismatch: {actual_stocks} vs {expected_stocks}')
    
    return self
```

## Usage Examples

### Creating Discovery Results

```python
from finwiz.schemas.discovery import APlusDiscoveryResult, InvestmentCandidate, APlusOpportunitySection

# Create investment candidates
candidates = [
    InvestmentCandidate(
        ticker="MSFT",
        name="Microsoft Corporation",
        asset_class="stock",
        grade="A+",
        composite_score=0.92,
        confidence=0.89,
        key_strengths=["Strong cloud growth", "Excellent margins"],
        risk_score=4,
        discovery_reason="Exceptional fundamentals and market position",
        data_completeness=0.95
    )
]

# Create opportunity sections
sections = [
    APlusOpportunitySection(
        category="Technology Leaders",
        description="Dominant tech companies with strong growth",
        opportunities=["MSFT", "GOOGL"],
        opportunity_count=2,
        avg_grade="A+",
        avg_confidence=0.87,
        avg_risk_score=4.5,
        category_thesis="Technology leaders offer the best risk-adjusted returns"
    )
]

# Create discovery results
discovery = APlusDiscoveryResult(
    total_opportunities=25,
    asset_breakdown={"stock": 15, "etf": 7, "crypto": 3},
    stock_opportunities=candidates,
    opportunity_sections=sections,
    screening_universe_size=5000,
    pass_rate=0.005,
    confidence_level=0.88
)
```

### Filtering Opportunities

```python
# Filter by grade
aplus_only = [
    candidate for candidate in discovery.stock_opportunities 
    if candidate.grade == "A+"
]

# Filter by risk score
low_risk = [
    candidate for candidate in discovery.stock_opportunities 
    if candidate.risk_score <= 5
]

# Filter by confidence
high_confidence = [
    candidate for candidate in discovery.stock_opportunities 
    if candidate.confidence >= 0.8
]
```

### Creating Improvement Suggestions

```python
from finwiz.schemas.discovery import APlusImprovementSuggestion

suggestion = APlusImprovementSuggestion(
    suggestion_type="REPLACE",
    priority="HIGH",
    current_holding="IBM",
    current_allocation=0.10,
    suggested_ticker="MSFT",
    suggested_allocation=0.10,
    expected_return_improvement=0.05,
    expected_risk_improvement=0.02,
    improvement_rationale="Microsoft offers superior growth prospects and financial metrics compared to IBM",
    key_advantages=["Better cloud position", "Higher margins", "Stronger growth"],
    implementation_timeline="SHORT",
    confidence=0.85
)
```

## Integration with Analysis

Discovery schemas integrate with analysis schemas:

```python
# Convert discovery candidate to full analysis
def convert_to_analysis(candidate: InvestmentCandidate) -> TenKInsight:
    if candidate.asset_class == "stock":
        return TenKInsight(
            ticker=candidate.ticker,
            company_name=candidate.name,
            recommendation="BUY" if candidate.grade in ["A+", "A"] else "HOLD",
            confidence_level=candidate.confidence,
            # ... other fields from detailed analysis
        )
```

## Related Documentation

- [Analysis Schemas](analysis_schemas.md) - Individual asset analysis schemas
- [Portfolio Schemas](portfolio_schemas.md) - Portfolio management schemas
- [Validation Schemas](validation_schemas.md) - Input validation schemas
- [Schema Relationships](relationships.md) - How schemas relate to each other