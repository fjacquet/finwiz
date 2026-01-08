# Design Document: Add Enum Instructions to Task Configurations

## Overview

This design document outlines the approach for adding comprehensive enum value instructions to all CrewAI task configuration files in FinWiz. The solution will ensure consistency across all crews (ETF, portfolio rebalancing, and investment discovery) by following the established patterns from the stock and crypto crews.

## Architecture

### Current State

The FinWiz codebase currently has:
- **Stock crew** (`src/finwiz/crews/stock_crew/config/tasks.yaml`) - Has comprehensive enum instructions
- **Crypto crew** (`src/finwiz/crews/crypto_crew/config/tasks.yaml`) - Has comprehensive enum instructions
- **ETF crew** (`src/finwiz/crews/etf_crew/config/tasks.yaml`) - Missing enum instructions
- **Portfolio rebalancing crew** (`src/finwiz/crews/portfolio_rebalancing_crew/config/tasks.yaml`) - Missing enum instructions
- **Investment discovery crew** (`src/finwiz/crews/investment_discovery_crew/config/tasks.yaml`) - Missing enum instructions

### Target State

All task configuration files will have:
1. Schema file references at the beginning of task descriptions
2. Dedicated "REQUIRED ENUM VALUES" sections documenting all enum fields
3. Consistent formatting and emphatic language
4. Clear case sensitivity requirements (uppercase, lowercase, capitalized)
5. Examples of incorrect values to avoid

## Components and Interfaces

### Component 1: Enum Instruction Template

A standardized template for documenting enum values in task descriptions:

```yaml
description: >
  FIRST: Read the schema files [schema_path] and [example_path] to understand the exact output format required.
  
  [Main task description content...]
  
  CRITICAL OUTPUT FORMAT:
  - Return ONLY the [SchemaName] object directly - do NOT wrap it in additional fields
  - Do NOT add wrapper fields like "data", "results", etc.
  - The JSON must match the [SchemaName] schema exactly
  
  REQUIRED ENUM VALUES (use EXACTLY these values):
  - field_name: MUST be one of: "value1", "value2", "value3" (case requirement)
  - nested.field_name: MUST be one of: "VALUE1", "VALUE2" (uppercase)
  
  OUTPUT: Return a structured JSON output conforming to the [SchemaName] schema.
```

### Component 2: Schema-to-Enum Mapping

For each crew, we need to identify all enum fields from the Pydantic schemas:

#### ETF Crew Enums

**ETFMarketTrend schema:**
- `market_sentiment`: "bullish", "bearish", "neutral", "mixed" (lowercase)

**ETFFactsheet schema:**
- `replication_method`: "physical", "synthetic", "optimized", "other" (lowercase)

**RiskAssessmentStandardized schema:**
- `scale`: "0_5", "L_M_H", "L_M_H_VH" (use "0_5")
- `level`: "Low", "Medium", "High", "Very High" (capitalized)

#### Portfolio Rebalancing Crew Enums

**HoldingDecision schema:**
- `decision`: "KEEP", "SELL" (uppercase)
- `asset_class`: "stock", "etf", "crypto" (lowercase)
- `grade`: "A+", "A", "B+", "B", "C+", "C", "D", "F" (exact format)
- `data_freshness`: "fresh", "recent", "stale" (lowercase)

**Alternative schema:**
- `swap_timing`: "immediate", "gradual", "tax_optimized" (lowercase with underscore)

**PositionSizing schema:**
- `sizing_action`: "add", "trim", "hold", "exit" (lowercase)

**RiskAssessmentStandardized schema:**
- `scale`: "0_5", "L_M_H", "L_M_H_VH" (use "0_5")
- `level`: "Low", "Medium", "High", "Very High" (capitalized)

#### Investment Discovery Crew Enums

**APlusDiscoveryResult schema:**
- `asset_type`: "etf", "stock", "crypto" (lowercase)

**APlusCandidate schema:**
- `asset_type`: "etf", "stock", "crypto" (lowercase)
- `grade`: "A+", "A", "B+", "B", "C+", "C", "D", "F" (exact format)

**MarketRegime schema:**
- `regime_type`: "bull", "bear", "sideways", "volatile" (lowercase)
- `interest_rate_trend`: "rising", "falling", "stable" (lowercase)
- `market_stress_level`: "low", "medium", "high" (lowercase)

**PortfolioImprovement schema:**
- `improvement_type`: "replacement", "addition", "rebalancing" (lowercase)
- `implementation_priority`: "high", "medium", "low" (lowercase)

**RiskAssessmentStandardized schema:**
- `scale`: "0_5", "L_M_H", "L_M_H_VH" (use "0_5")
- `level`: "Low", "Medium", "High", "Very High" (capitalized)

### Component 3: Schema Reference Patterns

Based on existing patterns in stock and crypto crews:

```yaml
description: >
  FIRST: Read the schema files docs/schemas/[SchemaName].schema.json and 
  docs/schemas/examples/[schema_name].example.json to understand the exact output format required.
```

This should be added to tasks that have corresponding schema documentation files.

## Data Models

### Enum Instruction Block Structure

```yaml
REQUIRED ENUM VALUES (use EXACTLY these values):
- field_name: MUST be one of: "value1", "value2", "value3" (lowercase)
- field_name: MUST be one of: "VALUE1", "VALUE2" (uppercase, no other values allowed)
- nested.field_name: MUST be one of: "Value1", "Value2" (capitalized)
```

### Schema Reference Block Structure

```yaml
CRITICAL SCHEMA REQUIREMENTS:
- Read docs/schemas/[SchemaName].schema.json and docs/schemas/examples/[schema_name].example.json
- Follow the exact schema structure shown in the example files
- Ensure all required fields are included with correct data types
- Return the object directly without wrapper fields
```

## Error Handling

### Validation Error Prevention

The enum instructions will prevent common validation errors by:

1. **Explicit Value Lists**: Documenting exact values that must be used
2. **Case Sensitivity**: Clearly stating case requirements (uppercase, lowercase, capitalized)
3. **Negative Examples**: Showing what NOT to use (e.g., "NOT 'Bullish', 'Bearish'")
4. **Emphatic Language**: Using "MUST be", "EXACTLY these values", "no other values allowed"
5. **Field Path Notation**: Using dot notation for nested fields (e.g., `risk_assessment.level`)

### Graceful Degradation

If agents still generate incorrect enum values despite instructions:
- Pydantic validation will catch the error
- ValidationManager will handle based on strictness mode (off/warn/error)
- Error messages will reference the task configuration for correction

## Testing Strategy

### Manual Verification

1. **Schema Completeness Check**: Verify all Literal fields from schemas are documented
2. **Format Consistency Check**: Ensure all enum instructions follow the same format
3. **Case Sensitivity Check**: Verify case requirements match schema definitions
4. **Reference Accuracy Check**: Ensure schema file paths are correct

### Integration Testing

1. **Agent Output Validation**: Run crews and verify outputs pass Pydantic validation
2. **Error Message Quality**: Verify validation errors reference correct enum values
3. **Cross-Crew Consistency**: Ensure common enums (like RiskAssessmentStandardized) are documented consistently

### Regression Testing

1. **Existing Functionality**: Verify stock and crypto crews still work correctly
2. **Validation Manager**: Ensure ValidationManager handles enum errors appropriately
3. **Schema Registry**: Verify schema registration still works correctly

## Implementation Approach

### Phase 1: ETF Crew Enhancement

1. Add schema references to `etf_market_trends_task`
2. Add enum instructions for `market_sentiment` to `etf_market_trends_task`
3. Add enum instructions for `replication_method` to `etf_technical_detail_task`
4. Add enum instructions for risk assessment enums to `etf_risk_assessment_task`
5. Add schema references where applicable

### Phase 2: Portfolio Rebalancing Crew Enhancement

1. Add enum instructions for `decision`, `asset_class`, `grade`, `data_freshness` to `analyze_holding_task`
2. Add enum instructions for `swap_timing` to `find_alternatives_task`
3. Add enum instructions for `sizing_action` to `portfolio_analysis_task`
4. Add enum instructions for risk assessment enums to `rebalancing_optimization_task`
5. Add schema references where applicable

### Phase 3: Investment Discovery Crew Enhancement

1. Add enum instructions for `asset_type` and `grade` to `etf_discovery_task`
2. Add enum instructions for market regime enums to `stock_discovery_task`
3. Add enum instructions for `improvement_type` and `implementation_priority` to `crypto_discovery_task`
4. Add enum instructions for risk assessment enums to `optimization_task`
5. Add schema references where applicable

### Phase 4: Validation and Documentation

1. Verify all enum fields are documented
2. Check format consistency across all files
3. Update any related documentation
4. Run integration tests to verify agent outputs

## Design Decisions and Rationales

### Decision 1: Follow Existing Patterns

**Rationale**: The stock and crypto crews already have well-established enum instruction patterns. Following these patterns ensures consistency and leverages proven approaches.

### Decision 2: Emphatic Language

**Rationale**: Using strong language like "MUST be", "EXACTLY these values", and "no other values allowed" helps ensure agents pay attention to enum requirements and don't generate invalid values.

### Decision 3: Dedicated Sections

**Rationale**: Placing enum instructions in a dedicated "REQUIRED ENUM VALUES" section makes them highly visible and easy to find, reducing the chance agents will miss them.

### Decision 4: Case Sensitivity Notation

**Rationale**: Explicitly stating case requirements (uppercase, lowercase, capitalized) prevents common errors where agents use the wrong case for enum values.

### Decision 5: Schema References

**Rationale**: Referencing schema files at the beginning of task descriptions helps agents understand the complete output structure and reduces validation errors.

### Decision 6: Field Path Notation

**Rationale**: Using dot notation for nested fields (e.g., `risk_assessment.level`) makes it clear which field in the schema hierarchy the enum applies to.

---

**Version**: 1.0  
**Created**: 2025-05-10  
**Status**: Draft
