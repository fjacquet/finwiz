# Phase 14: Sentiment Scoring - Research

**Researched:** 2026-02-09
**Domain:** Financial sentiment scoring, composite score integration, temporal decay weighting
**Confidence:** HIGH

## Summary

Phase 14 transforms the raw news sentiment data collected by Phase 13 into a per-holding sentiment score and integrates it into the existing composite scoring engine as an additive overlay. The codebase already has all the building blocks: `NewsSentimentResult` with per-article sentiment scores and source reliability weights, `ScoringThresholds.weight_sentiment_overlay` defaulting to 0.0, and a `sentiment_scoring` feature flag defaulting to off. The primary engineering work is (1) a new `SentimentScorer` class that computes a normalized sentiment score with temporal decay and confidence metrics, (2) wiring it into `DeepAnalysisScorer._compute_weighted_score()` as an additive adjustment, and (3) handling the "no news" case as `None` rather than 0.0.

The key architectural decision -- additive overlay rather than weight redistribution -- is already locked. This means the existing 40/30/30 fundamental/technical/risk weights remain untouched. The sentiment adjustment is added *after* the weighted composite is calculated: `final = composite + weight_sentiment_overlay * sentiment_score`. When the feature flag is off or weight is 0.0, the result is identical to today's scoring.

**Primary recommendation:** Create a `SentimentScorer` class in `src/finwiz/scoring/sentiment_scorer.py` following the existing component scorer pattern (like `FundamentalScorer`, `TechnicalScorer`, `RiskScorer`), wire it into the `DeepAnalysisScorer` orchestrator with additive overlay math, and gate everything behind the existing `sentiment_scoring` feature flag.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| vaderSentiment | >=3.3.2 | Local fallback sentiment scoring | Already in pyproject.toml; used by FinnhubNewsAdapter |
| finnhub-python | >=2.4.20 | Pre-computed sentiment from Finnhub API | Already in pyproject.toml; primary sentiment source |
| pydantic | >=2.0 | Schema validation for sentiment results | Project standard for all schemas |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| math (stdlib) | - | `math.exp()` for exponential decay | Temporal decay weighting calculation |
| statistics (stdlib) | - | Mean/stdev for confidence | Sentiment confidence metric |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| VADER fallback | FinBERT | FinBERT is more accurate for financial text but requires GPU, torch dependency, and ~2s per inference vs VADER's <1ms. Prior decision locks VADER as fallback. |
| Exponential decay | Linear decay | Linear is simpler but does not properly penalize stale news; exponential with half-life is standard in quantitative finance |
| Additive overlay | Weight redistribution | Weight redistribution would change existing 40/30/30 behavior; additive preserves backward compatibility. Prior decision locks additive overlay. |

**Installation:** No new dependencies needed. All libraries already in `pyproject.toml`.

## Architecture Patterns

### Recommended Project Structure

```
src/finwiz/
├── scoring/
│   ├── sentiment_scorer.py          # NEW: SentimentScorer class
│   ├── deep_analysis_scorer.py      # MODIFY: Wire sentiment overlay in _compute_weighted_score()
│   └── thresholds.py                # EXISTING: weight_sentiment_overlay, add decay/confidence thresholds
│
├── schemas/
│   └── sentiment.py                 # MODIFY: Add SentimentScore model with confidence
│
├── data/
│   └── news_utils.py                # MODIFY: Add temporal decay weighted sentiment function
│
├── config/features/
│   └── definitions.py               # EXISTING: sentiment_scoring flag already defined
│
└── analysis/
    └── deep_analysis_pipeline.py    # MODIFY: Pass news_sentiment to scorer
```

### Pattern 1: Component Scorer Pattern (existing codebase pattern)

**What:** Each scoring domain (fundamental, technical, risk) has its own scorer class that receives thresholds and data, returns (score, details) tuple.
**When to use:** Adding any new scoring component.
**Example from codebase:**
```python
# Source: src/finwiz/scoring/fundamental_scorer.py (existing pattern)
class FundamentalScorer:
    def __init__(self, thresholds: ScoringThresholds | None = None):
        self.thresholds = thresholds or get_thresholds()

    def calculate_fundamental_score(self, asset_class: str, data: dict) -> tuple[float, dict]:
        # Returns (score_0_to_1, details_dict)
        ...

# SentimentScorer should follow exact same pattern:
class SentimentScorer:
    def __init__(self, thresholds: ScoringThresholds | None = None):
        self.thresholds = thresholds or get_thresholds()

    def calculate_sentiment_score(self, data: dict) -> tuple[float | None, dict]:
        # Returns (score_or_None, details_dict)
        # None = no news coverage (SENT-05)
        ...
```

### Pattern 2: Additive Overlay (new pattern for Phase 14)

**What:** After computing the weighted composite (40F + 30T + 30R), apply an additive adjustment that defaults to zero impact.
**When to use:** Integrating supplementary scoring factors (sentiment, macro) that should not redistribute existing weights.
**Formula:**
```python
# Existing composite calculation (unchanged):
composite = weight_F * fundamental + weight_T * technical + weight_R * risk

# Additive overlay (new):
sentiment_adjustment = 0.0  # Default: no impact
if sentiment_score is not None and thresholds.weight_sentiment_overlay > 0:
    # sentiment_score is in [-1.0, +1.0], scale to adjustment range
    # Clamp final result to [0.0, 1.0]
    sentiment_adjustment = thresholds.weight_sentiment_overlay * sentiment_score

final_score = max(0.0, min(1.0, composite + sentiment_adjustment))
```

### Pattern 3: Temporal Decay Weighting

**What:** Recent articles weighted more heavily than older ones using exponential decay.
**When to use:** Computing aggregate sentiment from articles of varying ages.
**Formula:**
```python
import math
from datetime import datetime, timezone

def temporal_decay_weight(published_at: datetime, half_life_hours: float = 48.0) -> float:
    """Exponential decay: weight halves every half_life_hours.

    Args:
        published_at: Article publication timestamp
        half_life_hours: Time for weight to decay to 50% (default 48h)

    Returns:
        Weight in (0.0, 1.0] -- 1.0 for brand-new, decaying toward 0
    """
    now = datetime.now(tz=timezone.utc)
    age_hours = max(0.0, (now - published_at).total_seconds() / 3600)
    decay_rate = math.log(2) / half_life_hours
    return math.exp(-decay_rate * age_hours)
```

### Pattern 4: Confidence Metric

**What:** Sentiment confidence reflects how trustworthy the aggregate sentiment score is.
**When to use:** Determining whether the sentiment score should influence decisions.
**Factors:**
```python
def calculate_sentiment_confidence(
    article_count: int,
    source_diversity: int,  # Number of unique sources
    data_freshness_hours: float,
    min_articles_for_high_confidence: int = 10,
    max_freshness_hours: float = 168.0,  # 1 week
) -> float:
    """
    Confidence in [0.0, 1.0] based on:
    - Article count coverage (more articles = higher confidence)
    - Source diversity (more unique sources = higher confidence)
    - Data freshness (staler data = lower confidence)
    """
    count_factor = min(1.0, article_count / min_articles_for_high_confidence)
    diversity_factor = min(1.0, source_diversity / 3.0)  # 3+ sources = max
    freshness_factor = max(0.0, 1.0 - (data_freshness_hours / max_freshness_hours))

    return count_factor * 0.4 + diversity_factor * 0.3 + freshness_factor * 0.3
```

### Anti-Patterns to Avoid

- **Neutral default for missing data:** Absence of news is NOT neutral sentiment. It must be `None` to distinguish "no data" from "neutral sentiment" (SENT-05). Never default to 0.0.
- **Weight redistribution:** Do NOT change the 40/30/30 weights. The sentiment overlay is additive on top.
- **Unbounded adjustment:** The additive overlay must be clamped so the final composite stays in [0.0, 1.0].
- **Ignoring confidence:** Low-confidence sentiment scores should have reduced or zero impact. Consider multiplying the adjustment by the confidence value.
- **Direct article-level scoring in the scorer:** The `SentimentScorer` receives already-collected `NewsSentimentResult` from the pipeline's `raw_data["news_sentiment"]`. It should NOT call APIs itself.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sentiment scoring from text | Custom NLP model | VADER (already integrated via FinnhubNewsAdapter) | VADER is standard for financial text, no training needed, < 1ms per article |
| Deduplication | Custom string matching | `news_utils.deduplicate_articles()` | Already implemented with Jaccard similarity in Phase 13 |
| Source reliability weights | Hardcoded per-call lookup | `news_utils.get_source_reliability()` | Already implemented with SOURCE_RELIABILITY table in Phase 13 |
| Weighted average | Manual sum/divide | `news_utils.calculate_weighted_sentiment()` | Already implemented in Phase 13, handles None scores |
| Feature flag checking | Custom env var reading | `is_feature_enabled("sentiment_scoring")` | Already defined in `definitions.py` with circuit breaker support |

**Key insight:** Phase 13 delivered all the data collection and basic aggregation. Phase 14 adds temporal decay, confidence metrics, and the scoring integration layer on top. Resist the urge to rebuild what already exists.

## Common Pitfalls

### Pitfall 1: Treating No-News as Neutral

**What goes wrong:** Holdings with zero articles get sentiment_score = 0.0 (neutral), making them appear to have been analyzed when they haven't.
**Why it happens:** Default float values are 0.0; developers instinctively initialize to zero.
**How to avoid:** Use `float | None` for sentiment score. Return `None` from `SentimentScorer` when `article_count == 0`. The additive overlay formula checks for `None` and applies zero adjustment.
**Warning signs:** Tests pass but holdings with no news show sentiment as "neutral" instead of "unavailable".

### Pitfall 2: Sentiment Score Changing Existing Grades When Flag Is Off

**What goes wrong:** Even with `weight_sentiment_overlay = 0.0`, the code path produces different results due to floating point or logic errors.
**Why it happens:** Adding new code to `_compute_weighted_score()` introduces subtle changes.
**How to avoid:** Write explicit regression tests: compute scores with and without sentiment data, verify identical results when weight = 0.0. Test that `sentiment_scoring` flag = off produces byte-identical output.
**Warning signs:** Existing test_deep_analysis_scorer tests fail after changes.

### Pitfall 3: Unbounded Composite Score

**What goes wrong:** Additive overlay pushes composite score above 1.0 or below 0.0.
**Why it happens:** `sentiment_score` ranges [-1, +1], and multiplied by a positive weight, can push composite beyond bounds.
**How to avoid:** Always clamp: `max(0.0, min(1.0, composite + adjustment))`. Add boundary tests with extreme sentiment values.
**Warning signs:** Grades or recommendations behave unexpectedly for holdings with strong sentiment.

### Pitfall 4: Temporal Decay Making All Sentiment Negligible

**What goes wrong:** With a short half-life, articles older than a few hours have near-zero weight, making the aggregate dominated by noise from 1-2 recent articles.
**Why it happens:** Overly aggressive decay constant.
**How to avoid:** Use 48-hour half-life as default (articles 2 days old have 50% weight, 4 days old have 25% weight, 1 week old have ~10%). Make half-life configurable via thresholds.
**Warning signs:** Sentiment confidence is always low despite having 10+ articles spanning a week.

### Pitfall 5: Modifying NewsSentimentResult Schema Breaking Phase 13

**What goes wrong:** Adding fields to `NewsSentimentResult` with `extra="forbid"` causes existing serialized data to fail validation.
**Why it happens:** Adding required fields to an existing model.
**How to avoid:** Create a NEW schema `SentimentScore` for Phase 14 output. Keep `NewsSentimentResult` as-is (it's the Phase 13 data input). The scorer consumes `NewsSentimentResult` and produces `SentimentScore`.
**Warning signs:** Existing tests for `NewsSentimentResult` or `FinnhubNewsAdapter` fail.

### Pitfall 6: Using unittest.mock Instead of pytest-mock

**What goes wrong:** Import blocked at runtime by `conftest_unittest_blocker.py`, tests crash.
**Why it happens:** Habit from other Python projects.
**How to avoid:** Always use `mocker.patch()` from pytest-mock. This is enforced by ruff and `make check-unittest-mock`.
**Warning signs:** `make check` fails with unittest.mock import error.

## Code Examples

Verified patterns from the existing codebase:

### Existing Composite Score Calculation (to be modified)

```python
# Source: src/finwiz/scoring/deep_analysis_scorer.py lines 233-266
def _compute_weighted_score(self, scores: dict[str, Any]) -> float:
    fundamental_score = scores["fundamental_score"]
    fundamental_details = scores.get("fundamental_details", {})
    is_quality_company = self.result_builder.is_quality_company(fundamental_score, fundamental_details)

    if is_quality_company:
        weight_fundamental = 0.50
        weight_technical = 0.25
        weight_risk = 0.25
    else:
        weight_fundamental = self.thresholds.weight_fundamental  # 0.40
        weight_technical = self.thresholds.weight_technical      # 0.30
        weight_risk = self.thresholds.weight_risk                # 0.30

    composite_score = (weight_fundamental * scores["fundamental_score"]
                     + weight_technical * scores["technical_score"]
                     + weight_risk * scores["risk_score"])

    # Phase 14: Additive sentiment overlay goes HERE
    # sentiment_adjustment = self._calculate_sentiment_overlay(scores)
    # composite_score = max(0.0, min(1.0, composite_score + sentiment_adjustment))

    return float(composite_score)
```

### Existing Feature Flag Check Pattern

```python
# Source: src/finwiz/data/sentiment_collector.py lines 27-41
def collect_sentiment(self, ticker: str) -> NewsSentimentResult | None:
    if not is_feature_enabled("finnhub_news"):
        return None
    try:
        from finwiz.data.adapters.finnhub_news_adapter import FinnhubNewsAdapter
        adapter = FinnhubNewsAdapter()
        return adapter.get_news_sentiment(ticker)
    except Exception as e:
        logger.warning(f"Sentiment collection failed for {ticker}: {e}")
        return None
```

### Existing Threshold Configuration Pattern

```python
# Source: src/finwiz/scoring/thresholds.py lines 239-244
# ADDITIVE OVERLAY WEIGHTS (v4 Data Intelligence)
# These are ADDITIVE on top of the 40/30/30 composite -- not redistributed.
# Default 0.0 = disabled. Activated by feature flags in Phase 14+.
weight_sentiment_overlay: float = 0.0  # Additive sentiment adjustment
weight_macro_overlay: float = 0.0      # Additive macro context adjustment
```

### How Data Flows from Pipeline to Scorer

```python
# Source: src/finwiz/analysis/deep_analysis_pipeline.py lines 90-104
# Phase 13 stores sentiment in raw_data:
raw_data["news_sentiment"] = sentiment.model_dump(mode="json")

# Phase 14 needs to:
# 1. Pass raw_data to scorer (already happening)
# 2. Scorer reads raw_data["news_sentiment"] inside _compute_weighted_score
# 3. SentimentScorer.calculate_sentiment_score(raw_data) returns (score|None, details)
```

### Testing Pattern (pytest-mock, not unittest.mock)

```python
# Source: tests/unit/data/test_news_utils.py (existing test pattern)
def _make_article(title="Test headline", source="finnhub", **kwargs):
    defaults = {
        "title": title,
        "url": "https://example.com",
        "source": source,
        "published_at": datetime(2026, 1, 15),
        "ticker": "AAPL",
    }
    defaults.update(kwargs)
    return NewsArticle(**defaults)

# For scorer tests, use mocker fixture:
def test_sentiment_overlay_zero_weight(scorer, sample_stock_data):
    """Sentiment overlay has zero impact when weight is 0.0."""
    result_without = scorer.calculate_composite_score("AAPL", "stock", sample_stock_data)
    sample_stock_data["news_sentiment"] = {...}  # Add sentiment data
    result_with = scorer.calculate_composite_score("AAPL", "stock", sample_stock_data)
    assert result_without.composite_score == result_with.composite_score
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FinBERT for all sentiment | Finnhub pre-computed + VADER fallback | Phase 13 decision (2026) | No GPU dependency, sub-millisecond inference, $0 cost |
| Weight redistribution for new factors | Additive overlay pattern | Phase 13 design (2026) | Preserves existing 40/30/30 weights, backward compatible |
| Binary sentiment (positive/negative) | Continuous score [-1, +1] with confidence | Phase 13 schema | More nuanced scoring, handles uncertainty |

**Deprecated/outdated:**
- **FinBERT for this project:** Explicitly decided against in Phase 13 research. VADER is the local fallback, Finnhub provides pre-computed sentiment.
- **Weight redistribution:** The 40/30/30 weights must remain unchanged. Sentiment is additive.

## Integration Points Summary

### What Phase 13 Delivered (inputs to Phase 14)

| Component | Location | What It Provides |
|-----------|----------|------------------|
| `NewsSentimentResult` | `schemas/sentiment.py` | `weighted_sentiment`, `article_count`, `source_breakdown`, `data_freshness_hours` |
| `FinnhubNewsAdapter` | `data/adapters/finnhub_news_adapter.py` | Waterfall news fetching with VADER fallback |
| `news_utils` | `data/news_utils.py` | `calculate_weighted_sentiment()`, `get_source_reliability()`, deduplication |
| `SentimentMacroCollector` | `data/sentiment_collector.py` | `collect_sentiment(ticker)` returns `NewsSentimentResult | None` |
| Feature flags | `config/features/definitions.py` | `finnhub_news`, `sentiment_scoring` flags |
| Thresholds | `scoring/thresholds.py` | `weight_sentiment_overlay = 0.0` |
| Pipeline wiring | `analysis/deep_analysis_pipeline.py` | `raw_data["news_sentiment"]` populated during `collect_raw_data()` |

### What Phase 14 Must Create (new)

| Component | Location | What It Produces |
|-----------|----------|------------------|
| `SentimentScorer` | `scoring/sentiment_scorer.py` | `calculate_sentiment_score(data) -> (float\|None, dict)` |
| `SentimentScore` schema | `schemas/sentiment.py` | Validated output: score, confidence, temporal_weight_applied, article_count |
| Temporal decay function | `data/news_utils.py` | `calculate_temporal_decay_sentiment(articles, half_life_hours)` |
| Confidence calculator | `scoring/sentiment_scorer.py` | Based on article count, source diversity, freshness |
| Overlay wiring | `scoring/deep_analysis_scorer.py` | Additive adjustment in `_compute_weighted_score()` |
| Threshold additions | `scoring/thresholds.py` | `sentiment_half_life_hours`, `sentiment_min_confidence`, etc. |
| DeepAnalysisResult fields | `flow_state_models.py` | Optional `sentiment_score`, `sentiment_confidence` fields |

### What Phase 14 Must NOT Change

| Component | Location | Constraint |
|-----------|----------|------------|
| `NewsSentimentResult` schema | `schemas/sentiment.py` | Do not add required fields (breaks Phase 13) |
| 40/30/30 weight distribution | `scoring/thresholds.py` | Must remain unchanged |
| Existing test suite | `tests/unit/scoring/` | All 4,640 tests must continue passing |
| `FinnhubNewsAdapter` | `data/adapters/` | Data collection is Phase 13's job |

## Open Questions

1. **Sentiment score range for overlay**
   - What we know: Raw sentiment is [-1.0, +1.0]. The overlay weight is currently 0.0.
   - What's unclear: When enabled, what's a reasonable weight? 0.05 (5% adjustment)? 0.10 (10%)?
   - Recommendation: Default to 0.0 (disabled). Document that typical production values are 0.03-0.10 in threshold docstrings. Let users configure via `ScoringThresholds(weight_sentiment_overlay=0.05)`.

2. **Confidence threshold for application**
   - What we know: Low-confidence sentiment (few articles, stale data) is unreliable.
   - What's unclear: Should low-confidence sentiment be applied at reduced weight, or not at all?
   - Recommendation: Multiply the sentiment adjustment by the confidence value: `adjustment = weight * sentiment_score * confidence`. This naturally dampens unreliable signals without a hard cutoff.

3. **DeepAnalysisResult schema changes**
   - What we know: `DeepAnalysisResult` uses `extra="forbid"`, so new fields must be optional.
   - What's unclear: Whether to add `sentiment_score` and `sentiment_confidence` to `DeepAnalysisResult` or only to the crew export.
   - Recommendation: Add optional fields to `DeepAnalysisResult` (`sentiment_score: float | None = None`, `sentiment_confidence: float | None = None`). This makes the data available for reporting without breaking existing code.

4. **Half-life parameter value**
   - What we know: Financial news relevance decays; standard EWMA in finance uses varying spans.
   - What's unclear: Optimal half-life for headline sentiment specifically.
   - Recommendation: Default 48 hours (2 days). Articles from 2 days ago have 50% weight, 4 days = 25%, 1 week = ~10%. Make configurable via thresholds.

## Sources

### Primary (HIGH confidence)

- **Codebase inspection** - Direct reading of all relevant source files:
  - `src/finwiz/scoring/deep_analysis_scorer.py` - Current composite scoring architecture
  - `src/finwiz/scoring/thresholds.py` - Existing overlay weight fields
  - `src/finwiz/schemas/sentiment.py` - Phase 13 sentiment schemas
  - `src/finwiz/data/news_utils.py` - Phase 13 utility functions
  - `src/finwiz/data/sentiment_collector.py` - Phase 13 data collection
  - `src/finwiz/data/adapters/finnhub_news_adapter.py` - News waterfall adapter
  - `src/finwiz/analysis/deep_analysis_pipeline.py` - Pipeline wiring
  - `src/finwiz/config/features/definitions.py` - Feature flag definitions
  - `src/finwiz/flow_state_models.py` - DeepAnalysisResult schema

### Secondary (MEDIUM confidence)

- [VADER Sentiment GitHub](https://github.com/cjhutto/vaderSentiment) - VADER API reference (compound score in [-1, +1])
- [GeeksforGeeks VADER guide](https://www.geeksforgeeks.org/python/python-sentiment-analysis-using-vader/) - VADER `polarity_scores()` returns `{neg, neu, pos, compound}`
- [pythoninvest.com](https://pythoninvest.com/long-read/sentiment-analysis-of-financial-news) - Exponential decay weighting for financial news sentiment
- [BIS Working Paper](https://www.bis.org/publ/work1294.pdf) - Macroeconomic sentiment decomposition with LLMs

### Tertiary (LOW confidence)

- [Arxiv: Adaptive Financial Sentiment for NIFTY 50](https://arxiv.org/pdf/2512.20082) - RAG-based adaptive sentiment frameworks (informational, not directly applicable)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in pyproject.toml, no new dependencies
- Architecture: HIGH - Patterns directly observed in codebase (component scorer, threshold config, feature flags)
- Pitfalls: HIGH - Derived from codebase constraints (extra="forbid", unittest.mock ban, 40/30/30 invariant)
- Temporal decay formula: MEDIUM - Standard exponential decay from quantitative finance, but optimal half-life parameter is empirical

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (stable domain, codebase-driven)
