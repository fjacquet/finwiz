# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-09)

**Core value:** Hybrid financial analysis enriched with news sentiment and macroeconomic context for smarter scoring
**Current focus:** Phase 15 in progress - MacroScorer built, composite wiring next

## Current Position

Phase: 15 of 16 (Macro Context)
Plan: 1 of 3 in current phase
Status: In progress
Last activity: 2026-02-09 -- Completed 15-01-PLAN.md (MacroScorer component scorer)

Progress: [=============================░] 89% (39/44 plans across all milestones)

## Milestones Shipped

- v1 Hardening & Discovery (Phases 1-5, 13 plans) -- 2026-02-08
- v2 Security & Structural Quality (Phases 6-8, 6 plans) -- 2026-02-08
- v3 Performance & Risk Analysis (Phases 9-12, 7 plans) -- 2026-02-08

## Performance Metrics

**Velocity:**

- Total plans completed: 39 (v1: 13, v2: 6, v3: 7, v4-phase13: 10, v4-phase14: 2, v4-phase15: 1)
- Total phases completed: 14 (Phase 15 in progress)

**Codebase:**

- ~109,000 LOC Python
- 4,625 tests passing (31 new in 15-01)
- 66.89% coverage (above 65% threshold)
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

### Pending Todos

None.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-02-09
Stopped at: Phase 15 Plan 01 complete (MacroScorer), ready for Plan 15-02 (composite wiring)
Resume file: .planning/phases/15-macro-context/15-01-SUMMARY.md

*Updated after Plan 15-01 MacroScorer completion*
