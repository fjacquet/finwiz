---
title: "Schemas Reference"
description: "Complete reference for FinWiz Pydantic schemas and data models"
category: "reference"
tags:
  - "schemas"
  - "pydantic"
  - "data-models"
  - "validation"
date: "2025-10-26"
---

# Schemas Reference

Complete reference documentation for FinWiz's Pydantic schemas and data models used for validation and data structure definition.

!!! info "Interactive Schema Documentation"
    This page uses interactive schema blocks that show properties, examples, and validation rules. Click on "View JSON Schema" to see the complete schema definition.

## Overview

FinWiz uses Pydantic v2 for data validation and serialization. All crew outputs, tool inputs/outputs, and configuration objects are defined using strict Pydantic models with comprehensive validation rules.

## Schema Categories

### Analysis Schemas

Core schemas for investment analysis results.

#### TenKInsight

```schema:TenKInsight
Stock analysis results from SEC filing analysis and fundamental evaluation. This is the primary output schema for individual stock analysis.
```

#### ETFFactsheet

```schema:ETFFactsheet
Comprehensive ETF analysis results including cost analysis, performance metrics, and holdings information.
```

#### CryptoThesis

```schema:CryptoThesis
Cryptocurrency analysis and investment thesis including technology assessment, market dynamics, and regulatory considerations.
```

### Portfolio Schemas

Schemas for portfolio analysis and management.

#### PortfolioReview

```schema:PortfolioReview
Complete portfolio analysis results including holdings analysis, grade distribution, and improvement opportunities.
```

#### HoldingDecision

```schema:HoldingDecision
Individual holding analysis and recommendation including current position, price targets, and alternative suggestions.
```

#### Alternative

```schema:Alternative
Alternative investment suggestion for underperforming holdings with comparison metrics and transition strategies.
```

### Risk Schemas

Schemas for risk assessment and management.

#### RiskAssessmentStandardized

```schema:RiskAssessmentStandardized
Standardized risk assessment across all asset classes with systematic and idiosyncratic risk components.
```

### Discovery Schemas

Schemas for investment discovery and opportunity identification.

#### APlusDiscoveryResult

Results from A+ investment discovery process.

**Location**: `src/finwiz/schemas/aplus_discovery_result.py`

**Purpose**: A+ investment opportunities

**Fields**:

```python
class APlusDiscoveryResult(BaseModel):
    # Discovery metadata
    discovery_date: datetime
    asset_class: str = Field(..., pattern="^(stock|etf|crypto)$")
    
    # Discovered opportunities
    opportunities: List[InvestmentCandidate] = []
    total_opportunities: int = Field(..., ge=0)
    
    # Quality metrics
    avg_composite_score: float = Field(..., ge=0.0, le=1.0)
    score_distribution: Dict[str, int] = {}
    
    # Screening criteria
    screening_criteria: Dict[str, Any] = {}
    total_screened: int = Field(..., ge=0)
    pass_rate: float = Field(..., ge=0.0, le=1.0)
    
    # Market context
    market_conditions: str = Field(..., description="Current market environment")
    sector_distribution: Dict[str, int] = {}
    
    # Metadata
    session_id: str
    data_sources: List[str] = []
```

#### InvestmentCandidate

Individual investment opportunity from discovery process.

**Location**: `src/finwiz/schemas/investment_candidate.py`

**Purpose**: Discovered investment opportunity

**Fields**:

```python
class InvestmentCandidate(BaseModel):
    # Basic information
    ticker: str = Field(..., description="Asset ticker symbol")
    name: str = Field(..., description="Asset name")
    asset_class: str = Field(..., pattern="^(stock|etf|crypto)$")
    
    # Quality assessment
    grade: str = Field(..., pattern="^(A\\+|A|B|C|D|F)$")
    composite_score: float = Field(..., ge=0.0, le=1.0)
    
    # Key metrics
    fundamental_score: float = Field(..., ge=0.0, le=1.0)
    technical_score: float = Field(..., ge=0.0, le=1.0)
    risk_score: int = Field(..., ge=1, le=10)
    
    # Investment thesis
    investment_thesis: str = Field(..., min_length=100)
    key_strengths: List[str] = []
    potential_catalysts: List[str] = []
    
    # Financial metrics (asset-class specific)
    price_target: Optional[float] = None
    upside_potential: Optional[float] = None
    
    # Risk considerations
    risk_factors: List[str] = []
    
    # Discovery metadata
    discovery_rank: int = Field(..., ge=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    data_freshness: str = Field(..., description="Data age assessment")
```

### Validation Schemas

Schemas for data validation and quality assurance.

#### ValidatedTicker

Ticker validation results.

**Location**: `src/finwiz/schemas/validated_ticker.py`

**Purpose**: Ticker symbol validation

**Fields**:

```python
class ValidatedTicker(BaseModel):
    # Input ticker
    ticker: str = Field(..., description="Input ticker symbol")
    
    # Validation results
    is_valid: bool = Field(..., description="Whether ticker is valid")
    normalized_ticker: str = Field(..., description="Normalized ticker format")
    
    # Asset information
    asset_type: str = Field(..., pattern="^(stock|etf|crypto|unknown)$")
    exchange: Optional[str] = None
    currency: Optional[str] = None
    
    # Market status
    is_tradeable: bool = Field(..., description="Whether asset is tradeable")
    market_status: str = Field(..., pattern="^(OPEN|CLOSED|PRE_MARKET|AFTER_HOURS)$")
    
    # Data availability
    has_fundamental_data: bool = False
    has_price_data: bool = False
    has_volume_data: bool = False
    
    # Validation metadata
    validation_date: datetime
    data_source: str = Field(..., description="Validation data source")
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    # Error information (if invalid)
    error_message: Optional[str] = None
    suggestions: List[str] = []
```

#### ValidationResult

Generic validation result for various data types.

**Location**: `src/finwiz/schemas/validation_result.py`

**Purpose**: Generic validation results

**Fields**:

```python
class ValidationResult(BaseModel):
    # Validation status
    is_valid: bool = Field(..., description="Overall validation result")
    validation_type: str = Field(..., description="Type of validation performed")
    
    # Validation details
    passed_checks: List[str] = []
    failed_checks: List[str] = []
    warnings: List[str] = []
    
    # Data quality
    quality_score: float = Field(..., ge=0.0, le=1.0)
    completeness: float = Field(..., ge=0.0, le=1.0)
    freshness_score: float = Field(..., ge=0.0, le=1.0)
    
    # Validation metadata
    validation_date: datetime
    validator_version: str = Field(default="FinWiz Validator v2.0")
    
    # Remediation
    remediation_suggestions: List[str] = []
    can_proceed: bool = Field(..., description="Whether to proceed despite issues")
```

## Schema Validation

### Strict Mode Configuration

All schemas use strict validation:

```python
class BaseSchema(BaseModel):
    model_config = ConfigDict(
        extra='forbid',           # Reject unknown fields
        str_strip_whitespace=True, # Strip whitespace
        validate_assignment=True,  # Validate on assignment
        use_enum_values=True      # Use enum values
    )
```

### Custom Validators

Schemas include custom validation logic:

```python
class TenKInsight(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    
    @field_validator('ticker')
    @classmethod
    def validate_ticker_format(cls, v: str) -> str:
        if not re.match(r'^[A-Z]{1,5}$', v):
            raise ValueError('Ticker must be 1-5 uppercase letters')
        return v.upper()
    
    @model_validator(mode='after')
    def validate_score_consistency(self) -> 'TenKInsight':
        if self.composite_score > 0.95 and self.grade != 'A+':
            raise ValueError('High composite score must have A+ grade')
        return self
```

### Validation Examples

```python
# Valid data
data = {
    "ticker": "AAPL",
    "recommendation": "BUY",
    "grade": "A+",
    "composite_score": 0.92,
    "confidence": 0.87,
    "rationale": "Strong fundamentals with excellent growth prospects and technical momentum",
    "risk_score": 3,
    "analysis_date": "2025-10-26T10:30:00Z",
    "data_sources": ["SEC EDGAR", "Yahoo Finance"]
}

# Create validated instance
insight = TenKInsight.model_validate(data)

# Invalid data (will raise ValidationError)
invalid_data = {
    "ticker": "invalid",  # Invalid format
    "recommendation": "MAYBE",  # Invalid value
    "grade": "A++",  # Invalid grade
    "composite_score": 1.5,  # Out of range
    "confidence": -0.1,  # Negative value
    "rationale": "Too short",  # Below minimum length
    "risk_score": 15,  # Out of range
    "analysis_date": "invalid-date",  # Invalid date format
}

try:
    TenKInsight.model_validate(invalid_data)
except ValidationError as e:
    print(f"Validation errors: {e}")
```

## Schema Usage Patterns

### Crew Output Validation

```python
# In crew task configuration
@task
def analysis_task(self) -> Task:
    return Task(
        config=self.tasks_config['analysis_task'],
        output_pydantic=TenKInsight,  # Automatic validation
        output_json=True
    )
```

### API Response Serialization

```python
# Serialize to JSON
insight_json = insight.model_dump_json()

# Deserialize from JSON
insight = TenKInsight.model_validate_json(json_data)

# Convert to dictionary
insight_dict = insight.model_dump()
```

### Schema Evolution

```python
# Version-aware schema loading
def load_analysis_result(data: dict) -> TenKInsight:
    # Handle legacy format
    if 'version' not in data or data['version'] < '2.0':
        data = migrate_legacy_format(data)
    
    return TenKInsight.model_validate(data)
```

## Related Documentation

- **[Crews Reference](crews.md)** - How crews use schemas
- **[Tools Reference](tools.md)** - Tool input/output schemas
- **[Validation Guide](../../how-to/data_validation.md)** - Data validation best practices
- **[API Reference](index.md)** - Complete API documentation

---

**Version**: 2.0  
**Last Updated**: 2025-10-26
