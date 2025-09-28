# Schema Enhancements for A+ Investment Discovery

This document describes the enhancements made to the FinWiz portfolio review schemas to support A+ investment discovery features while maintaining backward compatibility.

## Overview

The schema enhancements add A+ investment discovery capabilities to the existing portfolio review system. These changes allow the system to:

1. Track A+ improvement suggestions for individual holdings
2. Provide portfolio-level A+ opportunity analysis
3. Maintain backward compatibility with existing v1 schemas
4. Support migration from v1 to v2 schemas

## Enhanced Schemas

### 1. APlusImprovementSuggestion

A new model that represents a specific A+ improvement suggestion for a holding.

```python
class APlusImprovementSuggestion(BaseModel):
    improvement_type: ImprovementType  # "replacement", "addition", "rebalancing"
    recommended_symbol: str
    recommended_name: str
    recommended_grade: Grade
    expected_grade_improvement: float
    grade_improvement_description: str
    allocation_percentage: float  # 0.0 to 100.0
    implementation_priority: Priority  # "high", "medium", "low"
    rationale: str
    expected_annual_benefit: float | None
    risk_impact_description: str
    cost_analysis: dict[str, float]
    implementation_notes: list[str]
```

### 2. APlusOpportunitySection

A new model that provides portfolio-level A+ opportunity analysis.

```python
class APlusOpportunitySection(BaseModel):
    total_opportunities_found: int = 0
    high_priority_opportunities: int = 0
    expected_portfolio_grade_improvement: float = 0.0
    grade_improvement_description: str = ""
    replacement_opportunities: int = 0
    addition_opportunities: int = 0
    rebalancing_opportunities: int = 0
    top_recommendations: list[str] = []  # Max 5 items
    implementation_timeline: str = ""
    total_expected_annual_benefit: float = 0.0
    last_discovery_date: datetime | None = None
    discovery_coverage: list[str] = []
    market_conditions_note: str = ""
```

### 3. Enhanced Alternative Model

The existing `Alternative` model has been enhanced with A+ discovery fields:

```python
class Alternative(BaseModel):
    # ... existing fields ...
    
    # New A+ enhancement fields
    is_a_plus_candidate: bool = False
    discovery_source: str | None = None
    confidence_level: float | None = None  # 0.0 to 1.0
    expected_annual_benefit: float | None = None
```

### 4. Enhanced HoldingDecision Model

The existing `HoldingDecision` model has been enhanced with A+ improvement suggestions:

```python
class HoldingDecision(BaseModel):
    # ... existing fields ...
    
    # New A+ improvement fields
    a_plus_improvement_suggestions: list[APlusImprovementSuggestion] = []  # Max 5 items
    has_a_plus_opportunities: bool = False
    current_grade_potential: str | None = None
```

### 5. Enhanced PortfolioReview Model

The existing `PortfolioReview` model has been enhanced with A+ opportunities:

```python
class PortfolioReview(BaseModel):
    # ... existing fields ...
    
    # New A+ opportunities integration
    a_plus_opportunities: APlusOpportunitySection = APlusOpportunitySection()
    current_a_plus_holdings_count: int = 0
    potential_a_plus_holdings_count: int = 0
    portfolio_grade_improvement_potential: float = 0.0
    
    # Migration and compatibility fields
    schema_version: str = "2.0"
    has_a_plus_analysis: bool = False
```

## Asset Class Support

The enhanced schemas now support crypto assets in addition to stocks and ETFs:

```python
AssetClass = Literal["stock", "etf", "crypto"]
```

This allows A+ discovery to work across all supported asset types.

## Migration System

### Automatic Migration

The migration system automatically detects v1 schemas and migrates them to v2:

```python
from finwiz.schemas.migration import migrate_portfolio_review_if_needed

# Automatically migrates v1 to v2 if needed
portfolio = migrate_portfolio_review_if_needed(raw_data)
```

### Manual Migration

You can also perform manual migration:

```python
from finwiz.schemas.migration import (
    migrate_portfolio_review_v1_to_v2,
    migrate_holding_decision_v1_to_v2
)

# Migrate portfolio review
v2_portfolio_data = migrate_portfolio_review_v1_to_v2(v1_data)

# Migrate individual holding
v2_holding_data = migrate_holding_decision_v1_to_v2(v1_holding_data)
```

### Backward Compatibility

Generate v1-compatible representations for legacy systems:

```python
from finwiz.schemas.migration import ensure_backward_compatibility

# Create v1-compatible representation
v1_compatible_data = ensure_backward_compatibility(v2_portfolio)
```

## Usage Examples

### Creating A+ Improvement Suggestions

```python
from finwiz.schemas.portfolio_review import APlusImprovementSuggestion

suggestion = APlusImprovementSuggestion(
    improvement_type="replacement",
    recommended_symbol="VTI",
    recommended_name="Vanguard Total Stock Market ETF",
    recommended_grade="A+",
    expected_grade_improvement=0.15,
    grade_improvement_description="Upgrade from B+ to A+ with lower fees",
    allocation_percentage=25.0,
    implementation_priority="high",
    rationale="Lower expense ratio (0.03% vs 0.75%) with broader diversification",
    risk_impact_description="Slightly reduced risk due to broader diversification",
    cost_analysis={"transaction_fee": 0.0, "bid_ask_spread": 0.01},
    implementation_notes=["Consider tax implications", "Execute during market hours"]
)
```

### Adding A+ Opportunities to Portfolio Review

```python
from finwiz.schemas.portfolio_review import APlusOpportunitySection
from finwiz.schemas.migration import add_a_plus_opportunities_to_existing_review

opportunities_data = {
    "total_opportunities_found": 3,
    "high_priority_opportunities": 1,
    "expected_portfolio_grade_improvement": 0.2,
    "grade_improvement_description": "Significant improvement from B+ to A-",
    "top_recommendations": ["VTI", "VXUS", "BND"]
}

updated_portfolio = add_a_plus_opportunities_to_existing_review(
    existing_portfolio, opportunities_data
)
```

### Working with Enhanced Holdings

```python
from finwiz.schemas.portfolio_review import HoldingDecision
from finwiz.schemas.common import RiskAssessmentStandardized

risk = RiskAssessmentStandardized(score=2.5, level="Medium")

holding = HoldingDecision(
    asset_class="etf",
    name="SPDR S&P 500 ETF",
    ticker="SPY",
    currency="USD",
    decision="KEEP",
    composite_score=0.75,
    grade="B+",
    grade_description="Good broad market exposure but higher fees",
    recommended_action="Consider alternatives",
    risk=risk,
    a_plus_improvement_suggestions=[suggestion],
    has_a_plus_opportunities=True,
    current_grade_potential="Could improve to A+ with lower-cost alternative"
)
```

## Schema Validation

All enhanced schemas use strict Pydantic validation:

- **Field limits**: Lists are limited to prevent excessive data (e.g., max 5 improvement suggestions)
- **Type safety**: All fields have proper type hints and validation
- **Range validation**: Numeric fields have appropriate ranges (e.g., allocation_percentage: 0.0-100.0)
- **Enum validation**: String fields use enums where appropriate

## JSON Schema Generation

Updated JSON schemas are automatically generated and stored in `docs/schemas/`:

- `HoldingDecision.schema.json`
- `PortfolioReview.schema.json`
- `Alternative.schema.json`
- `APlusImprovementSuggestion.schema.json` (new)
- `APlusOpportunitySection.schema.json` (new)

## Testing

Comprehensive tests cover:

- **Schema validation**: All field types, ranges, and constraints
- **Migration functionality**: v1 to v2 migration with various data scenarios
- **Backward compatibility**: v1-compatible representation generation
- **Error handling**: Invalid data and edge cases

Run tests with:

```bash
uv run pytest tests/unit/schemas/test_portfolio_review_enhancements.py -v
uv run pytest tests/unit/schemas/test_schema_migration.py -v
```

## Integration with Investment Discovery

The enhanced schemas integrate seamlessly with the investment discovery crew:

1. **Discovery Results**: A+ candidates from discovery are stored in `APlusOpportunitySection`
2. **Improvement Suggestions**: Specific recommendations are stored in `APlusImprovementSuggestion`
3. **Portfolio Impact**: Overall portfolio improvement potential is tracked
4. **Implementation Guidance**: Priority and timeline information guides execution

## Best Practices

1. **Always use migration utilities** when working with existing data
2. **Check schema version** before processing portfolio data
3. **Validate A+ opportunities** before adding to portfolio reviews
4. **Maintain backward compatibility** when integrating with existing systems
5. **Use appropriate field limits** to prevent performance issues

## Future Considerations

The enhanced schema design allows for future extensions:

- Additional asset classes (bonds, commodities, etc.)
- More sophisticated improvement types
- Enhanced risk impact modeling
- Integration with external portfolio management systems

The migration system ensures that future schema changes can be handled gracefully while maintaining backward compatibility.