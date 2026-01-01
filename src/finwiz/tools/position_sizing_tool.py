"""
Position Sizing Tool - Calculate risk-adjusted position sizing recommendations.

This module calculates position sizes by:
- Applying risk-based sizing (high/medium/low risk)
- Calculating correlation with existing portfolio holdings
- Enforcing concentration limits (single stock, sector)
- Generating sizing actions (add/trim/hold/exit)
- Ensuring portfolio allocations sum to 100%
"""

from typing import Literal, cast

from pydantic import BaseModel, Field

from finwiz.schemas.portfolio_review import AssetClass, PositionSizeRecommendation
from finwiz.tools.logger import get_logger

# Type alias for sizing action
SizingAction = Literal["add", "trim", "hold", "exit"]

logger = get_logger(__name__)


class PortfolioContext(BaseModel):
    """Context about the current portfolio for sizing calculations."""

    total_holdings: int = Field(ge=1)
    current_allocations: dict[str, float] = Field(default_factory=dict)  # ticker -> % allocation
    sector_allocations: dict[str, float] = Field(default_factory=dict)  # sector -> % allocation
    asset_class_allocations: dict[str, float] = Field(default_factory=dict)  # asset_class -> %
    total_allocated_pct: float = Field(ge=0.0, le=100.0, default=100.0)


class HoldingSizingProfile(BaseModel):
    """Profile of a holding for position sizing."""

    ticker: str
    asset_class: AssetClass
    risk_score: float = Field(ge=0.0, le=5.0)
    sector: str | None = None
    current_allocation_pct: float = Field(ge=0.0, le=100.0, default=0.0)


class PositionSizingTool:
    """Calculate risk-adjusted position sizing recommendations."""

    def __init__(self) -> None:
        """Initialize the position sizing tool."""
        self.logger = logger

        # Concentration limits
        self.max_single_stock_pct = 10.0  # Maximum 10% in single stock
        self.max_sector_pct = 35.0  # Maximum 35% in single sector
        self.max_crypto_total_pct = 10.0  # Maximum 10% total in crypto

        # Risk-based sizing ranges
        self.risk_sizing_ranges = {
            "very_low": (5.0, 15.0),  # Risk 0-1: 5-15%
            "low": (4.0, 12.0),  # Risk 1-2: 4-12%
            "medium": (3.0, 8.0),  # Risk 2-3: 3-8%
            "high": (2.0, 5.0),  # Risk 3-4: 2-5%
            "very_high": (1.0, 3.0),  # Risk 4-5: 1-3%
        }

    def calculate_position_size(
        self,
        holding: HoldingSizingProfile,
        portfolio: PortfolioContext,
        risk_tolerance: str = "moderate",
    ) -> PositionSizeRecommendation:
        """
        Calculate optimal position size for a holding.

        Args:
            holding: Profile of the holding
            portfolio: Current portfolio context
            risk_tolerance: User risk tolerance (conservative/moderate/aggressive)

        Returns:
            PositionSizeRecommendation with sizing action

        """
        self.logger.info(
            "Calculating position size",
            extra={
                "ticker": holding.ticker,
                "risk_score": holding.risk_score,
                "current_allocation": holding.current_allocation_pct,
            },
        )

        # Step 1: Calculate base recommended size based on risk
        base_size = self._calculate_base_size(
            risk_score=holding.risk_score,
            risk_tolerance=risk_tolerance,
        )

        # Step 2: Apply concentration limits
        size_after_limits = self._apply_concentration_limits(
            base_size=base_size,
            holding=holding,
            portfolio=portfolio,
        )

        # Step 3: Calculate correlation impact (simplified)
        correlation = self._estimate_correlation(holding, portfolio)

        # Step 4: Adjust for portfolio balance
        recommended_size = self._adjust_for_portfolio_balance(
            size=size_after_limits,
            holding=holding,
            portfolio=portfolio,
        )

        # Step 5: Determine sizing action
        sizing_action = self._determine_sizing_action(
            current_size=holding.current_allocation_pct,
            recommended_size=recommended_size,
        )

        # Step 6: Calculate risk contribution
        risk_contribution = self._calculate_risk_contribution(
            size=recommended_size,
            risk_score=holding.risk_score,
            portfolio=portfolio,
        )

        # Step 7: Generate rationale
        rationale = self._generate_rationale(
            holding=holding,
            base_size=base_size,
            recommended_size=recommended_size,
            sizing_action=sizing_action,
            risk_tolerance=risk_tolerance,
        )

        # Check if limits were applied
        concentration_limits_applied = size_after_limits < base_size
        risk_limits_applied = base_size < self._get_max_size_for_risk(holding.risk_score)

        return PositionSizeRecommendation(
            current_size_pct=holding.current_allocation_pct,
            recommended_size_pct=recommended_size,
            sizing_action=cast(SizingAction, sizing_action),
            sizing_rationale=rationale,
            risk_contribution=risk_contribution,
            correlation_with_portfolio=correlation,
            concentration_limits_applied=concentration_limits_applied,
            risk_limits_applied=risk_limits_applied,
        )

    def _calculate_base_size(
        self,
        risk_score: float,
        risk_tolerance: str,
    ) -> float:
        """Calculate base position size based on risk score."""
        # Determine risk category
        if risk_score < 1.0:
            risk_category = "very_low"
        elif risk_score < 2.0:
            risk_category = "low"
        elif risk_score < 3.0:
            risk_category = "medium"
        elif risk_score < 4.0:
            risk_category = "high"
        else:
            risk_category = "very_high"

        # Get sizing range for risk category
        min_size, max_size = self.risk_sizing_ranges[risk_category]

        # Adjust based on risk tolerance
        if risk_tolerance == "conservative":
            # Use lower end of range
            base_size = min_size + (max_size - min_size) * 0.3
        elif risk_tolerance == "aggressive":
            # Use upper end of range
            base_size = min_size + (max_size - min_size) * 0.7
        else:  # moderate
            # Use middle of range
            base_size = (min_size + max_size) / 2

        return round(base_size, 2)

    def _apply_concentration_limits(
        self,
        base_size: float,
        holding: HoldingSizingProfile,
        portfolio: PortfolioContext,
    ) -> float:
        """Apply concentration limits to position size."""
        size = base_size

        # Limit 1: Single stock maximum
        if holding.asset_class == "stock":
            size = min(size, self.max_single_stock_pct)

        # Limit 2: Sector concentration
        if holding.sector:
            current_sector_allocation = portfolio.sector_allocations.get(holding.sector, 0.0)
            # Don't let this holding push sector over limit
            max_additional = self.max_sector_pct - current_sector_allocation
            size = min(size, max_additional)

        # Limit 3: Crypto total concentration
        if holding.asset_class == "crypto":
            current_crypto_allocation = portfolio.asset_class_allocations.get("crypto", 0.0)
            max_additional = self.max_crypto_total_pct - current_crypto_allocation
            size = min(size, max_additional)

        # Ensure non-negative
        size = max(size, 0.0)

        return round(size, 2)

    def _estimate_correlation(
        self,
        holding: HoldingSizingProfile,
        portfolio: PortfolioContext,
    ) -> float:
        """
        Estimate correlation with existing portfolio.

        Simplified estimation based on asset class and sector.
        In production, would use actual price correlation.
        """
        # Base correlation by asset class
        if holding.asset_class == "stock":
            base_correlation = 0.6  # Stocks generally correlated
        elif holding.asset_class == "etf":
            base_correlation = 0.7  # ETFs highly correlated with market
        else:  # crypto
            base_correlation = 0.3  # Crypto less correlated

        # Adjust for sector concentration
        if holding.sector:
            sector_allocation = portfolio.sector_allocations.get(holding.sector, 0.0)
            if sector_allocation > 20.0:
                # High sector concentration increases correlation
                base_correlation += 0.2

        # Cap at 1.0
        return min(base_correlation, 1.0)

    def _adjust_for_portfolio_balance(
        self,
        size: float,
        holding: HoldingSizingProfile,
        portfolio: PortfolioContext,
    ) -> float:
        """Adjust size to maintain portfolio balance."""
        # If portfolio is over-allocated, reduce size
        if portfolio.total_allocated_pct > 100.0:
            reduction_factor = 100.0 / portfolio.total_allocated_pct
            size = size * reduction_factor

        # Ensure we don't exceed 100% total
        available_space = 100.0 - portfolio.total_allocated_pct + holding.current_allocation_pct
        size = min(size, available_space)

        return round(size, 2)

    def _determine_sizing_action(
        self,
        current_size: float,
        recommended_size: float,
    ) -> str:
        """Determine sizing action based on current vs recommended."""
        diff = recommended_size - current_size

        if abs(diff) < 0.5:
            # Within 0.5%, hold
            return "hold"
        elif diff > 0:
            # Recommended size is higher
            if recommended_size == 0.0:
                return "exit"
            else:
                return "add"
        else:
            # Recommended size is lower
            if recommended_size == 0.0:
                return "exit"
            else:
                return "trim"

    def _calculate_risk_contribution(
        self,
        size: float,
        risk_score: float,
        portfolio: PortfolioContext,
    ) -> float:
        """Calculate this holding's contribution to portfolio risk."""
        # Simplified: risk contribution = size * risk_score
        # In production, would use covariance matrix
        risk_contribution = (size / 100.0) * risk_score

        # Normalize to percentage of total portfolio risk
        # Assume average portfolio risk score of 2.5
        avg_portfolio_risk = 2.5
        total_portfolio_risk = avg_portfolio_risk * (portfolio.total_allocated_pct / 100.0)

        if total_portfolio_risk > 0:
            risk_contribution_pct = (risk_contribution / total_portfolio_risk) * 100.0
        else:
            risk_contribution_pct = 0.0

        return round(min(risk_contribution_pct, 100.0), 2)

    def _get_max_size_for_risk(self, risk_score: float) -> float:
        """Get maximum size for a given risk score."""
        if risk_score < 1.0:
            return 15.0
        elif risk_score < 2.0:
            return 12.0
        elif risk_score < 3.0:
            return 8.0
        elif risk_score < 4.0:
            return 5.0
        else:
            return 3.0

    def _generate_rationale(
        self,
        holding: HoldingSizingProfile,
        base_size: float,
        recommended_size: float,
        sizing_action: str,
        risk_tolerance: str,
    ) -> str:
        """Generate French rationale for sizing recommendation."""
        risk_level = self._get_risk_level_french(holding.risk_score)

        if sizing_action == "hold":
            return f"Position actuelle de {holding.current_allocation_pct:.1f}% appropriée. Risque {risk_level} (score {holding.risk_score:.1f}). Maintenir l'allocation actuelle."
        elif sizing_action == "add":
            diff = recommended_size - holding.current_allocation_pct
            return (
                f"Augmenter la position de {holding.current_allocation_pct:.1f}% à {recommended_size:.1f}% "
                f"(+{diff:.1f}%). Risque {risk_level} (score {holding.risk_score:.1f}). "
                f"Profil de risque {risk_tolerance} permet cette allocation."
            )
        elif sizing_action == "trim":
            diff = holding.current_allocation_pct - recommended_size
            return (
                f"Réduire la position de {holding.current_allocation_pct:.1f}% à {recommended_size:.1f}% "
                f"(-{diff:.1f}%). Risque {risk_level} (score {holding.risk_score:.1f}). "
                f"Position actuelle trop importante pour le profil de risque."
            )
        else:  # exit
            return (
                f"Sortir de la position (actuellement {holding.current_allocation_pct:.1f}%). "
                f"Risque {risk_level} (score {holding.risk_score:.1f}) trop élevé ou "
                f"limites de concentration dépassées."
            )

    def _get_risk_level_french(self, risk_score: float) -> str:
        """Get French risk level description."""
        if risk_score < 1.0:
            return "très faible"
        elif risk_score < 2.0:
            return "faible"
        elif risk_score < 3.0:
            return "modéré"
        elif risk_score < 4.0:
            return "élevé"
        else:
            return "très élevé"

    def validate_portfolio_allocations(
        self,
        holdings: list[HoldingSizingProfile],
        recommendations: list[PositionSizeRecommendation],
    ) -> tuple[bool, float, str]:
        """
        Validate that recommended allocations sum to 100%.

        Args:
            holdings: List of holdings
            recommendations: List of sizing recommendations

        Returns:
            Tuple of (is_valid, total_pct, message)

        """
        total_recommended = sum(rec.recommended_size_pct for rec in recommendations)

        is_valid = abs(total_recommended - 100.0) < 1.0  # Allow 1% tolerance

        if is_valid:
            message = f"Allocations valides: {total_recommended:.1f}% (cible 100%)"
        else:
            message = f"Allocations invalides: {total_recommended:.1f}% (cible 100%)"

        return is_valid, total_recommended, message
