#!/usr/bin/env python3
"""
Verification script for FinalReportGenerator implementation.

This script verifies that:
1. FinalReportGenerator class can be imported
2. Template exists and can be loaded
3. Basic functionality works with mock data
"""

import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from finwiz.schemas.crew_exports import ConsolidatedReportExport
from finwiz.utils.final_report_generator import FinalReportGenerator


def verify_implementation():
    """Verify FinalReportGenerator implementation."""
    print("=" * 80)
    print("Verifying FinalReportGenerator Implementation")
    print("=" * 80)

    # Test 1: Import and instantiation
    print("\n✓ Test 1: Import and instantiation")
    try:
        generator = FinalReportGenerator()
        print("  - FinalReportGenerator instantiated successfully")
        print(f"  - Template directory: {generator.template_dir}")
    except Exception as e:
        print(f"  ✗ Failed to instantiate: {e}")
        return False

    # Test 2: Template validation
    print("\n✓ Test 2: Template validation")
    try:
        template_exists = generator.validate_template_exists()
        template_path = generator.get_template_path()
        print(f"  - Template path: {template_path}")
        print(f"  - Template exists: {template_exists}")

        if not template_exists:
            print(f"  ✗ Template not found at: {template_path}")
            return False
    except Exception as e:
        print(f"  ✗ Template validation failed: {e}")
        return False

    # Test 3: Mock data generation
    print("\n✓ Test 3: Mock data generation")
    try:
        # Create minimal mock data
        mock_data = ConsolidatedReportExport(
            session_id="test-session-123",
            consolidation_date=datetime.now(),
            stock_analyses=[],
            etf_analyses=[],
            crypto_analyses=[],
            deep_analyses=[],
            discovery_results=None,
            rebalancing_results=None,
            crew_execution_status={"stock_crew": "completed", "etf_crew": "completed", "crypto_crew": "failed"},
            total_execution_time=45.67,
        )
        print("  - Mock ConsolidatedReportExport created")
        print(f"  - Session ID: {mock_data.session_id}")
        print(f"  - Execution time: {mock_data.total_execution_time}s")
    except Exception as e:
        print(f"  ✗ Failed to create mock data: {e}")
        return False

    # Test 4: Report generation
    print("\n✓ Test 4: Report generation")
    try:
        output_path = Path("output/test_reports/test_final_report.html")

        result_path = generator.generate_final_report(consolidated_data=mock_data, output_path=output_path)

        print(f"  - Report generated at: {result_path}")

        # Verify file exists
        if not Path(result_path).exists():
            print(f"  ✗ Output file not found: {result_path}")
            return False

        # Check file size
        file_size = Path(result_path).stat().st_size
        print(f"  - File size: {file_size:,} bytes")

        if file_size < 1000:
            print("  ✗ File seems too small (< 1KB)")
            return False

        # Read and verify content
        content = Path(result_path).read_text(encoding="utf-8")

        # Check for key elements
        checks = [
            ("<!DOCTYPE html>", "HTML doctype"),
            ("Rapport d'Analyse FinWiz", "French title"),
            ("test-session-123", "Session ID"),
            ("Résumé Exécutif", "Executive summary section"),
            ("Statut d'Exécution", "Execution status section"),
        ]

        print("\n  Content validation:")
        for check_str, description in checks:
            if check_str in content:
                print(f"    ✓ {description}")
            else:
                print(f"    ✗ Missing: {description}")
                return False

    except Exception as e:
        print(f"  ✗ Report generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("\n" + "=" * 80)
    print("✅ All verification tests passed!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = verify_implementation()
    sys.exit(0 if success else 1)
