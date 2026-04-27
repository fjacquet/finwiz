# Changelog

All notable changes to the FinWiz project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] - 2026-04-27

### Fixed

- **Phase 3 lost successfully-completed work** -- The 1800s aggregate timeout
  (`GLOBAL_PHASE_TIMEOUT` / `FINWIZ_PHASE_TIMEOUT` env var) was wrapping the
  per-holding `asyncio.gather` and discarding every already-completed future
  when it fired. A run on 2026-04-27 had XRP-USD finish cleanly at 09:00:12
  (grade=D, rec=SELL, 92.3s) but its result was thrown away when the
  aggregate timeout fired 4½ minutes later. With 60+ holdings, an outer cap
  is the wrong abstraction — it punishes work that already succeeded when
  one slow ticker pushes total runtime over. **The aggregate timeout has
  been removed entirely.** `PER_HOLDING_TIMEOUT` (600s default,
  `FINWIZ_HOLDING_TIMEOUT`) remains the only safety cap; total runtime now
  scales naturally with N. The gather now uses `return_exceptions=True` so
  one holding's exception doesn't poison siblings.
- **Phase 3 runner crashes were silent** -- Codex P1 catch on PR #22:
  `run_deep_analysis_concurrent` exceptions (executor init, asyncio loop,
  config errors) used to be caught, logged, and the orchestrator returned
  `{"error": ...}` — letting the flow continue and report success. Now the
  orchestrator updates state then re-raises so the failure can never go
  silent. The `flows/orchestrator.py` try/except wrapper still ensures
  cost/cache summaries fire on the failure path.
- **Single source of truth for Phase 3 fail-loud** -- Removed the duplicate
  fail-loud check in `flows/orchestrator.py:run_sequential_workflow` (the
  v0.3.0 location wasn't on every flow code path). The orchestrator now
  raises `RuntimeError` directly on 0 results — independent of which flow
  path called it.

## [0.3.0] - 2026-04-27

### Fixed

- **Deep analysis silent-failure → trust crisis (DELL B+ → D panic)** -- A portfolio kickoff produced 0 deep analyses for 62 of 63 holdings yet reported `"✅ FinWiz analysis workflow completed successfully"`. The hidden `DEEP_PORTFOLIO_ANALYSIS` env-var kill switch defaulted to `"false"` and silently no-op'd Phase 3, then the placeholder `grade="D"` / `composite_score=0.6` from `decisions.py` rendered as a real verdict in the report. Three layers of fixes: (1) DELETED the kill switch — deep analysis ALWAYS runs because financial trust requires it; (2) honest success accounting via `_failed_holdings` tracker + `deep_analysis_coverage` tuple on `FinwizState`, plus flow-level `RuntimeError` when 0 analyses produced for N>0 holdings; (3) reporting layer truthfully renders unanalyzed holdings as `⏳ Analyse en attente` (new `Grade="N/A"` literal) with `composite_score` reset to 0.0 so downstream consumers don't see fabricated 0.6.
- **Coverage banner on the executive summary** -- New green/amber/red banner showing actual `analyzed/total` ratio. Red includes the explicit warning **"NE PAS prendre de décisions sur ce rapport"** when 0 holdings analyzed. Average portfolio score now ignores N/A holdings so a 1/63 kickoff can't fabricate a portfolio-wide score from placeholder noise.
- **Date-anchored AI prompts** -- Every AI prompt (CrewAI deep_qualitative_analysis_task + the four Perplexity strategic prompts in `analysis/strategic_research.py`) now opens with the current date in long French form (e.g. `26 avril 2026`). The model is explicitly told that its training data may be outdated for corporate structure (acquisitions, divestitures, partnerships) and that "récent" means the 12 months preceding `{current_date}`. Resolves the DELL-still-owns-VMware class of hallucination (Dell sold VMware in November 2021).
- **OpenRouter mid-stream drops** -- Set `litellm.num_retries=3` at module import time in `config/llm/llm_config.py`. CrewAI's `LLM(...)` constructor doesn't expose num_retries (verified), so the litellm module-level global is the only working hook. Catches `httpcore.RemoteProtocolError` / "incomplete chunked read" / `APIError` 502/503/504 with built-in exponential backoff. Tunable via `LLM_NUM_RETRIES` env var (default: 3, with defensive parse for empty/garbage values).

### Changed

- **Qualitative crew now has bounded Perplexity access** -- `asset_analyst` in `crews/deep_analysis/` was running in zero-tool mode, which left it relying on training memory for corporate facts (cause of the DELL/VMware hallucination). Added `PerplexitySearchTool` with strict in-prompt caps: max 2 calls per holding, reserved for material facts (current corporate structure, recent leadership changes, major events in last 12 months), forbidden for already-provided Python data (scores/metrics). Web search wins over model memory whenever they conflict. Token-overflow risk mitigated by the call cap.

### Removed

- **Dependency cleanup** -- Dropped 16 unused runtime packages and 2 redundant wrappers from `pyproject.toml`. Removed: `firecrawl-py`, `serpapi`, `tavily-python` (no tool actually imported them), `supabase`, `asyncpg` (no persistence layer wired), `qdrant-client`, `faiss-cpu`, `sec-edgar-downloader`, `eod`, `perplexityai`, `quandl`, `statsmodels`, `trio`, `rumdl`. Redundant wrappers: `dotenv` (duplicate of `python-dotenv`), `bs4` (duplicate of `beautifulsoup4`). `uv.lock` shrank by ~250 lines / 35 packages including transitive trees.
- **`FIRECRAWL_API_KEY` env var** -- The `Firecrawl` `APIKeyConfig` entry, validation rule, and sanitizer entry were removed alongside the `firecrawl-py` package. Setting the env var is now a no-op. Documentation updated in `USER_GUIDE.md`, `setup_environment.md`, `tutorials/USER_GUIDE.md`, and `tutorials/getting_started.md`.

### Changed

- **Dev/docs dependency reorganization** -- Moved `ruff`, `pytest-asyncio`, and the five `mkdocs*` packages out of `[project.dependencies]` into the `[dependency-groups]` `dev` and `docs` blocks where they belong. Runtime `uv sync` no longer installs lint/test/docs tooling.

### Added

- **Options-implied scenario probabilities** -- Scenario probability bars (bull/base/bear) are now derived from market-implied data via Black-Scholes N(d₂) applied to yfinance options chains. Picks the expiry closest to 90 days, interpolates IV at +20% (bull) and -15% (bear) strikes. Fallback chain: options-implied → AI-provided → Python composite-score formula. Crypto and niche ETFs without liquid options use the Python fallback. Configurable via `RISK_FREE_RATE` env var (default: 0.045).
- **Recommendation conflict notice** -- When Python quantitative score and AI qualitative recommendation disagree, an amber warning box is shown in the HTML report (Python still wins; conflict is surfaced for transparency).
- **Python-computed scenario probabilities fallback** -- When AI omits `scenario_probabilities`, Python derives them from `composite_score` and `risk_score` (deterministic, $0), preventing "non disponible" display in scenario cards.

### Changed

- **Token optimization (ADR-007)** -- Pruned ~10K tokens of YAML boilerplate across all 7 crews: removed 33 redundant JSON OUTPUT blocks, 11 ANTI-HALLUCINATION blocks, 8 "Read schema" instructions, and compressed 25+ agent backstories to ~15 words each
- **LLM max_tokens caps** -- Added response length limits per model type (standard: 2048, mini: 1024, manager: 1024, planning: 2048, baseline: 4096) to prevent unbounded output; configurable via `LLM_MAX_TOKENS` env var
- **Deep analysis max_tokens** -- Increased to 4096 to accommodate structured JSON output requiring 1500-2000 words; further raised to 6144 to reduce token-pressure truncation of `investment_synthesis` prose
- **QualitativeInsights field ordering** -- `investment_synthesis` moved to first position in schema so LLM fills the most user-visible section before token budget runs out (zero-cost change, transparent to all callers)

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
