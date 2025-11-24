"""
Unit tests for A+ Investment Monitoring System.

Tests the core monitoring functionality including grade degradation detection,
alert generation, performance tracking, and automated re-evaluation triggers.
"""

from pytest import approx
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from finwiz.schemas.investment_discovery import APlusAnalysis, InvestmentCandidate, MarketRegime
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool
from finwiz.tools.notification_service import NotificationService
from finwiz.utils.a_plus_monitoring import (
    APlusMonitoringSystem,
)
from finwiz.utils.monitoring_alerts import (
    AlertSeverity,
    GradeDegradationAlert,
)
from finwiz.utils.monitoring_metrics import PerformanceMetrics

# Configure pytest for async tests
pytestmark = pytest.mark.anyio


class TestAPlusMonitoringSystem:
    """Test suite for A+ monitoring system core functionality."""

    @pytest.fixture
    def mock_scoring_tool(self, mocker):
        """Mock A+ scoring tool."""
        mock_tool = mocker.Mock(spec=APlusScoringTool)
        mock_tool._run = mocker.Mock(
            return_value={
                "symbol": "AAPL",
                "composite_score": 0.96,
                "grade": "A+",
                "is_a_plus_candidate": True,
                "analysis_summary": {
                    "component_scores": {
                        "fundamental": 0.95,
                        "technical": 0.92,
                        "quality": 0.98,
                        "risk": 0.90,
                    },
                    "confidence": 0.85,
                    "top_strengths": ["Strong fundamentals", "Market leadership"],
                },
            }
        )
        return mock_tool

    @pytest.fixture
    def mock_notification_service(self, mocker):
        """Mock notification service."""
        mock_service = mocker.Mock(spec=NotificationService)
        mock_service.send_alert = mocker.AsyncMock()
        return mock_service

    @pytest.fixture
    def monitoring_system(self, mock_scoring_tool, mock_notification_service):
        """Create monitoring system with mocked dependencies."""
        return APlusMonitoringSystem(
            scoring_tool=mock_scoring_tool,
            notification_service=mock_notification_service,
            alert_threshold_hours=24,
            reevaluation_interval_hours=168,
        )

    @pytest.fixture
    def sample_analysis(self):
        """Create sample A+ analysis for testing."""
        candidate = InvestmentCandidate(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type="stock",
            current_price=150.0,
            market_cap=2.5e12,
            preliminary_score=0.96,
            final_score=0.96,
            grade="A+",
            grade_description="Excellent - Champion du portefeuille",
            recommended_action="Augmentez l'allocation si possible",
            data_source="test",
        )

        return APlusAnalysis(
            candidate=candidate,
            fundamental_score=0.95,
            technical_score=0.92,
            quality_score=0.98,
            risk_score=0.90,
            composite_score=0.96,
            confidence_level=0.85,
            is_a_plus_candidate=True,
            rationale=["Strong fundamentals", "Market leadership", "Excellent quality"],
        )

    def test_should_initialize_monitoring_system_when_created(self, monitoring_system):
        """Test monitoring system initialization."""
        assert monitoring_system.alert_threshold_hours == 24
        assert monitoring_system.reevaluation_interval_hours == 168
        assert len(monitoring_system.monitored_investments) == 0
        assert len(monitoring_system.alert_history) == 0
        assert not monitoring_system._is_monitoring

    def test_should_add_investment_to_monitor_when_valid_analysis_provided(self, monitoring_system, sample_analysis):
        """Test adding investment to monitoring system."""
        # Act
        monitoring_system.add_investment_to_monitor(
            symbol="AAPL",
            asset_type="stock",
            initial_analysis=sample_analysis,
        )

        # Assert
        assert "AAPL" in monitoring_system.monitored_investments
        metrics = monitoring_system.monitored_investments["AAPL"]
        assert metrics.symbol == "AAPL"
        assert metrics.asset_type == "stock"
        assert metrics.initial_grade == "A+"
        assert metrics.current_grade == "A+"
        assert metrics.initial_score == approx(0.96)
        assert metrics.current_score == approx(0.96)
        assert metrics.is_active is True

    def test_should_remove_investment_from_monitor_when_requested(self, monitoring_system, sample_analysis):
        """Test removing investment from monitoring."""
        # Arrange
        monitoring_system.add_investment_to_monitor("AAPL", "stock", sample_analysis)

        # Act
        monitoring_system.remove_investment_from_monitor("AAPL", "Test removal")

        # Assert
        assert "AAPL" in monitoring_system.monitored_investments
        assert monitoring_system.monitored_investments["AAPL"].is_active is False

    def test_should_get_active_investments_when_some_inactive(self, monitoring_system, sample_analysis):
        """Test getting only active investments."""
        # Arrange
        monitoring_system.add_investment_to_monitor("AAPL", "stock", sample_analysis)
        monitoring_system.add_investment_to_monitor("MSFT", "stock", sample_analysis)
        monitoring_system.remove_investment_from_monitor("MSFT", "Test")

        # Act
        active_investments = monitoring_system.get_active_investments()

        # Assert
        assert len(active_investments) == 1
        assert "AAPL" in active_investments
        assert "MSFT" not in active_investments

    @pytest.mark.asyncio
    async def test_should_start_and_stop_monitoring_when_requested(self, monitoring_system):
        """Test starting and stopping monitoring process."""
        # Test start
        await monitoring_system.start_monitoring()
        assert monitoring_system._is_monitoring is True
        assert monitoring_system._monitoring_task is not None

        # Test stop
        await monitoring_system.stop_monitoring()
        assert monitoring_system._is_monitoring is False

    @pytest.mark.asyncio
    async def test_should_evaluate_investment_when_forced(self, monitoring_system, sample_analysis, mock_scoring_tool):
        """Test forced evaluation of investment."""
        # Arrange
        monitoring_system.add_investment_to_monitor("AAPL", "stock", sample_analysis)

        # Act
        result = await monitoring_system.evaluate_investment("AAPL", force_evaluation=True)

        # Assert
        assert result is not None
        assert result.candidate.symbol == "AAPL"
        assert result.composite_score == approx(0.96)
        mock_scoring_tool._run.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_skip_evaluation_when_not_due(self, monitoring_system, sample_analysis, mock_scoring_tool):
        """Test skipping evaluation when not due."""
        # Arrange
        monitoring_system.add_investment_to_monitor("AAPL", "stock", sample_analysis)
        # Set last evaluation to recent time
        monitoring_system.monitored_investments["AAPL"].last_evaluated = datetime.now()

        # Act
        result = await monitoring_system.evaluate_investment("AAPL", force_evaluation=False)

        # Assert
        assert result is None
        mock_scoring_tool._run.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_detect_grade_degradation_when_score_drops(self, monitoring_system, sample_analysis, mock_scoring_tool):
        """Test detection of grade degradation."""
        # Arrange
        monitoring_system.add_investment_to_monitor("AAPL", "stock", sample_analysis)

        # Mock degraded score
        mock_scoring_tool._run.return_value = {
            "symbol": "AAPL",
            "composite_score": 0.82,  # Dropped from 0.96 to 0.82
            "grade": "B+",
            "is_a_plus_candidate": False,
            "analysis_summary": {
                "component_scores": {"fundamental": 0.8, "technical": 0.8, "quality": 0.8, "risk": 0.8},
                "confidence": 0.7,
                "top_strengths": ["Still decent"],
            },
        }

        # Act
        await monitoring_system.evaluate_investment("AAPL", force_evaluation=True)

        # Assert
        metrics = monitoring_system.monitored_investments["AAPL"]
        assert metrics.current_grade == "B+"
        assert metrics.current_score == approx(0.82)
        assert len(monitoring_system.alert_history) == 1

        alert = monitoring_system.alert_history[0]
        assert alert.symbol == "AAPL"
        assert alert.previous_grade == "A+"
        assert alert.current_grade == "B+"
        assert alert.severity == AlertSeverity.CRITICAL  # A+ to B+ is critical

    @pytest.mark.asyncio
    async def test_should_evaluate_all_investments_when_requested(self, monitoring_system, sample_analysis, mock_scoring_tool):
        """Test evaluating all monitored investments."""
        # Arrange
        monitoring_system.add_investment_to_monitor("AAPL", "stock", sample_analysis)
        monitoring_system.add_investment_to_monitor("MSFT", "stock", sample_analysis)

        # Act
        results = await monitoring_system.evaluate_all_investments(force_evaluation=True)

        # Assert
        assert len(results) == 2
        assert "AAPL" in results
        assert "MSFT" in results
        assert mock_scoring_tool._run.call_count == 2

    def test_should_determine_alert_severity_correctly(self, monitoring_system):
        """Test alert severity determination logic."""
        # Critical: A+ to B+
        severity = monitoring_system._determine_alert_severity("A+", "B+", 0.96, 0.82)
        assert severity == AlertSeverity.CRITICAL

        # High: A+ to A
        severity = monitoring_system._determine_alert_severity("A+", "A", 0.96, 0.88)
        assert severity == AlertSeverity.HIGH

        # Medium: Moderate drop
        severity = monitoring_system._determine_alert_severity("A", "A", 0.90, 0.83)
        assert severity == AlertSeverity.MEDIUM

        # Low: Small drop
        severity = monitoring_system._determine_alert_severity("A", "A", 0.90, 0.87)
        assert severity == AlertSeverity.LOW

    def test_should_get_recent_alerts_when_requested(self, monitoring_system):
        """Test getting recent degradation alerts."""
        # Arrange - create some alerts
        old_alert = GradeDegradationAlert(
            symbol="OLD",
            asset_type="stock",
            previous_grade="A+",
            current_grade="A",
            previous_score=0.96,
            current_score=0.88,
            score_change=-0.08,
            severity=AlertSeverity.HIGH,
            alert_timestamp=datetime.now() - timedelta(hours=48),  # 2 days old
        )

        recent_alert = GradeDegradationAlert(
            symbol="RECENT",
            asset_type="stock",
            previous_grade="A+",
            current_grade="B+",
            previous_score=0.96,
            current_score=0.82,
            score_change=-0.14,
            severity=AlertSeverity.CRITICAL,
            alert_timestamp=datetime.now() - timedelta(hours=12),  # 12 hours old
        )

        monitoring_system.alert_history.extend([old_alert, recent_alert])

        # Act
        recent_alerts = monitoring_system.get_degradation_alerts(hours_back=24)

        # Assert
        assert len(recent_alerts) == 1
        assert recent_alerts[0].symbol == "RECENT"

    def test_should_generate_performance_summary_when_investments_exist(self, monitoring_system, sample_analysis):
        """Test performance summary generation."""
        # Arrange
        monitoring_system.add_investment_to_monitor("AAPL", "stock", sample_analysis)
        monitoring_system.add_investment_to_monitor("MSFT", "stock", sample_analysis)

        # Modify one investment to be degraded
        monitoring_system.monitored_investments["MSFT"].current_score = 0.80
        monitoring_system.monitored_investments["MSFT"].current_grade = "B+"

        # Act
        summary = monitoring_system.get_performance_summary()

        # Assert
        assert summary["total_investments"] == 2
        assert summary["a_plus_count"] == 1  # Only AAPL still A+
        assert summary["degraded_count"] == 1  # MSFT degraded
        assert summary["a_plus_percentage"] == approx(50.0)
        assert summary["monitoring_health"] == "needs_attention"

    def test_should_generate_empty_summary_when_no_investments(self, monitoring_system):
        """Test performance summary with no investments."""
        # Act
        summary = monitoring_system.get_performance_summary()

        # Assert
        assert summary["total_investments"] == 0
        assert summary["summary"] == "No investments currently monitored"

    @pytest.mark.asyncio
    async def test_should_update_market_regime_and_trigger_callbacks(self, monitoring_system):
        """Test market regime update and callback triggering."""
        # Arrange
        callback_called = False
        old_regime = None
        new_regime = None

        def test_callback(prev_regime, curr_regime):
            nonlocal callback_called, old_regime, new_regime
            callback_called = True
            old_regime = prev_regime
            new_regime = curr_regime

        monitoring_system.register_regime_change_callback(test_callback)

        # Set initial regime
        initial_regime = MarketRegime(
            regime_type="bull",
            vix_level=15.0,
            inflation_rate=2.0,
            interest_rate_trend="stable",
            market_stress_level="low",
        )
        await monitoring_system.update_market_regime(initial_regime)

        # Update to different regime
        new_market_regime = MarketRegime(
            regime_type="bear",
            vix_level=35.0,
            inflation_rate=5.0,
            interest_rate_trend="rising",
            market_stress_level="high",
        )

        # Act
        await monitoring_system.update_market_regime(new_market_regime)

        # Assert
        assert callback_called is True
        assert old_regime.regime_type == "bull"
        assert new_regime.regime_type == "bear"

    def test_should_validate_performance_metrics_schema(self):
        """Test PerformanceMetrics schema validation."""
        # Valid metrics
        metrics = PerformanceMetrics(
            symbol="AAPL",
            asset_type="stock",
            recommendation_date=datetime.now(),
            initial_grade="A+",
            current_grade="A+",
            initial_score=0.96,
            current_score=0.96,
            total_return=0.15,
            annualized_return=0.12,
            benchmark_return=0.10,
            alpha=0.02,
            sharpe_ratio=1.5,
            max_drawdown=-0.08,
        )

        assert metrics.symbol == "AAPL"
        assert metrics.asset_type == "stock"
        assert metrics.is_active is True

        # Invalid score (out of range)
        with pytest.raises(ValidationError):
            PerformanceMetrics(
                symbol="INVALID",
                asset_type="stock",
                recommendation_date=datetime.now(),
                initial_grade="A+",
                current_grade="A+",
                initial_score=1.5,  # Invalid: > 1.0
                current_score=0.96,
                total_return=0.15,
                annualized_return=0.12,
                benchmark_return=0.10,
                alpha=0.02,
                sharpe_ratio=1.5,
                max_drawdown=-0.08,
            )

    def test_should_validate_degradation_alert_schema(self):
        """Test GradeDegradationAlert schema validation."""
        # Valid alert
        alert = GradeDegradationAlert(
            symbol="AAPL",
            asset_type="stock",
            previous_grade="A+",
            current_grade="A",
            previous_score=0.96,
            current_score=0.88,
            score_change=-0.08,
            severity=AlertSeverity.HIGH,
        )

        assert alert.symbol == "AAPL"
        assert alert.severity == AlertSeverity.HIGH
        assert alert.score_change == approx(-0.08)

        # Invalid score (out of range)
        with pytest.raises(ValidationError):
            GradeDegradationAlert(
                symbol="INVALID",
                asset_type="stock",
                previous_grade="A+",
                current_grade="A",
                previous_score=1.5,  # Invalid: > 1.0
                current_score=0.88,
                score_change=-0.08,
                severity=AlertSeverity.HIGH,
            )

    def test_should_analyze_degradation_factors_correctly(self, monitoring_system):
        """Test degradation factor analysis."""
        # Large score drop
        factors = monitoring_system._analyze_degradation_factors("AAPL", 0.96, 0.80)
        assert "Significant fundamental deterioration" in factors

        # Moderate score drop
        factors = monitoring_system._analyze_degradation_factors("AAPL", 0.90, 0.83)
        assert "Moderate performance decline" in factors

        # Should always include some general factors
        assert len(factors) > 0
        assert all(isinstance(factor, str) for factor in factors)

    def test_should_generate_recommended_actions_based_on_grade(self, monitoring_system):
        """Test recommended actions generation."""
        # F grade - immediate exit
        actions = monitoring_system._generate_recommended_actions("AAPL", "F", [])
        assert any("immediate" in action.lower() for action in actions)

        # D grade - consider reduction
        actions = monitoring_system._generate_recommended_actions("AAPL", "D", [])
        assert any("reduction" in action.lower() for action in actions)

        # B+ grade - maintain but monitor
        actions = monitoring_system._generate_recommended_actions("AAPL", "B+", [])
        assert any("maintain" in action.lower() for action in actions)

        # Should always include some actions
        assert len(actions) > 0

    @pytest.mark.asyncio
    async def test_should_find_replacement_candidates_by_asset_type(self, monitoring_system):
        """Test finding replacement candidates."""
        # ETF replacements
        candidates = await monitoring_system._find_replacement_candidates("VTI", "etf")
        assert len(candidates) > 0
        assert "VTI" not in candidates  # Should not include the degraded symbol itself

        # Stock replacements
        candidates = await monitoring_system._find_replacement_candidates("AAPL", "stock")
        assert len(candidates) > 0
        assert "AAPL" not in candidates

        # Crypto replacements
        candidates = await monitoring_system._find_replacement_candidates("BTC-USD", "crypto")
        assert len(candidates) > 0
        assert "BTC-USD" not in candidates

    def test_should_detect_significant_regime_change(self, monitoring_system):
        """Test significant market regime change detection."""
        prev_regime = MarketRegime(
            regime_type="bull",
            vix_level=15.0,
            inflation_rate=2.0,
            interest_rate_trend="stable",
            market_stress_level="low",
        )

        # Significant change - regime type
        new_regime = MarketRegime(
            regime_type="bear",
            vix_level=15.0,
            inflation_rate=2.0,
            interest_rate_trend="stable",
            market_stress_level="low",
        )
        assert monitoring_system._is_significant_regime_change(prev_regime, new_regime) is True

        # Significant change - VIX jump
        new_regime = MarketRegime(
            regime_type="bull",
            vix_level=25.0,  # +10 points
            inflation_rate=2.0,
            interest_rate_trend="stable",
            market_stress_level="low",
        )
        assert monitoring_system._is_significant_regime_change(prev_regime, new_regime) is True

        # Minor change - not significant
        new_regime = MarketRegime(
            regime_type="bull",
            vix_level=17.0,  # +2 points
            inflation_rate=2.5,  # +0.5 points
            interest_rate_trend="stable",
            market_stress_level="low",
        )
        assert monitoring_system._is_significant_regime_change(prev_regime, new_regime) is False