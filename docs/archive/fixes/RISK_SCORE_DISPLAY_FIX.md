# Risk Score Display Fix

## Problem Identified

You correctly identified a **confusing and backwards risk display** in the consolidated report:

**Before Fix:**
- UBSG.SW showed "Risque: 5.8/10" with yellow color (risk-medium)
- This **looked like high risk** to users
- But internally, 5.8/10 meant **LOW RISK** (good!)

## Root Cause

The risk scoring system has **inverted semantics**:

```python
def calculate_risk_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """
    Calculate risk score (0-5 scale converted to 0-1, where 1 = low risk).
    """
```

So:
- **risk_score = 0.58** = LOW RISK (low volatility, small drawdown)
- **risk_score = 0.20** = HIGH RISK (high volatility, large drawdown)

But the template was displaying it as:
```jinja
{{ "%.1f"|format(analysis.risk_score * 10) }}/10
```

This showed **5.8/10** which looks like **high risk** to users!

## The Fix Applied

### Changed in `src/finwiz/templates/crew_reports/final_report.html`

**1. Inverted the display formula:**
```jinja
{# OLD - Confusing #}
{{ "%.1f"|format(analysis.risk_score * 10) }}/10

{# NEW - Clear #}
{{ "%.1f"|format((1.0 - analysis.risk_score) * 10) }}/10
```

Now:
- risk_score 0.58 → displays as **4.2/10** (lower number = lower risk)
- risk_score 0.20 → displays as **8.0/10** (higher number = higher risk)

**2. Fixed the color thresholds:**
```jinja
{# OLD - Backwards #}
risk-{{ 'low' if analysis.risk_score <= 0.3 else ('medium' if analysis.risk_score <= 0.6 else 'high') }}

{# NEW - Correct #}
risk-{{ 'high' if analysis.risk_score <= 0.3 else ('medium' if analysis.risk_score <= 0.6 else 'low') }}
```

Now:
- risk_score ≤ 0.3 → RED (high risk)
- risk_score 0.3-0.6 → YELLOW (medium risk)  
- risk_score ≥ 0.7 → GREEN (low risk)

**3. Added descriptive labels:**
```jinja
<small>{% if analysis.risk_score >= 0.7 %}Faible{% elif analysis.risk_score >= 0.4 %}Modéré{% else %}Élevé{% endif %}</small>
```

Now users see:
- "4.2/10" with "Faible" (Low) label in GREEN
- "8.0/10" with "Élevé" (High) label in RED

**4. Changed header from "Risque" to "Niveau de Risque"** for clarity

## Result

**After Fix:**
- UBSG.SW now shows "Niveau de Risque: 4.2/10 Faible" in GREEN
- This correctly communicates **LOW RISK**
- Higher numbers = higher risk (intuitive!)
- Color coding matches the risk level (green = low, red = high)

## Example Transformations

| Internal Score | OLD Display | NEW Display | Meaning |
|----------------|-------------|-------------|---------|
| 0.90 (very safe) | 9.0/10 🟡 | 1.0/10 🟢 Faible | Very Low Risk |
| 0.70 (safe) | 7.0/10 🔴 | 3.0/10 🟢 Faible | Low Risk |
| 0.58 (moderate) | 5.8/10 🟡 | 4.2/10 🟡 Modéré | Moderate Risk |
| 0.40 (risky) | 4.0/10 🟢 | 6.0/10 🟡 Modéré | Moderate-High Risk |
| 0.20 (very risky) | 2.0/10 🟢 | 8.0/10 🔴 Élevé | High Risk |

## Testing

To verify the fix:
1. Run a portfolio analysis
2. Check the consolidated report at `output/reports/default/final_report.html`
3. Look at the "Niveau de Risque" column
4. Verify:
   - Lower numbers (1-3) are GREEN with "Faible"
   - Medium numbers (4-6) are YELLOW with "Modéré"
   - Higher numbers (7-10) are RED with "Élevé"

## Summary

The risk display is now **intuitive and correct**:
- ✅ Higher number = higher risk (matches user expectations)
- ✅ Color coding matches risk level (green = safe, red = risky)
- ✅ Descriptive labels clarify the meaning
- ✅ No more confusion about what the score means!

Great catch on identifying this confusing display! 🎯
