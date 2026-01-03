"""
Performance monitoring for FinWiz optimization modes.

This module tracks execution time, LLM calls, API calls, and cost estimates
to validate optimization improvements and compare against baseline performance.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.config.performance.performance_config import OptimizationMode, get_performance_config_manager
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TickerMetrics:
    """Performance metrics for a single ticker analysis."""

    ticker: str
    asset_class: str
    mode: OptimizationMode

    # Timing metrics
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    execution_time: float | None = None

    # Usage metrics
    llm_call_count: int = 0
    api_call_count: int = 0
    cost_estimate: float = 0.0

    # Performance comparison
    baseline_time_estimate: float = 300.0  # 5 minutes baseline
    baseline_cost_estimate: float = 0.075  # $0.075 baseline

    # Quality metrics
    grade: str | None = None
    composite_score: float | None = None
    confidence: float | None = None

    # Status
    success: bool = False
    error_message: str | None = None

    def complete(self, success: bool = True, error_message: str | None = None) -> None:
        """Mark the analysis as complete and calculate metrics."""
        self.end_time = time.time()
        self.execution_time = self.end_time - self.start_time
        self.success = success
        self.error_message = error_message

    def calculate_performance_gains(self) -> dict[str, float]:
        """Calculate performance improvements vs baseline."""
        if not self.execution_time:
            return {}

        time_savings_pct = (self.baseline_time_estimate - self.execution_time) / self.baseline_time_estimate * 100
        cost_savings_pct = (self.baseline_cost_estimate - self.cost_estimate) / self.baseline_cost_estimate * 100
        speedup_factor = self.baseline_time_estimate / self.execution_time

        return {
            "time_savings_pct": time_savings_pct,
            "cost_savings_pct": cost_savings_pct,
            "speedup_factor": speedup_factor,
            "time_saved_seconds": self.baseline_time_estimate - self.execution_time,
            "cost_saved_usd": self.baseline_cost_estimate - self.cost_estimate,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        performance_gains = self.calculate_performance_gains()

        return {
            "ticker": self.ticker,
            "asset_class": self.asset_class,
            "mode": self.mode.value,
            "execution_time": self.execution_time,
            "llm_call_count": self.llm_call_count,
            "api_call_count": self.api_call_count,
            "cost_estimate": self.cost_estimate,
            "grade": self.grade,
            "composite_score": self.composite_score,
            "confidence": self.confidence,
            "success": self.success,
            "error_message": self.error_message,
            "performance_gains": performance_gains,
            "baseline_comparison": {
                "baseline_time": self.baseline_time_estimate,
                "baseline_cost": self.baseline_cost_estimate,
                "actual_time": self.execution_time,
                "actual_cost": self.cost_estimate,
            },
        }


@dataclass
class PortfolioMetrics:
    """Cumulative performance metrics for portfolio analysis."""

    session_id: str
    mode: OptimizationMode
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None

    # Ticker metrics
    ticker_metrics: list[TickerMetrics] = field(default_factory=list)

    # Cumulative metrics
    total_tickers: int = 0
    successful_tickers: int = 0
    failed_tickers: int = 0

    total_execution_time: float = 0.0
    total_llm_calls: int = 0
    total_api_calls: int = 0
    total_cost_estimate: float = 0.0

    # Baseline comparison
    total_baseline_time: float = 0.0
    total_baseline_cost: float = 0.0

    def add_ticker_metrics(self, metrics: TickerMetrics) -> None:
        """Add ticker metrics to portfolio totals."""
        self.ticker_metrics.append(metrics)
        self.total_tickers += 1

        if metrics.success:
            self.successful_tickers += 1
        else:
            self.failed_tickers += 1

        if metrics.execution_time:
            self.total_execution_time += metrics.execution_time

        self.total_llm_calls += metrics.llm_call_count
        self.total_api_calls += metrics.api_call_count
        self.total_cost_estimate += metrics.cost_estimate

        self.total_baseline_time += metrics.baseline_time_estimate
        self.total_baseline_cost += metrics.baseline_cost_estimate

    def complete(self) -> None:
        """Mark portfolio analysis as complete."""
        self.end_time = time.time()

    def calculate_portfolio_performance(self) -> dict[str, Any]:
        """Calculate overall portfolio performance metrics."""
        if self.total_tickers == 0:
            return {}

        # Average metrics per ticker
        avg_time_per_ticker = self.total_execution_time / self.total_tickers
        avg_cost_per_ticker = self.total_cost_estimate / self.total_tickers
        avg_llm_calls_per_ticker = self.total_llm_calls / self.total_tickers
        avg_api_calls_per_ticker = self.total_api_calls / self.total_tickers

        # Baseline comparisons
        avg_baseline_time = self.total_baseline_time / self.total_tickers
        avg_baseline_cost = self.total_baseline_cost / self.total_tickers

        # Performance improvements
        time_savings_pct = ((self.total_baseline_time - self.total_execution_time) / self.total_baseline_time * 100) if self.total_baseline_time > 0 else 0
        cost_savings_pct = ((self.total_baseline_cost - self.total_cost_estimate) / self.total_baseline_cost * 100) if self.total_baseline_cost > 0 else 0
        speedup_factor = self.total_baseline_time / self.total_execution_time if self.total_execution_time > 0 else 0

        # Success rate
        success_rate = self.successful_tickers / self.total_tickers * 100 if self.total_tickers > 0 else 0

        return {
            "total_tickers": self.total_tickers,
            "successful_tickers": self.successful_tickers,
            "failed_tickers": self.failed_tickers,
            "success_rate_pct": success_rate,
            "total_execution_time": self.total_execution_time,
            "avg_time_per_ticker": avg_time_per_ticker,
            "total_llm_calls": self.total_llm_calls,
            "avg_llm_calls_per_ticker": avg_llm_calls_per_ticker,
            "total_api_calls": self.total_api_calls,
            "avg_api_calls_per_ticker": avg_api_calls_per_ticker,
            "total_cost_estimate": self.total_cost_estimate,
            "avg_cost_per_ticker": avg_cost_per_ticker,
            "baseline_comparison": {
                "total_baseline_time": self.total_baseline_time,
                "avg_baseline_time": avg_baseline_time,
                "total_baseline_cost": self.total_baseline_cost,
                "avg_baseline_cost": avg_baseline_cost,
            },
            "performance_improvements": {
                "time_savings_pct": time_savings_pct,
                "cost_savings_pct": cost_savings_pct,
                "speedup_factor": speedup_factor,
                "time_saved_total": self.total_baseline_time - self.total_execution_time,
                "cost_saved_total": self.total_baseline_cost - self.total_cost_estimate,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        portfolio_performance = self.calculate_portfolio_performance()

        return {
            "session_id": self.session_id,
            "mode": self.mode.value,
            "timestamp": datetime.now().isoformat(),
            "portfolio_performance": portfolio_performance,
            "ticker_details": [metrics.to_dict() for metrics in self.ticker_metrics],
        }


class PerformanceMonitor:
    """Performance monitoring system for optimization modes."""

    def __init__(self, session_id: str = "default"):
        """Initialize performance monitor."""
        self.session_id = session_id
        self.perf_config = get_performance_config_manager()
        self.mode = self.perf_config.get_mode()

        # Portfolio-level metrics
        self.portfolio_metrics = PortfolioMetrics(session_id=session_id, mode=self.mode)

        # Current ticker being tracked
        self.current_ticker_metrics: TickerMetrics | None = None

        logger.info(f"Performance monitor initialized for session {session_id} in {self.mode.value} mode")

    def start_ticker_analysis(self, ticker: str, asset_class: str) -> TickerMetrics:
        """Start tracking performance for a ticker analysis."""
        self.current_ticker_metrics = TickerMetrics(ticker=ticker, asset_class=asset_class, mode=self.mode)

        logger.info(f"Started performance tracking for {ticker} ({asset_class}) in {self.mode.value} mode")
        return self.current_ticker_metrics

    def record_llm_call(self, cost_estimate: float = 0.0) -> None:
        """Record an LLM call and its estimated cost."""
        if self.current_ticker_metrics:
            self.current_ticker_metrics.llm_call_count += 1
            self.current_ticker_metrics.cost_estimate += cost_estimate

    def record_api_call(self) -> None:
        """Record an API call."""
        if self.current_ticker_metrics:
            self.current_ticker_metrics.api_call_count += 1

    def record_analysis_result(self, grade: str, composite_score: float, confidence: float) -> None:
        """Record analysis results for quality tracking."""
        if self.current_ticker_metrics:
            self.current_ticker_metrics.grade = grade
            self.current_ticker_metrics.composite_score = composite_score
            self.current_ticker_metrics.confidence = confidence

    def complete_ticker_analysis(self, success: bool = True, error_message: str | None = None) -> TickerMetrics:
        """Complete ticker analysis and add to portfolio metrics."""
        if not self.current_ticker_metrics:
            raise ValueError("No ticker analysis in progress")

        self.current_ticker_metrics.complete(success, error_message)
        self.portfolio_metrics.add_ticker_metrics(self.current_ticker_metrics)

        # Log performance results
        self._log_ticker_performance(self.current_ticker_metrics)

        completed_metrics = self.current_ticker_metrics
        self.current_ticker_metrics = None

        return completed_metrics

    def complete_portfolio_analysis(self) -> PortfolioMetrics:
        """Complete portfolio analysis and generate final report."""
        self.portfolio_metrics.complete()

        # Log portfolio performance summary
        self._log_portfolio_performance()

        # Save performance report
        self._save_performance_report()

        return self.portfolio_metrics

    def _log_ticker_performance(self, metrics: TickerMetrics) -> None:
        """Log performance results for a single ticker."""
        if not metrics.execution_time:
            return

        gains = metrics.calculate_performance_gains()

        logger.info(
            f"📊 PERFORMANCE RESULTS for {metrics.ticker}:\n"
            f"  ✅ Mode: {metrics.mode.value}\n"
            f"  ⏱️  Execution time: {metrics.execution_time:.2f}s "
            f"(baseline: {metrics.baseline_time_estimate:.0f}s)\n"
            f"  🤖 LLM calls: {metrics.llm_call_count}\n"
            f"  🌐 API calls: {metrics.api_call_count}\n"
            f"  💰 Cost: ${metrics.cost_estimate:.4f} "
            f"(baseline: ${metrics.baseline_cost_estimate:.4f})\n"
            f"  🚀 Speedup: {gains.get('speedup_factor', 0):.1f}x\n"
            f"  💸 Cost savings: {gains.get('cost_savings_pct', 0):.1f}%\n"
            f"  📈 Grade: {metrics.grade} (score: {metrics.composite_score:.3f})"
        )

    def _log_portfolio_performance(self) -> None:
        """Log portfolio-level performance summary."""
        perf = self.portfolio_metrics.calculate_portfolio_performance()

        logger.info(
            f"🎯 PORTFOLIO PERFORMANCE SUMMARY ({self.mode.value} mode):\n"
            f"  📊 Tickers analyzed: {perf['total_tickers']} "
            f"({perf['successful_tickers']} successful, {perf['failed_tickers']} failed)\n"
            f"  ✅ Success rate: {perf['success_rate_pct']:.1f}%\n"
            f"  ⏱️  Total time: {perf['total_execution_time']:.1f}s "
            f"(avg: {perf['avg_time_per_ticker']:.1f}s per ticker)\n"
            f"  🤖 Total LLM calls: {perf['total_llm_calls']} "
            f"(avg: {perf['avg_llm_calls_per_ticker']:.1f} per ticker)\n"
            f"  🌐 Total API calls: {perf['total_api_calls']} "
            f"(avg: {perf['avg_api_calls_per_ticker']:.1f} per ticker)\n"
            f"  💰 Total cost: ${perf['total_cost_estimate']:.2f} "
            f"(avg: ${perf['avg_cost_per_ticker']:.4f} per ticker)\n"
            f"  🚀 Overall speedup: {perf['performance_improvements']['speedup_factor']:.1f}x\n"
            f"  💸 Overall cost savings: {perf['performance_improvements']['cost_savings_pct']:.1f}%\n"
            f"  ⏰ Time saved: {perf['performance_improvements']['time_saved_total']:.1f}s\n"
            f"  💵 Cost saved: ${perf['performance_improvements']['cost_saved_total']:.2f}"
        )

    def _save_performance_report(self) -> None:
        """Save performance report to JSON file."""
        try:
            # Create output directory
            output_dir = Path("output") / "reports" / self.session_id
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save performance report
            report_path = output_dir / "performance_metrics.json"
            with open(report_path, "w") as f:
                json.dump(self.portfolio_metrics.to_dict(), f, indent=2)

            logger.info(f"Performance report saved to {report_path}")

        except Exception as e:
            logger.error(f"Failed to save performance report: {e}")

    def get_current_metrics(self) -> TickerMetrics | None:
        """Get current ticker metrics being tracked."""
        return self.current_ticker_metrics

    def get_portfolio_metrics(self) -> PortfolioMetrics:
        """Get portfolio-level metrics."""
        return self.portfolio_metrics

    def validate_performance_targets(self) -> dict[str, bool]:
        """Validate performance against mode-specific targets."""
        perf = self.portfolio_metrics.calculate_portfolio_performance()

        if self.mode == OptimizationMode.MAXIMUM_SPEED:
            # Maximum Speed targets: 10-30s, 0 LLM calls, $0 cost
            time_target = 10 <= perf.get("avg_time_per_ticker", 0) <= 30
            llm_target = perf.get("avg_llm_calls_per_ticker", 0) == 0
            cost_target = perf.get("avg_cost_per_ticker", 0) == 0.0
            speedup_target = perf.get("performance_improvements", {}).get("speedup_factor", 0) >= 10

        elif self.mode == OptimizationMode.BALANCED:
            # Balanced targets: 15-40s, 1 LLM call, $0.01 cost
            time_target = 15 <= perf.get("avg_time_per_ticker", 0) <= 40
            llm_target = perf.get("avg_llm_calls_per_ticker", 0) <= 1
            cost_target = perf.get("avg_cost_per_ticker", 0) <= 0.01
            speedup_target = perf.get("performance_improvements", {}).get("speedup_factor", 0) >= 8

        else:  # BASELINE
            # Baseline targets: 5-10 minutes (for comparison)
            time_target = 300 <= perf.get("avg_time_per_ticker", 0) <= 600
            llm_target = True  # No specific target for baseline
            cost_target = True  # No specific target for baseline
            speedup_target = True  # Baseline is 1x by definition

        return {
            "time_target_met": time_target,
            "llm_target_met": llm_target,
            "cost_target_met": cost_target,
            "speedup_target_met": speedup_target,
            "all_targets_met": all([time_target, llm_target, cost_target, speedup_target]),
        }


# Global performance monitor instance
_performance_monitor: PerformanceMonitor | None = None


def get_performance_monitor(session_id: str = "default") -> PerformanceMonitor:
    """Get or create performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None or _performance_monitor.session_id != session_id:
        _performance_monitor = PerformanceMonitor(session_id)
    return _performance_monitor


def start_ticker_tracking(ticker: str, asset_class: str, session_id: str = "default") -> TickerMetrics:
    """Start performance tracking for a ticker."""
    monitor = get_performance_monitor(session_id)
    return monitor.start_ticker_analysis(ticker, asset_class)


def record_llm_call(cost_estimate: float = 0.0, session_id: str = "default") -> None:
    """Record an LLM call."""
    monitor = get_performance_monitor(session_id)
    monitor.record_llm_call(cost_estimate)


def record_api_call(session_id: str = "default") -> None:
    """Record an API call."""
    monitor = get_performance_monitor(session_id)
    monitor.record_api_call()


def complete_ticker_tracking(success: bool = True, error_message: str | None = None, session_id: str = "default") -> TickerMetrics:
    """Complete ticker performance tracking."""
    monitor = get_performance_monitor(session_id)
    return monitor.complete_ticker_analysis(success, error_message)


def complete_portfolio_tracking(session_id: str = "default") -> PortfolioMetrics:
    """Complete portfolio performance tracking."""
    monitor = get_performance_monitor(session_id)
    return monitor.complete_portfolio_analysis()
