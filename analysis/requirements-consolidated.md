# FinWiz Platform: Consolidated Requirements Specification

## 1. Introduction

This document provides a unified and consistent set of requirements for the FinWiz platform. It is the result of a comprehensive review of multiple requirement specifications and incorporates a clear architectural vision based on performance, reliability, and trust.

This specification establishes a single source of truth for development, guided by the core principles outlined below.

## 2. Core Architectural Principles

### 2.1. Python-First for Deterministic Tasks

To ensure speed, reliability, and cost-effectiveness, the system will adhere to a "Python-First" principle.
-   **Deterministic calculations**, such as scoring, grading, risk metric computation, and data aggregation, **must** be implemented in pure Python.
-   **HTML report generation** **must** be handled by a Python templating engine (Jinja2).
-   **AI agents and crews** are reserved for tasks that require genuine reasoning, synthesis, and complex, non-deterministic analysis. They are a powerful tool, not a default for every task.

This approach provides 10-20x performance improvements, 100% cost reduction for calculations, and fully testable, reproducible results.

### 2.2. Fail-Fast on Critical Errors ("Stop and Fix")

Given that the system's outputs inform financial decisions, correctness is paramount. The system will adopt the "Stop and Fix" philosophy, inspired by the Toyota Production System's Andon cord.
-   The system **must** halt execution immediately upon encountering a **critical failure**. It is better to produce no report than a partial or inaccurate one.
-   **Graceful degradation** is only acceptable for non-critical, isolated failures (e.g., a single news article failing to download for sentiment analysis) and must be clearly logged and flagged in the final report.
-   Critical failures include, but are not limited to: core data integration failures, inability to load portfolio data, critical schema validation errors, or a high percentage (>10%) of holdings failing analysis.

## 3. Core Architectural Requirements

### 3.1. Hybrid Deep Analysis (Python-First, AI-Optional)

**User Story:** As a FinWiz operator, I want deep analysis to be performed by a fast, deterministic Python engine by default, with the option to use an AI crew for occasional, deeper reasoning, so that I can balance speed and cost with analytical depth.

#### Acceptance Criteria

1.  The system SHALL use an environment variable to control the deep analysis mode: `DEEP_ANALYSIS_MODE` (options: `python`, `ai`; default: `python`).
2.  WHEN `DEEP_ANALYSIS_MODE=python`, THE Flow SHALL execute a pure Python analysis function that uses a `DeepAnalysisScorer` class for all calculations. This path must be fast (< 1 minute per ticker), deterministic, and make zero LLM calls for scoring.
3.  WHEN `DEEP_ANALYSIS_MODE=ai`, THE Flow SHALL execute the `DeepAnalysisCrew` for a full AI-based analysis. This mode is for occasional use, validation, or complex cases, not for high-volume production runs.
4.  The roles of the **Discovery Crews** (`StockCrew`, `ETFCrew`, `CryptoCrew`) remain unchanged: they are for screening and identifying "top 10" new opportunities and are not to be used for single-ticker deep analysis.

### 3.2. Corrected Flow Orchestration

**User Story:** As a FinWiz operator, I want the execution flow to follow the logical business sequence, so that portfolio analysis happens before discovery and all phases execute in the proper order.

#### Acceptance Criteria

1.  WHEN the flow starts, THE `FinwizFlow` SHALL execute `validate_data_integration` as Phase 1.
2.  WHEN Phase 1 completes, THE `FinwizFlow` SHALL execute `check_portfolio` as Phase 2 to analyze existing holdings.
3.  WHEN Phase 2 completes, THE `FinwizFlow` SHALL execute `analyze_and_update_portfolio` as Phase 3 to grade holdings and identify needs.
4.  WHEN Phase 3 completes, THE `FinwizFlow` SHALL execute discovery crews (`check_stock`, `check_etf`, `check_crypto`) as Phase 4.
5.  WHEN all discovery crews complete, THE `FinwizFlow` SHALL execute `check_investment_discovery` to consolidate A+ opportunities.
6.  WHEN Phase 4 completes, THE `FinwizFlow` SHALL execute `check_portfolio_rebalancing` as Phase 5 to optimize allocations.
7.  WHEN Phase 5 completes, THE `FinwizFlow` SHALL execute `report` as Phase 6 to present final recommendations.
8.  WHEN `analyze_and_update_portfolio` executes, THE `FinwizFlow` SHALL perform deep analysis, match alternatives, and update portfolio review in one atomic operation.

## 4. Data, Integration, and Quality Requirements

### 4.1. Data Integration & Validation

**User Story:** As a FinWiz quality engineer, I want data to flow correctly between all system components with strict validation, so that the reporter receives complete and accurate data.

#### Acceptance Criteria

1.  WHEN a crew completes execution, THE Data Integration System SHALL store crew outputs as validated JSON files in `output/{crew_name}/` directories.
2.  WHEN data is passed between components, it SHALL be validated against strict Pantic models with `extra='forbid'`.
3.  WHEN the `ReportCrew` receives input, it SHALL be validated against the `ReporterInput` Pantic schema.
4.  WHEN a crew begins analysis, THE Data Integration System SHALL use `TickerValidationTool` to verify ticker symbols.
5.  All intermediate crew tasks SHALL output validated JSON data conforming to Pantic schemas. Only final reports may be HTML.

### 4.2. Data Freshness and Quality

**User Story:** As a financial analyst, I want to ensure that all market data is current and high-quality, so that investment recommendations are based on relevant information.

#### Acceptance Criteria

1.  WHEN market data is retrieved, THE Data Integration System SHALL validate that timestamps are no older than 24 hours.
2.  IF market data is older than 24 hours, THEN THE Data Integration System SHALL flag the analysis with warnings and reduce confidence scores.
3.  The system SHALL track data quality metrics (calculated vs. defaulted vs. missing) and display a quality indicator in reports.

### 4.3. Elimination of Hardcoding

**User Story:** As an investor, I want to see realistic grades and risk metrics based on actual calculations, not optimistic hardcoded defaults.

#### Acceptance Criteria

1.  THE System SHALL use actual calculated values for all risk metrics (volatility, max drawdown, beta) and never use default values.
2.  THE System SHALL calculate grades for all assets (including alternatives) from their composite scores, never defaulting to "A+".
3.  THE System SHALL use actual composite scores from crew analysis, never defaulting to placeholder values like 0.7 or 0.85.

### 4.4. Error Handling Philosophy: Fail-Fast

**User Story:** As a system operator, I want the system to halt immediately on critical failures, so that we can prevent the generation of incomplete or inaccurate reports that could lead to poor financial decisions.

#### Acceptance Criteria

1.  THE System SHALL raise a `CriticalFlowError` and halt execution upon encountering a critical failure.
2.  Critical failures are defined as: invalid system configuration, failure to load portfolio data, critical schema validation failure, or more than 10% of holdings failing deep analysis.
3.  WHEN a critical failure occurs, the system SHALL generate detailed logs to enable a swift "Stop and Fix" response.

## 5. Analysis & Crew Capabilities

### 5.1. Analysis Capabilities & Tool Usage

**User Story:** As a FinWiz analyst, I want comprehensive analysis capabilities for all asset classes, so that investment decisions are based on complete information.

#### Acceptance Criteria

1.  WHEN analyzing a stock ticker, THE `DeepAnalysisCrew` SHALL perform fundamental analysis (P/E, EPS), 10-K/10-Q SEC filing analysis, and quantitative analysis (beta, Sharpe ratio).
2.  WHEN analyzing an ETF ticker, THE `DeepAnalysisCrew` SHALL retrieve factsheet data (expense ratio, AUM), calculate tracking error, and analyze holdings.
3.  WHEN analyzing a crypto ticker, THE `DeepAnalysisCrew` SHALL retrieve on-chain metrics (TVL, active addresses), analyze tokenomics, and calculate correlation to BTC/ETH.
4.  All crews SHALL use a standardized 0-5 risk scoring methodology and a multi-source sentiment analysis tool.
5.  For underperforming holdings (grade C or lower), an `AlternativeFinder` SHALL match them with A+ opportunities from discovery crews.

### 5.2. Crew Task Configuration

**User Story:** As a developer, I want crew task configurations to be clear and explicit to ensure agents perform as expected.

#### Acceptance Criteria

1.  All `tasks.yaml` files SHALL include a "REQUIRED ENUM VALUES" section to guide agent output.
2.  The instructions SHALL use the format: `"field_name: MUST be one of: value1, value2, value3"`.
3.  Task descriptions SHALL reference the location of their Pantic output schema (e.g., "Read the schema file at docs/schemas/....").

## 6. System-wide & Non-Functional Requirements

### 6.1. Code Quality & Modernization

**User Story:** As a FinWiz developer, I want the codebase to follow modern best practices and standards, so that the system is maintainable, secure, and easy to work on.

#### Acceptance Criteria

1.  All Python files SHALL be kept under 400 lines; larger files must be refactored into smaller, single-responsibility modules.
2.  All tests SHALL use `pytest-mock` exclusively; `unittest.mock` is banned.
3.  All HTML generation SHALL use the BeautifulSoup (`bs4`) library to prevent security risks and improve readability; manual string concatenation for HTML is banned.
4.  All crews SHALL adhere to CrewAI patterns (`@agent`, `@task`, `@crew` decorators, YAML configurations).
5.  The final reporter agent (`investment_reporter`) SHALL have an empty tools list (`tools=[]`) and use the `@final_reporter` decorator.
6.  All public functions SHALL have comprehensive type hints using modern Python 3.12+ syntax (`|` for Union/Optional).
7.  The flow orchestrator SHALL use a structured Pantic model for state management (`self.state`), not an unstructured dictionary (`self.inputs`).

### 6.2. Flow Resilience & Performance

**User Story:** As a FinWiz operator, I want the system to handle failures gracefully and perform efficiently, so that large portfolios can be analyzed reliably.

#### Acceptance Criteria

1.  IF a crew execution fails with a transient error, THE `FinwizFlow` SHALL automatically retry with exponential backoff. If all retries fail, this is considered a holding failure.
2.  The flow SHALL use the `@persist()` decorator to save progress checkpoints to disk, allowing resumption from the last successful step if interrupted.
3.  The system SHALL optimize API calls through tool-level batching and context sharing between tasks.
4.  All I/O-bound tasks SHALL use `async_execution=True` for parallel execution (except for the final task in a sequence).

### 6.3. Testing and Coverage

**User Story:** As a developer, I want a stable and comprehensive test suite to ensure code quality and prevent regressions.

#### Acceptance Criteria

1.  The test suite SHALL run without any import errors or module errors.
2.  Code coverage SHALL be measured, excluding test files, with a target of 80% for all critical modules.
3.  Tests that require fake data SHALL use the `Faker` library.
4.  The test suite SHALL include unit, integration, and end-to-end tests.

### 6.4. Configuration & Management

**User Story:** As a FinWiz administrator, I want configuration to be consistent and managed through feature flags, so that the system can be adapted for different environments.

#### Acceptance Criteria

1.  All critical environment variables SHALL be validated at startup.
2.  All required API keys and configuration options SHALL be documented in `.env.example`.

## 7. Reporting Requirements

### 7.1. Python-Based HTML Generation

**User Story:** As a developer, I want HTML reports to be generated using Python templates (Jinja2) from JSON exports, making the process fast, testable, and deterministic.

#### Acceptance Criteria

1.  All HTML reports SHALL be generated using Jinja2 templates, not AI agents.
2.  The final report SHALL be in professional French, including all analysis sections and A+ discovery opportunities.
3.  The report generation SHALL be a pure Python function that is unit-testable with mock JSON data.

### 7.2. Report Completeness and Accuracy

**User Story:** As a financial analyst, I need the final report to be complete and accurate, with no placeholder data, forged URLs, or missing sections.

#### Acceptance Criteria

1.  The final report SHALL integrate data from all stages: deep analysis, A+ discovery alternatives, and rebalancing recommendations.
2.  All URLs in the report (e.g., for SEC filings) SHALL be valid and point to the correct source documents.
3.  The data availability section of the report SHALL accurately reflect the status of all data sources.
4.  The report SHALL display the correct, calculated grades for all holdings, not fallback values.

## 8. Optional Integrations

### 8.1. Supabase for Caching and RAG

**User Story:** As a FinWiz user, I want analysis results to be cached in a central database to speed up subsequent runs and enable historical analysis.

#### Acceptance Criteria

1.  The system MAY use Supabase for caching analysis results and for vector storage to enable RAG capabilities.
2.  Supabase integration MUST be completely optional and the system must function perfectly without it.
3.  All database operations must be non-blocking (asynchronous) with strict timeouts (e.g., 2 seconds) and a circuit breaker pattern to ensure they never slow down or fail an analysis.