---
phase: 15-macro-context
plan: 01
subsystem: scoring
tags: [macro, yield-curve, vix, fed-rate, sensitivity, pydantic]

# Dependency graph
requires:
  - phase: 14-sentiment-scoring
    provides: SentimentScorer component pattern, ScoringThresholds additive overlay fields
provides:
  - MacroScorer component scorer with VIX/yield-curve/Fed-rate composite scoring
  - YieldCurveRegime literal type and MacroScore Pydantic model
  - Macro threshold configuration in ScoringThresholds
  - Per-asset-class sensitivity coefficients (stock=1.0, etf=0.7, crypto=0.3)
affects: [15-02 composite wiring, 15-03 FRED data collection, deep-analysis-scorer]

# Tech tracking
tech-stack:
  added: []
  patterns: [component-scorer-pattern, yield-curve-regime-classification, asset-class-sensitivity-scaling]

key-files:
  created:
    - src/finwiz/scoring/macro_scorer.py
    - tests/unit/scoring/test_macro_scorer.py
  modified:
    - src/finwiz/schemas/macro.py
    - src/finwiz/scoring/thresholds.py
    - src/finwiz/schemas/__init__.py

key-decisions:
  - "MacroScorer follows exact SentimentScorer component pattern: (score_or_None, details_dict)"
  - "Yield curve classified into 4 regimes at boundaries: 0.0, 0.5, 2.0"
  - "No feature flag logic in MacroScorer -- gating deferred to DeepAnalysisScorer (Plan 15-02)"

patterns-established:
  - "Component scorer pattern: __init__(thresholds), calculate_X_score(data, ...) -> tuple[float | None, dict]"
  - "Per-asset-class sensitivity scaling via ScoringThresholds fields"

# Metrics
duration: 5min
completed: 2026-02-09
---

# Phase 15 Plan 01: MacroScorer Summary

**MacroScorer component scorer with yield-curve regime classification, VIX/Fed-rate composite scoring, and per-asset-class sensitivity coefficients**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-09T09:08:31Z
- **Completed:** 2026-02-09T09:13:50Z
- **Tasks:** 3/3
- **Files modified:** 5

## Accomplishments

- MacroScorer class implementing full component scorer pattern with VIX, yield-curve, and Fed-rate scoring
- Yield curve regime classification with boundary-tested thresholds: inverted (<0), flat (0-0.5), normal (0.5-2.0), steep (>=2.0)
- Per-asset-class sensitivity coefficients: stock=1.0, etf=0.7, crypto=0.3 (configurable via ScoringThresholds)
- Comprehensive test suite with 31 tests covering all edge cases, boundary values, and sensitivity ordering

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend macro schema and scoring thresholds** - `aefe66b` (feat)
2. **Task 2: Create MacroScorer class** - `961e4d3` (feat)
3. **Task 3: MacroScorer test suite** - `e1a5558` (test)

## Files Created/Modified

- `src/finwiz/scoring/macro_scorer.py` - MacroScorer component scorer (239 lines)
- `tests/unit/scoring/test_macro_scorer.py` - 31 tests across 6 test classes (265 lines)
- `src/finwiz/schemas/macro.py` - Added YieldCurveRegime literal type and MacroScore Pydantic model
- `src/finwiz/scoring/thresholds.py` - Added macro scoring configuration (yield curve, VIX, Fed rate, sensitivity)
- `src/finwiz/schemas/__init__.py` - Exported MacroScore and YieldCurveRegime

## Decisions Made

- MacroScorer follows exact SentimentScorer component pattern: returns (score_or_None, details_dict)
- Yield curve boundaries at 0.0/0.5/2.0 (configurable via ScoringThresholds)
- No feature flag logic in MacroScorer -- gating deferred to DeepAnalysisScorer (Plan 15-02)
- Confidence = count of non-None fields out of 5 key fields (vix, fed_rate, cpi_yoy, treasury_10y, treasury_2y)
- All-None MacroSnapshot returns score=0.0 (not None), since the snapshot exists but has no contributing data

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- MacroScorer ready for composite scoring wiring in Plan 15-02
- ScoringThresholds extended with macro fields; weight_macro_overlay already exists (default 0.0)
- All 242 scoring tests pass with zero regressions
- All quality gates (lint + test + mock check + docs validation) pass

---
*Phase: 15-macro-context*
*Completed: 2026-02-09*
