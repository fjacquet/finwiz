# Codebase Structure

**Analysis Date:** 2026-02-07

## Directory Layout

```console
finwiz/
├── src/finwiz/           # Main source code
│   ├── main.py           # Application entry point
│   ├── flow_state.py     # Pydantic flow state models
│   ├── crew_factory.py   # Crew creation with error handling
│   ├── core/             # Bootstrap and initialization
│   ├── flows/            # CrewAI Flow orchestration
│   ├── orchestrators/    # Specialized orchestration modules
│   ├── analysis/         # Functional analysis pipeline
│   ├── scoring/          # Python scoring engines ($0 cost)
│   ├── crews/            # AI crews for qualitative insights
│   ├── tools/            # Data collection and analysis tools
│   ├── schemas/          # Pydantic models (all data contracts)
│   ├── quantitative/     # Quantitative finance calculations
│   ├── reporting/        # HTML report generation
│   ├── data/             # Data access layer
│   ├── infrastructure/   # Cross-cutting concerns
│   ├── integration/      # Crew data integration management
│   ├── config/           # Configuration and settings
│   ├── validation/       # Input and output validation
│   ├── exceptions/       # Custom exceptions
│   ├── utils/            # Utility functions
│   ├── cache/            # Caching logic
│   ├── cli/              # Command-line interface
│   ├── api/              # API endpoints (if any)
│   └── templates/        # Jinja2 templates for reports
├── tests/                # Test suite
│   ├── unit/             # Unit tests (mirrors src structure)
│   ├── integration/      # Integration tests
│   ├── fixtures/         # Test data fixtures
│   └── conftest.py       # Pytest configuration
├── data/                 # Input data files
│   └── portfolio_holdings.csv  # Portfolio to analyze
├── output/               # Generated reports and crew outputs
│   ├── portfolio/        # Consolidated reports
│   ├── stock/            # Stock crew outputs
│   ├── etf/              # ETF crew outputs
│   ├── crypto/           # Crypto crew outputs
│   └── discovery/        # Discovery crew outputs
├── cache/                # Cached quantitative results
│   ├── quantitative/     # Python scoring cache
│   └── portfolio_analysis/  # Portfolio analysis cache
├── logs/                 # Application logs
├── config/               # External configuration files
├── docs/                 # Documentation (MkDocs)
├── scripts/              # Utility scripts
├── .env                  # Environment variables (not committed)
├── .env.example          # Example environment configuration
├── pyproject.toml        # Project dependencies and config
├── uv.lock               # UV lockfile
├── Makefile              # Build and test commands
└── CLAUDE.md             # Project instructions for Claude
```

## Directory Purposes

**src/finwiz/ (Root Package):**

- Purpose: Main application package
- Contains: Entry points, core abstractions, factory classes
- Key files:
  - `main.py`: CLI entry point
  - `flow_state.py`: Pydantic state models (FinwizState, DeepAnalysisResult)
  - `flow_state_models.py`: State model definitions
  - `flow_state_utils.py`: State utility functions
  - `crew_factory.py`: Crew creation with error handling wrapper

**src/finwiz/core/:**

- Purpose: Application bootstrapping and initialization
- Contains: Startup logic, configuration validation
- Key files:
  - `app_initializer.py`: Main initialization sequence (kickoff())

**src/finwiz/flows/:**

- Purpose: CrewAI Flow orchestration
- Contains: FinwizFlow (main coordinator), flow utilities
- Key files:
  - `orchestrator.py`: FinwizFlow class with 8-phase workflow
  - `hybrid_analysis_synthesizer.py`: Analysis result synthesis

**src/finwiz/orchestrators/:**

- Purpose: Specialized orchestration modules (single-responsibility)
- Contains: ValidationOrchestrator, DeepAnalysisOrchestrator, DiscoveryOrchestrator, ReportingOrchestrator, ErrorHandlingOrchestrator, ProgressTrackingOrchestrator, UtilityOrchestrator
- Subdirectories:
  - `orchestrators/discovery/`: Discovery orchestration and extractors
  - `orchestrators/error_handling/`: Error handling strategies
  - `orchestrators/extraction/`: Data extraction utilities
  - `orchestrators/portfolio_review/`: Portfolio review logic
  - `orchestrators/registry/`: Orchestrator registry
  - `orchestrators/validation/`: Validation helpers
  - `orchestrators/registry/`: Orchestrator registry (v2 — eliminates circular imports)
- Key files:
  - `validation_orchestrator.py`: Input validation, portfolio review
  - `deep_analysis_orchestrator.py`: Per-holding analysis coordination
  - `discovery_orchestrator.py`: A+ discovery coordination
  - `reporting_orchestrator.py`: Report consolidation
  - `deep_analysis_data_collector.py`: Data collection for analysis

**src/finwiz/analysis/:**

- Purpose: Functional analysis pipeline (pure functions with composition)
- Contains: Pipeline functions (collect, calculate, generate, synthesize)
- Key files:
  - `deep_analysis_pipeline.py`: Main functional pipeline with analyze_holding()

**src/finwiz/scoring/:**

- Purpose: Deterministic Python scoring engines ($0 cost)
- Contains: Composite scorer, component scorers, grading system
- Subdirectories:
  - `scoring/asset_analyzers/`: Asset-specific analyzers
- Key files:
  - `deep_analysis_scorer.py`: Composite scorer (40% fund, 30% tech, 30% risk)
  - `fundamental_scorer.py`: Fundamental analysis scorer
  - `technical_scorer.py`: Technical analysis scorer
  - `risk_scorer.py`: Risk analysis scorer
  - `grading_system.py`: Grade assignment (A+ to F)
  - `thresholds.py`: Scoring thresholds configuration

**src/finwiz/crews/:**

- Purpose: AI crews for qualitative insights
- Contains: CrewAI crew classes with @CrewBase decorator
- Subdirectories (each crew):
  - `crews/{crew_name}/config/`: agents.yaml, tasks.yaml
  - `crews/{crew_name}/{crew_name}.py`: Crew class
- Crews:
  - `stock_crew/`: Stock analysis crew
  - `etf_crew/`: ETF analysis crew
  - `crypto_crew/`: Crypto analysis crew
  - `deep_analysis/`: Deep analysis crew (generic)
  - `investment_discovery_crew/`: A+ opportunity discovery
  - `portfolio_rebalancing_crew/`: Rebalancing recommendations
  - `report_crew/`: Final report generation
  - `helpers/`: Shared crew utilities

**src/finwiz/tools/:**

- Purpose: Data collection and analysis tools
- Contains: API clients, data fetchers, analysis tools
- Subdirectories:
  - `tools/analysis/`: Analysis tools
  - `tools/charts/`: Chart generation
  - `tools/etf/`: ETF-specific tools
  - `tools/reporting/`: Reporting utilities
  - `tools/scoring/`: Scoring tools
  - `tools/sentiment/`: Sentiment analysis
  - `tools/twelve_data/`: TwelveData API client
- Key files:
  - `tool_factories.py`: Factory functions for crew tools
  - `yahoo_finance_*.py`: Yahoo Finance API tools
  - `alpha_vantage_tool.py`: Alpha Vantage API client
  - `enhanced_sec_tool.py`: SEC filing analysis
  - `perplexity_search_tool.py`: Perplexity API integration

**src/finwiz/schemas/:**

- Purpose: Pydantic models for all data contracts
- Contains: Type-safe data models
- Subdirectories:
  - `schemas/hybrid_analysis/`: EnrichedAnalysis, QuantitativeAnalysis, QualitativeInsights
  - `schemas/api/`: API request/response models
  - `schemas/tools/`: Tool input/output models
  - `schemas/quantitative/`: Quantitative data models
  - `schemas/rebalancing/`: Rebalancing models
  - `schemas/integration/`: Integration models
- Key files:
  - `crew_exports.py`: Crew output schemas
  - `integration_models.py`: Data integration models

**src/finwiz/quantitative/:**

- Purpose: Quantitative finance calculations
- Contains: Backtesting, optimization, risk metrics, technical indicators, performance analysis
- Subdirectories:
  - `quantitative/technical/`: Technical indicators (RSI, MACD, etc.)
  - `quantitative/etf/`: ETF-specific metrics
  - `quantitative/risk/`: Risk calculations
- Key files:
  - `backtesting.py`: Backtesting engine
  - `optimization.py`: Portfolio optimization
  - `risk_metrics.py`: Risk calculations
  - `performance_metrics.py`: Performance analytics
  - `technical.py`: Technical analysis

**src/finwiz/reporting/:**

- Purpose: HTML report generation
- Contains: Report generators, HTML builders, CSS/JS components
- Subdirectories:
  - `reporting/css/`: CSS styles
  - `reporting/js/`: JavaScript code
  - `reporting/rebalancing/`: Rebalancing report components
- Key files:
  - `final_report_generator.py`: Main consolidated report
  - `deep_analysis_report_generator.py`: Per-holding reports
  - `consolidator.py`: Report consolidation logic

**src/finwiz/data/:**

- Purpose: Data access layer and external API integration
- Contains: API clients, data adapters
- Subdirectories:
  - `data/adapters/`: Data transformation adapters
- Key files: API-specific data access modules

**src/finwiz/infrastructure/:**

- Purpose: Cross-cutting concerns and system utilities
- Contains: Caching, logging, monitoring, resilience, JSON utilities
- Subdirectories:
  - `infrastructure/caching/`: Cache implementations
  - `infrastructure/logging/`: Structured logging
  - `infrastructure/monitoring/`: LiteLLM token tracking
  - `infrastructure/resilience/`: Retry decorators, circuit breakers
  - `infrastructure/json/`: JSON serialization utilities
  - `infrastructure/time/`: Time utilities
  - `infrastructure/decorators/`: Decorator utilities
  - `infrastructure/health/`: Health checks

**src/finwiz/integration/:**

- Purpose: Crew data integration management
- Contains: CrewDataIntegrationManager, CrewDataAccessor, DataAvailabilityTracker
- Key files:
  - `manager.py`: CrewDataIntegrationManager (crew output storage)
  - `accessor.py`: CrewDataAccessor (read crew outputs)
  - `availability.py`: DataAvailabilityTracker (data staleness checking)

**src/finwiz/config/:**

- Purpose: Configuration management
- Contains: Settings, feature flags, resilience config, LLM config
- Subdirectories:
  - `config/features/`: Feature flag system
  - `config/llm/`: LLM configuration
  - `config/performance/`: Performance settings
- Key files:
  - `settings.py`: Main configuration
  - `features/flags.py`: Feature flag system (is_feature_enabled())
  - `resilience_config.py`: Retry and circuit breaker config
  - `batch_prefetch_config.py`: Batch data prefetch settings

**src/finwiz/validation/:**

- Purpose: Input and output validation
- Contains: Template validation, AI output validation
- Key files:
  - `template.py`: YAML template variable validation
  - `ai_output.py`: AI response validation with retry

**tests/:**

- Purpose: Comprehensive test suite
- Contains: Unit tests, integration tests, fixtures
- Subdirectories mirror src/finwiz/ structure
- Key files:
  - `conftest.py`: Shared pytest fixtures
  - `conftest_unittest_blocker.py`: Blocks unittest.mock imports (pytest-mock only)
  - `fixtures/`: Faker-based test data generators

## Key File Locations

**Entry Points:**

- `src/finwiz/main.py`: CLI entry point (imports kickoff from app_initializer)
- `src/finwiz/core/app_initializer.py`: Main bootstrap logic (kickoff())
- `src/finwiz/flows/orchestrator.py`: FinwizFlow class (main workflow coordinator)

**Configuration:**

- `.env`: Environment variables (API keys, feature flags)
- `.env.example`: Example configuration
- `pyproject.toml`: Project dependencies, tool configuration (ruff, mypy, pytest)
- `src/finwiz/config/settings.py`: Application settings
- `src/finwiz/config/features/flags.py`: Feature flags

**Core Logic:**

- `src/finwiz/analysis/deep_analysis_pipeline.py`: Functional analysis pipeline
- `src/finwiz/scoring/deep_analysis_scorer.py`: Composite scoring engine
- `src/finwiz/crew_factory.py`: Crew execution with error handling
- `src/finwiz/integration/manager.py`: Crew data storage and retrieval

**Testing:**

- `tests/conftest.py`: Shared test fixtures
- `tests/unit/`: Unit tests (mirrors src structure)
- `tests/integration/`: Integration tests (requires API keys)
- `Makefile`: Test commands (make test, make coverage, make check)

**Documentation:**

- `README.md`: Project overview
- `CLAUDE.md`: Project-specific instructions for Claude
- `docs/`: MkDocs documentation site
- `AGENTS.md`: Legacy agent documentation

## Naming Conventions

**Files:**

- **Pattern**: snake_case.py (all lowercase with underscores)
- **Examples**:
  - `deep_analysis_pipeline.py` (analysis module)
  - `validation_orchestrator.py` (orchestrator)
  - `crew_factory.py` (factory)
  - `app_initializer.py` (initializer)

**Directories:**

- **Pattern**: snake_case (all lowercase with underscores)
- **Examples**:
  - `deep_analysis/` (crew directory)
  - `hybrid_analysis/` (schema subdirectory)
  - `error_handling/` (orchestrator subdirectory)

**Functions:**

- **Pattern**: snake_case (all lowercase with underscores)
- **Examples**:
  - `analyze_holding()` (main entry point)
  - `collect_raw_data()` (pipeline function)
  - `calculate_quantitative()` (pipeline function)
  - `is_feature_enabled()` (utility function)

**Classes:**

- **Pattern**: PascalCase (capitalized words, no underscores)
- **Examples**:
  - `FinwizFlow` (main flow)
  - `DeepAnalysisScorer` (scorer)
  - `CrewFactory` (factory)
  - `ValidationOrchestrator` (orchestrator)

**Variables:**

- **Pattern**: snake_case (all lowercase with underscores)
- **Examples**:
  - `crew_factory` (instance)
  - `integration_manager` (dependency)
  - `raw_data` (data variable)

**Constants:**

- **Pattern**: UPPER_SNAKE_CASE (all uppercase with underscores)
- **Examples**:
  - `MAXIMUM_SPEED` (mode constant - though not widely used in codebase)

**Pydantic Models:**

- **Pattern**: PascalCase (like classes)
- **Examples**:
  - `FinwizState` (flow state)
  - `EnrichedAnalysis` (analysis result)
  - `QualitativeInsights` (AI output)
  - `DeepAnalysisResult` (cached result)

**Crew Names:**

- **Pattern**: snake_case_crew (directory and module name)
- **Examples**:
  - `stock_crew/` → `StockCrew` class
  - `deep_analysis/` → `DeepAnalysisCrew` class
  - `investment_discovery_crew/` → `InvestmentDiscoveryCrew` class

**Configuration Files:**

- **Pattern**: lowercase with hyphens or underscores
- **Examples**:
  - `agents.yaml` (crew config)
  - `tasks.yaml` (crew config)
  - `pyproject.toml` (project config)
  - `.env.example` (environment template)

## Where to Add New Code

**New Feature:**

- Primary code:
  - Domain logic: `src/finwiz/analysis/` or `src/finwiz/scoring/`
  - Orchestration: `src/finwiz/orchestrators/`
  - Tools: `src/finwiz/tools/`
- Tests: `tests/unit/{corresponding_module}/`
- Schemas: `src/finwiz/schemas/` (if new data contracts needed)

**New Crew:**

- Implementation: `src/finwiz/crews/{crew_name}/`
- Structure:
  - `{crew_name}.py`: Crew class with @CrewBase
  - `config/agents.yaml`: Agent definitions
  - `config/tasks.yaml`: Task definitions
- Factory integration: Add execution method in `src/finwiz/crew_factory.py`
- Tests: `tests/unit/crews/{crew_name}/`

**New Orchestrator:**

- Implementation: `src/finwiz/orchestrators/{orchestrator_name}_orchestrator.py`
- Integration: Add lazy-loaded property in `src/finwiz/flows/orchestrator.py`
- Tests: `tests/unit/orchestrators/`

**New Tool:**

- Implementation: `src/finwiz/tools/{tool_name}_tool.py`
- Factory registration: Add to `src/finwiz/tools/tool_factories.py`
- Tests: `tests/unit/tools/`
- Schemas (if needed): `src/finwiz/schemas/tools/`

**New Schema:**

- Implementation: `src/finwiz/schemas/{domain}/` (create subdirectory if needed)
- Pattern: Use Pydantic BaseModel
- Location guidelines:
  - Analysis results: `schemas/hybrid_analysis/`
  - Crew outputs: `schemas/crew_exports.py`
  - Tool I/O: `schemas/tools/`
  - Quantitative data: `schemas/quantitative/`
  - API models: `schemas/api/`

**Utilities:**

- Shared helpers: `src/finwiz/utils/`
- Infrastructure utilities: `src/finwiz/infrastructure/{category}/`
- Test utilities: `tests/fixtures/` or `tests/conftest.py`

**Configuration:**

- Feature flags: `src/finwiz/config/features/flags.py`
- Settings: `src/finwiz/config/settings.py`
- Domain config: `src/finwiz/config/{config_name}_config.py`

**Reports:**

- Report generators: `src/finwiz/reporting/{report_type}_report_generator.py`
- HTML components: `src/finwiz/reporting/{category}/`
- Templates: `src/finwiz/templates/`

## Special Directories

**cache/:**

- Purpose: File-based caching for quantitative results
- Generated: Yes (at runtime)
- Committed: No (.gitignore)
- Structure:
  - `cache/quantitative/{ticker}_{asset_class}.json`
  - `cache/portfolio_analysis/`

**output/:**

- Purpose: Generated reports and crew outputs
- Generated: Yes (at runtime)
- Committed: No (.gitignore)
- Structure:
  - `output/portfolio/`: Consolidated HTML reports
  - `output/stock/`: Stock crew JSON outputs
  - `output/etf/`: ETF crew JSON outputs
  - `output/crypto/`: Crypto crew JSON outputs
  - `output/discovery/`: Discovery crew JSON outputs

**logs/:**

- Purpose: Application logs
- Generated: Yes (at runtime)
- Committed: No (.gitignore)
- Files: Timestamped log files

**data/:**

- Purpose: Input data files
- Generated: No (manually created)
- Committed: Example files only
- Key files:
  - `data/portfolio_holdings.csv`: Portfolio to analyze

**docs/:**

- Purpose: MkDocs documentation site
- Generated: Manually written + auto-generated
- Committed: Yes
- Build: `mkdocs build` → `site/`

**site/:**

- Purpose: Built MkDocs documentation
- Generated: Yes (by mkdocs build)
- Committed: No (.gitignore)

**scripts/:**

- Purpose: Utility scripts for development
- Generated: No (manually created)
- Committed: Yes
- Examples: Data generation, analysis helpers

**.planning/:**

- Purpose: Codebase documentation for GSD commands
- Generated: By GSD map-codebase command
- Committed: Yes
- Files: ARCHITECTURE.md, STRUCTURE.md, STACK.md, etc.

**.serena/:**

- Purpose: Serena MCP cache and memories
- Generated: Yes (by Serena MCP)
- Committed: No (.gitignore)

**.claude/:**

- Purpose: Claude-specific configuration and old agent definitions
- Generated: No (manually created)
- Committed: Yes
- Note: Contains legacy agent definitions (now deprecated)

**checkpoints/:**

- Purpose: Flow checkpoints (if used)
- Generated: Yes (by CrewAI Flow)
- Committed: No (.gitignore)

---

*Structure analysis: 2026-02-07 (updated 2026-02-08 after v2)*
