# Requirements Document

## Introduction

This specification defines a reorganization of the FinWiz crew architecture to fix the broken data flow between analysis crews and the final report. The current architecture has crews performing analysis without generating complete outputs, leading to data loss and fallback values persisting in the final report. The new architecture will reorganize each crew to perform pillar tasks and generate BOTH a structured JSON output AND a complete HTML report. A new aggregator crew will then consolidate all crew outputs into a final comprehensive report.

## Glossary

- **Crew**: An autonomous AI agent team that performs specific analysis tasks (e.g., StockCrew, ETFCrew, CryptoCrew, DeepAnalysisCrew)
- **Report**: A complete HTML document containing analysis findings, recommendations, and data
- **Aggregator Crew**: A new crew responsible for consolidating multiple crew reports into a single comprehensive report
- **Flow**: The CrewAI Flow orchestrator that manages crew execution sequence and data passing
- **Portfolio Review**: Analysis of existing holdings with keep/sell recommendations
- **Deep Analysis**: Comprehensive analysis of individual holdings using specialized crews
- **Discovery**: Process of finding new A+ investment opportunities

## Requirements

### Requirement 1: Pydantic-Validated Export Objects for All Crews

**User Story:** As a FinWiz developer, I want each crew to generate a Pydantic-validated export object saved to JSON, so that all crew outputs are type-safe and validated.

#### Acceptance Criteria

1. THE System SHALL define a dedicated Pydantic export schema for each crew (StockCrewExport, ETFCrewExport, CryptoCrewExport, DeepAnalysisCrewExport, DiscoveryCrewExport, RebalancingCrewExport)
2. WHEN a crew completes its analysis tasks, THE Crew SHALL have a final reporter task that creates a Pydantic-validated export object
3. THE reporter task SHALL validate all analysis data against the crew's Pydantic export schema
4. WHEN validation succeeds, THE reporter task SHALL save the Pydantic export object to a JSON file
5. THE JSON file SHALL include all analysis data (scores, grades, recommendations, risk assessments, metadata, file paths)
6. THE JSON file SHALL be saved to: `output/reports/{session_id}/{crew_name}/{crew_name}_export.json`
7. IF validation fails, THEN THE reporter task SHALL raise a clear error with validation failure details

### Requirement 2: HTML Report Generation with Python Templates (NO AI)

**User Story:** As a FinWiz developer, I want HTML reports generated using Python templates (Jinja2) from JSON exports, so that report generation is fast, testable, cheap, and deterministic.

#### Acceptance Criteria

1. THE System SHALL use Jinja2 templates for ALL HTML report generation (NO AI agents for HTML generation)
2. THE System SHALL create professional HTML templates for each crew type with light/dark mode support
3. THE HTML templates SHALL accept the crew's JSON export as input data
4. THE HTML generation SHALL be pure Python code (testable, fast, no LLM costs)
5. WHEN a crew completes its JSON export, THE System SHALL call a Python function to generate HTML from template
6. THE HTML generation function SHALL validate the JSON data against the crew's Pydantic export schema
7. THE HTML templates SHALL include professional styling (CSS) with responsive design
8. THE HTML file SHALL be saved to: `output/reports/{session_id}/{crew_name}/{crew_name}_report.html`
9. THE HTML generation SHALL NOT use AI agents, LLM calls, or CrewAI tasks
10. THE HTML generation code SHALL be unit-testable with mock JSON data

### Requirement 3: Python-Based Data Consolidation (NO Aggregator Crew)

**User Story:** As a FinWiz developer, I want data consolidation done in pure Python without any AI crew, so that aggregation is fast, deterministic, testable, and free of LLM costs.

#### Acceptance Criteria

1. THE System SHALL use pure Python code for data consolidation (NO Aggregator Crew, NO AI agents)
2. THE Flow SHALL call a Python consolidation function after all SME crews complete
3. THE Python consolidation function SHALL receive file paths of all SME crew JSON exports as parameters
4. THE Python consolidation function SHALL read all SME crew JSON export files from disk
5. WHEN reading JSON files, THE consolidation function SHALL validate each file against its source crew's Pydantic export schema
6. THE consolidation function SHALL create a consolidated Pydantic export object (ConsolidatedReportExport)
7. THE consolidation function SHALL save the consolidated export to: `output/reports/{session_id}/consolidated_report.json`
8. THE consolidation function SHALL preserve ALL grades, scores, and recommendations exactly as provided by SME crews
9. THE consolidation function SHALL be unit-testable with mock JSON files
10. THE consolidation function SHALL NOT call external APIs or LLMs
11. THE consolidation SHALL be deterministic (same inputs = same outputs)
12. THE consolidation function SHALL complete in milliseconds (not seconds)

### Requirement 4: Comprehensive Crew Evaluation - All Existing Crews

**User Story:** As a FinWiz manager, I want to evaluate ALL existing crews (crypto_crew, deep_analysis, etf_crew, investment_discovery_crew, portfolio_rebalancing_crew, report_crew, stock_crew) to identify tasks that should be Python instead of AI, so that we maximize quality, speed, and cost-efficiency.

#### Acceptance Criteria

1. THE System SHALL evaluate EVERY task in EVERY existing crew to determine if AI is truly necessary
2. THE evaluation SHALL cover: crypto_crew, deep_analysis, etf_crew, investment_discovery_crew, portfolio_rebalancing_crew, report_crew, stock_crew
3. FOR EACH crew, THE System SHALL document:
   - Which tasks require AI (and WHY - what makes them non-deterministic)
   - Which tasks should be Python (and implementation requirements)
   - Which tasks should be removed entirely (redundant or unnecessary)
4. THE evaluation SHALL identify tasks that are:
   - Data fetching (should be Python tools, not AI tasks)
   - Calculations (should be Python functions, not AI tasks)
   - Validations (should be Pydantic, not AI tasks)
   - HTML generation (should be Jinja2 templates, not AI tasks)
   - Data transformation (should be Python, not AI tasks)
5. THE System SHALL create a detailed evaluation document for each crew listing:
   - Current tasks
   - AI necessity assessment (YES/NO with justification)
   - Python replacement requirements (if applicable)
   - Expected cost savings
   - Expected performance improvement
6. THE evaluation SHALL be ruthless - if Python can do it, mark it for replacement
7. THE System SHALL prioritize: quality > speed > cost savings (but achieve all three)

### Requirement 5: Final Report Generation with Python Template (NO AI, NO Crew)

**User Story:** As a FinWiz user, I want the final French report generated using a Python template from consolidated JSON, so that report generation is instant, free, and produces consistent professional output.

#### Acceptance Criteria

1. THE System SHALL use a Jinja2 template for final report generation (NO AI agent, NO crew)
2. THE Flow SHALL call a Python function to generate the final HTML report after consolidation
3. THE final report template SHALL accept the consolidated JSON export as input
4. THE final report template SHALL generate professional French-language HTML with light/dark mode
5. THE final report SHALL include sections for each SME crew's analysis
6. THE final report generation SHALL be pure Python code (no LLM calls, no CrewAI)
7. THE final report HTML SHALL be saved to: `output/reports/{session_id}/final_report.html`
8. THE final report generation SHALL be unit-testable with mock consolidated JSON
9. THE template SHALL include executive summary, detailed findings, and recommendations sections
10. THE template SHALL use professional financial terminology in French
11. THE template SHALL be maintainable by developers (not generated by AI)
12. THE final report generation SHALL complete in milliseconds

### Requirement 6: File-Based Data Passing to Avoid Context Limits

**User Story:** As a FinWiz developer, I want the Flow to pass file paths (not data) between crews, so that we avoid exceeding model context size limits.

#### Acceptance Criteria

1. THE Flow SHALL store file paths in structured state (NOT the actual data)
2. WHEN a crew completes, THE Flow SHALL store the JSON export file path in structured state
3. WHEN passing data to downstream crews, THE Flow SHALL pass file paths as input parameters
4. THE Crews SHALL read data from files when needed (not from Flow state)
5. THE Flow state SHALL remain small and focused on orchestration metadata (file paths, status, timestamps)
6. THE System SHALL NOT pass large data objects through Flow state or crew inputs

### Requirement 7: Concurrent SME Crew Execution with Python Consolidation

**User Story:** As a FinWiz developer, I want all SME crews to run concurrently, then call a Python function for consolidation, so that analysis is fast and consolidation is instant.

#### Acceptance Criteria

1. THE Flow SHALL execute all SME crews (Stock, ETF, Crypto, DeepAnalysis, Discovery, Rebalancing) concurrently using CrewAI Flow's parallel execution patterns
2. THE Flow SHALL use `@listen()` decorators with the same trigger to enable parallel crew execution
3. THE SME crews SHALL NOT depend on each other's outputs for execution
4. WHEN all SME crews complete, THE Flow SHALL call a Python consolidation function using `@listen(and_(...))`
5. THE Flow SHALL pass all crew JSON output file paths to the Python consolidation function
6. THE Python consolidation function SHALL NOT be a CrewAI crew (pure Python function)
7. WHEN a crew fails, THE Flow SHALL continue execution and mark the crew output as unavailable
8. THE Flow SHALL track crew execution status in structured state (pending, running, completed, failed)

### Requirement 8: French Language Final Report

**User Story:** As a FinWiz user, I want the final aggregated report in professional French, so that I can review investment recommendations in my preferred language.

#### Acceptance Criteria

1. THE FinancialExpertAggregatorCrew SHALL generate the final report entirely in French
2. WHEN synthesizing findings, THE FinancialExpertAggregatorCrew SHALL use professional financial terminology in French
3. THE final report SHALL include clear sections for each SME crew's analysis (Actions, ETFs, Cryptomonnaies, Analyse Approfondie, Découverte, Rééquilibrage)
4. THE final report SHALL include executive summary, detailed findings, and actionable recommendations in French
5. THE FinancialExpertAggregatorCrew agent backstory SHALL specify French-speaking financial expert

### Requirement 9: Report File Management

**User Story:** As a FinWiz developer, I want a standardized directory structure for crew outputs, so that JSON and HTML files are easy to locate and manage.

#### Acceptance Criteria

1. THE System SHALL create an output directory structure: `output/reports/{session_id}/{crew_name}/`
2. WHEN a crew generates outputs, THE Crew SHALL save both JSON and HTML files with descriptive filenames including timestamp
3. WHEN saving JSON output, THE Crew SHALL use filename pattern: `{crew_name}_{ticker}_{timestamp}.json`
4. WHEN saving HTML output, THE Crew SHALL use filename pattern: `{crew_name}_{ticker}_{timestamp}.html`
5. WHEN the Flow executes, THE Flow SHALL track all generated file paths in structured state (separate lists for JSON and HTML)
6. THE System SHALL maintain a report manifest JSON file listing all generated outputs with metadata (crew_name, ticker, asset_class, status, file_paths)
7. WHEN the aggregator crew executes, THE FinancialExpertAggregatorCrew SHALL read the report manifest to locate source files

### Requirement 10: Data Integrity Validation

**User Story:** As a FinWiz developer, I want validation that ensures crew reports contain actual analysis data (not fallback values), so that the final report is accurate.

#### Acceptance Criteria

1. WHEN a crew generates a report, THE Crew SHALL validate that all required data fields are present
2. WHEN validating data, THE System SHALL reject reports containing only fallback values (e.g., Grade D with score 0.6)
3. IF a crew report fails validation, THEN THE System SHALL log a detailed error message with the validation failure reason
4. WHEN the aggregator crew reads a report, THE ReportAggregatorCrew SHALL validate the HTML structure and data completeness
5. IF a source report is invalid, THEN THE ReportAggregatorCrew SHALL include a warning in the final report

### Requirement 11: Clean Break from Legacy Architecture

**User Story:** As a FinWiz developer, I want to implement a clean new architecture without backward compatibility constraints, so that we can fix fundamental design flaws.

#### Acceptance Criteria

1. THE System SHALL implement a new architecture without maintaining backward compatibility with the broken legacy system
2. THE System SHALL remove all legacy data merge logic that caused fallback values to persist
3. THE System SHALL remove all legacy portfolio review injection patterns
4. THE System SHALL implement new Pydantic schemas for all crew outputs without legacy field constraints
5. THE System SHALL implement new Flow orchestration without legacy state management patterns

### Requirement 12: Error Handling and Resilience

**User Story:** As a FinWiz developer, I want robust error handling that prevents partial failures from breaking the entire Flow, so that users receive the best possible report even when some crews fail.

#### Acceptance Criteria

1. WHEN a crew fails to generate a report, THE Flow SHALL continue execution with remaining crews
2. WHEN the aggregator crew encounters a missing report, THE ReportAggregatorCrew SHALL include a placeholder section noting the missing analysis
3. IF all source reports are missing, THEN THE ReportAggregatorCrew SHALL generate a minimal report with error details
4. THE System SHALL log all crew execution failures with detailed error messages
5. WHEN a crew times out, THE Flow SHALL mark the crew as failed and continue with remaining crews

### Requirement 13: Flow-Based Routing Logic

**User Story:** As a FinWiz developer, I want all routing and orchestration logic in the CrewAI Flow, so that crews remain simple and focused on their analysis tasks.

#### Acceptance Criteria

1. THE CrewAI Flow SHALL contain ALL routing logic for crew execution sequence
2. THE Crews SHALL NOT contain any routing or orchestration logic
3. THE Crews SHALL NOT decide which other crews to execute
4. THE Flow SHALL use `@listen()`, `@router()`, and `and_()` decorators for all routing decisions
5. WHEN a crew completes, THE Crew SHALL return its output data without making routing decisions
6. THE Flow SHALL determine which crews to execute based on structured state and routing logic
7. THE Crews SHALL remain focused on their single analysis responsibility

### Requirement 14: SME Crew Independence

**User Story:** As a FinWiz developer, I want each SME crew to operate independently without requiring data from other crews, so that crews can execute concurrently without blocking.

#### Acceptance Criteria

1. THE SME crews SHALL NOT read outputs from other SME crews during execution
2. THE SME crews SHALL receive all required inputs from the Flow at kickoff time
3. WHEN a crew requires market context, THE Crew SHALL fetch data directly using its own tools
4. THE SME crews SHALL NOT share state or communicate with each other during execution
5. THE Flow SHALL provide each crew with session metadata (date, timestamp, language) at kickoff
6. WHERE a crew requires ticker information, THE Flow SHALL pass the ticker as an input parameter

### Requirement 15: Performance Optimization

**User Story:** As a FinWiz user, I want the new architecture to maximize execution performance, so that reports are generated quickly.

#### Acceptance Criteria

1. THE System SHALL execute ALL SME crews concurrently using CrewAI Flow's parallel execution (Stock, ETF, Crypto, DeepAnalysis, Discovery, Rebalancing)
2. THE SME crews SHALL use `reasoning=False` and `planning=False` for fast execution
3. THE SME crews SHALL use `allow_delegation=False` since they operate independently
4. WHEN generating outputs, THE Crew SHALL write JSON and HTML files to avoid blocking
5. THE FinancialExpertAggregatorCrew SHALL read and parse source files efficiently
6. THE System SHALL maintain existing caching mechanisms to avoid redundant crew executions
7. THE Flow SHALL use CrewAI's `@listen()` pattern with same trigger for parallel crew execution
