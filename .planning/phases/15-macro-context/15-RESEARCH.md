# Phase 15: Macro Context - Research

**Researched:** 2026-02-09
**Domain:** Macroeconomic data integration, dynamic risk scoring, yield curve analysis
**Confidence:** HIGH

## Summary

Phase 15 replaces hardcoded macroeconomic values scattered across the codebase with real data from the FRED adapter (built in Phase 13) and wires that data into the scoring pipeline as a macro overlay (following the additive pattern established in Phase 14). The phase has three pillars: (1) injecting real macro data into existing functions that currently use hardcoded defaults, (2) building a MacroScorer component that classifies yield curve regimes and detects market conditions, and (3) applying dynamic risk weight adjustments and per-asset-class sensitivity coefficients via the additive overlay mechanism.

The codebase is well-prepared for this phase. The FRED adapter (`data/adapters/fred_adapter.py`) already fetches all needed series (VIX, Fed rate, CPI, GDP, 10Y yield, 2Y yield) and computes yield curve spread. The `MacroSnapshot` schema (`schemas/macro.py`) already has `get_market_regime()` and `is_recession_signal()` methods. The `SentimentMacroCollector` already collects and caches macro data per session. The `weight_macro_overlay` field already exists in `ScoringThresholds` (defaulting to 0.0). The `macro_scoring` feature flag already exists (defaulting to off). What remains is wiring: replacing hardcoded values with real data, building the `MacroScorer` component, computing yield curve regime classification, and implementing per-asset-class sensitivity.

**Primary recommendation:** Follow the Phase 14 SentimentScorer pattern exactly. Create a `MacroScorer` class in `scoring/macro_scorer.py` that receives `data["macro_snapshot"]`, classifies yield curve regime, computes a macro adjustment score, and returns `(adjustment, details)`. Wire it into `_compute_weighted_score()` as a second additive overlay with the same 4-gate safety pattern (feature flag, weight check, score computation, confidence threshold).

## Standard Stack

### Core (Already Installed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fredapi | 0.5.2 | FRED API access | Already installed, used by FREDAdapter |
| pydantic | 2.12.5 | Schema validation | Project standard for all models |
| pytest | 9.0.2 | Testing | Project standard |
| pytest-mock | 3.15.1 | Mocking (mocker.patch) | REQUIRED -- unittest.mock is BANNED |

### Supporting (No New Dependencies)

This phase requires NO new package installations. All necessary infrastructure exists from Phase 13.

| Component | Location | Status |
|-----------|----------|--------|
| FREDAdapter | `data/adapters/fred_adapter.py` | Complete from Phase 13 |
| MacroSnapshot schema | `schemas/macro.py` | Complete from Phase 13 |
| SentimentMacroCollector | `data/sentiment_collector.py` | Complete from Phase 13 |
| ScoringThresholds.weight_macro_overlay | `scoring/thresholds.py` | Exists, defaults to 0.0 |
| FF_MACRO_SCORING feature flag | `config/features/definitions.py` | Exists, defaults to off |
| Pipeline integration | `analysis/deep_analysis_pipeline.py` | Already collects macro_snapshot |

## Architecture Patterns

### Recommended Project Structure (New/Modified Files)

```
src/finwiz/
├── scoring/
│   ├── macro_scorer.py              # NEW: MacroScorer component (like SentimentScorer)
│   └── deep_analysis_scorer.py      # MODIFY: Wire macro overlay into _compute_weighted_score()
│   └── thresholds.py                # MODIFY: Add macro-specific threshold fields
├── schemas/
│   └── macro.py                     # MODIFY: Add YieldCurveRegime enum, MacroScore schema
├── orchestrators/extraction/
│   └── market_context.py            # MODIFY: Replace hardcoded values with MacroSnapshot
├── tools/scoring/
│   └── scoring_criteria.py          # MODIFY: Replace hardcoded VIX=20.0 in assess_market_regime()
tests/unit/scoring/
│   └── test_macro_scorer.py         # NEW: Full test coverage for MacroScorer
│   └── test_deep_analysis_scorer_macro.py  # NEW: Integration tests for macro overlay
```

### Pattern 1: MacroScorer Component (Follows SentimentScorer Pattern)

**What:** A dedicated scorer class that receives raw macro data and returns (adjustment, details)
**When to use:** For all macro-to-scoring integration
**Example:**

```python
# Source: Modeled on finwiz/scoring/sentiment_scorer.py (Phase 14)
class MacroScorer:
    """Score macro context for composite scoring overlay.

    Follows component scorer pattern (FundamentalScorer, TechnicalScorer, RiskScorer, SentimentScorer).
    Receives raw data dict containing macro_snapshot, returns (score_or_None, details_dict).
    """

    def __init__(self, thresholds: ScoringThresholds | None = None) -> None:
        self.thresholds = thresholds or get_thresholds()

    def calculate_macro_score(self, data: dict[str, Any]) -> tuple[float | None, dict[str, Any]]:
        """Calculate macro adjustment score from session-level macro data.

        Returns:
            Tuple of (score_or_None, details_dict).
            score is in [-1.0, +1.0] or None if no data.
        """
        # Gate: extract macro_snapshot from data
        # Gate: validate fields present
        # Compute yield curve regime
        # Compute market regime from real VIX
        # Return weighted macro score based on regime
        ...

    def classify_yield_curve(self, spread: float) -> str:
        """Classify yield curve from 10Y-2Y spread.

        Returns one of: inverted, flat, normal, steep
        """
        ...

    def calculate_regime_risk_adjustment(
        self, macro_snapshot: MacroSnapshot, asset_class: str
    ) -> tuple[float, dict[str, Any]]:
        """Calculate per-asset-class regime-based risk adjustment."""
        ...
```

### Pattern 2: Additive Macro Overlay (4-Gate Safety, Same as Sentiment)

**What:** Macro overlay added AFTER composite score, with same 4 safety gates
**When to use:** In `_compute_weighted_score()` after sentiment overlay
**Example:**

```python
# Source: Modeled on _calculate_sentiment_overlay() in deep_analysis_scorer.py
def _calculate_macro_overlay(self, data: dict[str, Any], asset_class: str) -> tuple[float, dict[str, Any]]:
    """Calculate additive macro overlay adjustment.

    Applied AFTER composite score (SCORE-03).
    4-gate safety pattern from Phase 14.
    """
    details: dict[str, Any] = {"macro_overlay_applied": False}

    # Gate 1: Feature flag
    if not is_feature_enabled("macro_scoring"):
        details["reason"] = "feature_flag_off"
        return 0.0, details

    # Gate 2: Weight is zero
    weight = self.thresholds.weight_macro_overlay
    if weight == 0.0:
        details["reason"] = "weight_is_zero"
        return 0.0, details

    # Gate 3: Compute macro score (with asset_class sensitivity)
    macro_score, macro_details = self._macro_scorer.calculate_macro_score(data)
    details["macro_details"] = macro_details
    if macro_score is None:
        details["reason"] = "no_macro_data"
        return 0.0, details

    # Gate 4: Confidence threshold (macro data availability)
    confidence = macro_details.get("confidence", 0.0)
    if confidence < self.thresholds.macro_min_confidence:
        details["reason"] = "below_confidence_threshold"
        return 0.0, details

    # Compute adjustment with per-asset-class sensitivity
    sensitivity = self._get_asset_sensitivity(asset_class)
    adjustment = weight * macro_score * confidence * sensitivity
    details["macro_overlay_applied"] = True
    details["adjustment"] = adjustment
    return adjustment, details
```

### Pattern 3: Per-Asset-Class Sensitivity Coefficients (SCORE-04)

**What:** Different asset classes respond differently to macro indicators
**When to use:** When computing macro overlay adjustment
**Rationale:** Stocks are most sensitive to rate changes, ETFs partially sensitive (diversified), crypto least correlated to traditional macro

```python
# Per-asset-class sensitivity coefficients (configurable in ScoringThresholds)
MACRO_SENSITIVITY = {
    "stock": 1.0,   # Full macro sensitivity (rates, inflation, yield curve all matter)
    "etf": 0.7,     # Moderate sensitivity (diversified, but still correlated)
    "crypto": 0.3,  # Low sensitivity (less correlated to traditional macro indicators)
}
```

### Pattern 4: Yield Curve Regime Classification (MACRO-05)

**What:** Classify the 10Y-2Y Treasury spread into regimes
**When to use:** In MacroScorer for regime detection

```python
# Yield curve classification thresholds
def classify_yield_curve(spread: float) -> str:
    """Classify yield curve from 10Y-2Y spread in percentage points.

    Standard financial classification:
    - inverted: spread < 0    (recession signal)
    - flat: 0 <= spread < 0.5  (slowdown signal)
    - normal: 0.5 <= spread < 2.0  (healthy economy)
    - steep: spread >= 2.0     (recovery/expansion signal)
    """
    if spread < 0:
        return "inverted"
    elif spread < 0.5:
        return "flat"
    elif spread < 2.0:
        return "normal"
    else:
        return "steep"
```

### Pattern 5: Replacing Hardcoded Values (MACRO-01, MACRO-02)

**What:** Functions that use hardcoded VIX/rate values should accept optional MacroSnapshot
**When to use:** In `scoring_criteria.py::assess_market_regime()` and `market_context.py::_estimate_interest_rate()`

```python
# BEFORE (hardcoded):
vix_level = market_context.get("vix", 20.0)  # Hardcoded default

# AFTER (real data with fallback):
macro_snapshot = market_context.get("macro_snapshot")
if macro_snapshot and macro_snapshot.get("vix") is not None:
    vix_level = macro_snapshot["vix"]
else:
    vix_level = market_context.get("vix", 20.0)  # Fallback to original default
```

### Anti-Patterns to Avoid

- **Breaking existing behavior when flag is off:** The macro_scoring flag defaults to False. When off, ALL existing behavior MUST be identical. Zero regression.
- **Per-holding FRED calls:** MACRO-07 requires macro data is fetched ONCE per session. The SentimentMacroCollector already handles this caching. Do NOT add new FRED calls in per-holding loops.
- **Weight redistribution:** SCORE-03 says "adjust risk scoring weights dynamically" -- this means the RISK weight changes within the composite, NOT that the 40/30/30 split changes. The additive overlay adds a separate macro adjustment on top.
- **Hardcoded asset class lists:** Use the existing pattern of checking `asset_class` parameter, do not create separate scorer classes per asset type.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FRED API access | Custom HTTP client | `fredapi` (0.5.2, installed) | Already built in Phase 13 |
| Macro data caching | Custom cache | `SentimentMacroCollector._macro_snapshot` | Already caches per session |
| Feature flag gating | Manual env checks | `is_feature_enabled("macro_scoring")` | Project standard |
| Scoring overlay pattern | Custom integration | Copy sentiment overlay 4-gate pattern | Battle-tested in Phase 14 |
| Yield curve spread | Manual computation | `FREDAdapter.get_macro_snapshot()` | Already computes it |

**Key insight:** Phase 13 and 14 built 90% of the infrastructure. Phase 15 is mostly wiring and a new scorer component.

## Common Pitfalls

### Pitfall 1: Breaking the 40/30/30 Weight Distribution
**What goes wrong:** Developer interprets "dynamic risk weight adjustment" (SCORE-03) as changing the 40/30/30 fundamental/technical/risk split
**Why it happens:** The requirement says "adjusts risk scoring weights dynamically" which is ambiguous
**How to avoid:** The macro overlay is ADDITIVE on top of the composite (same as sentiment). Within the risk score itself (RiskScorer), you can adjust how volatility/drawdown/beta are weighted based on regime. But the 40/30/30 split stays.
**Warning signs:** Tests showing weight_fundamental != 0.40 when macro is enabled

### Pitfall 2: Per-Holding FRED Calls
**What goes wrong:** Each of 30+ holdings triggers a separate FRED API call
**Why it happens:** Developer adds FRED fetching inside the scoring loop
**How to avoid:** Macro data flows through `data["macro_snapshot"]` which is collected ONCE by SentimentMacroCollector in `collect_raw_data()`. The scorer only reads from the dict.
**Warning signs:** Multiple "FRED macro snapshot collected" log lines in a single run

### Pitfall 3: Forgetting the Feature Flag Gate
**What goes wrong:** Macro scoring runs even when FF_MACRO_SCORING=false
**Why it happens:** Developer wires scoring but skips the feature flag check
**How to avoid:** First gate in `_calculate_macro_overlay()` checks `is_feature_enabled("macro_scoring")`. Also gate 2 checks `weight_macro_overlay == 0.0`.
**Warning signs:** Default test runs showing non-zero macro adjustments

### Pitfall 4: NoneType Errors from Missing FRED Data
**What goes wrong:** MacroSnapshot fields are None (FRED unavailable), but code assumes float
**Why it happens:** FRED API may be unavailable (no key, rate limit, network), any field can be None
**How to avoid:** Every field access from MacroSnapshot MUST handle None. Use pattern: `if snapshot.vix is not None:` before any math.
**Warning signs:** TypeError in scoring during tests without FRED_API_KEY

### Pitfall 5: Using unittest.mock
**What goes wrong:** Test uses `from unittest.mock import patch` which is BANNED
**Why it happens:** Habit from other projects
**How to avoid:** Use `mocker.patch()` from pytest-mock exclusively. Enforced by `make check-unittest-mock`.
**Warning signs:** Import error from conftest_unittest_blocker.py

### Pitfall 6: Not Testing All Yield Curve Regimes
**What goes wrong:** Yield curve classification misses edge cases
**Why it happens:** Only testing normal and inverted, forgetting flat and steep
**How to avoid:** Parametrized tests covering: inverted (spread < 0), flat (0-0.5), normal (0.5-2.0), steep (>= 2.0), plus boundary values (0.0, 0.5, 2.0).
**Warning signs:** Yield curve always classified as "normal"

### Pitfall 7: Macro Score Exceeding Bounds
**What goes wrong:** Composite score goes above 1.0 or below 0.0 after overlay
**Why it happens:** Additive overlay not clamped
**How to avoid:** Same clamping as sentiment: `composite_score = max(0.0, min(1.0, composite_score + macro_adjustment + sentiment_adjustment))`
**Warning signs:** Scores > 1.0 in edge cases with high sentiment AND high macro adjustments

## Code Examples

### Example 1: MacroScorer calculate_macro_score() Skeleton

```python
# Source: Based on sentiment_scorer.py pattern (verified in codebase)
def calculate_macro_score(self, data: dict[str, Any], asset_class: str = "stock") -> tuple[float | None, dict[str, Any]]:
    details: dict[str, Any] = {}

    macro_raw = data.get("macro_snapshot")
    if macro_raw is None:
        details["reason"] = "no_macro_data"
        return None, details

    try:
        if isinstance(macro_raw, dict):
            snapshot = MacroSnapshot(**macro_raw)
        elif isinstance(macro_raw, MacroSnapshot):
            snapshot = macro_raw
        else:
            details["reason"] = "invalid_macro_data_type"
            return None, details
    except Exception as e:
        details["reason"] = "parse_error"
        details["error"] = str(e)
        return None, details

    # Classify yield curve regime
    yield_regime = "unknown"
    if snapshot.yield_curve_spread is not None:
        yield_regime = self.classify_yield_curve(snapshot.yield_curve_spread)
    details["yield_curve_regime"] = yield_regime

    # Market regime from real VIX
    market_regime = snapshot.get_market_regime()
    details["market_regime"] = market_regime

    # Compute macro score based on regime
    score = self._compute_regime_score(snapshot, yield_regime, market_regime, asset_class)
    details["macro_score"] = score
    details["asset_class"] = asset_class

    # Confidence based on data completeness
    available_fields = sum(1 for f in [snapshot.vix, snapshot.fed_rate, snapshot.cpi_yoy,
                                         snapshot.treasury_10y, snapshot.treasury_2y] if f is not None)
    confidence = available_fields / 5.0
    details["confidence"] = confidence
    details["available_macro_fields"] = available_fields

    return score, details
```

### Example 2: Yield Curve Regime Classification

```python
# Standard financial classification thresholds
def classify_yield_curve(self, spread: float) -> str:
    if spread < self.thresholds.yield_curve_inverted:     # default: 0.0
        return "inverted"
    elif spread < self.thresholds.yield_curve_flat:       # default: 0.5
        return "flat"
    elif spread < self.thresholds.yield_curve_steep:      # default: 2.0
        return "normal"
    else:
        return "steep"
```

### Example 3: Dynamic Risk Weight Adjustment (SCORE-03)

```python
# Inside MacroScorer: adjust risk emphasis based on regime
def _compute_regime_score(self, snapshot: MacroSnapshot, yield_regime: str,
                           market_regime: str, asset_class: str) -> float:
    """Compute macro adjustment score from -1.0 to +1.0.

    Negative = headwinds (increase risk aversion)
    Positive = tailwinds (favorable macro conditions)
    """
    score = 0.0

    # VIX component: high VIX = negative, low VIX = positive
    if snapshot.vix is not None:
        if snapshot.vix > 30:
            score -= 0.4  # High volatility headwind
        elif snapshot.vix > 20:
            score -= 0.1  # Mildly elevated
        elif snapshot.vix < 15:
            score += 0.2  # Low volatility tailwind

    # Yield curve component
    if yield_regime == "inverted":
        score -= 0.3  # Strong recession signal
    elif yield_regime == "flat":
        score -= 0.1  # Caution signal
    elif yield_regime == "steep":
        score += 0.2  # Recovery/expansion signal

    # Interest rate environment
    if snapshot.fed_rate is not None:
        if snapshot.fed_rate > 5.0:
            score -= 0.1  # Tight policy headwind
        elif snapshot.fed_rate < 2.0:
            score += 0.1  # Accommodative tailwind

    # Asset-class sensitivity (SCORE-04)
    sensitivity = self.thresholds.macro_sensitivity_stock  # or _etf, _crypto
    if asset_class == "etf":
        sensitivity = self.thresholds.macro_sensitivity_etf
    elif asset_class == "crypto":
        sensitivity = self.thresholds.macro_sensitivity_crypto

    return max(-1.0, min(1.0, score * sensitivity))
```

### Example 4: Wiring into DeepAnalysisScorer._compute_weighted_score()

```python
# In deep_analysis_scorer.py, after sentiment overlay:

# Phase 15: Additive macro overlay (SCORE-03, SCORE-04)
macro_adjustment, macro_details = self._calculate_macro_overlay(data or {}, asset_class)
if macro_adjustment != 0.0:
    composite_score = max(0.0, min(1.0, composite_score + macro_adjustment))
scores["macro_overlay"] = macro_details
```

### Example 5: Replacing Hardcoded VIX in assess_market_regime() (MACRO-01)

```python
# In tools/scoring/scoring_criteria.py
def assess_market_regime(market_context: dict[str, Any], cache=None) -> MarketRegime:
    # Try real macro data first (MACRO-01)
    macro_snapshot = market_context.get("macro_snapshot")
    if macro_snapshot and isinstance(macro_snapshot, dict):
        vix_level = macro_snapshot.get("vix") or market_context.get("vix", 20.0)
        inflation_rate = macro_snapshot.get("cpi_yoy") or market_context.get("inflation", 3.0)
    else:
        vix_level = market_context.get("vix", 20.0)
        inflation_rate = market_context.get("inflation", 3.0)
    # ... rest of function unchanged
```

### Example 6: New ScoringThresholds Fields

```python
# New fields to add to ScoringThresholds dataclass
# ============================================================================
# MACRO SCORING CONFIGURATION (Phase 15)
# ============================================================================

# Yield curve classification thresholds (10Y-2Y spread in percentage points)
yield_curve_inverted: float = 0.0     # Below 0 = inverted
yield_curve_flat: float = 0.5         # 0 to 0.5 = flat
yield_curve_steep: float = 2.0        # Above 2.0 = steep (0.5-2.0 = normal)

# Per-asset-class macro sensitivity coefficients (SCORE-04)
macro_sensitivity_stock: float = 1.0   # Full sensitivity
macro_sensitivity_etf: float = 0.7     # Moderate sensitivity
macro_sensitivity_crypto: float = 0.3  # Low sensitivity

# Macro confidence threshold
macro_min_confidence: float = 0.0      # Minimum confidence to apply (0.0 = always)

# VIX regime thresholds for scoring
macro_vix_high: float = 30.0          # High volatility threshold
macro_vix_elevated: float = 20.0      # Elevated volatility threshold
macro_vix_low: float = 15.0           # Low volatility threshold

# Fed rate thresholds
macro_rate_tight: float = 5.0         # Tight monetary policy threshold
macro_rate_accommodative: float = 2.0  # Accommodative policy threshold
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| VIX hardcoded to 20.0 | Real VIX from FRED via MacroSnapshot | Phase 15 (now) | Market regime reflects actual conditions |
| Interest rate estimated from trend string | Real Fed funds rate from FRED | Phase 15 (now) | Accurate rate environment assessment |
| No yield curve analysis | 10Y-2Y spread with 4-regime classification | Phase 15 (now) | Recession/recovery signal detection |
| Static risk weights | Dynamic risk adjustment based on macro regime | Phase 15 (now) | Risk scoring adapts to market conditions |
| Same scoring for all assets | Per-asset-class macro sensitivity coefficients | Phase 15 (now) | Crypto less affected by rates than stocks |

**What exists and is ready from prior phases:**
- FREDAdapter fetches all 7 FRED series (Phase 13)
- MacroSnapshot schema with `get_market_regime()` method (Phase 13)
- SentimentMacroCollector caches macro per session (Phase 13)
- Pipeline already passes `macro_snapshot` in raw data dict (Phase 13)
- Additive overlay pattern with 4-gate safety (Phase 14)
- `weight_macro_overlay` in ScoringThresholds (Phase 14)
- `macro_scoring` feature flag (Phase 13)

## Open Questions

1. **Risk weight redistribution vs additive overlay for SCORE-03**
   - What we know: The requirement says "adjusts risk scoring weights dynamically based on market regime." The additive overlay pattern is established.
   - What's unclear: Should "risk scoring weights" mean (a) the overlay adjusts the overall risk contribution, or (b) within RiskScorer, the volatility/drawdown/beta sub-weights shift?
   - Recommendation: Implement as additive overlay (consistent with Phase 14 pattern). The overlay score reflects macro risk assessment and gets added on top. If needed, RiskScorer internal sub-weights can also shift in a future enhancement. Keep it simple for now.

2. **Exact macro score magnitude**
   - What we know: The score should be in [-1.0, +1.0] range with the weight controlling its impact.
   - What's unclear: What's the right balance between VIX, yield curve, and rate components? What magnitude of adjustment is appropriate?
   - Recommendation: Start with conservative coefficients (max total: +/- 0.5 before weight scaling). The weight_macro_overlay defaults to 0.0, so any initial magnitude is gated. Tune later based on backtesting.

3. **Crypto macro sensitivity value**
   - What we know: Crypto is less correlated to traditional macro indicators than stocks.
   - What's unclear: The exact correlation coefficient. Academic research shows Bitcoin's correlation to macro factors has increased post-2020 but remains lower than equities.
   - Recommendation: Start with 0.3 (configurable in ScoringThresholds). This is a tuning parameter, not a critical architectural decision.

## Sources

### Primary (HIGH confidence)
- `src/finwiz/scoring/sentiment_scorer.py` -- SentimentScorer pattern (verified in codebase)
- `src/finwiz/scoring/deep_analysis_scorer.py` -- `_compute_weighted_score()` and `_calculate_sentiment_overlay()` (verified)
- `src/finwiz/scoring/thresholds.py` -- ScoringThresholds with `weight_macro_overlay` (verified)
- `src/finwiz/data/adapters/fred_adapter.py` -- FREDAdapter with all FRED series and yield curve computation (verified)
- `src/finwiz/schemas/macro.py` -- MacroSnapshot with `get_market_regime()` (verified)
- `src/finwiz/data/sentiment_collector.py` -- SentimentMacroCollector per-session caching (verified)
- `src/finwiz/config/features/definitions.py` -- `macro_scoring` feature flag (verified)
- `src/finwiz/tools/scoring/scoring_criteria.py` -- `assess_market_regime()` with hardcoded VIX=20.0 (verified)
- `src/finwiz/orchestrators/extraction/market_context.py` -- `_estimate_interest_rate()` with hardcoded rates (verified)
- `src/finwiz/analysis/deep_analysis_pipeline.py` -- Pipeline already collects macro_snapshot (verified)
- `tests/unit/scoring/test_sentiment_scorer.py` -- Test pattern to follow (verified)

### Secondary (MEDIUM confidence)
- Yield curve classification thresholds (inverted < 0, flat 0-0.5, normal 0.5-2.0, steep > 2.0) -- standard financial convention widely documented
- VIX regime thresholds (15/20/30) -- based on CBOE historical percentile data, consistent with existing codebase usage

### Tertiary (LOW confidence)
- Crypto macro sensitivity coefficient (0.3) -- rough estimate based on general understanding of crypto-macro correlations; should be validated with backtesting data

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all infrastructure exists from Phase 13-14, no new dependencies
- Architecture: HIGH -- follows exact SentimentScorer pattern from Phase 14, all integration points identified
- Pitfalls: HIGH -- based on direct analysis of codebase patterns and existing anti-pattern enforcement (unittest.mock blocker, feature flags)
- Yield curve thresholds: MEDIUM -- standard financial convention but exact boundaries are judgment calls
- Per-asset sensitivity: LOW -- crypto coefficient (0.3) is a tuning parameter without strong empirical backing in this context

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (stable -- all dependencies pinned, patterns established)
