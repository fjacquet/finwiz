"""
Feedback Storage Module.

Handles all file I/O operations for feedback data persistence.
"""

import json
from datetime import datetime
from pathlib import Path

from finwiz.schemas.feedback import PerformanceFeedback, UserFeedback
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class FeedbackStorage:
    """Storage manager for feedback data."""

    def __init__(self, feedback_path: Path, performance_path: Path) -> None:
        """Initialize storage with paths."""
        self.feedback_path = feedback_path
        self.performance_path = performance_path

        # Ensure directories exist
        self.feedback_path.mkdir(parents=True, exist_ok=True)
        self.performance_path.mkdir(parents=True, exist_ok=True)

    async def save_user_feedback(self, feedback: UserFeedback) -> str:
        """Save user feedback to storage."""
        feedback_id = feedback.feedback_id
        feedback_file = self.feedback_path / f"{feedback_id}.json"

        try:
            feedback_data = feedback.model_dump()
            feedback_data["timestamp"] = feedback.timestamp.isoformat()

            with open(feedback_file, "w") as f:
                json.dump(feedback_data, f, indent=2)

            logger.info(f"Saved user feedback: {feedback_id}")
            return feedback_id

        except Exception as e:
            logger.error(f"Failed to save user feedback: {str(e)}")
            raise

    async def save_performance_feedback(self, performance: PerformanceFeedback) -> str:
        """Save performance feedback to storage."""
        performance_id = performance.feedback_id
        performance_file = self.performance_path / f"{performance_id}.json"

        try:
            performance_data = performance.model_dump()
            performance_data["evaluation_date"] = performance.evaluation_date.isoformat()

            with open(performance_file, "w") as f:
                json.dump(performance_data, f, indent=2)

            logger.info(f"Saved performance feedback: {performance_id}")
            return performance_id

        except Exception as e:
            logger.error(f"Failed to save performance feedback: {str(e)}")
            raise

    async def load_feedback_since(self, cutoff_date: datetime) -> list[UserFeedback]:
        """Load user feedback since cutoff date."""
        feedback_list = []

        for feedback_file in self.feedback_path.glob("*.json"):
            try:
                with open(feedback_file) as f:
                    data = json.load(f)

                feedback_timestamp = datetime.fromisoformat(data["timestamp"])
                if feedback_timestamp >= cutoff_date:
                    # Remove storage-specific fields
                    data.pop("id", None)
                    data["timestamp"] = feedback_timestamp
                    feedback_list.append(UserFeedback(**data))

            except Exception as e:
                logger.warning(f"Failed to load feedback file {feedback_file}: {str(e)}")

        return feedback_list

    async def load_performance_since(self, cutoff_date: datetime) -> list[PerformanceFeedback]:
        """Load performance feedback since cutoff date."""
        performance_list = []

        for performance_file in self.performance_path.glob("*.json"):
            try:
                with open(performance_file) as f:
                    data = json.load(f)

                performance_timestamp = datetime.fromisoformat(data["timestamp"])
                if performance_timestamp >= cutoff_date:
                    # Remove storage-specific fields
                    data.pop("id", None)
                    data["timestamp"] = performance_timestamp
                    performance_list.append(PerformanceFeedback(**data))

            except Exception as e:
                logger.warning(f"Failed to load performance file {performance_file}: {str(e)}")

        return performance_list

    async def load_feedback_for_period(self, start_date: datetime, end_date: datetime) -> list[UserFeedback]:
        """Load feedback for a specific time period."""
        feedback_list = []

        for feedback_file in self.feedback_path.glob("*.json"):
            try:
                with open(feedback_file) as f:
                    data = json.load(f)

                feedback_timestamp = datetime.fromisoformat(data["timestamp"])
                if start_date <= feedback_timestamp <= end_date:
                    data.pop("id", None)
                    data["timestamp"] = feedback_timestamp
                    feedback_list.append(UserFeedback(**data))

            except Exception as e:
                logger.warning(f"Failed to load feedback file {feedback_file}: {str(e)}")

        return feedback_list

    async def load_performance_for_period(self, start_date: datetime, end_date: datetime) -> list[PerformanceFeedback]:
        """Load performance feedback for a specific time period."""
        performance_list = []

        for performance_file in self.performance_path.glob("*.json"):
            try:
                with open(performance_file) as f:
                    data = json.load(f)

                performance_timestamp = datetime.fromisoformat(data["timestamp"])
                if start_date <= performance_timestamp <= end_date:
                    data.pop("id", None)
                    data["timestamp"] = performance_timestamp
                    performance_list.append(PerformanceFeedback(**data))

            except Exception as e:
                logger.warning(f"Failed to load performance file {performance_file}: {str(e)}")

        return performance_list
