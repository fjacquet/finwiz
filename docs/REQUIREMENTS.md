# Reviewed Requirements: FinWiz Architectural Consolidation

## 1. Introduction

This document provides a unified and consistent set of requirements for the FinWiz platform. It is the result of a comprehensive review of multiple requirement specifications, which were found to have critical contradictions in architectural approach and process flow.

This specification resolves these conflicts by adopting a single, robust architecture:

1. **A Unified `DeepAnalysisCrew`**: A new, single crew is established for the in-depth analysis of individual portfolio holdings (stocks, ETFs, or crypto). This replaces the problematic use of "discovery" crews for single-ticker analysis, which was identified as a root cause of system hangs and instability.
2. **A Corrected Business Logic Flow**: The main execution flow is re-sequenced to follow a logical business process: **Portfolio Analysis → Deep Analysis → Discovery → Rebalancing → Reporting**. This ensures that analysis of existing assets happens *before* discovering new ones.

All requirements from previous documents have been migrated and adapted to align with this clear architectural vision, creating a single source of truth for development.

---

## 2. Glossary

- **FinWiz System**: The AI-powered financial research platform using CrewAI agents for investment analysis.
- **Discovery Crews**: The `StockCrew`, `ETFCrew`, and `CryptoCrew` responsible for screening and identifying "top 10" new investment opportunities. **They are not used for analyzing existing portfolio holdings.**
- **Deep Analysis Crew**: The new, unified `DeepAnalysisCrew` responsible for comprehensive analysis of a **single ticker** from any asset class.
- **Flow Orchestration**: The CrewAI Flow-based execution sequence managing crew dependencies and data passing.
- **Data Integration System**: The components responsible for crew data sharing, consolidation, and freshness validation.
- **Graceful Degradation**: The system's ability to continue operating with partial data when components fail.
- **Feature Flags**: Configuration switches to enable/disable specific features, like deep analysis.

---

## 3. Core Architectural Requirements

### Requirement 3.1: Unified Deep Analysis Crew

A single, unified `DeepAnalysisCrew` shall be created to handle in-depth analysis of any single ticker, regardless of its asset class.

- **3.1.1. Single-Ticker Focus:** The crew must be designed to accept a single `ticker` and its `asset_class` as input and perform a deep analysis on only that asset. It must not enter loops or errors requesting a list of 10 tickers.
- **3.1.2. Dynamic Tool Routing:** The crew shall dynamically select and use the appropriate set of tools (e.g., SEC analysis for stocks, on-chain metrics for crypto) based on the provided `asset_class` parameter.
- **3.1.3. Standardized Output:** The crew's final output must conform to a unified `DeepAnalysisResult` Pydantic schema, including fields for scores (fundamental, technical, risk), a final grade (A+ to F), and data freshness timestamps.
- **3.1.4. Clear Separation of Concerns:** The existing `StockCrew`, `EtfCrew`, and `CryptoCrew` are to be explicitly designated and documented as **discovery-only crews**. Their task descriptions must clearly state their purpose is to "screen and identify top 10 assets."

### Requirement 3.2: Corrected Flow Orchestration

The main execution flow shall be re-architected to follow the logical business sequence.

- **3.2.1. Correct Sequence:** The flow must execute in the following order:
    1. **Phase 1: Validation**: `validate_data_integration`
    2. **Phase 2: Portfolio Analysis**: `check_portfolio` (Analyze what you own)
    3. **Phase 3: Deep Analysis & Update**: `analyze_and_update_portfolio` (Grade holdings, find needs)
    4. **Phase 4: Discovery**: `check_stock`, `check_etf`, `check_crypto` -> `check_investment_discovery` (Find A+ solutions)
    5. **Phase 5: Rebalancing**: `check_portfolio_rebalancing` (Optimize allocations)
    6. **Phase 6: Reporting**: `report` (Present final recommendations)
- **3.2.2. Atomic Portfolio Update:** A single, consolidated flow method, `analyze_and_update_portfolio()`, shall perform deep analysis, match underperforming holdings with alternatives, and update the portfolio review in one atomic operation. This prevents the portfolio from being generated twice.
- **3.2.3. Logical Dependency:** Discovery crews must run *after* portfolio analysis to ensure they can find A+ alternatives for identified needs. Rebalancing must run *after* discovery to incorporate new opportunities.

---

## 4. Detailed Functional Requirements

### Requirement 4.1: Data Integration & Validation

- **4.1.1. Data Consolidation Fix:** The data consolidation system shall be fixed to correctly retrieve all successfully stored crew outputs, ensuring that downstream processes receive actual analysis data, not empty placeholders.
- **4.1.2. Strict Schema Contracts:** All data passed between crews and to the reporter shall be validated against strict Pydantic models (`extra='forbid'`). The reporter must only accept a validated `ReporterInput` schema.
- **4.1.3. Data Freshness Guarantee:** All market data used for analysis must be no older than 24 hours. The system must validate timestamps and attempt to refresh stale data. Analysis based on stale data must be flagged with warnings and reduced confidence scores. Accuracy is prioritized over caching for time-sensitive data like market prices.
- **4.1.4. Ticker Validation:** All crews must use a standardized `TickerExistenceValidationTool` (from `crewai_custom_tools`) to verify symbols against authoritative sources before analysis.

### Requirement 4.2: Analysis Capabilities & Tool Usage

- **4.2.1. Comprehensive Asset-Specific Analysis:** The `DeepAnalysisCrew` must provide analysis tailored to each asset class:
  - **Stocks:** Fundamental analysis (P/E, EPS), 10-K/10-Q SEC filing analysis, technical indicators, and quantitative metrics (beta, Sharpe ratio).
  - **ETFs:** Factsheet data (expense ratio, AUM), tracking error analysis, and holdings breakdown.
  - **Crypto:** On-chain metrics (TVL, active addresses), tokenomics, and correlation to BTC/ETH.
- **4.2.2. Advanced Technical Analysis:** The system shall integrate multi-source technical analysis, including Fibonacci retracements, support/resistance levels, and multi-indicator confluence from the Twelve Data API.
- **4.2.3. Standardized Risk & Sentiment:** All crews must use a standardized 0-5 risk scoring methodology and a multi-source sentiment analysis tool.
- **4.2.4. A+ Alternative Matching:** An `AlternativeFinder` service shall match underperforming holdings (grade C or lower) with A+ opportunities discovered by the discovery crews. These alternatives must be integrated into the portfolio review and final report.
- **4.2.5. Enum Instruction Enforcement:** All task configuration files (`tasks.yaml`) must include a "REQUIRED ENUM VALUES" section that explicitly documents the exact, case-sensitive enum values required for Pydantic schema outputs to prevent validation failures.

### Requirement 4.3: Flow Resilience & Performance

- **4.3.1. Automatic Retries:** The flow shall automatically retry failed crew executions (due to transient network or API errors) using an exponential backoff strategy with jitter.
- **4.3.2. Checkpointing & Resumption:** The flow must use CrewAI's native state persistence (`@persist()`) to save progress after each holding is analyzed. The system must be able to resume an interrupted flow from the last successful checkpoint, skipping already-completed work.
- **4.3.3. Graceful Degradation:** If a holding fails analysis after all retries, the system shall mark it as failed, use fallback data if available, and continue processing the remaining holdings.
- **4.3.4. API Efficiency:** To manage costs without sacrificing accuracy, crews must use tool-level batching (e.g., fetching multiple indicators in one API call) and share data via context between tasks to avoid redundant fetches.
- **4.3.5. Asynchronous Execution:** I/O-bound tasks shall be executed in parallel (`async_execution=True`) where possible to improve performance, while respecting API rate limits.

### Requirement 4.4: Code Quality, Testing & Modernization

- **4.4.1. CrewAI Pattern Compliance:** All crews, including the new `DeepAnalysisCrew`, must adhere to standard CrewAI patterns, using `@agent`, `@task`, `@crew` decorators and YAML configurations.
- **4.4.2. Report Crew Tool Restriction:** The final `ReportCrew` must have its tool list explicitly empty and validated, ensuring it only consolidates data from upstream and makes no external API calls.
- **4.4.3. Test Framework Standardization:** The entire test suite shall be migrated to use `pytest-mock` exclusively, removing all usage of `unittest.mock`. Tests requiring fake data shall use the `Faker` library.
- **4.4.4. Codebase Refactoring:** All Python files exceeding 400 lines shall be refactored into smaller, single-responsibility modules.
- **4.4.5. Secure HTML Generation:** All HTML generation must be migrated to use the `BeautifulSoup` (bs4) library to prevent manual string concatenation and mitigate XSS risks.
- **4.4.6. Structured Flow State:** The entire flow orchestrator state shall be migrated from an unstructured dictionary (`self.inputs`) to a comprehensive Pydantic model (`self.state`) to ensure type safety and maintainability.

### Requirement 4.5: Configuration & Management

- **4.5.1. Feature Flag Control:** Key features, especially deep portfolio analysis and alternative matching, must be controllable via environment variables (e.g., `DEEP_PORTFOLIO_ANALYSIS=true/false`).
- **4.5.2. Standardized Configuration:** All configuration, including API keys and feature flags, shall use a consistent, documented naming convention.

---

## 5. Success Criteria

- **Stability:** The system successfully analyzes large portfolios (50+ holdings) without hangs, infinite loops, or crashes. Deep analysis of a single ticker completes in under 5 minutes.
- **Correctness:** The main flow executes in the specified logical order. Portfolio holdings receive accurate, nuanced grades (A+ to F) based on deep analysis.
- **Completeness:** The final report integrates data from all stages: deep analysis, A+ discovery alternatives, and rebalancing recommendations.
- **Resilience:** The system can successfully resume from an interrupted flow, recovering its progress from a persisted checkpoint.
- **Maintainability:** The codebase is cleaner, with smaller modules, consistent testing patterns, and adherence to CrewAI best practices.
- **Efficiency:** API call volume is optimized through smart batching and context sharing, and overall execution time is reduced through parallelization.
