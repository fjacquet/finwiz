---
title: ""
description: "Complete reference documentation for "
category: "reference"
tags:
  - "reference"
date: "2025-10-26"
source: "schemas/README.md"
---

# FinWiz Schema Documentation

## Overview

FinWiz uses strict Pydantic v2 schemas to ensure type-safe data flow between crew tasks. All intermediate task outputs are validated against these schemas, providing:

- **Type Safety**: Automatic validation of data types and constraints
- **Data Quality**: Guaranteed presence of required fields
- **Error Detection**: Clear field-level error messages when validation fails
- **Documentation**: Self-documenting data structures with field descriptions
- **Consistency**: Standardized data formats across all crews

## Schema Organization

Schemas are organized by domain in `src/finwiz/schemas/`:

```text
src/finwiz/schemas/
├── common.py                    # Shared base models and enums
├── stock.py                     # Stock crew schemas
├── etf.py                       # ETF crew schemas
├── crypto.py                    # Crypto crew schemas
├── investment_discovery.py      # Investment discovery crew schemas
├── portfolio_rebalancing.py     # Portfolio rebalancing crew schemas
├── portfolio_review.py          # Portfolio review schemas
├── report.py                    # Report crew schemas
├── quantitative.py              # Quantitative analysis schemas
├── perplexity.py               # Perplexity API integration schemas
├── session.py                   # Session management schemas
├── validation.py                # Validation schemas
├── feedback.py                  # Feedback system schemas
├── export.py                    # Export format schemas
├── migration.py                 # Migration schemas
├── integration_models.py        # Integration schemas
├── validate.py                  # Validation utilities
├── api/                         # FastAPI request/response models
├── integration/                 # System integration schemas
├── quantitative/                # Quantitative analysis sub-schemas
├── rebalancing/                 # Rebalancing sub-schemas
└── tools/                       # Tool input validation schemas
```text
## Core Schemas

### Common Schemas

#### RiskAssessmentStandardized

Standardized risk assessment used across all asset classes (stocks, ETFs, crypto).

**Fields:**
- `scale` (str): Risk scale type, default "0_5" (0=lowest, 5=highest)
- `score` (float): Risk score from 0.0 to 5.0
- `level` (str): Human-friendly risk level ("Low", "Medium", "High", "Very High")
- `risk_factors` (list[str]): Up to 10 specific risk factors

**Example:**
```json
{
  "scale": "0_5",
  "score": 3.5,
  "level": "High",
  "risk_factors": [
    "High volatility in recent months",
    "Regulatory uncertainty in sector",
    "Concentration risk in top holdings"
  ]
}
```text
**Usage:**
```pythonthon
from finwiz.schemas.common import RiskAssessmentStandardized

risk = RiskAssessmentStandardized(
    score=3.5,
    level="High",
    risk_factors=["High volatility", "Regulatory uncertainty"]
)
```text
### Stock Crew Schemas

#### TenKInsight

Extracted insights from SEC 10-K filings with provenance tracking.

**Fields:**
- `schema_version` (int): Schema version for compatibility
- `ticker` (str): Stock ticker symbol (1-10 characters)
- `filing_url` (str): URL to SEC filing (validated)
- `filed_at` (datetime): Filing timestamp with timezone
- `section` (str): SEC filing section ("Item 1", "Item 1A", "Item 7", "Item 7A", "Item 8")
- `excerpt` (str): Extracted text excerpt (minimum 20 characters)
- `sec_citation` (str): Citation format (e.g., "10-K (2024), Item 1A, p. 17")

**Example:**
```json
{
  "schema_version": 1,
  "ticker": "AAPL",
  "filing_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193",
  "filed_at": "2024-11-01T16:30:00Z",
  "section": "Item 1A",
  "excerpt": "The Company faces intense competition in all areas of its business...",
  "sec_citation": "10-K (2024), Item 1A, p. 17"
}
```text
#### MarketSentiment

Aggregated market sentiment analysis from news sources.

**Fields:**
- `schema_version` (int): Schema version
- `ticker` (str): Stock ticker symbol
- `mean_score` (float): Average sentiment score (-1.0 to 1.0)
- `counts` (dict): Count of positive, neutral, negative articles
- `top_pos` (list[SentimentItem]): Top positive sentiment articles
- `top_neg` (list[SentimentItem]): Top negative sentiment articles

**Example:**
```json
{
  "schema_version": 1,
  "ticker": "AAPL",
  "mean_score": 0.65,
  "counts": {
    "pos": 45,
    "neu": 20,
    "neg": 10
  },
  "top_pos": [
    {
      "headline": "Apple Reports Record Quarter",
      "url": "https://example.com/article1",
      "date": "2024-11-01T10:00:00Z",
      "score": 0.95
    }
  ],
  "top_neg": []
}
```text
#### MarketTrend

Market trend analysis for stock market overview.

**Fields:**
- `schema_version` (int): Schema version
- `analysis_date` (date): Date of analysis
- Additional fields for trend indicators

**Example:**
```json
{
  "schema_version": 1,
  "analysis_date": "2024-11-01"
}
```text
### ETF Crew Schemas

#### ETFFactsheet

Comprehensive ETF information and metrics.

**Fields:**
- `ticker` (str): ETF ticker symbol
- `name` (str): Full ETF name
- `expense_ratio` (float): Annual expense ratio
- `aum` (float): Assets under management
- `inception_date` (date): ETF inception date
- Additional fields for holdings, performance, etc.

**Example:**
```json
{
  "ticker": "SPY",
  "name": "SPDR S&P 500 ETF Trust",
  "expense_ratio": 0.0945,
  "aum": 450000000000.0,
  "inception_date": "1993-01-22"
}
```text
#### ETFTopHolding

Individual ETF holding details.

**Fields:**
- `ticker` (str): Holding ticker symbol
- `name` (str): Company/asset name
- `weight` (float): Portfolio weight percentage
- `shares` (int): Number of shares held
- `market_value` (float): Market value of holding

**Example:**
```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "weight": 7.2,
  "shares": 165000000,
  "market_value": 28500000000.0
}
```text
### Crypto Crew Schemas

#### CryptoThesis

Investment thesis for cryptocurrency analysis.

**Fields:**
- `ticker` (str): Crypto ticker symbol
- `name` (str): Cryptocurrency name
- `thesis` (str): Investment thesis narrative
- `strengths` (list[str]): Key strengths
- `weaknesses` (list[str]): Key weaknesses
- `opportunities` (list[str]): Market opportunities
- `threats` (list[str]): Market threats

**Example:**
```json
{
  "ticker": "BTC",
  "name": "Bitcoin",
  "thesis": "Bitcoin remains the dominant store of value cryptocurrency...",
  "strengths": ["Network effect", "Brand recognition", "Liquidity"],
  "weaknesses": ["Scalability limitations", "Energy consumption"],
  "opportunities": ["Institutional adoption", "ETF approvals"],
  "threats": ["Regulatory crackdown", "Competing cryptocurrencies"]
}
```text
### Investment Discovery Schemas

#### APlusDiscoveryResult

Results from A+ investment discovery process.

**Fields:**
- `candidates` (list[InvestmentCandidate]): Discovered investment candidates
- `discovery_date` (datetime): When discovery was performed
- `criteria_used` (dict): Criteria used for discovery
- `total_screened` (int): Total assets screened

**Example:**
```json
{
  "candidates": [
    {
      "ticker": "MSFT",
      "grade": "A+",
      "composite_score": 0.92,
      "rationale": "Strong fundamentals with consistent growth"
    }
  ],
  "discovery_date": "2024-11-01T10:00:00Z",
  "criteria_used": {"min_score": 0.85, "min_grade": "A"},
  "total_screened": 500
}
```text
### Portfolio Rebalancing Schemas

#### PortfolioAnalysis

Comprehensive portfolio analysis results.

**Fields:**
- `holdings` (list[Holding]): Current portfolio holdings
- `metrics` (PortfolioMetrics): Portfolio-level metrics
- `recommendations` (list[str]): Rebalancing recommendations
- `analysis_date` (datetime): Analysis timestamp

**Example:**
```json
{
  "holdings": [
    {
      "ticker": "AAPL",
      "shares": 100,
      "current_price": 175.50,
      "market_value": 17550.0,
      "weight": 0.35
    }
  ],
  "metrics": {
    "total_value": 50000.0,
    "diversification_score": 0.75,
    "risk_score": 3.2
  },
  "recommendations": ["Consider reducing AAPL position"],
  "analysis_date": "2024-11-01T10:00:00Z"
}
```text
#### HoldingDecision

Keep/sell decision for individual portfolio holding.

**Fields:**
- `ticker` (str): Holding ticker symbol
- `decision` (str): "KEEP" or "SELL"
- `rationale` (str): Detailed reasoning
- `confidence` (float): Decision confidence (0.0-1.0)
- `alternative_suggestions` (list[str]): Alternative tickers if selling

**Example:**
```json
{
  "ticker": "IBM",
  "decision": "SELL",
  "rationale": "Underperforming with grade D, better alternatives available",
  "confidence": 0.85,
  "alternative_suggestions": ["MSFT", "GOOGL"]
}
```text
#### Alternative

Alternative investment suggestion for portfolio improvement.

**Fields:**
- `ticker` (str): Alternative ticker symbol
- `name` (str): Asset name
- `grade` (str): Quality grade
- `composite_score` (float): Overall score
- `improvement_potential` (float): Expected improvement
- `rationale` (str): Why this alternative is better

**Example:**
```json
{
  "ticker": "MSFT",
  "name": "Microsoft Corporation",
  "grade": "A+",
  "composite_score": 0.92,
  "improvement_potential": 0.25,
  "rationale": "Superior fundamentals and growth trajectory compared to current holding"
}
```text
## Schema Validation

### Using Schemas in Code

```pythonthon
from finwiz.schemas.stock import TenKInsight
from finwiz.utils.json_error_handlers import validate_schema

# Parse and validate JSON data
data = {
    "schema_version": 1,
    "ticker": "AAPL",
    "filing_url": "https://www.sec.gov/...",
    "filed_at": "2024-11-01T16:30:00Z",
    "section": "Item 1A",
    "excerpt": "The Company faces intense competition...",
    "sec_citation": "10-K (2024), Item 1A, p. 17"
}

# Validate against schema
try:
    insight = validate_schema(data, TenKInsight)
    print(f"Validated insight for {insight.ticker}")
except SchemaValidationError as e:
    print(f"Validation failed: {e}")
```text
### Using Schemas in CrewAI Tasks

```yaml
# config/tasks.yaml
stock_analysis_task:
  description: "Analyze stock fundamentals from 10-K filing"
  expected_output: "Structured 10-K insights with SEC citations"
  output_pydantic: "TenKInsight"  # References schema class
  output_file: "ten_k_insight.json"
  agent: stock_analyst
```text
## Validation Rules

### Common Validation Patterns

1. **Required Fields**: All fields without default values must be provided
2. **Type Validation**: Values must match declared types
3. **Range Constraints**: Numeric fields respect `ge`, `le`, `gt`, `lt` constraints
4. **String Patterns**: String fields may require regex pattern matching
5. **List Constraints**: Lists may have `min_length`, `max_length` constraints
6. **Enum Values**: Literal types restrict to specific allowed values
7. **URL Validation**: URL fields are validated for proper format
8. **Date/Time Validation**: Datetime fields require timezone awareness

### Field Constraints

```pythonthon
from pydantic import Field

# Numeric constraints
score: float = Field(ge=0.0, le=5.0)  # 0.0 ≤ score ≤ 5.0

# String constraints
ticker: str = Field(min_length=1, max_length=10)

# Pattern matching
recommendation: str = Field(pattern="^(BUY|HOLD|SELL)$")

# List constraints
risk_factors: list[str] = Field(max_length=10)

# Optional fields
notes: str | None = Field(None, description="Optional notes")
```text
## Error Handling

### Common Validation Errors

#### Missing Required Field

```json
{
  "error": "field required",
  "field": "ticker",
  "type": "missing"
}
```text
**Solution**: Ensure all required fields are present in the data.

#### Type Mismatch

```json
{
  "error": "value is not a valid float",
  "field": "score",
  "type": "float_parsing",
  "input": "invalid"
}
```text
**Solution**: Ensure field values match the expected type.

#### Value Out of Range

```json
{
  "error": "ensure this value is less than or equal to 5.0",
  "field": "score",
  "type": "less_than_equal",
  "input": 6.5
}
```text
**Solution**: Ensure numeric values are within specified constraints.

#### Invalid Enum Value

```json
{
  "error": "value is not a valid enumeration member",
  "field": "section",
  "type": "enum",
  "input": "Item 9"
}
```text
**Solution**: Use only allowed enum values (e.g., "Item 1", "Item 1A", etc.).

#### Pattern Mismatch

```json
{
  "error": "string does not match regex",
  "field": "recommendation",
  "type": "string_pattern_mismatch",
  "pattern": "^(BUY|HOLD|SELL)$"
}
```text
**Solution**: Ensure string values match the required pattern.

## Best Practices

### Schema Design

1. **Use Descriptive Names**: Schema and field names should be self-explanatory
2. **Add Field Descriptions**: Use `Field(description=...)` for documentation
3. **Set Appropriate Constraints**: Use `ge`, `le`, `pattern`, etc. to enforce data quality
4. **Use Enums for Fixed Values**: Prefer `Literal` types over free-form strings
5. **Version Your Schemas**: Include `schema_version` field for compatibility
6. **Forbid Extra Fields**: Use `model_config = ConfigDict(extra='forbid')` for strict validation

### Data Quality

1. **Validate Early**: Validate data at crew task boundaries
2. **Provide Context**: Include metadata like timestamps, sources, citations
3. **Use Standardized Scales**: Use consistent scales (e.g., 0-5 for risk)
4. **Document Assumptions**: Include fields for confidence, data quality indicators
5. **Handle Missing Data**: Use optional fields with `None` default for incomplete data

### Error Handling

1. **Catch Validation Errors**: Use try/except blocks around schema validation
2. **Log Sanitized Errors**: Log field paths and error types, not sensitive data
3. **Provide Clear Messages**: Give actionable error messages to users
4. **Fail Fast**: Validate inputs before expensive operations
5. **Use Error Handlers**: Leverage `json_error_handlers.py` utilities

## Schema Registry

All schemas are registered in `src/finwiz/schemas/__init__.py` for easy import:

```pythonthon
from finwiz.schemas import (
    RiskAssessmentStandardized,
    TenKInsight,
    MarketSentiment,
    ETFFactsheet,
    CryptoThesis,
    APlusDiscoveryResult,
    PortfolioAnalysis,
    HoldingDecision,
)
```text
## Additional Resources

- **Design Document**: `.kiro/specs/json-first-crew-architecture/design.md`
- **Requirements**: `.kiro/specs/json-first-crew-architecture/requirements.md`
- **Migration Guide**: `docs/JSON_MIGRATION_GUIDE.md`
- **Error Handlers**: `src/finwiz/utils/json_error_handlers.py`
- **Validation Standards**: `.kiro/steering/validation.md`

## Version History

- **v1.0** (2024-11-01): Initial schema documentation
- Schemas use modern Python 3.12+ type annotations (`Type | None`, `list`, `dict`)
- All schemas enforce strict validation with `extra='forbid'`
- Standardized risk assessment across all asset classes

---

**Last Updated**: 2025-05-10
**Maintained By**: FinWiz Development Team
