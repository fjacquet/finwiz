"""Portfolio-fit scorer for the Portfolio-Aware Opportunity Cascade.

Pure-Python (AI-minimalism): rates how much a candidate *improves the current
portfolio* — independent of the candidate's standalone quality. The discovery
pipeline multiplies a candidate's standalone factor score by this fit score, so
a great asset the portfolio already effectively owns ranks below a good asset
that fills a hole.

The score blends up to three terms, each in ``[0, 1]``:

* **sector gap match** — under-/un-represented sectors score high; heavily-held
  sectors score low. Needs the candidate sector + ``sector_weights``.
* **diversification** — ``1 - max correlation`` to held names. Needs the
  candidate's return series + ``holding_returns``.
* **risk reduction** — lower-risk-than-average candidates reduce concentration.
  Needs the candidate risk score + ``mean_risk_score``.

Any term whose inputs are unavailable is dropped and its weight redistributed
proportionally across the remaining terms (graceful degradation). When *no*
term can be computed the scorer returns a neutral ``0.5`` — which makes the
multiplicative final score collapse to the standalone factor score, i.e. the
pre-cascade behavior.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from finwiz.scoring.thresholds import ScoringThresholds, get_thresholds
from finwiz.tools.logger import get_logger

if TYPE_CHECKING:
    from finwiz.schemas.newcomer_discovery import PortfolioGapProfile

logger = get_logger(__name__)

NEUTRAL_FIT = 0.5


def _clamp01(value: float) -> float:
    """Clamp a value to the closed interval [0, 1]."""
    return max(0.0, min(1.0, value))


def _max_correlation(candidate: list[float], holdings: dict[str, list[float]]) -> float | None:
    """Return the max abs Pearson correlation of ``candidate`` to any holding series.

    Series are aligned by truncating both to their common (shortest) length.
    Returns ``None`` when no usable pair exists (too short / zero variance).
    """
    if not candidate or not holdings:
        return None

    import numpy as np

    cand = np.asarray(candidate, dtype=float)
    best: float | None = None
    for series in holdings.values():
        if not series:
            continue
        other = np.asarray(series, dtype=float)
        n = min(cand.size, other.size)
        if n < 3:  # need a few points for a meaningful correlation
            continue
        a, b = cand[-n:], other[-n:]
        if a.std() == 0.0 or b.std() == 0.0:
            continue
        corr = float(np.corrcoef(a, b)[0, 1])
        if np.isnan(corr):
            continue
        abs_corr = abs(corr)
        best = abs_corr if best is None else max(best, abs_corr)
    return best


class PortfolioFitScorer:
    """Scores a candidate's marginal fit to a :class:`PortfolioGapProfile`."""

    def __init__(self, thresholds: ScoringThresholds | None = None) -> None:
        self.thresholds = thresholds or get_thresholds()
        self.logger = logger

    def score(
        self,
        profile: PortfolioGapProfile,
        *,
        sector: str | None = None,
        returns: list[float] | None = None,
        risk_score: float | None = None,
    ) -> tuple[float, str | None]:
        """Compute ``portfolio_fit`` and the gap label this candidate addresses.

        Args:
            profile: The current portfolio gap profile.
            sector: Candidate sector (yfinance ``.info`` sector), if known.
            returns: Candidate daily-return series, if available.
            risk_score: Candidate risk score (0-1, 1 = low risk), if available.

        Returns:
            ``(fit, gap_filled)`` where ``fit`` is in ``[0, 1]`` and ``gap_filled``
            names the sector the candidate diversifies into (or ``None``).
        """
        if profile is None or getattr(profile, "is_empty", True):
            return NEUTRAL_FIT, None

        terms: list[tuple[float, float]] = []  # (weight, value)
        gap_filled: str | None = None

        # --- sector gap match -------------------------------------------------
        if sector:
            held_share = profile.sector_weights.get(sector, 0.0)
            sector_match = _clamp01(1.0 - held_share)
            terms.append((self.thresholds.weight_fit_sector, sector_match))
            if sector in profile.underweight_sectors or held_share == 0.0:
                gap_filled = sector

        # --- diversification (low correlation) --------------------------------
        if returns:
            max_corr = _max_correlation(returns, profile.holding_returns)
            if max_corr is not None:
                terms.append((self.thresholds.weight_fit_diversification, _clamp01(1.0 - max_corr)))

        # --- risk-concentration reduction -------------------------------------
        if risk_score is not None and profile.mean_risk_score is not None:
            # risk_score: 1 = low risk. Safer-than-average -> reduces concentration.
            risk_reduction = _clamp01(0.5 + (risk_score - profile.mean_risk_score))
            terms.append((self.thresholds.weight_fit_risk, risk_reduction))

        if not terms:
            return NEUTRAL_FIT, gap_filled

        total_weight = sum(w for w, _ in terms)
        if total_weight <= 0.0:
            return NEUTRAL_FIT, gap_filled

        fit = sum(w * v for w, v in terms) / total_weight
        return _clamp01(fit), gap_filled

    def score_for_slot(
        self,
        profile: PortfolioGapProfile,
        slot_sector: str | None,
        *,
        sector: str | None = None,
        returns: list[float] | None = None,
        risk_score: float | None = None,
    ) -> tuple[float, str | None]:
        """Score a candidate as a replacement for a specific underperformer slot.

        Same blend as :meth:`score`, but a candidate matching the slot's sector
        is rewarded (it fills the freed slot), so alternatives stay on-theme
        while still favoring diversification and lower risk.
        """
        fit, gap_filled = self.score(profile, sector=sector, returns=returns, risk_score=risk_score)
        if slot_sector and sector and sector == slot_sector:
            # Nudge toward same-sector replacements without overriding the blend.
            fit = _clamp01(0.5 * fit + 0.5)
            gap_filled = gap_filled or slot_sector
        return fit, gap_filled
