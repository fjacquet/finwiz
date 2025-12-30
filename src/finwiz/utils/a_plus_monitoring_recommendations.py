"""
A+ monitoring recommendation and analysis functions.

Extracted from APlusMonitoringSystem for focused recommendation logic.
"""

from typing import TYPE_CHECKING, Any

from finwiz.tools.logger import get_logger

if TYPE_CHECKING:
    from finwiz.utils.a_plus_monitoring import MonitoredInvestment

logger = get_logger(__name__)


async def find_replacement_candidates(
    degraded_symbol: str,
    asset_type: str,
) -> list[str]:
    """
    Find replacement candidates for a degraded investment.

    Args:
        degraded_symbol: Symbol of the degraded investment
        asset_type: Type of asset (stock, etf, crypto)

    Returns:
        List of candidate symbols (excluding the degraded symbol)
    """
    # Mock implementation - in production, this would query the A+ discovery system
    candidates = []

    if asset_type == "etf":
        candidates = ["VOO", "VTI", "SPY", "IVV", "SCHX"]
    elif asset_type == "stock":
        candidates = ["MSFT", "GOOGL", "AMZN", "NVDA", "META"]
    elif asset_type == "crypto":
        candidates = ["BTC", "ETH", "SOL", "AVAX", "MATIC"]

    # Remove the degraded symbol from candidates
    return [c for c in candidates if c != degraded_symbol]


def analyze_degradation_factors(
    symbol: str,
    previous_score: float,
    current_score: float,
) -> list[str]:
    """
    Analyze factors contributing to grade degradation.

    Args:
        symbol: Investment symbol
        previous_score: Previous composite score
        current_score: Current composite score

    Returns:
        List of degradation factors
    """
    factors = []
    score_drop = previous_score - current_score

    if score_drop >= 0.15:
        factors.append("Significant fundamental deterioration")
    elif score_drop >= 0.05:
        factors.append("Moderate performance decline")

    # Add general factors
    factors.append(f"Score decreased by {score_drop:.2%}")

    return factors


def generate_recommended_actions(
    symbol: str,
    grade: str,
    degradation_factors: list[str],
) -> list[str]:
    """
    Generate recommended actions based on grade and degradation factors.

    Args:
        symbol: Investment symbol
        grade: Current grade
        degradation_factors: List of degradation factors

    Returns:
        List of recommended actions
    """
    actions = []

    if grade == "F":
        actions.append(f"Consider immediate exit from {symbol}")
        actions.append("Review portfolio allocation")
    elif grade == "D":
        actions.append(f"Consider position reduction in {symbol}")
        actions.append("Monitor closely for further degradation")
    elif grade in ["B+", "B", "B-"]:
        actions.append(f"Maintain position in {symbol} but monitor closely")
        actions.append("Review quarterly performance")
    else:
        actions.append(f"Continue monitoring {symbol}")

    return actions


def generate_performance_summary(
    monitored_investments: dict[str, "MonitoredInvestment"],
) -> dict[str, Any]:
    """
    Generate a performance summary for all monitored investments.

    Args:
        monitored_investments: Dict of monitored investments

    Returns:
        Dictionary containing performance metrics and statistics
    """
    if not monitored_investments:
        return {
            "total_investments": 0,
            "summary": "No investments currently monitored",
        }

    active_investments = [inv for inv in monitored_investments.values() if inv.is_active]

    # Count A+ investments
    a_plus_count = sum(
        1
        for inv in active_investments
        if (inv.current_grade.value if hasattr(inv.current_grade, "value") else str(inv.current_grade)) == "A+"
    )

    # Count degraded investments (grade lower than initial)
    degraded_count = sum(
        1
        for inv in active_investments
        if (inv.current_grade.value if hasattr(inv.current_grade, "value") else str(inv.current_grade))
        != (inv.initial_grade.value if hasattr(inv.initial_grade, "value") else str(inv.initial_grade))
    )

    # Calculate A+ percentage
    a_plus_percentage = (a_plus_count / len(active_investments) * 100) if active_investments else 0.0

    # Determine monitoring health
    if a_plus_percentage >= 80:
        monitoring_health = "excellent"
    elif a_plus_percentage >= 60:
        monitoring_health = "good"
    elif a_plus_percentage >= 40:
        monitoring_health = "needs_attention"
    else:
        monitoring_health = "poor"

    return {
        "total_investments": len(monitored_investments),
        "a_plus_count": a_plus_count,
        "degraded_count": degraded_count,
        "a_plus_percentage": a_plus_percentage,
        "monitoring_health": monitoring_health,
    }
