"""
Checkpoint Manager for FinWiz Flow Job Resumption.

Provides per-phase and per-ticker checkpoints to enable resuming after crashes.
Uses simple JSON files for maximum reliability and debuggability.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class CheckpointManager:
    """
    Manages checkpoints for job resumption.

    Saves state after each phase/ticker to enable resuming from the last checkpoint.
    """

    def __init__(self, session_id: str, checkpoint_dir: Path | str | None = None) -> None:
        """
        Initialize CheckpointManager.

        Args:
            session_id: Unique session identifier
            checkpoint_dir: Directory for checkpoints (default: checkpoints/{session_id})

        """
        self.session_id = session_id
        if checkpoint_dir is None:
            self.checkpoint_dir = Path("checkpoints") / session_id
        else:
            self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"CheckpointManager initialized: {self.checkpoint_dir}")

    def save_phase(self, phase_name: str, data: dict[str, Any]) -> Path:
        """
        Save checkpoint for a phase.

        Args:
            phase_name: Name of the phase (e.g., 'deep_analysis', 'discovery')
            data: Phase data to save

        Returns:
            Path to the checkpoint file

        """
        checkpoint_file = self.checkpoint_dir / f"{phase_name}.json"
        checkpoint_data = {
            "phase": phase_name,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }

        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint_data, f, indent=2, default=str)

        logger.debug(f"Saved checkpoint for phase '{phase_name}'")
        return checkpoint_file

    def load_phase(self, phase_name: str) -> dict[str, Any] | None:
        """
        Load checkpoint for a phase.

        Args:
            phase_name: Name of the phase

        Returns:
            Checkpoint data or None if not found

        """
        checkpoint_file = self.checkpoint_dir / f"{phase_name}.json"
        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file) as f:
                checkpoint_data = json.load(f)
            logger.info(f"Loaded checkpoint for phase '{phase_name}'")
            return checkpoint_data.get("data", {})
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load checkpoint for '{phase_name}': {e}")
            return None

    def get_completed_tickers(self, phase_name: str = "deep_analysis") -> set[str]:
        """
        Get tickers that have been completed for a phase.

        Args:
            phase_name: Name of the phase

        Returns:
            Set of completed ticker symbols

        """
        data = self.load_phase(phase_name)
        if data is None:
            return set()
        return set(data.get("completed_tickers", []))

    def save_ticker_result(
        self,
        ticker: str,
        result: dict[str, Any],
        phase_name: str = "deep_analysis",
    ) -> None:
        """
        Save result for a single ticker and update completed list.

        Args:
            ticker: Ticker symbol
            result: Analysis result
            phase_name: Name of the phase

        """
        # Load existing data
        data = self.load_phase(phase_name) or {
            "completed_tickers": [],
            "results": {},
        }

        # Update with new result
        completed = set(data.get("completed_tickers", []))
        completed.add(ticker)
        data["completed_tickers"] = sorted(completed)
        data["results"] = data.get("results", {})
        data["results"][ticker] = result

        # Save
        self.save_phase(phase_name, data)
        logger.debug(f"Saved result for ticker '{ticker}' in phase '{phase_name}'")

    def get_results(self, phase_name: str = "deep_analysis") -> dict[str, Any]:
        """
        Get all results for a phase.

        Args:
            phase_name: Name of the phase

        Returns:
            Dictionary of ticker -> result

        """
        data = self.load_phase(phase_name)
        if data is None:
            return {}
        return data.get("results", {})

    def clear_phase(self, phase_name: str) -> bool:
        """
        Clear checkpoint for a phase.

        Args:
            phase_name: Name of the phase

        Returns:
            True if cleared, False otherwise

        """
        checkpoint_file = self.checkpoint_dir / f"{phase_name}.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            logger.info(f"Cleared checkpoint for phase '{phase_name}'")
            return True
        return False

    def clear_all(self) -> int:
        """
        Clear all checkpoints for this session.

        Returns:
            Number of checkpoints cleared

        """
        count = 0
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            checkpoint_file.unlink()
            count += 1

        if count > 0:
            logger.info(f"Cleared {count} checkpoints for session '{self.session_id}'")
        return count

    def get_resumption_info(self) -> dict[str, Any]:
        """
        Get info about what can be resumed.

        Returns:
            Dict with phase names and their completion status

        """
        info = {
            "session_id": self.session_id,
            "checkpoint_dir": str(self.checkpoint_dir),
            "phases": {},
        }

        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            phase_name = checkpoint_file.stem
            try:
                with open(checkpoint_file) as f:
                    data = json.load(f)
                completed_count = len(data.get("data", {}).get("completed_tickers", []))
                info["phases"][phase_name] = {
                    "timestamp": data.get("timestamp"),
                    "completed_count": completed_count,
                }
            except (json.JSONDecodeError, OSError):
                info["phases"][phase_name] = {"error": "Failed to load"}

        return info


def get_checkpoint_manager(session_id: str) -> CheckpointManager:
    """
    Get a CheckpointManager instance for the given session.

    Args:
        session_id: Session identifier

    Returns:
        CheckpointManager instance

    """
    return CheckpointManager(session_id)
