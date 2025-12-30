"""
A+ monitoring market regime tracking functions.

Extracted from APlusMonitoringSystem for focused regime management.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from finwiz.tools.logger import get_logger

if TYPE_CHECKING:
    from finwiz.schemas.investment_discovery import MarketRegime

logger = get_logger(__name__)


async def assess_regime_impact(
    previous_regime: "MarketRegime",
    new_regime: "MarketRegime",
    monitored_investments_count: int,
) -> dict[str, Any]:
    """
    Assess the impact of market regime change on A+ investments.

    Args:
        previous_regime: Previous market regime
        new_regime: New market regime
        monitored_investments_count: Number of monitored investments

    Returns:
        Impact assessment dictionary
    """
    # Simplified impact assessment
    impact_level = "medium"

    # High impact transitions (compare regime_type strings)
    if (previous_regime.regime_type == "bull" and new_regime.regime_type == "bear") or (
        previous_regime.market_stress_level == "low" and new_regime.market_stress_level == "high"
    ):
        impact_level = "high"

    return {
        "impact_level": impact_level,
        "affected_investments": monitored_investments_count,
        "recommended_action": "Review all A+ positions for regime-specific risks",
        "assessment_timestamp": datetime.now(),
    }


def detect_significant_regime_change(
    old_regime: "MarketRegime",
    new_regime: "MarketRegime",
) -> bool:
    """
    Detect if a market regime change is significant enough to trigger alerts.

    Args:
        old_regime: Previous market regime
        new_regime: New market regime

    Returns:
        True if change is significant
    """
    # Check regime type change
    if old_regime.regime_type != new_regime.regime_type:
        return True

    # Check stress level change
    if old_regime.market_stress_level != new_regime.market_stress_level:
        return True

    # Check VIX level change (>=10 point swing)
    if abs(old_regime.vix_level - new_regime.vix_level) >= 10.0:
        return True

    return False
