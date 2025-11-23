"""
Performance benchmark tests for hybrid analysis architecture.

Tests validate that the system meets performance requirements:
- Single holding: ≤30s, ≤$0.10
- Batch processing: Scales appropriately

Note: These tests use mocked data to avoid external API calls and LLM costs.
"""

import time

import pytest

from finwiz.flows.hybrid_analysis_flow import HybridAnalysisFlow
from finwiz.schemas.hybrid_analysis.enriched import EnrichedAnalysis


class TestSingleHoldingPerformance:
    """Test performance requirements for single holding analysis."""

    def test_should_complete_single_holding_within_30_seconds(self, mock_hybrid_flow_complete):
        """
        Test that single holding analysis completes within 30 seconds.

        **Validates: Requirements 3.4**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Apple Inc."

        # Act
        start_time = time.time()
        result = flow.kickoff()
        elapsed_time = time.time() - start_time

        # Assert
        assert elapsed_time <= 30.0, f"Analysis took {elapsed_time:.2f}s, exceeds 30s limit"
        assert isinstance(result, EnrichedAnalysis)

    def test_should_limit_llm_cost_to_10_cents(self, mock_hybrid_flow_complete):
        """
        Test that LLM cost per holding is ≤$0.10.

        **Validates: Requirements 3.2**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Apple Inc."

        # Act
        result = flow.kickoff()

        # Assert
        assert result.llm_cost_dollars <= 0.10, f"LLM cost ${result.llm_cost_dollars:.4f} exceeds $0.10 limit"


class TestBatchProcessingPerformance:
    """Test performance requirements for batch processing."""

    @pytest.mark.parametrize("batch_size", [10])
    def test_should_process_batch_within_time_limit(self, batch_size, mock_hybrid_flow_complete):
        """
        Test batch processing completes within expected time limits.

        Time limits:
        - 10 holdings: ≤300s (30s * 10)

        **Validates: Requirements 10.1, 10.2**
        """
        # Arrange
        tickers = [f"TICK{i:02d}" for i in range(batch_size)]
        max_time = batch_size * 30.0  # 30s per holding

        # Act
        start_time = time.time()
        results = []
        for ticker in tickers:
            flow = HybridAnalysisFlow()
            flow.state.ticker = ticker
            flow.state.asset_class = "stock"
            flow.state.company_name = f"{ticker} Corp"
            result = flow.kickoff()
            results.append(result)
        elapsed_time = time.time() - start_time

        # Assert
        assert elapsed_time <= max_time, f"Batch of {batch_size} took {elapsed_time:.2f}s, exceeds {max_time:.2f}s limit"
        assert len(results) == batch_size


class TestPerformanceMetrics:
    """Test that performance metrics are tracked correctly."""

    def test_should_track_processing_time(self, mock_hybrid_flow_complete):
        """
        Test that processing time is tracked and non-negative.

        **Validates: Requirements 4.3**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Apple Inc."

        # Act
        result = flow.kickoff()

        # Assert
        assert result.processing_time_seconds > 0, "Processing time must be positive"
        assert result.processing_time_seconds <= 30.0, "Processing time exceeds 30s limit"

    def test_should_track_llm_cost(self, mock_hybrid_flow_complete):
        """
        Test that LLM cost is tracked and non-negative.

        **Validates: Requirements 4.3**
        """
        # Arrange
        flow = HybridAnalysisFlow()
        flow.state.ticker = "AAPL"
        flow.state.asset_class = "stock"
        flow.state.company_name = "Apple Inc."

        # Act
        result = flow.kickoff()

        # Assert
        assert result.llm_cost_dollars >= 0, "LLM cost must be non-negative"
        assert result.llm_cost_dollars <= 0.10, "LLM cost exceeds $0.10 limit"
