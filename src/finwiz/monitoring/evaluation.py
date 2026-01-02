"""
A+ investment evaluation functions.

Extracted from APlusMonitoringSystem for focused evaluation logic.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from finwiz.schemas.investment_discovery import APlusAnalysis, InvestmentCandidate
from finwiz.tools.logger import get_logger
from finwiz.utils.grading_system import score_to_grade

if TYPE_CHECKING:
    from finwiz.tools.a_plus_scoring_tool import APlusScoringTool
    from finwiz.utils.a_plus_monitoring import MonitoredInvestment

logger = get_logger(__name__)


async def evaluate_single_investment(
    symbol: str,
    monitored_inv: "MonitoredInvestment",
    scoring_tool: "APlusScoringTool",
    reevaluation_interval_hours: int,
    force_evaluation: bool = False,
) -> APlusAnalysis | None:
    """
    Evaluate a single investment and return analysis.

    Args:
        symbol: Investment symbol to evaluate
        monitored_inv: Monitored investment tracking object
        scoring_tool: A+ scoring tool instance
        reevaluation_interval_hours: Hours between evaluations
        force_evaluation: If True, evaluate regardless of last evaluation time

    Returns:
        APlusAnalysis if evaluation was performed, None if skipped
    """
    # Check if evaluation is due
    if not force_evaluation:
        time_since_eval = (datetime.now() - monitored_inv.last_evaluated).total_seconds() / 3600
        if time_since_eval < reevaluation_interval_hours:
            logger.debug(f"Skipping evaluation for {symbol} - not due yet")
            return None

    try:
        # Use the scoring tool to get new analysis
        result = scoring_tool._run(symbol)

        # Convert to APlusAnalysis
        candidate = InvestmentCandidate(
            symbol=result["symbol"],
            name=result.get("name", result["symbol"]),
            asset_type=monitored_inv.asset_type,
            current_price=result.get("current_price", 100.0),
            preliminary_score=result["composite_score"],
            final_score=result["composite_score"],
            grade=result["grade"],
            grade_description=f"Grade {result['grade']}",
            recommended_action="Monitor",
            data_source="scoring_tool",
        )

        analysis_summary = result.get("analysis_summary", {})
        component_scores = analysis_summary.get("component_scores", {})

        return APlusAnalysis(
            candidate=candidate,
            fundamental_score=component_scores.get("fundamental", 0.8),
            technical_score=component_scores.get("technical", 0.8),
            quality_score=component_scores.get("quality", 0.8),
            risk_score=component_scores.get("risk", 0.8),
            composite_score=result["composite_score"],
            confidence_level=analysis_summary.get("confidence", 0.8),
            is_a_plus_candidate=result.get("is_a_plus_candidate", False),
            rationale=analysis_summary.get("top_strengths", []),
        )

    except Exception as e:
        import traceback

        logger.error(f"Error evaluating {symbol}: {e}\n{traceback.format_exc()}")
        return None


async def check_grade_for_investment(
    symbol: str,
    monitored_inv: "MonitoredInvestment",
    scoring_tool: "APlusScoringTool",
) -> tuple[Any | None, APlusAnalysis | None]:
    """
    Check current grade for a monitored investment.

    Args:
        symbol: Investment symbol
        monitored_inv: Monitored investment tracking object
        scoring_tool: A+ scoring tool instance

    Returns:
        Tuple of (new_grade, new_analysis) or (None, None) on error
    """
    try:
        # Re-evaluate the investment
        new_analysis = await scoring_tool.analyze_investment(symbol, monitored_inv.asset_type)
        grade_info = score_to_grade(new_analysis.composite_score)
        new_grade = grade_info.grade

        return new_grade, new_analysis

    except Exception as e:
        logger.error(f"Error checking grade for {symbol}: {e}")
        return None, None


def determine_alert_severity(
    previous_grade: str,
    current_grade: str,
    previous_score: float,
    current_score: float,
) -> Any:
    """
    Determine the severity of a grade degradation alert.

    Args:
        previous_grade: Previous letter grade
        current_grade: Current letter grade
        previous_score: Previous composite score
        current_score: Current composite score

    Returns:
        AlertSeverity level
    """
    from finwiz.utils.monitoring_alerts import AlertSeverity

    # Grade value mapping
    grade_values = {"A+": 4, "A": 3, "B+": 2, "B": 1, "C+": 0.5, "C": 0, "D": -1, "F": -2}

    prev_value = grade_values.get(previous_grade, 0)
    curr_value = grade_values.get(current_grade, 0)
    grade_drop = prev_value - curr_value

    # Score drop
    score_drop = previous_score - current_score

    # Critical: A+ to B+ or worse, or massive score drop
    if (previous_grade == "A+" and grade_drop >= 2) or score_drop > 0.10:
        return AlertSeverity.CRITICAL

    # High: A+ to A, or large score drop with grade change
    if (previous_grade == "A+" and grade_drop >= 1) or (grade_drop > 0 and score_drop > 0.05):
        return AlertSeverity.HIGH

    # Medium: Moderate score drop (same grade or minor grade change)
    if score_drop > 0.05 or (grade_drop > 0 and score_drop > 0.02):
        return AlertSeverity.MEDIUM

    # Low: Minor changes
    return AlertSeverity.LOW
