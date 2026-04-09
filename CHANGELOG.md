# Changelog

All notable changes to the FinWiz project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Token optimization (ADR-007)** -- Pruned ~10K tokens of YAML boilerplate across all 7 crews: removed 33 redundant JSON OUTPUT blocks, 11 ANTI-HALLUCINATION blocks, 8 "Read schema" instructions, and compressed 25+ agent backstories to ~15 words each
- **LLM max_tokens caps** -- Added response length limits per model type (standard: 2048, mini: 1024, manager: 1024, planning: 2048, baseline: 4096) to prevent unbounded output; configurable via `LLM_MAX_TOKENS` env var
- **Deep analysis max_tokens** -- Increased to 4096 to accommodate structured JSON output requiring 1500-2000 words

### Fixed

- **risk_factors schema** -- Added field_validator to `SecAnalysisInsights` to coerce LLM dict responses (`{'risk': '...', 'severity': '...'}`) to plain strings, preventing Pydantic validation failures
- **LLM cache key** -- Include `max_tokens` in cache key to prevent callers with different token limits from receiving the wrong cached instance

### Added

- **Pre-call token guard** -- LiteLLM callback now logs error when estimated prompt tokens exceed configurable `MAX_PROMPT_TOKENS` threshold (default: 100K)
- **CrewAI usage_metrics logging** -- Token consumption per crew logged after each execution for cost visibility
- **ADR-007** -- Token Consumption Optimization architecture decision record

## [0.2.0] - 2026-03-29

### Added

- **MacroScorer**: New component scorer wiring macro-economic data into the composite scoring pipeline (40% fundamental, 30% technical, 30% risk)
- **Sentiment & Macro report sections**: Wire sentiment summary, macro dashboard, and economic calendar sections into the per-holding enriched analysis report
- **EconomicCalendar schemas**: New `EconomicCalendar` Pydantic models and adapter with feature-flag guard
- **Report enrichment pipeline**: Persist `sentiment_summary` in enriched JSON; add macro overlay and calendar section generators
- **Per-holding sentiment rendering**: Dedicated sentiment section in deep analysis HTML report
- Comprehensive CLAUDE.md documentation for all 12 major subfolders (crews, flows, tools, schemas, quantitative, orchestrators, reporting, utils, data, integration, scoring, validation)

### Changed

- **Major Refactoring** — Split 13 large files (600–1682 lines) into 40+ focused modules
  - `deep_analysis_orchestrator.py` (1,682 → 4 modules): data_collector, executor, processor
  - `deep_analysis_scorer.py` (1,178 → 3 modules): score_result_builder, crew_export_generator
  - `hybrid_analysis_flow.py` (1,042 → 3 modules): data_collector, synthesizer
  - `quantitative_analysis_tool.py` (649 → 5 modules): technical, backtesting, performance analyzers
  - `report_consolidator.py` (646 → 3 modules): export_loaders, html_collector
  - `schemas/quantitative/models.py` (643 → 7 domain files): backtesting, data, enums, portfolio, risk, screening, technical
  - `supabase/client.py` (641 → 6 modules): config, health, metrics, operations, pool
  - `registry_manager.py` (624 → 5 modules): models, data_retrieval, execution, storage
  - `flow_state.py` (620 → 4 modules): models, analysis, utils
- Applied functional programming patterns (list comprehensions, itertools, operator module)
- Centralized exception hierarchy in `exceptions/` module
- Circuit breaker now configurable via `ResilienceConfig`
- Holding analysis timeout increased to 600 s to accommodate deep analysis workloads
- Upgraded all dependencies (`uv.lock`)

### Fixed

- **CI: memory constraint test** — Mock `peak_memory` so `test_should_validate_memory_constraints_when_within_limit` is deterministic and no longer fails on loaded CI runners (#11)
- **CI: notification quiet-hours test** — Mock quiet-hours logic to prevent timezone-dependent failures in CI (#10)
- Force-exit after flow completion to prevent thread-pool hang on process exit
- ROE validation relaxed; `beta=1.0` accepted; NaN guarded in backtesting calculations
- `data_extractor.py`: Fallback to `final_grade`/`final_score` when AI crews emit those keys instead of `grade`/`composite_score`
- `python_report_generator.py`: Handle `None` grade to prevent `'NoneType' has no attribute 'lower'` error
- Dead code: Prefixed 8 unused parameters with underscore (vulture 100% confidence)
- Security: `MD5` hash flagged with `usedforsecurity=False` (bandit high-severity)
- Lint: 10 ruff issues resolved (unused imports, unsorted imports)

## [0.1.0] - 2025-12-07

### Added

- Initial FinWiz platform release
- CrewAI-based multi-agent financial analysis system
- Stock, ETF, and cryptocurrency analysis crews
- Portfolio review and rebalancing functionality
- A+ investment discovery system
- Deep per-holding analysis with Python scoring
- Hybrid Python/AI analysis architecture
- Quantitative analysis with Backtrader, TA-Lib, QuantLib, PyPortfolioOpt
- Batch processing for high-performance portfolio analysis (10-20x speedup)
- HTML report generation with Jinja2 templates
- RAG (Retrieval-Augmented Generation) integration
- Multi-source data fetching with fallback strategies

### Core Crews

- `StockCrew` - Stock fundamental and technical analysis
- `EtfCrew` - ETF factsheet and holdings analysis
- `CryptoCrew` - Cryptocurrency on-chain metrics
- `DeepAnalysisCrew` - Per-holding comprehensive analysis
- `InvestmentDiscoveryCrew` - A+ opportunity discovery
- `PortfolioRebalancingCrew` - Portfolio optimization
- `ReportCrew` - Final consolidated report generation

### AI Minimalism Implementation

- Python-based scoring engine (100% cost reduction vs AI)
- Jinja2 template-based report generation
- Deterministic calculations for reproducibility
- AI reserved for analysis requiring reasoning

### Testing

- pytest with pytest-mock (no unittest.mock)
- Faker for test data generation
- 65% minimum coverage requirement
- Type checking with mypy

---

## Changelog Maintenance

Claude should maintain this changelog by:

1. **Adding entries** when implementing new features or fixing bugs
2. **Categorizing changes** under appropriate headers:
   - `Added` - New features
   - `Changed` - Changes in existing functionality
   - `Deprecated` - Soon-to-be removed features
   - `Removed` - Removed features
   - `Fixed` - Bug fixes
   - `Security` - Security-related changes
3. **Including context** - Brief description of what changed and why
4. **Referencing issues/PRs** when applicable

### Example Entry

```markdown
### Fixed
- Resolved JSON serialization error in crew exports by adding `default=str` to all `json.dumps()` calls
- Fixed mock path errors in tests by patching at import location rather than definition
```
