# Phase 4: Performance - Research

**Researched:** 2026-02-08
**Domain:** Python asyncio concurrency, rate limiting, circuit breakers, cache management
**Confidence:** HIGH

## Summary

Phase 4 addresses four distinct performance bottlenecks in the FinWiz pipeline: sequential data collection, blocking rate limiters, unprotected crew executions, and blocking cache cleanup. The codebase already has substantial asyncio infrastructure, a rate limiter module, cache manager, and resilience patterns -- but each has specific deficiencies that PERF-01 through PERF-04 target.

The codebase is in better shape than expected. The `DeepAnalysisOrchestrator.run_deep_analysis_concurrent()` already uses `asyncio.gather()` with semaphore and `asyncio.wait_for()` for per-holding timeouts. However, `crew_factory.py` has 7 `crew.kickoff()` calls with NO timeout protection, and the rate limiter uses blocking `asyncio.sleep()` instead of a token bucket algorithm. The cache cleanup loop uses a blocking `asyncio.sleep(3600)` pattern.

**Primary recommendation:** Refactor the existing `RateLimiter` to use a token bucket algorithm (via `aiolimiter` library), wrap all `crew.kickoff()` calls with `asyncio.wait_for()`, and replace the cache cleanup sleep loop with event-driven eviction.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `aiolimiter` | 1.2.1+ | Token bucket rate limiting | Efficient asyncio leaky-bucket, used in production by many projects, minimal API |
| `asyncio` (stdlib) | 3.12 | Semaphore, gather, wait_for | Already used extensively in codebase |
| `tenacity` | (already installed) | Retry with backoff | Already used in `infrastructure/resilience/retry.py` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `circuitbreaker` | 2.0+ | Circuit breaker decorator | Wrap crew.kickoff() calls -- simple decorator pattern, no heavy dependencies |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `aiolimiter` | Custom token bucket | aiolimiter is 100 lines, battle-tested; hand-rolling risks edge cases |
| `circuitbreaker` | `aiobreaker` | circuitbreaker is simpler, supports async, no extra deps; aiobreaker has Redis backing |
| `circuitbreaker` | Expand existing circuit breaker in `evaluators.py` | Existing one is for feature flags, not crew execution; separate concerns |

**Installation:**
```bash
uv add aiolimiter circuitbreaker
```

## Architecture Patterns

### Current Architecture (Before Changes)

```
src/finwiz/
├── infrastructure/
│   ├── resilience/
│   │   ├── rate_limiter.py      # [PERF-02] Sliding window + asyncio.sleep() cooldowns
│   │   ├── degradation.py       # Has asyncio.wait_for() + retry + circuit breaker concept
│   │   ├── timeout.py           # Generic with_timeout() wrapper
│   │   └── retry.py             # tenacity-based retry decorator
│   └── caching/
│       └── manager.py           # [PERF-04] cleanup_loop uses asyncio.sleep(3600)
├── crew_factory.py              # [PERF-03] 7 kickoff() calls, NO timeout/circuit breaker
├── flows/utils.py               # [PERF-03] 1 kickoff() call, NO timeout
├── analysis/
│   └── deep_analysis_pipeline.py # [PERF-03] 1 kickoff() call, NO timeout
├── orchestrators/
│   ├── deep_analysis_orchestrator.py  # [PERF-01] ALREADY has asyncio.gather + semaphore + wait_for
│   └── validation_orchestrator.py     # [PERF-03] 1 kickoff() call, NO timeout
├── crews/
│   ├── stock_crew/stock_crew.py       # [PERF-03] 1 kickoff() call via run_analysis()
│   ├── etf_crew/etf_crew.py           # [PERF-03] 1 kickoff() call via run_analysis()
│   ├── crypto_crew/crypto_crew.py     # [PERF-03] 1 kickoff() call via run_analysis()
│   └── deep_analysis/deep_analysis.py # [PERF-03] 1 kickoff() call via run_with_logging()
└── tools/analysis/
    └── analysis_coordinator.py  # [PERF-01] Has asyncio.gather + asyncio.sleep(1.0) between batches
```

### Pattern 1: Token Bucket Rate Limiter (PERF-02)

**What:** Replace sliding window + asyncio.sleep() cooldown with aiolimiter's AsyncLimiter
**When to use:** Every API call that currently goes through RateLimiter.acquire()

```python
# Source: aiolimiter official docs (https://aiolimiter.readthedocs.io/)
from aiolimiter import AsyncLimiter

# Per-API token buckets with burst capacity
API_LIMITERS: dict[APIProvider, AsyncLimiter] = {
    APIProvider.ALPHA_VANTAGE: AsyncLimiter(5, 60),       # 5 req/min, burst=5
    APIProvider.YAHOO_FINANCE: AsyncLimiter(10, 1),       # 10 req/sec, burst=10
    APIProvider.TWELVE_DATA: AsyncLimiter(8, 60),         # 8 req/min, burst=8
    APIProvider.SEC_EDGAR: AsyncLimiter(10, 60),          # 10 req/min
    APIProvider.PERPLEXITY: AsyncLimiter(30, 60),         # 30 req/min
    APIProvider.KRAKEN: AsyncLimiter(60, 60),             # 60 req/min
}

async def acquire(self, provider: APIProvider, endpoint: str = "") -> bool:
    limiter = self._limiters.get(provider)
    if limiter:
        await limiter.acquire()  # Non-blocking wait for token
    return True
```

### Pattern 2: Crew Timeout + Circuit Breaker (PERF-03)

**What:** Wrap every crew.kickoff() with asyncio.wait_for() and track failures
**When to use:** Every location where crew.kickoff() is called

```python
# Using circuitbreaker library (https://pypi.org/project/circuitbreaker/)
import asyncio
from circuitbreaker import circuit

HOLDING_TIMEOUT = int(os.getenv("FINWIZ_HOLDING_TIMEOUT", "300"))

# Circuit breaker: open after 3 failures, reset after 60s
@circuit(failure_threshold=3, recovery_timeout=60)
def execute_crew_with_timeout(crew_instance, inputs, timeout=HOLDING_TIMEOUT):
    """Execute crew.kickoff() with timeout protection."""
    # For sync crew.kickoff(), wrap in asyncio if needed
    result = crew_instance.kickoff(inputs=inputs)
    return result
```

### Pattern 3: Semaphore-based Concurrent Data Collection (PERF-01)

**What:** Use asyncio.Semaphore to control concurrent API fetches
**When to use:** Batch data collection for multiple holdings

```python
# Source: Python docs (https://docs.python.org/3/library/asyncio-sync.html)
semaphore = asyncio.Semaphore(10)  # Max 10 concurrent fetches

async def fetch_with_semaphore(ticker: str):
    async with semaphore:
        return await fetch_data(ticker)

results = await asyncio.gather(
    *[fetch_with_semaphore(t) for t in tickers],
    return_exceptions=True
)
```

### Pattern 4: Event-driven LRU Cache Eviction (PERF-04)

**What:** Replace `asyncio.sleep(3600)` loop with on-access eviction checks
**When to use:** Cache manager cleanup

```python
# Instead of:
async def cleanup_loop():
    while True:
        await asyncio.sleep(3600)  # BLOCKS for 1 hour
        await self.cleanup_expired()

# Use event-driven approach:
async def _ensure_memory_capacity(self) -> None:
    """Evict on insertion when at capacity (already exists in manager.py)."""
    while len(self.memory_cache) >= self.config.max_memory_items:
        # Evict LRU entry
        oldest_key = min(self.memory_cache.keys(),
                        key=lambda k: self.memory_cache[k].last_accessed)
        await self._remove_entry(oldest_key)

# Incremental cleanup on get():
async def get(self, key, default=None):
    # Check TTL on access (lazy eviction)
    entry = self.memory_cache.get(cache_key)
    if entry and entry.is_expired:
        await self._remove_entry(cache_key)
        return default
    ...
```

### Anti-Patterns to Avoid

- **asyncio.sleep() for rate limiting:** Blocks the event loop thread; use token bucket acquire() instead
- **Unbounded asyncio.gather():** Always use semaphore to limit concurrency; gathering 66 crew.kickoff() calls simultaneously will exhaust API limits and memory
- **Crew kickoff without timeout:** A stuck LLM call can hang indefinitely; always use asyncio.wait_for() or equivalent
- **Global cleanup intervals:** Sleeping for 1 hour wastes memory; evict lazily on access

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token bucket rate limiting | Custom implementation | `aiolimiter.AsyncLimiter` | Edge cases around timing, burst capacity, thread safety |
| Circuit breaker | Custom state machine | `circuitbreaker` library | State transitions, half-open testing, thread safety |
| Retry with backoff | Custom loop | `tenacity` (already used) | Jitter, exponential backoff, conditional retry |
| Async semaphore | Custom counter | `asyncio.Semaphore` (stdlib) | Already battle-tested, used in codebase |

**Key insight:** The codebase already has a partially-built rate limiter and circuit breaker in feature flags. Rather than extending those, use dedicated libraries that handle the edge cases correctly, and keep the existing code for its current purposes.

## Common Pitfalls

### Pitfall 1: crew.kickoff() is Synchronous

**What goes wrong:** CrewAI's `crew.kickoff()` is a synchronous blocking call. You cannot directly `await asyncio.wait_for(crew.kickoff(...))`.
**Why it happens:** CrewAI runs its own event loop internally.
**How to avoid:** The codebase already solves this in `deep_analysis_orchestrator.py` by using `loop.run_in_executor()` to run `crew.kickoff()` in a ThreadPoolExecutor, then wrapping that with `asyncio.wait_for()`. All other crew.kickoff() sites must follow this same pattern.
**Warning signs:** `asyncio.wait_for()` wrapping a non-coroutine function directly.

### Pitfall 2: Rate Limiter asyncio.sleep() Inside Lock

**What goes wrong:** The current `RateLimiter.acquire()` holds `self._lock` (an asyncio.Lock) while calling `asyncio.sleep()`. This serializes ALL API calls through a single lock.
**Why it happens:** The lock was meant to protect shared state, but the sleep inside it blocks all other coroutines.
**How to avoid:** With `aiolimiter`, there is no explicit lock needed; the library handles this internally. Each API provider gets its own AsyncLimiter instance.
**Warning signs:** Only one API call happening at a time despite asyncio concurrency.

### Pitfall 3: Token Bucket vs. Sliding Window Semantics

**What goes wrong:** The current rate limiter uses a sliding window (count requests in last N seconds). Token bucket allows bursts up to capacity, then rate-limits. These behave differently.
**Why it happens:** Different algorithms optimize for different use cases.
**How to avoid:** Token bucket is better for API calls because APIs typically allow burst capacity. Configure `aiolimiter.AsyncLimiter(max_rate, time_period)` where `max_rate` is the burst capacity and `time_period` controls the refill rate.
**Warning signs:** API 429 errors despite staying under per-minute limits.

### Pitfall 4: Circuit Breaker Scope

**What goes wrong:** Applying circuit breaker too broadly (e.g., one breaker for all crews) means one failing crew disables unrelated crews.
**Why it happens:** Shared state across independent failure domains.
**How to avoid:** One circuit breaker per crew type (stock, etf, crypto, deep_analysis, etc.). The existing per-crew error handling in `crew_factory.py` already provides the right structure.
**Warning signs:** All crews failing because one had a transient error.

### Pitfall 5: Cache Cleanup Removing Active Entries

**What goes wrong:** Aggressive LRU eviction removes entries that are still needed by in-flight analyses.
**Why it happens:** LRU eviction considers only access time, not whether the entry is currently being used.
**How to avoid:** Use TTL-based expiry as primary mechanism (entries expire after their TTL), and LRU only for memory pressure situations. The current `_ensure_memory_capacity()` already does this correctly.
**Warning signs:** Cache misses on data that was just fetched.

## Detailed Codebase Findings

### PERF-01: asyncio.sleep() Calls Categorized

Found **14 asyncio.sleep() calls** in the codebase:

#### Category A: Rate Limiting (REPLACE with token bucket) - 4 calls

| File | Line | Context | Current Behavior |
|------|------|---------|-----------------|
| `infrastructure/resilience/rate_limiter.py` | 219 | `RateLimiter.acquire()` | Sleeps for cooldown_seconds inside asyncio.Lock |
| `infrastructure/resilience/rate_limiter.py` | 269 | `wait_for_availability()` | Polls with sleep in loop |
| `infrastructure/resilience/rate_limiter.py` | 429 | `with_rate_limit()` | Retry backoff between attempts |
| `integration/batch_data_prefetcher.py` | 464 | `_fetch_alpha_vantage_batch()` | Fixed 12s delay between AV calls |

#### Category B: Cache Cleanup (REPLACE with event-driven) - 1 call

| File | Line | Context | Current Behavior |
|------|------|---------|-----------------|
| `infrastructure/caching/manager.py` | 135 | `_start_cleanup_task()` | `asyncio.sleep(3600)` - blocks for 1 hour |

#### Category C: Retry/Backoff (KEEP - legitimate use) - 5 calls

| File | Line | Context | Rationale |
|------|------|---------|-----------|
| `infrastructure/resilience/degradation.py` | 223 | Exponential backoff | Legitimate retry strategy |
| `tools/portfolio_price_service.py` | 254 | Stock price retry | Legitimate retry delay |
| `tools/portfolio_price_service.py` | 310 | Crypto price retry | Legitimate retry delay |
| `tools/llm_retry.py` | 191 | LLM call retry backoff | Legitimate exponential backoff |
| `tools/perplexity_analysis_integration.py` | 300 | Perplexity retry | Legitimate backoff |

#### Category D: Inter-Batch Delay (REPLACE with token bucket) - 1 call

| File | Line | Context | Current Behavior |
|------|------|---------|-----------------|
| `tools/analysis/analysis_coordinator.py` | 130 | Between analysis batches | Fixed 1.0s sleep between batches |

#### Category E: Monitoring/Long-Running (OUT OF SCOPE) - 3 calls

| File | Line | Context | Rationale |
|------|------|---------|-----------|
| `quantitative/portfolio_monitor.py` | 247 | Monitor check interval | Long-running monitoring loop |
| `quantitative/portfolio_monitor.py` | 257 | Monitor sleep between checks | Long-running monitoring loop |
| `quantitative/portfolio_monitor.py` | 267 | Error recovery wait (5min) | Long-running monitoring loop |

### PERF-02: Token Bucket Migration Points

The current `RateLimiter` class at `infrastructure/resilience/rate_limiter.py` must be refactored:

1. **Replace `acquire()` method** (line 177-225): Currently uses sliding window counting + asyncio.sleep(). Replace with `aiolimiter.AsyncLimiter` per provider.
2. **Replace `wait_for_availability()` method** (line 255-272): Currently polls with sleep. Replace with single `await limiter.acquire()`.
3. **Keep `get_retry_delay()` and `should_retry()`**: These handle retry logic, not rate limiting.
4. **Keep `DEFAULT_RATE_LIMITS` config**: Use these values to configure AsyncLimiter instances.

Per-API token bucket configuration (derived from existing `DEFAULT_RATE_LIMITS`):

| Provider | Current Config | Token Bucket Config |
|----------|---------------|-------------------|
| ALPHA_VANTAGE | 5 req/min, cooldown=12s | `AsyncLimiter(5, 60)` |
| YAHOO_FINANCE | 600 req/min, cooldown=0.1s | `AsyncLimiter(10, 1)` (10/sec) |
| TWELVE_DATA | 8 req/min, cooldown=7.5s | `AsyncLimiter(8, 60)` |
| CHART_IMG | 30 req/min, cooldown=2s | `AsyncLimiter(5, 10)` (burst=5) |
| COINMARKETCAP | 30 req/min, cooldown=2s | `AsyncLimiter(5, 10)` |
| KRAKEN | 60 req/min, cooldown=1s | `AsyncLimiter(10, 10)` |
| SEC_EDGAR | 10 req/min, cooldown=6s | `AsyncLimiter(10, 60)` |
| PERPLEXITY | 30 req/min, cooldown=2s | `AsyncLimiter(5, 10)` |

### PERF-03: crew.kickoff() Calls Inventory

Found **13 crew.kickoff() calls** that need timeout/circuit breaker wrapping:

#### Already Protected (2 calls)

| File | Line | Crew | Protection |
|------|------|------|-----------|
| `orchestrators/deep_analysis_orchestrator.py` | 261 | Deep analysis | asyncio.wait_for() + semaphore + ThreadPoolExecutor |
| `infrastructure/resilience/degradation.py` | 191 | Generic wrapper | asyncio.wait_for() with config.timeout_seconds |

#### Need Protection (11 calls)

| File | Line | Crew | Current Protection |
|------|------|------|--------------------|
| `crew_factory.py` | 56 | CryptoCrew | try/except only |
| `crew_factory.py` | 111 | StockCrew | try/except only |
| `crew_factory.py` | 166 | EtfCrew | try/except only |
| `crew_factory.py` | 223 | PortfolioRebalancingCrew | try/except only |
| `crew_factory.py` | 264 | InvestmentDiscoveryCrew | try/except only |
| `crew_factory.py` | 335 | ReportCrew | try/except only |
| `flows/utils.py` | 71 | Generic crew | try/except only |
| `analysis/deep_analysis_pipeline.py` | 142 | DeepAnalysisCrew | try/except only |
| `orchestrators/validation_orchestrator.py` | 169 | PortfolioRebalancingCrew | try/except only |
| `crews/stock_crew/stock_crew.py` | 244 | StockCrew internal | try/except + timing |
| `crews/etf_crew/etf_crew.py` | 238 | EtfCrew internal | try/except + timing |
| `crews/crypto_crew/crypto_crew.py` | 261 | CryptoCrew internal | try/except + timing |
| `crews/deep_analysis/deep_analysis.py` | 340 | DeepAnalysis internal | try/except + timing |

**Note:** The crew internal calls (stock_crew.py, etf_crew.py, etc.) have their own `run_analysis()` or `run_with_logging()` methods. The best approach is to add timeout at the caller level (crew_factory.py, flows/utils.py, validation_orchestrator.py, deep_analysis_pipeline.py) rather than inside each crew class.

### PERF-04: Cache Cleanup Implementation Details

Current blocking pattern in `infrastructure/caching/manager.py` (lines 129-148):

```python
def _start_cleanup_task(self) -> None:
    async def cleanup_loop() -> None:
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)  # BLOCKS 3600s
                await self.cleanup_expired()
            except asyncio.CancelledError:
                break
    self._cleanup_task = loop.create_task(cleanup_loop())
```

The cache already has LRU eviction in `_ensure_memory_capacity()` (lines 419-433) and lazy TTL checking in `get()` (line 202). The fix is to:
1. Remove the blocking cleanup_loop
2. Add incremental cleanup on `set()` (e.g., every 100 insertions, clean 10% of expired)
3. Keep `_ensure_memory_capacity()` as-is (already event-driven)
4. Add cleanup on `get()` for expired entries (already partially done at line 202)

Also found in `tools/analysis/analysis_coordinator.py` line 56:
```python
cleanup_interval=3600,  # Cleanup every hour
```
This instantiates a CacheManager with the same blocking cleanup pattern.

## Code Examples

### Example 1: Token Bucket Rate Limiter Replacement

```python
# Source: aiolimiter docs + existing DEFAULT_RATE_LIMITS
from aiolimiter import AsyncLimiter
from finwiz.infrastructure.resilience.rate_limiter import APIProvider, RateLimitConfig, DEFAULT_RATE_LIMITS

class TokenBucketRateLimiter:
    """Token bucket rate limiter using aiolimiter."""

    def __init__(self, config: dict[APIProvider, RateLimitConfig] | None = None) -> None:
        self.config = config or DEFAULT_RATE_LIMITS
        self._limiters: dict[APIProvider, AsyncLimiter] = {}
        for provider, cfg in self.config.items():
            # max_rate = burst_limit, time_period = 60/requests_per_minute * burst_limit
            time_period = 60.0 / cfg.requests_per_minute * cfg.burst_limit if cfg.requests_per_minute > 0 else 60.0
            self._limiters[provider] = AsyncLimiter(cfg.burst_limit, time_period)

    async def acquire(self, provider: APIProvider, endpoint: str = "") -> bool:
        limiter = self._limiters.get(provider)
        if limiter:
            await limiter.acquire()  # Waits for token, non-blocking
        return True
```

### Example 2: Crew Kickoff with Timeout + Circuit Breaker

```python
# Apply to crew_factory.py execute_*_crew() methods
import asyncio
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=4)

CREW_TIMEOUT = int(os.getenv("FINWIZ_HOLDING_TIMEOUT", "300"))

# Track failures per crew type for circuit breaker
_crew_failures: dict[str, int] = {}
_crew_circuit_open: dict[str, float] = {}
FAILURE_THRESHOLD = 3
RECOVERY_TIMEOUT = 60.0

async def execute_crew_with_protection(crew_name, crew_instance, inputs, timeout=CREW_TIMEOUT):
    """Execute crew.kickoff() with timeout and circuit breaker."""
    # Check circuit breaker
    if crew_name in _crew_circuit_open:
        if time.time() - _crew_circuit_open[crew_name] < RECOVERY_TIMEOUT:
            raise RuntimeError(f"Circuit breaker open for {crew_name}")
        del _crew_circuit_open[crew_name]  # Half-open: try again

    loop = asyncio.get_running_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(_executor, crew_instance.kickoff, inputs),
            timeout=timeout,
        )
        _crew_failures[crew_name] = 0  # Reset on success
        return result
    except (TimeoutError, Exception) as e:
        _crew_failures[crew_name] = _crew_failures.get(crew_name, 0) + 1
        if _crew_failures[crew_name] >= FAILURE_THRESHOLD:
            _crew_circuit_open[crew_name] = time.time()
            logger.error(f"Circuit breaker OPEN for {crew_name} after {FAILURE_THRESHOLD} failures")
        raise
```

### Example 3: Event-Driven Cache Cleanup

```python
# Replace cleanup_loop in infrastructure/caching/manager.py
class CacheManager:
    def __init__(self, config=None):
        ...
        self._insertion_count = 0
        self._cleanup_every_n = 100  # Clean every 100 insertions

    async def set(self, key, value, ttl=None, tags=None):
        ...
        self._insertion_count += 1
        if self._insertion_count % self._cleanup_every_n == 0:
            # Incremental cleanup: remove up to 10 expired entries
            await self._incremental_cleanup(max_entries=10)

    async def _incremental_cleanup(self, max_entries=10):
        """Remove a small batch of expired entries."""
        removed = 0
        expired_keys = []
        for key, entry in self.memory_cache.items():
            if entry.is_expired:
                expired_keys.append(key)
                if len(expired_keys) >= max_entries:
                    break
        for key in expired_keys:
            await self._remove_entry(key)
            removed += 1
        if removed:
            logger.debug(f"Incremental cleanup: removed {removed} expired entries")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sliding window rate limiting | Token bucket (aiolimiter) | Standard since 2020+ | Allows burst capacity, non-blocking |
| `asyncio.sleep()` cooldowns | `AsyncLimiter.acquire()` | When aiolimiter matured | No blocking, precise rate control |
| Manual circuit breaker state | `circuitbreaker` library | Stable since 2019+ | Handles state transitions correctly |
| Periodic cleanup loops | Event-driven / lazy eviction | Modern cache practice | No blocking background tasks |

**Deprecated/outdated:**
- Manual `asyncio.sleep()` for rate limiting: Use token bucket libraries instead
- Global cleanup intervals: Use lazy eviction on access + incremental cleanup on write

## Open Questions

1. **CrewAI kickoff() thread safety**
   - What we know: `crew.kickoff()` is synchronous and runs its own event loop. The deep_analysis_orchestrator already uses ThreadPoolExecutor to run it.
   - What's unclear: Whether multiple `crew.kickoff()` calls from different threads interfere with each other (shared LLM clients, etc.)
   - Recommendation: Keep the existing ThreadPoolExecutor pattern for concurrent crews; limit concurrency via semaphore (already done in deep_analysis_orchestrator)

2. **circuitbreaker library async support**
   - What we know: The `circuitbreaker` PyPI package supports async functions as of v2.0
   - What's unclear: Whether it works correctly with `loop.run_in_executor()` wrapping
   - Recommendation: Implement circuit breaker as a simple class (like Code Example 2) rather than a decorator, since crew.kickoff() is sync and needs executor wrapping. Use the library only if it cleanly wraps the pattern.

3. **Impact of removing cleanup_loop on long-running sessions**
   - What we know: FinWiz runs as a batch process (not a server), so cleanup loops are less critical
   - What's unclear: Whether file-based cache entries accumulate without periodic cleanup
   - Recommendation: Keep file cleanup as a separate utility (run at start/end of flow), use in-memory LRU eviction during execution

## Sources

### Primary (HIGH confidence)
- `/mjpieters/aiolimiter` (Context7) - Token bucket API, usage patterns, burst behavior
- Codebase analysis - All file paths, line numbers, and patterns verified by direct inspection
- Python 3.12 stdlib docs - asyncio.Semaphore, asyncio.gather(), asyncio.wait_for()

### Secondary (MEDIUM confidence)
- [aiolimiter docs](https://aiolimiter.readthedocs.io/) - Leaky bucket algorithm details
- [circuitbreaker PyPI](https://pypi.org/project/circuitbreaker/) - Circuit breaker pattern for Python
- [pybreaker GitHub](https://github.com/danielfm/pybreaker) - Circuit breaker implementation reference
- [aiobreaker GitHub](https://github.com/arlyon/aiobreaker) - Asyncio circuit breaker fork
- [Python asyncio sync primitives](https://docs.python.org/3/library/asyncio-sync.html) - Semaphore documentation
- [Super Fast Python - gather limit concurrency](https://superfastpython.com/asyncio-gather-limit-concurrency/) - Semaphore + gather patterns

### Tertiary (LOW confidence)
- [purgatory circuit breaker](https://github.com/mardiros/purgatory) - Alternative async circuit breaker
- [pyrate-limiter](https://pypi.org/project/pyrate-limiter/) - Alternative rate limiter with SQLite/Redis

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - aiolimiter verified via Context7, circuitbreaker verified via PyPI, both widely used
- Architecture: HIGH - Patterns directly derived from existing codebase structure and verified library APIs
- Pitfalls: HIGH - Based on actual code inspection (e.g., asyncio.sleep inside lock, sync kickoff)
- Code examples: MEDIUM - Patterns verified but untested against actual FinWiz crew execution
- Open questions: MEDIUM - CrewAI threading model needs validation during implementation

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (30 days - stable domain)
