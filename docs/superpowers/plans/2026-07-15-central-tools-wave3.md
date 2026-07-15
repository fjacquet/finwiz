# Central Tools Migration — Wave 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship crewai-custom-tools v0.6.0 with a new `tools/analytics/` + `tools/files/` surface (valuation, ETF analytics, regulatory compliance, position sizing, price targets, the A+ grading cluster, file readers), swap finwiz to it, and purge finwiz's dead/placeholder tooling.

**Architecture:** Selective centralization (user decision): only dependency-light code moves — numpy/pandas at most, NO ta-lib/backtrader/QuantLib in central. The quant-library-backed tools (QuantitativeAnalysis, Backtesting), portfolio price service, and `analysis/` orchestration stay in finwiz as domain code (spec delta). Same three-repo order: central release → epic_news additive gate → finwiz swaps. Wrapper pattern only where enrichment exists (none in this wave — these are clean moves).

**Tech Stack:** Python (3.11+ central, 3.13 finwiz), uv, pytest + pytest-mock (unittest.mock BANNED), CrewAI BaseTool, numpy/pandas, yfinance.

## Spec deltas (approved scope corrections)

1. **Stay in finwiz permanently (domain):** `quantitative_analysis_tool` + its 4 analyzer helpers, `backtesting_tool` (thin fronts over `finwiz.quantitative`, whose closure demands ta-lib/backtrader/QuantLib and Python 3.13), `portfolio_price_service`, `portfolio_cache_service`, `analysis/` (flow orchestration), `alternative_finder_tool` (reads finwiz `output/` files — domain glue).
2. **Deleted as noise/dead code (user-approved):** `optimization_tool` + `risk_assessment_tool` (np.random placeholder outputs wired into the investment-discovery crew — agents were consuming random numbers), `chart_analyzer` + `charts/` subdir (zero production callers).
3. **Name collision:** central already has a (simpler) `MarketScreeningTool`. finwiz's universe-screening tool moves as **`APlusScreeningTool`** — factories, tests, and crew yaml prose in finwiz update to the new class/tool name.
4. **Latent bug fixed during the grading move:** `screening_ranking.score_candidates` reads a top-level `composite_score` key the A+ scorer never emits (always fell back to 0.5) — the moved code reads `analysis_summary.composite_score` (or the scorer emits it top-level; pick one, test it).
5. **Schema single-source rule:** models that move to central (`AssetClass`, `PositionSizeRecommendation`, `PriceTargets`, `APlusScore`, screening inputs/results, `MarketRegime`, `ScoringCriteria`) become canonical in `crewai_custom_tools.models.analytics_models`; finwiz's `schemas/portfolio_review.py` / `schemas/tools/` RE-EXPORT them (import-and-reexport, keeping every finwiz import path stable — no consumer churn).

## Global Constraints

- **Envelope contract** for BaseTools moving to central: `_run` returns `ok(data)`/`err(msg)` JSON strings (convert finwiz's `json_ok`/raw-dict/raw-json returns during the move). EXCEPTION: `FileReadTool`/`DirectoryReadTool` keep plain-string returns (their output IS the content agents read; documented exception like the sentiment tools).
- **Plain classes** (`PositionSizingTool`, `PriceTargetCalculator`) move as plain classes with identical public methods — they are programmatic APIs, not agent tools; no envelope.
- **Additive-first for epic_news:** v0.6.0 adds a new surface; nothing epic_news uses changes. Its gate expects ZERO test changes.
- **No new heavy deps in central:** numpy/pandas only (already declared). If a moving module imports anything beyond stdlib+numpy+pandas+yfinance+requests, STOP and report — that's a scope error.
- pytest-mock only; tests offline/pristine; finwiz `make check` green per commit; new files ≤300 lines (split modules accordingly); commit trailer:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
- Central branch `wave3-analytics` from main; finwiz continues on `spec/centralized-tools`. finwiz env note: re-run `uv sync --group docs` after any plain `uv sync`.
- **Read-first rule:** every task reads the current source of each file it touches before editing; the recon line numbers are approximate.

---

## Part A — crewai_custom_tools (Tasks 1–5)

Working directory: `/Users/fjacquet/Projects/crewai_custom_tools`. Before Task 1: `git checkout main && git pull && git checkout -b wave3-analytics`.

### Task 1: `tools/files/` — FileReadTool + DirectoryReadTool

**Files:** Create `src/crewai_custom_tools/tools/files/__init__.py`, `src/crewai_custom_tools/tools/files/file_tools.py`; Test `tests/test_file_tools.py`.

**Interfaces:** Port finwiz's `src/finwiz/tools/file_tools.py` (117 LOC, stdlib-only, drop-in replacements for crewai_tools' readers without the heavy `crewai[tools]` extra) VERBATIM in behavior: `FileReadTool(file_path=None)` with `_run(file_path=None, start_line=1, line_count=None) -> str` (plain string; `"Error: ..."` strings on FileNotFoundError/PermissionError/OSError), `DirectoryReadTool(directory=None)` with `_run(**kwargs) -> str` and the fixed-directory schema swap. Keep class names identical (finwiz Task 7 swaps imports 1:1). Tests: tmp_path-based read/range/missing-file/permission cases + fixed-vs-runtime path behavior.

- [ ] TDD: port tests first (write against the new module path), then the module; full suite; commit `feat(files): port lightweight FileReadTool/DirectoryReadTool from finwiz` + trailer.

### Task 2: `tools/analytics/` — valuation + ETF analytics (with their pure-function engines)

**Files:** Create `src/crewai_custom_tools/tools/analytics/__init__.py`, `analytics/price_targets.py` (port of finwiz `quantitative/price_targets.py`, 569 LOC pure functions), `analytics/valuation.py` (`ValuationTool`), `analytics/etf_metrics.py` (port of finwiz `quantitative/etf/etf_metrics.py`, 522 LOC pure functions), `analytics/etf_analysis.py` (`ETFAnalysisTool`); `src/crewai_custom_tools/models/analytics_models.py` (new; `ValuationInput`, `ETFAnalysisInput` moved from finwiz schemas). Tests: `tests/test_analytics_valuation.py`, `tests/test_analytics_etf.py`.

**Interfaces:**

- Read finwiz's `valuation_tool.py` (200) + `etf_analysis_tool.py` (226) first. Both keep their `_run` signatures; returns CONVERT to central `ok()`/`err()` envelopes (finwiz returned `json_ok`/raw `json.dumps` — both agent-facing only, no programmatic parsers per recon §4, so the envelope change is safe).
- The pure-function modules port verbatim minus finwiz imports (`finwiz.tools.logger` → `logging.getLogger`); verify they import nothing beyond numpy/pandas/stdlib (STOP if they do).
- finwiz's factory functions (`get_valuation_tool`, `get_etf_analysis_tool`) are NOT ported — finwiz's factories will construct the classes directly.

- [ ] TDD per tool (port the meaningful cases from finwiz's tests if any exist — recon says valuation/etf_analysis had NO dedicated tests, so write fresh ones: happy path with mocked yfinance/pure-function inputs, error envelope path); full suite; one commit per tool or one combined `feat(analytics): valuation and ETF analytics tools with pure-function engines` + trailer.

### Task 3: `tools/analytics/` — regulatory compliance + position sizing + price targets

**Files:** Create `analytics/regulatory_compliance.py` (`RegulatoryComplianceTool`), `analytics/position_sizing.py` (`PositionSizingTool` + `PortfolioContext`, `HoldingSizingProfile`), `analytics/price_target_calculator.py` (`PriceTargetCalculator` + `PriceHistory`, `FundamentalData`); extend `models/analytics_models.py` (`RegulatoryComplianceInput`, `AssetClass`, `PositionSizeRecommendation`, `PriceTargets` — ported from finwiz `schemas/portfolio_review.py` / `schemas/tools/`). Tests: `tests/test_analytics_compliance.py`, `tests/test_analytics_sizing_targets.py`.

**Interfaces:**

- `RegulatoryComplianceTool._run(symbol, jurisdictions=None, include_risk_assessment=True, include_compliance_status=True) -> str` — finwiz returned a raw dict; CONVERT to envelope (agent-facing only, one crypto-bundle consumer: finwiz factory swap handles it).
- `PositionSizingTool` / `PriceTargetCalculator`: plain classes, public methods and pydantic return models IDENTICAL (finwiz's rebalancing crew calls `calculate_position_size(...)`, `validate_portfolio_allocations(...)`, `calculate_targets(...)` programmatically — signature stability is the contract).
- Port finwiz's dedicated tests for sizing/targets (they exist, no mocks — pure logic) into the central suite.

- [ ] TDD; full suite; commit `feat(analytics): regulatory compliance, position sizing, price target calculator` + trailer.

### Task 4: `tools/analytics/` — the A+ grading cluster

**Files:** Create `analytics/scoring_algorithms.py` + `analytics/scoring_criteria.py` (port of finwiz `tools/scoring/`, 532 LOC), `analytics/grading.py` (port of `finwiz/scoring/grading_system.py` `score_to_grade` — read it first; port only what the cluster uses), `analytics/a_plus_scoring.py` (`APlusScoringTool`), `analytics/screening_criteria.py`, `analytics/screening_utils.py` (555 LOC — SPLIT if >300 lines per the file-size rule; its `finwiz.infrastructure.caching.manager.cache_key` import is replaced by central's `config/cache.py` equivalent or an inline key builder — read both and pick the smallest change), `analytics/screening_ranking.py`, `analytics/aplus_screening.py` (**`APlusScreeningTool`** — finwiz's `MarketScreeningTool` renamed; give it a distinct `.name` string, e.g. `"aplus_screening"`, since central's simpler `market_screening` already exists); extend `models/analytics_models.py` (`APlusScore`, `APlusScoringInput`, `MarketRegime`, `ScoringCriteria`, `APlusScreeningInput` (renamed), `MarketScreeningResult`). Tests: port finwiz's `test_a_plus_scoring_tool.py` + `test_market_screening_tool.py` cases; add a regression test for the composite_score bug.

**Interfaces:**

- `APlusScoringTool._run(...)` — finwiz returned a raw dict consumed programmatically by `screening_ranking` (`._a_plus_scorer._run(...)`); CONVERT to envelope AND adapt `screening_ranking` internally (`parse_tool_result`). **Fix the latent bug here:** `score_candidates`' detailed path must read the composite score from where the scorer actually puts it — and a test must pin it (a candidate with a known composite ≠ 0.5 must NOT score 0.5).
- `APlusScreeningTool._run(asset_type, screening_criteria=None, market_region="global", max_candidates=50, min_a_plus_score=0.85, include_detailed_analysis=False) -> str` (envelope; finwiz returned raw dict, agent-facing only).
- These modules may import yfinance/requests (screening_utils does) — allowed; nothing heavier.

- [ ] TDD; full suite; commit `feat(analytics): A+ grading cluster (scoring, screening, APlusScreeningTool); fix composite_score fallback bug` + trailer.

### Task 5: Exports + release v0.6.0

**Files:** `src/crewai_custom_tools/tools/analytics/__init__.py` + `tools/files/__init__.py` aggregators; top-level `__init__.py` imports + `__all__` (FileReadTool, DirectoryReadTool, ValuationTool, ETFAnalysisTool, RegulatoryComplianceTool, PositionSizingTool, PriceTargetCalculator, APlusScoringTool, APlusScreeningTool — plain classes exported too, but note only BaseTool subclasses register on MCP); `pyproject.toml` + `__init__` version 0.6.0; `uv lock`; test_scaffold version assertion; CHANGELOG (`## [0.6.0] - <today>`: new analytics/files surface, APlusScreeningTool naming, composite_score fix, deliberate plain-string exception for file tools).

- [ ] Full suite + export smoke (`python -c "from crewai_custom_tools import ValuationTool, APlusScreeningTool, FileReadTool; print('ok')"`); MCP registration sanity (`tests/test_mcp_server.py` passes — new tools must construct with `cls()`); commit, merge --no-ff to main, annotated tag v0.6.0, push with tags; verify tag via `gh api`.

---

## Part B — epic_news (Task 6)

### Task 6: Pin bump v0.6.0 (additive gate)

Same procedure as the v0.5.1 bump (temp worktree from origin/main; baseline → bump → identical failure set → commit pin+lock only → push → both workflows green; the `test_get_project_root` worktree artifact in both runs counts as matching). ZERO test edits expected; any new failure = central regression → BLOCKED.

---

## Part C — finwiz (Tasks 7–11)

### Task 7: Bump pin + file_tools swap

**Files:** `pyproject.toml`+`uv.lock` (pin → v0.6.0); `tool_factories.py:12`, `crews/investment_discovery_crew/investment_discovery_crew.py:23`, `crews/portfolio_rebalancing_crew/portfolio_rebalancing_crew.py:26`, `crews/report_crew/report_crew.py:30` (imports → `from crewai_custom_tools import DirectoryReadTool, FileReadTool`); `tests/unit/tools/test_tool_factories.py` patch targets (import-site patching keeps working — verify); DELETE `src/finwiz/tools/file_tools.py` (+ its test file if dedicated).

- [ ] Bump → smoke import → swap → orphan sweep (`file_tools`) → `make check` → commit.

### Task 8: Valuation + ETF analysis swap

**Files:** `tool_factories.py` (`get_valuation_tool`/`get_etf_analysis_tool` imports at :11,:19 → construct central classes directly, e.g. `ValuationTool()`; keep the factory-function seam inside tool_factories if simpler — read it), `crews/deep_analysis/tool_routing.py:92-93` (same); DELETE `src/finwiz/tools/valuation_tool.py`, `etf_analysis_tool.py`, `src/finwiz/quantitative/price_targets.py`, `src/finwiz/quantitative/etf/etf_metrics.py` — the last two ONLY after a grep proves the moved tools were their sole consumers (recon says yes for price_targets; etf_metrics also feeds `quantitative_comprehensive_analyzer._fetch_etf_specific_data`? VERIFY — if any surviving consumer exists, the module STAYS and central keeps its own copy; document which).

- Schema note: `ValuationInput`/`ETFAnalysisInput` lived inline/schemas — orphan-check and re-export per the single-source rule if anything else imports them.

- [ ] Swap → deletions with verification greps → tests (envelope: these were agent-facing; factory tests only assert presence) → `make check` → commit.

### Task 9: Compliance + sizing + targets swap (with schema re-export shim)

**Files:** `finance_tools.py:32,:93` (RegulatoryComplianceTool from central), `crews/portfolio_rebalancing_crew/portfolio_rebalancing_crew.py:52-54` (PriceTargetCalculator, PositionSizingTool from central), `orchestrators/` consumers per recon §4; `src/finwiz/schemas/portfolio_review.py` becomes a RE-EXPORT for `AssetClass`, `PositionSizeRecommendation`, `PriceTargets` (`from crewai_custom_tools.models.analytics_models import AssetClass, ...` — every finwiz import path stays valid; the classes are now central's); DELETE `src/finwiz/tools/regulatory_compliance_tool.py`, `position_sizing_tool.py`, `price_target_calculator.py` (+ their tests, which moved centrally in Task 3).

- CAUTION: `schemas/portfolio_review.py` contains models that DON'T move (`Alternative`, `Grade`, ...) — only re-export the moved three; the rest stay defined locally. Pydantic identity: since finwiz re-exports the same class objects, isinstance checks and validation stay coherent.

- [ ] Swap → shim → deletions → focused tests (`test_position_sizing_tool.py`/`test_price_target_calculator.py` deleted with the code; rebalancing-crew and orchestrator tests must pass UNCHANGED) → `make check` → commit.

### Task 10: Grading cluster swap

**Files:** `finance_tools.py` (:23 APlusScoringTool, :30 MarketScreeningTool→`APlusScreeningTool`, :139-146, :163-170, :208 instantiations + alias), `discovery/candidate_scorer.py:16-17` + `discovery/universe_provider.py:15` (central imports), `tools/__init__.py` (lazy exports update); crew yaml prose sweep: `grep -rn "Market Screening\|market_screening\|A+ Scoring\|APlusScoring\|a_plus" src/finwiz/crews --include="*.yaml"` — update any prose naming the old tool name strings to the new central names (the W2-T8 etf_crew lesson: LLM-facing prose must match real tool names); DELETE `a_plus_scoring_tool.py`, `market_screening_tool.py`, `screening_criteria.py`, `screening_utils.py`, `screening_ranking.py`, `tools/scoring/` subdir (+ moved tests); orphan-check `finwiz/scoring/grading_system.py` (if the deep-analysis scorer still uses it, it STAYS — only the cluster's usage moved).

- `screening_ranking`'s programmatic consumers (`candidate_scorer` uses `calculate_preliminary_score`) now import central's — verify signature parity.

- [ ] Swap → yaml sweep → deletions with greps → tests (discovery tests re-pointed; investment-discovery comprehensive test's patch targets move to central module paths with envelope-wrapped `_run` mocks) → `make check` → commit.

### Task 11: Noise/dead-code purge + debt sweep + wave gates

**Files/actions:**

- DELETE `optimization_tool.py` + `risk_assessment_tool.py` (np.random placeholders): remove from `investment_discovery_crew.py` (:30,:34, `_get_portfolio_tools`, `validation_agent`) and `tools/__init__.py`; yaml prose sweep for their tool-name strings in investment_discovery config; note in commit body this is deliberate noise removal (agents were receiving random numbers).
- DELETE `chart_analyzer.py` + `charts/` subdir + `tests/unit/tools/test_chart_analyzer.py` (zero production callers — re-verify grep first).
- Debt sweep (accumulated minors): stale docs referencing `TickerValidationTool` (`docs/explanations/python_pipeline/troubleshooting.md`, `docs/reference/api/tools.md` — fix to `TickerExistenceValidationTool` central import); delete production-orphaned `KRAKEN_BASE`/`COINBASE_BASE` from `config/endpoints.py` if tests are their only consumers (else leave); delete `integration/freshness_validated_tool.py` (W1-final-review orphan; re-verify zero consumers); delete `PerplexitySearchWrapperInput` from schemas if still orphaned; drop the dead `data.get("answer")` fallback in `perplexity_analysis_integration._parse_perplexity_response` OR route `_execute_search_with_retry` through the central tool (read first; pick the smaller correct change).
- Extend `tests/unit/tools/test_central_tools_contract.py`: stock bundle contains central `ValuationTool`-by-name; discovery bundle contains `APlusScreeningTool`; file tools importable from central.
- Gates: `make check && make coverage` (≥65%); exit checklist (central v0.6.0 tagged+pushed; epic_news green; no deleted-module references; no `tool.uv.sources` committed).

- [ ] Purge with per-deletion verification greps → sweep → contract tests → gates → commit `refactor(tools): Wave-3 noise purge and debt sweep` + trailer.

---

## Post-wave

Whole-wave final review (three repos, most capable model) → triage → PR update (the finwiz branch already feeds PR #97; Wave 3 rides the same PR unless the user says otherwise). Wave 4 (final cleanup: finwiz rate limiter/api_decorators deletion, api_key_validation, orphaned cache service, then the `crewai flow kickoff` baseline comparison) becomes a small closing plan.
