# Requirements Document

## Introduction

Critical regressions have been introduced after completing the core-analysis-restoration spec. Despite all tasks being marked complete, the system is producing severely degraded output with data corruption, missing information, and incorrect grades. 

**USER REQUIREMENT**: All data produced by the different crews must be consolidated in a proper report instead of producing hallucinations after costly operations. The system is currently running expensive AI analysis (crews generating detailed risk assessments, grades, and recommendations) but then ignoring this data and showing generic fallback values instead.

This specification addresses the urgent need to diagnose and fix these regressions to restore system functionality and ensure that expensive crew analysis is actually used in the final output.

## Glossary

- **Grade Corruption**: A+ quality tickers being incorrectly labeled as Grade D
- **URL Forgery**: Real SEC filing URLs being replaced with placeholder example.com URLs
- **Data Availability Report**: Section of report showing which data sources are available/missing
- **Alternative Recommendations**: Suggested replacement investments for underperforming holdings
- **Flow State**: CrewAI Flow's structured state containing all analysis results
- **Report Crew**: Final crew that consolidates all analysis into HTML report
- **Discovery Results**: A+ investment opportunities found by screening crews

## Requirements

### Requirement 1: Grade Corruption Diagnosis and Fix - USE ACTUAL CREW DATA

**User Story:** As a financial analyst, I need portfolio holdings to display their correct grades (A+, A, B, etc.) from the actual crew analysis instead of all showing fallback Grade D, so that I can make informed investment decisions based on the expensive AI analysis that was actually performed.

**CONTEXT**: The system is running costly crew analysis that generates proper grades and risk assessments (confirmed in output files), but then ignoring this data and showing generic Grade D fallback values. This is wasting computational resources and providing incorrect information to users.

#### Acceptance Criteria

1. WHEN portfolio holdings are analyzed THEN they SHALL display their actual computed grades (A+, A, B, C, D, F)
2. WHEN A+ quality holdings exist THEN they SHALL be labeled as Grade A+ not Grade D
3. WHEN grades are computed THEN the computation logic SHALL be verified to produce correct results
4. WHEN grades are passed through the data flow THEN they SHALL not be corrupted or overwritten with default values
5. WHEN the report displays grades THEN it SHALL show the grades from the actual analysis, not fallback values
6. IF grade computation fails THEN the system SHALL log detailed error information and use appropriate fallback logic
7. WHEN debugging grade issues THEN the system SHALL trace grade values through the entire data flow pipeline

### Requirement 2: URL Forgery Diagnosis and Fix - AUDIT TRAIL REQUIREMENT

**User Story:** As an auditor, I need real SEC filing URLs and data source citations in reports, not placeholder example.com URLs, so that I can fact-check the report by verifying data accuracy against original sources.

**AUDIT REQUIREMENT**: Every data point in the report must be traceable to its source through valid URLs. This is essential for compliance, due diligence, and verifying that AI analysis is based on real data, not hallucinations.

#### Acceptance Criteria

1. WHEN SEC filings are referenced THEN they SHALL include real SEC EDGAR URLs not example.com placeholders
2. WHEN data sources are cited THEN they SHALL include actual URLs to the data sources for audit verification
3. WHEN URL generation fails THEN the system SHALL log errors and omit the URL rather than forge a fake one
4. WHEN the report is generated THEN it SHALL only include URLs that have been successfully retrieved from tools
5. IF a URL is unavailable THEN the report SHALL indicate "URL not available" rather than showing example.com
6. WHEN debugging URL issues THEN the system SHALL trace URL values from tool output through to report generation
7. WHEN tools return URLs THEN those URLs SHALL be preserved through all data transformations
8. WHEN an auditor clicks a URL THEN it SHALL lead to the actual source document, not a placeholder or error page
9. WHEN data is cited THEN the citation SHALL include: source name, URL, and as-of date for full traceability
10. WHEN the system cannot obtain a valid URL THEN it SHALL NOT include that data point in the report (fail-safe for audit trail)

### Requirement 3: Missing Alternatives Diagnosis and Fix

**User Story:** As a portfolio manager, I need alternative investment recommendations for underperforming holdings, not "aucune alternative fournie" messages, so that I can make informed rebalancing decisions.

#### Acceptance Criteria

1. WHEN holdings are graded below B THEN the system SHALL provide alternative investment recommendations
2. WHEN alternatives are computed THEN they SHALL be included in the portfolio review data structure
3. WHEN alternatives are passed to the report THEN they SHALL be preserved and displayed correctly
4. WHEN no suitable alternatives exist THEN the system SHALL explicitly state "No suitable alternatives found" with reasoning
5. IF alternative finding fails THEN the system SHALL log detailed error information
6. WHEN the report displays holdings THEN it SHALL show alternatives for each underperforming holding
7. WHEN debugging alternative issues THEN the system SHALL trace alternative data through the entire pipeline

### Requirement 4: Data Availability Report Fix

**User Story:** As a system operator, I need the data availability report to accurately reflect which data sources are available, not show "NOT PROVIDED" for all fields, so that I can understand system health and data quality.

#### Acceptance Criteria

1. WHEN the report is generated THEN it SHALL include a complete data availability summary
2. WHEN data sources are queried THEN their availability status SHALL be tracked and reported
3. WHEN the data availability summary is constructed THEN it SHALL include counts of available/unavailable/stale sources
4. WHEN freshness warnings exist THEN they SHALL be included in the data availability report
5. WHEN discovery is not run THEN the report SHALL clearly state "Discovery not run - use --discovery flag"
6. WHEN discovery IS run THEN the report SHALL show actual discovery results and backtesting status
7. WHEN the report crew receives inputs THEN it SHALL have access to data_availability_summary and data_availability_summary_formatted

### Requirement 5: Root Cause Analysis - DATA CREATION vs CONSUMPTION GAP

**User Story:** As a developer, I need to understand exactly where and why these regressions were introduced, so that I can fix them properly and prevent similar issues in the future.

**CRITICAL FINDING**: Analysis crews ARE creating rich, detailed data with proper grades and risk assessments (confirmed in output/stock/stock_output_*.json files), but this data is NOT being consumed by the portfolio review. The portfolio review shows all holdings with fallback Grade D (composite_score 0.6) and generic "Validation rapide" messages, indicating the deep analysis results are not being merged.

#### Acceptance Criteria

1. WHEN analyzing the regression THEN the system SHALL confirm that crews ARE generating proper data (verified: stock_output shows detailed risk assessments with proper grades)
2. WHEN tracing data flow THEN the system SHALL identify where the disconnect occurs between data creation (crews) and data consumption (portfolio review)
3. WHEN examining the deep analysis merge THEN the system SHALL verify why cached deep analysis is not being applied to portfolio holdings
4. WHEN reviewing the portfolio_holdings_processor THEN the system SHALL identify why it's using fallback grades instead of deep analysis grades
5. WHEN examining the analyze_and_update_portfolio flow THEN the system SHALL verify the deep analysis results are being passed correctly
6. WHEN checking the merge logic THEN the system SHALL identify why "Deep analysis merge complete: 5 holdings with deep analysis" doesn't actually merge the grades
7. WHEN analyzing the issue THEN the system SHALL document that this is a DATA CONSUMPTION bug, not a data generation bug

### Requirement 6: Data Flow Integrity Verification

**User Story:** As a system architect, I need to verify that data flows correctly from crews through Flow state to the report, without corruption or loss, so that the system produces accurate outputs.

#### Acceptance Criteria

1. WHEN crews execute THEN their outputs SHALL be stored with complete and accurate data
2. WHEN Flow state is updated THEN all required fields SHALL be populated with actual data not defaults
3. WHEN data is passed between Flow methods THEN it SHALL be preserved without corruption
4. WHEN the report crew receives inputs THEN it SHALL have access to ALL required data from upstream
5. WHEN data transformations occur THEN they SHALL preserve data integrity and not introduce defaults
6. IF data is missing at any stage THEN the system SHALL log detailed diagnostic information
7. WHEN debugging data flow THEN the system SHALL provide tools to trace data through the entire pipeline

### Requirement 7: Test Coverage for Regressions

**User Story:** As a developer, I need comprehensive tests that would have caught these regressions, so that similar issues don't occur in the future.

#### Acceptance Criteria

1. WHEN tests are written THEN they SHALL verify correct grade assignment and preservation
2. WHEN tests are written THEN they SHALL verify real URLs are included not placeholders
3. WHEN tests are written THEN they SHALL verify alternatives are provided for underperforming holdings
4. WHEN tests are written THEN they SHALL verify data availability reports are complete
5. WHEN tests are written THEN they SHALL verify end-to-end data flow from crews to report
6. IF any regression test fails THEN it SHALL provide clear diagnostic information
7. WHEN tests run THEN they SHALL catch data corruption, missing data, and incorrect defaults

### Requirement 8: Emergency Rollback Plan

**User Story:** As a system operator, I need the ability to quickly rollback to a working state if the fix introduces new issues, so that users can continue using the system.

#### Acceptance Criteria

1. WHEN a rollback is needed THEN the system SHALL have a documented rollback procedure
2. WHEN rolling back THEN the system SHALL restore to the last known good state
3. WHEN rollback is complete THEN all functionality SHALL work as it did before the regression
4. IF rollback is not possible THEN the system SHALL have a hotfix procedure
5. WHEN rollback occurs THEN users SHALL be notified of the temporary state
6. WHEN the fix is ready THEN it SHALL be deployed with verification that regressions are resolved
7. WHEN deploying fixes THEN they SHALL be tested in a staging environment first

### Requirement 9: Immediate Diagnostic Logging

**User Story:** As a developer, I need detailed diagnostic logging added to the current system to understand exactly where data is being corrupted or lost, so that I can fix the issues quickly.

#### Acceptance Criteria

1. WHEN crews execute THEN they SHALL log the grades they compute with ticker symbols
2. WHEN Flow state is updated THEN it SHALL log what data is being stored
3. WHEN data is passed to the report crew THEN it SHALL log all input fields and their values
4. WHEN the report crew processes data THEN it SHALL log what it receives and how it transforms it
5. WHEN URLs are generated THEN the system SHALL log the actual URLs being created
6. WHEN alternatives are found THEN the system SHALL log the alternatives for each holding
7. WHEN data availability is checked THEN the system SHALL log the status of each data source

### Requirement 10: Data Consolidation - NO HALLUCINATIONS

**User Story:** As a user paying for expensive AI analysis, I need the final report to consolidate ALL actual data produced by crews, not generate hallucinations or use fallback values, so that I get value from the computational resources spent.

**CRITICAL**: The system must NEVER show generic/fallback data when actual crew analysis exists. Every piece of data in the final report must be traceable to actual crew outputs, not invented or defaulted.

#### Acceptance Criteria

1. WHEN crews generate analysis data THEN that data SHALL be used in the final report, not replaced with defaults
2. WHEN the report displays grades THEN they SHALL come from actual crew analysis, not fallback Grade D values
3. WHEN the report shows risk scores THEN they SHALL come from actual risk assessment tools, not baseline defaults
4. WHEN the report includes URLs THEN they SHALL be real URLs from tools, not example.com placeholders
5. WHEN alternatives are shown THEN they SHALL be from actual alternative finding logic, not empty lists
6. WHEN data availability is reported THEN it SHALL reflect actual data sources queried, not "NOT PROVIDED" messages
7. WHEN the system cannot find crew data THEN it SHALL log detailed errors and investigate why, not silently use defaults
8. WHEN consolidating data THEN the system SHALL verify each field comes from actual crew output before including it
9. IF crew data is missing THEN the system SHALL fail loudly with clear error messages, not silently degrade to hallucinations
10. WHEN users see analysis results THEN they SHALL be confident the data reflects actual analysis, not invented values

### Requirement 11: Audit Trail and Data Provenance

**User Story:** As an auditor, I need complete traceability from every data point in the report back to its original source, so that I can fact-check the analysis and verify data accuracy for compliance and due diligence.

**COMPLIANCE REQUIREMENT**: Financial reports must be auditable. Every claim, grade, risk score, and recommendation must be traceable to verifiable sources.

#### Acceptance Criteria

1. WHEN the report shows a grade THEN it SHALL include the source of that grade (crew name, analysis date, confidence level)
2. WHEN the report shows a risk score THEN it SHALL cite the tool and data sources used to compute it
3. WHEN the report references SEC filings THEN it SHALL include direct EDGAR URLs to the specific filing
4. WHEN the report shows market data THEN it SHALL cite the data provider (Yahoo Finance, Alpha Vantage, etc.) with as-of date
5. WHEN the report includes recommendations THEN it SHALL show the reasoning chain and data sources that led to that recommendation
6. WHEN an auditor needs to verify data THEN they SHALL be able to click through to original sources
7. WHEN data cannot be verified THEN it SHALL NOT be included in the report (no unverifiable claims)
8. WHEN the report is generated THEN it SHALL include a "Data Sources" section listing all sources with URLs
9. WHEN crew analysis is used THEN the report SHALL indicate which crew performed the analysis and when
10. WHEN the system uses cached data THEN the report SHALL indicate the cache age and original analysis date

### Requirement 12: End-to-End Data Flow Verification

**User Story:** As a senior data analyst, I need to verify that all crews are generating proper data AND that data is consumed properly to generate reports, so that I can ensure data integrity throughout the entire pipeline.

**DATA QUALITY ASSURANCE**: The system must provide verification at every stage: data generation, data storage, data retrieval, data consolidation, and report generation.

#### Acceptance Criteria

1. WHEN crews execute THEN the system SHALL log what data they generated (grades, scores, URLs, recommendations)
2. WHEN crew data is stored THEN the system SHALL verify the data was written correctly and is retrievable
3. WHEN data is retrieved THEN the system SHALL verify it matches what was stored (no corruption)
4. WHEN data is consolidated THEN the system SHALL log which crew data was included and which was missing
5. WHEN the report is generated THEN the system SHALL verify each data point came from actual crew output
6. WHEN data flow is complete THEN the system SHALL provide a verification report showing: crews run, data generated, data stored, data retrieved, data used in report
7. WHEN data is missing at any stage THEN the system SHALL log detailed diagnostics: what was expected, what was found, where the gap occurred
8. WHEN debugging data issues THEN analysts SHALL be able to trace data from crew output → storage → retrieval → consolidation → report
9. WHEN the system runs THEN it SHALL generate a data lineage report showing the complete flow for audit purposes
10. WHEN data quality issues are detected THEN the system SHALL alert immediately, not silently degrade

### Requirement 13: Fail-Fast Error Handling - NO SILENT DEGRADATION

**User Story:** As an expert on quality outcomes, I want the system to stop immediately if it detects errors, so that bad data never reaches the final report and users are never misled by degraded output.

**QUALITY PRINCIPLE**: It is better to fail loudly and stop execution than to silently degrade and produce misleading reports. Users must be able to trust that if they receive a report, it contains accurate data.

#### Acceptance Criteria

1. WHEN crew execution fails THEN the system SHALL stop immediately and report the error, not continue with fallback data
2. WHEN data retrieval fails THEN the system SHALL stop and investigate why, not silently use Grade D defaults
3. WHEN data consolidation finds missing data THEN the system SHALL stop and log detailed diagnostics, not proceed with partial data
4. WHEN URL generation fails THEN the system SHALL stop and report the issue, not forge example.com placeholders
5. WHEN alternative finding fails THEN the system SHALL stop and explain why, not show empty lists
6. WHEN data validation detects corruption THEN the system SHALL stop immediately, not attempt to fix or ignore it
7. WHEN the report crew receives incomplete inputs THEN it SHALL refuse to generate a report, not fill gaps with hallucinations
8. WHEN any data quality check fails THEN the system SHALL provide clear error messages with remediation steps
9. WHEN errors are detected THEN the system SHALL log: what failed, why it failed, what data was expected, what was found
10. WHEN the system stops due to errors THEN users SHALL receive actionable error messages, not generic failures

**EXCEPTION**: The system MAY continue with graceful degradation ONLY when explicitly configured to do so AND when it clearly marks degraded sections in the report with warnings.

### Requirement 14: CrewAI Task and Agent Configuration Validation

**User Story:** As a CrewAI expert, I need to ensure that all crew task descriptions are accurate and synchronized with our specifications and requirements, so that agents perform the correct analysis and produce the expected outputs.

**CONFIGURATION INTEGRITY**: Crew configurations (agents.yaml, tasks.yaml) must accurately reflect the system requirements. Misaligned configurations lead to agents performing wrong analysis or producing incorrect output formats.

#### Acceptance Criteria

1. WHEN crews are configured THEN their task descriptions SHALL match the requirements in this specification
2. WHEN agents are defined THEN their roles and goals SHALL align with the data they are expected to produce
3. WHEN tasks specify expected_output THEN it SHALL match the actual Pydantic schemas used for validation
4. WHEN tasks use output_pydantic THEN the schema SHALL exist and be correctly referenced
5. WHEN agents use tools THEN those tools SHALL be appropriate for the task and produce the expected data format
6. WHEN the report crew is configured THEN it SHALL have NO tools (tool-free reporter pattern)
7. WHEN discovery crews are configured THEN they SHALL be clearly marked as "top 10 screening" not "single ticker analysis"
8. WHEN deep analysis crews are configured THEN they SHALL be clearly marked as "single ticker deep dive"
9. WHEN task descriptions are updated THEN they SHALL be reviewed against requirements to ensure alignment
10. WHEN configuration drift is detected THEN the system SHALL alert and require manual review before proceeding

### Requirement 15: Pydantic Schema Enforcement for Data Transfer

**User Story:** As a data scientist, I need to ensure that Pydantic is always used to transfer data with high quality and semantic validation, so that data integrity is maintained throughout the system and type safety prevents errors.

**DATA TRANSFER STANDARD**: ALL data transfers between system components MUST use strict Pydantic v2 models with `extra='forbid'` to ensure type safety, semantic validation, and prevent data corruption.

#### Acceptance Criteria

1. WHEN crews generate outputs THEN they SHALL use Pydantic models with strict validation (`extra='forbid'`)
2. WHEN data is passed between Flow methods THEN it SHALL be validated against Pydantic schemas
3. WHEN the report crew receives inputs THEN all inputs SHALL be Pydantic-validated before processing
4. WHEN data is stored THEN it SHALL be serialized from validated Pydantic models
5. WHEN data is retrieved THEN it SHALL be deserialized into Pydantic models with validation
6. WHEN data transformations occur THEN input and output SHALL both be Pydantic-validated
7. WHEN validation fails THEN the system SHALL stop immediately with detailed field-level error messages
8. WHEN new data structures are added THEN they SHALL have corresponding Pydantic models defined
9. WHEN Pydantic models are updated THEN all usages SHALL be reviewed for compatibility
10. WHEN data is passed as dict THEN it SHALL be immediately converted to Pydantic model for validation

**BANNED PATTERNS:**
- ❌ Passing raw dicts between components without validation
- ❌ Using `extra='allow'` (allows unknown fields)
- ❌ Skipping validation for "performance"
- ❌ Manual dict construction instead of Pydantic models
- ❌ Type: ignore comments to bypass validation

**REQUIRED PATTERNS:**
- ✅ All crew outputs use `output_pydantic` with strict schemas
- ✅ All Flow state fields are Pydantic models
- ✅ All API boundaries validate with Pydantic
- ✅ All data storage/retrieval uses Pydantic serialization
- ✅ Validation errors include field paths and clear messages

### Requirement 16: Alignment with FinWiz Steering Standards

**User Story:** As a system architect, I need to ensure all requirements align with FinWiz steering standards, so that the fix maintains consistency with established patterns and doesn't introduce architectural drift.

**STEERING COMPLIANCE**: All fixes must comply with established FinWiz standards in `.kiro/steering/` directory.

#### Acceptance Criteria - Alignment Verification

1. **validation.md**: WHEN implementing fixes THEN they SHALL use strict Pydantic v2 models with `extra='forbid'` as specified
2. **crewai-standards.md**: WHEN configuring crews THEN they SHALL follow the required structure (agents.yaml, tasks.yaml, output_pydantic)
3. **crewai-flow-compliance.md**: WHEN using Flow state THEN it SHALL use structured Pydantic models, not unstructured dicts
4. **output-standards.md**: WHEN generating reports THEN they SHALL use proper HTML structure, French language, and emoji standards
5. **testing-standards.md**: WHEN writing tests THEN they SHALL use pytest-mock (unittest.mock is BANNED)
6. **quality.md**: WHEN handling errors THEN they SHALL implement graceful degradation with clear logging
7. **security.md**: WHEN handling data THEN they SHALL never log sensitive information or API keys
8. **tech.md**: WHEN writing code THEN it SHALL follow Ruff standards (110 char limit, type hints)
9. **finance.md**: WHEN providing analysis THEN it SHALL use standardized risk assessment (0-5 scale)
10. **agents.md**: WHEN configuring agents THEN they SHALL follow AI-driven analysis principles (not just Python logic)

**CRITICAL ALIGNMENTS:**
- ✅ Pydantic strict validation (validation.md)
- ✅ CrewAI Flow structured state (crewai-flow-compliance.md)
- ✅ Tool-free final reporter (crewai-standards.md)
- ✅ pytest-mock only (testing-standards.md, unittest-mock-ban.md)
- ✅ Fail-fast error handling (quality.md)
- ✅ French output standards (output-standards.md)
- ✅ Audit trail requirements (finance.md, security.md)

### Requirement 17: Validation of Recent Changes

**User Story:** As a code reviewer, I need to validate that recent changes to data passing and report generation are correct and haven't introduced bugs, so that the system works as designed.

#### Acceptance Criteria

1. WHEN reviewing Task 13 changes THEN they SHALL be verified to correctly pass all Flow state to report crew
2. WHEN reviewing data consolidation fixes THEN they SHALL be verified to not corrupt existing data
3. WHEN reviewing report crew changes THEN they SHALL be verified to correctly process all inputs
4. WHEN reviewing Flow state management THEN it SHALL be verified to preserve all data correctly
5. IF any recent change is found to be incorrect THEN it SHALL be reverted or fixed
6. WHEN validating changes THEN they SHALL be tested with real portfolio data
7. WHEN changes are validated THEN they SHALL be verified to not introduce new regressions
