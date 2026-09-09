"""Alternatives Matching Orchestrator for FinWiz Flow."""

import os
from typing import Any

from finwiz.flow_state import FinwizState
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


# A fund whose largest sector is below this weight is treated as having no single
# sector: a broad world index peaks around 0.24 in Technology, which is a
# composition fact, not a sector thesis.
_MIN_DOMINANT_SECTOR_WEIGHT = 0.40


def _fact_pack_details(analysis: Any) -> dict[str, Any]:
    """Return the fact pack's ``details`` mapping, or an empty one."""
    fact_pack = getattr(analysis, "fact_pack", None)
    if fact_pack is None:
        return {}
    details = fact_pack.get("details") if isinstance(fact_pack, dict) else getattr(fact_pack, "details", None)
    return details if isinstance(details, dict) else {}


def _extract_sector(analysis: Any) -> str | None:
    """Best available sector label for a holding, or None.

    An equity has one sector. A fund does not -- it has ``sector_weights`` -- so
    its dominant sector is used, which is what makes "same sector" mean anything
    for a fund at all. Below ``_MIN_DOMINANT_SECTOR_WEIGHT`` the fund is too
    diversified for a single label to describe it (a world index would otherwise
    be filed under Technology at ~24%), and None is returned so the sector step
    skips rather than pairing a broad fund with a sector fund.
    """
    details = _fact_pack_details(analysis)

    sector = details.get("sector")
    if isinstance(sector, str) and sector.strip():
        return sector.strip()

    weights = details.get("sector_weights")
    if isinstance(weights, dict) and weights:
        numeric = {k: float(v) for k, v in weights.items() if isinstance(v, (int, float))}
        if numeric:
            top, weight = max(numeric.items(), key=lambda kv: kv[1])
            if weight >= _MIN_DOMINANT_SECTOR_WEIGHT:
                return top.replace("_", " ").strip()

    return None


def _extract_expense_ratio(analysis: Any) -> float | None:
    """Expense ratio as a fraction (0.0015 = 0.15%), or None when unknown."""
    details = _fact_pack_details(analysis)
    candidates = [details.get("expense_ratio")]

    fundamentals = getattr(analysis, "fundamental_details", None)
    if isinstance(fundamentals, dict):
        candidates.append(fundamentals.get("expense_ratio"))

    for value in candidates:
        if value is None:
            continue
        try:
            ratio = float(value)
        except (TypeError, ValueError):
            continue
        if 0.0 <= ratio < 1.0:
            return ratio

    return None


class AlternativesMatchingOrchestrator:
    """Finds and matches A+ alternatives for underperforming holdings."""

    def __init__(self, state: FinwizState, **dependencies: Any) -> None:
        """
        Initialize AlternativesMatchingOrchestrator.

        Args:
            state: FinwizState instance for accessing flow state
            **dependencies: Additional dependencies (unused currently)

        """
        self.state = state
        self.logger = get_logger(self.__class__.__name__)

    def match_alternatives_for_holdings(
        self,
        holdings: list[dict[str, Any]],
        discovery_results: dict[str, Any],
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Match alternatives from discovery results.

        Requirements: 4.1, 4.2, 4.3, 4.4

        Args:
            holdings: List of holdings with deep analysis results
            discovery_results: Discovery crew results (currently unused, for future enhancement)

        Returns:
            dict: Alternatives data keyed by ticker, empty dict if disabled or no alternatives

        """
        # Check if alternative matching is enabled
        enabled = (os.getenv("PORTFOLIO_ENABLE_ALTERNATIVES") or "true").strip().lower() in {"1", "true", "yes", "on"}
        if not enabled:
            self.logger.info("Alternative matching disabled via PORTFOLIO_ENABLE_ALTERNATIVES")
            return {}

        if not holdings:
            self.logger.warning("No holdings provided for alternative matching")
            return {}

        # Import here to avoid circular dependencies
        from finwiz.tools.alternative_finder_tool import AlternativeFinder, HoldingProfile

        # Check if any holdings need alternatives before instantiating finder
        needs_alternatives = any(holding.get("grade") in ["C", "D", "F"] for holding in holdings)

        if not needs_alternatives:
            self.logger.info("No underperforming holdings (all grades B or above)")
            return {}

        # Only instantiate AlternativeFinder if needed
        alternative_finder = AlternativeFinder()
        max_alternatives = int(os.getenv("PORTFOLIO_MAX_ALTERNATIVES", "5"))

        # Process holdings with grade C or below
        alternatives_data = {}
        alternatives_count = 0

        for holding in holdings:
            ticker = holding.get("ticker")
            if not ticker:
                continue

            # Extract grade - handle both dict and object types
            if isinstance(holding, dict):
                grade = holding.get("grade", "D")
                # Try risk_score directly first (Python scorer), then fall back to risk.score (legacy)
                risk_score = holding.get("risk_score")
                if risk_score is None:
                    risk_obj = holding.get("risk", {})
                    risk_score = risk_obj.get("score") if isinstance(risk_obj, dict) else getattr(risk_obj, "score", None)
                composite_score = holding.get("composite_score")
                name = holding.get("name", ticker)
                asset_class = holding.get("asset_class", "stock")
                sector = holding.get("sector")
                expense_ratio = holding.get("expense_ratio")
            else:
                grade = getattr(holding, "grade", "D")
                # Try risk_score directly first (DeepAnalysisResult), then fall back to risk.score (legacy)
                risk_score = getattr(holding, "risk_score", None)
                if risk_score is None:
                    risk_obj = getattr(holding, "risk", None)
                    risk_score = risk_obj.score if risk_obj else None
                composite_score = getattr(holding, "composite_score", None)
                name = getattr(holding, "name", ticker)
                asset_class = getattr(holding, "asset_class", "stock")
                sector = getattr(holding, "sector", None)
                expense_ratio = getattr(holding, "expense_ratio", None)

            # Only find alternatives for grades C, D, or F (Requirement 4.1)
            if grade not in ["C", "D", "F"]:
                self.logger.debug(f"Skipping alternative matching for {ticker} (grade: {grade} - B or above)")
                continue

            try:
                # FAIL LOUDLY - NO DEFAULTS FOR FINANCIAL DATA
                if risk_score is None:
                    self.logger.error(f"❌ CRITICAL: Missing risk_score for {ticker} - cannot make investment decisions without risk data")
                    raise ValueError(f"Missing required field 'risk_score' for {ticker}. Cannot proceed with financial analysis without risk assessment.")

                if composite_score is None:
                    self.logger.error(f"❌ CRITICAL: Missing composite_score for {ticker} - cannot make investment decisions without score")
                    raise ValueError(f"Missing required field 'composite_score' for {ticker}. Cannot proceed with financial analysis without composite score.")

                # Create HoldingProfile for AlternativeFinder
                holding_profile = HoldingProfile(
                    ticker=ticker,
                    name=name,
                    asset_class=asset_class,
                    grade=grade,
                    composite_score=composite_score,
                    risk_score=risk_score,
                    sector=sector,
                    expense_ratio=expense_ratio,
                )

                # Find alternatives using existing tool (Requirement 4.2)
                alternatives = alternative_finder.find_alternatives(holding=holding_profile, max_alternatives=max_alternatives)

                if alternatives:
                    # Convert Alternative objects to dictionaries for storage (Requirement 4.3)
                    alt_dicts = [alt.model_dump(mode="json") for alt in alternatives]
                    # Portfolio-Aware Opportunity Cascade: re-rank by fit to this
                    # underperformer's slot using the shared PortfolioFitScorer.
                    alt_dicts = self._rerank_by_slot_fit(ticker, alt_dicts)
                    alternatives_data[ticker] = alt_dicts
                    alternatives_count += len(alt_dicts)
                    self.logger.info(f"Found {len(alt_dicts)} alternatives for {ticker} (grade: {grade})")
                else:
                    # Requirement 4.4: Return empty list when no alternatives found
                    self.logger.info(f"No alternatives found for {ticker} (grade: {grade})")

            except Exception as e:
                self.logger.error(f"Alternative matching failed for {ticker}: {e}")
                continue

        self.logger.info(f"Alternative matching completed: {alternatives_count} alternatives for {len(alternatives_data)} holdings")

        return alternatives_data

    def _rerank_by_slot_fit(self, slot_ticker: str, alternatives: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Re-rank a holding's alternatives by portfolio fit to its freed slot.

        Defensive and flag-gated: when the ``portfolio_aware_discovery`` flag is
        off, the gap profile is empty, or alternative dicts lack a ``sector``,
        the input ordering is preserved (stable no-op).
        """
        try:
            from finwiz.config.features.flags import is_feature_enabled

            if not is_feature_enabled("portfolio_aware_discovery") or len(alternatives) < 2:
                return alternatives

            from finwiz.schemas.newcomer_discovery import PortfolioGapProfile
            from finwiz.scoring.discovery.portfolio_fit_scorer import PortfolioFitScorer

            profile = PortfolioGapProfile(**(self.state.portfolio_gap_profile or {}))
            if profile.is_empty:
                return alternatives

            slot_sector = next(
                (s.sector for s in profile.underperformer_slots if s.ticker.upper() == slot_ticker.upper()),
                None,
            )
            scorer = PortfolioFitScorer()

            def _fit(alt: dict[str, Any]) -> float:
                fit, _ = scorer.score_for_slot(profile, slot_sector, sector=alt.get("sector"))
                # None = no fit signal; treat as neutral for a stable sort.
                return 0.5 if fit is None else fit

            return sorted(alternatives, key=_fit, reverse=True)
        except Exception as e:
            self.logger.debug(f"Slot re-rank skipped for {slot_ticker}: {e}")
            return alternatives

    def match_alternatives_after_discovery(self, discovery_data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        """
        Match alternatives for underperforming holdings.

        Called from `run_sequential_workflow` after discovery crews complete, and
        matches alternatives for underperforming holdings using discovery results.

        Requirements: 4.1, 4.2, 4.3, 4.4

        Args:
            discovery_data: Discovery crew results (currently unused, for future enhancement)

        Returns:
            dict: Alternatives data keyed by ticker

        """
        self.logger.info("=" * 80)
        self.logger.info("Phase 4.5: Matching alternatives for underperforming holdings")
        self.logger.info("=" * 80)

        # Check if alternative matching is enabled
        enabled = (os.getenv("PORTFOLIO_ENABLE_ALTERNATIVES") or "true").strip().lower() in {"1", "true", "yes", "on"}
        if not enabled:
            self.logger.info("Alternative matching disabled via PORTFOLIO_ENABLE_ALTERNATIVES")
            return {}

        # Get deep analysis results from state
        deep_analysis_results = self.state.deep_analysis_results or {}

        if not deep_analysis_results:
            self.logger.warning("No deep analysis results available for alternative matching")
            return {}

        # Convert DeepAnalysisResult objects to dicts for processing
        holdings = []
        for ticker, analysis in deep_analysis_results.items():
            holding_dict = {
                "ticker": ticker,
                "grade": analysis.grade,
                "composite_score": analysis.composite_score,
                # risk_score is stored in DeepAnalysisResult, create nested risk object
                "risk": {"score": analysis.risk_score} if analysis.risk_score is not None else {},
                "name": getattr(analysis, "name", ticker),
                "asset_class": analysis.asset_class,
                # Sector and expense ratio drive the sector-match and cheaper-ETF
                # searches. Without them those two steps are blind and return
                # empty regardless of what the candidate universe holds.
                "sector": _extract_sector(analysis),
                "expense_ratio": _extract_expense_ratio(analysis),
            }
            holdings.append(holding_dict)

        # Match alternatives using the Python discovery output
        alternatives_data = self.match_alternatives_for_holdings(holdings, discovery_data)

        # Update structured Flow state
        self.state.portfolio_alternatives = alternatives_data
        self.state.alternatives_success = True
        self.state.alternatives_count = sum(len(alts) for alts in alternatives_data.values())

        self.logger.info(f"Alternative matching completed: {self.state.alternatives_count} alternatives found")
        self.logger.info("=" * 80)

        return alternatives_data
