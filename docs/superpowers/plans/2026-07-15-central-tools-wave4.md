# Central Tools Migration — Wave 4 Implementation Plan (final cleanup)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete finwiz's now-redundant tool infrastructure (async rate limiter, api_decorators, api_key_validation, no-op retry chain, orphaned bases), clean stale config/docs, and run the deferred `crewai flow kickoff` baseline acceptance.

**Architecture:** finwiz-only wave — NO central release, NO epic_news gate (central v0.6.0 already provides every replacement: sync bounded rate limiter, `require_api_key`). Executes after Wave 3 ships, on whatever branch succeeds `wave3-tools`. Every deletion is verification-grep-gated (the W3-T8 `price_targets` precedent: a grep that finds a live consumer means KEEP + report).

**Tech Stack:** Python 3.13, uv, pytest + pytest-mock (unittest.mock BANNED), asyncio.

## Recon verdicts this plan is built on (2026-07-15, commit ad26652f)

- `infrastructure/decorators/api_decorators.py`: **fully orphaned** (zero importers; itself the last consumer of `rate_limiter.with_rate_limit`).
- `infrastructure/resilience/rate_limiter(.config).py`: **2 live async consumers** — `tools/analysis/analysis_coordinator.py:9,62-64,130` (YAHOO_FINANCE pacing) and `integration/batch_data_prefetcher.py:38,100,433` (ALPHA_VANTAGE pacing).
- `tools/api_key_validation.py`: **3 live consumers** — alpha_vantage_tool:54, twelve_data_tool:48, twelve_data_multi_indicator_tool:47 (fail-fast in `model_post_init`).
- `tools/crewai_retry_patch.py`: documented **no-op** (llm_config.py:46-49 — the patch target `Agent._get_llm` no longer exists); called from `cli/argument_parser.py:59` and `tests/validation/stock_crew_validation.py:33`. `tools/llm_retry.py`'s ONLY consumer is this no-op.
- `tools/base_tools.py` (AsyncFeedbackTool) and `tools/tool_result.py` (ToolResult): **test-only orphans**.
- `tools/portfolio_cache_service.py`, `robust_tool_wrapper.py`, `run_helpers.py`, `_text_chunking.py`: **LIVE — stay** (documented spec delta: cache service keeps its single price-service consumer).
- `config/endpoints.py` test-only constants: `COINGECKO_BASE`, `COINBASE_BASE`, `KRAKEN_BASE`, `GNEWS_BASE`, `FRED_BASE`; `CHART_IMG_BASE` orphaned once W3-T11's charts/ purge lands.
- Stale pyproject entries: ruff per-file-ignores for deleted `etf_analysis_tool.py`, `screening_ranking.py`, `scoring/scoring_algorithms.py`, `scoring/scoring_criteria.py` (+ `api_decorators.py` after Task 1); coverage-omit for deleted `perplexity_search_tool.py`.
- `src/finwiz/tools/CLAUDE.md` directory tree lists many deleted files.
- Baseline for acceptance: full Jun 30 2026 22:47 run exists (`output/finwiz_family_financial_plan.html` + per-asset reports).

## Global Constraints

- Verification grep BEFORE every deletion; live consumer found ⇒ KEEP + report.
- Async contexts must not block the event loop: central's rate-limiter `acquire` is sync-blocking — async call sites wrap it in `asyncio.to_thread`.
- pytest-mock only; `make check` green per commit; trailer on every commit:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
- After plain `uv sync`, re-run `uv sync --group docs`.
- The acceptance run (Task 5) spends real API money — it is **user-gated**: prepare everything, then STOP and ask before kickoff.

---

### Task 1: Replace finwiz's async rate limiter with central's bounded limiter; delete the stack

**Files:** Modify `src/finwiz/tools/analysis/analysis_coordinator.py`, `src/finwiz/integration/batch_data_prefetcher.py`; Delete `src/finwiz/infrastructure/resilience/rate_limiter.py`, `rate_limiter_config.py`, `src/finwiz/infrastructure/decorators/api_decorators.py`, `tests/unit/infrastructure/resilience/test_rate_limiter.py`, `test_rate_limiter_config_v4.py`; Modify `pyproject.toml` (drop `aiolimiter` dep if nothing else uses it — grep first; drop the api_decorators ruff ignore at ~:192).

**Interfaces:** The two call sites currently `await limiter.acquire(APIProvider.X)` / `wait_for_availability`. Replacement pattern (read each site; keep pacing semantics):

```python
from crewai_custom_tools.core.rate_limiter import get_rate_limiter

await asyncio.to_thread(get_rate_limiter().acquire, "YahooFinance")  # coordinator
await asyncio.to_thread(get_rate_limiter().acquire, "AlphaVantage")  # prefetcher
```

Central provider strings: "YahooFinance", "AlphaVantage" (registry-backed, bounded by CREWAI_TOOLS_RATE_LIMIT_MAX_WAIT). Premium-tier env vars (`ALPHA_VANTAGE_PREMIUM`, `TWELVE_DATA_PREMIUM`) are already honored by central — finwiz loses no behavior. Any RateLimiter attribute the coordinator exposes (`orchestrator.rate_limiter` — a perf test asserts non-None) must be adapted or the assertion updated (read `test_holding_analyzer_orchestrator_performance.py:55`).
Tests: adapt coordinator/prefetcher tests (patch central's `get_rate_limiter` at the import site); `make check`.

### Task 2: Swap `validate_api_key` → central `require_api_key`; delete the module

**Files:** Modify the three wrappers (alpha_vantage_tool.py, twelve_data_tool.py, twelve_data_multi_indicator_tool.py): `validate_api_key("X_KEY", self.__class__.__name__)` → `require_api_key("X_KEY", tool_name=self.__class__.__name__)` (`from crewai_custom_tools.core.keys import require_api_key`) — same ValueError semantics, `_safe_init` untouched; Delete `src/finwiz/tools/api_key_validation.py` + `tests/unit/tools/test_api_key_validation.py` (central's `tests/test_keys.py` covers the helper). Fail-fast tests for the wrappers stay and must pass unchanged.

### Task 3: Delete the no-op retry chain

**Files:** Delete `src/finwiz/tools/crewai_retry_patch.py`, `src/finwiz/tools/llm_retry.py` (+ any dedicated tests); Modify `src/finwiz/cli/argument_parser.py` (~:12, :59 — remove import + call), `tests/validation/stock_crew_validation.py` (~:16, :33 — same); `pyproject.toml`: drop the crewai_retry_patch ruff ignore (~:226) and the llm_retry + any retry-related coverage-omit entries.

**Verify the no-op claim first** (don't trust the recon alone): read `config/llm/llm_config.py:46-49` and confirm `Agent._get_llm` doesn't exist in the installed crewai (one `uv run python -c "from crewai import Agent; print(hasattr(Agent, '_get_llm'))"`). If it EXISTS again (crewai re-added it), STOP and report — the patch may be live.

### Task 4: Orphan deletions + config/docs hygiene

**Files:**

- Delete `src/finwiz/tools/base_tools.py` + `tests/unit/tools/test_base_tools.py`; `src/finwiz/tools/tool_result.py` + `tests/unit/tools/test_tool_result.py` (verify test-only status with fresh greps).
- `src/finwiz/config/endpoints.py`: delete `COINGECKO_BASE`, `COINBASE_BASE`, `KRAKEN_BASE`, `GNEWS_BASE`, `FRED_BASE`, and `CHART_IMG_BASE` (verify charts/ is gone post-W3-T11) + their assertions in `tests/unit/config/test_endpoints*.py`.
- `pyproject.toml`: remove stale ruff per-file-ignores (etf_analysis_tool, screening_ranking, scoring/scoring_algorithms, scoring/scoring_criteria — confirm each file MISSING first) and the `perplexity_search_tool.py` coverage-omit.
- `src/finwiz/tools/CLAUDE.md`: refresh the Directory Structure tree to the actual post-W3/W4 file list (recon §10 has the full inventory; also fix `sec_tool.py`→`enhanced_sec_tool.py`, drop deleted entries, add missing present ones like `etf/etf_analyzers.py`); update the Infrastructure section (no more retry patch/base_tools/tool_result).
- Extend `tests/unit/tools/test_central_tools_contract.py`: central `require_api_key` importable; central rate-limiter registry has "YahooFinance"/"AlphaVantage" entries (pins Task 1's dependency).
- W3 final-review follow-ups (all finwiz-side, triage-confirmed): delete `CriteriaOptimizationInput` schema + its test (verify orphan with fresh grep — no production consumer as of ef43643); fix `docs/schemas/ValidatedTicker.schema.json:3` stale path (module migrated to central); consolidate the `quantitative/price_targets.py` fork — point `quantitative/tactical_pricing.py:24` at central's byte-identical `calculate_support_resistance_targets` and delete the local module IF the swap is clean, else document the fork as deliberate in the module docstring.
- Gates: `make check && make coverage` (≥65%).

### Task 5: Deferred acceptance — baseline `crewai flow kickoff` comparison (USER-GATED)

- [ ] Preserve the baseline: `cp -r` the Jun 30 artifacts (at minimum `output/finwiz_family_financial_plan.html`, `output/{stock,etf,crypto}/`) to `output_baseline_20260630/` (outside `output/`).
- [ ] Clean `output/` (the stale-enriched-data trap: the report generator silently reuses `*_enriched.json` — a clean dir is mandatory for an honest comparison).
- [ ] **STOP — ask the user to authorize the run** (real API spend). On go: `crewai flow kickoff`, then compare: report generated end-to-end; per-asset reports present for the same tickers; no tool-related errors in `output/run_ledger/`; spot-diff 2-3 reports vs baseline for structural parity (prices/dates will differ; sections/graphs/tool-sourced fields must not be empty or "N/A"-degraded).
- [ ] Record results in the ledger; regressions become fix tasks before the wave ships.

---

## Post-wave

Opus whole-wave review (per user's standing model preference) → PR. **Migration complete:** spec Waves 1-4 all delivered; remaining follow-up backlog lives in the ledger's minor-findings sections (candidates for the Pass-2/3 simplification leads).
