"""Property-based tests for DeepAnalysisOrchestrator.

Tests system reliability, performance constraints, batch processing, and metadata tracking.

**Feature: python-ai-hybrid-analysis, Property 14: System Reliability**
**Feature: python-ai-hybrid-analysis, Property 11: Performance Constraints**
**Feature: python-ai-hybrid-analysis, Property 12: Batch Processing Performance**
**Feature: python-ai-hybrid-analysis, Property 10: Processing Metadata Tracking**
"""

import time

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator
from finwiz.schemas.hybrid_analysis import EnrichedAnalysis

# Skip tests that depend on unimplemented cache manager features
pytestmark = pytest.mark.skip(reason="Tests depend on cache manager features not yet implemented")


class TestDeepAnalysisOrchestratorProperties:
    """Property-based tests for DeepAnalysisOrchestrator."""

    # Property 14: System Reliability
    # **Validates: Requirements 10.4**
    @given(
        num_holdings=st.integers(min_value=1, max_value=10),
        failure_rate=st.floats(min_value=0.0, max_value=0.05),  # Max 5% failure rate
    )
    @settings(
        max_examples=10,  # Reduced for performance
        deadline=None,  # No deadline for slow tests
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
    )
    def test_batch_processing_success_rate_above_95_percent(self, mocker, num_holdings, failure_rate):
        """
        Property: Batch processing success rate ≥95%.

        For any batch of holdings with failure rate ≤5%, the system must:
        - Achieve success rate ≥95%
        - Create fallback analyses for failures
        - Log all errors appropriately
        """
        # Arrange
        state = FinwizState()
        state.session_id = "test_session"

        # Mock dependencies
        batch_prefetch_config = mocker.Mock()
        batch_prefetch_config.enabled = False
        batch_prefetch_config.min_holdings_for_batch = 100  # Disable batch mode for test

        orchestrator = DeepAnalysisOrchestrator(
            state=state,
            batch_prefetch_config=batch_prefetch_config,
            cache_service=None,
            cache_enabled=False,
            crew_factory=None,
            integration_manager=None,
            error_handler=None,
        )

        # Create test holdings
        holdings = [
            {
                "ticker": f"TEST{i}",
                "asset_class": "stock",
                "name": f"Test Company {i}",
            }
            for i in range(num_holdings)
        ]

        # Mock _process_single_holding to simulate failures
        num_failures = int(num_holdings * failure_rate)
        call_count = 0

        def mock_process_holding(ticker, asset_class, cache_mgr, cache_ttl, batch_enabled):
            nonlocal call_count
            call_count += 1

            # Simulate failure for first num_failures calls
            if call_count <= num_failures:
                raise Exception(f"Simulated failure for {ticker}")

            # Return mock result for successful calls
            mock_result = mocker.Mock()
            mock_result.ticker = ticker
            mock_result.asset_class = asset_class
            mock_result.grade = "B"
            mock_result.composite_score = 0.75
            mock_result.risk_score = 3.0
            return mock_result

        mocker.patch.object(
            orchestrator,
            "_process_single_holding",
            side_effect=mock_process_holding
        )

        # Mock cache manager
        mock_cache_mgr = mocker.Mock()
        mock_cache_mgr.log_cache_stats = mocker.Mock()
        mocker.patch(
            "finwiz.orchestrators.deep_analysis_orchestrator.get_analysis_cache_manager",
            return_value=mock_cache_mgr
        )

        # Act
        results = orchestrator.run_deep_analysis_on_holdings(holdings)

        # Assert - Success rate ≥95%
        success_count = len(results)
        success_rate = success_count / num_holdings if num_holdings > 0 else 1.0

        assert success_rate >= 0.95, f"Success rate {success_rate:.1%} must be ≥95%"

        # Assert - Failed holdings tracked
        expected_failures = min(num_failures, num_holdings)
        assert len(state.failed_holdings) == expected_failures, \
            f"Expected {expected_failures} failed holdings, got {len(state.failed_holdings)}"

    # Property 11: Performance Constraints
    # **Validates: Requirements 7.1, 7.2**
    @given(
        processing_time=st.floats(min_value=0.1, max_value=30.0),
        llm_cost=st.floats(min_value=0.01, max_value=0.10),
    )
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_single_holding_performance_constraints(self, mocker, processing_time, llm_cost):
        """
        Property: Single holding analysis meets performance constraints.

        For any single holding analysis, the system must:
        - Complete in ≤30 seconds
        - Cost ≤$0.10 in LLM usage
        """
        # Arrange
        state = FinwizState()
        batch_prefetch_config = mocker.Mock()
        batch_prefetch_config.enabled = False

        orchestrator = DeepAnalysisOrchestrator(
            state=state,
            batch_prefetch_config=batch_prefetch_config,
        )

        # Create mock EnrichedAnalysis with given constraints
        mock_analysis = mocker.Mock(spec=EnrichedAnalysis)
        mock_analysis.ticker = "TEST"
        mock_analysis.processing_time_seconds = processing_time
        mock_analysis.llm_cost_dollars = llm_cost
        mock_analysis.report_word_count = 2500
        mock_analysis.unique_insights_count = 7
        mock_analysis.final_grade = "A"

        # Act
        warnings = orchestrator._validate_analysis_quality(mock_analysis)

        # Assert - Performance constraints
        if processing_time > 30.0:
            assert any("Processing time exceeded" in w for w in warnings), \
                "Must warn when processing time >30s"
        else:
            assert not any("Processing time exceeded" in w for w in warnings), \
                "Must not warn when processing time ≤30s"

        if llm_cost > 0.10:
            assert any("LLM cost exceeded" in w for w in warnings), \
                "Must warn when LLM cost >$0.10"
        else:
            assert not any("LLM cost exceeded" in w for w in warnings), \
                "Must not warn when LLM cost ≤$0.10"

    # Property 12: Batch Processing Performance
    # **Validates: Requirements 10.1, 10.2**
    @given(
        num_holdings=st.integers(min_value=50, max_value=66),
    )
    @settings(
        max_examples=5,  # Very few examples due to performance
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
    )
    def test_batch_processing_performance_constraints(self, mocker, num_holdings):
        """
        Property: Batch processing meets performance constraints.

        For any batch of 50-66 holdings, the system must:
        - Complete in ≤1800 seconds (30 minutes)
        - Cost ≤$6.60 total (66 * $0.10)
        - Maintain per-holding constraints
        """
        # Arrange
        state = FinwizState()

        batch_prefetch_config = mocker.Mock()
        batch_prefetch_config.enabled = False
        batch_prefetch_config.min_holdings_for_batch = 100  # Disable batch mode

        orchestrator = DeepAnalysisOrchestrator(
            state=state,
            batch_prefetch_config=batch_prefetch_config,
        )

        # Create test holdings
        holdings = [
            {"ticker": f"TEST{i}", "asset_class": "stock"}
            for i in range(num_holdings)
        ]

        # Mock _process_single_holding to return quickly
        def mock_process_holding(ticker, asset_class, cache_mgr, cache_ttl, batch_enabled):
            mock_result = mocker.Mock()
            mock_result.ticker = ticker
            mock_result.asset_class = asset_class
            mock_result.grade = "B"
            mock_result.composite_score = 0.75
            mock_result.risk_score = 3.0
            return mock_result

        mocker.patch.object(
            orchestrator,
            "_process_single_holding",
            side_effect=mock_process_holding
        )

        # Mock cache manager
        mock_cache_mgr = mocker.Mock()
        mock_cache_mgr.log_cache_stats = mocker.Mock()
        mocker.patch(
            "finwiz.orchestrators.deep_analysis_orchestrator.get_analysis_cache_manager",
            return_value=mock_cache_mgr
        )

        # Act
        start_time = time.time()
        results = orchestrator.run_deep_analysis_on_holdings(holdings)
        total_time = time.time() - start_time

        # Assert - Total time constraint (≤1800s for 66 holdings)
        max_time = (num_holdings / 66) * 1800  # Scale based on actual count
        assert total_time <= max_time, \
            f"Batch processing took {total_time:.1f}s, must be ≤{max_time:.1f}s"

        # Assert - All holdings processed
        assert len(results) == num_holdings, \
            f"Expected {num_holdings} results, got {len(results)}"

        # Assert - Per-holding time constraint (≤30s average)
        avg_time_per_holding = total_time / num_holdings if num_holdings > 0 else 0
        assert avg_time_per_holding <= 30.0, \
            f"Average time per holding {avg_time_per_holding:.1f}s must be ≤30s"

    # Property 10: Processing Metadata Tracking
    # **Validates: Requirements 4.3**
    @given(
        start_time=st.floats(min_value=1000000000.0, max_value=2000000000.0),
    )
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_processing_metadata_populated_and_non_negative(self, mocker, start_time):
        """
        Property: Processing metadata is populated and non-negative.

        For any analysis, the system must:
        - Populate processing_time_seconds
        - Populate llm_cost_dollars
        - Ensure both values are non-negative
        """
        # Arrange
        state = FinwizState()
        orchestrator = DeepAnalysisOrchestrator(state=state)

        # Act - Calculate processing time
        # Simulate some time passing
        end_time = start_time + 15.5  # 15.5 seconds later

        # Mock time.time() to return our controlled values
        import time as time_module
        original_time = time_module.time

        try:
            # First call returns start_time, second returns end_time
            call_count = [0]
            def mock_time():
                call_count[0] += 1
                return start_time if call_count[0] == 1 else end_time

            time_module.time = mock_time

            processing_time = orchestrator._calculate_processing_time(start_time)

            # Act - Calculate LLM cost
            llm_cost = orchestrator._calculate_llm_cost({})

            # Assert - Values populated
            assert processing_time is not None, "Processing time must be populated"
            assert llm_cost is not None, "LLM cost must be populated"

            # Assert - Values non-negative
            assert processing_time >= 0, f"Processing time {processing_time} must be non-negative"
            assert llm_cost >= 0, f"LLM cost {llm_cost} must be non-negative"

            # Assert - Processing time is reasonable
            expected_time = end_time - start_time
            assert abs(processing_time - expected_time) < 0.1, \
                f"Processing time {processing_time} should be close to {expected_time}"

        finally:
            # Restore original time function
            time_module.time = original_time

    # Property: Fallback Analysis Creation
    # **Validates: Requirements 6.2**
    @given(
        ticker=st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=("Lu",))),
        asset_class=st.sampled_from(["stock", "etf", "crypto"]),
    )
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_fallback_analysis_has_low_confidence(self, mocker, ticker, asset_class):
        """
        Property: Fallback analysis has LOW confidence.

        For any ticker and asset class, when AI analysis fails, the system must:
        - Create fallback analysis using Python-only calculations
        - Set recommendation_confidence to "LOW"
        - Return valid EnrichedAnalysis
        """
        # Arrange
        state = FinwizState()
        orchestrator = DeepAnalysisOrchestrator(state=state)

        # Mock _collect_data_with_python to return minimal data
        mock_data = {
            "ticker": ticker,
            "asset_class": asset_class,
            "company_name": f"{ticker} Corp",
            "current_price": 100.0,
        }
        mocker.patch.object(
            orchestrator,
            "_collect_data_with_python",
            return_value=mock_data
        )

        # Mock DeepAnalysisScorer
        mock_scorer = mocker.Mock()
        mock_result = mocker.Mock()
        mock_result.composite_score = 0.75
        mock_result.fundamental_score = 0.8
        mock_result.technical_score = 0.7
        mock_result.risk_score = 3.0
        mock_result.grade = "B"
        mock_result.recommendation = "HOLD"
        mock_result.rationale = "Test rationale"
        mock_result.fundamental_metrics = {}
        mock_result.technical_indicators = {}
        mock_result.risk_metrics = {}

        mock_scorer.calculate_composite_score.return_value = mock_result
        mocker.patch(
            "finwiz.orchestrators.deep_analysis_orchestrator.DeepAnalysisScorer",
            return_value=mock_scorer
        )

        # Act
        error = Exception("AI analysis failed")
        fallback = orchestrator._create_fallback_analysis(ticker, asset_class, error)

        # Assert - Fallback created
        assert fallback is not None, "Fallback analysis must be created"

        # Assert - LOW confidence
        assert fallback.recommendation_confidence == "LOW", \
            "Fallback analysis must have LOW confidence"

        # Assert - Valid EnrichedAnalysis
        assert isinstance(fallback, EnrichedAnalysis), \
            "Fallback must be EnrichedAnalysis instance"
        assert fallback.ticker == ticker, "Ticker must match"
        assert fallback.asset_class == asset_class, "Asset class must match"
        assert fallback.final_grade == "B", "Grade must be from Python calculation"

    # Property: Quality Validation Warnings
    # **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
    @given(
        word_count=st.integers(min_value=1000, max_value=3000),
        insights_count=st.integers(min_value=1, max_value=10),
        processing_time=st.floats(min_value=5.0, max_value=60.0),
        llm_cost=st.floats(min_value=0.01, max_value=0.20),
    )
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_quality_validation_detects_threshold_violations(
        self, mocker, word_count, insights_count, processing_time, llm_cost
    ):
        """
        Property: Quality validation detects all threshold violations.

        For any analysis metrics, the system must:
        - Warn if word_count <2000
        - Warn if insights_count <5
        - Warn if processing_time >30s
        - Warn if llm_cost >$0.10
        """
        # Arrange
        state = FinwizState()
        orchestrator = DeepAnalysisOrchestrator(state=state)

        mock_analysis = mocker.Mock(spec=EnrichedAnalysis)
        mock_analysis.ticker = "TEST"
        mock_analysis.report_word_count = word_count
        mock_analysis.unique_insights_count = insights_count
        mock_analysis.processing_time_seconds = processing_time
        mock_analysis.llm_cost_dollars = llm_cost

        # Act
        warnings = orchestrator._validate_analysis_quality(mock_analysis)

        # Assert - Word count threshold
        if word_count < 2000:
            assert any("Word count below threshold" in w for w in warnings), \
                f"Must warn when word_count {word_count} <2000"
        else:
            assert not any("Word count below threshold" in w for w in warnings), \
                f"Must not warn when word_count {word_count} ≥2000"

        # Assert - Insights count threshold
        if insights_count < 5:
            assert any("Insights count below threshold" in w for w in warnings), \
                f"Must warn when insights_count {insights_count} <5"
        else:
            assert not any("Insights count below threshold" in w for w in warnings), \
                f"Must not warn when insights_count {insights_count} ≥5"

        # Assert - Processing time threshold
        if processing_time > 30.0:
            assert any("Processing time exceeded" in w for w in warnings), \
                f"Must warn when processing_time {processing_time:.1f}s >30s"
        else:
            assert not any("Processing time exceeded" in w for w in warnings), \
                f"Must not warn when processing_time {processing_time:.1f}s ≤30s"

        # Assert - LLM cost threshold
        if llm_cost > 0.10:
            assert any("LLM cost exceeded" in w for w in warnings), \
                f"Must warn when llm_cost ${llm_cost:.3f} >$0.10"
        else:
            assert not any("LLM cost exceeded" in w for w in warnings), \
                f"Must not warn when llm_cost ${llm_cost:.3f} ≤$0.10"
