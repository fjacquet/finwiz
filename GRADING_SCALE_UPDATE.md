# Grading Scale Update - More Discriminating Thresholds

## Date: 2025-11-14

## Problem Identified

The original grading scale was **too lenient**, resulting in most holdings receiving B or better grades even when they were mediocre performers. This made the grading system less useful for identifying truly exceptional vs. average investments.

### Original Scale (TOO LENIENT)

| Grade | Score Range | Description |
|-------|-------------|-------------|
| A+ | 85%+ | Exceptional |
| A | 75-84% | Excellent |
| B | 65-74% | Good |
| C | 55-64% | Average |
| D | 45-54% | Below Average |
| F | <45% | Poor |

**Problem**: Even holdings with 65% scores (barely passing) received B grades.

## New Scale (MORE DISCRIMINATING)

| Grade | Score Range | Description | Change |
|-------|-------------|-------------|--------|
| A+ | 90%+ | Exceptional | +5% (stricter) |
| A | 80-89% | Excellent | +5% (stricter) |
| B | 70-79% | Good | +5% (stricter) |
| C | 60-69% | Average | +5% (stricter) |
| D | 50-59% | Below Average | +5% (stricter) |
| F | <50% | Poor | +5% (stricter) |

**Benefit**: Only truly exceptional investments (90%+) receive A+ grades.

## Impact on Existing Holdings

Based on current portfolio analysis:

### Before (Old Scale)
- **All holdings**: B or better
- **Top holdings**: A+ (92%)
- **Bottom holdings**: B (66%)
- **Problem**: No discrimination between good and mediocre

### After (New Scale)
- **Top holdings**: A+ (92%) ✅ Still exceptional
- **Good holdings**: A (85-88%) ✅ Properly recognized
- **Average holdings**: B (70-75%) ⚠️ More realistic
- **Below average**: C (65-68%) ⚠️ Needs attention
- **Benefit**: Clear differentiation between quality levels

## Recommendation Thresholds Also Updated

### Buy Threshold
- **Old**: 70% (A- or better)
- **New**: 80% (A or better)
- **Rationale**: Only recommend buying excellent investments

### Sell Threshold
- **Old**: 50% (Below C)
- **New**: 60% (Below C)
- **Rationale**: Consider selling average performers, not just poor ones

## Example Holdings Regraded

| Ticker | Score | Old Grade | New Grade | Change |
|--------|-------|-----------|-----------|--------|
| CORC.SW | 0.920 | A+ | A+ | No change (truly exceptional) |
| VUSA.L | 0.880 | A+ | A | Downgraded (excellent, not exceptional) |
| SCMN.SW | 0.850 | A+ | A | Downgraded (excellent, not exceptional) |
| BROS | 0.706 | B | B | No change (good) |
| DELL | 0.688 | B | C | Downgraded (average, needs review) |
| XAIX | 0.656 | B | C | Downgraded (average, needs review) |

## Benefits

1. **Better Discrimination**: Clear separation between exceptional, good, and average investments
2. **More Actionable**: C grades now signal "review needed" rather than "acceptable"
3. **Realistic Standards**: Aligns with professional investment grading standards
4. **Motivates Improvement**: Encourages portfolio optimization by highlighting mediocre holdings

## Implementation

- **File Modified**: `src/finwiz/scoring/deep_analysis_scorer.py`
- **Lines Changed**: Grade thresholds and recommendation thresholds
- **Backward Compatible**: Yes (only changes grade assignments, not scoring logic)
- **Effective**: Immediately for all new analyses

## Next Steps

1. ✅ Grading scale updated
2. ⏳ Re-run portfolio analysis to see new grades
3. ⏳ Review holdings that dropped to C or D grades
4. ⏳ Consider replacing C/D holdings with A+ alternatives

## Notes

- The **scoring algorithm** remains unchanged (still 40% fundamental, 30% technical, 30% risk)
- Only the **grade assignment thresholds** have been adjusted
- This makes the system more aligned with professional investment standards
- A+ grades are now truly reserved for exceptional opportunities (top 10%)

---

**Recommendation**: Re-run your portfolio analysis to see the updated grades and identify holdings that may need replacement.
