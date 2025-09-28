"""
Crew Data Integration System Demo.

Demonstrates how to use the CrewDataIntegrationManager for coordinating
crew execution and managing data flow between crews.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from finwiz.integration import CrewDataIntegrationManager
from finwiz.integration.manager import CrewConfig


async def demo_integration_system() -> None:
    """Demonstrate the integration system functionality."""
    print("=== FinWiz Crew Data Integration System Demo ===\n")

    # Initialize the integration manager
    print("1. Initializing CrewDataIntegrationManager...")
    manager = CrewDataIntegrationManager(output_dir=Path("output"))
    print(f"   Integration directory: {manager.integration_dir}")
    print(f"   Metadata directory: {manager.metadata_dir}")
    print(f"   Contracts directory: {manager.contracts_dir}")
    print(f"   Consolidated directory: {manager.consolidated_dir}\n")

    # Check data freshness
    print("2. Checking data freshness...")
    freshness_report = manager.check_data_freshness(max_age_hours=24)
    print(f"   Overall status: {freshness_report.overall_status}")
    print(f"   Fresh data: {freshness_report.fresh_data}")
    print(f"   Stale data: {freshness_report.stale_data}")
    print(f"   Missing data: {freshness_report.missing_data}\n")

    # Check upstream data availability
    print("3. Checking upstream data for report crew...")
    upstream_data = manager.get_upstream_data("report")
    print(f"   Available data sources: {list(upstream_data.available_data.keys())}")
    print(f"   Missing data sources: {upstream_data.missing_data}")
    print(f"   Stale data sources: {upstream_data.stale_data}\n")

    # Validate sample crew output
    print("4. Validating sample crew output...")
    sample_output = {
        "metadata": {
            "crew_name": "stock",
            "execution_timestamp": datetime.now().isoformat(),
            "schema_version": 1,
            "validation_status": "VALID",
        },
        "analysis_results": [
            {"ticker": "AAPL", "recommendation": "BUY", "confidence": 0.85},
            {"ticker": "GOOGL", "recommendation": "HOLD", "confidence": 0.72},
        ],
        "sec_citations": [
            {"ticker": "AAPL", "filing_url": "https://sec.gov/example", "filed_at": "2024-01-15", "section": "Business Overview"}
        ],
    }

    validation_result = manager.validate_crew_output("stock", sample_output)
    print(f"   Validation result: {'PASSED' if validation_result.is_valid else 'FAILED'}")
    print(f"   Errors: {validation_result.errors}")
    print(f"   Warnings: {validation_result.warnings}\n")

    # Demonstrate crew execution coordination
    print("5. Coordinating crew execution...")
    crews = [
        CrewConfig(name="stock", dependencies=[]),
        CrewConfig(name="etf", dependencies=[]),
        CrewConfig(name="crypto", dependencies=[]),
        CrewConfig(name="discovery", dependencies=["stock", "etf", "crypto"]),
        CrewConfig(name="report", dependencies=["stock", "etf", "crypto", "discovery"]),
    ]

    execution_result = await manager.coordinate_crew_execution(crews)
    print(f"   Execution success: {execution_result.success}")
    print(f"   Executed crews: {execution_result.executed_crews}")
    print(f"   Failed crews: {execution_result.failed_crews}")
    print(f"   Execution time: {execution_result.execution_time:.2f} seconds")
    if execution_result.errors:
        print(f"   Errors: {execution_result.errors}\n")
    else:
        print()

    # Show logging capabilities
    print("6. Integration system logging...")
    print("   The integration system provides structured logging for:")
    print("   - Crew execution start/completion")
    print("   - Data validation results")
    print("   - Data freshness checks")
    print("   - Integration errors and recovery suggestions")
    print("   - Data lineage tracking")
    print("   - Performance metrics\n")

    print("=== Demo Complete ===")
    print("The integration system is ready to coordinate crew data flow!")


if __name__ == "__main__":
    asyncio.run(demo_integration_system())
