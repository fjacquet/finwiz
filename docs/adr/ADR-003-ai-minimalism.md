# ADR-003: AI Minimalism -- Python for Deterministic, AI for Qualitative

- **Status:** Accepted
- **Date:** 2025-01-20
- **Deciders:** FinWiz Core Team

## Context

The initial architecture used AI crews for all analysis stages including data collection,
numerical scoring, and synthesis. This caused severe problems:

- 200K-335K token overflow per ticker from accumulated crew context.
- Cost of $0.50+ per individual analysis (unsustainable for 66+ holdings).
- AI hallucination in numerical calculations produced unreliable scores.
- 5-10 minute execution time per ticker due to sequential LLM calls.

## Decision

Enforce strict separation between deterministic Python work and AI qualitative reasoning.

- **Python handles 100%** of deterministic work: data collection via tool factories,
  composite scoring via `DeepAnalysisScorer` (40% fundamental, 30% technical, 30% risk),
  and final synthesis.
- **AI crews provide qualitative insights only**: SEC filing context, fundamental narrative,
  technical strategy interpretation, risk assessment narrative, and investment thesis.
- **When Python and AI disagree** on recommendations, Python wins.
- Pipeline order: `collect_raw_data()` -> `calculate_quantitative()` ->
  `generate_qualitative()` -> `synthesize()`.

## Consequences

### Positive

- $0 cost for all deterministic work (scoring, data collection, synthesis).
- 10-30 seconds per ticker vs 5-10 minutes previously.
- No hallucination in numerical scores -- Python calculations are exact.
- Fully testable with standard pytest (no LLM mocking needed for scoring).

### Negative

- AI insights are limited to qualitative analysis; cannot contribute to scoring.
- Two codepaths to maintain (Python pipeline and AI crew configurations).

### Risks

- Python scoring may miss nuanced patterns that AI could catch in edge cases.

## References

- `src/finwiz/analysis/deep_analysis_pipeline.py`
- `src/finwiz/scoring/deep_analysis_scorer.py`
