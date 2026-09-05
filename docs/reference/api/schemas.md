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

**Location**: `src/finwiz/schemas/investment_discovery.py`

**Purpose**: A+ investment opportunities

**Fields**:

```python
class APlusDiscoveryResult(BaseModel):
    asset_type: Literal["etf", "stock", "crypto"]
    total_screened: int = Field(default=0, ge=0)
    candidates_found: int = Field(default=0, ge=0)
    discovery_criteria: APlusCriteria = Field(default_factory=APlusCriteria)
    market_context: MarketRegime
    discovery_timestamp: datetime = Field(default_factory=datetime.now)

    # A+ candidates with detailed analysis
    a_plus_candidates: list[APlusAnalysis] = Field(default_factory=list)

    # Summary statistics
    average_score: float = Field(default=0.0, ge=0.0, le=1.0)
    grade_distribution: dict[Grade, int] = Field(default_factory=dict)
    a_plus_percentage: float = Field(default=0.0, ge=0.0, le=100.0)

    # UCITS compliance for ETFs (European investors)
    ucits_compliant_count: int | None = None
    ucits_compliant_symbols: list[str] = Field(default_factory=list)

    # Recommendations
    top_recommendations: list[str] = Field(default_factory=list)
    implementation_notes: list[str] = Field(default_factory=list)

    # Quality metrics
    high_confidence_count: int = Field(default=0)
    screening_efficiency: float = Field(default=0.0, ge=0.0, le=100.0)
```

#### InvestmentCandidate

Individual investment opportunity from discovery process.

**Location**: `src/finwiz/schemas/investment_discovery.py`

**Purpose**: Discovered investment opportunity

**Fields**:

```python
class InvestmentCandidate(BaseModel):
    symbol: str = Field(..., description="Investment symbol (e.g., AAPL, SPY, BTC-USD)")
    name: str = Field(..., description="Full name of the investment")
    asset_type: Literal["etf", "stock", "crypto"]
    current_price: float = Field(..., gt=0)
    market_cap: float | None = None
    preliminary_score: float = Field(..., ge=0.0, le=1.0, description="Initial A+ score")
    final_score: float = Field(..., ge=0.0, le=1.0, description="Final A+ score after validation")
    grade: Grade = Field(..., description="Letter grade from FinWiz grading system (A+ to F)")
    grade_description: str
    recommended_action: str
    discovery_date: datetime = Field(default_factory=datetime.now)
    data_source: str
    risk_assessment: RiskAssessmentStandardized | None = None
```

### Validation Schemas

Schemas for data validation and quality assurance.

#### ValidatedTicker

Ticker validation results.

**Location**: `src/finwiz/schemas/validation.py`

**Purpose**: Ticker symbol validation. Mirrors the output of
`TickerExistenceValidationTool` (`crewai_custom_tools.tools.finance.enhanced`).

**Fields**:

```python
class ValidatedTicker(BaseModel):
    symbol: str = Field(min_length=1, max_length=15)
    asset_class: Literal["stock", "etf", "crypto"]
    valid: bool
    reason: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
```

#### ValidationResult

Generic validation result for various data types.

**Location**: `src/finwiz/validation/result.py`. This is the generic
validation-error/warning container used across the codebase; note that three
other, purpose-specific `ValidationResult` classes also exist
(`schemas/integration/models.py`, `schemas/investment_discovery.py`,
`validation/int_manager.py`) — check the import path in the code you're
reading before assuming this is the one in scope.

**Purpose**: Generic validation results

**Fields**:

```python
class ValidationError(BaseModel):
    field_path: str = Field(..., description="Dot-separated path to the field that failed validation")
    error_type: str
    message: str
    input_value: Any = None
    context: dict[str, Any] = Field(default_factory=dict)


class ValidationWarning(BaseModel):
    field_path: str
    message: str
    input_value: Any = None
    context: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    is_valid: bool = Field(..., description="Whether validation passed")
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[ValidationWarning] = Field(default_factory=list)
    sanitized_data: dict[str, Any] | None = Field(default=None, description="Cleaned/sanitized data if validation passed")
```

## Schema Validation

### Strict Mode Configuration

All schemas use strict validation:

```python
class BaseSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",  # Reject unknown fields
        str_strip_whitespace=True,  # Strip whitespace
        validate_assignment=True,  # Validate on assignment
        use_enum_values=True,  # Use enum values
    )
```

### Custom Validators

Schemas include custom validation logic:

```python
class TenKInsight(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")

    @field_validator("ticker")
    @classmethod
    def validate_ticker_format(cls, v: str) -> str:
        if not re.match(r"^[A-Z]{1,5}$", v):
            raise ValueError("Ticker must be 1-5 uppercase letters")
        return v.upper()

    @model_validator(mode="after")
    def validate_score_consistency(self) -> "TenKInsight":
        if self.composite_score > 0.95 and self.grade != "A+":
            raise ValueError("High composite score must have A+ grade")
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
    "data_sources": ["SEC EDGAR", "Yahoo Finance"],
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
        config=self.tasks_config["analysis_task"],
        output_pydantic=TenKInsight,  # Automatic validation
        output_json=True,
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
    if "version" not in data or data["version"] < "2.0":
        data = migrate_legacy_format(data)

    return TenKInsight.model_validate(data)
```

## Related Documentation

- **[Crews Reference](crews.md)** - How crews use schemas
- **[Tools Reference](tools.md)** - Tool input/output schemas
- **[API Reference](index.md)** - Complete API documentation

---

**Version**: 2.0
**Last Updated**: 2025-10-26
