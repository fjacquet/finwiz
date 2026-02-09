---
phase: 15-macro-context
plan: 02
subsystem: scoring
tags: [macro, overlay, vix, fed-rate, yield-curve, composite-score, feature-flag]

# Dependency graph
requires:
  - phase: 15-01
    provides: "MacroScorer component scorer with calculate_macro_score() returning (score_or_None, details)"
provides:
  - "_calculate_macro_overlay() wired into _compute_weighted_score() with 4-gate safety"
  - "DeepAnalysisResult.macro_score and .macro_regime optional fields"
  - "assess_market_regime() uses real VIX from macro_snapshot"
  - "_estimate_interest_rate() accepts real Fed rate from FRED"
  - "10 regression/integration tests for macro overlay"
affects: [15-03, reporting, deep-analysis-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: ["4-gate additive overlay (flag->weight->data->confidence) reused from sentiment"]

key-files:
  created: []
  modified:
    - "src/finwiz/scoring/deep_analysis_scorer.py"
    - "src/finwiz/flow_state_models.py"
    - "src/finwiz/scoring/score_result_builder.py"
    - "src/finwiz/tools/scoring/scoring_criteria.py"
    - "src/finwiz/orchestrators/extraction/market_context.py"
    - "tests/unit/scoring/test_deep_analysis_scorer.py"

key-decisions:
  - "Macro overlay uses identical 4-gate safety pattern as sentiment overlay (Phase 14)"
  - "Both overlays stack: composite = base + sentiment_adj + macro_adj, clamped per-overlay"
  - "Quality company adaptive weights (50/25/25) coexist with macro overlay without interference"

patterns-established:
  - "Additive overlay stacking: multiple overlays applied sequentially after base composite"
  - "Hardcoded value replacement: fallback chain (real data -> legacy field -> hardcoded default)"

# Metrics
duration: 6min
completed: 2026-02-09
---

# Phase 15 Plan 02: Composite Wiring Summary

**MacroScorer wired into DeepAnalysisScorer with 4-gate additive overlay, real VIX/Fed-rate in scoring_criteria and market_context, 10 regression tests proving backward compatibility**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-09T09:16:52Z
- **Completed:** 2026-02-09T09:23:21Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Macro overlay wired into `_compute_weighted_score()` after sentiment overlay using same 4-gate safety pattern (feature flag, weight, data, confidence)
- `DeepAnalysisResult` extended with optional `macro_score` and `macro_regime` fields (backward compatible, None defaults)
- Hardcoded VIX=20.0 and inflation=3.0 in `assess_market_regime()` replaced with real `macro_snapshot` data when available
- Hardcoded interest rates in `_estimate_interest_rate()` replaced with real Fed rate from FRED when available
- 10 new regression/integration tests in `TestMacroOverlay` class, all 252 scoring tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire macro overlay and replace hardcoded values** - `e1af613` (feat)
2. **Task 2: Macro overlay regression and integration tests** - `420ddf8` (test)

## Files Created/Modified
- `src/finwiz/scoring/deep_analysis_scorer.py` - Added MacroScorer import, `_macro_scorer` init, `_calculate_macro_overlay()` method, macro wiring in `_compute_weighted_score()`
- `src/finwiz/flow_state_models.py` - Added optional `macro_score` and `macro_regime` fields to `DeepAnalysisResult`
- `src/finwiz/scoring/score_result_builder.py` - Passes `macro_score` and `macro_regime` from scores dict to `DeepAnalysisResult` constructor
- `src/finwiz/tools/scoring/scoring_criteria.py` - `assess_market_regime()` reads VIX/CPI from `macro_snapshot` dict with fallback
- `src/finwiz/orchestrators/extraction/market_context.py` - `_estimate_interest_rate()` accepts and uses real Fed rate, added `Any` import
- `tests/unit/scoring/test_deep_analysis_scorer.py` - Added `TestMacroOverlay` class with 10 tests and `_make_macro_snapshot_data()` helper

## Decisions Made
- Macro overlay uses identical 4-gate safety as sentiment (Phase 14) for consistency
- Both overlays stack sequentially: base composite -> sentiment clamp -> macro clamp (each bounded to [0,1])
- Test for 40/30/30 weights uses non-quality-company data to avoid adaptive weights (50/25/25) interfering

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed weight test using quality-company data**
- **Found during:** Task 2 (test_40_30_30_weights_unchanged_with_macro)
- **Issue:** The sample_stock_data fixture triggers quality company detection (ROE=0.25, debt=0.3, margin=0.20), which uses adaptive 50/25/25 weights instead of standard 40/30/30
- **Fix:** Used custom data dict with lower fundamentals (ROE=0.10, debt=1.0, margin=0.08) that does not trigger quality detection, plus added assertion for `is_quality_company is False`
- **Files modified:** tests/unit/scoring/test_deep_analysis_scorer.py
- **Verification:** All 49 tests pass
- **Committed in:** 420ddf8 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Test data adjusted for correctness. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 15 complete: MacroScorer component (15-01) + composite wiring (15-02) both done
- Macro overlay is safe-by-default: feature flag off, weight=0.0, no data = zero impact
- Ready for Phase 16 or any future plan that enables the `macro_scoring` feature flag
- Real VIX/Fed-rate data will flow automatically when FRED data collection is active in the pipeline

## Self-Check: PASSED

All 6 modified files verified present. Both task commits (e1af613, 420ddf8) verified in git log.

---
*Phase: 15-macro-context*
*Completed: 2026-02-09*
