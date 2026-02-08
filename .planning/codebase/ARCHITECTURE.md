# Architecture

**Analysis Date:** 2026-02-07

## Pattern Overview

**Overall:** Layered Architecture with Functional Pipeline Core + AI Orchestration (Hybrid Python/AI)

**Key Characteristics:**

- Separation of deterministic Python logic ($0 cost) from AI reasoning (variable cost)
- Flow-based orchestration using CrewAI Flow framework with Pydantic state management
- Orchestrator delegation pattern for single-responsibility modules
- Functional programming pipeline for per-holding analysis (pure functions with composition)
- Defensive error handling with graceful degradation and fallback strategies

## Layers

**Presentation Layer:**

- Purpose: HTML report generation and output formatting
- Location: `src/finwiz/reporting/`, `src/finwiz/templates/`
- Contains: Report generators, HTML builders, CSS/JS components, formatters
- Depends on: Schemas (hybrid_analysis, crew_exports), Flow state
- Used by: ReportingOrchestrator (Phase 6 of flow)

**Application Layer (Flow Orchestration):**

- Purpose: Workflow coordination via CrewAI Flow framework
- Location: `src/finwiz/flows/`, `src/finwiz/orchestrators/`
- Contains: FinwizFlow (main coordinator), specialized orchestrators (ValidationOrchestrator, DeepAnalysisOrchestrator, DiscoveryOrchestrator, ReportingOrchestrator, etc.)
- Depends on: Domain layer, Infrastructure layer, Crews
- Used by: Core initialization (`src/finwiz/core/app_initializer.py`)
- Pattern: Lazy-loaded orchestrator properties, dependency injection via OrchestratorDependencies dataclass

**Domain Layer:**

- Purpose: Business logic for financial analysis (Python-first, AI-assisted)
- Location: `src/finwiz/analysis/`, `src/finwiz/scoring/`, `src/finwiz/quantitative/`
- Contains: Functional analysis pipeline, scoring engines (composite: 40% fundamental, 30% technical, 30% risk), quantitative calculations
- Depends on: Schemas, Infrastructure (caching, resilience)
- Used by: DeepAnalysisOrchestrator, crews
- Key files:
  - `src/finwiz/analysis/deep_analysis_pipeline.py` - functional pipeline composition
  - `src/finwiz/scoring/deep_analysis_scorer.py` - composite scoring engine
  - `src/finwiz/scoring/grading_system.py` - grade assignment (A+ to F)

**Integration Layer (Crews + Tools):**

- Purpose: AI crews for qualitative insights and data collection tools
- Location: `src/finwiz/crews/`, `src/finwiz/tools/`
- Contains: CrewAI crews (stock_crew, etf_crew, crypto_crew, deep_analysis, investment_discovery_crew, portfolio_rebalancing_crew, report_crew), Python tools for data fetching
- Depends on: Schemas, Infrastructure, Tool factories
- Used by: CrewFactory (with error handling wrapper)
- Pattern: `@CrewBase` decorator, YAML config files (`config/agents.yaml`, `config/tasks.yaml`)

**Infrastructure Layer:**

- Purpose: Cross-cutting concerns and system-level utilities
- Location: `src/finwiz/infrastructure/`, `src/finwiz/config/`, `src/finwiz/data/`
- Contains: Caching, logging, monitoring (LiteLLM callbacks), resilience (retry decorators, circuit breakers), JSON serialization, time utilities, health checks
- Depends on: Nothing (pure infrastructure)
- Used by: All other layers

**Data Access Layer:**

- Purpose: External API integration and data fetching
- Location: `src/finwiz/data/adapters/`, `src/finwiz/integration/`
- Contains: API clients (Yahoo Finance, Alpha Vantage, TwelveData, CoinMarketCap), data adapters, CrewDataIntegrationManager
- Depends on: Infrastructure (caching, resilience)
- Used by: Tools, Orchestrators

**Schema Layer (Cross-cutting):**

- Purpose: Type-safe data contracts using Pydantic
- Location: `src/finwiz/schemas/`
- Contains: All Pydantic models (hybrid_analysis, crew_exports, quantitative, rebalancing, tools, api, integration)
- Depends on: Nothing (pure data models)
- Used by: All layers
- Key models: FinwizState, DeepAnalysisResult, EnrichedAnalysis, QuantitativeAnalysis, QualitativeInsights

## Data Flow

**Main Analysis Workflow:**

1. **Initialization** (`main.py` → `app_initializer.py`)
   - Validate environment variables
   - Initialize configuration, logging, caching
   - Create FinwizFlow instance with FinwizState

2. **Phase 1: Data Validation** (ValidationOrchestrator)
   - Validate required data sources
   - Check API connectivity
   - Initialize DataAvailabilityTracker

3. **Phase 2: Portfolio Review** (ValidationOrchestrator)
   - Load portfolio holdings from CSV (`data/portfolio_holdings.csv`)
   - Parse holdings into FinwizState.portfolio_holdings
   - Validate ticker symbols

4. **Phase 3: Deep Analysis** (DeepAnalysisOrchestrator → deep_analysis_pipeline)
   - For each holding:
     a. `collect_raw_data(ctx)` - Python tools fetch financial data ($0)
     b. `calculate_quantitative(ctx, raw)` - Python scorer calculates composite score ($0)
     c. `generate_qualitative(ctx, quant)` - AI crew generates insights (~$0.05)
     d. `synthesize_enriched_analysis(ctx, quant, qual)` - Combine results ($0)
   - Store DeepAnalysisResult in flow state
   - Merge with previous analysis if available

5. **Phase 4: Discovery** (DiscoveryOrchestrator - optional)
   - Parallel execution: check_crypto(), check_stock(), check_etf()
   - Consolidate A+ investment opportunities
   - Store in flow state

6. **Phase 5: Alternative Matching** (AlternativesMatchingOrchestrator)
   - Match portfolio holdings with A+ alternatives
   - Calculate opportunity scores

7. **Phase 6: Reporting** (ReportingOrchestrator)
   - Consolidate all analysis results
   - Generate HTML reports (individual + consolidated)
   - Save to `output/` directory

**Per-Holding Analysis Pipeline (Functional):**

```
AnalysisContext(ticker, asset_class, company_name)
  ↓
collect_raw_data(ctx)
  → RawData: {price_data, financial_statements, technical_indicators, news}
  ↓
calculate_quantitative(ctx, raw_data)
  → (DeepAnalysisResult, QuantitativeAnalysis)
  → Composite: 40% fundamental + 30% technical + 30% risk
  → Grade: A+ to F, Score: 0.0 to 1.0
  ↓
generate_qualitative(ctx, quant)
  → QualitativeInsights (AI-generated)
  → {sec_insights, fundamental_context, technical_strategy, contextual_risks, investment_synthesis}
  ↓
synthesize_enriched_analysis(ctx, quant, qual)
  → EnrichedAnalysis
  → Python wins on recommendation conflicts
  → Output: final_grade, final_recommendation, executive_summary
```

**State Management:**

- Flow uses Pydantic FinwizState for type-safe state across phases
- State persisted in memory during flow execution
- CrewDataIntegrationManager stores crew outputs in JSON files (`output/{crew_type}/{ticker}.json`)
- Cache layer stores quantitative results in `cache/quantitative/{ticker}_{asset_class}.json`

## Key Abstractions

**FinwizFlow (Flow Orchestrator):**

- Purpose: Main workflow coordinator using CrewAI Flow framework
- Examples: `src/finwiz/flows/orchestrator.py`
- Pattern: Flow[FinwizState] with @start() and @listen() decorators for phase sequencing
- Delegates to specialized orchestrators via lazy-loaded properties

**Orchestrators (Single-Responsibility Coordinators):**

- Purpose: Focused orchestration modules for specific phases
- Examples:
  - `src/finwiz/orchestrators/validation_orchestrator.py` - input validation, portfolio review
  - `src/finwiz/orchestrators/deep_analysis_orchestrator.py` - per-holding analysis
  - `src/finwiz/orchestrators/discovery_orchestrator.py` - A+ discovery
  - `src/finwiz/orchestrators/reporting_orchestrator.py` - report generation
- Pattern: Each orchestrator receives FinwizState and specialized dependencies

**AnalysisContext (Immutable Analysis Input):**

- Purpose: Type-safe context for functional pipeline
- Examples: `src/finwiz/analysis/deep_analysis_pipeline.py`
- Pattern: @dataclass(frozen=True) with ticker, asset_class, company_name

**DeepAnalysisScorer (Composite Scorer):**

- Purpose: Deterministic Python scoring engine ($0 cost)
- Examples: `src/finwiz/scoring/deep_analysis_scorer.py`
- Pattern: Composite pattern with FundamentalScorer (40%), TechnicalScorer (30%), RiskScorer (30%)

**CrewFactory (Crew Execution with Error Handling):**

- Purpose: Create and execute crews with fallback strategies
- Examples: `src/finwiz/crew_factory.py`
- Pattern: Factory with CoreAnalysisErrorHandler for graceful degradation

**CrewDataIntegrationManager (Crew Output Storage):**

- Purpose: Store and retrieve crew outputs from JSON files
- Examples: `src/finwiz/integration/manager.py`
- Pattern: File-based storage in `output/{crew_type}/{ticker}.json`

## Entry Points

**Main Application:**

- Location: `src/finwiz/main.py`
- Triggers: Command-line execution (`crewai flow kickoff`)
- Responsibilities: Delegates to app_initializer.kickoff()

**Application Initializer:**

- Location: `src/finwiz/core/app_initializer.py`
- Triggers: Called by main.py
- Responsibilities:
  - Validate environment configuration
  - Initialize logging infrastructure
  - Create FinwizFlow instance
  - Execute flow.kickoff()

**FinwizFlow (Main Flow):**

- Location: `src/finwiz/flows/orchestrator.py`
- Triggers: app_initializer calls flow.kickoff()
- Responsibilities:
  - Initialize shared dependencies (OrchestratorDependencies)
  - Lazy-load orchestrators
  - Execute sequential workflow (8 phases)
  - Manage flow state (FinwizState)

**Functional Analysis Pipeline:**

- Location: `src/finwiz/analysis/deep_analysis_pipeline.py`
- Triggers: Called by DeepAnalysisOrchestrator for each holding
- Responsibilities:
  - Compose pure functions for analysis
  - Call AI crew for qualitative insights
  - Return (DeepAnalysisResult, EnrichedAnalysis)

## Error Handling

**Strategy:** Defensive programming with graceful degradation and fallback strategies

**Patterns:**

- **Crew Failure Handling**: CoreAnalysisErrorHandler provides fallback data when crews fail
- **Retry with Exponential Backoff**: create_retry_decorator() in `src/finwiz/infrastructure/resilience/retry.py`
- **Circuit Breakers**: Feature flags in `src/finwiz/config/features/flags.py` disable failing components
- **Validation with Retry**: `src/finwiz/validation/ai_output.py` validates AI outputs with retry on malformed responses
- **Python Fallback**: In MAXIMUM_SPEED mode, AI calls are replaced with Python-generated content
- **None-Safe Defaults**: All crew inputs have defensive None-safe defaults to prevent format string errors

## Cross-Cutting Concerns

**Logging:**

- Approach: Structured logging via `src/finwiz/tools/logger.py`
- Format: `[timestamp] [level] [module] message`
- Destination: `logs/` directory + console
- Configuration: setup_logging() in app_initializer.py

**Validation:**

- Approach: Multi-level validation
  1. Environment validation (API keys, required config)
  2. Template variable validation at startup (crew YAML files)
  3. Input validation (portfolio CSV structure)
  4. AI output validation with retry (malformed JSON)
- Location: `src/finwiz/validation/`, `src/finwiz/cli/argument_parser.py`

**Authentication:**

- Approach: API keys via environment variables
- Required: OPENAI_API_KEY, SERPER_API_KEY
- Optional: ANTHROPIC_API_KEY, PERPLEXITY_API_KEY, ALPHA_VANTAGE_API_KEY, COINMARKETCAP_API_KEY, TWELVE_DATA_API_KEY
- Validation: initialize_environment() in cli/argument_parser.py

**Caching:**

- Approach: File-based JSON caching
- Quantitative Results: `cache/quantitative/{ticker}_{asset_class}.json`
- Portfolio Analysis: `cache/portfolio_analysis/`
- Crew Outputs: `output/{crew_type}/{ticker}.json` (managed by CrewDataIntegrationManager)
- Implementation: `src/finwiz/infrastructure/caching/`

**Monitoring:**

- Approach: LiteLLM callback for token usage tracking
- Implementation: `src/finwiz/infrastructure/monitoring/litellm_callback.py`
- Metrics: Token count, cost estimation, model usage
- Initialization: enable_token_monitoring() in FinwizFlow.**init**()

**Resilience:**

- Approach: Retry decorators, circuit breakers, timeout handling
- Configuration: `src/finwiz/config/resilience_config.py`
- Parameters: max_retries=3, retry_base_delay=1.0s, exponential backoff
- Implementation: `src/finwiz/infrastructure/resilience/`

**Feature Flags:**

- Approach: Environment-based toggles with circuit breakers
- Implementation: `src/finwiz/config/features/flags.py`
- Flags: DEEP_ANALYSIS_ENABLED, PERPLEXITY_RESEARCH_ENABLED, INVESTMENT_DISCOVERY_ENABLED, PORTFOLIO_REBALANCING_ENABLED
- Usage: is_feature_enabled(feature_name) returns bool

---

*Architecture analysis: 2026-02-07*
