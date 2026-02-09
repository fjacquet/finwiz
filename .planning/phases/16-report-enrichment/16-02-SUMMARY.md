---
phase: 16-report-enrichment
plan: 02
subsystem: reporting
tags: [sentiment, macro-dashboard, traffic-light, fear-greed-gauge, economic-calendar, css, html]

# Dependency graph
requires:
  - phase: 16-report-enrichment
    provides: sentiment_summary in enriched JSON, macro_snapshot on FinwizState, EconomicCalendarAdapter
provides:
  - generate_sentiment_section() with per-holding sentiment cards, French labels, color-coded scores
  - generate_macro_dashboard_section() with 6 traffic-light indicators and Fear & Greed horizontal gauge
  - generate_economic_calendar_section() with economic events and earnings date tables
  - Traffic-light CSS (.traffic-light-green/yellow/red), Fear & Greed gauge CSS, macro-grid CSS, calendar table CSS
  - PythonReportGenerator wired with holdings_sentiment, macro_snapshot, economic_calendar params
  - ReportingOrchestrator._extract_holdings_sentiment() reads enriched JSON for sentiment data
  - ReportingOrchestrator._collect_economic_calendar() calls SentimentMacroCollector
affects: [16-03-PLAN, reporting, templates]

# Tech tracking
tech-stack:
  added: []
  patterns: [traffic-light color coding via CSS classes, Fear & Greed horizontal bar gauge, section generator graceful degradation (return empty string)]

key-files:
  created:
    - tests/unit/reporting/test_sentiment_section_rendering.py
    - tests/unit/reporting/test_macro_dashboard_rendering.py
    - tests/unit/reporting/test_economic_calendar_rendering.py
  modified:
    - src/finwiz/reporting/section_generators.py
    - src/finwiz/reporting/css_styles.py
    - src/finwiz/reporting/python_report_generator.py
    - src/finwiz/orchestrators/reporting_orchestrator.py

key-decisions:
  - "Macro dashboard placed after executive summary (portfolio-level context first)"
  - "Sentiment section placed after holdings analysis (per-holding detail context)"
  - "Economic calendar placed before footer (forward-looking events last)"
  - "Traffic-light thresholds match research: VIX<=20 green, yield_curve>0.50 green, GDP>2.0 green, CPI<3.0 green, fed_rate<3.0 green, unemployment<5.0 green"
  - "Fear & Greed gauge uses pure CSS horizontal bar with 5 gradient segments and absolute-positioned marker"

patterns-established:
  - "Section generators return empty string for None/empty input -- consistent graceful degradation"
  - "New report sections added via delegation methods in PythonReportGenerator (lazy import pattern)"
  - "ReportingOrchestrator extracts sentiment from enriched JSON files (same directory scan as deep analysis)"

# Metrics
duration: 7min
completed: 2026-02-09
---

# Phase 16 Plan 02: Sentiment, Macro Dashboard, and Calendar Report Sections Summary

**Three new consolidated report sections with traffic-light macro indicators, Fear & Greed gauge, per-holding sentiment cards, and economic calendar tables -- all French-labeled with 34 new tests**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-09T10:12:29Z
- **Completed:** 2026-02-09T10:19:30Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Three section generator functions (sentiment, macro dashboard, economic calendar) with graceful None handling
- Traffic-light CSS (green/yellow/red) with threshold-based indicator classification for 6 macro indicators
- Fear & Greed horizontal gauge with 5-segment gradient bar and positioned marker
- All labels in French: "Sentiment de Marche", "Tableau de Bord Macroeconomique", "Calendrier Economique"
- Full report pipeline wired: orchestrator extracts sentiment from enriched JSON, passes macro_snapshot from state, collects economic calendar
- 34 new rendering tests across 3 test files, full suite 4795 passing at 67.41% coverage

## Task Commits

Each task was committed atomically:

1. **Task 1: Create section generators and CSS** - `a20d33a` (feat)
2. **Task 2: Wire sections into pipeline and add tests** - `a7a2cec` (feat)

## Files Created/Modified
- `src/finwiz/reporting/section_generators.py` - Added generate_sentiment_section(), generate_macro_dashboard_section(), generate_economic_calendar_section() with helper functions
- `src/finwiz/reporting/css_styles.py` - Added traffic-light, fear-greed-gauge, macro-grid, and calendar-table CSS classes
- `src/finwiz/reporting/python_report_generator.py` - Added 3 new params, 3 delegation methods, wired sections into HTML template
- `src/finwiz/orchestrators/reporting_orchestrator.py` - Added _extract_holdings_sentiment(), _collect_economic_calendar(), passes macro_snapshot from state
- `tests/unit/reporting/test_sentiment_section_rendering.py` - 10 tests: None handling, French labels, color coding, headline rendering
- `tests/unit/reporting/test_macro_dashboard_rendering.py` - 13 tests: traffic lights, Fear & Greed gauge labels, partial data
- `tests/unit/reporting/test_economic_calendar_rendering.py` - 11 tests: event rendering, earnings dates, row limits, empty lists

## Decisions Made
- Macro dashboard placed after executive summary for portfolio-level context first
- Sentiment section placed after holdings analysis to provide per-holding detail in context
- Economic calendar placed before footer as forward-looking events
- Traffic-light thresholds from research document: VIX, yield curve, GDP, CPI, Fed rate, unemployment
- Fear & Greed gauge as pure CSS horizontal gradient bar (no JS dependency)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. All sections degrade gracefully (empty string) when data is unavailable.

## Next Phase Readiness
- All three report sections ready for 16-03 (per-holding enriched report templates)
- Macro dashboard, sentiment, and calendar sections render correctly with sample data
- CSS classes available for dark mode via media queries
- All feature flags from Plan 16-01 still apply (economic_calendar gated behind FF_ECONOMIC_CALENDAR)

---
*Phase: 16-report-enrichment*
*Completed: 2026-02-09*
