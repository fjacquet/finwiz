# Requirements Document: Add Enum Instructions to Task Configurations

## Introduction

This specification addresses the need to add comprehensive enum value instructions to all CrewAI task configuration files in FinWiz. Currently, only the stock and crypto crew task files have explicit enum instructions, while ETF, portfolio rebalancing, and investment discovery crews lack these critical guidelines. This inconsistency can lead to validation errors when agents generate outputs with incorrect enum values.

The goal is to ensure all task configurations explicitly document the exact enum values that must be used in their Pydantic schema outputs, preventing validation failures and improving agent output quality.

## Requirements

### Requirement 1: ETF Crew Enum Instructions

**User Story:** As a FinWiz developer, I want the ETF crew task configuration to include explicit enum instructions, so that agents generate outputs with correct enum values that pass Pydantic validation.

#### Acceptance Criteria

1. WHEN the ETF market trends task is executed THEN the task description SHALL include enum instructions for `market_sentiment` field
2. WHEN the ETF screening task is executed THEN the task description SHALL include enum instructions for any applicable enum fields in ETFScreeningResult schema
3. WHEN the ETF technical detail task is executed THEN the task description SHALL include enum instructions for `replication_method` and any other enum fields in ETFTechnicalAnalysis schema
4. WHEN the ETF risk assessment task is executed THEN the task description SHALL include enum instructions for risk level enums in RiskAssessmentStandardized schema
5. WHEN the ETF investment strategy task is executed THEN the task description SHALL include enum instructions for recommendation and time horizon enums

### Requirement 2: Portfolio Rebalancing Crew Enum Instructions

**User Story:** As a FinWiz developer, I want the portfolio rebalancing crew task configuration to include explicit enum instructions, so that agents generate portfolio decisions with correct enum values.

#### Acceptance Criteria

1. WHEN the analyze holding task is executed THEN the task description SHALL include enum instructions for `decision` field ("KEEP", "SELL")
2. WHEN the analyze holding task is executed THEN the task description SHALL include enum instructions for `asset_class` field ("stock", "etf", "crypto")
3. WHEN the analyze holding task is executed THEN the task description SHALL include enum instructions for `grade` field ("A+", "A", "B+", "B", "C+", "C", "D", "F")
4. WHEN the analyze holding task is executed THEN the task description SHALL include enum instructions for `data_freshness` field ("fresh", "recent", "stale")
5. WHEN the find alternatives task is executed THEN the task description SHALL include enum instructions for `swap_timing` field ("immediate", "gradual", "tax_optimized")
6. WHEN the portfolio analysis task is executed THEN the task description SHALL include enum instructions for `sizing_action` field ("add", "trim", "hold", "exit")
7. WHEN the rebalancing optimization task is executed THEN the task description SHALL include enum instructions for risk assessment scale and level enums

### Requirement 3: Investment Discovery Crew Enum Instructions

**User Story:** As a FinWiz developer, I want the investment discovery crew task configuration to include explicit enum instructions, so that agents generate A+ discovery results with correct enum values.

#### Acceptance Criteria

1. WHEN the ETF discovery task is executed THEN the task description SHALL include enum instructions for `asset_type` field ("etf", "stock", "crypto")
2. WHEN the ETF discovery task is executed THEN the task description SHALL include enum instructions for `grade` field ("A+", "A", "B+", "B", "C+", "C", "D", "F")
3. WHEN the stock discovery task is executed THEN the task description SHALL include enum instructions for market regime enums ("bull", "bear", "sideways", "volatile")
4. WHEN the stock discovery task is executed THEN the task description SHALL include enum instructions for interest rate trend enums ("rising", "falling", "stable")
5. WHEN the stock discovery task is executed THEN the task description SHALL include enum instructions for market stress level enums ("low", "medium", "high")
6. WHEN the crypto discovery task is executed THEN the task description SHALL include enum instructions for `improvement_type` field ("replacement", "addition", "rebalancing")
7. WHEN the crypto discovery task is executed THEN the task description SHALL include enum instructions for `implementation_priority` field ("high", "medium", "low")
8. WHEN the optimization task is executed THEN the task description SHALL include enum instructions for risk assessment enums

### Requirement 4: Consistent Enum Instruction Format

**User Story:** As a FinWiz developer, I want all enum instructions to follow a consistent format across all task files, so that the documentation is clear and maintainable.

#### Acceptance Criteria

1. WHEN enum instructions are added to any task THEN they SHALL be placed in a dedicated "REQUIRED ENUM VALUES" section
2. WHEN enum instructions are documented THEN they SHALL use the format: "field_name: MUST be one of: value1, value2, value3"
3. WHEN enum values are case-sensitive THEN the instruction SHALL explicitly state the case requirement (e.g., "uppercase", "lowercase", "capitalized")
4. WHEN enum instructions are added THEN they SHALL be placed after the main task description and before the OUTPUT section
5. WHEN multiple enum fields exist THEN each SHALL be documented on a separate line with clear field path notation

### Requirement 5: Schema Reference Documentation

**User Story:** As a FinWiz developer, I want task configurations to reference the relevant schema files, so that agents can understand the complete output structure.

#### Acceptance Criteria

1. WHEN a task uses a Pydantic output schema THEN the task description SHALL reference the schema file location (e.g., "docs/schemas/ETFMarketTrend.schema.json")
2. WHEN example files exist for a schema THEN the task description SHALL reference the example file location (e.g., "docs/schemas/examples/etf_market_trend.example.json")
3. WHEN schema references are added THEN they SHALL be placed at the beginning of the task description
4. WHEN schema references are added THEN they SHALL use the format: "FIRST: Read the schema files [path] to understand the exact output format required"
5. WHEN schema references are added THEN they SHALL be consistent with existing patterns in stock and crypto crew task files

### Requirement 6: Validation Error Prevention

**User Story:** As a FinWiz developer, I want enum instructions to prevent common validation errors, so that agent outputs pass Pydantic validation on the first attempt.

#### Acceptance Criteria

1. WHEN enum instructions are added THEN they SHALL cover all Literal type fields in the output schema
2. WHEN enum instructions are added THEN they SHALL explicitly state that no other values are allowed
3. WHEN enum instructions are added THEN they SHALL include examples of incorrect values to avoid (e.g., "NOT 'Bullish', 'Bearish', etc.")
4. WHEN enum instructions are added THEN they SHALL be placed prominently in the task description to ensure agent visibility
5. WHEN enum instructions are added THEN they SHALL use emphatic language (e.g., "MUST be", "EXACTLY these values", "no other values allowed")

---

**Version**: 1.0  
**Created**: 2025-05-10  
**Status**: Draft
