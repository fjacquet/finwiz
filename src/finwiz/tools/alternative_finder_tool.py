"""
Alternative Finder Tool - Find better alternatives for underperforming holdings.

This module finds alternatives by:
- Matching sector/exposure for similar holdings
- Prioritizing A+ candidates from discovery crew
- Comparing key metrics (expense ratios, fundamentals, liquidity)
- Generating transition strategies (immediate/gradual/tax-optimized)
- Calculating expected grade improvements
"""

import json
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, Field

from finwiz.schemas.portfolio_review import Alternative, AssetClass, Grade
from finwiz.tools.logger import get_logger

# Type alias for swap timing
SwapTiming = Literal["immediate", "gradual", "tax_optimized"]

logger = get_logger(__name__)

# Grades eligible for "A-band" alternative sourcing from consolidated_discovery.json's
# flat `opportunities` list. Matches the top two tiers of the Grade vocabulary that
# finwiz.scoring.grading_system.score_to_grade actually emits (A+, A, B+, B, C+, C, D, F
# — the sole grader behind discovery opportunities; see finwiz.discovery.candidate_scorer).
# Broader than "A+ only" so this isn't perpetually empty: A+ alone requires a >=95%
# composite score, which is rare in practice.
_A_BAND_GRADES: frozenset[str] = frozenset({"A+", "A"})


class HoldingProfile(BaseModel):
    """Profile of a holding for matching alternatives."""

    ticker: str
    name: str
    asset_class: AssetClass
    grade: Grade
    composite_score: float = Field(ge=0.0, le=1.0)
    sector: str | None = None
    expense_ratio: float | None = None  # For ETFs
    market_cap: float | None = None  # For stocks/crypto
    risk_score: float = Field(ge=0.0, le=5.0, default=2.5)


class AlternativeFinder:
    """Find better alternatives for underperforming holdings."""

    def __init__(self, output_dir: Path = Path("output")) -> None:
        """
        Initialize the alternative finder.

        Args:
            output_dir: Base output directory for crew outputs

        """
        self.output_dir = output_dir
        self.discovery_output_dir = output_dir / "discovery"
        self.logger = logger

        # Grade hierarchy for comparison
        self.grade_values = {
            "A+": 10,
            "A": 9,
            "B+": 8,
            "B": 7,
            "C+": 6,
            "C": 5,
            "D": 4,
            "F": 3,
        }

    def find_alternatives(
        self,
        holding: HoldingProfile,
        max_alternatives: int = 3,
    ) -> list[Alternative]:
        """
        Find better alternatives for a holding.

        Prioritizes:
        1. A+ candidates from discovery crew
        2. Same sector/exposure with better metrics
        3. Lower cost alternatives (ETFs)

        Args:
            holding: Profile of the current holding
            max_alternatives: Maximum number of alternatives to return

        Returns:
            List of Alternative objects

        """
        self.logger.info(
            "Finding alternatives",
            extra={
                "ticker": holding.ticker,
                "grade": holding.grade,
                "asset_class": holding.asset_class,
            },
        )

        # Only find alternatives for holdings graded below B
        if self.grade_values.get(holding.grade, 0) >= self.grade_values["B"]:
            self.logger.info(
                "Holding grade is B or above, no alternatives needed",
                extra={"ticker": holding.ticker, "grade": holding.grade},
            )
            return []

        alternatives = []

        # Step 1: Check A+ discovery crew outputs
        self.logger.info(f"Step 1: Searching for A+ alternatives for {holding.ticker} (grade: {holding.grade})")
        aplus_alternatives = self._find_aplus_alternatives(holding)
        if aplus_alternatives:
            self.logger.info(f"Found {len(aplus_alternatives)} A+ alternatives for {holding.ticker}")
            alternatives.extend(aplus_alternatives)
        else:
            self.logger.warning(
                f"No A+ alternatives found for {holding.ticker} from discovery crew. Check if discovery crew has run and generated A+ candidates for {holding.asset_class}."
            )

        # Step 2: Find same-sector alternatives (if not enough A+ found)
        if len(alternatives) < max_alternatives:
            self.logger.info(f"Step 2: Searching for sector alternatives for {holding.ticker} (need {max_alternatives - len(alternatives)} more)")
            sector_alternatives = self._find_sector_alternatives(holding)
            if sector_alternatives:
                self.logger.info(f"Found {len(sector_alternatives)} sector alternatives for {holding.ticker}")
                alternatives.extend(sector_alternatives)
            else:
                self.logger.info(f"No sector alternatives found for {holding.ticker} (feature not yet implemented)")

        # Step 3: Find lower-cost alternatives for ETFs
        if holding.asset_class == "etf" and len(alternatives) < max_alternatives:
            self.logger.info(f"Step 3: Searching for lower-cost ETF alternatives for {holding.ticker}")
            cost_alternatives = self._find_lower_cost_etf_alternatives(holding)
            if cost_alternatives:
                self.logger.info(f"Found {len(cost_alternatives)} lower-cost alternatives for {holding.ticker}")
                alternatives.extend(cost_alternatives)
            else:
                self.logger.info(f"No lower-cost alternatives found for {holding.ticker} (feature not yet implemented)")

        # Remove duplicates and limit to max
        seen_tickers = set()
        unique_alternatives = []
        for alt in alternatives:
            if alt.ticker not in seen_tickers:
                seen_tickers.add(alt.ticker)
                unique_alternatives.append(alt)
                if len(unique_alternatives) >= max_alternatives:
                    break

        # Log final result with detailed information
        if unique_alternatives:
            self.logger.info(
                f"✅ Found {len(unique_alternatives)} alternatives for {holding.ticker}",
                extra={
                    "ticker": holding.ticker,
                    "grade": holding.grade,
                    "alternatives_count": len(unique_alternatives),
                    "alternatives": [alt.ticker for alt in unique_alternatives],
                },
            )
        else:
            self.logger.warning(
                f"⚠️ No alternatives found for {holding.ticker} (grade: {holding.grade}). "
                f"Possible reasons: no A+ candidates match this asset class in the current "
                f"discovery output, or sector/cost matching has no eligible pairs.",
                extra={
                    "ticker": holding.ticker,
                    "grade": holding.grade,
                    "asset_class": holding.asset_class,
                },
            )

        return unique_alternatives

    def _find_aplus_alternatives(self, holding: HoldingProfile) -> list[Alternative]:
        """Find A-band alternatives from the consolidated discovery output.

        ``consolidated_discovery.json`` is the only file the discovery pipeline
        actually writes (see ``discovery_orchestrator.py``). It holds a flat
        ``opportunities`` list spanning every asset class and every grade —
        unlike the array this reader used to look for, nothing pre-filters it
        to A-band candidates, so filtering by asset class and grade happens here.
        """
        alternatives = []

        discovery_file = self.discovery_output_dir / "consolidated_discovery.json"
        if not discovery_file.exists():
            self.logger.warning(f"No discovery output found at {discovery_file}; A-band alternatives unavailable for this run.")
            return alternatives

        try:
            with open(discovery_file) as f:
                discovery_data = json.load(f)

            opportunities = discovery_data.get("opportunities", [])
            if not opportunities:
                self.logger.warning(f"Discovery output exists but has no opportunities. File: {discovery_file}")
                return alternatives

            aplus_items = [item for item in opportunities if isinstance(item, dict) and item.get("asset_class") == holding.asset_class and item.get("grade") in _A_BAND_GRADES]

            if not aplus_items:
                self.logger.info(f"No A-band {holding.asset_class}s found in discovery output for {holding.ticker}.")
                return alternatives

            self.logger.info(f"Found {len(aplus_items)} A-band {holding.asset_class}s in discovery output, filtering for alternatives to {holding.ticker}")

            for item in aplus_items:
                ticker = item.get("ticker", "")
                if ticker and ticker != holding.ticker:
                    alternative = self._create_alternative_from_aplus(
                        item=item,
                        holding=holding,
                    )
                    if alternative:
                        alternatives.append(alternative)
                        self.logger.info(f"Created alternative: {ticker} (grade: {item.get('grade', 'N/A')}) for {holding.ticker}")
                elif ticker == holding.ticker:
                    self.logger.debug(f"Skipping {ticker} as it's the same as current holding")

            if not alternatives:
                self.logger.warning(
                    f"Found {len(aplus_items)} A-band {holding.asset_class}s but none are suitable alternatives for {holding.ticker} (all may be the same ticker or failed validation)"
                )

        except Exception as e:
            self.logger.error(
                f"Error reading discovery output from {discovery_file}: {e}",
                extra={"error": str(e), "file": str(discovery_file)},
                exc_info=True,
            )

        return alternatives

    def _create_alternative_from_aplus(
        self,
        item: dict,
        holding: HoldingProfile,
    ) -> Alternative | None:
        """Create Alternative object from A+ discovery item."""
        from finwiz.exceptions.data_quality import MissingRequiredFieldError

        try:
            ticker = item.get("ticker", "")
            name = item.get("name", ticker)

            # NO DEFAULTS - require explicit values
            if "composite_score" not in item or item["composite_score"] is None:
                raise MissingRequiredFieldError(ticker=ticker, field="composite_score", context={"source": "aplus_discovery", "item_keys": list(item.keys())})

            if "grade" not in item or item["grade"] is None:
                raise MissingRequiredFieldError(ticker=ticker, field="grade", context={"source": "aplus_discovery", "item_keys": list(item.keys())})

            composite_score = float(item["composite_score"])
            grade = cast(Grade, str(item["grade"]))

            # Calculate expected improvement
            current_grade_value = self.grade_values.get(holding.grade, 5)
            alternative_grade_value = self.grade_values.get(grade, 10)
            grade_improvement = alternative_grade_value - current_grade_value

            # Determine swap timing based on grade difference
            swap_timing: SwapTiming
            if grade_improvement >= 4:  # e.g., D to A+
                swap_timing = "immediate"
            elif grade_improvement >= 2:  # e.g., C to A
                swap_timing = "gradual"
            else:
                swap_timing = "tax_optimized"

            # Create transition strategy
            transition_strategy = self._create_transition_strategy(
                current_ticker=holding.ticker,
                alternative_ticker=ticker,
                swap_timing=swap_timing,
                grade_improvement=grade_improvement,
            )

            # Tax implications
            tax_implications = self._create_tax_implications(swap_timing)

            # Comparison metrics
            expense_ratio_savings = None
            fundamental_improvement = None
            liquidity_improvement = None

            if holding.asset_class == "etf":
                # Calculate expense ratio savings
                current_expense = holding.expense_ratio or 0.50
                alternative_expense = item.get("expense_ratio", 0.10)
                expense_ratio_savings = current_expense - alternative_expense

            elif holding.asset_class == "stock":
                # Fundamental improvements
                fundamental_improvement = {
                    "grade_improvement": grade_improvement,
                    "score_improvement": composite_score - holding.composite_score,
                }

            elif holding.asset_class == "crypto":
                # Liquidity improvement (if available)
                current_market_cap = holding.market_cap or 1000000
                alternative_market_cap = item.get("market_cap", 10000000)
                liquidity_improvement = (alternative_market_cap - current_market_cap) / current_market_cap

            return Alternative(
                ticker=ticker,
                name=name,
                asset_class=holding.asset_class,
                composite_score=composite_score,
                grade=grade,
                grade_description=self._get_grade_description(grade),
                recommended_action=self._get_recommended_action(grade),
                risk_score_standardized=item.get("risk_score", 2.0),
                key_metrics=item.get("key_metrics", {}),
                thesis_bullets=item.get("thesis_bullets", []),
                citations=item.get("citations", ["Discovery Crew A+ Analysis"]),
                is_a_plus_candidate=True,
                discovery_source="investment_discovery_crew",
                confidence_level=item.get("confidence_level", 0.85),
                expected_annual_benefit=item.get("expected_annual_benefit"),
                transition_strategy=transition_strategy,
                swap_timing=swap_timing,
                tax_implications=tax_implications,
                expense_ratio_savings=expense_ratio_savings,
                fundamental_improvement=fundamental_improvement,
                liquidity_improvement=liquidity_improvement,
            )

        except Exception as e:
            self.logger.error(
                "Error creating alternative from A+ item",
                extra={"ticker": item.get("ticker"), "error": str(e)},
            )
            return None

    def _find_sector_alternatives(self, holding: HoldingProfile) -> list[Alternative]:
        """Find alternatives in the same sector (placeholder for future implementation)."""
        # This would integrate with sector/industry databases
        # For now, return empty list
        self.logger.info(
            "Sector matching not yet implemented",
            extra={"ticker": holding.ticker},
        )
        return []

    def _find_lower_cost_etf_alternatives(self, holding: HoldingProfile) -> list[Alternative]:
        """Find lower-cost ETF alternatives (placeholder for future implementation)."""
        # This would integrate with ETF databases to find similar exposure with lower fees
        # For now, return empty list
        self.logger.info(
            "ETF cost comparison not yet implemented",
            extra={"ticker": holding.ticker},
        )
        return []

    def _create_transition_strategy(
        self,
        current_ticker: str,
        alternative_ticker: str,
        swap_timing: str,
        grade_improvement: int,
    ) -> str:
        """Create transition strategy description in French."""
        if swap_timing == "immediate":
            return (
                f"Remplacer {current_ticker} par {alternative_ticker} immédiatement. "
                f"L'amélioration de note significative ({grade_improvement} niveaux) justifie une action rapide. "
                f"Vendre {current_ticker} et acheter {alternative_ticker} dans la même session."
            )
        elif swap_timing == "gradual":
            return (
                f"Transition progressive de {current_ticker} vers {alternative_ticker}. "
                f"Vendre 50% de {current_ticker} et acheter {alternative_ticker}, "
                f"puis compléter la transition sur 2-3 mois. "
                f"Permet de moyenner les prix d'entrée/sortie."
            )
        else:  # tax_optimized
            return (
                f"Transition optimisée fiscalement de {current_ticker} vers {alternative_ticker}. "
                f"Attendre une période fiscale favorable ou utiliser des pertes fiscales. "
                f"Transition sur 6-12 mois pour minimiser l'impact fiscal."
            )

    def _create_tax_implications(self, swap_timing: str) -> str:
        """Create tax implications description in French."""
        if swap_timing == "immediate":
            return "Réalisation immédiate des gains/pertes en capital. Considérer l'impact fiscal avant d'exécuter. Peut être avantageux si position en perte."
        elif swap_timing == "gradual":
            return "Réalisation progressive des gains/pertes. Impact fiscal étalé sur plusieurs périodes. Permet une meilleure planification fiscale."
        else:  # tax_optimized
            return (
                "Stratégie optimisée pour minimiser l'impôt. "
                "Attendre période fiscale favorable (nouvelle année, compensation pertes). "
                "Peut utiliser comptes fiscalement avantageux (PEA, assurance-vie)."
            )

    def _get_grade_description(self, grade: Grade) -> str:
        """Get French description for grade."""
        descriptions = {
            "A+": "Excellent - Opportunité exceptionnelle",
            "A": "Très bon - Fortement recommandé",
            "B+": "Bon - Recommandé",
            "B": "Satisfaisant - Acceptable",
            "C+": "Moyen - À surveiller",
            "C": "Passable - Minimum acceptable",
            "D": "Insuffisant - À améliorer rapidement",
            "F": "Très insuffisant - À remplacer",
        }
        return descriptions.get(grade, "Non évalué")

    def _get_recommended_action(self, grade: Grade) -> str:
        """Get French recommended action for grade."""
        actions = {
            "A+": "Acheter et renforcer",
            "A": "Acheter",
            "B+": "Conserver et surveiller",
            "B": "Conserver",
            "C+": "Surveiller de près",
            "C": "Maintenez mais ne renforcez pas",
            "D": "Réduisez progressivement la position",
            "F": "Vendez rapidement",
        }
        return actions.get(grade, "Évaluer")

    def compare_holdings(
        self,
        current: HoldingProfile,
        alternative: HoldingProfile,
    ) -> dict[str, Any]:
        """
        Compare two holdings and return comparison metrics.

        Args:
            current: Current holding profile
            alternative: Alternative holding profile

        Returns:
            Dictionary with comparison metrics

        """
        comparison = {
            "grade_improvement": self.grade_values.get(alternative.grade, 5) - self.grade_values.get(current.grade, 5),
            "score_improvement": alternative.composite_score - current.composite_score,
            "risk_change": alternative.risk_score - current.risk_score,
        }

        # Asset-specific comparisons
        if current.asset_class == "etf" and alternative.asset_class == "etf":
            if current.expense_ratio and alternative.expense_ratio:
                comparison["expense_ratio_savings"] = current.expense_ratio - alternative.expense_ratio

        elif current.asset_class == "stock" and alternative.asset_class == "stock":
            if current.market_cap and alternative.market_cap:
                comparison["market_cap_ratio"] = alternative.market_cap / current.market_cap

        return comparison
