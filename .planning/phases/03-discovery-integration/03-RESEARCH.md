# Phase 3: Discovery Integration - Research

**Researched:** 2026-02-07
**Domain:** Pipeline orchestration, feature flag routing, Perplexity API enrichment, JSON output persistence, pytest testing patterns
**Confidence:** HIGH

## Summary

Phase 3 integrates the discovery modules built in Phase 2 (schemas, universe provider, screeners, scorer) into a working end-to-end pipeline within the existing FinWiz flow. The integration touches five concerns: (1) a `NewcomerDiscoveryPipeline` class that orchestrates the Phase 2 components and excludes portfolio-held tickers, (2) Perplexity enrichment for high-scoring candidates gated by the existing `perplexity_research` feature flag, (3) a new `newcomer_discovery` feature flag that routes the three analyzers (`scoring/stock_analyzer.py`, `scoring/etf_analyzer.py`, `scoring/crypto_analyzer.py`) through either the new pipeline or legacy mocked data, (4) JSON persistence of results to `output/discovery/newcomer_{asset_class}.json`, and (5) comprehensive unit tests for all discovery modules.

The codebase already provides all necessary infrastructure: the feature flag system in `config/features/` (with `FeatureFlagConfig`, `create_default_flags()`, `is_feature_enabled()`), the `DiscoveryOrchestrator` in `orchestrators/discovery_orchestrator.py` (which calls the three analyzers and saves results), the `PerplexityAnalysisIntegration` class with async `search_financial_news()`, and the `PortfolioHoldingsProcessor` for loading portfolio tickers from CSV. Phase 3 is primarily a wiring and integration effort rather than building new infrastructure.

**Primary recommendation:** Build the pipeline orchestrator first (it has no external dependencies beyond Phase 2 modules), then add feature flag routing to the three analyzers (smallest change, biggest impact), then Perplexity enrichment (most complex, gated by existing flag), and finally unit tests for all modules. The pipeline should follow the AI Minimalism principle: all orchestration is pure Python, Perplexity is used only for qualitative enrichment of already-scored candidates.

## Standard Stack

### Core (Already in Project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | >=2.11.7 | `NewcomerCandidate`, `EnrichmentResult`, `NewcomerDiscoveryResult` schemas (Phase 2) | All schemas must be in `schemas/`, project standard |
| pytest | >=8.x | Unit testing framework | Project standard |
| pytest-mock | >=3.14.1 | `mocker.patch()` for mocking (unittest.mock BANNED) | Enforced by project rules |
| Faker | >=x.x | Test data generation | Used in `tests/conftest.py` |
| requests | >=2.x | HTTP calls to Perplexity API (via `PerplexitySearchTool`) | Already used by Perplexity integration |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | N/A | Output persistence with `default=str` | Writing `newcomer_{asset_class}.json` |
| pathlib (stdlib) | N/A | Directory creation, path handling | `output/discovery/` directory management |
| csv (stdlib) | N/A | Portfolio CSV loading (via `PortfolioHoldingsProcessor`) | Portfolio exclusion logic |
| asyncio (stdlib) | N/A | Async Perplexity API calls | `PerplexityAnalysisIntegration.search_financial_news()` is async |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct Perplexity API call | CrewAI crew with Perplexity tool | Direct call is $0, crew costs $0.05+ per call. AI Minimalism says direct call. |
| New `newcomer_discovery` flag | Reuse `investment_discovery` flag | New flag needed: the existing `investment_discovery` flag controls the overall discovery phase, not the newcomer pipeline vs. legacy routing |
| Sync enrichment | Async enrichment with `asyncio.gather()` | Async is better for multiple candidates but adds complexity. Since enrichment hits Perplexity per-candidate, async is correct. |
| Pipeline in `orchestrators/` | Pipeline in `scoring/` | Pipeline orchestrates modules, so `orchestrators/` or `scoring/` could work. But pipeline manages flow logic not scoring, and the existing `DiscoveryOrchestrator` is in `orchestrators/`. Place pipeline alongside discovery modules where Phase 2 builds them (likely `scoring/discovery/` or a new `discovery/` package). |

**Installation:** No new packages needed. All dependencies are already installed.

## Architecture Patterns

### Recommended Project Structure

Phase 2 will have built discovery modules. Phase 3 adds integration:

```
src/finwiz/
├── scoring/
│   ├── stock_analyzer.py          # MODIFIED: add newcomer_discovery flag routing
│   ├── etf_analyzer.py            # MODIFIED: add newcomer_discovery flag routing
│   ├── crypto_analyzer.py         # MODIFIED: add newcomer_discovery flag routing
│   └── discovery/                 # Phase 2 created this package
│       ├── __init__.py
│       ├── universe_provider.py   # Phase 2: DynamicUniverseProvider
│       ├── ipo_screener.py        # Phase 2: IPOScreener
│       ├── breakout_detector.py   # Phase 2: BreakoutDetector
│       ├── momentum_scanner.py    # Phase 2: MomentumScanner
│       ├── candidate_scorer.py    # Phase 2: CandidateScorer
│       └── pipeline.py            # Phase 3: NewcomerDiscoveryPipeline (NEW)
├── schemas/
│   └── newcomer_discovery.py      # Phase 2: schemas
├── config/features/
│   └── definitions.py             # MODIFIED: add newcomer_discovery flag
├── orchestrators/
│   └── discovery_orchestrator.py   # MODIFIED: route through pipeline when flag enabled
└── tools/
    └── perplexity_feature_utils.py # EXISTING: reuse for enrichment flag checks
```

```
tests/unit/
├── scoring/
│   └── discovery/                 # Phase 3: NEW test directory
│       ├── __init__.py
│       ├── test_pipeline.py       # Pipeline orchestrator tests
│       ├── test_universe_provider.py
│       ├── test_ipo_screener.py
│       ├── test_breakout_detector.py
│       ├── test_momentum_scanner.py
│       └── test_candidate_scorer.py
├── schemas/
│   └── test_newcomer_discovery.py # Schema tests
└── orchestrators/
    └── test_discovery_orchestrator.py  # EXISTING: extend with pipeline routing tests
```

### Pattern 1: Pipeline Orchestrator with Portfolio Exclusion

**What:** `NewcomerDiscoveryPipeline` orchestrates all Phase 2 components in sequence, excluding tickers the user already holds.

**When to use:** Called by `scoring/{asset_class}_analyzer.py` when `newcomer_discovery` feature flag is enabled.

**Key design decisions:**
- Pipeline reads portfolio tickers from CSV files via `PortfolioHoldingsProcessor.load_all_holdings()` or a simpler CSV-reading utility
- Portfolio tickers are normalized (strip `Yahoo:` prefix) and collected into a `set[str]` for O(1) lookup
- Each screener/scanner returns candidates; pipeline filters out any candidate whose ticker is in the portfolio set
- Pipeline delegates to `CandidateScorer` for final scoring
- Top candidates (score >= 0.80) are enriched via Perplexity if `perplexity_research` flag is enabled
- Returns `NewcomerDiscoveryResult` Pydantic model

**Example:**
```python
# Source: Codebase patterns from discovery_orchestrator.py + portfolio_holdings_processor.py
class NewcomerDiscoveryPipeline:
    def __init__(self, asset_class: str) -> None:
        self.asset_class = asset_class
        self.portfolio_tickers: set[str] = set()
        self._load_portfolio_tickers()

    def _load_portfolio_tickers(self) -> None:
        """Load all portfolio tickers for exclusion."""
        from pathlib import Path
        import csv
        csv_map = {"stock": "data/stock.csv", "etf": "data/etf.csv", "crypto": "data/crypto.csv"}
        for csv_path in csv_map.values():
            path = Path(csv_path)
            if path.exists():
                with path.open(newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        ticker = (row.get("Ticker") or "").strip()
                        if ticker.upper().startswith("YAHOO:"):
                            ticker = ticker.split(":", 1)[1]
                        if ticker:
                            self.portfolio_tickers.add(ticker.upper())

    def discover(self, session_id: str) -> NewcomerDiscoveryResult:
        """Run full discovery pipeline for this asset class."""
        # 1. Get candidate universe
        candidates = self._gather_candidates()
        # 2. Exclude portfolio holdings
        candidates = [c for c in candidates if c.ticker.upper() not in self.portfolio_tickers]
        # 3. Score candidates
        scored = self._score_candidates(candidates)
        # 4. Enrich top candidates
        enriched = self._enrich_top_candidates(scored)
        # 5. Build result
        return self._build_result(enriched)
```

### Pattern 2: Feature Flag Routing in Analyzers

**What:** Each analyzer checks `newcomer_discovery` flag and routes to pipeline or legacy mocked data.

**When to use:** Every call to `analyze_{asset_class}_opportunities()`.

**Key design decisions:**
- Use `is_feature_enabled("newcomer_discovery")` from `config/features/flags.py`
- When enabled: instantiate `NewcomerDiscoveryPipeline(asset_class)` and call `discover()`
- When disabled: return existing hardcoded mock data (current behavior, zero behavior change)
- Convert `NewcomerDiscoveryResult` to the dict format expected by `DiscoveryOrchestrator`
- Flag uses `BOOLEAN` strategy (simple on/off via `FF_NEWCOMER_DISCOVERY` env var)

**Example:**
```python
# Source: Pattern from existing analyzers + feature flag system
from finwiz.config.features.flags import is_feature_enabled

def analyze_stock_opportunities(session_id: str) -> dict[str, Any]:
    start_time = time.time()
    logger.info("Starting stock analysis")

    if is_feature_enabled("newcomer_discovery"):
        logger.info("Using NewcomerDiscoveryPipeline for stock discovery")
        from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline
        pipeline = NewcomerDiscoveryPipeline("stock")
        result = pipeline.discover(session_id)
        return _convert_to_legacy_format(result, start_time)
    else:
        # Legacy hardcoded mock data (existing behavior)
        return _legacy_stock_analysis(session_id, start_time)
```

### Pattern 3: Perplexity Enrichment (Gated)

**What:** Top candidates (score >= 0.80) get Perplexity research enrichment when the existing `perplexity_research` feature flag is enabled.

**When to use:** Inside `NewcomerDiscoveryPipeline._enrich_top_candidates()`.

**Key design decisions:**
- Reuse existing `PerplexityAnalysisIntegration` class and `perplexity_feature_utils.py` helpers
- The `perplexity_research` flag already exists with circuit breaker strategy (threshold: 5, timeout: 300s)
- Enrichment is async (the Perplexity integration uses `async def search_financial_news()`)
- If Perplexity is disabled or fails, candidates proceed without enrichment (graceful degradation)
- Enrichment result stored in `EnrichmentResult` Pydantic model (from Phase 2 schemas)
- Score threshold (0.80) corresponds to B+ grade, which filters to meaningful candidates only

**Example:**
```python
# Source: perplexity_feature_utils.py + perplexity_analysis_integration.py patterns
from finwiz.tools.perplexity_feature_utils import initialize_perplexity_integration, is_perplexity_enabled

def _enrich_top_candidates(self, candidates: list[NewcomerCandidate]) -> list[NewcomerCandidate]:
    """Enrich top candidates with Perplexity research."""
    integration = initialize_perplexity_integration("newcomer_discovery")
    if not is_perplexity_enabled(integration):
        logger.info("Perplexity enrichment disabled, returning candidates as-is")
        return candidates

    top_candidates = [c for c in candidates if c.composite_score >= 0.80]
    if not top_candidates:
        return candidates

    # Run async enrichment
    import asyncio
    loop = asyncio.get_event_loop()
    for candidate in top_candidates:
        try:
            result = loop.run_until_complete(
                integration.search_financial_news(
                    query=f"{candidate.ticker} investment analysis outlook",
                    ticker=candidate.ticker,
                    asset_type=self.asset_class,
                    analysis_type="fundamental",
                )
            )
            if result.success:
                candidate.enrichment = EnrichmentResult(
                    source="perplexity",
                    articles=len(result.results),
                    summary=_summarize_articles(result.results),
                )
        except Exception as e:
            logger.warning(f"Perplexity enrichment failed for {candidate.ticker}: {e}")
            # Continue without enrichment - graceful degradation

    return candidates
```

### Pattern 4: Output Persistence

**What:** Discovery results saved to `output/discovery/newcomer_{asset_class}.json`.

**When to use:** After pipeline completes in the analyzer functions.

**Key design decisions:**
- Follow existing `DiscoveryOrchestrator._save_discovery_results()` pattern
- Use `json.dumps(result.model_dump(), indent=2, default=str)` per project standards
- Create `output/discovery/` directory with `Path.mkdir(parents=True, exist_ok=True)`
- Use `NewcomerDiscoveryResult.model_dump()` for Pydantic serialization
- File naming: `newcomer_stock.json`, `newcomer_etf.json`, `newcomer_crypto.json`

**Example:**
```python
# Source: Pattern from discovery_orchestrator.py._save_discovery_results()
import json
from pathlib import Path

def _persist_result(result: NewcomerDiscoveryResult, asset_class: str) -> None:
    discovery_dir = Path("output") / "discovery"
    discovery_dir.mkdir(parents=True, exist_ok=True)
    output_file = discovery_dir / f"newcomer_{asset_class}.json"
    with open(output_file, "w") as f:
        json.dump(result.model_dump(), f, indent=2, default=str)
    logger.info(f"Saved newcomer discovery results to {output_file}")
```

### Anti-Patterns to Avoid

- **Modifying `DiscoveryOrchestrator` heavily:** The orchestrator already works. Route at the analyzer level (`scoring/{asset_class}_analyzer.py`), not at the orchestrator level. The orchestrator calls analyzers; analyzers decide which path (pipeline vs mock).
- **Creating a new Perplexity integration class:** The `PerplexityAnalysisIntegration` class and `perplexity_feature_utils.py` already handle everything needed. Reuse, don't rebuild.
- **Using unittest.mock:** BANNED. All test mocking must use `mocker.patch()` from pytest-mock.
- **Running Perplexity synchronously without asyncio:** The `PerplexityAnalysisIntegration.search_financial_news()` is async. Use `asyncio.run()` or `loop.run_until_complete()` if calling from sync code.
- **Putting pipeline logic in `orchestrators/`:** The pipeline is a scoring/analysis concern, not an orchestration concern. It belongs in `scoring/discovery/pipeline.py`.
- **Hard-coding the 0.80 enrichment threshold:** Make it a constant at module level (e.g., `ENRICHMENT_SCORE_THRESHOLD = 0.80`) for easy adjustment.
- **Forgetting `default=str` on json.dumps:** Project rule: always use `default=str`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Feature flag system | Custom flag implementation | `config/features/flags.py` `is_feature_enabled()` | Full system exists with circuit breakers, percentage rollout, etc. |
| Perplexity API integration | Direct `requests.post()` calls | `PerplexityAnalysisIntegration.search_financial_news()` | Handles retry, rate limits, fallback, structured parsing |
| Perplexity feature checking | Manual env var check | `perplexity_feature_utils.initialize_perplexity_integration()` | Handles flag + API key + availability in one call |
| Portfolio CSV loading | Custom CSV parser | `PortfolioHoldingsProcessor.normalize_ticker()` logic | Already handles `Yahoo:` prefix stripping, crypto `-USD` suffixing |
| Score-to-grade conversion | Hardcoded grade thresholds | `scoring/grading_system.py` `score_to_grade()` | Canonical grading with A+ to F, CSS classes, descriptions |
| Screening criteria | Custom threshold definitions | `tools/screening_criteria.py` `ScreeningCriteria` | Per-asset-class criteria already defined (ETF, stock, crypto) |
| JSON persistence with dir creation | Manual `os.makedirs()` | `Path.mkdir(parents=True, exist_ok=True)` + `json.dump()` | Idiomatic Python, project already uses this pattern |
| Test mocking | unittest.mock | pytest-mock `mocker.patch()` | unittest.mock is BANNED and enforced by `conftest_unittest_blocker.py` |

**Key insight:** Phase 3 is an integration phase. Every building block already exists -- feature flags, Perplexity integration, portfolio loading, grading system, screening criteria. The value is in wiring them together correctly, not building new infrastructure.

## Common Pitfalls

### Pitfall 1: Portfolio Ticker Normalization Mismatch

**What goes wrong:** Discovery pipeline finds candidate "AAPL" but portfolio CSV has "Yahoo:AAPL". The exclusion set lookup fails because the strings don't match.

**Why it happens:** Portfolio CSVs use `Yahoo:AAPL` format. Discovery modules likely return plain tickers like `AAPL`.

**How to avoid:** Normalize all tickers on both sides. Strip `Yahoo:` prefix when loading portfolio. Use `.upper()` on both sides. For crypto, handle the `-USD` suffix difference (portfolio has `BTC`, pipeline might have `BTC-USD` or vice versa).

**Warning signs:** Tests pass but production shows "discovered" tickers that are already in the portfolio.

### Pitfall 2: Async/Sync Context Mismatch with Perplexity

**What goes wrong:** `PerplexityAnalysisIntegration.search_financial_news()` is async, but the analyzer functions (`analyze_stock_opportunities()`) are sync. Calling `asyncio.run()` inside an already-running event loop raises `RuntimeError`.

**Why it happens:** FinWiz runs inside CrewAI Flow which may have its own event loop.

**How to avoid:** Check if there's an existing event loop with `asyncio.get_event_loop()`. If running inside an async context, use `await` directly. If in sync context, use `asyncio.run()`. Alternatively, make a sync wrapper using `asyncio.get_event_loop().run_until_complete()` or use `nest_asyncio` if the loop is already running. The safest pattern: detect and adapt.

**Warning signs:** `RuntimeError: This event loop is already running` in production.

### Pitfall 3: Feature Flag Not Registered in definitions.py

**What goes wrong:** Adding `newcomer_discovery` flag usage in analyzers but forgetting to register it in `create_default_flags()` in `definitions.py`. The `is_feature_enabled()` call returns `False` and logs "Unknown feature flag" warning.

**Why it happens:** Feature flag definition is in a different file from usage.

**How to avoid:** Always add the flag to `create_default_flags()` in `config/features/definitions.py` BEFORE referencing it. Follow the exact `FeatureFlagConfig` pattern used by existing flags (e.g., `investment_discovery`).

**Warning signs:** Log output shows "Unknown feature flag: newcomer_discovery".

### Pitfall 4: FinwizState Extra Fields

**What goes wrong:** The pipeline tries to store newcomer-specific data in FinwizState, but the state model doesn't have those fields.

**Why it happens:** FinwizState uses `model_config = {"extra": "allow"}`, so extra fields silently work but are untyped.

**How to avoid:** FinwizState has `extra: "allow"`, so dynamically added attributes work (as the existing `DiscoveryOrchestrator._update_state_from_dict()` does). This is acceptable for now. But discovery results should primarily be persisted to JSON files (the DISC-10 requirement), not stored in flow state.

**Warning signs:** Type checkers show no errors but runtime state has unexpected fields.

### Pitfall 5: Test Isolation with Feature Flags

**What goes wrong:** Tests for flag-enabled behavior leak into tests for flag-disabled behavior because the global `_feature_flags` singleton persists state.

**Why it happens:** The feature flag system uses a module-level global singleton `_feature_flags`.

**How to avoid:** In tests, mock `is_feature_enabled()` directly via `mocker.patch("finwiz.config.features.flags.is_feature_enabled")` rather than manipulating the singleton. Alternatively, mock the environment variable `FF_NEWCOMER_DISCOVERY` via `mocker.patch.dict(os.environ, ...)` and reset the singleton.

**Warning signs:** Tests pass individually but fail when run together.

### Pitfall 6: Output Format Compatibility

**What goes wrong:** The new pipeline returns `NewcomerDiscoveryResult` (Pydantic model) but `DiscoveryOrchestrator` expects `dict[str, Any]` with specific keys like `"opportunities"`, `"analysis_summary"`, `"performance_metrics"`.

**Why it happens:** The analyzers return `dict[str, Any]` in a specific format. The pipeline returns a Pydantic model in a different shape.

**How to avoid:** Add a `_convert_to_legacy_format()` function in each analyzer that converts `NewcomerDiscoveryResult` to the dict format expected by `DiscoveryOrchestrator`. The conversion maps `result.candidates` to `opportunities`, `result.summary` to `analysis_summary`, etc.

**Warning signs:** `DiscoveryOrchestrator` logs empty opportunities or crashes on missing keys.

## Code Examples

### Feature Flag Definition (definitions.py addition)

```python
# Source: Pattern from existing flags in config/features/definitions.py
"newcomer_discovery": FeatureFlagConfig(
    name="newcomer_discovery",
    enabled=get_env_bool("FF_NEWCOMER_DISCOVERY", False),  # Disabled by default
    strategy=FeatureFlagStrategy.BOOLEAN,
    fallback_strategy=FallbackStrategy.DEFAULT_VALUES,
    description="Route stock/etf/crypto analyzers through NewcomerDiscoveryPipeline instead of legacy mocked data",
),
```

### Analyzer Routing Pattern

```python
# Source: Pattern from scoring/stock_analyzer.py + feature flag patterns
def analyze_stock_opportunities(session_id: str) -> dict[str, Any]:
    start_time = time.time()
    logger.info("Starting stock analysis")

    if is_feature_enabled("newcomer_discovery"):
        try:
            from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline
            pipeline = NewcomerDiscoveryPipeline("stock")
            result = pipeline.discover(session_id)
            return _newcomer_result_to_legacy(result, start_time)
        except Exception as e:
            logger.error(f"Newcomer discovery pipeline failed, falling back to legacy: {e}")
            # Fall through to legacy on pipeline failure

    # Legacy mocked data
    opportunities = [
        {"ticker": "MSFT", "name": "Microsoft Corporation", "grade": "A+", ...},
        ...
    ]
    ...
```

### Test Pattern (pytest-mock, no unittest.mock)

```python
# Source: Pattern from tests/unit/orchestrators/test_discovery_orchestrator.py
class TestNewcomerDiscoveryPipeline:
    @pytest.fixture
    def pipeline(self, mocker):
        """Create pipeline with mocked dependencies."""
        # Mock CSV loading to avoid filesystem access
        mocker.patch(
            "finwiz.scoring.discovery.pipeline.NewcomerDiscoveryPipeline._load_portfolio_tickers",
            return_value=None,
        )
        p = NewcomerDiscoveryPipeline("stock")
        p.portfolio_tickers = {"AAPL", "MSFT", "GOOGL"}  # Known portfolio
        return p

    def test_should_exclude_portfolio_tickers(self, pipeline, mocker):
        """Test that pipeline excludes tickers already in portfolio."""
        # Arrange: mock universe to return mix of portfolio and new tickers
        mock_candidates = [
            NewcomerCandidate(ticker="AAPL", ...),   # In portfolio
            NewcomerCandidate(ticker="NVDA", ...),    # NOT in portfolio
            NewcomerCandidate(ticker="MSFT", ...),    # In portfolio
            NewcomerCandidate(ticker="PLTR", ...),    # NOT in portfolio
        ]
        mocker.patch.object(pipeline, "_gather_candidates", return_value=mock_candidates)
        mocker.patch.object(pipeline, "_score_candidates", side_effect=lambda x: x)
        mocker.patch.object(pipeline, "_enrich_top_candidates", side_effect=lambda x: x)

        # Act
        result = pipeline.discover("test_session")

        # Assert: only non-portfolio tickers remain
        result_tickers = [c.ticker for c in result.candidates]
        assert "AAPL" not in result_tickers
        assert "MSFT" not in result_tickers
        assert "NVDA" in result_tickers
        assert "PLTR" in result_tickers

    def test_should_skip_enrichment_when_perplexity_disabled(self, pipeline, mocker):
        """Test graceful degradation when Perplexity is disabled."""
        mocker.patch(
            "finwiz.tools.perplexity_feature_utils.initialize_perplexity_integration",
            return_value=None,
        )
        candidates = [NewcomerCandidate(ticker="NVDA", composite_score=0.92, ...)]
        result = pipeline._enrich_top_candidates(candidates)
        assert len(result) == 1
        assert result[0].enrichment is None  # No enrichment applied
```

### Feature Flag Toggle Test Pattern

```python
# Source: Pattern from existing test patterns
def test_should_use_pipeline_when_flag_enabled(self, mocker):
    """Test that analyzer routes to pipeline when flag is enabled."""
    mocker.patch("finwiz.config.features.flags.is_feature_enabled", return_value=True)
    mock_pipeline = mocker.patch("finwiz.scoring.discovery.pipeline.NewcomerDiscoveryPipeline")
    mock_pipeline.return_value.discover.return_value = NewcomerDiscoveryResult(...)

    result = analyze_stock_opportunities("test_session")

    mock_pipeline.assert_called_once_with("stock")
    mock_pipeline.return_value.discover.assert_called_once_with("test_session")

def test_should_use_legacy_when_flag_disabled(self, mocker):
    """Test that analyzer falls back to legacy mocked data when flag is disabled."""
    mocker.patch("finwiz.config.features.flags.is_feature_enabled", return_value=False)

    result = analyze_stock_opportunities("test_session")

    assert result["performance_metrics"]["method"] == "python_analysis"
    assert len(result["opportunities"]) > 0  # Legacy mock data
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| AI crews for discovery | Python-only discovery (AI Minimalism) | Current design | $0 cost, <100ms, deterministic |
| Hardcoded mock data | Real pipeline with screeners/scanners | Phase 2-3 | Actual market-driven discovery |
| No portfolio exclusion | Portfolio exclusion via CSV loading | Phase 3 | No duplicate recommendations |
| No enrichment gating | Perplexity enrichment gated by feature flag | Phase 3 | Graceful degradation when API unavailable |

**Deprecated/outdated:**
- Legacy hardcoded tickers in `stock_analyzer.py`, `etf_analyzer.py`, `crypto_analyzer.py`: These remain as the fallback path when `FF_NEWCOMER_DISCOVERY=false`. They are NOT removed -- they become the fallback.
- Direct AI crew calls for discovery: The project already moved away from this with AI Minimalism.

## Open Questions

1. **Pipeline location: `scoring/discovery/pipeline.py` vs. separate top-level `discovery/` package?**
   - What we know: Phase 2 builds individual modules. If Phase 2 places them in `scoring/discovery/`, the pipeline naturally goes there too. If Phase 2 creates a new top-level `discovery/` package, the pipeline goes there.
   - What's unclear: Phase 2 hasn't been implemented yet, so the exact file locations may differ.
   - Recommendation: Follow wherever Phase 2 places the modules. The planner should note this dependency and specify "same package as Phase 2 modules."

2. **Async enrichment in sync context**
   - What we know: `PerplexityAnalysisIntegration.search_financial_news()` is async. The analyzer functions are sync. CrewAI Flow may have its own event loop.
   - What's unclear: Whether CrewAI Flow's event loop is accessible from within analyzer calls (discovery phase runs inside `run_sequential_workflow()`).
   - Recommendation: Use `asyncio.run()` for enrichment if no loop exists, or create a dedicated sync wrapper. Test this early in implementation.

3. **How many candidates should be enriched?**
   - What we know: Threshold is score >= 0.80 (B+ grade). Perplexity has rate limits (circuit breaker threshold: 5 failures).
   - What's unclear: How many candidates will typically pass the 0.80 threshold. If 50 candidates pass, enriching all 50 may hit rate limits.
   - Recommendation: Add a `MAX_ENRICHMENT_CANDIDATES = 10` cap per asset class. Enrich only the top 10 by score.

## Sources

### Primary (HIGH confidence)

- Codebase inspection: `config/features/definitions.py` -- all 19 existing feature flags verified
- Codebase inspection: `config/features/flags.py` -- `is_feature_enabled()`, `execute_with_feature_flag()` API verified
- Codebase inspection: `scoring/stock_analyzer.py`, `etf_analyzer.py`, `crypto_analyzer.py` -- all three return identical dict format with `opportunities`, `analysis_summary`, `performance_metrics`
- Codebase inspection: `orchestrators/discovery_orchestrator.py` -- full `DiscoveryOrchestrator` class, `check_crypto/stock/etf()` methods, `_save_discovery_results()` pattern
- Codebase inspection: `tools/perplexity_analysis_integration.py` -- `PerplexityAnalysisIntegration` class with async `search_financial_news()`
- Codebase inspection: `tools/perplexity_feature_utils.py` -- `initialize_perplexity_integration()`, `is_perplexity_enabled()` helpers
- Codebase inspection: `orchestrators/portfolio_holdings_processor.py` -- CSV loading with `Yahoo:` prefix normalization
- Codebase inspection: `flow_state_models.py` -- `FinwizState` with `extra="allow"` configuration
- Codebase inspection: `data/stock.csv`, `data/etf.csv`, `data/crypto.csv` -- CSV format with `Name,Ticker,Currency` columns, `Yahoo:` prefix
- Codebase inspection: `tests/unit/orchestrators/test_discovery_orchestrator.py` -- existing test patterns with pytest-mock
- Codebase inspection: `scoring/grading_system.py` -- `score_to_grade()`, grade thresholds (B+ >= 0.80)
- Codebase inspection: `tools/screening_criteria.py` -- `ScreeningCriteria` with per-asset-class defaults
- Codebase inspection: `schemas/perplexity.py` -- `SonarSearchResult`, `SonarArticle` models
- Codebase inspection: `schemas/investment_discovery.py` -- existing `APlusDiscoveryResult`, `InvestmentCandidate` models

### Secondary (MEDIUM confidence)

- ROADMAP.md Phase 2 description -- specifies Phase 2 builds schemas + modules, Phase 3 integrates
- REQUIREMENTS.md DISC-07 through DISC-11 -- requirements text is clear on scope

### Tertiary (LOW confidence)

- None -- all findings verified from codebase inspection

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in project, verified via codebase inspection
- Architecture: HIGH -- all integration points verified in source code, patterns follow existing codebase conventions
- Pitfalls: HIGH -- identified from actual code patterns (ticker normalization, async/sync, feature flag singleton)
- Code examples: MEDIUM -- examples follow verified patterns but Phase 2 module APIs are not yet implemented

**Research date:** 2026-02-07
**Valid until:** 2026-03-07 (stable -- internal codebase, no external API changes expected)
