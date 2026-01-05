#!/usr/bin/env python
"""
Run only the report_crew using existing analysis data.

This script generates the final comprehensive report using data from
previously completed crew analyses (stock, ETF, crypto, discovery, portfolio).
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.utils.core_analysis_error_handler import CoreAnalysisErrorHandler

from finwiz.crew_factory import CrewFactory
from finwiz.flow_state import FlowStateManager
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.tools.logger import get_logger, setup_logging

# Setup logging
log_dir = Path(__file__).parent / "logs"
setup_logging(log_level=logging.INFO, log_dir=str(log_dir))
logger = get_logger(__name__)


def main():
    """Run the report crew with existing data."""
    try:
        logger.info("=" * 80)
        logger.info("Starting Report Generation with Existing Data")
        logger.info("=" * 80)

        # Initialize data integration system
        integration_manager = CrewDataIntegrationManager()
        data_accessor = CrewDataAccessor(integration_manager)
        error_handler = CoreAnalysisErrorHandler(integration_manager)

        logger.info("✓ Data integration system initialized")

        # Initialize state manager and create inputs
        state_manager = FlowStateManager()
        inputs = state_manager.create_flow_inputs()

        logger.info("✓ Flow state manager initialized")

        # Check data availability
        availability_report = data_accessor.check_data_availability()
        logger.info(f"Data availability status: {availability_report.overall_status.value}")
        logger.info(
            f"Available crews: Stock={availability_report.stock_available}, "
            f"ETF={availability_report.etf_available}, "
            f"Crypto={availability_report.crypto_available}, "
            f"Discovery={availability_report.discovery_available}, "
            f"Portfolio={availability_report.portfolio_available}"
        )

        # Get consolidated data for reporter
        consolidated_data = data_accessor.get_consolidated_reporter_input()
        logger.info(f"✓ Consolidated data from {len(consolidated_data)} sources")

        # Prepare inputs for report crew
        inputs["consolidated_data"] = consolidated_data
        inputs["integrated_data_available"] = len(consolidated_data) > 0
        inputs["market_sentiment"] = consolidated_data.get("market_sentiment", {})
        inputs["ticker_validation"] = consolidated_data.get("ticker_validation", {})
        inputs["aplus_opportunities"] = consolidated_data.get("aplus_opportunities")
        inputs["portfolio_allocation_updates"] = consolidated_data.get("portfolio_allocation_updates", [])
        inputs["aplus_availability_status"] = consolidated_data.get("aplus_availability_status", "UNAVAILABLE")

        # Add core analysis data
        crew_data_dict = consolidated_data.get("consolidated_crew_data", consolidated_data)
        for crew_type in ["stock", "etf", "crypto"]:
            if crew_type in crew_data_dict:
                inputs[f"{crew_type}_analysis_data"] = crew_data_dict[crew_type]
                logger.info(f"✓ {crew_type.capitalize()} analysis data loaded")

        # Check for portfolio review data
        portfolio_json_path = Path("output/portfolio/portfolio_review.json")
        if portfolio_json_path.exists():
            import json

            with open(portfolio_json_path, encoding="utf-8") as f:
                inputs["portfolio_review"] = json.load(f)
            inputs["portfolio_review_json"] = str(portfolio_json_path)
            logger.info("✓ Portfolio review data loaded")
        else:
            logger.warning("⚠ Portfolio review data not found")
            inputs["portfolio_review"] = {}

        # Initialize crew factory
        crew_factory = CrewFactory(integration_manager, error_handler)
        logger.info("✓ Crew factory initialized")

        # Execute report crew
        logger.info("")
        logger.info("=" * 80)
        logger.info("Executing Report Crew")
        logger.info("=" * 80)

        result_data = crew_factory.execute_report_crew(inputs)

        logger.info("")
        logger.info("=" * 80)
        logger.info("Report Generation Complete")
        logger.info("=" * 80)

        if result_data.get("report_generation_success"):
            logger.info("✅ Report generated successfully!")
            logger.info("")
            logger.info("Output files:")
            logger.info("  • output/finwiz_family_financial_plan.html (English)")
            logger.info("  • output/finwiz_family_financial_plan_fr.html (French)")
            logger.info("  • output/report/consolidated_financial_analysis.json")
            logger.info("  • output/report/optimal_portfolio_allocation.json")
            logger.info("  • output/report/risk_assessment_and_mitigation.json")
        else:
            logger.error("❌ Report generation failed")
            if "error" in result_data:
                logger.error(f"Error: {result_data['error']}")

    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
