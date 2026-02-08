# v3 Milestone Audit: Performance & Risk Analysis

---
milestone: v3
audited: 2026-02-08
status: gaps_found
scores:
  requirements: 12/13
  phases: 3/3
  integration: 29/30
  flows: 1/1
gaps:
  requirements:
    - "RISK-04: Stress test HTML template exists but not wired into FinalReportGenerator"
  integration:
    - "stress_test_results stored in state but FinalReportGenerator._prepare_template_data() doesn't pass it to template"
    - "stress_test_section.html exists but not included in crew_reports/final_report.html"
  flows: []
tech_debt: []
---

## Requirements Coverage

| Requirement | Phase | Status | Evidence |
|-------------|-------|--------|----------|
| PERF-01: Async data adapters | 9 | MET | 5 async adapters, DataSourceOrchestrator fully async |
| PERF-02: Configurable parallel limit | 9 | MET | `DEEP_ANALYSIS_BATCH_SIZE=10` default, env-configurable |
| PERF-03: BatchDataPreFetcher integrated | 9 | MET | `run_batch_prefetch()` called before concurrent analysis |
| PERF-04: Batch API calls | 9 | MET | `prefetched_data` threaded through entire pipeline |
| CACHE-01: Tiered eviction | 10 | MET | `CacheTier(HOT/WARM/COLD)` in `manager.py:43`, `calculate_tier()` method, tiered eviction in `_ensure_memory_capacity()` |
| CACHE-02: Type-aware TTLs | 10 | MET | `CacheTTLRegistry` in `ttl_config.py:48` — market:900s, fundamentals:86400s, static:604800s, env overrides |
| CACHE-03: Cache metrics | 10 | MET | `CacheMetricsLogger` in `metrics_logger.py:14`, registered in `orchestrator.py:63-70`, `log_summary()` called post-reporting |
| COST-01: LiteLLM tracking | 10 | MET | `litellm.completion_cost()` in `litellm_callback.py:95`, crew attribution via `contextvars` |
| COST-02: Per-crew costs | 10 | MET | `get_cost_summary()` returns per-crew dict, `log_cost_summary()` called in `orchestrator.py:281`, stored in state |
| RISK-01: Market crash | 11 | MET | `_apply_market_crash()` in `engine.py:91` — beta-adjusted, crypto 1.5x, bonds -0.3x |
| RISK-02: Rate shock | 11 | MET | `_apply_rate_shock()` in `engine.py:114` — duration-based bonds, growth/value sector differentiation |
| RISK-03: Sector shock | 11 | MET | `_apply_sector_shock()` in `engine.py:150` — target sector + spillover to non-target |
| RISK-04: Stress in HTML | 11 | PARTIAL | Template `stress_test_section.html` exists (80 lines), engine runs, results stored in state — but NOT wired into `FinalReportGenerator._prepare_template_data()` or `final_report.html` |

**Summary:** 12/13 requirements satisfied (92.3%), 1 partial (RISK-04 rendering gap)

## Phase Status

| Phase | Name | Status | Plans | Tests |
|-------|------|--------|-------|-------|
| 9 | Async & Batch Performance | COMPLETE | 09-01, 09-02 | 82 tests |
| 10 | Cache & Cost Observability | COMPLETE | 10-01, 10-02 | 32 tests |
| 11 | Risk Stress Testing | COMPLETE (backend) | 11-01, 11-02 | 28 tests |

## Cross-Phase Integration

**Status:** 29/30 connections verified (1 gap)

### Connected (29)

Phase 9 → Phase 10:
- BatchDataPreFetcher populates `state.prefetched_data` → StressTestOrchestrator reads it for enrichment
- CacheManager used throughout data collection → CacheMetricsLogger aggregates stats

Phase 10 → Flow:
- `enable_token_monitoring()` called in `orchestrator.py:52`
- `CacheMetricsLogger.register_cache()` in `orchestrator.py:63-70`
- `set_crew_context()` wraps `crew.kickoff()` in `crew_execution.py:73-101`
- `log_cost_summary()` + state fields populated in `orchestrator.py:279-286`
- `cache_metrics.log_summary()` in `orchestrator.py:270`

Phase 11 → Flow:
- StressTestOrchestrator reads `state.deep_analysis_results` and `state.prefetched_data`
- Runs after deep analysis (Phase 3.5) in `orchestrator.py:222-236`
- Results stored in `state.stress_test_results` and `state.stress_test_count`

### Gap (1)

- **`state.stress_test_results` → `FinalReportGenerator`**: Data stored in state but `_prepare_template_data()` (line 108-135) doesn't include it. Template `stress_test_section.html` exists but isn't included in `crew_reports/final_report.html`.

## E2E Flow

```
main.py → core → flows/orchestrator.py → run_sequential_workflow()
  Phase 1: validation                                           ✅
  Phase 2: portfolio review                                     ✅
  Phase 3: deep analysis (batch prefetch → concurrent analysis) ✅
    └─ cost tracking per crew via contextvars                   ✅
  Phase 3.5: stress testing (3 default scenarios)               ✅
    └─ results stored in state                                  ✅
  Phase 4: discovery                                            ✅
  Phase 5: alternative matching                                 ✅
  Phase 6: reporting                                            ✅
    └─ stress test section in HTML report                       ❌ NOT WIRED
  Post-flow: cache metrics summary                              ✅
  Post-flow: LLM cost summary                                   ✅
```

## Tests

- 4501 total tests passing (62 new for Phases 10-11)
- 66.85% coverage (above 65% threshold)
- All pre-commit hooks pass (14/14)
- `make check` passes clean

## Gap Detail: RISK-04

**What exists:**
- `stress_test_section.html` (80 lines, Jinja2 template with scenario cards)
- `state.stress_test_results` populated with model_dump() data
- Engine runs 3 default scenarios successfully

**What's missing:**
1. `FinalReportGenerator._prepare_template_data()` doesn't pass `stress_test_results` to template context
2. `crew_reports/final_report.html` doesn't include `stress_test_section.html`

**Fix scope:** ~10 lines across 2 files (report generator + main template)

---
*Audit performed: 2026-02-08*
*Phase 9 committed: c37b5a4*
*Phase 10+11 committed: c6a28cb*
