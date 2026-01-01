"""
Optimization accuracy validator for FinWiz performance modes.

This module validates that optimization modes maintain accuracy within acceptable
thresholds compared to baseline performance while achieving performance improvements.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finwiz.tools.logger import get_logger
from finwiz.utils.performance_config import OptimizationMode, get_performance_config_manager
from finwiz.utils.performance_monitor import PortfolioMetrics

logger = get_logger(__name__)


@dataclass
class AccuracyValidationResult:
    """Result of accuracy validation for a single ticker."""

    ticker: str
    mode: OptimizationMode

    # Score comparisons
    baseline_score: float | None = None
    optimized_score: float | None = None
    score_difference: float | None = None
    score_within_threshold: bool = False

    # Grade comparisons
    baseline_grade: str | None = None
    optimized_grade: str | None = None
    grade_matches: bool = False

    # Recommendation comparisons
    baseline_recommendation: str | None = None
    optimized_recommendation: str | None = None
    recommendation_matches: bool = False

    # Overall validation
    accuracy_validated: bool = False
    validation_notes: list[str] | None = None

    def __post_init__(self):
        if self.validation_notes is None:
            self.validation_notes = []


@dataclass
class PerformanceValidationResult:
    """Result of performance validation for optimization mode."""

    mode: OptimizationMode

    # Performance metrics
    avg_execution_time: float = 0.0
    target_time_min: float = 0.0
    target_time_max: float = 0.0
    time_target_met: bool = False

    speedup_factor: float = 0.0
    target_speedup_min: float = 0.0
    speedup_target_met: bool = False

    cost_savings_pct: float = 0.0
    target_cost_savings: float = 0.0
    cost_target_met: bool = False

    # Performance degradation check
    performance_degraded: bool = False
    degradation_pct: float = 0.0
    degradation_threshold: float = 10.0  # 10% threshold

    # Overall validation
    performance_validated: bool = False
    validation_notes: list[str] | None = None

    def __post_init__(self):
        if self.validation_notes is None:
            self.validation_notes = []


class OptimizationValidator:
    """Validator for optimization accuracy and performance."""

    # Accuracy thresholds
    SCORE_THRESHOLD = 0.05  # ±0.05 score difference allowed
    GRADE_MATCH_REQUIRED = True
    RECOMMENDATION_MATCH_REQUIRED = True

    # Performance degradation threshold
    PERFORMANCE_DEGRADATION_THRESHOLD = 10.0  # 10%

    def __init__(self) -> None:
        """Initialize optimization validator."""
        self.perf_config = get_performance_config_manager()
        self.mode = self.perf_config.get_mode()

        # Performance targets by mode
        self.performance_targets = {
            OptimizationMode.MAXIMUM_SPEED: {
                "time_min": 10,
                "time_max": 30,
                "speedup_min": 10,
                "speedup_max": 20,
                "cost_savings": 100,
            },
            OptimizationMode.BALANCED: {"time_min": 15, "time_max": 40, "speedup_min": 8, "speedup_max": 15, "cost_savings": 80},
            OptimizationMode.BASELINE: {"time_min": 300, "time_max": 600, "speedup_min": 1, "speedup_max": 1, "cost_savings": 0},
        }

    def validate_accuracy_against_baseline(self, ticker: str, baseline_result: dict[str, Any], optimized_result: dict[str, Any]) -> AccuracyValidationResult:
        """
        Validate that optimized results match baseline within thresholds.

        Args:
            ticker: Asset ticker
            baseline_result: Results from baseline (AI) mode
            optimized_result: Results from optimized mode

        Returns:
            AccuracyValidationResult with validation details

        """
        result = AccuracyValidationResult(ticker=ticker, mode=self.mode)

        # Extract scores
        result.baseline_score = baseline_result.get("composite_score")
        result.optimized_score = optimized_result.get("composite_score")

        # Validate score difference
        if result.baseline_score is not None and result.optimized_score is not None:
            result.score_difference = abs(result.baseline_score - result.optimized_score)
            result.score_within_threshold = result.score_difference <= self.SCORE_THRESHOLD

            if not result.score_within_threshold:
                result.validation_notes.append(f"Score difference {result.score_difference:.3f} exceeds threshold {self.SCORE_THRESHOLD}")
        else:
            result.validation_notes.append("Missing score data for comparison")

        # Extract and validate grades
        result.baseline_grade = baseline_result.get("grade")
        result.optimized_grade = optimized_result.get("grade")

        if result.baseline_grade and result.optimized_grade:
            result.grade_matches = result.baseline_grade == result.optimized_grade

            if not result.grade_matches and self.GRADE_MATCH_REQUIRED:
                result.validation_notes.append(f"Grade mismatch: baseline {result.baseline_grade} vs optimized {result.optimized_grade}")
        else:
            result.validation_notes.append("Missing grade data for comparison")

        # Extract and validate recommendations
        result.baseline_recommendation = baseline_result.get("recommendation")
        result.optimized_recommendation = optimized_result.get("recommendation")

        if result.baseline_recommendation and result.optimized_recommendation:
            result.recommendation_matches = result.baseline_recommendation == result.optimized_recommendation

            if not result.recommendation_matches and self.RECOMMENDATION_MATCH_REQUIRED:
                result.validation_notes.append(f"Recommendation mismatch: baseline {result.baseline_recommendation} vs optimized {result.optimized_recommendation}")
        else:
            result.validation_notes.append("Missing recommendation data for comparison")

        # Overall accuracy validation
        accuracy_checks = []

        if result.baseline_score is not None and result.optimized_score is not None:
            accuracy_checks.append(result.score_within_threshold)

        if self.GRADE_MATCH_REQUIRED and result.baseline_grade and result.optimized_grade:
            accuracy_checks.append(result.grade_matches)

        if self.RECOMMENDATION_MATCH_REQUIRED and result.baseline_recommendation and result.optimized_recommendation:
            accuracy_checks.append(result.recommendation_matches)

        result.accuracy_validated = all(accuracy_checks) if accuracy_checks else False

        # Log validation result
        if result.accuracy_validated:
            logger.info(f"✅ Accuracy validation PASSED for {ticker} in {self.mode.value} mode")
        else:
            logger.warning(f"❌ Accuracy validation FAILED for {ticker} in {self.mode.value} mode: {result.validation_notes}")

        return result

    def validate_performance_targets(self, portfolio_metrics: PortfolioMetrics) -> PerformanceValidationResult:
        """
        Validate performance against mode-specific targets.

        Args:
            portfolio_metrics: Portfolio performance metrics

        Returns:
            PerformanceValidationResult with validation details

        """
        result = PerformanceValidationResult(mode=self.mode)

        # Get performance data
        perf_data = portfolio_metrics.calculate_portfolio_performance()
        targets = self.performance_targets[self.mode]

        # Validate execution time
        result.avg_execution_time = perf_data.get("avg_time_per_ticker", 0)
        result.target_time_min = targets["time_min"]
        result.target_time_max = targets["time_max"]
        result.time_target_met = result.target_time_min <= result.avg_execution_time <= result.target_time_max

        if not result.time_target_met:
            result.validation_notes.append(f"Execution time {result.avg_execution_time:.1f}s outside target range {result.target_time_min}-{result.target_time_max}s")

        # Validate speedup factor
        result.speedup_factor = perf_data.get("performance_improvements", {}).get("speedup_factor", 0)
        result.target_speedup_min = targets["speedup_min"]
        result.speedup_target_met = result.speedup_factor >= result.target_speedup_min

        if not result.speedup_target_met:
            result.validation_notes.append(f"Speedup factor {result.speedup_factor:.1f}x below target minimum {result.target_speedup_min}x")

        # Validate cost savings
        result.cost_savings_pct = perf_data.get("performance_improvements", {}).get("cost_savings_pct", 0)
        result.target_cost_savings = targets["cost_savings"]
        result.cost_target_met = result.cost_savings_pct >= result.target_cost_savings

        if not result.cost_target_met:
            result.validation_notes.append(f"Cost savings {result.cost_savings_pct:.1f}% below target {result.target_cost_savings}%")

        # Check for performance degradation (compared to previous runs)
        result.performance_degraded = False  # Would need historical data to implement

        # Overall performance validation
        result.performance_validated = all([result.time_target_met, result.speedup_target_met, result.cost_target_met, not result.performance_degraded])

        # Log validation result
        if result.performance_validated:
            logger.info(f"✅ Performance validation PASSED for {self.mode.value} mode")
        else:
            logger.warning(f"❌ Performance validation FAILED for {self.mode.value} mode: {result.validation_notes}")

        return result

    def run_regression_tests(self, test_tickers: list[str], baseline_results: dict[str, dict[str, Any]], optimized_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """
        Run regression tests comparing baseline vs optimized results.

        Args:
            test_tickers: List of tickers to test
            baseline_results: Results from baseline mode
            optimized_results: Results from optimized mode

        Returns:
            Dict with regression test results

        """
        regression_results: dict[str, Any] = {
            "mode": self.mode.value,
            "total_tickers": len(test_tickers),
            "passed_tickers": 0,
            "failed_tickers": 0,
            "accuracy_validations": [],
            "overall_passed": False,
        }

        for ticker in test_tickers:
            if ticker in baseline_results and ticker in optimized_results:
                validation = self.validate_accuracy_against_baseline(ticker, baseline_results[ticker], optimized_results[ticker])

                regression_results["accuracy_validations"].append(
                    {
                        "ticker": ticker,
                        "passed": validation.accuracy_validated,
                        "score_difference": validation.score_difference,
                        "grade_matches": validation.grade_matches,
                        "recommendation_matches": validation.recommendation_matches,
                        "notes": validation.validation_notes,
                    }
                )

                if validation.accuracy_validated:
                    regression_results["passed_tickers"] += 1
                else:
                    regression_results["failed_tickers"] += 1
            else:
                logger.warning(f"Missing results for ticker {ticker} in regression test")
                regression_results["failed_tickers"] += 1

        # Calculate pass rate
        pass_rate = regression_results["passed_tickers"] / regression_results["total_tickers"] * 100 if regression_results["total_tickers"] > 0 else 0

        regression_results["pass_rate_pct"] = pass_rate
        regression_results["overall_passed"] = pass_rate >= 90.0  # 90% pass rate required

        # Log regression test results
        logger.info(
            f"📊 REGRESSION TEST RESULTS for {self.mode.value} mode:\n"
            f"  ✅ Passed: {regression_results['passed_tickers']}/{regression_results['total_tickers']} "
            f"({pass_rate:.1f}%)\n"
            f"  ❌ Failed: {regression_results['failed_tickers']}\n"
            f"  🎯 Overall: {'PASSED' if regression_results['overall_passed'] else 'FAILED'}"
        )

        return regression_results

    def generate_validation_report(
        self,
        portfolio_metrics: PortfolioMetrics,
        accuracy_validations: list[AccuracyValidationResult] | None = None,
        session_id: str = "default",
    ) -> dict[str, Any]:
        """
        Generate comprehensive validation report.

        Args:
            portfolio_metrics: Portfolio performance metrics
            accuracy_validations: List of accuracy validation results
            session_id: Session identifier

        Returns:
            Dict with validation report

        """
        # Performance validation
        performance_validation = self.validate_performance_targets(portfolio_metrics)

        # Accuracy summary
        accuracy_summary = {}
        if accuracy_validations:
            total_validations = len(accuracy_validations)
            passed_validations = sum(1 for v in accuracy_validations if v.accuracy_validated)

            accuracy_summary = {
                "total_tickers": total_validations,
                "passed_tickers": passed_validations,
                "failed_tickers": total_validations - passed_validations,
                "pass_rate_pct": (passed_validations / total_validations * 100 if total_validations > 0 else 0),
                "validations": [
                    {
                        "ticker": v.ticker,
                        "passed": v.accuracy_validated,
                        "score_difference": v.score_difference,
                        "grade_matches": v.grade_matches,
                        "recommendation_matches": v.recommendation_matches,
                        "notes": v.validation_notes,
                    }
                    for v in accuracy_validations
                ],
            }

        # Overall validation status
        performance_passed = performance_validation.performance_validated
        accuracy_passed = accuracy_summary.get("pass_rate_pct", 0) >= 90.0 if accuracy_validations else True

        validation_report = {
            "session_id": session_id,
            "mode": self.mode.value,
            "timestamp": portfolio_metrics.portfolio_metrics.start_time,
            "performance_validation": {
                "passed": performance_passed,
                "avg_execution_time": performance_validation.avg_execution_time,
                "time_target_met": performance_validation.time_target_met,
                "speedup_factor": performance_validation.speedup_factor,
                "speedup_target_met": performance_validation.speedup_target_met,
                "cost_savings_pct": performance_validation.cost_savings_pct,
                "cost_target_met": performance_validation.cost_target_met,
                "notes": performance_validation.validation_notes,
            },
            "accuracy_validation": accuracy_summary,
            "overall_validation": {
                "passed": performance_passed and accuracy_passed,
                "performance_passed": performance_passed,
                "accuracy_passed": accuracy_passed,
                "recommendations": self._generate_recommendations(performance_validation, accuracy_validations),
            },
        }

        # Save validation report
        self._save_validation_report(validation_report, session_id)

        return validation_report

    def _generate_recommendations(self, performance_validation: PerformanceValidationResult, accuracy_validations: list[AccuracyValidationResult] | None = None) -> list[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        # Performance recommendations
        if not performance_validation.time_target_met:
            if performance_validation.avg_execution_time > performance_validation.target_time_max:
                recommendations.append("Consider enabling more aggressive optimizations to reduce execution time")
            else:
                recommendations.append("Execution time below target - consider adding more comprehensive analysis")

        if not performance_validation.speedup_target_met:
            recommendations.append("Speedup factor below target - review optimization implementation")

        if not performance_validation.cost_target_met:
            recommendations.append("Cost savings below target - review LLM usage patterns")

        # Accuracy recommendations
        if accuracy_validations:
            failed_validations = [v for v in accuracy_validations if not v.accuracy_validated]
            if failed_validations:
                recommendations.append(f"Accuracy validation failed for {len(failed_validations)} tickers - review scoring algorithms")

        # General recommendations
        if not recommendations:
            recommendations.append("All validation targets met - optimization performing as expected")

        return recommendations

    def _save_validation_report(self, report: dict[str, Any], session_id: str) -> None:
        """Save validation report to JSON file."""
        try:
            # Create output directory
            output_dir = Path("output") / "reports" / session_id
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save validation report
            report_path = output_dir / "optimization_validation.json"
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)

            logger.info(f"Validation report saved to {report_path}")

        except Exception as e:
            logger.error(f"Failed to save validation report: {e}")


# Global validator instance
_optimization_validator: OptimizationValidator | None = None


def get_optimization_validator() -> OptimizationValidator:
    """Get or create optimization validator instance."""
    global _optimization_validator
    if _optimization_validator is None:
        _optimization_validator = OptimizationValidator()
    return _optimization_validator


def validate_accuracy_against_baseline(ticker: str, baseline_result: dict[str, Any], optimized_result: dict[str, Any]) -> AccuracyValidationResult:
    """Validate accuracy against baseline."""
    validator = get_optimization_validator()
    return validator.validate_accuracy_against_baseline(ticker, baseline_result, optimized_result)


def validate_performance_targets(portfolio_metrics: PortfolioMetrics) -> PerformanceValidationResult:
    """Validate performance targets."""
    validator = get_optimization_validator()
    return validator.validate_performance_targets(portfolio_metrics)


def run_regression_tests(test_tickers: list[str], baseline_results: dict[str, dict[str, Any]], optimized_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Run regression tests."""
    validator = get_optimization_validator()
    return validator.run_regression_tests(test_tickers, baseline_results, optimized_results)
