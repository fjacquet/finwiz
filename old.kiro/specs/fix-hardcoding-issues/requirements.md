# Requirements Document: Fix Hardcoding Issues

## Introduction

FinWiz currently suffers from pervasive hardcoding issues that compromise data integrity and analysis accuracy. Default values are used throughout the codebase when real data should be calculated, leading to grade inflation, identical risk profiles across different assets, and loss of user trust. This spec addresses the systematic removal of hardcoded defaults and implementation of proper data quality tracking.

## Glossary

- **System**: FinWiz financial analysis platform
- **Deep Analysis Scorer**: Python-based scoring engine that calculates composite scores and grades
- **Quantitative Analysis Tool**: Tool that calculates risk metrics (volatility, max drawdown, beta)
- **Alternative Finder**: Tool that recommends alternative investments for underperforming holdings
- **Data Quality Metrics**: Tracking system for calculated vs defaulted vs missing data fields
- **Grade Inflation**: Phenomenon where most assets receive A/A+ grades due to optimistic defaults
- **Composite Score**: Weighted score (0.0-1.0) combining fundamental, technical, and risk analysis
- **Risk Metrics**: Volatility, maximum drawdown, beta, and other risk measurements
- **Crew Output**: Structured data returned by CrewAI crews after analysis

## Requirements

### Requirement 1: Eliminate Risk Metrics Hardcoding

**User Story:** As a portfolio manager, I want each asset to display its actual calculated risk metrics, so that I can accurately assess and compare risk profiles across different investments.

#### Acceptance Criteria

1. WHEN the System calculates risk metrics for an asset, THE System SHALL use actual calculated values from historical price data
2. WHEN volatility data is unavailable, THE System SHALL log a warning and mark the field as "missing" rather than using a default value
3. WHEN max drawdown data is unavailable, THE System SHALL log a warning and mark the field as "missing" rather than using a default value
4. WHEN the Quantitative Analysis Tool returns risk metrics, THE System SHALL properly extract and pass volatility, max_drawdown, and beta to the Deep Analysis Scorer
5. WHEN displaying risk metrics in reports, THE System SHALL show actual calculated values with data quality indicators

### Requirement 2: Eliminate Grade Hardcoding

**User Story:** As an investor, I want to see realistic grade distributions across my portfolio and discovery recommendations, so that I can identify truly exceptional (A+) investments versus average (C) or poor (D/F) ones.

#### Acceptance Criteria

1. WHEN the Alternative Finder recommends alternatives, THE System SHALL calculate grades from composite scores rather than defaulting to "A+"
2. WHEN the Portfolio Review displays alternatives, THE System SHALL use calculated grades rather than defaulting to "A+"
3. WHEN the Template Renderer processes discovery data, THE System SHALL require explicit grades rather than defaulting to "A+"
4. WHEN the Investment Discovery Schema creates candidates, THE System SHALL validate that grades are explicitly calculated
5. WHEN the Feedback Tools record recommendations, THE System SHALL use actual recommendation grades rather than assuming "A+"

### Requirement 3: Eliminate Composite Score Hardcoding

**User Story:** As a financial analyst, I want composite scores to reflect actual analysis results, so that investment recommendations are based on real data rather than optimistic defaults.

#### Acceptance Criteria

1. WHEN the Flow Orchestrator processes crew results, THE System SHALL extract actual composite scores rather than defaulting to 0.7
2. WHEN the Alternative Finder evaluates alternatives, THE System SHALL use calculated composite scores rather than defaulting to 0.85
3. WHEN the A+ Extractor processes discovery candidates, THE System SHALL require explicit composite scores for stocks, ETFs, and crypto
4. WHEN composite scores are missing, THE System SHALL raise an error or mark the analysis as incomplete
5. WHEN displaying composite scores, THE System SHALL verify they match the calculated grade according to the grading scale

### Requirement 4: Implement Data Quality Tracking

**User Story:** As a system administrator, I want to track which data fields are calculated versus defaulted versus missing, so that I can monitor data quality and identify issues early.

#### Acceptance Criteria

1. WHEN the System calculates analysis results, THE System SHALL track which fields were calculated from real data
2. WHEN the System uses default values, THE System SHALL log warnings and record the field as "defaulted"
3. WHEN data is completely missing, THE System SHALL record the field as "missing" and include it in quality metrics
4. WHEN analysis completes, THE System SHALL calculate a data completeness score (0.0-1.0) based on calculated vs defaulted vs missing fields
5. WHEN data quality is low (completeness < 0.7), THE System SHALL mark the analysis with a quality warning

### Requirement 5: Add Data Quality Indicators to Reports

**User Story:** As an investor, I want to see data quality indicators in analysis reports, so that I can assess the reliability of recommendations before making investment decisions.

#### Acceptance Criteria

1. WHEN the System generates HTML reports, THE System SHALL display data quality level (high/medium/low) prominently
2. WHEN data quality is "low", THE System SHALL show a warning message: "⚠️ Limited data available - results may be less reliable"
3. WHEN data quality is "medium", THE System SHALL show an info message: "ℹ️ Some data estimated - verify before investing"
4. WHEN data quality is "high", THE System SHALL show a success message: "✅ High quality data - comprehensive analysis"
5. WHEN users hover over quality indicators, THE System SHALL display which specific fields were calculated vs defaulted vs missing

### Requirement 6: Standardize Default Handling

**User Story:** As a developer, I want consistent default handling across the codebase, so that behavior is predictable and maintainable.

#### Acceptance Criteria

1. WHEN the System encounters missing data, THE System SHALL follow a standardized default handling policy
2. WHEN critical fields are missing (grade, composite_score, volatility), THE System SHALL raise ValueError rather than using defaults
3. WHEN optional fields are missing, THE System SHALL use None rather than optimistic defaults
4. WHEN defaults must be used, THE System SHALL use consistent values across all modules
5. WHEN the System uses a default value, THE System SHALL log the event at WARNING level with context

### Requirement 7: Implement Fail-Loud Error Handling

**User Story:** As a system operator, I want the system to fail loudly when critical data is missing, so that I can identify and fix data collection issues rather than silently producing incorrect results.

#### Acceptance Criteria

1. WHEN grade data is missing from crew output, THE System SHALL raise ValueError with message "Missing grade for {ticker}"
2. WHEN composite score is missing from crew output, THE System SHALL raise ValueError with message "Missing composite_score for {ticker}"
3. WHEN risk metrics are missing from quantitative analysis, THE System SHALL raise ValueError with message "Missing risk metrics for {ticker}"
4. WHEN the System raises data validation errors, THE System SHALL include the ticker symbol and missing field names in the error message
5. WHEN validation errors occur, THE System SHALL log the full context (ticker, asset_class, attempted operation) for debugging

### Requirement 8: Validate Score-to-Grade Mapping

**User Story:** As a quality assurance engineer, I want to ensure that grades always match their corresponding composite scores, so that users see consistent and accurate information.

#### Acceptance Criteria

1. WHEN the System assigns a grade, THE System SHALL verify it matches the composite score according to the grading scale
2. WHEN composite_score >= 0.95, THE System SHALL assign grade "A+"
3. WHEN 0.85 <= composite_score < 0.95, THE System SHALL assign grade "A"
4. WHEN 0.75 <= composite_score < 0.85, THE System SHALL assign grade "B+"
5. WHEN grade and composite_score are inconsistent, THE System SHALL raise ValidationError with details

### Requirement 9: Track Grade Distribution Metrics

**User Story:** As a product manager, I want to monitor grade distribution across analyses, so that I can detect grade inflation and ensure realistic distributions.

#### Acceptance Criteria

1. WHEN the System completes portfolio analysis, THE System SHALL record the distribution of grades (A+, A, B, C, D, F)
2. WHEN grade distribution is unrealistic (>50% A+), THE System SHALL log a warning about potential grade inflation
3. WHEN the System generates discovery recommendations, THE System SHALL track the percentage of A+ candidates
4. WHEN monitoring grade distributions, THE System SHALL compare against expected realistic distributions
5. WHEN grade inflation is detected, THE System SHALL alert administrators via logging

### Requirement 10: Implement Data Quality Schema

**User Story:** As a developer, I want a standardized schema for tracking data quality, so that all components consistently report quality metrics.

#### Acceptance Criteria

1. WHEN the System creates analysis results, THE System SHALL include a DataQualityMetrics object
2. WHEN DataQualityMetrics is created, THE System SHALL populate fields_calculated list with all calculated field names
3. WHEN DataQualityMetrics is created, THE System SHALL populate fields_defaulted list with all defaulted field names
4. WHEN DataQualityMetrics is created, THE System SHALL populate fields_missing list with all missing field names
5. WHEN DataQualityMetrics is created, THE System SHALL calculate completeness_score as (calculated / total_fields)

### Requirement 11: Add Comprehensive Logging

**User Story:** As a system administrator, I want detailed logging of data quality issues, so that I can diagnose and fix problems quickly.

#### Acceptance Criteria

1. WHEN the System uses a default value, THE System SHALL log at WARNING level: "Using default {field}={value} for {ticker}"
2. WHEN the System encounters missing data, THE System SHALL log at ERROR level: "Missing required field {field} for {ticker}"
3. WHEN data quality is low, THE System SHALL log at WARNING level: "Low data quality ({score:.1%}) for {ticker}"
4. WHEN the System successfully calculates all fields, THE System SHALL log at INFO level: "High quality analysis for {ticker} ({score:.1%} complete)"
5. WHEN logging data quality events, THE System SHALL include ticker, asset_class, field names, and quality score

### Requirement 12: Implement Gradual Rollout

**User Story:** As a release manager, I want to roll out hardcoding fixes gradually, so that we can validate each change without breaking production.

#### Acceptance Criteria

1. WHEN deploying Phase 1 (risk metrics), THE System SHALL maintain backward compatibility with existing reports
2. WHEN deploying Phase 2 (grades), THE System SHALL add warnings before enforcing strict validation
3. WHEN deploying Phase 3 (UI indicators), THE System SHALL make quality indicators optional via feature flag
4. WHEN a phase fails validation, THE System SHALL allow rollback to previous behavior via configuration
5. WHEN all phases are deployed, THE System SHALL remove backward compatibility code and feature flags

### Requirement 13: Validate Against Real Data

**User Story:** As a QA engineer, I want to validate fixes against real market data, so that I can ensure the system produces accurate results for actual investments.

#### Acceptance Criteria

1. WHEN testing risk metrics fixes, THE System SHALL analyze 10 different stocks and verify unique volatility values
2. WHEN testing grade fixes, THE System SHALL analyze 20 different assets and verify realistic grade distribution
3. WHEN testing composite scores, THE System SHALL verify scores match calculated grades for 50 test cases
4. WHEN testing data quality tracking, THE System SHALL verify quality metrics are accurate for 100 analyses
5. WHEN validation tests pass, THE System SHALL produce a test report showing grade distribution and risk metric variance

### Requirement 14: Implement Complete Data Lineage Tracking

**User Story:** As a data scientist, I want complete data lineage for every calculation, so that I can trace where values came from, what transformations were applied, and reproduce results for validation and debugging.

#### Acceptance Criteria

1. WHEN the System calculates any metric, THE System SHALL record the data source (API, cache, calculation) with timestamp
2. WHEN the System applies transformations, THE System SHALL record the transformation type, input values, and output values
3. WHEN the System uses calculated values in scoring, THE System SHALL record which raw metrics contributed to each score component
4. WHEN the System generates final grades, THE System SHALL record the complete calculation chain from raw data to final grade
5. WHEN data scientists request lineage, THE System SHALL provide a complete audit trail showing: data sources → transformations → calculations → scores → grades

### Requirement 15: Provide Lineage Query Interface

**User Story:** As a data scientist, I want to query data lineage for specific tickers and metrics, so that I can understand and validate calculation logic without reading code.

#### Acceptance Criteria

1. WHEN querying lineage for a ticker, THE System SHALL return all data sources used in the analysis
2. WHEN querying lineage for a specific metric (e.g., volatility), THE System SHALL show: raw data points → calculation method → final value
3. WHEN querying lineage for composite scores, THE System SHALL show: component scores → weights → calculation → final score
4. WHEN querying lineage for grades, THE System SHALL show: composite score → grading scale → assigned grade
5. WHEN lineage data is incomplete, THE System SHALL clearly indicate which steps are missing or estimated

### Requirement 16: Export Lineage for Reproducibility

**User Story:** As a data scientist, I want to export complete lineage data, so that I can reproduce calculations independently and validate results in external tools (Python notebooks, R, Excel).

#### Acceptance Criteria

1. WHEN exporting lineage, THE System SHALL provide data in JSON format with all calculation steps
2. WHEN exporting lineage, THE System SHALL include raw input data, transformation formulas, and intermediate results
3. WHEN exporting lineage, THE System SHALL include timestamps for all data sources (to verify data freshness)
4. WHEN exporting lineage, THE System SHALL include version information (scorer version, formula version)
5. WHEN data scientists import lineage data, THE System SHALL provide example code (Python/R) to reproduce calculations

---

**Version**: 2.0  
**Created**: 2025-10-28  
**Updated**: 2025-10-29  
**Status**: Requirements Complete - Added Data Lineage Requirements (14-16)
