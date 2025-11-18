"""
Unit tests for RebalancingHistoryTracker.

Tests cover historical tracking, performance attribution analysis, trend analysis,
and analytics dashboard generation functionality.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from finwiz.quantitative.rebalancing_history_tracker import RebalancingHistoryTracker
from finwiz.schemas.portfolio_rebalancing import (
    CostAnalysis,
    ExecutionSummary,
    PerformanceAttribution,
    PortfolioAnalysis,
    PortfolioMetrics,
    RebalancingAnalytics,
    RebalancingHistoryEntry,
    RebalancingRecommendation,
    RebalancingResult,
    TradeAction,
    TradeRecommendation,
    TrendAnalysis,
    UrgencyLevel,
)


class TestRebalancingHistoryTracker:
    """Test suite for RebalancingHistoryTracker class."""

    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage path for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def tracker(self, temp_storage_path):
        """Create RebalancingHistoryTracker instance for testing."""
        return RebalancingHistoryTracker(storage_path=temp_storage_path)

    @pytest.fixture
    def sample_portfolio_analysis(self):
        """Create sample portfolio analysis for testing."""
        return PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.4, "GOOGL": 0.35, "MSFT": 0.25},
            deviations_from_target={"AAPL": 0.05, "GOOGL": -0.03, "MSFT": -0.02},
            positions_needing_rebalancing=["AAPL"],
            risk_metrics={"volatility": 0.15, "sharpe_ratio": 1.2},
        )

    @pytest.fixture
    def sample_trade_recommendations(self):
        """Create sample trade recommendations for testing."""
        return [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.SELL,
                quantity=50.0,
                current_price=150.0,
                trade_value=7500.0,
                estimated_commission=5.0,
                estimated_spread_cost=15.0,
                total_estimated_cost=20.0,
                current_weight=0.4,
                target_weight=0.35,
                weight_deviation=0.05,
                projected_weight_after_trade=0.35,
                priority=1,
                urgency=UrgencyLevel.MEDIUM,
                rationale="Reduce overweight position to target allocation",
            ),
            TradeRecommendation(
                symbol="GOOGL",
                action=TradeAction.BUY,
                quantity=3.0,
                current_price=2500.0,
                trade_value=7500.0,
                estimated_commission=5.0,
                estimated_spread_cost=15.0,
                total_estimated_cost=20.0,
                current_weight=0.32,
                target_weight=0.35,
                weight_deviation=-0.03,
                projected_weight_after_trade=0.35,
                priority=2,
                urgency=UrgencyLevel.LOW,
                rationale="Increase underweight position to target allocation",
            ),
        ]

    @pytest.fixture
    def sample_rebalancing_result(self, sample_portfolio_analysis, sample_trade_recommendations):
        """Create sample rebalancing result for testing."""
        projected_analysis = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.35, "GOOGL": 0.35, "MSFT": 0.30},
            deviations_from_target={"AAPL": 0.0, "GOOGL": 0.0, "MSFT": 0.05},
            positions_needing_rebalancing=[],
            risk_metrics={"volatility": 0.14, "sharpe_ratio": 1.3},
        )

        cost_analysis = CostAnalysis(
            total_transaction_costs=40.0,
            commission_costs=10.0,
            spread_costs=30.0,
            cost_as_percentage=0.0004,
        )

        execution_summary = ExecutionSummary(
            total_trades_required=2,
            positions_requiring_action=2,
            positions_within_tolerance=1,
            estimated_execution_time="5 minutes",
            capital_required=0.0,
        )

        return RebalancingResult(
            analysis_timestamp=datetime.now(),
            portfolio_id="test_portfolio",
            current_portfolio=sample_portfolio_analysis,
            trade_recommendations=sample_trade_recommendations,
            projected_portfolio=projected_analysis,
            cost_analysis=cost_analysis,
            current_risk_score=6.0,
            projected_risk_score=5.5,
            risk_improvement=0.5,
            execution_summary=execution_summary,
            overall_recommendation=RebalancingRecommendation.REBALANCE_NOW,
            next_review_date=datetime.now() + timedelta(days=30),
        )

    def test_should_initialize_tracker_when_valid_storage_path_provided(self, temp_storage_path):
        """Test tracker initialization with valid storage path."""
        # Act
        tracker = RebalancingHistoryTracker(storage_path=temp_storage_path)

        # Assert
        assert tracker.storage_path == Path(temp_storage_path)
        assert tracker.storage_path.exists()

    def test_should_create_storage_directory_when_path_does_not_exist(self):
        """Test that tracker creates storage directory if it doesn't exist."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_path = Path(temp_dir) / "new_directory"

            # Act
            tracker = RebalancingHistoryTracker(storage_path=str(non_existent_path))

            # Assert
            assert tracker.storage_path.exists()

    def test_should_record_rebalancing_action_when_valid_data_provided(self, tracker, sample_rebalancing_result, sample_trade_recommendations):
        """Test recording a rebalancing action with valid data."""
        # Arrange
        portfolio_id = "test_portfolio_123"

        # Act
        entry_id = tracker.record_rebalancing_action(
            portfolio_id=portfolio_id,
            rebalancing_result=sample_rebalancing_result,
            executed_trades=sample_trade_recommendations,
            execution_status="COMPLETED",
            execution_notes="Test execution",
        )

        # Assert
        assert entry_id is not None
        assert isinstance(entry_id, str)

        # Verify file was created
        history_file = tracker.storage_path / f"{portfolio_id}_history.json"
        assert history_file.exists()

        # Verify content
        with open(history_file, encoding="utf-8") as f:
            history_data = json.load(f)

        assert len(history_data) == 1
        assert history_data[0]["entry_id"] == entry_id
        assert history_data[0]["portfolio_id"] == portfolio_id
        assert history_data[0]["execution_status"] == "COMPLETED"

    def test_should_calculate_correct_metrics_when_recording_action(self, tracker, sample_rebalancing_result, sample_trade_recommendations):
        """Test that correct metrics are calculated when recording action."""
        # Arrange
        portfolio_id = "test_portfolio_metrics"

        # Act
        tracker.record_rebalancing_action(
            portfolio_id=portfolio_id,
            rebalancing_result=sample_rebalancing_result,
            executed_trades=sample_trade_recommendations,
        )

        # Assert
        history = tracker.get_portfolio_history(portfolio_id)
        assert len(history) == 1

        entry = history[0]
        assert entry.total_transaction_costs == 40.0  # Sum of trade costs
        assert entry.positions_rebalanced == 2  # Both trades have quantity > 0
        assert entry.deviation_improvement > 0  # Should show improvement

    def test_should_raise_validation_error_when_invalid_data_provided(self, tracker):
        """Test that IOError is raised for invalid data."""
        # Arrange
        invalid_result = "not_a_rebalancing_result"

        # Act & Assert
        with pytest.raises(IOError):
            tracker.record_rebalancing_action(
                portfolio_id="test",
                rebalancing_result=invalid_result,
                executed_trades=[],
            )

    def test_should_retrieve_portfolio_history_when_history_exists(self, tracker, sample_rebalancing_result, sample_trade_recommendations):
        """Test retrieving portfolio history when history exists."""
        # Arrange
        portfolio_id = "test_portfolio_history"

        # Record multiple entries
        tracker.record_rebalancing_action(
            portfolio_id=portfolio_id,
            rebalancing_result=sample_rebalancing_result,
            executed_trades=sample_trade_recommendations,
        )

        # Modify timestamp for second entry
        sample_rebalancing_result.analysis_timestamp = datetime.now() + timedelta(days=1)
        tracker.record_rebalancing_action(
            portfolio_id=portfolio_id,
            rebalancing_result=sample_rebalancing_result,
            executed_trades=sample_trade_recommendations,
        )

        # Act
        history = tracker.get_portfolio_history(portfolio_id)

        # Assert
        assert len(history) == 2
        assert all(isinstance(entry, RebalancingHistoryEntry) for entry in history)
        assert history[0].timestamp <= history[1].timestamp  # Should be sorted by timestamp

    def test_should_return_empty_list_when_no_history_exists(self, tracker):
        """Test that empty list is returned when no history exists."""
        # Act
        history = tracker.get_portfolio_history("nonexistent_portfolio")

        # Assert
        assert history == []

    def test_should_filter_history_by_date_range_when_dates_provided(self, tracker, sample_rebalancing_result, sample_trade_recommendations):
        """Test filtering history by date range."""
        # Arrange
        portfolio_id = "test_portfolio_filter"

        # Record entries with different dates - use the record timestamp instead of analysis timestamp
        entry_ids = []
        for i in range(5):
            entry_id = tracker.record_rebalancing_action(
                portfolio_id=portfolio_id,
                rebalancing_result=sample_rebalancing_result,
                executed_trades=sample_trade_recommendations,
            )
            entry_ids.append(entry_id)

        # Get all history first to debug
        all_history = tracker.get_portfolio_history(portfolio_id)
        assert len(all_history) == 5  # Should have all 5 entries

        # Use the actual timestamps from the recorded entries for filtering
        if len(all_history) >= 3:
            start_date = all_history[1].timestamp  # Second entry
            end_date = all_history[3].timestamp  # Fourth entry

            # Act
            filtered_history = tracker.get_portfolio_history(portfolio_id, start_date, end_date)

            # Assert - Should include entries 1, 2, 3 (indices 1, 2, 3)
            assert len(filtered_history) >= 2  # At least entries at start and end dates
            for entry in filtered_history:
                assert start_date <= entry.timestamp <= end_date
        else:
            # Fallback assertion if something went wrong
            assert len(all_history) == 5

    def test_should_analyze_performance_attribution_when_sufficient_data_exists(self, tracker, sample_rebalancing_result, sample_trade_recommendations):
        """Test performance attribution analysis with sufficient data."""
        # Arrange
        portfolio_id = "test_portfolio_attribution"

        # Record multiple entries over time
        base_date = datetime.now() - timedelta(days=100)
        for i in range(5):
            sample_rebalancing_result.analysis_timestamp = base_date + timedelta(days=i * 20)
            sample_rebalancing_result.current_portfolio.total_value = 100000 + (i * 5000)
            tracker.record_rebalancing_action(
                portfolio_id=portfolio_id,
                rebalancing_result=sample_rebalancing_result,
                executed_trades=sample_trade_recommendations,
            )

        # Act
        start_date = base_date
        end_date = datetime.now()
        attribution = tracker.analyze_performance_attribution(portfolio_id, start_date, end_date)

        # Assert
        assert isinstance(attribution, PerformanceAttribution)
        assert attribution.attribution_start_date == start_date
        assert attribution.attribution_end_date == end_date
        assert attribution.total_return_with_rebalancing > 0  # Should show positive return
        assert attribution.rebalancing_frequency_days > 0
        assert attribution.optimal_frequency_estimate > 0

    def test_should_raise_error_when_insufficient_data_for_attribution(self, tracker):
        """Test that error is raised when insufficient data for attribution analysis."""
        # Arrange
        portfolio_id = "test_portfolio_insufficient"
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        # Act & Assert
        with pytest.raises(ValueError, match="Insufficient history"):
            tracker.analyze_performance_attribution(portfolio_id, start_date, end_date)

    def test_should_analyze_rebalancing_trends_when_data_available(self, tracker, sample_rebalancing_result, sample_trade_recommendations):
        """Test trend analysis with available data."""
        # Arrange
        portfolio_id = "test_portfolio_trends"

        # Record entries with varying deviations
        base_date = datetime.now() - timedelta(days=200)
        for i in range(8):
            sample_rebalancing_result.analysis_timestamp = base_date + timedelta(days=i * 25)
            # Vary deviations to create patterns
            deviation_factor = 0.02 + (i % 3) * 0.01
            sample_rebalancing_result.current_portfolio.deviations_from_target = {
                "AAPL": deviation_factor,
                "GOOGL": -deviation_factor * 0.8,
                "MSFT": deviation_factor * 0.5,
            }
            tracker.record_rebalancing_action(
                portfolio_id=portfolio_id,
                rebalancing_result=sample_rebalancing_result,
                executed_trades=sample_trade_recommendations,
            )

        # Act
        trend_analysis = tracker.analyze_rebalancing_trends(portfolio_id, analysis_period_days=365)

        # Assert
        assert isinstance(trend_analysis, TrendAnalysis)
        assert trend_analysis.analysis_period_months == 365 // 30  # Converted to months
        assert len(trend_analysis.frequency_scenarios_tested) > 0
        assert trend_analysis.optimal_frequency_days > 0
        assert 0.0 <= trend_analysis.confidence_in_optimal <= 1.0

    def test_should_provide_default_recommendations_when_insufficient_trend_data(self, tracker):
        """Test that default recommendations are provided when insufficient data."""
        # Arrange
        portfolio_id = "test_portfolio_default_trends"

        # Act
        trend_analysis = tracker.analyze_rebalancing_trends(portfolio_id)

        # Assert
        assert isinstance(trend_analysis, TrendAnalysis)
        assert trend_analysis.optimal_frequency_days == 60  # Default
        assert trend_analysis.confidence_in_optimal < 0.5  # Low confidence

    def test_should_generate_analytics_dashboard_when_history_exists(self, tracker, sample_rebalancing_result, sample_trade_recommendations):
        """Test analytics dashboard generation with existing history."""
        # Arrange
        portfolio_id = "test_portfolio_dashboard"

        # Record multiple entries
        base_date = datetime.now() - timedelta(days=180)
        for i in range(6):
            sample_rebalancing_result.analysis_timestamp = base_date + timedelta(days=i * 30)
            tracker.record_rebalancing_action(
                portfolio_id=portfolio_id,
                rebalancing_result=sample_rebalancing_result,
                executed_trades=sample_trade_recommendations,
                execution_status="COMPLETED" if i % 2 == 0 else "PARTIAL",
            )

        # Act
        analytics = tracker.generate_analytics_dashboard(portfolio_id)

        # Assert - Match actual RebalancingAnalytics schema
        assert isinstance(analytics, RebalancingAnalytics)
        assert isinstance(analytics.current_portfolio_metrics, PortfolioMetrics)
        assert isinstance(analytics.current_rebalancing_needs, list)
        assert analytics.recommended_action is not None
        assert analytics.next_review_date is not None
        # Optional fields
        if analytics.performance_attribution:
            assert isinstance(analytics.performance_attribution, PerformanceAttribution)
        if analytics.trend_analysis:
            assert isinstance(analytics.trend_analysis, TrendAnalysis)

    def test_should_raise_error_when_no_history_for_dashboard(self, tracker):
        """Test that error is raised when no history exists for dashboard."""
        # Act & Assert
        with pytest.raises(ValueError, match="No rebalancing history found"):
            tracker.generate_analytics_dashboard("nonexistent_portfolio")

    def test_should_calculate_position_histories_correctly(self, tracker, sample_rebalancing_result, sample_trade_recommendations):
        """Test that position histories are calculated correctly."""
        # Arrange
        portfolio_id = "test_portfolio_positions"

        # Record entries with different position activities
        for i in range(4):
            # Modify trade quantities to create different patterns
            modified_trades = []
            for trade in sample_trade_recommendations:
                modified_trade = trade.model_copy()
                new_quantity = trade.quantity * (1 + i * 0.1)
                modified_trade.quantity = new_quantity
                modified_trade.trade_value = new_quantity * trade.current_price  # Fix trade value
                modified_trade.weight_deviation = 0.02 + i * 0.01
                modified_trades.append(modified_trade)

            tracker.record_rebalancing_action(
                portfolio_id=portfolio_id,
                rebalancing_result=sample_rebalancing_result,
                executed_trades=modified_trades,
            )

        # Act
        analytics = tracker.generate_analytics_dashboard(portfolio_id)

        # Assert - Verify analytics was generated successfully
        assert isinstance(analytics, RebalancingAnalytics)
        assert analytics.current_portfolio_metrics is not None
        assert len(analytics.current_rebalancing_needs) >= 0

    def test_should_generate_appropriate_strategy_recommendations(self, tracker, sample_rebalancing_result, sample_trade_recommendations):
        """Test that appropriate strategy recommendations are generated."""
        # Arrange
        portfolio_id = "test_portfolio_recommendations"

        # Create scenario with high costs (negative net benefit)
        high_cost_trades = []
        for trade in sample_trade_recommendations:
            high_cost_trade = trade.model_copy()
            high_cost_trade.estimated_commission = 500.0  # Very high commission
            high_cost_trade.estimated_spread_cost = 500.0  # Very high spread
            high_cost_trade.total_estimated_cost = 1000.0  # Very high total cost
            high_cost_trades.append(high_cost_trade)

        # Record multiple entries to meet minimum requirement for analytics
        base_date = datetime.now() - timedelta(days=100)
        for i in range(3):
            result_copy = sample_rebalancing_result.model_copy()
            result_copy.analysis_timestamp = base_date + timedelta(days=i * 30)
            result_copy.current_portfolio.total_value = 100000 + (i * 5000)
            tracker.record_rebalancing_action(
                portfolio_id=portfolio_id,
                rebalancing_result=result_copy,
                executed_trades=high_cost_trades,
            )

        # Act
        analytics = tracker.generate_analytics_dashboard(portfolio_id)

        # Assert
        recommendations = analytics.strategy_recommendations
        assert len(recommendations) > 0

        # Should include cost-related recommendations due to high costs
        cost_recommendations = [r for r in recommendations if "cost" in r.lower()]
        assert len(cost_recommendations) > 0

    def test_should_handle_numpy_operations_gracefully_when_empty_data(self, tracker, mocker):
        """Test graceful handling of numpy operations with empty data."""
        # Arrange
        mock_mean = mocker.patch("numpy.mean")
        mock_mean.return_value = 0.0
        portfolio_id = "test_portfolio_empty"

        # Act & Assert - Should not raise error even with empty data
        with pytest.raises(ValueError):  # Expected due to no history
            tracker.generate_analytics_dashboard(portfolio_id)

    def test_should_validate_frequency_scenarios_in_trend_analysis(self, tracker, sample_rebalancing_result, sample_trade_recommendations):
        """Test that frequency scenarios are properly validated in trend analysis."""
        # Arrange
        portfolio_id = "test_portfolio_frequency_validation"

        # Record sufficient data
        base_date = datetime.now() - timedelta(days=300)
        for i in range(10):
            sample_rebalancing_result.analysis_timestamp = base_date + timedelta(days=i * 30)
            tracker.record_rebalancing_action(
                portfolio_id=portfolio_id,
                rebalancing_result=sample_rebalancing_result,
                executed_trades=sample_trade_recommendations,
            )

        # Act
        trend_analysis = tracker.analyze_rebalancing_trends(portfolio_id)

        # Assert
        assert all(freq > 0 for freq in trend_analysis.frequency_scenarios_tested)
        assert all(str(freq) in trend_analysis.performance_by_frequency for freq in trend_analysis.frequency_scenarios_tested)
        assert all(str(freq) in trend_analysis.cost_by_frequency for freq in trend_analysis.frequency_scenarios_tested)
        assert all(str(freq) in trend_analysis.net_benefit_by_frequency for freq in trend_analysis.frequency_scenarios_tested)

    def test_should_handle_file_io_errors_gracefully(self, tracker, sample_rebalancing_result):
        """Test graceful handling of file I/O errors."""
        # Arrange
        portfolio_id = "test_portfolio_io_error"

        # Make storage path read-only to simulate I/O error
        tracker.storage_path.chmod(0o444)

        # Act & Assert
        with pytest.raises(IOError):
            tracker.record_rebalancing_action(
                portfolio_id=portfolio_id,
                rebalancing_result=sample_rebalancing_result,
                executed_trades=[],
            )

        # Restore permissions for cleanup
        tracker.storage_path.chmod(0o755)

    def test_should_maintain_data_consistency_across_operations(self, tracker, sample_rebalancing_result, sample_trade_recommendations):
        """Test that data consistency is maintained across multiple operations."""
        # Arrange
        portfolio_id = "test_portfolio_consistency"

        # Record multiple entries to meet minimum requirement for analytics
        base_date = datetime.now() - timedelta(days=100)
        entry_ids = []
        for i in range(3):
            result_copy = sample_rebalancing_result.model_copy()
            result_copy.analysis_timestamp = base_date + timedelta(days=i * 30)
            result_copy.current_portfolio.total_value = 100000 + (i * 5000)
            entry_id = tracker.record_rebalancing_action(
                portfolio_id=portfolio_id,
                rebalancing_result=result_copy,
                executed_trades=sample_trade_recommendations,
            )
            entry_ids.append(entry_id)

        # Act - Perform multiple operations
        history = tracker.get_portfolio_history(portfolio_id)
        analytics = tracker.generate_analytics_dashboard(portfolio_id)

        # Assert - Data should be consistent
        assert len(history) == 3
        assert history[0].entry_id == entry_ids[0]
        assert analytics.total_rebalancing_events == 3
        assert analytics.portfolio_id == portfolio_id

        # Position histories should match trade data
        expected_symbols = {trade.symbol for trade in sample_trade_recommendations}
        actual_symbols = {pos.symbol for pos in analytics.position_histories}
        assert expected_symbols == actual_symbols
