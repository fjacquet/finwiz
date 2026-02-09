# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-09)

**Core value:** Hybrid financial analysis enriched with news sentiment and macroeconomic context for smarter scoring
**Current focus:** Phase 16 (Report Enrichment) -- Plan 02 complete, Plan 03 remaining

## Current Position

Phase: 16 of 16 (Report Enrichment)
Plan: 2 of 3 in current phase -- COMPLETE
Status: In progress
Last activity: 2026-02-09 -- Completed 16-02-PLAN.md (sentiment/macro/calendar report sections), 4795 tests passing, 67.41% coverage

Progress: [================================░] 98% (43/44 plans across all milestones)

## Milestones Shipped

- v1 Hardening & Discovery (Phases 1-5, 13 plans) -- 2026-02-08
- v2 Security & Structural Quality (Phases 6-8, 6 plans) -- 2026-02-08
- v3 Performance & Risk Analysis (Phases 9-12, 7 plans) -- 2026-02-08
- v4 Data Intelligence & Smart Scoring (Phases 13-16, 18 plans) -- 2026-02-09

## Performance Metrics

**Velocity:**

- Total plans completed: 43 (v1: 13, v2: 6, v3: 7, v4-phase13: 10, v4-phase14: 2, v4-phase15: 2 + 1 config, v4-phase16: 2)
- Total phases completed: 15 (Phase 16 in progress)

**Codebase:**

- ~109,000 LOC Python
- 4,795 tests passing (34 new in Plan 16-02)
- 67.41% coverage (above 65% threshold)
- All pre-commit hooks pass (14/14)

## Accumulated Context

### Decisions

All decisions logged in PROJECT.md Key Decisions table.

Recent decisions affecting current work:
- Additive overlay pattern for sentiment/macro scoring (NOT weight redistribution)
- Feature-flag all new scoring factors with default=off
- Finnhub pre-computed sentiment first, VADER as local fallback (not FinBERT)
- Macro data collected ONCE per run at session level, not per holding
- SentimentScorer follows component scorer pattern (FundamentalScorer, TechnicalScorer, RiskScorer)
- No-news returns None (not 0.0) to distinguish missing data from neutral sentiment
- Temporal decay uses exponential half-life model (default 48h)
- Confidence: article count 40%, source diversity 30%, freshness 30%
- Sentiment overlay uses 4-gate safety: feature flag -> weight -> data -> confidence threshold
- DeepAnalysisResult uses optional fields (None default) for sentiment backward compatibility
- MacroScorer follows exact SentimentScorer component pattern: (score_or_None, details_dict)
- Yield curve classified into 4 regimes at boundaries: 0.0, 0.5, 2.0
- No feature flag logic in MacroScorer -- gating deferred to DeepAnalysisScorer (Plan 15-02)
- Macro overlay uses identical 4-gate safety as sentiment (flag->weight->data->confidence)
- Both overlays stack: composite = base + sentiment_adj + macro_adj, clamped per-overlay
- Quality company adaptive weights (50/25/25) coexist with macro overlay without interference
- assess_market_regime() reads real VIX from macro_snapshot with fallback to 20.0
- _estimate_interest_rate() accepts real Fed rate from FRED with fallback to trend-based
- [16-01] sentiment_summary added as optional field on EnrichedAnalysis (auto-persisted in enriched JSON)
- [16-01] Confidence = min(1.0, article_count/10) as simple heuristic for sentiment summary
- [16-01] macro_snapshot set once per session in DeepAnalysisOrchestrator (not pipeline)
- [16-01] Economic calendar filters US events + high-impact keywords (FOMC, CPI, GDP, employment)
- [16-02] Macro dashboard placed after executive summary (portfolio-level context first)
- [16-02] Sentiment section placed after holdings analysis (per-holding detail context)
- [16-02] Economic calendar placed before footer (forward-looking events)
- [16-02] Traffic-light thresholds: VIX<=20 green, yield_curve>0.50 green, GDP>2.0 green, CPI<3.0 green
- [16-02] Fear & Greed gauge as pure CSS horizontal gradient bar (no JS)

### Pending Todos

None.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-02-09
Stopped at: Plan 16-02 complete, ready for Plan 16-03 (per-holding enriched report templates)
Resume file: .planning/phases/16-report-enrichment/16-02-SUMMARY.md

*Updated after Plan 16-02 completion (34 new tests, 4795 total passing)*
