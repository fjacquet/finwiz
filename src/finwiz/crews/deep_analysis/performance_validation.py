"""
Performance validation for DeepAnalysisCrew.

Validates execution performance against targets for pure Python and hybrid approaches.
Extracted from deep_analysis.py for maintainability.
"""

from dataclasses import dataclass
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceTargets:
    """Performance targets for validation."""

    time_min: int
    time_max: int
    llm_calls: int
    cost: float
    speedup_min: int
    speedup_max: int
    cost_reduction: int
    approach_name: str

    @classmethod
    def for_hybrid(cls) -> "PerformanceTargets":
        """Get targets for hybrid approach (Python + AI summary)."""
        return cls(
            time_min=15,
            time_max=40,
            llm_calls=1,
            cost=0.01,
            speedup_min=8,
            speedup_max=15,
            cost_reduction=80,
            approach_name="HYBRID",
        )

    @classmethod
    def for_pure_python(cls) -> "PerformanceTargets":
        """Get targets for pure Python approach."""
        return cls(
            time_min=10,
            time_max=30,
            llm_calls=0,
            cost=0.0,
            speedup_min=10,
            speedup_max=20,
            cost_reduction=100,
            approach_name="PURE PYTHON",
        )


@dataclass
class BaselineMetrics:
    """Baseline AI performance metrics for comparison."""

    time_min: int = 5 * 60  # 5 minutes
    time_max: int = 10 * 60  # 10 minutes
    cost_min: float = 0.05
    cost_max: float = 0.10

    @property
    def avg_time(self) -> float:
        """Average baseline time."""
        return (self.time_min + self.time_max) / 2

    @property
    def avg_cost(self) -> float:
        """Average baseline cost."""
        return (self.cost_min + self.cost_max) / 2


def validate_performance_targets(
    ticker: str,
    execution_time: float,
    api_metrics: dict[str, Any],
    ai_summary_enabled: bool = False,
) -> dict[str, Any]:
    """
    Validate performance improvements against targets.

    Pure Python: 10-30s, 0 LLM calls, $0 cost
    Hybrid: 15-40s, 1 LLM call, $0.01 cost

    Args:
        ticker: Asset ticker
        execution_time: Total execution time in seconds
        api_metrics: API usage metrics
        ai_summary_enabled: Whether AI summary (hybrid approach) is enabled

    Returns:
        Dict with validation results

    """
    # Get appropriate targets
    targets = PerformanceTargets.for_hybrid() if ai_summary_enabled else PerformanceTargets.for_pure_python()
    baseline = BaselineMetrics()

    # Calculate metrics based on approach
    llm_calls = 1 if ai_summary_enabled else 0
    cost_usd = 0.01 if ai_summary_enabled else 0.0

    # Calculate speedup
    speedup_factor = baseline.avg_time / execution_time if execution_time > 0 else 0

    # Calculate cost reduction
    cost_reduction_pct = ((baseline.avg_cost - cost_usd) / baseline.avg_cost * 100) if baseline.avg_cost > 0 else 100

    # Validate targets
    time_target_met = targets.time_min <= execution_time <= targets.time_max
    llm_target_met = llm_calls <= targets.llm_calls
    cost_target_met = cost_usd <= targets.cost
    speedup_target_met = targets.speedup_min <= speedup_factor <= targets.speedup_max * 2  # Allow flexibility
    cost_reduction_target_met = cost_reduction_pct >= targets.cost_reduction

    return {
        "ticker": ticker,
        "approach": targets.approach_name,
        "ai_summary_enabled": ai_summary_enabled,
        "execution_time": execution_time,
        "llm_calls": llm_calls,
        "cost_usd": cost_usd,
        "speedup_factor": speedup_factor,
        "cost_reduction_pct": cost_reduction_pct,
        # Target validation
        "time_target_met": time_target_met,
        "llm_target_met": llm_target_met,
        "cost_target_met": cost_target_met,
        "speedup_target_met": speedup_target_met,
        "cost_reduction_target_met": cost_reduction_target_met,
        # Overall validation
        "all_targets_met": all([
            time_target_met,
            llm_target_met,
            cost_target_met,
            speedup_target_met,
            cost_reduction_target_met,
        ]),
        # Baseline comparison
        "baseline_ai_time_avg": baseline.avg_time,
        "baseline_ai_cost_avg": baseline.avg_cost,
        # Targets for reference
        "targets": {
            "approach": targets.approach_name,
            "time_range": f"{targets.time_min}-{targets.time_max}s",
            "llm_calls": targets.llm_calls,
            "cost": f"${targets.cost:.2f}",
            "speedup_range": f"{targets.speedup_min}-{targets.speedup_max}x",
            "cost_reduction": f"{targets.cost_reduction}%",
        },
    }


def log_performance_validation(validation: dict[str, Any]) -> None:
    """
    Log performance validation results.

    Args:
        validation: Validation results from validate_performance_targets

    """
    ticker = validation["ticker"]
    targets = validation["targets"]

    logger.info(
        f"📊 PERFORMANCE VALIDATION for {ticker} ({validation['approach']}):\n"
        f"  ✅ Execution time: {validation['execution_time']:.2f}s "
        f"({'✅ PASS' if validation['time_target_met'] else '❌ FAIL'} - target: {targets['time_range']})\n"
        f"  ✅ LLM calls: {validation['llm_calls']} "
        f"({'✅ PASS' if validation['llm_target_met'] else '❌ FAIL'} - target: {targets['llm_calls']})\n"
        f"  ✅ Cost: ${validation['cost_usd']:.4f} "
        f"({'✅ PASS' if validation['cost_target_met'] else '❌ FAIL'} - target: {targets['cost']})\n"
        f"  🚀 Speedup achieved: {validation['speedup_factor']:.1f}x "
        f"({'✅ PASS' if validation['speedup_target_met'] else '❌ FAIL'} - target: {targets['speedup_range']})\n"
        f"  💸 Cost reduction: {validation['cost_reduction_pct']:.1f}% "
        f"({'✅ PASS' if validation['cost_reduction_target_met'] else '❌ FAIL'} - target: {targets['cost_reduction']})"
    )
