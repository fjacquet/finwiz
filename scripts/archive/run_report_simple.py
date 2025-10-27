#!/usr/bin/env python
"""
Simple script to run only the report crew using existing data on disk.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from finwiz.crews.report_crew.report_crew import ReportCrew

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_portfolio_review():
    """Load portfolio review from disk."""
    portfolio_path = Path("output/portfolio/portfolio_review.json")
    if portfolio_path.exists():
        with open(portfolio_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def create_basic_inputs():
    """Create basic inputs for report crew from existing data."""
    inputs = {
        # Date/time info
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "current_day": datetime.now().strftime("%d"),
        "current_month": datetime.now().strftime("%m"),
        "current_year": datetime.now().strftime("%Y"),
        "full_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": datetime.now().isoformat(),
        "report_language": "fr",
        # Portfolio data
        "portfolio_review": load_portfolio_review(),
    }

    logger.info(f"Created inputs with {len(inputs)} keys")
    return inputs


def main():
    """Run the report crew."""
    try:
        logger.info("=" * 80)
        logger.info("Starting Report Generation with Existing Data")
        logger.info("=" * 80)

        # Create basic inputs
        inputs = create_basic_inputs()

        # Initialize report crew
        logger.info("Initializing ReportCrew...")
        report_crew = ReportCrew()

        # Execute report crew
        logger.info("Executing report crew...")
        logger.info("=" * 80)

        result = report_crew.kickoff(inputs=inputs, max_age_hours=168)  # 7 days

        logger.info("=" * 80)
        logger.info("✅ Report generation completed!")
        logger.info("")
        logger.info("Check output files:")
        logger.info("  • output/finwiz_family_financial_plan.html")
        logger.info("")

        return 0

    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
