#!/usr/bin/env python3
"""
Graceful Degradation Test Script

Tests that the system works correctly when Supabase is unavailable:
1. Test with Supabase enabled
2. Test with Supabase disabled
3. Test with slow/timing out Supabase
4. Verify analysis completes in all cases

Usage:
    python scripts/test_graceful_degradation.py
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finwiz.supabase.client import SupabaseClient
from finwiz.supabase.services.cache_service import CacheService
from finwiz.supabase.repositories.analysis_repository import AnalysisRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GracefulDegradationTester:
    """Tests graceful degradation scenarios."""

    def __init__(self):
        """Initialize tester."""
        self.results = []

    async def test_scenario(self, name: str, test_fn) -> bool:
        """
        Run a test scenario.
        
        Args:
            name: Test scenario name
            test_fn: Async test function
            
        Returns:
            True if test passed, False otherwise
        """
        logger.info("=" * 80)
        logger.info(f"TEST: {name}")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        try:
            result = await test_fn()
            elapsed = time.time() - start_time
            
            if result:
                logger.info(f"✅ PASS: {name} (completed in {elapsed:.2f}s)")
                self.results.append({"name": name, "passed": True, "elapsed": elapsed})
                return True
            else:
                logger.error(f"❌ FAIL: {name} (completed in {elapsed:.2f}s)")
                self.results.append({"name": name, "passed": False, "elapsed": elapsed})
                return False
        
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ FAIL: {name} - Exception: {e} (after {elapsed:.2f}s)")
            self.results.append({"name": name, "passed": False, "elapsed": elapsed, "error": str(e)})
            return False

    async def test_with_supabase_enabled(self) -> bool:
        """Test with Supabase enabled (normal operation)."""
        client = SupabaseClient()
        repository = AnalysisRepository(client)
        cache_service = CacheService(repository, client)
        
        # Initialize cache
        init_result = await cache_service.initialize()
        logger.info(f"Cache initialized: {init_result}")
        
        # Test cache operation
        async def mock_execute():
            await asyncio.sleep(0.1)
            return {"test": "data", "scenario": "enabled"}
        
        result, is_cached = await cache_service.get_or_execute(
            ticker="TEST1",
            asset_class="stock",
            execute_fn=mock_execute
        )
        
        # Verify result
        success = (
            result is not None and
            isinstance(result, dict) and
            result.get("test") == "data"
        )
        
        logger.info(f"Result: {result}")
        logger.info(f"Is Cached: {is_cached}")
        logger.info(f"Cache Enabled: {cache_service.is_enabled}")
        
        return success

    async def test_with_supabase_disabled(self) -> bool:
        """Test with Supabase disabled (graceful degradation)."""
        # Create client with Supabase disabled
        original_enabled = os.getenv("SUPABASE_ENABLED")
        os.environ["SUPABASE_ENABLED"] = "false"
        
        try:
            client = SupabaseClient()
            repository = AnalysisRepository(client)
            cache_service = CacheService(repository, client)
            
            # Initialize cache (should fail gracefully)
            init_result = await cache_service.initialize()
            logger.info(f"Cache initialized: {init_result}")
            
            # Test that analysis still works
            async def mock_execute():
                await asyncio.sleep(0.1)
                return {"test": "data", "scenario": "disabled"}
            
            result, is_cached = await cache_service.get_or_execute(
                ticker="TEST2",
                asset_class="stock",
                execute_fn=mock_execute
            )
            
            # Verify result
            success = (
                result is not None and
                isinstance(result, dict) and
                result.get("test") == "data" and
                not is_cached and  # Should not be cached
                not cache_service.is_enabled  # Cache should be disabled
            )
            
            logger.info(f"Result: {result}")
            logger.info(f"Is Cached: {is_cached}")
            logger.info(f"Cache Enabled: {cache_service.is_enabled}")
            
            return success
        
        finally:
            # Restore original setting
            if original_enabled:
                os.environ["SUPABASE_ENABLED"] = original_enabled
            else:
                os.environ.pop("SUPABASE_ENABLED", None)

    async def test_with_cache_disabled_flag(self) -> bool:
        """Test with cache disabled via is_enabled flag."""
        client = SupabaseClient()
        repository = AnalysisRepository(client)
        cache_service = CacheService(repository, client)
        
        # Manually disable cache
        cache_service.is_enabled = False
        
        # Test that analysis still works
        async def mock_execute():
            await asyncio.sleep(0.1)
            return {"test": "data", "scenario": "cache_disabled"}
        
        result, is_cached = await cache_service.get_or_execute(
            ticker="TEST3",
            asset_class="stock",
            execute_fn=mock_execute
        )
        
        # Verify result
        success = (
            result is not None and
            isinstance(result, dict) and
            result.get("test") == "data" and
            not is_cached  # Should not be cached
        )
        
        logger.info(f"Result: {result}")
        logger.info(f"Is Cached: {is_cached}")
        logger.info(f"Cache Enabled: {cache_service.is_enabled}")
        
        return success

    async def test_connectivity_test_timeout(self) -> bool:
        """Test that connectivity test completes within timeout."""
        client = SupabaseClient()
        
        # Test connectivity with timeout
        start_time = time.time()
        result = await client.test_connectivity()
        elapsed = time.time() - start_time
        
        # Should complete within timeout + 1 second buffer
        timeout = client.connectivity_test_timeout
        success = elapsed <= timeout + 1.0
        
        logger.info(f"Connectivity test result: {result}")
        logger.info(f"Elapsed time: {elapsed:.2f}s")
        logger.info(f"Timeout: {timeout}s")
        logger.info(f"Within timeout: {success}")
        
        return success

    async def test_cache_write_non_blocking(self) -> bool:
        """Test that cache writes don't block analysis."""
        client = SupabaseClient()
        repository = AnalysisRepository(client)
        cache_service = CacheService(repository, client)
        
        # Initialize cache
        await cache_service.initialize()
        
        # Test that get_or_execute returns quickly
        async def mock_execute():
            await asyncio.sleep(0.1)
            return {"test": "data", "scenario": "non_blocking"}
        
        start_time = time.time()
        result, is_cached = await cache_service.get_or_execute(
            ticker="TEST4",
            asset_class="stock",
            execute_fn=mock_execute
        )
        elapsed = time.time() - start_time
        
        # Should complete quickly (< 1 second)
        # Cache write happens asynchronously in background
        success = elapsed < 1.0 and result is not None
        
        logger.info(f"Result: {result}")
        logger.info(f"Elapsed time: {elapsed:.3f}s")
        logger.info(f"Non-blocking: {success}")
        
        # Wait a bit for background write to complete
        await asyncio.sleep(0.5)
        
        return success

    async def test_circuit_breaker_state(self) -> bool:
        """Test circuit breaker state management."""
        client = SupabaseClient()
        
        # Check initial state
        is_open = client.circuit_breaker.is_open()
        logger.info(f"Circuit breaker initial state: {'OPEN' if is_open else 'CLOSED'}")
        
        # Test that we can check state without errors
        success = isinstance(is_open, bool)
        
        # Get health status
        health = client.get_health_status()
        logger.info(f"Health status: Available={health.is_available}, CB Open={health.circuit_breaker_open}")
        
        return success

    async def run_all_tests(self) -> bool:
        """
        Run all graceful degradation tests.
        
        Returns:
            True if all tests passed, False otherwise
        """
        logger.info("=" * 80)
        logger.info("GRACEFUL DEGRADATION TEST SUITE")
        logger.info("=" * 80)
        
        tests = [
            ("Supabase Enabled", self.test_with_supabase_enabled),
            ("Supabase Disabled", self.test_with_supabase_disabled),
            ("Cache Disabled Flag", self.test_with_cache_disabled_flag),
            ("Connectivity Test Timeout", self.test_connectivity_test_timeout),
            ("Cache Write Non-Blocking", self.test_cache_write_non_blocking),
            ("Circuit Breaker State", self.test_circuit_breaker_state),
        ]
        
        all_passed = True
        for name, test_fn in tests:
            passed = await self.test_scenario(name, test_fn)
            if not passed:
                all_passed = False
        
        # Print summary
        self.print_summary()
        
        return all_passed

    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        
        if failed > 0:
            logger.info("\nFailed Tests:")
            for result in self.results:
                if not result["passed"]:
                    error = result.get("error", "Unknown error")
                    logger.info(f"  ❌ {result['name']}: {error}")
        
        logger.info("\nTest Results:")
        for result in self.results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            logger.info(f"  {status}: {result['name']} ({result['elapsed']:.2f}s)")
        
        if passed == total:
            logger.info("\n✅ ALL TESTS PASSED")
        else:
            logger.info(f"\n❌ {failed} TEST(S) FAILED")
        
        logger.info("=" * 80)


async def main():
    """Main test entry point."""
    tester = GracefulDegradationTester()
    
    try:
        all_passed = await tester.run_all_tests()
        sys.exit(0 if all_passed else 1)
    
    except Exception as e:
        logger.error(f"Test suite failed with exception: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
