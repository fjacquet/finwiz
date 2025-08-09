"""
Flow utilities for FinWiz.

This module provides utility functions for flow management, including
output directory handling, caching, and result persistence.
"""

import logging
import os
from typing import Any

from weasyprint import HTML

# Set up logging
logger = logging.getLogger(__name__)


def get_output_dir() -> str:
    """
    Return the absolute path to the output directory for generated reports.

    The directory is resolved relative to the project root, under
    "output/report". The caller is responsible for creating the directory
    if it does not exist (some call sites already do this with
    os.makedirs(output_dir, exist_ok=True)).

    Returns:
        str: Absolute path to the output/report directory.


    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(project_root, "output", "report")


def run_crew_with_caching(
    crew_class: Any,
    output_filename: str,
    state_key: str,
    state: Any,
    inputs: dict[str, Any],
) -> None:
    """
    Run a crew with caching, or load from cache if results exist.

    Args:
        crew_class: The crew class to instantiate and run
        output_filename: Name of the file to cache results
        state_key: Key in the state object to store results
        state: State object to update with results
        inputs: Input parameters for the crew

    """
    output_dir = get_output_dir()
    json_file = os.path.join(output_dir, output_filename)

    if os.path.exists(json_file):
        logger.info(f"Found existing analysis results at {json_file}")
        try:
            with open(json_file) as f:
                result_raw = f.read()
            if isinstance(state, dict):
                state[state_key] = result_raw
            else:
                setattr(state, state_key, result_raw)
            logger.info(f"Loaded existing {state_key} results successfully")
            return
        except Exception as e:
            logger.warning(f"Failed to load existing {state_key} results: {e}. Will run analysis.")

    logger.info(f"Starting {crew_class.__name__} analysis")
    try:
        result = crew_class().crew().kickoff(inputs=inputs)
        logger.info(f"{crew_class.__name__} analysis completed successfully")
        result_raw = result.raw

        if isinstance(state, dict):
            state[state_key] = result_raw
        else:
            setattr(state, state_key, result_raw)

        os.makedirs(output_dir, exist_ok=True)
        with open(json_file, "w") as f:
            f.write(result_raw)
        logger.debug(f"Saved {state_key} HTML results to {json_file}")

        # Generate PDF from HTML
        try:
            pdf_filename = os.path.splitext(json_file)[0] + ".pdf"
            HTML(filename=json_file).write_pdf(pdf_filename)
            logger.info(f"Successfully generated PDF report: {pdf_filename}")
        except Exception as e:
            logger.error(f"Failed to generate PDF report from {json_file}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error in {state_key} analysis: {e}", exc_info=True)
        raise
