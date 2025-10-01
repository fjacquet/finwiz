"""
Unit tests for the A+ Investment Feedback Learning System.

Tests cover feedback collection, performance tracking, learning algorithms,
and criteria optimization functionality.
"""

import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from finwiz.schemas.feedback import (
    FeedbackSentiment,
    FeedbackType,
    LearningConfiguration,
    PerformanceFeedback,
    PerformanceOutcome,
    RecommendationOutcome,
    UserFeedback,
)
from finwiz.schemas.investment_discovery import APlusCriteria
from finwiz.services.feedback_service import FeedbackLearningService


class TestFeedbackLearningService:
    """Test cases for the FeedbackLearningService."""

    @pytest.fixture
    def feedback_service(self, tmp_path):
        """Create a feedback service with temporary storage."""
        config = LearningConfiguration(
            min_feedback_samples=5,
            learning_rate=0.1,
            confidence_threshold=0.7,
            adjustment_frequency_days=7,  # Short for testing
        )

        service = FeedbackLearningService(config)
        # Override storage paths to use temporary directory
        service.feedback_storage_path = tmp_path / "feedback"
        service.criteria_history_path = tmp_path / "criteria_history"
        service.feedback_storage_path.mkdir(parents=True, exist_ok=True)
        service.criteria_history_path.mkdir(parents=True, exist_ok=True)

        return service

    @pytest.fixture
    def sample_user_feedback(self):
        """Create sample user feedback for testing."""
        return UserFeedback(
            feedback_id=str(uuid.uuid4()),
            user_id="test_user_123",
            feedback_type=FeedbackType.RECOMMENDATION_ACCEPTANCE,
            recommendation_id="rec_123",
            symbol="AAPL",
            asset_type="stock",
            recommended_grade="A+",
            recommended_score=0.96,
            outcome=RecommendationOutcome.ACCEPTED,
            sentiment=FeedbackSentiment.POSITIVE,
            confidence_rating=4,
            reasons=["Strong fundamentals", "Good growth prospects"],
            user_comments="Excellent recommendation",
        )

    @pytest.fixture
    def sample_performance_feedback(self):
        """Create sample performance feedback for testing."""
        return PerformanceFeedback(
            feedback_id=str(uuid.uuid4()),
            original_recommendation_id="rec_123",
            symbol="AAPL",
            evaluation_date=datetime.now(),
            holding_period_days=90,
            absolute_return=0.15,
            benchmark_return=0.10,
            alpha=0.05,
            current_grade="A+",
            grade_maintained=True,
            performance_outcome=PerformanceOutcome.OUTPERFORMED,
            met_expectations=True,
            volatility=0.20,
            max_drawdown=-0.05,
            market_regime_during_period="bull",
        )

    @pytest.fixture
    def sample_criteria(self):
        """Create sample A+ criteria for testing."""
        return APlusCriteria(
            etf_max_expense_ratio=0.15,
            etf_min_aum=1e9,
            stock_min_roe=0.20,
            stock_min_revenue_growth=0.15,
            crypto_min_market_cap=10e9,
            crypto_min_daily_volume=500e6,
        )

    @pytest.mark.asyncio
    async def test_should_collect_user_feedback_when_valid_data_provided(self, feedback_service, sample_user_feedback):
        """Test collecting user feedback with valid data."""
        # Act
        feedback_id = await feedback_service.collect_user_feedback(sample_user_feedback)

        # Assert
        assert feedback_id == sample_user_feedback.feedback_id
        assert feedback_id in feedback_service._feedback_cache

        # Check file was created
        feedback_file = feedback_service.feedback_storage_path / f"user_feedback_{feedback_id}.json"
        assert feedback_file.exists()

        # Verify file content
        stored_data = json.loads(feedback_file.read_text())
        assert stored_data["symbol"] == "AAPL"
        assert stored_data["outcome"] == "accepted"

    @pytest.mark.asyncio
    async def test_should_record_performance_outcome_when_valid_data_provided(self, feedback_service, sample_performance_feedback):
        """Test recording performance outcomes with valid data."""
        # Act
        performance_id = await feedback_service.record_performance_outcome(sample_performance_feedback)

        # Assert
        assert performance_id == sample_performance_feedback.feedback_id
        assert performance_id in feedback_service._performance_cache

        # Check file was created
        performance_file = feedback_service.feedback_storage_path / f"performance_{performance_id}.json"
        assert performance_file.exists()

        # Verify file content
        stored_data = json.loads(performance_file.read_text())
        assert stored_data["symbol"] == "AAPL"
        assert stored_data["performance_outcome"] == "outperformed"

    @pytest.mark.asyncio
    async def test_should_analyze_feedback_patterns_when_sufficient_data_available(
        self, feedback_service, sample_user_feedback, sample_performance_feedback
    ):
        """Test feedback pattern analysis with sufficient data."""
        # Arrange - Create multiple feedback samples
        feedback_samples = []
        for i in range(10):
            feedback = sample_user_feedback.model_copy()
            feedback.feedback_id = str(uuid.uuid4())
            feedback.symbol = f"STOCK{i}"
            feedback.outcome = RecommendationOutcome.ACCEPTED if i % 2 == 0 else RecommendationOutcome.REJECTED
            feedback_samples.append(feedback)

        # Store feedback samples
        for feedback in feedback_samples:
            await feedback_service.collect_user_feedback(feedback)

        # Store performance feedback
        await feedback_service.record_performance_outcome(sample_performance_feedback)

        # Act
        analysis = await feedback_service.analyze_feedback_patterns(days_back=30)

        # Assert
        assert analysis.total_feedback_items == 10
        assert analysis.unique_users == 1
        assert analysis.sample_size_adequacy  # >= min_feedback_samples
        assert "stock" in analysis.acceptance_by_asset_type
        assert analysis.acceptance_by_asset_type["stock"] == 0.5  # 50% acceptance
        assert len(analysis.key_insights) > 0

    @pytest.mark.asyncio
    async def test_should_adjust_criteria_when_sufficient_feedback_and_due_timing(
        self, feedback_service, sample_criteria, sample_user_feedback
    ):
        """Test criteria adjustment based on feedback learning."""
        # Arrange - Create feedback indicating low acceptance for stocks
        feedback_samples = []
        for i in range(10):
            feedback = sample_user_feedback.model_copy()
            feedback.feedback_id = str(uuid.uuid4())
            feedback.symbol = f"STOCK{i}"
            feedback.asset_type = "stock"
            feedback.outcome = RecommendationOutcome.REJECTED  # All rejected
            feedback.reasons = ["ROE too high", "Growth requirements too strict"]
            feedback_samples.append(feedback)

        # Store feedback samples
        for feedback in feedback_samples:
            await feedback_service.collect_user_feedback(feedback)

        # Mock backtesting to pass
        with patch.object(feedback_service, "_backtest_criteria_adjustment") as mock_backtest:
            mock_backtest.return_value = {"passed": True, "sharpe_ratio": 1.2}

            # Act
            adjustment = await feedback_service.adjust_criteria_based_on_learning(
                current_criteria=sample_criteria, force_adjustment=True
            )

        # Assert
        assert adjustment is not None
        assert adjustment.adjustment_reason is not None
        assert adjustment.confidence_level > 0
        assert adjustment.expected_improvement > 0

        # Check that stock criteria were loosened (due to rejections)
        assert adjustment.criteria_after.stock_min_roe <= sample_criteria.stock_min_roe
        assert adjustment.criteria_after.stock_min_revenue_growth <= sample_criteria.stock_min_revenue_growth

    @pytest.mark.asyncio
    async def test_should_not_adjust_criteria_when_insufficient_feedback(self, feedback_service, sample_criteria):
        """Test that criteria adjustment is skipped with insufficient feedback."""
        # Arrange - Only create 2 feedback samples (below minimum of 5)
        for i in range(2):
            feedback = UserFeedback(
                feedback_id=str(uuid.uuid4()),
                user_id="test_user",
                feedback_type=FeedbackType.RECOMMENDATION_ACCEPTANCE,
                recommendation_id=f"rec_{i}",
                symbol=f"STOCK{i}",
                asset_type="stock",
                recommended_grade="A+",
                recommended_score=0.95,
                outcome=RecommendationOutcome.ACCEPTED,
                sentiment=FeedbackSentiment.POSITIVE,
                confidence_rating=4,
            )
            await feedback_service.collect_user_feedback(feedback)

        # Act
        adjustment = await feedback_service.adjust_criteria_based_on_learning(
            current_criteria=sample_criteria, force_adjustment=True
        )

        # Assert
        assert adjustment is None  # Should not adjust with insufficient data

    @pytest.mark.asyncio
    async def test_should_get_learning_metrics_when_data_available(
        self, feedback_service, sample_user_feedback, sample_performance_feedback
    ):
        """Test learning metrics calculation with available data."""
        # Arrange - Create feedback and performance data
        await feedback_service.collect_user_feedback(sample_user_feedback)
        await feedback_service.record_performance_outcome(sample_performance_feedback)

        # Act
        metrics = await feedback_service.get_learning_metrics(days_back=30)

        # Assert
        assert metrics.total_recommendations >= 1
        assert metrics.acceptance_rate >= 0.0
        assert metrics.recommendations_with_outcomes >= 1
        assert metrics.outperformance_rate >= 0.0
        assert metrics.grade_maintenance_rate >= 0.0
        assert metrics.average_confidence_rating > 0

    @pytest.mark.asyncio
    async def test_should_rollback_criteria_adjustment_when_requested(self, feedback_service, sample_criteria):
        """Test rolling back a criteria adjustment."""
        # Arrange - First create an adjustment
        with patch.object(feedback_service, "_backtest_criteria_adjustment") as mock_backtest:
            mock_backtest.return_value = {"passed": True}

            # Create sufficient feedback for adjustment
            for i in range(10):
                feedback = UserFeedback(
                    feedback_id=str(uuid.uuid4()),
                    user_id="test_user",
                    feedback_type=FeedbackType.RECOMMENDATION_ACCEPTANCE,
                    recommendation_id=f"rec_{i}",
                    symbol=f"STOCK{i}",
                    asset_type="stock",
                    recommended_grade="A+",
                    recommended_score=0.95,
                    outcome=RecommendationOutcome.REJECTED,
                    sentiment=FeedbackSentiment.NEGATIVE,
                    confidence_rating=2,
                )
                await feedback_service.collect_user_feedback(feedback)

            adjustment = await feedback_service.adjust_criteria_based_on_learning(
                current_criteria=sample_criteria, force_adjustment=True
            )

        assert adjustment is not None
        adjustment_id = adjustment.adjustment_id

        # Act - Rollback the adjustment
        success = await feedback_service.rollback_criteria_adjustment(
            adjustment_id=adjustment_id, reason="Performance degradation detected"
        )

        # Assert
        assert success

        # Check rollback file was created
        rollback_files = list(feedback_service.criteria_history_path.glob("adjustment_*.json"))
        assert len(rollback_files) >= 2  # Original + rollback

    @pytest.mark.asyncio
    async def test_should_handle_invalid_feedback_gracefully(self, feedback_service):
        """Test handling of invalid feedback data."""
        # Arrange - Create invalid feedback (missing required fields)
        invalid_feedback = UserFeedback(
            feedback_id="",
            user_id="",  # Invalid empty user_id
            feedback_type=FeedbackType.RECOMMENDATION_ACCEPTANCE,
            recommendation_id="rec_123",
            symbol="AAPL",
            asset_type="stock",
            recommended_grade="A+",
            recommended_score=0.95,
            outcome=RecommendationOutcome.ACCEPTED,
            sentiment=FeedbackSentiment.POSITIVE,
            confidence_rating=4,
        )

        # Act & Assert - Should handle gracefully without crashing
        try:
            feedback_id = await feedback_service.collect_user_feedback(invalid_feedback)
            # If it succeeds, it should generate an ID
            assert feedback_id is not None
        except Exception as e:
            # If it fails, it should be a validation error, not a crash
            assert "validation" in str(e).lower() or "required" in str(e).lower()

    def test_should_validate_criteria_adjustment_within_bounds(self, feedback_service, sample_criteria):
        """Test that criteria adjustments are validated to be within acceptable bounds."""
        # Arrange - Create criteria with extreme changes
        extreme_criteria = sample_criteria.model_copy()
        extreme_criteria.stock_min_roe = 0.50  # 150% increase (way above max_criteria_change of 20%)

        # Act
        is_valid = feedback_service._validate_criteria_adjustment(sample_criteria, extreme_criteria)

        # Assert
        assert not is_valid  # Should reject extreme changes

    def test_should_calculate_acceptance_rates_by_asset_type(self, feedback_service):
        """Test calculation of acceptance rates by asset type."""
        # Arrange
        feedback_list = [
            UserFeedback(
                feedback_id=str(uuid.uuid4()),
                user_id="user1",
                feedback_type=FeedbackType.RECOMMENDATION_ACCEPTANCE,
                recommendation_id="rec1",
                symbol="SPY",
                asset_type="etf",
                recommended_grade="A+",
                recommended_score=0.95,
                outcome=RecommendationOutcome.ACCEPTED,
                sentiment=FeedbackSentiment.POSITIVE,
                confidence_rating=4,
            ),
            UserFeedback(
                feedback_id=str(uuid.uuid4()),
                user_id="user1",
                feedback_type=FeedbackType.RECOMMENDATION_ACCEPTANCE,
                recommendation_id="rec2",
                symbol="VTI",
                asset_type="etf",
                recommended_grade="A+",
                recommended_score=0.96,
                outcome=RecommendationOutcome.REJECTED,
                sentiment=FeedbackSentiment.NEGATIVE,
                confidence_rating=2,
            ),
        ]

        # Act
        acceptance_rates = feedback_service._calculate_acceptance_by_asset(feedback_list)

        # Assert
        assert "etf" in acceptance_rates
        assert acceptance_rates["etf"] == 0.5  # 1 accepted out of 2

    def test_should_identify_success_and_failure_patterns(self, feedback_service):
        """Test identification of success and failure patterns."""
        # Arrange
        user_feedback = [
            UserFeedback(
                feedback_id=str(uuid.uuid4()),
                user_id="user1",
                feedback_type=FeedbackType.RECOMMENDATION_ACCEPTANCE,
                recommendation_id="rec1",
                symbol="AAPL",
                asset_type="stock",
                recommended_grade="A+",
                recommended_score=0.97,
                outcome=RecommendationOutcome.ACCEPTED,
                sentiment=FeedbackSentiment.POSITIVE,
                confidence_rating=5,
            ),
        ]

        performance_feedback = [
            PerformanceFeedback(
                feedback_id=str(uuid.uuid4()),
                original_recommendation_id="rec1",
                symbol="AAPL",
                evaluation_date=datetime.now(),
                holding_period_days=90,
                absolute_return=0.20,
                benchmark_return=0.10,
                alpha=0.10,
                current_grade="A+",
                grade_maintained=True,
                performance_outcome=PerformanceOutcome.OUTPERFORMED,
                met_expectations=True,
                volatility=0.15,
                max_drawdown=-0.03,
                market_regime_during_period="bull",
            ),
        ]

        # Act
        success_patterns = feedback_service._identify_success_patterns(user_feedback, performance_feedback)
        failure_patterns = feedback_service._identify_failure_patterns(user_feedback, performance_feedback)

        # Assert
        assert len(success_patterns) > 0
        assert "score" in success_patterns[0].lower()  # Should mention score patterns
        assert len(failure_patterns) == 0  # No failures in this case

    def test_should_assess_data_quality_correctly(self, feedback_service):
        """Test data quality assessment functionality."""
        # Arrange - Create feedback with varying completeness
        complete_feedback = [
            UserFeedback(
                feedback_id=str(uuid.uuid4()),
                user_id="user1",
                feedback_type=FeedbackType.RECOMMENDATION_ACCEPTANCE,
                recommendation_id="rec1",
                symbol="AAPL",
                asset_type="stock",
                recommended_grade="A+",
                recommended_score=0.95,
                outcome=RecommendationOutcome.ACCEPTED,
                sentiment=FeedbackSentiment.POSITIVE,
                confidence_rating=4,
                reasons=["Good fundamentals", "Strong growth"],  # Complete
                user_comments="Excellent choice",
            ),
        ]

        incomplete_feedback = [
            UserFeedback(
                feedback_id=str(uuid.uuid4()),
                user_id="user2",
                feedback_type=FeedbackType.RECOMMENDATION_ACCEPTANCE,
                recommendation_id="rec2",
                symbol="MSFT",
                asset_type="stock",
                recommended_grade="A+",
                recommended_score=0.94,
                outcome=RecommendationOutcome.REJECTED,
                sentiment=FeedbackSentiment.NEUTRAL,
                confidence_rating=1,  # Minimum valid value
                reasons=[],  # Missing
            ),
        ]

        # Act
        complete_quality = feedback_service._assess_data_quality(complete_feedback, [])
        incomplete_quality = feedback_service._assess_data_quality(incomplete_feedback, [])

        # Assert
        assert complete_quality > incomplete_quality
        assert 0.0 <= complete_quality <= 1.0
        assert 0.0 <= incomplete_quality <= 1.0


class TestFeedbackIntegrationTools:
    """Test cases for feedback integration tools."""

    @pytest.mark.asyncio
    async def test_feedback_collection_tool_should_process_valid_input(self):
        """Test feedback collection tool with valid input."""
        from finwiz.tools.feedback_integration_tool import FeedbackCollectionTool

        tool = FeedbackCollectionTool()

        # Arrange
        input_data = {
            "user_id": "test_user_123",
            "recommendation_id": "rec_456",
            "symbol": "AAPL",
            "asset_type": "stock",
            "outcome": "accepted",
            "sentiment": "positive",
            "confidence_rating": 4,
            "reasons": ["Strong fundamentals", "Good growth"],
            "user_comments": "Great recommendation",
        }

        # Mock the feedback service
        with patch("finwiz.tools.feedback_integration_tool.get_feedback_service") as mock_service:
            mock_feedback_service = AsyncMock()
            mock_feedback_service.collect_user_feedback.return_value = "feedback_123"
            mock_service.return_value = mock_feedback_service

            # Act
            result = await tool._arun(**input_data)

            # Assert
            assert result["success"]
            assert result["feedback_id"] == "feedback_123"
            assert "AAPL" in result["message"]
            mock_feedback_service.collect_user_feedback.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_tracking_tool_should_calculate_alpha_correctly(self):
        """Test performance tracking tool alpha calculation."""
        from finwiz.tools.feedback_integration_tool import PerformanceTrackingTool

        tool = PerformanceTrackingTool()

        # Arrange
        input_data = {
            "recommendation_id": "rec_123",
            "symbol": "AAPL",
            "holding_period_days": 90,
            "absolute_return": 0.15,  # 15% return
            "benchmark_return": 0.10,  # 10% benchmark
            "current_grade": "A+",
            "grade_maintained": True,
        }

        # Mock the feedback service
        with patch("finwiz.tools.feedback_integration_tool.get_feedback_service") as mock_service:
            mock_feedback_service = AsyncMock()
            mock_feedback_service.record_performance_outcome.return_value = "performance_123"
            mock_service.return_value = mock_feedback_service

            # Act
            result = await tool._arun(**input_data)

            # Assert
            assert result["success"]
            assert result["alpha"] == 0.05  # 15% - 10% = 5% alpha
            assert result["performance_outcome"] == "outperformed"  # Alpha > 2%
            mock_feedback_service.record_performance_outcome.assert_called_once()

    @pytest.mark.asyncio
    async def test_criteria_optimization_tool_should_handle_no_adjustment_needed(self):
        """Test criteria optimization tool when no adjustment is needed."""
        from finwiz.tools.feedback_integration_tool import CriteriaOptimizationTool

        tool = CriteriaOptimizationTool()

        # Arrange
        input_data = {
            "current_criteria": {
                "etf_max_expense_ratio": 0.15,
                "stock_min_roe": 0.20,
                "crypto_min_market_cap": 10e9,
            },
            "analysis_period_days": 90,
            "force_adjustment": False,
        }

        # Mock the feedback service to return no adjustment
        with patch("finwiz.tools.feedback_integration_tool.get_feedback_service") as mock_service:
            mock_feedback_service = AsyncMock()
            mock_feedback_service.adjust_criteria_based_on_learning.return_value = None
            mock_service.return_value = mock_feedback_service

            # Act
            result = await tool._arun(**input_data)

            # Assert
            assert result["success"]
            assert not result["adjustment_made"]
            assert "not needed" in result["message"]
            mock_feedback_service.adjust_criteria_based_on_learning.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
