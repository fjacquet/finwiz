"""
Performance tests for Core Analysis functionality.

Tests the performance characteristics of core analysis crews including
execution time, memory usage, and scalability.
"""

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from finwiz.main import FinwizFlow


class TestCoreAnalysisPerformance:
    """Test cases for Core Analysis Performance."""

    @pytest.fixture
    def performance_inputs(self):
        """Create inputs optimized for performance testing."""
        today = datetime.now()
        return {
            "current_day": today.day,
            "current_month": today.month,
            "current_year": today.year,
            "current_date": today.strftime("%Y-%m-%d"),
            "full_date": today.strftime("%B %d, %Y"),
            "timestamp": today.strftime("%Y-%m-%d %H:%M:%S"),
            "report_language": "en",  # English for faster processing
            "has_existing_session": False,
            "session_id": "",
            "analysis_count": 0,
        }

    @pytest.fixture
    def mock_fast_crew_results(self):
        """Create mock crew results optimized for performance testing."""
        return {
            "stock": MagicMock(raw="Fast stock analysis: BUY AAPL"),
            "etf": MagicMock(raw="Fast ETF analysis: BUY SPY"),
            "crypto": MagicMock(raw="Fast crypto analysis: HOLD BTC"),
        }

    def test_should_execute_single_crew_within_time_limit(self, performance_inputs):
        """Test that a single crew executes within acceptable time limits."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                # Mock fast crew execution
                mock_stock_crew = MagicMock()
                mock_result = MagicMock()
                mock_result.raw = "Fast stock analysis"
                mock_stock_crew.crew().kickoff.return_value = mock_result
                mock_stock_crew_class.return_value = mock_stock_crew

                flow = FinwizFlow()

                # Measure execution time
                start_time = time.time()
                flow.check_stock()
                execution_time = time.time() - start_time

                # Verify execution time is reasonable (< 5 seconds for mocked execution)
                assert execution_time < 5.0, f"Stock crew execution took {execution_time:.2f}s, expected < 5.0s"

    def test_should_execute_all_crews_in_parallel_efficiently(self, performance_inputs, mock_fast_crew_results):
        """Test that all crews can execute efficiently when run in parallel."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with (
                patch("finwiz.main.StockCrew") as mock_stock_crew_class,
                patch("finwiz.main.EtfCrew") as mock_etf_crew_class,
                patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class,
            ):
                # Mock crew instances with fast execution
                mock_stock_crew = MagicMock()
                mock_stock_crew.crew().kickoff.return_value = mock_fast_crew_results["stock"]
                mock_stock_crew_class.return_value = mock_stock_crew

                mock_etf_crew = MagicMock()
                mock_etf_crew.crew().kickoff.return_value = mock_fast_crew_results["etf"]
                mock_etf_crew_class.return_value = mock_etf_crew

                mock_crypto_crew = MagicMock()
                mock_crypto_crew.crew().kickoff.return_value = mock_fast_crew_results["crypto"]
                mock_crypto_crew_class.return_value = mock_crypto_crew

                flow = FinwizFlow()

                # Measure total execution time for all crews
                start_time = time.time()

                # Execute all crews (in real scenario these would run in parallel)
                flow.check_stock()
                flow.check_etf()
                flow.check_crypto()

                total_execution_time = time.time() - start_time

                # Verify total execution time is reasonable
                assert total_execution_time < 10.0, f"All crews execution took {total_execution_time:.2f}s, expected < 10.0s"

                # Verify all crews were executed
                mock_stock_crew.crew().kickoff.assert_called_once()
                mock_etf_crew.crew().kickoff.assert_called_once()
                mock_crypto_crew.crew().kickoff.assert_called_once()

    def test_should_handle_large_input_datasets_efficiently(self, performance_inputs):
        """Test that crews handle large input datasets efficiently."""
        # Create large input dataset
        large_inputs = {
            **performance_inputs,
            "portfolio_holdings": [
                {"symbol": f"STOCK{i}", "shares": 100, "cost_basis": 50.0}
                for i in range(1000)  # 1000 holdings
            ],
            "watchlist": [f"TICKER{i}" for i in range(500)],  # 500 tickers
            "market_data": {
                f"SYMBOL{i}": {"price": 100.0, "volume": 1000000}
                for i in range(200)  # 200 symbols
            },
        }

        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                mock_stock_crew = MagicMock()
                mock_result = MagicMock()
                mock_result.raw = "Analysis of large dataset completed"
                mock_stock_crew.crew().kickoff.return_value = mock_result
                mock_stock_crew_class.return_value = mock_stock_crew

                flow = FinwizFlow()
                flow.inputs.update(large_inputs)

                # Measure execution time with large dataset
                start_time = time.time()
                flow.check_stock()
                execution_time = time.time() - start_time

                # Should still execute within reasonable time even with large dataset
                assert execution_time < 8.0, f"Large dataset execution took {execution_time:.2f}s, expected < 8.0s"

    def test_should_maintain_memory_efficiency(self, performance_inputs):
        """Test that crew execution maintains memory efficiency."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                mock_stock_crew = MagicMock()
                mock_result = MagicMock()
                mock_result.raw = "Memory efficient analysis"
                mock_stock_crew.crew().kickoff.return_value = mock_result
                mock_stock_crew_class.return_value = mock_stock_crew

                flow = FinwizFlow()

                # Execute crew multiple times to test memory leaks
                for _ in range(10):
                    flow.check_stock()

                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = final_memory - initial_memory

                # Memory increase should be reasonable (< 100MB for mocked execution)
                assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB, expected < 100MB"

    def test_should_handle_concurrent_crew_executions(self, performance_inputs):
        """Test that system handles concurrent crew executions efficiently."""
        import queue
        import threading

        results_queue = queue.Queue()
        execution_times = []

        def execute_crew(crew_type):
            """Execute a crew and measure time."""
            with patch("finwiz.main.is_feature_enabled", return_value=True):
                if crew_type == "stock":
                    with patch("finwiz.main.StockCrew") as mock_crew_class:
                        mock_crew = MagicMock()
                        mock_result = MagicMock()
                        mock_result.raw = f"Concurrent {crew_type} analysis"
                        mock_crew.crew().kickoff.return_value = mock_result
                        mock_crew_class.return_value = mock_crew

                        flow = FinwizFlow()
                        start_time = time.time()
                        flow.check_stock()
                        execution_time = time.time() - start_time

                        results_queue.put((crew_type, execution_time))

        # Create threads for concurrent execution
        threads = []
        for i in range(3):  # 3 concurrent executions
            thread = threading.Thread(target=execute_crew, args=("stock",))
            threads.append(thread)

        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Collect results
        while not results_queue.empty():
            crew_type, exec_time = results_queue.get()
            execution_times.append(exec_time)

        # Verify concurrent execution completed efficiently
        assert len(execution_times) == 3
        assert total_time < 15.0, f"Concurrent execution took {total_time:.2f}s, expected < 15.0s"
        assert all(t < 8.0 for t in execution_times), "Individual executions took too long"

    def test_should_optimize_data_integration_performance(self, performance_inputs):
        """Test that data integration system performs efficiently."""
        from finwiz.integration.manager import CrewDataIntegrationManager

        integration_manager = CrewDataIntegrationManager()

        # Test storing multiple crew outputs efficiently
        crew_outputs = {}
        for i in range(100):  # 100 crew outputs
            crew_outputs[f"crew_{i}"] = {
                "analysis": f"Analysis {i}",
                "recommendation": "BUY",
                "risk_score": 5,
                "confidence": 0.8,
                "timestamp": datetime.now().isoformat(),
            }

        # Measure storage performance
        start_time = time.time()
        for crew_name, output in crew_outputs.items():
            integration_manager.store_crew_output(crew_name, output)
        storage_time = time.time() - start_time

        # Measure retrieval performance
        start_time = time.time()
        for crew_name in crew_outputs.keys():
            retrieved_output = integration_manager.get_crew_output(crew_name)
            assert retrieved_output is not None
        retrieval_time = time.time() - start_time

        # Verify performance is acceptable
        assert storage_time < 2.0, f"Storage took {storage_time:.2f}s, expected < 2.0s"
        assert retrieval_time < 1.0, f"Retrieval took {retrieval_time:.2f}s, expected < 1.0s"

    def test_should_handle_error_scenarios_efficiently(self, performance_inputs):
        """Test that error handling doesn't significantly impact performance."""
        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with patch("finwiz.main.StockCrew") as mock_stock_crew_class:
                # Mock crew that fails
                mock_stock_crew = MagicMock()
                mock_stock_crew.crew().kickoff.side_effect = Exception("Simulated failure")
                mock_stock_crew_class.return_value = mock_stock_crew

                flow = FinwizFlow()

                # Mock error handler for fast fallback
                mock_fallback_response = MagicMock()
                mock_fallback_response.success = False
                mock_fallback_response.message = "Fast fallback"
                mock_fallback_response.fallback_strategy = "skip"
                mock_fallback_response.degraded_functionality = []
                flow.error_handler.handle_crew_failure.return_value = mock_fallback_response

                # Measure error handling performance
                start_time = time.time()
                flow.check_stock()  # This should fail and trigger error handling
                error_handling_time = time.time() - start_time

                # Error handling should be fast
                assert error_handling_time < 3.0, f"Error handling took {error_handling_time:.2f}s, expected < 3.0s"

                # Verify error was handled
                assert flow.inputs["stock_analysis_success"] is False
                assert flow.inputs["stock_analysis_fallback"] is True

    def test_should_scale_with_feature_flag_combinations(self, performance_inputs):
        """Test that performance scales properly with different feature flag combinations."""
        feature_combinations = [
            {"stock_analysis": True, "etf_analysis": False, "crypto_analysis": False},
            {"stock_analysis": True, "etf_analysis": True, "crypto_analysis": False},
            {"stock_analysis": True, "etf_analysis": True, "crypto_analysis": True},
        ]

        execution_times = []

        for feature_flags in feature_combinations:

            def mock_feature_enabled(feature_name):
                return feature_flags.get(feature_name, False)

            with patch("finwiz.main.is_feature_enabled", side_effect=mock_feature_enabled):
                with (
                    patch("finwiz.main.StockCrew") as mock_stock_crew_class,
                    patch("finwiz.main.EtfCrew") as mock_etf_crew_class,
                    patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class,
                ):
                    # Mock all crews
                    for mock_crew_class in [mock_stock_crew_class, mock_etf_crew_class, mock_crypto_crew_class]:
                        mock_crew = MagicMock()
                        mock_result = MagicMock()
                        mock_result.raw = "Fast analysis"
                        mock_crew.crew().kickoff.return_value = mock_result
                        mock_crew_class.return_value = mock_crew

                    flow = FinwizFlow()

                    # Measure execution time
                    start_time = time.time()
                    flow.check_stock()
                    flow.check_etf()
                    flow.check_crypto()
                    execution_time = time.time() - start_time

                    execution_times.append(execution_time)

        # Verify execution times scale reasonably
        assert len(execution_times) == 3

        # More crews should take more time, but not excessively
        assert execution_times[0] < execution_times[1] < execution_times[2]
        assert execution_times[2] < 12.0, f"Full execution took {execution_times[2]:.2f}s, expected < 12.0s"

    def test_should_optimize_flow_initialization(self):
        """Test that flow initialization is optimized for performance."""
        # Measure flow initialization time
        initialization_times = []

        for _ in range(10):  # Test multiple initializations
            start_time = time.time()
            flow = FinwizFlow()
            initialization_time = time.time() - start_time
            initialization_times.append(initialization_time)

        # Verify initialization is fast and consistent
        avg_init_time = sum(initialization_times) / len(initialization_times)
        max_init_time = max(initialization_times)

        assert avg_init_time < 1.0, f"Average initialization took {avg_init_time:.2f}s, expected < 1.0s"
        assert max_init_time < 2.0, f"Maximum initialization took {max_init_time:.2f}s, expected < 2.0s"

    @pytest.mark.slow
    def test_should_handle_stress_test_scenario(self, performance_inputs):
        """Stress test with multiple crews and large datasets."""
        # This test is marked as slow and may be skipped in regular test runs

        # Create stress test inputs
        stress_inputs = {
            **performance_inputs,
            "portfolio_holdings": [
                {"symbol": f"STOCK{i}", "shares": 100, "cost_basis": 50.0}
                for i in range(5000)  # 5000 holdings
            ],
            "watchlist": [f"TICKER{i}" for i in range(2000)],  # 2000 tickers
        }

        with patch("finwiz.main.is_feature_enabled", return_value=True):
            with (
                patch("finwiz.main.StockCrew") as mock_stock_crew_class,
                patch("finwiz.main.EtfCrew") as mock_etf_crew_class,
                patch("finwiz.main.CryptoCrew") as mock_crypto_crew_class,
            ):
                # Mock crews with realistic delays
                for mock_crew_class in [mock_stock_crew_class, mock_etf_crew_class, mock_crypto_crew_class]:
                    mock_crew = MagicMock()
                    mock_result = MagicMock()
                    mock_result.raw = "Stress test analysis completed"

                    def slow_kickoff(*args, **kwargs):
                        time.sleep(0.1)  # Simulate some processing time
                        return mock_result

                    mock_crew.crew().kickoff.side_effect = slow_kickoff
                    mock_crew_class.return_value = mock_crew

                flow = FinwizFlow()
                flow.inputs.update(stress_inputs)

                # Measure stress test execution
                start_time = time.time()
                flow.check_stock()
                flow.check_etf()
                flow.check_crypto()
                stress_test_time = time.time() - start_time

                # Should complete within reasonable time even under stress
                assert stress_test_time < 30.0, f"Stress test took {stress_test_time:.2f}s, expected < 30.0s"

                # Verify all crews completed successfully
                assert "stock_analysis_result" in flow.inputs
                assert "etf_analysis_result" in flow.inputs
                assert "crypto_analysis_result" in flow.inputs
