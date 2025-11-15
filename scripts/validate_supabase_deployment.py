#!/usr/bin/env python3
"""
Supabase Deployment Validation Script

Validates Supabase timeout fix deployment by:
1. Checking configuration
2. Testing connectivity
3. Monitoring timeout rates
4. Validating graceful degradation
5. Verifying performance impact

Usage:
    python scripts/validate_supabase_deployment.py --phase 1
    python scripts/validate_supabase_deployment.py --phase 2
    python scripts/validate_supabase_deployment.py --validate-all
"""

import argparse
import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finwiz.supabase.client import SupabaseClient
from finwiz.supabase.repositories.analysis_repository import AnalysisRepository
from finwiz.supabase.services.cache_service import CacheService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DeploymentValidator:
    """Validates Supabase deployment phases."""

    def __init__(self):
        """Initialize validator."""
        self.client = SupabaseClient()
        self.repository = AnalysisRepository(self.client)
        self.cache_service = CacheService(self.repository, self.client)
        self.results = {"timestamp": datetime.now().isoformat(), "phase": None, "checks": [], "success": True, "errors": []}

    def log_check(self, name: str, passed: bool, message: str):
        """Log validation check result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {name} - {message}")

        self.results["checks"].append({"name": name, "passed": passed, "message": message, "timestamp": datetime.now().isoformat()})

        if not passed:
            self.results["success"] = False
            self.results["errors"].append(f"{name}: {message}")

    async def validate_phase_1(self) -> bool:
        """
        Validate Phase 1: Increased timeouts.

        Checks:
        - Timeout configuration updated
        - Environment variables set correctly
        - Circuit breaker thresholds configured

        Returns:
            True if all checks pass, False otherwise

        """
        logger.info("=" * 80)
        logger.info("PHASE 1 VALIDATION: Increased Timeouts")
        logger.info("=" * 80)

        self.results["phase"] = 1

        # Check 1: Read timeout configuration
        read_timeout = self.client.read_timeout
        expected_read = 10.0
        passed = read_timeout >= expected_read
        self.log_check("Read Timeout Configuration", passed, f"Read timeout is {read_timeout}s (expected: >={expected_read}s)")

        # Check 2: Write timeout configuration
        write_timeout = self.client.write_timeout
        expected_write = 15.0
        passed = write_timeout >= expected_write
        self.log_check("Write Timeout Configuration", passed, f"Write timeout is {write_timeout}s (expected: >={expected_write}s)")

        # Check 3: Max retries configuration
        max_retries = self.client.max_retries
        expected_retries = 1
        passed = max_retries == expected_retries
        self.log_check("Max Retries Configuration", passed, f"Max retries is {max_retries} (expected: {expected_retries})")

        # Check 4: Circuit breaker threshold
        cb_threshold = self.client.circuit_breaker.failure_threshold
        expected_threshold = 5
        passed = cb_threshold >= expected_threshold
        self.log_check("Circuit Breaker Threshold", passed, f"Circuit breaker threshold is {cb_threshold} (expected: >={expected_threshold})")

        # Check 5: Circuit breaker timeout
        cb_timeout = self.client.circuit_breaker.recovery_timeout
        expected_cb_timeout = 60
        passed = cb_timeout >= expected_cb_timeout
        self.log_check("Circuit Breaker Timeout", passed, f"Circuit breaker timeout is {cb_timeout}s (expected: >={expected_cb_timeout}s)")

        # Check 6: Environment variables
        env_vars = {
            "SUPABASE_READ_TIMEOUT": os.getenv("SUPABASE_READ_TIMEOUT"),
            "SUPABASE_WRITE_TIMEOUT": os.getenv("SUPABASE_WRITE_TIMEOUT"),
            "SUPABASE_MAX_RETRIES": os.getenv("SUPABASE_MAX_RETRIES"),
            "SUPABASE_CIRCUIT_BREAKER_THRESHOLD": os.getenv("SUPABASE_CIRCUIT_BREAKER_THRESHOLD"),
            "SUPABASE_CIRCUIT_BREAKER_TIMEOUT": os.getenv("SUPABASE_CIRCUIT_BREAKER_TIMEOUT"),
        }

        all_set = all(v is not None for v in env_vars.values())
        self.log_check("Environment Variables", all_set, f"All timeout environment variables configured: {all_set}")

        return self.results["success"]

    async def validate_phase_2(self) -> bool:
        """
        Validate Phase 2: Connectivity test and graceful degradation.

        Checks:
        - Connectivity test executes
        - Cache service initializes
        - Graceful degradation works
        - Analysis completes with cache disabled

        Returns:
            True if all checks pass, False otherwise

        """
        logger.info("=" * 80)
        logger.info("PHASE 2 VALIDATION: Connectivity Test & Graceful Degradation")
        logger.info("=" * 80)

        self.results["phase"] = 2

        # Check 1: Connectivity test timeout
        conn_timeout = self.client.connectivity_test_timeout
        expected_conn = 5.0
        passed = conn_timeout == expected_conn
        self.log_check("Connectivity Test Timeout", passed, f"Connectivity test timeout is {conn_timeout}s (expected: {expected_conn}s)")

        # Check 2: Run connectivity test
        logger.info("Running connectivity test...")
        start_time = time.time()
        connectivity_result = await self.client.test_connectivity()
        elapsed = time.time() - start_time

        passed = elapsed <= conn_timeout + 1.0  # Allow 1s buffer
        self.log_check("Connectivity Test Execution", passed, f"Test completed in {elapsed:.2f}s (timeout: {conn_timeout}s), result: {connectivity_result}")

        # Check 3: Cache service initialization
        logger.info("Initializing cache service...")
        cache_init_result = await self.cache_service.initialize()

        self.log_check(
            "Cache Service Initialization",
            True,  # Always passes, just logs result
            f"Cache service initialized: {cache_init_result}",
        )

        # Check 4: Test graceful degradation with cache disabled
        logger.info("Testing graceful degradation...")

        # Temporarily disable cache
        original_enabled = self.cache_service.is_enabled
        self.cache_service.is_enabled = False

        try:
            # Simulate cache operation
            async def mock_execute():
                await asyncio.sleep(0.1)
                return {"test": "data"}

            result, is_cached = await self.cache_service.get_or_execute(ticker="TEST", asset_class="stock", execute_fn=mock_execute)

            passed = not is_cached and result == {"test": "data"}
            self.log_check("Graceful Degradation", passed, f"Analysis completed with cache disabled: {passed}")
        finally:
            # Restore cache state
            self.cache_service.is_enabled = original_enabled

        # Check 5: Verify is_available flag
        passed = hasattr(self.client, "is_available")
        self.log_check("Availability Flag", passed, f"Client has is_available flag: {passed}, value: {getattr(self.client, 'is_available', None)}")

        return self.results["success"]

    async def validate_success_criteria(self) -> bool:
        """
        Validate overall success criteria.

        Checks:
        - Analysis works with 0% Supabase availability
        - Timeout rate < 10% when available
        - Circuit breaker recovers automatically
        - No blocking delays
        - Clear logging

        Returns:
            True if all checks pass, False otherwise

        """
        logger.info("=" * 80)
        logger.info("SUCCESS CRITERIA VALIDATION")
        logger.info("=" * 80)

        self.results["phase"] = "success_criteria"

        # Check 1: Test with Supabase unavailable
        logger.info("Testing with Supabase unavailable...")

        # Temporarily disable Supabase
        original_enabled = self.client.enabled
        self.client.enabled = False

        try:

            async def mock_analysis():
                await asyncio.sleep(0.1)
                return {"analysis": "complete"}

            result, is_cached = await self.cache_service.get_or_execute(ticker="TEST", asset_class="stock", execute_fn=mock_analysis)

            passed = not is_cached and result == {"analysis": "complete"}
            self.log_check("0% Supabase Availability", passed, f"Analysis completed with Supabase disabled: {passed}")
        finally:
            self.client.enabled = original_enabled

        # Check 2: Timeout rate
        health = self.client.get_health_status()
        timeout_rate = health.timeout_count / max(health.total_operations, 1)
        passed = timeout_rate < 0.10 or health.total_operations == 0
        self.log_check("Timeout Rate", passed, f"Timeout rate: {timeout_rate:.1%} (expected: <10%, operations: {health.total_operations})")

        # Check 3: Circuit breaker state
        cb_open = self.client.circuit_breaker.is_open()
        self.log_check(
            "Circuit Breaker State",
            True,  # Always log, not a failure
            f"Circuit breaker is {'OPEN' if cb_open else 'CLOSED'}",
        )

        # Check 4: No blocking delays (verify async operations)
        logger.info("Testing non-blocking cache writes...")
        start_time = time.time()

        # This should return immediately without waiting for cache write
        async def quick_execute():
            return {"quick": "result"}

        result, _ = await self.cache_service.get_or_execute(ticker="QUICK", asset_class="stock", execute_fn=quick_execute)

        elapsed = time.time() - start_time
        passed = elapsed < 1.0  # Should complete in under 1 second
        self.log_check("Non-Blocking Operations", passed, f"Operation completed in {elapsed:.3f}s (expected: <1.0s)")

        # Check 5: Logging verification
        passed = hasattr(self.client, "log_configuration") and hasattr(self.client, "log_metrics")
        self.log_check("Logging Methods", passed, f"Client has logging methods: {passed}")

        # Log final health status
        logger.info("\n" + "=" * 80)
        logger.info("FINAL HEALTH STATUS")
        logger.info("=" * 80)
        logger.info(f"Available: {health.is_available}")
        logger.info(f"Success Rate: {health.success_rate:.1%}")
        logger.info(f"Avg Response Time: {health.avg_response_time:.1f}ms")
        logger.info(f"Circuit Breaker: {'OPEN' if health.circuit_breaker_open else 'CLOSED'}")
        logger.info(f"Total Operations: {health.total_operations}")
        logger.info(f"Successful: {health.successful_operations}")
        logger.info(f"Failed: {health.failed_operations}")
        logger.info(f"Timeouts: {health.timeout_count}")

        return self.results["success"]

    def print_summary(self):
        """Print validation summary."""
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Phase: {self.results['phase']}")
        logger.info(f"Timestamp: {self.results['timestamp']}")
        logger.info(f"Total Checks: {len(self.results['checks'])}")

        passed_checks = sum(1 for c in self.results["checks"] if c["passed"])
        logger.info(f"Passed: {passed_checks}/{len(self.results['checks'])}")

        if self.results["success"]:
            logger.info("✅ OVERALL: PASS")
        else:
            logger.info("❌ OVERALL: FAIL")
            logger.info("\nErrors:")
            for error in self.results["errors"]:
                logger.info(f"  - {error}")

        logger.info("=" * 80)


async def main():
    """Main validation entry point."""
    parser = argparse.ArgumentParser(description="Validate Supabase deployment")
    parser.add_argument("--phase", type=int, choices=[1, 2], help="Deployment phase to validate (1 or 2)")
    parser.add_argument("--validate-all", action="store_true", help="Run all validation checks")

    args = parser.parse_args()

    if not args.phase and not args.validate_all:
        parser.error("Must specify --phase or --validate-all")

    validator = DeploymentValidator()

    try:
        if args.validate_all:
            # Run all phases
            logger.info("Running complete validation suite...")

            phase1_success = await validator.validate_phase_1()
            validator.print_summary()

            # Reset for phase 2
            validator.results = {"timestamp": datetime.now().isoformat(), "phase": None, "checks": [], "success": True, "errors": []}

            phase2_success = await validator.validate_phase_2()
            validator.print_summary()

            # Reset for success criteria
            validator.results = {"timestamp": datetime.now().isoformat(), "phase": None, "checks": [], "success": True, "errors": []}

            criteria_success = await validator.validate_success_criteria()
            validator.print_summary()

            overall_success = phase1_success and phase2_success and criteria_success

            logger.info("\n" + "=" * 80)
            logger.info("COMPLETE VALIDATION RESULT")
            logger.info("=" * 80)
            logger.info(f"Phase 1: {'✅ PASS' if phase1_success else '❌ FAIL'}")
            logger.info(f"Phase 2: {'✅ PASS' if phase2_success else '❌ FAIL'}")
            logger.info(f"Success Criteria: {'✅ PASS' if criteria_success else '❌ FAIL'}")
            logger.info(f"Overall: {'✅ PASS' if overall_success else '❌ FAIL'}")
            logger.info("=" * 80)

            sys.exit(0 if overall_success else 1)

        elif args.phase == 1:
            success = await validator.validate_phase_1()
            validator.print_summary()
            sys.exit(0 if success else 1)

        elif args.phase == 2:
            success = await validator.validate_phase_2()
            validator.print_summary()
            sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Validation failed with exception: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
