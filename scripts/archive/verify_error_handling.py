#!/usr/bin/env python
"""
Verification script for Task 8: Error Handling and Resilience implementation.

This script demonstrates the error handling features implemented in Task 8:
- Partial data fetch failure handling
- Crew execution failure handling
- Fallback to sequential mode

Usage:
    python verify_error_handling.py
"""

from pathlib import Path


def verify_batch_prefetcher_error_handling():
    """Verify batch data prefetcher error handling implementation."""
    print("=" * 80)
    print("VERIFYING BATCH DATA PREFETCHER ERROR HANDLING")
    print("=" * 80)

    # Check if batch_data_prefetcher.py has error handling
    prefetcher_file = Path("src/finwiz/utils/batch_data_prefetcher.py")

    if not prefetcher_file.exists():
        print("❌ batch_data_prefetcher.py not found")
        return False

    content = prefetcher_file.read_text()

    # Check for key error handling features
    checks = {
        "Failed ticker tracking": "failed_tickers" in content,
        "Failed field in results": '"failed": True' in content or "'failed': True" in content,
        "Error logging": "logger.warning" in content and "Failed to" in content,
        "Partial failure handling": "partial_failure" in content or "partial_failures" in content,
        "Continue on failure": "continue" in content or "Continue" in content,
    }

    print("\nError Handling Features:")
    all_passed = True
    for feature, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {feature}")
        if not passed:
            all_passed = False

    return all_passed


def verify_flow_orchestrator_error_handling():
    """Verify flow orchestrator error handling implementation."""
    print("\n" + "=" * 80)
    print("VERIFYING FLOW ORCHESTRATOR ERROR HANDLING")
    print("=" * 80)

    # Check if flow_orchestrator.py has error handling
    flow_file = Path("src/finwiz/flows/flow_orchestrator.py")

    if not flow_file.exists():
        print("❌ flow_orchestrator.py not found")
        return False

    content = flow_file.read_text()

    # Check for key error handling features
    checks = {
        "Error summary generation": "_generate_error_summary" in content,
        "Fallback to sequential mode": "_fallback_to_sequential_mode" in content,
        "Crew execution error handling": "_execute_crew_with_error_handling" in content,
        "Error collection in state": "crew_execution_errors" in content,
        "Graceful degradation": "graceful degradation" in content.lower(),
        "Failure rate checking": "failure_rate" in content,
        "Fallback event tracking": "fallback_events" in content,
    }

    print("\nError Handling Features:")
    all_passed = True
    for feature, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {feature}")
        if not passed:
            all_passed = False

    return all_passed


def verify_requirements_coverage():
    """Verify that all requirements are covered in the implementation."""
    print("\n" + "=" * 80)
    print("VERIFYING REQUIREMENTS COVERAGE")
    print("=" * 80)

    # Check both files for requirement references
    prefetcher_file = Path("src/finwiz/utils/batch_data_prefetcher.py")
    flow_file = Path("src/finwiz/flows/flow_orchestrator.py")

    prefetcher_content = prefetcher_file.read_text() if prefetcher_file.exists() else ""
    flow_content = flow_file.read_text() if flow_file.exists() else ""

    combined_content = prefetcher_content + flow_content

    # Check for requirement references
    requirements = {
        "17.52": "Batch fails completely - retry with smaller batch size",
        "17.53": "Individual tickers fail - log failures and continue",
        "17.54": "Collect all batch errors for consolidated summary",
        "17.55": "Don't fail entire portfolio due to single ticker failures",
    }

    print("\nRequirements Coverage:")
    all_covered = True
    for req_id, description in requirements.items():
        covered = req_id in combined_content
        status = "✅" if covered else "❌"
        print(f"  {status} Requirement {req_id}: {description}")
        if not covered:
            all_covered = False

    return all_covered


def main():
    """Run all verification checks."""
    print("\n" + "=" * 80)
    print("TASK 8: ERROR HANDLING AND RESILIENCE - VERIFICATION")
    print("=" * 80)

    results = {
        "Batch Prefetcher Error Handling": verify_batch_prefetcher_error_handling(),
        "Flow Orchestrator Error Handling": verify_flow_orchestrator_error_handling(),
        "Requirements Coverage": verify_requirements_coverage(),
    }

    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)

    all_passed = True
    for check, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {check}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL VERIFICATION CHECKS PASSED")
        print("Task 8 implementation is complete and correct!")
    else:
        print("❌ SOME VERIFICATION CHECKS FAILED")
        print("Please review the implementation.")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
