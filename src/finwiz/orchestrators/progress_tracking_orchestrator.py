"""
Progress Tracking Orchestrator for FinWiz Flow.

This module provides progress calculation and metrics persistence functionality,
tracking workflow progress and saving batch metrics to files.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.flow_state import FinwizState
from finwiz.tools.logger import get_logger


class ProgressTrackingOrchestrator:
    """Tracks and reports execution progress."""

    def __init__(self, state: FinwizState, **dependencies: Any) -> None:
        """
        Initialize the ProgressTrackingOrchestrator.

        Args:
            state: FinwizState instance for tracking progress
            **dependencies: Additional dependencies (not currently used)

        """
        self.state = state
        self.logger = get_logger(self.__class__.__name__)
        self.dependencies = dependencies

    def update_progress(
        self,
        holdings_processed: int,
        total_holdings: int,
    ) -> None:
        """
        Update progress metrics in Flow state.

        Calculates and updates progress-related fields:
        - progress_percentage: Percentage of holdings processed
        - estimated_time_remaining: Estimated seconds until completion
        - last_checkpoint_time: Timestamp of this progress update

        Args:
            holdings_processed: Number of holdings processed so far
            total_holdings: Total number of holdings to process

        Requirements: 8.1, 8.3, 8.4

        """
        # Update state counters
        self.state.holdings_processed = holdings_processed
        self.state.total_holdings = total_holdings
        self.state.holdings_remaining = total_holdings - holdings_processed

        # Calculate progress percentage
        if total_holdings > 0:
            self.state.progress_percentage = (holdings_processed / total_holdings) * 100
        else:
            self.state.progress_percentage = 0.0

        # Calculate estimated time remaining based on average time per holding
        if holdings_processed > 0 and self.state.holdings_remaining > 0 and self.state.flow_start_time:
            # Calculate elapsed time
            flow_start = (
                self.state.flow_start_time
                if isinstance(self.state.flow_start_time, datetime)
                else datetime.fromisoformat(self.state.flow_start_time)
            )
            elapsed_time = (datetime.now() - flow_start).total_seconds()

            # Calculate average time per holding
            avg_time_per_holding = elapsed_time / holdings_processed

            # Estimate remaining time
            self.state.estimated_time_remaining = avg_time_per_holding * self.state.holdings_remaining
        else:
            self.state.estimated_time_remaining = 0.0

        # Update last checkpoint time
        self.state.last_checkpoint_time = datetime.now().isoformat()

        # Log progress with formatted message
        self._log_progress()

    def save_batch_metrics_to_file(
        self,
        metrics: dict[str, Any],
        output_path: str | None = None,
    ) -> None:
        """
        Save batch metrics to JSON file.

        Creates a JSON file with batch processing metrics including:
        - Total tickers, successful, failed
        - Duration breakdown (prefetch vs execution)
        - Time savings percentage
        - Per-ticker execution times

        Args:
            metrics: Dictionary containing batch metrics to save
            output_path: Optional custom output path. If None, uses session output directory

        Requirements: 8.2

        """
        if not metrics:
            self.logger.warning("No batch metrics to save")
            return

        try:
            # Determine output path
            if output_path:
                metrics_file = Path(output_path)
                # Create parent directory if it doesn't exist
                metrics_file.parent.mkdir(parents=True, exist_ok=True)
            else:
                # Use session output directory
                output_dir = Path(f"output/reports/{self.state.session_id}")
                output_dir.mkdir(parents=True, exist_ok=True)
                metrics_file = output_dir / "batch_prefetch_metrics.json"

            # Write metrics to file
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2, default=str)

            self.logger.info(f"✓ Batch metrics saved to: {metrics_file}")
            self.logger.info(f"  File size: {metrics_file.stat().st_size / 1024:.1f} KB")

        except Exception as e:
            self.logger.error(f"✗ Failed to save batch metrics: {e}", exc_info=True)

    def _log_progress(self) -> None:
        """
        Log formatted progress message.

        Internal helper method that formats and logs progress information including:
        - Holdings processed/total with percentage
        - Elapsed time
        - Estimated remaining time
        - Success/failure counts

        Requirements: 8.4

        """
        # Calculate elapsed time
        if self.state.flow_start_time:
            flow_start = (
                self.state.flow_start_time
                if isinstance(self.state.flow_start_time, datetime)
                else datetime.fromisoformat(self.state.flow_start_time)
            )
            elapsed_time = (datetime.now() - flow_start).total_seconds()
            elapsed_minutes = int(elapsed_time // 60)
            elapsed_seconds = int(elapsed_time % 60)
        else:
            elapsed_minutes = 0
            elapsed_seconds = 0

        # Calculate remaining time
        remaining_minutes = int(self.state.estimated_time_remaining // 60)
        remaining_seconds = int(self.state.estimated_time_remaining % 60)

        # Calculate success/failure counts
        failed_count = len(self.state.failed_holdings)
        timeout_count = len(self.state.timeout_holdings)
        success_count = self.state.holdings_processed - failed_count

        # Log formatted progress message
        self.logger.info(
            f"Progress Update: {self.state.holdings_processed}/{self.state.total_holdings} "
            f"({self.state.progress_percentage:.1f}%) | "
            f"Elapsed: {elapsed_minutes}m {elapsed_seconds}s | "
            f"Remaining: ~{remaining_minutes}m {remaining_seconds}s | "
            f"Success: {success_count}, "
            f"Failed: {failed_count}, "
            f"Timeouts: {timeout_count}"
        )
