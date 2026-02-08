# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

```bash
# Run full portfolio analysis
crewai flow kickoff

# Install dependencies
uv sync

# Unit tests (default, excludes integration)
make test

# All quality checks (lint + test + unittest.mock check + docs validation)
make check

# Run a single test
uv run pytest tests/unit/tools/test_yahoo_finance_tool.py::test_name -v -s

# Code quality
make lint                              # ruff check --fix + ruff format
make format                            # same as lint
make mypy                              # uv run mypy src/finwiz

# Coverage (65% minimum threshold)
make coverage
```

## Project Overview

FinWiz is an AI-powered financial analysis platform built with CrewAI. It analyzes portfolios of stocks, ETFs, and crypto using a hybrid approach: deterministic Python scoring ($0, <100ms) for quantitative analysis, and AI crews for qualitative insights only.

## Architecture

### Layered Structure

```
Presentation (reporting/, templates/)
    ↓
Application (flows/, orchestrators/)
    ↓
Domain (schemas/, scoring/, analysis/)
    ↑
Infrastructure (data/, cache/, integration/)
```

### Execution Flow

```
main.py → core/app_initializer.py → flows/orchestrator.py (FinwizFlow)
                                          │
                                          ├── Phase 1: Data Validation (ValidationOrchestrator)
                                          ├── Phase 2: Portfolio Review (ValidationOrchestrator)
                                          ├── Phase 3: Deep Analysis per holding
                                          │     └── analysis/deep_analysis_pipeline.py
                                          │           1. collect_raw_data()     [Python tools, $0]
                                          │           2. calculate_quantitative() [Python scorer, $0]
                                          │           3. generate_qualitative()  [AI crew, ~$0.05]
                                          │           4. synthesize()           [Python, $0]
                                          ├── Phase 4: Discovery (crypto/stock/etf crews)
                                          ├── Phase 5: Alternative Matching
                                          └── Phase 6: Reporting (ReportingOrchestrator)
```

### Key Components

| Component | Location | Role |
|-----------|----------|------|
| Main flow | `flows/orchestrator.py` → `FinwizFlow(Flow[FinwizState])` | Coordinates all phases via orchestrator delegation |
| Flow state | `flow_state.py` → `FinwizState` (Pydantic) | Type-safe state shared across flow phases |
| Crew factory | `crew_factory.py` → `CrewFactory` | Creates crews with error handling and fallback |
| Analysis pipeline | `analysis/deep_analysis_pipeline.py` | Functional pipeline: Python scoring + AI insights |
| Scoring engine | `scoring/deep_analysis_scorer.py` → `DeepAnalysisScorer` | Composite: 40% fundamental, 30% technical, 30% risk |
| Tool factories | `tools/tool_factories.py` | `get_stock_crew_tools()`, `get_etf_crew_tools()`, etc. |
| Feature flags | `config/features/flags.py` → `is_feature_enabled()` | Environment-based feature toggles with circuit breakers |
| Schemas | `schemas/` | All Pydantic models (hybrid_analysis, crew_exports, etc.) |

### Crew Pattern

Each crew lives in `crews/<name>/` with `config/agents.yaml`, `config/tasks.yaml`, and a crew class using `@CrewBase`. Crews are: `stock_crew`, `etf_crew`, `crypto_crew`, `deep_analysis`, `investment_discovery_crew`, `portfolio_rebalancing_crew`, `report_crew`.

### Orchestrator Delegation

`FinwizFlow` delegates to lazy-loaded orchestrators in `orchestrators/`:

- `ValidationOrchestrator` - input validation, portfolio review
- `DeepAnalysisOrchestrator` - per-holding analysis
- `DiscoveryOrchestrator` - A+ investment discovery
- `AlternativesMatchingOrchestrator` - alternative matching
- `ReportingOrchestrator` - report consolidation, HTML generation
- `ErrorHandlingOrchestrator` - crew failure handling
- `ProgressTrackingOrchestrator` - metrics

## Critical Rules

- **unittest.mock is BANNED** - Use pytest-mock only (`mocker.patch()`). Enforced by ruff and `make check-unittest-mock`.
- **json.dumps** - Always use `default=str` to handle datetime and other non-serializable types.
- **File size** - Max 300 lines per file. Split larger files into focused modules.
- **Pydantic models** - All models go in `schemas/`, not in domain folders.
- **Final reporters** - Report crew agents must have `tools=[]` and use `@final_reporter` decorator.
- **Flow methods** - Must return `dict[str, Any]`.
- **self.inputs** - NEVER use in flows (deprecated). Use `self.state` for all state access.
- **Tool instantiation** - Use factory functions from `tools/tool_factories.py`, never instantiate tools directly.
- **AI Minimalism** - Use Python for deterministic tasks (scoring, data collection, synthesis). AI only for qualitative reasoning. When Python and AI disagree, Python wins.
- **Line length** - 180 characters (configured in ruff).

## Testing

- Fixtures use Faker for data generation (`tests/fixtures/`)
- Shared fixtures in `tests/conftest.py` (stock_data, etf_data, crypto_data, etc.)
- `tests/conftest_unittest_blocker.py` blocks unittest.mock imports at runtime
- Markers: `integration`, `unit`, `slow`, `asyncio`, `performance`, `benchmark`, `crew`, `flow`
- Default pytest run excludes integration tests (`-m "not integration"`)
- Coverage reports to `htmlcov/`, minimum 65%

## Environment Variables

```bash
OPENAI_API_KEY=...              # Required
SERPER_API_KEY=...              # Required
# Optional: ANTHROPIC_API_KEY, PERPLEXITY_API_KEY, ALPHA_VANTAGE_API_KEY, etc.
# Feature flags: DEEP_ANALYSIS_ENABLED, PERPLEXITY_RESEARCH_ENABLED
# Validation: VALIDATION_STRICTNESS=off|warn|error
```
