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

Set in `.env`:

```bash
CACHE_BACKEND=hybrid        # memory/file/hybrid
CACHE_TTL=2700              # 45 minutes default
CACHE_MAX_SIZE=1000         # Max entries
```

## Related Modules

- `finwiz.utils.cache_manager` — Generic cache utilities
- `finwiz.utils.cache_decorators` — `@cache_result` decorator
- `finwiz.utils.crew_output_cache` — Crew-specific caching
- `finwiz.infrastructure.caching.manager` — In-memory CacheManager (different layer)
