# Design: Migrate FinWiz Tools to Centralized crewai-custom-tools

**Date:** 2026-07-14
**Status:** Approved design, pending implementation plan
**Repos involved:** `crewai_custom_tools` (library), `finwiz` (consumer), `epic_news` (consumer)

## Goal

Replace finwiz's local tool implementations with the centralized
[`crewai-custom-tools`](https://github.com/fjacquet/crewai-custom-tools) package,
pushing every reusable tool upstream so finwiz keeps only its product-specific
code. epic_news (already a consumer at `v0.3.1`) must never break silently;
where a breaking change is deliberate, its fix ships in the same wave.

## Decisions Made

| Decision | Choice |
|---|---|
| Scope | Maximum centralization: all overlapping tools swap to central; generic analytics, grading, and generic leftovers move upstream |
| Drift resolution | finwiz features port upstream FIRST (central becomes a superset); no feature loss on swap |
| Dependency form | Git tag pin in `pyproject.toml` + documented `[tool.uv.sources]` editable override for local co-development |
| Boundary | finwiz keeps only French reports, flow glue, factories, logger, Perplexity integration satellites |
| Tests | Unit tests move with the code; finwiz keeps thin contract tests at the factory seam |
| Migration strategy | Phased, category-by-category, both repos green at every step (Approach 1) |

## Architecture

```
crewai_custom_tools  (single source of truth for reusable tools)
        ▲                    ▲
        │ git tag pin        │ git tag pin (exists: v0.3.1)
     finwiz               epic_news
```

- finwiz declares `crewai-custom-tools @ git+https://github.com/fjacquet/crewai-custom-tools.git@v0.4.0`
  (first adoption tag; bumped each wave).
- Local co-development uses a `[tool.uv.sources]` editable override pointing at
  `/Users/fjacquet/Projects/crewai_custom_tools`; the committed state is always the git tag pin.
- `tool_factories.py` and `finance_tools.py` remain finwiz's composition seam: crews keep
  calling `get_stock_crew_tools()` etc. unchanged; only imports inside the bundles flip.
- No compatibility shims in finwiz: all direct import sites are rewritten to
  `from crewai_custom_tools import ...` (finwiz has no external consumers).

## Tool Inventory

### Swap to existing central equivalents (~20 tools)

Yahoo Finance ×5 (TickerInfo, History, CompanyInfo, News, ETFHoldings), KrakenTickerInfo,
AlphaVantage ×2 (note: finwiz `AlphaVantageCompanyOverviewTool` = central `AlphaVantageOverviewTool`),
TwelveData ×2 (Indicator, MultiIndicator), ChartImg, TickerExistenceValidation,
EnhancedETFAnalysis, EnhancedCryptoAnalysis, EnhancedSECAnalysis, DeFiMetrics,
MarketScreening, StandardizedRiskScoring, StandardizedSentimentAnalysis,
CrossAssetSentimentComparator, PerplexitySearch, PerplexityStructured.

Central versions have drifted (simpler signatures, no batch mode). Each category is
reconciled upstream to finwiz's current behavior before finwiz swaps.

### Move upstream (new in central)

- Analytics: Backtesting, Optimization, RiskAssessment, PositionSizing,
  PriceTargetCalculator, Valuation, QuantitativeAnalysis, RegulatoryCompliance,
  AlternativeFinder, ETFAnalysis, ChartAnalyzer
- Grading: APlusScoring + `screening_criteria.py` / `screening_utils.py` / `screening_ranking.py`
- Generic leftovers: `file_tools` (DirectoryRead/FileRead), `portfolio_price_service`
  (adopts central's SHA-256 TTL cache)
- Dependency closures (support code for migrating tools): `etf/`, `twelve_data/`,
  `sentiment/`, `charts/` subdirectories
- Infrastructure: finwiz rate limiter → `crewai_custom_tools.core.rate_limiter`;
  tool input schemas (e.g. `GetTickerInfoInput`) → `crewai_custom_tools.models`

### Stays in finwiz

- French HTML report/rebalancing/scenario generators (~2,980 lines — product output)
- `tool_factories.py` + `finance_tools.py` (composition seam)
- Perplexity integration satellites (`perplexity_analysis_integration.py`, logging/errors/
  performance modules) — domain glue that calls the central tool
- `analysis/`, `scoring/`, `reporting/` subdirs (flow orchestration + DeepAnalysisScorer helpers)
- `logger.py` (172 import sites, project-wide infra)
- `portfolio_cache_service` — dies in cleanup wave if orphaned once price service moves

## Upstream Changes to crewai_custom_tools

1. **Batch mode (additive):** Yahoo tools gain `prefetched_data: dict | None = None`;
   default reproduces current behavior.
2. **Perplexity signature (sanctioned break):** central adopts finwiz's signature
   `_run(query, model="sonar-pro", top_k=5, search_recency=None, search_domain_filter=None)`.
   epic_news's two call sites are fixed in the same wave (`recency` → `search_recency`).
3. **Rate limiter:** ported from `finwiz.infrastructure.resilience.rate_limiter` into
   `crewai_custom_tools.core`, keyed by the provider strings `@api_tool` already receives.
   Opt-in layer on top of existing timeout + 429-retry; default behavior unchanged.
4. **Fail-fast contract:** tools with strictly-required keys raise `ValueError` at
   construction (finwiz's `_safe_init` skip pattern depends on this). Central tools that
   defer the check to `_run` are aligned.
5. **`parse_tool_result()` helper** exported from central `core/results.py`: parses the
   `ToolResult` JSON envelope into a dict, with typed error on `success=False`. Owned by
   the library that defines the envelope.
6. **Compatibility floor:** central CI must test against crewai 1.x (finwiz pins
   `crewai>=1.15.1`; central currently declares `>=0.100.0`). Python: central `>=3.11`,
   finwiz 3.13 — compatible.
7. **Versioning:** one minor release per wave (v0.4.0, v0.5.0, ...), tagged, CHANGELOG'd.
   Breaking changes only ship with the consumer fix in the same wave.
8. Migrated tools adopt the `ToolResult` envelope, central logging, and central input
   schemas. The MCP server auto-exposes all new tools.

## Contracts and Error Handling

- **Envelope:** every central tool returns the `ToolResult` JSON string
  (`{success, data, error}`). finwiz's programmatic callers (deep-analysis pipeline,
  portfolio services, Perplexity integration) adopt `parse_tool_result()`. epic_news
  already depends on this envelope — it is the fixed contract.
- **No silent behavior changes:** where finwiz logged-and-returned-partial-data and
  central errors (or vice versa), finwiz's behavior wins — live pipelines depend on it.
  Differences are resolved upstream during per-category reconciliation, never papered
  over in finwiz.
- **Resilience:** `@api_tool` per-call timeout + one 429 retry (existing) + provider-keyed
  rate limiting (new, ported from finwiz).

## epic_news Compatibility Contract

1. **Additive-first:** new capabilities are optional parameters whose defaults reproduce
   current behavior; epic_news at v0.3.1 semantics never breaks silently.
2. **Breaking changes pay their toll:** each sanctioned break ships with the epic_news
   fix (pin bump + call-site updates + test run) in the same wave.
3. **Release gate:** before finwiz consumes a new central tag, epic_news's test suite
   runs against that tag.

Shared surface today: `PerplexitySearchTool` (2 call sites — the only conflict),
`KrakenTickerInfoTool`. All other epic_news imports (Wikipedia, RSS, search providers,
scrapers, OSINT, SaveToRag, ExchangeRate, GeoapifyPlaces, GitHub) are untouched.

## Testing

1. **Central:** migrated tools bring their finwiz unit tests, converted to central's
   offline/mocked conventions (pytest-mock, zero network — same rules both repos).
2. **finwiz:** thin contract tests at the factory seam — factories return expected tool
   names, envelopes parse, `_safe_init` skips key-less tools, deep-analysis programmatic
   calls round-trip against mocked central tools. The 65% coverage gate gets easier as
   moved code leaves the denominator.
3. **Release gate:** epic_news suite against each new tag (see above).
4. **Acceptance:** final wave ends with a full `crewai flow kickoff` compared against a
   pre-migration baseline report — agent-facing tool descriptions and envelopes influence
   crew behavior in ways unit tests cannot see.

## Migration Waves

Each wave = central release (reconcile + move code, tag) → epic_news gate → finwiz PR
(swap imports, delete local files + migrated tests, `make check` green).

1. **Wave 1 — infrastructure + first swap:** central gains rate limiter, fail-fast
   alignment, `parse_tool_result()`, `prefetched_data`, new Perplexity signature, crewai 1.x
   CI floor → v0.4.0. epic_news: pin bump + 2 Perplexity call-site fixes. finwiz: add
   dependency, swap the five Yahoo tools + two Perplexity tools (key-gated tools like
   AlphaVantage/TwelveData/ChartImg wait for Wave 2).
2. **Wave 2 — enhanced/validation/sentiment:** reconcile drift for Enhanced ETF/Crypto/SEC,
   TickerValidation, DeFiMetrics, sentiment ×2, risk scoring, TwelveData ×2, ChartImg,
   AlphaVantage ×2, Kraken, MarketScreening; move `etf/`, `twelve_data/`, `sentiment/`
   closures → v0.5.0. finwiz swaps the category.
3. **Wave 3 — analytics + grading:** move the 11 analytics tools, APlusScoring + screening
   helpers, `file_tools`, `portfolio_price_service`, `charts/` → v0.6.0. finwiz swaps and
   deletes.
4. **Wave 4 — cleanup:** finwiz deletes orphaned infrastructure (`api_key_validation`,
   local rate limiter, unused `run_helpers` paths, `portfolio_cache_service` if orphaned,
   stale mypy/ruff per-file ignores), rewrites remaining direct import sites, runs the
   baseline flow comparison.

## Risks

- **Behavioral drift beyond signatures:** per-tool audit during each reconciliation wave;
  finwiz behavior wins.
- **Agent behavior shifts** from changed tool descriptions/envelopes: caught by the
  baseline `crewai flow kickoff` comparison, not unit tests.
- **Editable-override foot-gun:** committed state must always be the tag pin; the
  editable override is a documented local workflow, verified absent in CI.
- **Three-repo coordination overhead:** mitigated by additive-first policy — most waves
  don't touch epic_news at all.

## Acceptance Criteria

- All three repos green (lint, type check, tests) at every wave boundary.
- finwiz `src/finwiz/tools/` reduced to the "stays in finwiz" list above.
- epic_news tests pass against every tag finwiz consumes.
- Final `crewai flow kickoff` produces a report consistent with the pre-migration baseline.
- No `unittest.mock` anywhere; no committed machine-specific paths.
