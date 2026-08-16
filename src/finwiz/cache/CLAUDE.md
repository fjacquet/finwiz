# Cache Module

Caching infrastructure for analysis results. Two distinct caches live here:
- `AnalysisCacheManager` — per-ticker crew analysis results (24h TTL, JSON on disk)
- `FactPackCache` — verified Perplexity fact packs (v5.2; freshness-banded, no
  hard TTL eviction). See ADR-010.

## Directory Structure

```
cache/
├── __init__.py
├── _models.py                  # CrewAnalysisResult, CachedAnalysis (Pydantic)
├── _helpers.py                 # verify/find/convert/clear_stale/get_stats helpers
├── analysis_cache_manager.py   # AnalysisCacheManager (thin coordinator)
└── fact_pack_cache.py          # FactPackCache (v5.2 grounded qualitative)
```

`analysis_cache_manager.py` is split across `_models.py` and `_helpers.py` to
keep each file under the project's 300-line cap. The split is purely
structural — the manager's public API (`get_cached_analysis`, `cache_analysis`,
`clear_stale_cache`, `get_cache_stats`, `log_cache_stats`) is unchanged.

## Major Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `analysis_cache_manager.py` | `AnalysisCacheManager` | Central cache for crew analysis results |
| `analysis_cache_manager.py` | `get_analysis_cache_manager()` | Process-wide singleton accessor |
| `_models.py` | `CrewAnalysisResult` | Pydantic model for cached analysis payload |
| `_models.py` | `CachedAnalysis` | Cache envelope with TTL/age helpers |
| `fact_pack_cache.py` | `FactPackCache` | v5.2 fact pack cache (path-traversal hardened) |

## Usage

```python
from finwiz.cache.analysis_cache_manager import AnalysisCacheManager

cache = AnalysisCacheManager()

cached = cache.get_cached_analysis(ticker="AAPL", asset_class="stock")
if cached:
    return cached

result = perform_analysis(ticker)
cache.cache_analysis(ticker, "stock", result)
```

## Cache Configuration

**Not environment-driven.** No code in this module reads `CACHE_BACKEND`,
`CACHE_TTL`, or `CACHE_MAX_SIZE` — setting them has no effect, even though
`.env.example` still lists the first two.

TTL is a constructor argument, defaulting to 24 hours:

```python
AnalysisCacheManager(cache_dir="cache/portfolio_analysis", ttl_hours=24)
```

The per-type TTL registry used elsewhere in the tree
(`CACHE_TTL_{TYPE}`) lives in `infrastructure/caching/ttl_config.py` and is a
separate layer from this one.

## Related Modules

- `finwiz.infrastructure.caching.manager` — In-memory CacheManager (different layer)
- `finwiz.infrastructure.caching.ttl_config` — Per-type TTL registry
