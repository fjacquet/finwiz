---
phase: 14-sentiment-scoring
verified: 2026-02-09T08:15:00Z
status: passed
score: 5/5 must-haves verified
must_haves:
  truths:
    - "Each holding shows a sentiment score (positive/negative/neutral) computed from aggregated news headlines with source-reliability weighting"
    - "Sentiment confidence reflects article count (40%), source diversity (30%), and recency (30%) -- holdings with few or stale articles show low confidence"
    - "Holdings with no news coverage show sentiment as 'unavailable' (None), not neutral (0.0)"
    - "Composite score includes sentiment as an additive adjustment that defaults to zero impact (weight=0.0, feature-flagged off)"
    - "Enabling sentiment scoring with a non-zero weight does not change the existing 40/30/30 fundamental/technical/risk weight distribution"
  artifacts:
    - path: "src/finwiz/scoring/sentiment_scorer.py"
      provides: "SentimentScorer class with calculate_sentiment_score() method"
    - path: "src/finwiz/schemas/sentiment.py"
      provides: "SentimentScore Pydantic model for Phase 14 output"
    - path: "src/finwiz/scoring/thresholds.py"
      provides: "Sentiment-specific threshold fields (half_life, confidence, freshness)"
    - path: "src/finwiz/data/news_utils.py"
      provides: "temporal_decay_weight() and calculate_sentiment_confidence() functions"
    - path: "src/finwiz/scoring/deep_analysis_scorer.py"
      provides: "_calculate_sentiment_overlay() and additive adjustment in _compute_weighted_score()"
    - path: "src/finwiz/flow_state_models.py"
      provides: "Optional sentiment_score and sentiment_confidence fields on DeepAnalysisResult"
    - path: "src/finwiz/scoring/score_result_builder.py"
      provides: "Sentiment data propagation into DeepAnalysisResult"
  key_links:
    - from: "sentiment_scorer.py"
      to: "news_utils.py"
      via: "imports temporal_decay_weight, calculate_sentiment_confidence"
    - from: "sentiment_scorer.py"
      to: "schemas/sentiment.py"
      via: "imports NewsSentimentResult, SentimentScore"
    - from: "sentiment_scorer.py"
      to: "thresholds.py"
      via: "imports ScoringThresholds, get_thresholds"
    - from: "deep_analysis_scorer.py"
      to: "sentiment_scorer.py"
      via: "imports SentimentScorer, instantiates in __init__"
    - from: "deep_analysis_scorer.py"
      to: "config/features/flags.py"
      via: "imports is_feature_enabled for gate 1"
    - from: "score_result_builder.py"
      to: "flow_state_models.py"
      via: "passes sentiment_score/sentiment_confidence to DeepAnalysisResult"
---

# Phase 14: Sentiment Scoring Verification Report

**Phase Goal:** Each holding receives a sentiment score derived from news headlines, integrated into the composite score as an additive overlay
**Verified:** 2026-02-09T08:15:00Z
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Each holding shows a sentiment score (positive/negative/neutral) computed from aggregated news headlines with source-reliability weighting | VERIFIED | `SentimentScorer.calculate_sentiment_score()` (183 lines) computes temporal-decay-weighted scores with `article.source_reliability * decay` combined weight per article (line 139). Tests `TestSentimentScoring` and `TestSourceReliabilityWeighting` (6 tests) confirm positive, negative, mixed, and reliability-weighted scoring behavior. |
| 2 | Sentiment confidence reflects article count (40%), source diversity (30%), and recency (30%) -- holdings with few or stale articles show low confidence | VERIFIED | `calculate_sentiment_confidence()` in `news_utils.py` (lines 131-161) implements the exact 40/30/30 formula: `count_factor * 0.4 + diversity_factor * 0.3 + freshness_factor * 0.3`. Tests `TestConfidenceMetric` (3 tests) and `TestCalculateSentimentConfidence` (4 tests) confirm: many articles + many sources + fresh = 1.0, zero articles = 0.6, stale data = 0.7, single source = ~0.8. |
| 3 | Holdings with no news coverage show sentiment as "unavailable" (None), not neutral (0.0) | VERIFIED | `SentimentScorer.calculate_sentiment_score()` returns `(None, details)` in four cases: no key (line 57), None value (line 57), zero articles (line 81), invalid type (line 69). Comment at line 76 explicitly states `SENT-05: None, not 0.0`. Tests `TestNoNewsHandling` (4 tests) confirm all four cases return `score is None`. `SentimentScore.score` field has `None` as default (schema line 62). |
| 4 | Composite score includes sentiment as an additive adjustment that defaults to zero impact (weight=0.0, feature-flagged off) | VERIFIED | `_calculate_sentiment_overlay()` (lines 290-346) implements 4-gate safety: (1) `is_feature_enabled("sentiment_scoring")` returns False by default (`FF_SENTIMENT_SCORING=False` in definitions.py line 299), (2) `weight_sentiment_overlay = 0.0` (thresholds.py line 243). Both gates return `(0.0, details)` immediately. Test `test_overlay_zero_weight_no_impact` proves identical scores with and without news data when weight=0.0. Test `test_overlay_feature_flag_off_no_impact` confirms flag-off behavior. |
| 5 | Enabling sentiment scoring with a non-zero weight does not change the existing 40/30/30 fundamental/technical/risk weight distribution | VERIFIED | `_compute_weighted_score()` (lines 236-288) first computes `composite_score = weight_fundamental * fundamental + weight_technical * technical + weight_risk * risk` (line 260), then adds sentiment adjustment AFTER (line 266: `composite_score + sentiment_adjustment`). The 40/30/30 weights are never modified. Test `test_weights_40_30_30_unchanged_with_overlay` (line 658) confirms weights remain 40/30/30 with overlay enabled. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/finwiz/scoring/sentiment_scorer.py` | SentimentScorer class | VERIFIED | 183 lines, 3 public methods (calculate_sentiment_score, build_sentiment_score, _compute_decay_weighted_sentiment), proper imports and exports, no stubs, imported by deep_analysis_scorer.py |
| `src/finwiz/schemas/sentiment.py` | SentimentScore Pydantic model | VERIFIED | 73 lines, SentimentScore class (lines 56-73) with score/confidence/article_count/source_count/temporal_decay_applied/details fields, ConfigDict(extra="forbid"), imported by sentiment_scorer.py |
| `src/finwiz/scoring/thresholds.py` | Sentiment threshold fields | VERIFIED | 269 lines, 5 sentiment fields (lines 249-253): sentiment_half_life_hours=48.0, sentiment_min_confidence=0.0, sentiment_max_freshness_hours=168.0, sentiment_min_articles_for_high_confidence=10, sentiment_min_sources_for_max_diversity=3. weight_sentiment_overlay=0.0 (line 243) |
| `src/finwiz/data/news_utils.py` | temporal_decay_weight() and calculate_sentiment_confidence() | VERIFIED | 161 lines, temporal_decay_weight (lines 109-128) with exponential decay math, calculate_sentiment_confidence (lines 131-161) with 40/30/30 formula. Both used by SentimentScorer |
| `src/finwiz/scoring/deep_analysis_scorer.py` | _calculate_sentiment_overlay() and _compute_weighted_score() | VERIFIED | 431 lines, SentimentScorer instantiated at line 67, _calculate_sentiment_overlay() (lines 290-346) with 4-gate safety, _compute_weighted_score() (lines 236-288) applies additive overlay after composite calculation |
| `src/finwiz/flow_state_models.py` | sentiment_score, sentiment_confidence fields on DeepAnalysisResult | VERIFIED | Lines 53-55: `sentiment_score: float | None = Field(None, ge=-1.0, le=1.0)` and `sentiment_confidence: float | None = Field(None, ge=0.0, le=1.0)` with proper descriptions and None defaults |
| `src/finwiz/scoring/score_result_builder.py` | Sentiment data propagation | VERIFIED | Lines 108-109: `sentiment_score=scores.get("sentiment_score"), sentiment_confidence=scores.get("sentiment_confidence")` passed when constructing DeepAnalysisResult |
| `tests/unit/scoring/test_sentiment_scorer.py` | 18 scorer tests | VERIFIED | 214 lines, 18 tests across 6 test classes (TestNoNewsHandling: 4, TestSentimentScoring: 5, TestTemporalDecay: 3, TestConfidenceMetric: 3, TestSourceReliabilityWeighting: 1, TestBuildSentimentScore: 2). All 18 pass. |
| `tests/unit/scoring/test_deep_analysis_scorer.py` | TestSentimentOverlay (6 tests) | VERIFIED | Lines 491-694, 6 tests: zero_weight_no_impact, feature_flag_off_no_impact, positive_raises_score, negative_lowers_score, clamped_to_unit_range, weights_40_30_30_unchanged. All 6 pass. |
| `tests/unit/data/test_news_utils.py` | Temporal decay and confidence tests | VERIFIED | 219 lines, 8 new Phase 14 tests in TestTemporalDecayWeight (4 tests) and TestCalculateSentimentConfidence (4 tests). All pass. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| sentiment_scorer.py | news_utils.py | `from finwiz.data.news_utils import temporal_decay_weight, calculate_sentiment_confidence` | WIRED | Import at line 12-15, both functions called in calculate_sentiment_score (lines 88-96, 138) |
| sentiment_scorer.py | schemas/sentiment.py | `from finwiz.schemas.sentiment import NewsSentimentResult, SentimentScore` | WIRED | Import at line 16, NewsSentimentResult parsed at line 62, SentimentScore returned at lines 174-183 |
| sentiment_scorer.py | thresholds.py | `from finwiz.scoring.thresholds import ScoringThresholds, get_thresholds` | WIRED | Import at line 17, thresholds used for half_life (line 128), confidence params (lines 93-95) |
| deep_analysis_scorer.py | sentiment_scorer.py | `from finwiz.scoring.sentiment_scorer import SentimentScorer` | WIRED | Import at line 26, instantiated at line 67, called at line 321 |
| deep_analysis_scorer.py | config/features/flags.py | `is_feature_enabled("sentiment_scoring")` | WIRED | Called at line 310, feature flag "sentiment_scoring" defined in definitions.py line 297 with default=False |
| score_result_builder.py | flow_state_models.py | sentiment_score and sentiment_confidence passed to DeepAnalysisResult | WIRED | Lines 108-109 pass scores.get("sentiment_score") and scores.get("sentiment_confidence") |

### Requirements Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| SENT-01: Headline sentiment scoring | SATISFIED | SentimentScorer uses per-article sentiment_score from NewsSentimentResult (article.sentiment_score at line 140) |
| SENT-02: Aggregate sentiment per holding with source-reliability weighting | SATISFIED | _compute_decay_weighted_sentiment combines source_reliability * temporal_decay per article (line 139) |
| SENT-03: Sentiment confidence metric (count, diversity, recency) | SATISFIED | calculate_sentiment_confidence implements 40/30/30 formula (news_utils.py lines 157-161) |
| SENT-04: Temporal decay weighting (exponential) | SATISFIED | temporal_decay_weight uses exp(-ln(2)/half_life * age_hours) (news_utils.py lines 127-128) |
| SENT-05: No-news = None, not 0.0 | SATISFIED | Four explicit None returns in sentiment_scorer.py (lines 57, 69, 74, 81) with code comment citing SENT-05 |
| SCORE-01: Sentiment as additive overlay | SATISFIED | _compute_weighted_score applies `composite_score + sentiment_adjustment` at line 266, after 40/30/30 calculation |
| SCORE-02: Default weight=0.0, feature-flagged off | SATISFIED | weight_sentiment_overlay=0.0 (thresholds.py line 243), FF_SENTIMENT_SCORING=False (definitions.py line 299) |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | - | - | - | No TODO/FIXME/placeholder/stub patterns detected in any Phase 14 files |

### Human Verification Required

### 1. End-to-End Sentiment Scoring with Real Data

**Test:** Run `crewai flow kickoff` with `FF_SENTIMENT_SCORING=true` and `weight_sentiment_overlay=0.05` on a portfolio with mixed news coverage (some holdings with news, some without)
**Expected:** Holdings with news show non-None sentiment_score and sentiment_confidence in DeepAnalysisResult. Holdings without news show None for both fields. Composite scores for holdings with news differ slightly from baseline.
**Why human:** Requires live API data flow through the full pipeline with real Finnhub news data.

### 2. Temporal Decay Behavior with Real Article Timestamps

**Test:** Examine scoring output for a holding with articles spanning several days to verify recent articles dominate the sentiment
**Expected:** A holding with a recent bearish article and older bullish articles should show net-bearish sentiment
**Why human:** Requires real article timestamps and visual inspection of scoring breakdown details

### 3. Feature Flag Toggle Behavior

**Test:** Run the same portfolio analysis with FF_SENTIMENT_SCORING=false (default) and FF_SENTIMENT_SCORING=true, compare outputs
**Expected:** Scores are identical when flag is off. When flag is on with weight > 0, scores show small additive adjustments.
**Why human:** Requires running the full flow twice and comparing structured output

### Gaps Summary

No gaps found. All 5 observable truths are verified against the actual codebase. All 7 requirements (SENT-01 through SENT-05, SCORE-01, SCORE-02) are satisfied. All key artifacts exist, are substantive (no stubs), and are fully wired. All 32 relevant tests (18 scorer + 8 utility + 6 overlay) pass.

---

_Verified: 2026-02-09T08:15:00Z_
_Verifier: Claude (gsd-verifier)_
