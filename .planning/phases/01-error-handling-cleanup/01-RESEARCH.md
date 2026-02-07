# Phase 1: Error Handling Cleanup - Research

**Researched:** 2026-02-07
**Domain:** Python exception handling, JSON serialization, CrewAI structured output
**Confidence:** HIGH

## Summary

This phase addresses three related error handling deficiencies in the FinWiz codebase: bare exception handlers, unsafe JSON serialization, and inconsistent CrewAI output handling. The codebase has 585 `except Exception` occurrences across 196 files (far more than the 44+ initially estimated in CONCERNS.md -- the 44+ figure refers only to the worst offenders with bare `except Exception:` without `as e`). There are 40 `json.dumps()` calls missing `default=str`, and 5 locations in `crew_factory.py` using the fragile `str(result.raw)` pattern for crew output.

The project already has strong foundations: a custom exception hierarchy in `src/finwiz/exceptions/`, Pydantic export schemas in `src/finwiz/schemas/crew_exports.py`, and crews already using `output_pydantic` in tasks.yaml. The cleanup is a matter of applying existing patterns consistently rather than inventing new ones.

**Primary recommendation:** Prioritize the 46 bare `except Exception:` (no alias) handlers first since they silently swallow errors. Then fix the 40 missing `default=str` calls. Finally, standardize crew output handling in `crew_factory.py` to use the Pydantic `.pydantic` attribute that CrewAI already provides.

## Standard Stack

### Core (Already in Project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | >=2.11.7 | Structured validation, crew output schemas | Already used throughout schemas/, required by CrewAI |
| ruff | >=0.11.13 | Linting, can enforce BLE001 (blind-except) rule | Already configured in pyproject.toml |
| CrewAI | >=1.5.0 | `output_pydantic` on tasks for structured output | Already used in all crew task configs |
| pytest-mock | >=3.14.1 | Testing (mocker fixtures only, unittest.mock banned) | Already project standard |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | N/A | JSON serialization with `default=str` | Every json.dumps call |
| logging (stdlib) | N/A | Error context logging | Every exception handler |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom exception classes | Built-in exceptions only | Custom exceptions provide better domain context; project already has hierarchy in `exceptions/` |
| `default=str` everywhere | Custom JSON encoder class | `default=str` is simpler, consistent with CLAUDE.md standard, no new code needed |
| Per-file exception fixes | ruff BLE001 auto-enforcement | BLE001 would flag too many false positives initially (585 occurrences). Manual fix with BLE001 enabled after cleanup is better. |

## Architecture Patterns

### Existing Exception Hierarchy (Use and Extend)

```
Exception (Python builtin)
├── DataQualityError (finwiz.exceptions.data_quality)
│   ├── MissingRequiredFieldError
│   └── GradeScoreMismatchError
├── PortfolioRebalancingError (finwiz.exceptions.orchestrator)
│   └── InsufficientPriceDataError
├── OptimizationFailedError (finwiz.exceptions.orchestrator)
├── ConfigurationError (finwiz.validation.template / finwiz.config.manager)
├── AIOutputError (finwiz.validation.ai_output)
│   ├── OutputParsingError
│   ├── MissingRequiredFieldError
│   └── ToolCallInsteadOfAnalysisError
├── PerplexityError (finwiz.tools.perplexity_errors)
│   ├── PerplexityRateLimitError
│   ├── PerplexityAPIError
│   ├── PerplexityTimeoutError
│   └── PerplexityConnectionError
├── PriceServiceError (finwiz.tools.portfolio_price_service)
│   └── PriceDataUnavailableError
├── JSONParsingError (finwiz.infrastructure.json.error_handlers)
├── SchemaValidationError (finwiz.infrastructure.json.error_handlers)
├── DataMergeError (finwiz.orchestrators.deep_analysis_merger)
└── CoinMarketCapException (finwiz.tools.coinmarketcap_tool)
```

### Pattern 1: Exception Replacement Strategy

**What:** Replace bare `except Exception` with specific types based on context.

**Decision matrix for which exception to catch:**

| Code Context | Replace `except Exception` with |
|---|---|
| JSON parsing (json.loads, json.dumps) | `except (json.JSONDecodeError, TypeError, ValueError)` |
| HTTP/API calls (requests.*) | `except (requests.exceptions.RequestException, ConnectionError, TimeoutError)` |
| File I/O operations | `except (OSError, FileNotFoundError, PermissionError)` |
| Pydantic validation | `except (pydantic.ValidationError, ValueError)` |
| yfinance data access | `except (KeyError, ValueError, AttributeError)` |
| Dictionary/data access | `except (KeyError, TypeError, ValueError)` |
| Numeric computation | `except (ValueError, ZeroDivisionError, OverflowError)` |
| CrewAI crew execution | `except Exception as e:` (KEEP -- system boundary, but must log) |
| Import fallbacks | `except ImportError:` (already correct in many places) |
| Configuration loading | `except (KeyError, ValueError, ConfigurationError)` |

**When to KEEP `except Exception as e:`:** Only at system boundaries where any failure must be caught for graceful degradation. The 8 locations in `crew_factory.py` are legitimate because crew execution can fail in unpredictable ways. These should keep `except Exception as e:` but MUST log with `exc_info=True`.

### Pattern 2: json.dumps Safety

**What:** Every `json.dumps()` call uses `default=str`.

**Standard pattern:**
```python
# Always use default=str
json.dumps(data, indent=2, default=str)

# For HTTP request bodies (no indent needed but still safe)
json.dumps(payload, default=str)

# For logging context
json.dumps(context, indent=2, default=str)
```

**Exception:** `json.dumps()` used for schema export (`schemas/export.py`) where the data is guaranteed to be JSON-serializable Pydantic schema dicts. The `ensure_ascii=False` calls are fine as-is but should still add `default=str` for safety.

### Pattern 3: CrewAI Output via Pydantic

**What:** Access crew results through `.pydantic` attribute instead of `str(result.raw)`.

**Current anti-pattern in `crew_factory.py`:**
```python
# BAD: Loses all structure, fragile
result_data = {
    "crypto_analysis_result": str(result.raw) if hasattr(result, "raw") else str(result),
}
```

**Standard pattern from CrewAI docs (Context7 verified, HIGH confidence):**
```python
# GOOD: Structured access via Pydantic model
if result.pydantic:
    result_data = result.pydantic.model_dump()
elif result.json_dict:
    result_data = result.json_dict
else:
    # Fallback: parse raw
    result_data = {"raw_output": result.raw}
```

**CrewAI `CrewOutput` object attributes (Context7 verified):**
- `result.raw` -- Raw string output
- `result.pydantic` -- Pydantic model if `output_pydantic` was set on task
- `result.json_dict` -- Dict if `output_json` was set on task
- `result.tasks_output` -- List of individual task outputs
- `result.token_usage` -- Token usage stats
- `result["field"]` -- Dict-style access (delegates to pydantic/json_dict)
- `result.to_dict()` -- Convert to dict

**The project's crews already configure `output_pydantic` on their final tasks:**
- `crypto_crew` -> `CryptoCrewExport`
- `stock_crew` -> `StockCrewExport` (via `EnrichedAnalysis`)
- `etf_crew` -> `ETFCrewExport`
- `investment_discovery_crew` -> `DiscoveryCrewExport`
- `portfolio_rebalancing_crew` -> `RebalancingCrewExport`

So `result.pydantic` SHOULD be populated after kickoff. The existing `str(result.raw)` pattern discards this structured data.

### Anti-Patterns to Avoid

- **Silent swallowing:** `except Exception: pass` or `except Exception: continue` -- hides bugs entirely. Found in 15+ places.
- **String-ifying Pydantic models:** `str(result.raw)` when `.pydantic` is available. Loses all structure.
- **Inconsistent json.dumps:** Some calls have `default=str`, some don't. Crashes are intermittent, depends on what data flows through.
- **Re-catching same exception:** Some code has nested try/except that catch the same exception type.
- **Bare except without logging:** `except Exception:` with no `as e` binding means the error is unknowable.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Exception type mapping per context | Massive switch/case logic | Decision matrix above + code review | Each context is different; simple heuristic |
| JSON serialization safety | Custom JSON encoder class | `default=str` parameter | CLAUDE.md explicitly mandates this pattern |
| Crew output parsing | Custom parser per crew | `result.pydantic.model_dump()` | CrewAI already does the parsing when `output_pydantic` is set |
| Exception hierarchy | New base classes | Extend existing `finwiz.exceptions.*` | Hierarchy already exists, just under-used |
| Ruff enforcement | Custom AST checker | Enable `BLE001` rule in ruff config | Ruff already has the rule, just not enabled |

**Key insight:** All three problems have existing project solutions that are inconsistently applied. The work is standardization, not invention.

## Common Pitfalls

### Pitfall 1: Over-Specificity in Exception Handlers

**What goes wrong:** Catching too narrow an exception type causes new failure modes to be unhandled.
**Why it happens:** Zealous replacement of `except Exception` with a single specific type.
**How to avoid:** Catch tuples of related exceptions. Example: `except (ValueError, KeyError, TypeError)` not just `except ValueError`.
**Warning signs:** New test failures after exception replacement that weren't there before.

### Pitfall 2: Breaking Graceful Degradation

**What goes wrong:** Tools/orchestrators that previously returned fallback data now crash.
**Why it happens:** The bare `except Exception` was serving as a catch-all for graceful degradation.
**How to avoid:** For tool `_run()` methods, keep a broad handler as the LAST catch, but add specific handlers before it. For system boundaries (crew_factory, orchestrators), `except Exception as e:` is acceptable with proper logging.
**Warning signs:** Integration tests failing because expected fallback paths are no longer reached.

### Pitfall 3: json.dumps on Request Bodies

**What goes wrong:** Adding `default=str` to `json.dumps()` used for HTTP request bodies (e.g., `requests.post(data=json.dumps(payload))`) silently converts non-serializable types to strings.
**Why it happens:** API endpoints expect exact types, not string-ified versions.
**How to avoid:** For HTTP request payloads (`requests.post(data=...)`), ensure the payload is already clean JSON types BEFORE `json.dumps`. The `default=str` should still be added for safety but indicates a data issue if triggered.
**Warning signs:** API calls returning 400 errors after the fix.

### Pitfall 4: CrewAI output_pydantic May Be None

**What goes wrong:** Accessing `result.pydantic` without checking returns `None`, causing AttributeError on `.model_dump()`.
**Why it happens:** LLM may return malformed output that fails Pydantic validation, causing `.pydantic` to be None even though `output_pydantic` was configured.
**How to avoid:** Always check `if result.pydantic:` before accessing. Have fallback path to `result.json_dict` then `result.raw`.
**Warning signs:** AttributeError on NoneType in crew factory methods.

### Pitfall 5: Existing Tests May Assert on Exception Swallowing

**What goes wrong:** Tests that relied on broad exception handling now fail because specific exceptions propagate.
**Why it happens:** Changing `except Exception` to `except ValueError` means `KeyError` now propagates.
**How to avoid:** Run full test suite after each file change. Review test assertions that check for error fallback behavior.
**Warning signs:** Tests checking fallback responses fail.

## Code Examples

### Exception Replacement: Tool _run() Method

Source: Existing project pattern analysis

```python
# BEFORE (current)
def _run(self, ticker: str, **kwargs: Any) -> str:
    try:
        result = self._analyze(ticker)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

# AFTER (corrected)
def _run(self, ticker: str, **kwargs: Any) -> str:
    try:
        result = self._analyze(ticker)
        return json.dumps(result, indent=2, default=str)
    except (ValueError, KeyError) as e:
        logger.warning(f"Analysis failed for {ticker}: {e}", extra={"ticker": ticker})
        return json.dumps({"error": str(e), "ticker": ticker}, default=str)
    except requests.exceptions.RequestException as e:
        logger.error(f"API call failed for {ticker}: {e}", extra={"ticker": ticker})
        return json.dumps({"error": f"API error: {e}", "ticker": ticker}, default=str)
    except Exception as e:
        logger.error(f"Unexpected error analyzing {ticker}: {e}", exc_info=True)
        return json.dumps({"error": str(e), "ticker": ticker}, default=str)
```

### json.dumps Safety Fix

```python
# BEFORE: Missing default=str
json.dumps(error_context, indent=2)

# AFTER: Safe serialization
json.dumps(error_context, indent=2, default=str)
```

### CrewAI Output Standardization

Source: CrewAI official docs (Context7 /crewaiinc/crewai)

```python
# BEFORE (crew_factory.py current pattern)
result_data = {
    "crypto_analysis_result": str(result.raw) if hasattr(result, "raw") else str(result),
    "core_analysis_completed": True,
    "crypto_analysis_success": True,
}

# AFTER (using Pydantic output)
if result.pydantic:
    result_data = {
        "crypto_analysis_result": result.pydantic.model_dump(),
        "core_analysis_completed": True,
        "crypto_analysis_success": True,
    }
elif result.json_dict:
    result_data = {
        "crypto_analysis_result": result.json_dict,
        "core_analysis_completed": True,
        "crypto_analysis_success": True,
    }
else:
    logger.warning("Crypto crew returned no structured output, falling back to raw")
    result_data = {
        "crypto_analysis_result": result.raw,
        "core_analysis_completed": True,
        "crypto_analysis_success": True,
    }
```

### Adding Specific Exception Handlers to Orchestrators

```python
# BEFORE (orchestrators/portfolio_review_orchestrator.py)
try:
    value = float(holding.get("current_value", 0))
except Exception:
    value = 0.0

# AFTER
try:
    value = float(holding.get("current_value", 0))
except (ValueError, TypeError):
    value = 0.0
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| `except Exception:` catch-all | Specific exception types with context | Python best practice (PEP 8) | Better debugging, fewer hidden bugs |
| `json.dumps(data)` | `json.dumps(data, default=str)` | Project standard (CLAUDE.md) | Prevents TypeError on datetime/Decimal |
| `str(result.raw)` for crew output | `result.pydantic.model_dump()` | CrewAI docs pattern | Preserves structure, enables validation |
| ruff without BLE001 | ruff with BLE001 enabled | Can enable now | Prevents new bare exceptions |

**Deprecated/outdated:**
- `str(result)` or `str(result.raw)`: CrewAI provides structured access via `.pydantic`, `.json_dict`, `[]` indexing, and `.to_dict()`. Using `str()` discards all structure.

## Quantitative Assessment

### ERRH-01: Bare Exception Replacement

**Total `except Exception` occurrences:** 585 across 196 files
**Bare `except Exception:` (no alias, most dangerous):** 46 across 44 files
**`except Exception as e:` with logging:** ~400 (many legitimate at system boundaries)
**`except Exception as e:` without proper logging:** ~139 (need review)

**Categorization of 46 bare handlers by file domain:**

| Domain | Count | Files | Risk Level |
|--------|-------|-------|------------|
| tools/ | 22 | etf_data_fetchers, screening_*, scoring_*, price_service, etc. | HIGH - silent data loss |
| orchestrators/ | 4 | portfolio_rebalancing, portfolio_review_orchestrator | MEDIUM - graceful degradation |
| validation/ | 6 | scripts, sec_citation, report | MEDIUM - validation bypass |
| infrastructure/ | 4 | cache, health/checks, logging/enhanced | LOW - infrastructure resilience |
| quantitative/ | 3 | backtesting_performance, performance_benchmarks | MEDIUM - calculation bypass |
| integration/ | 1 | cache | LOW - caching resilience |
| tools/enhanced_* | 6 | enhanced_sec, perplexity_analysis_integration | HIGH - silent API failures |

**Priority order:** tools/ (22 bare) > validation/ (6 bare) > orchestrators/ (4 bare) > others

### ERRH-02: json.dumps Missing default=str

**Total json.dumps calls:** 47 across 25 files
**Already have default=str:** 7 calls
**Missing default=str:** 40 calls across 18 files

**Breakdown by domain:**

| Domain | Missing Count | Key Files |
|--------|--------------|-----------|
| infrastructure/logging/enhanced.py | 10 | Logging context -- datetime in data will crash |
| tools/ | 19 | Various analysis tools -- results may contain datetime/Decimal |
| crew_factory.py | 3 | Fallback response data |
| orchestrators/ | 1 | portfolio_review_orchestrator |
| Other | 7 | perplexity, benchmark CLI |

### ERRH-03: CrewAI Output Standardization

**`str(result.raw)` / `str(result)` occurrences in crew_factory.py:** 5 (crypto, stock, etf, rebalancing, discovery)
**Existing correct `.pydantic` usage:** 2 files (validation_orchestrator.py, deep_analysis_pipeline.py)
**Crews with `output_pydantic` configured:** All 7 crews

## Open Questions

1. **Should `except Exception as e:` with `exc_info=True` be left as-is?**
   - What we know: ruff BLE001 exempts exceptions that log with `exc_info`. These are functionally correct.
   - What's unclear: Whether to still narrow them or leave them for a later pass.
   - Recommendation: Leave `except Exception as e:` with `exc_info=True` for Phase 1. Focus on the 46 bare handlers and the ~139 without proper logging first. Narrowing logged exceptions is a Phase 5 (tests) activity.

2. **Should ruff BLE001 be enabled now or after cleanup?**
   - What we know: Enabling now would flag 585 occurrences, making CI red.
   - What's unclear: Whether to enable with per-file ignores or wait.
   - Recommendation: Enable BLE001 AFTER the cleanup, not before. Add it in Phase 5 once all handlers are clean.

3. **How do downstream consumers handle the crew_factory output change?**
   - What we know: `crew_factory.py` returns dicts consumed by flow state. Changing from `str` to `dict` changes the type of `*_analysis_result` keys.
   - What's unclear: Every consumer of these dict values.
   - Recommendation: Search for all references to `crypto_analysis_result`, `stock_analysis_result`, `etf_analysis_result` to map consumers. The change from string to dict may require consumer updates.

## Sources

### Primary (HIGH confidence)
- Context7 `/crewaiinc/crewai` -- CrewAI output_pydantic, CrewOutput attributes, structured output patterns
- Codebase analysis: 196 files with `except Exception`, 25 files with `json.dumps`, crew_factory.py and all crew implementations
- ruff documentation: BLE001 (blind-except) rule definition and exemptions
- Project CLAUDE.md: `json.dumps` always with `default=str`, Pydantic models in `schemas/`, `output_pydantic` requirement

### Secondary (MEDIUM confidence)
- PEP 8 exception handling recommendations (stable, well-established)
- Python documentation on exception hierarchy

### Tertiary (LOW confidence)
- None -- all findings verified against codebase and official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in project, no new dependencies
- Architecture: HIGH -- patterns verified from codebase analysis and CrewAI docs
- Pitfalls: HIGH -- derived from actual codebase patterns and CrewAI docs
- Quantitative counts: HIGH -- grep-verified against actual source files

**Research date:** 2026-02-07
**Valid until:** 2026-03-07 (stable domain, no fast-moving dependencies)
