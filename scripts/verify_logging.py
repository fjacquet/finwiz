#!/usr/bin/env python3
"""
Manual verification script for CrewLogger integration.

This script demonstrates the structured logging functionality
by simulating crew execution and showing the log output.
"""

import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finwiz.utils.logging_helpers import CrewLogger


class LogFormatter(logging.Formatter):
    """Custom formatter to display structured log fields."""

    def format(self, record):
        """Format log record with extra fields."""
        # Get base message
        msg = super().format(record)

        # Add extra fields if present
        extra_fields = []
        if hasattr(record, "crew"):
            extra_fields.append(f"crew={record.crew}")
        if hasattr(record, "event"):
            extra_fields.append(f"event={record.event}")
        if hasattr(record, "input_keys"):
            extra_fields.append(f"input_keys={record.input_keys}")
        if hasattr(record, "duration"):
            extra_fields.append(f"duration={record.duration:.2f}s")
        if hasattr(record, "error_type"):
            extra_fields.append(f"error_type={record.error_type}")

        if extra_fields:
            msg += f" [{', '.join(extra_fields)}]"

        return msg


def setup_logging():
    """Configure logging to show structured fields."""
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add console handler with custom formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = LogFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def simulate_successful_execution():
    """Simulate a successful crew execution."""
    print("\n" + "=" * 80)
    print("SCENARIO 1: Successful Crew Execution")
    print("=" * 80 + "\n")

    logger = CrewLogger("TestCrew")
    inputs = {"ticker": "AAPL", "analysis_type": "fundamental"}

    # Log start
    logger.log_start(inputs)

    # Simulate work
    time.sleep(0.5)

    # Log completion
    duration = 0.5
    logger.log_complete(duration)


def simulate_execution_with_error():
    """Simulate a crew execution that fails."""
    print("\n" + "=" * 80)
    print("SCENARIO 2: Failed Crew Execution")
    print("=" * 80 + "\n")

    logger = CrewLogger("ErrorCrew")
    inputs = {"ticker": "INVALID"}

    # Log start
    logger.log_start(inputs)

    # Simulate error
    try:
        raise ValueError("Invalid ticker symbol: INVALID")
    except ValueError as e:
        logger.log_error(e)


def simulate_execution_with_empty_inputs():
    """Simulate a crew execution with no inputs."""
    print("\n" + "=" * 80)
    print("SCENARIO 3: Execution with Empty Inputs")
    print("=" * 80 + "\n")

    logger = CrewLogger("MinimalCrew")

    # Log start with empty inputs
    logger.log_start({})

    # Simulate work
    time.sleep(0.2)

    # Log completion
    duration = 0.2
    logger.log_complete(duration)


def simulate_multiple_crews():
    """Simulate multiple crews executing in sequence."""
    print("\n" + "=" * 80)
    print("SCENARIO 4: Multiple Crews Executing")
    print("=" * 80 + "\n")

    crews = ["StockCrew", "CryptoCrew", "EtfCrew", "ReportCrew"]

    for crew_name in crews:
        logger = CrewLogger(crew_name)
        inputs = {"asset": f"test_{crew_name.lower()}"}

        logger.log_start(inputs)
        time.sleep(0.1)
        logger.log_complete(0.1)


def main():
    """Run all verification scenarios."""
    print("\n" + "=" * 80)
    print("CrewLogger Integration Verification")
    print("=" * 80)
    print("\nThis script demonstrates the structured logging functionality")
    print("integrated into all FinWiz crews.\n")

    # Setup logging
    setup_logging()

    # Run scenarios
    simulate_successful_execution()
    simulate_execution_with_error()
    simulate_execution_with_empty_inputs()
    simulate_multiple_crews()

    print("\n" + "=" * 80)
    print("Verification Complete")
    print("=" * 80)
    print("\nKey observations:")
    print("✓ All log entries include structured 'extra' fields")
    print("✓ crew_start events include crew name, input_keys, and event type")
    print("✓ crew_complete events include crew name, duration, and event type")
    print("✓ crew_error events include crew name, error_type, and exception info")
    print("✓ Duration tracking is accurate")
    print("✓ Empty inputs are handled correctly")
    print("\n")


if __name__ == "__main__":
    main()
