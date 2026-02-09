---
phase: 16-report-enrichment
plan: 01
subsystem: data
tags: [finnhub, economic-calendar, sentiment, macro, pydantic, feature-flag]

# Dependency graph
requires:
  - phase: 13-news-sentiment
    provides: FinnhubNewsAdapter, NewsSentimentResult, SentimentMacroCollector
  - phase: 15-macro-context
    provides: MacroSnapshot, MacroScorer, FRED adapter
provides:
  - EconomicCalendarAdapter with Finnhub integration and session caching
  - EconomicEvent, EarningsEvent, EconomicCalendar Pydantic schemas
  - sentiment_summary field on EnrichedAnalysis (score, confidence, top headlines)
  - macro_snapshot field on FinwizState for report-time access
  - collect_economic_calendar() on SentimentMacroCollector
  - economic_calendar feature flag (FF_ECONOMIC_CALENDAR, default off)
affects: [16-02-PLAN, 16-03-PLAN, reporting, templates]

# Tech tracking
tech-stack:
  added: [finnhub (calendar_economic, earnings_calendar)]
  patterns: [lazy-import Finnhub client, session-level caching, per-ticker error isolation, sentiment summary extraction]

key-files:
  created:
    - src/finwiz/schemas/economic_calendar.py
    - src/finwiz/data/adapters/economic_calendar_adapter.py
    - tests/unit/data/test_economic_calendar_adapter.py
    - tests/unit/data/test_sentiment_summary_persistence.py
  modified:
    - src/finwiz/config/features/definitions.py
    - src/finwiz/flow_state_models.py
    - src/finwiz/analysis/deep_analysis_pipeline.py
    - src/finwiz/data/sentiment_collector.py
    - src/finwiz/orchestrators/deep_analysis_orchestrator.py
    - src/finwiz/schemas/hybrid_analysis/enriched.py
    - src/finwiz/schemas/__init__.py
    - src/finwiz/data/adapters/__init__.py

key-decisions:
  - "sentiment_summary added as optional field on EnrichedAnalysis (auto-persisted in enriched JSON)"
  - "Confidence derived from article count: min(1.0, count/10) as simple heuristic"
  - "macro_snapshot set once per session in DeepAnalysisOrchestrator._ensure_macro_snapshot_on_state()"
  - "Economic calendar filters US events + high-impact keywords (FOMC, CPI, GDP, employment, PMI)"

patterns-established:
  - "_build_sentiment_summary() extracts top 5 headlines from raw_data for report rendering"
  - "_ensure_macro_snapshot_on_state() sets state.macro_snapshot once, skips if already present"

# Metrics
duration: 10min
completed: 2026-02-09
---

# Phase 16 Plan 01: Data Infrastructure for Report Enrichment Summary

**EconomicCalendarAdapter with Finnhub integration, sentiment_summary in enriched JSON, and macro_snapshot on FinwizState for report-time access**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-09T09:59:08Z
- **Completed:** 2026-02-09T10:09:00Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- EconomicCalendarAdapter fetches and caches Finnhub economic and earnings calendar data with graceful error handling and per-ticker failure isolation
- Enriched JSON per-holding files now include sentiment_summary with score, confidence, article_count, and top 5 headlines
- FinwizState.macro_snapshot is set once per session during deep analysis and available at report generation time
- Economic calendar gated behind feature flag (FF_ECONOMIC_CALENDAR, default off)
- 25 new tests, full suite: 4740 passing, 67.42% coverage

## Task Commits

Each task was committed atomically:

1. **Task 1: Create EconomicCalendar schemas, adapter, and feature flag** - `104783f` (feat)
2. **Task 2: Persist sentiment_summary in enriched JSON and add macro_snapshot to FinwizState** - `60abc94` (feat)

## Files Created/Modified
- `src/finwiz/schemas/economic_calendar.py` - EconomicEvent, EarningsEvent, EconomicCalendar Pydantic models
- `src/finwiz/data/adapters/economic_calendar_adapter.py` - Finnhub economic calendar adapter with session caching
- `src/finwiz/config/features/definitions.py` - Added economic_calendar feature flag
- `src/finwiz/flow_state_models.py` - Added macro_snapshot field to FinwizState
- `src/finwiz/analysis/deep_analysis_pipeline.py` - Added _build_sentiment_summary() and wired sentiment_summary into enriched analysis
- `src/finwiz/schemas/hybrid_analysis/enriched.py` - Added sentiment_summary optional field to EnrichedAnalysis
- `src/finwiz/data/sentiment_collector.py` - Added collect_economic_calendar() method
- `src/finwiz/orchestrators/deep_analysis_orchestrator.py` - Added _ensure_macro_snapshot_on_state() for one-time macro snapshot
- `src/finwiz/schemas/__init__.py` - Export new economic calendar schemas
- `src/finwiz/data/adapters/__init__.py` - Export EconomicCalendarAdapter
- `tests/unit/data/test_economic_calendar_adapter.py` - 9 adapter tests
- `tests/unit/data/test_sentiment_summary_persistence.py` - 16 sentiment/macro/calendar tests

## Decisions Made
- Added sentiment_summary as an optional field on EnrichedAnalysis rather than modifying JSON post-serialization, so it is automatically included when model_dump_json() is called
- Confidence is computed as min(1.0, article_count / 10.0) as a simple heuristic (0 articles = 0.0, 10+ articles = 1.0)
- Macro snapshot is set on FinwizState in the orchestrator (not in the pipeline) to maintain clean separation of concerns
- Economic calendar filters for US events and high-impact keywords to reduce noise

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed mypy type error in _ensure_macro_snapshot_on_state**
- **Found during:** Task 2 (commit attempt)
- **Issue:** `macro.model_dump() if hasattr(...) else macro` returned `dict | MacroSnapshot`, incompatible with `dict | None` field type
- **Fix:** Added explicit type annotation `snapshot_dict: dict[str, Any]` with proper conversion
- **Files modified:** src/finwiz/orchestrators/deep_analysis_orchestrator.py
- **Verification:** mypy passes, pre-commit hooks pass
- **Committed in:** 60abc94 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Minimal - type annotation fix for mypy strictness. No scope creep.

## Issues Encountered
- Lazy imports in methods required patching at source module level in tests (not at consuming module level). Resolved by patching `finwiz.data.sentiment_collector.SentimentMacroCollector` instead of `finwiz.orchestrators.deep_analysis_orchestrator.SentimentMacroCollector`.

## User Setup Required
None - no external service configuration required. Economic calendar uses existing FINNHUB_API_KEY and is gated behind FF_ECONOMIC_CALENDAR=false by default.

## Next Phase Readiness
- Economic calendar adapter ready for 16-02 (sentiment/macro report section templates)
- sentiment_summary available in enriched JSON for 16-02 headline rendering
- macro_snapshot on FinwizState ready for 16-03 report generation access
- All feature flags default off, safe for production

---
*Phase: 16-report-enrichment*
*Completed: 2026-02-09*
