# Analysis Schemas

Core schemas for financial analysis results across all asset classes.

## TenKInsight

Comprehensive stock analysis schema based on SEC 10-K filings and market data.

### Schema Definition

```python
class TenKInsight(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Company name")
    analysis_date: datetime = Field(default_factory=datetime.now)
    recommendation: Literal["BUY", "HOLD", "SELL"]
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    price_target: Optional[float] = Field(None, gt=0)
    current_price: float = Field(..., gt=0)
    
    # Financial metrics
    financial_metrics: Dict[str, float] = Field(default_factory=dict)
    
    # Risk assessment
    risk_assessment: RiskAssessmentStandardized
    
    # Analysis rationale
    rationale: str = Field(..., min_length=100)
    key_strengths: List[str] = Field(default_factory=list)
    key_concerns: List[str] = Field(default_factory=list)
    
    # Data sources
    data_sources: List[str] = Field(default_factory=list)
    
    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True
    }
```

### Example

```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "analysis_date": "2025-01-15T10:30:00Z",
  "recommendation": "BUY",
  "confidence_level": 0.85,
  "price_target": 180.00,
  "current_price": 150.00,
  "financial_metrics": {
    "pe_ratio": 25.5,
    "revenue_growth": 0.15,
    "profit_margin": 0.25,
    "debt_to_equity": 0.3,
    "roe": 0.28,
    "current_ratio": 1.2
  },
  "risk_assessment": {
    "overall_risk_score": 4,
    "systematic_risk": 0.6,
    "idiosyncratic_risk": 0.3,
    "risk_factors": ["Market volatility", "Tech sector exposure"],
    "risk_category": "MODERATE"
  },
  "rationale": "Apple demonstrates strong fundamentals with consistent revenue growth, excellent profit margins, and a robust balance sheet. The company's ecosystem creates strong customer loyalty and recurring revenue streams.",
  "key_strengths": [
    "Strong brand loyalty and ecosystem",
    "Consistent revenue growth",
    "Excellent profit margins",
    "Strong balance sheet"
  ],
  "key_concerns": [
    "High valuation multiples",
    "Dependence on iPhone sales",
    "Regulatory scrutiny"
  ],
  "data_sources": [
    "SEC EDGAR",
    "Yahoo Finance",
    "Alpha Vantage"
  ]
}
```

## ETFFactsheet

Comprehensive ETF analysis including expense ratios, holdings, and tracking performance.

### Schema Definition

```python
class ETFFactsheet(BaseModel):
    ticker: str = Field(..., description="ETF ticker symbol")
    fund_name: str = Field(..., description="ETF name")
    analysis_date: datetime = Field(default_factory=datetime.now)
    recommendation: Literal["BUY", "HOLD", "SELL"]
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    
    # ETF-specific metrics
    expense_ratio: float = Field(..., ge=0.0, le=1.0)
    aum: float = Field(..., gt=0, description="Assets under management")
    tracking_error: Optional[float] = Field(None, ge=0.0)
    
    # Holdings analysis
    top_holdings: List[ETFTopHolding] = Field(default_factory=list)
    sector_allocation: Dict[str, float] = Field(default_factory=dict)
    
    # Performance metrics
    ytd_return: Optional[float] = None
    one_year_return: Optional[float] = None
    three_year_return: Optional[float] = None
    
    # Risk assessment
    risk_assessment: RiskAssessmentStandardized
    
    # Analysis
    rationale: str = Field(..., min_length=100)
    key_strengths: List[str] = Field(default_factory=list)
    key_concerns: List[str] = Field(default_factory=list)
    
    # Data sources
    data_sources: List[str] = Field(default_factory=list)
```

### Example

```json
{
  "ticker": "VTI",
  "fund_name": "Vanguard Total Stock Market ETF",
  "analysis_date": "2025-01-15T10:30:00Z",
  "recommendation": "BUY",
  "confidence_level": 0.90,
  "expense_ratio": 0.0003,
  "aum": 1500000000000,
  "tracking_error": 0.02,
  "top_holdings": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "weight": 0.065,
      "shares": 1000000
    }
  ],
  "sector_allocation": {
    "Technology": 0.28,
    "Healthcare": 0.14,
    "Financial Services": 0.13,
    "Consumer Cyclical": 0.11
  },
  "ytd_return": 0.12,
  "one_year_return": 0.18,
  "three_year_return": 0.15,
  "risk_assessment": {
    "overall_risk_score": 5,
    "systematic_risk": 0.8,
    "idiosyncratic_risk": 0.1,
    "risk_factors": ["Market risk", "Sector concentration"],
    "risk_category": "MODERATE"
  }
}
```

## CryptoThesis

Cryptocurrency analysis focusing on technology, adoption, and market dynamics.

### Schema Definition

```python
class CryptoThesis(BaseModel):
    ticker: str = Field(..., description="Crypto ticker symbol")
    name: str = Field(..., description="Cryptocurrency name")
    analysis_date: datetime = Field(default_factory=datetime.now)
    recommendation: Literal["BUY", "HOLD", "SELL"]
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    
    # Crypto-specific metrics
    market_cap: float = Field(..., gt=0)
    circulating_supply: Optional[float] = Field(None, gt=0)
    max_supply: Optional[float] = Field(None, gt=0)
    
    # Technology assessment
    technology_score: int = Field(..., ge=1, le=10)
    adoption_score: int = Field(..., ge=1, le=10)
    team_score: int = Field(..., ge=1, le=10)
    
    # Market metrics
    volatility_30d: Optional[float] = Field(None, ge=0.0)
    volume_24h: Optional[float] = Field(None, ge=0.0)
    
    # Risk assessment
    risk_assessment: RiskAssessmentStandardized
    
    # Analysis
    thesis: str = Field(..., min_length=200)
    key_catalysts: List[str] = Field(default_factory=list)
    key_risks: List[str] = Field(default_factory=list)
    
    # Data sources
    data_sources: List[str] = Field(default_factory=list)
```

## MarketSentiment

Market sentiment analysis from news, social media, and analyst reports.

### Schema Definition

```python
class MarketSentiment(BaseModel):
    ticker: str = Field(..., description="Asset ticker symbol")
    analysis_date: datetime = Field(default_factory=datetime.now)
    
    # Sentiment scores
    overall_sentiment: float = Field(..., ge=-1.0, le=1.0)
    news_sentiment: float = Field(..., ge=-1.0, le=1.0)
    social_sentiment: Optional[float] = Field(None, ge=-1.0, le=1.0)
    analyst_sentiment: Optional[float] = Field(None, ge=-1.0, le=1.0)
    
    # Sentiment sources
    news_articles_analyzed: int = Field(default=0, ge=0)
    social_posts_analyzed: int = Field(default=0, ge=0)
    analyst_reports_analyzed: int = Field(default=0, ge=0)
    
    # Key themes
    positive_themes: List[str] = Field(default_factory=list)
    negative_themes: List[str] = Field(default_factory=list)
    
    # Confidence and reliability
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    data_quality_score: float = Field(..., ge=0.0, le=1.0)
    
    # Data sources
    data_sources: List[str] = Field(default_factory=list)
```

## RiskAssessmentStandardized

Standardized risk assessment used across all asset classes.

### Schema Definition

```python
class RiskCategory(str, Enum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"

class RiskAssessmentStandardized(BaseModel):
    overall_risk_score: int = Field(..., ge=1, le=10, description="1=Very Low, 10=Very High")
    systematic_risk: float = Field(..., ge=0.0, le=1.0, description="Market/sector risk component")
    idiosyncratic_risk: float = Field(..., ge=0.0, le=1.0, description="Asset-specific risk")
    
    # Risk categorization
    risk_category: RiskCategory
    
    # Risk factors
    risk_factors: List[str] = Field(default_factory=list)
    risk_mitigation: List[str] = Field(default_factory=list)
    
    # Risk metrics
    volatility: Optional[float] = Field(None, ge=0.0)
    max_drawdown: Optional[float] = Field(None, le=0.0)
    beta: Optional[float] = Field(None)
    
    # Confidence in assessment
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    
    model_config = {
        "extra": "forbid",
        "use_enum_values": True
    }
```

### Risk Score Interpretation

| Score | Category | Description | Typical Assets |
|-------|----------|-------------|----------------|
| 1-2 | Very Low | Minimal risk, stable assets | Treasury bonds, high-grade corporate bonds |
| 3-4 | Low | Below-average risk | Dividend aristocrats, utility stocks |
| 5-6 | Moderate | Average market risk | S&P 500 ETFs, blue-chip stocks |
| 7-8 | High | Above-average risk | Growth stocks, sector ETFs |
| 9-10 | Very High | Extreme risk, speculative | Penny stocks, volatile cryptocurrencies |

## Validation Rules

### Common Validation Patterns

All analysis schemas enforce these validation rules:

```python
# Ticker format validation
@field_validator('ticker')
@classmethod
def validate_ticker_format(cls, v: str) -> str:
    if not v.replace('-', '').replace('.', '').isalnum():
        raise ValueError('Invalid ticker format')
    return v.upper()

# Confidence level validation
@field_validator('confidence_level')
@classmethod
def validate_confidence(cls, v: float) -> float:
    if not 0.0 <= v <= 1.0:
        raise ValueError('Confidence must be between 0.0 and 1.0')
    return v

# Price validation
@field_validator('current_price', 'price_target')
@classmethod
def validate_positive_price(cls, v: Optional[float]) -> Optional[float]:
    if v is not None and v <= 0:
        raise ValueError('Price must be positive')
    return v
```

### Required Fields

All analysis schemas require:

- `ticker` - Asset identifier
- `analysis_date` - When analysis was performed
- `recommendation` - BUY/HOLD/SELL decision
- `confidence_level` - Confidence in recommendation (0.0-1.0)
- `risk_assessment` - Standardized risk assessment
- `rationale` - Detailed explanation (minimum 100 characters)
- `data_sources` - List of data sources used

## Usage Examples

### Creating Analysis Results

```python
from finwiz.schemas.analysis import TenKInsight, RiskAssessmentStandardized

# Create risk assessment
risk_assessment = RiskAssessmentStandardized(
    overall_risk_score=4,
    systematic_risk=0.6,
    idiosyncratic_risk=0.3,
    risk_category="MODERATE",
    risk_factors=["Market volatility", "Sector exposure"],
    confidence_level=0.85
)

# Create stock analysis
analysis = TenKInsight(
    ticker="AAPL",
    company_name="Apple Inc.",
    recommendation="BUY",
    confidence_level=0.85,
    current_price=150.00,
    price_target=180.00,
    risk_assessment=risk_assessment,
    rationale="Strong fundamentals and growth prospects",
    data_sources=["SEC EDGAR", "Yahoo Finance"]
)
```

### Validation

```python
from pydantic import ValidationError

try:
    analysis = TenKInsight.model_validate(data)
    print("Analysis is valid")
except ValidationError as e:
    for error in e.errors():
        print(f"Validation error: {error}")
```

## Related Documentation

- [Portfolio Schemas](portfolio_schemas.md) - Portfolio management schemas
- [Discovery Schemas](discovery_schemas.md) - Investment discovery schemas
- [Validation Schemas](validation_schemas.md) - Input validation schemas
- [Schema Relationships](relationships.md) - How schemas relate to each other