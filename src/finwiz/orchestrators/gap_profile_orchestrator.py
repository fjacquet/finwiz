"""Gap Profile Orchestrator for FinWiz Flow (Phase 3.6).

Builds a deterministic :class:`PortfolioGapProfile` describing what the current
(equal-weight) portfolio lacks, from deep-analysis results + cheap cached market
data. The profile is written to ``state.portfolio_gap_profile`` and persisted to
``output/discovery/gap_profile.json`` so the discovery pipeline (which is
instantiated without flow state) can load it.

Pure Python (AI-minimalism). Fail-soft: any failure yields an empty profile,
which makes downstream :class:`PortfolioFitScorer` return neutral fit so the
cascade degrades to standalone-factor ranking (pre-cascade behavior).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.flow_state import FinwizState
from finwiz.schemas.newcomer_discovery import PortfolioGapProfile, UnderperformerSlot
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

GAP_PROFILE_PATH = Path("output") / "discovery" / "gap_profile.json"
_UNDERPERFORMER_GRADES = {"C", "C-", "D+", "D", "D-", "F"}


class GapProfileOrchestrator:
    """Builds the portfolio gap profile consumed by the opportunity cascade."""

    def __init__(self, state: FinwizState, **dependencies: Any) -> None:
        self.state = state
        self.logger = get_logger(self.__class__.__name__)

    def build_gap_profile(self) -> dict[str, Any]:
        """Build, store, and persist the portfolio gap profile.

        Returns:
            dict with keys ``gap_profile_complete`` and ``is_empty``.
        """
        self.logger.info("=" * 80)
        self.logger.info("Phase 3.6: Building portfolio gap profile")
        self.logger.info("=" * 80)

        try:
            profile = self._compute_profile()
        except Exception as e:
            self.logger.warning("Gap profile build failed, using empty profile: %s", e)
            profile = PortfolioGapProfile(session_id=self.state.session_id or "", is_empty=True)

        self.state.portfolio_gap_profile = profile.model_dump()
        self._persist(profile)
        self.logger.info(
            "Gap profile built: %d holdings, %d sectors, %d underperformer slots (empty=%s)",
            len(profile.holdings),
            len(profile.sector_weights),
            len(profile.underperformer_slots),
            profile.is_empty,
        )
        return {"gap_profile_complete": True, "is_empty": profile.is_empty}

    def _compute_profile(self) -> PortfolioGapProfile:
        results = self.state.deep_analysis_results or {}
        if not results:
            self.logger.warning("No deep analysis results; gap profile will be empty")
            return PortfolioGapProfile(session_id=self.state.session_id or "", is_empty=True)

        holdings = sorted(results.keys())
        # Group by asset class for correct yfinance symbol normalization.
        by_class: dict[str, list[str]] = {}
        for ticker, res in results.items():
            by_class.setdefault(getattr(res, "asset_class", "stock") or "stock", []).append(ticker)

        from finwiz.discovery.market_data import get_returns, get_sectors

        sectors: dict[str, str | None] = {}
        holding_returns: dict[str, list[float]] = {}
        for asset_class, tickers in by_class.items():
            sectors.update(get_sectors(tickers, asset_class))
            holding_returns.update(get_returns(tickers, asset_class))

        sector_weights = self._sector_weights(sectors)
        underweight = self._underweight_sectors(sector_weights)
        mean_risk = self._mean_low_risk_score(results)
        slots = self._underperformer_slots(results, sectors)

        return PortfolioGapProfile(
            session_id=self.state.session_id or "",
            timestamp=datetime.now().isoformat(),
            holdings=holdings,
            sector_weights=sector_weights,
            underweight_sectors=underweight,
            holding_returns=holding_returns,
            mean_risk_score=mean_risk,
            underperformer_slots=slots,
            is_empty=False,
        )

    @staticmethod
    def _sector_weights(sectors: dict[str, str | None]) -> dict[str, float]:
        """Count-share per sector across holdings with a known sector."""
        known = [s for s in sectors.values() if s]
        if not known:
            return {}
        counts: dict[str, int] = {}
        for s in known:
            counts[s] = counts.get(s, 0) + 1
        total = len(known)
        return {sector: count / total for sector, count in counts.items()}

    @staticmethod
    def _underweight_sectors(sector_weights: dict[str, float]) -> list[str]:
        """Held sectors whose share is below an equal-spread baseline."""
        if not sector_weights:
            return []
        baseline = 1.0 / len(sector_weights)
        return sorted([s for s, w in sector_weights.items() if w < baseline])

    @staticmethod
    def _to_low_risk(raw: float | None) -> float | None:
        """Convert risk_score (0-5, 5=high risk) to a 0-1 low-risk-is-high score."""
        if raw is None:
            return None
        return 1.0 - max(0.0, min(1.0, float(raw) / 5.0))

    @classmethod
    def _mean_low_risk_score(cls, results: dict[str, Any]) -> float | None:
        """Mean holding risk on a 0-1 (1 = low risk) scale."""
        scores = [low for res in results.values() if (low := cls._to_low_risk(getattr(res, "risk_score", None))) is not None]
        return sum(scores) / len(scores) if scores else None

    @classmethod
    def _underperformer_slots(cls, results: dict[str, Any], sectors: dict[str, str | None]) -> list[UnderperformerSlot]:
        slots: list[UnderperformerSlot] = []
        for ticker, res in results.items():
            grade = getattr(res, "grade", "") or ""
            if grade not in _UNDERPERFORMER_GRADES:
                continue
            low_risk = cls._to_low_risk(getattr(res, "risk_score", None))
            slots.append(
                UnderperformerSlot(
                    ticker=ticker,
                    asset_class=getattr(res, "asset_class", "stock") or "stock",
                    grade=grade,
                    sector=sectors.get(ticker.upper()),
                    risk_score=low_risk,
                )
            )
        return slots

    def _persist(self, profile: PortfolioGapProfile) -> None:
        try:
            GAP_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with GAP_PROFILE_PATH.open("w", encoding="utf-8") as f:
                json.dump(profile.model_dump(), f, indent=2, default=str)
            self.logger.info("Saved gap profile to %s", GAP_PROFILE_PATH)
        except OSError as e:
            self.logger.warning("Failed to persist gap profile: %s", e)


def load_gap_profile() -> PortfolioGapProfile:
    """Load the persisted gap profile, or an empty profile if unavailable.

    Used by the discovery pipeline, which runs without flow state.
    """
    try:
        if GAP_PROFILE_PATH.exists():
            with GAP_PROFILE_PATH.open(encoding="utf-8") as f:
                data = json.load(f)
            return PortfolioGapProfile(**data)
    except Exception as e:  # incl. pydantic ValidationError (not a ValueError in v2) on schema drift
        logger.warning("Failed to load gap profile, using empty: %s", e)
    return PortfolioGapProfile(is_empty=True)
