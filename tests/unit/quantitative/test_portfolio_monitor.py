"""
Unit tests for portfolio monitoring system.

Tests cover portfolio drift monitoring, alert generation, and health dashboard functionality.
"""

from datetime import datetime, timedelta

import pytest

from finwiz.quantitative.portfolio_monitor import (
    AlertSeverity,
    AlertType,
    MonitoringRule,
    PortfolioAlert,
    PortfolioHealthDashboard,
    PortfolioMonitor,
    UrgencyLevel,
)
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioConfiguration,
    RebalancingNeed,
)


class TestPortfolioMonitor:
    """Test cases for PortfolioMonitor class."""

    @pytest.fixture
    def mock_price_service(self, mocker):
        """Mock price service."""
        mock_service = mocker.patch("finwiz.quantitative.portfolio_monitor.PortfolioPriceService")
        mock_service.return_value.get_current_prices = mocker.AsyncMock(return_value={"AAPL": 150.0, "GOOGL": 2500.0, "MSFT": 300.0})
        return mock_service.return_value

    @pytest.fixture
    def mock_portfolio_analyzer(self, mocker):
        """Mock portfolio analyzer."""
        mock_analyzer = mocker.patch("finwiz.quantitative.portfolio_monitor.PortfolioAnalyzer")
        return mock_analyzer

    @pytest.fixture
    def mock_rebalancing_engine(self, mocker):
        """Mock rebalancing engine."""
        mock_engine = mocker.patch("finwiz.quantitative.portfolio_monitor.RebalancingEngine")
        return mock_engine

    @pytest.fixture
    def sample_portfolio_config(self):
        """Sample portfolio configuration."""
        return PortfolioConfiguration(
            holdings=[Holding(symbol="AAPL", shares=100), Holding(symbol="GOOGL", shares=10), Holding(symbol="MSFT", shares=50)],
            target_weights={"AAPL": 0.4, "GOOGL": 0.4, "MSFT": 0.2},
            global_tolerance=0.05,
        )

    @pytest.fixture
    def sample_rebalancing_needs(self):
        """Sample rebalancing needs."""
        return [
            RebalancingNeed(
                symbol="AAPL",
                current_weight=0.35,
                target_weight=0.4,
                deviation=-0.05,
                tolerance_band=0.05,
                needs_rebalancing=False,
                urgency_score=0.3,
            ),
            RebalancingNeed(
                symbol="GOOGL",
                current_weight=0.5,
                target_weight=0.4,
                deviation=0.1,
                tolerance_band=0.05,
                needs_rebalancing=True,
                urgency_score=0.8,
            ),
            RebalancingNeed(
                symbol="MSFT",
                current_weight=0.15,
                target_weight=0.2,
                deviation=-0.05,
                tolerance_band=0.05,
                needs_rebalancing=False,
                urgency_score=0.3,
            ),
        ]

    @pytest.fixture
    def portfolio_monitor(self, mock_price_service, mock_portfolio_analyzer, mock_rebalancing_engine):
        """Portfolio monitor instance."""
        return PortfolioMonitor(price_service=mock_price_service, portfolio_analyzer=mock_portfolio_analyzer, rebalancing_engine=mock_rebalancing_engine)

    def test_should_initialize_portfolio_monitor_when_created(self, portfolio_monitor):
        """Test portfolio monitor initialization."""
        # Assert
        assert portfolio_monitor is not None
        assert portfolio_monitor._monitoring_tasks == {}
        assert portfolio_monitor._monitoring_rules == {}
        assert portfolio_monitor._alert_history == {}
        assert portfolio_monitor._last_check_times == {}

    @pytest.mark.asyncio
    async def test_should_start_monitoring_when_valid_config_provided(self, portfolio_monitor, sample_portfolio_config):
        """Test starting portfolio monitoring."""
        # Arrange
        portfolio_id = "test_portfolio"
        monitoring_rule = MonitoringRule(rule_id="test_rule", rule_name="Test Rule", min_check_interval_hours=1)

        # Act
        await portfolio_monitor.start_monitoring(portfolio_id, sample_portfolio_config, monitoring_rule)

        # Assert
        assert portfolio_id in portfolio_monitor._monitoring_rules
        assert portfolio_id in portfolio_monitor._monitoring_tasks
        assert portfolio_monitor._monitoring_rules[portfolio_id] == monitoring_rule

    @pytest.mark.asyncio
    async def test_should_stop_monitoring_when_requested(self, portfolio_monitor, sample_portfolio_config):
        """Test stopping portfolio monitoring."""
        # Arrange
        portfolio_id = "test_portfolio"
        await portfolio_monitor.start_monitoring(portfolio_id, sample_portfolio_config)

        # Act
        await portfolio_monitor.stop_monitoring(portfolio_id)

        # Assert
        assert portfolio_id not in portfolio_monitor._monitoring_tasks
        assert portfolio_id not in portfolio_monitor._monitoring_rules

    @pytest.mark.asyncio
    async def test_should_check_portfolio_drift_when_requested(self, mocker, portfolio_monitor, mock_portfolio_analyzer, sample_portfolio_config, sample_rebalancing_needs):
        """Test portfolio drift checking."""
        # Arrange
        portfolio_id = "test_portfolio"

        # Create mock analysis result with weightings
        mock_analysis = mocker.Mock()
        mock_analysis.weightings = {"AAPL": 0.35, "GOOGL": 0.5, "MSFT": 0.15}

        mock_portfolio_analyzer.analyze_current_portfolio.return_value = mock_analysis
        mock_portfolio_analyzer.identify_rebalancing_needs.return_value = sample_rebalancing_needs

        # Act
        result = await portfolio_monitor.check_portfolio_drift(portfolio_id, sample_portfolio_config)

        # Assert
        assert result == sample_rebalancing_needs
        assert portfolio_id in portfolio_monitor._last_check_times

    @pytest.mark.asyncio
    async def test_should_generate_health_dashboard_when_requested(self, mocker, portfolio_monitor, sample_portfolio_config, sample_rebalancing_needs):
        """Test health dashboard generation."""
        # Arrange
        portfolio_id = "test_portfolio"
        portfolio_monitor.check_portfolio_drift = mocker.AsyncMock(return_value=sample_rebalancing_needs)

        # Act
        dashboard = await portfolio_monitor.generate_health_dashboard(portfolio_id, sample_portfolio_config)

        # Assert
        assert isinstance(dashboard, PortfolioHealthDashboard)
        assert dashboard.portfolio_id == portfolio_id
        assert dashboard.max_deviation == 0.1  # From GOOGL deviation
        assert dashboard.rebalancing_urgency == UrgencyLevel.LOW
        assert len(dashboard.positions_needing_attention) == 1  # Only GOOGL exceeds tolerance

    def test_should_calculate_correct_health_score_when_no_deviations(self, portfolio_monitor):
        """Test health score calculation with no deviations."""
        # Arrange
        rebalancing_needs = []
        portfolio_config = PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100)], target_weights={"AAPL": 1.0})

        # Act
        health_score = portfolio_monitor._calculate_health_score(rebalancing_needs, portfolio_config)

        # Assert
        assert health_score == 10.0

    def test_should_calculate_correct_health_score_when_minor_deviations(self, portfolio_monitor, sample_rebalancing_needs, sample_portfolio_config):
        """Test health score calculation with minor deviations."""
        # Act
        health_score = portfolio_monitor._calculate_health_score(sample_rebalancing_needs, sample_portfolio_config)

        # Assert
        assert 5.0 <= health_score <= 9.0  # Should be in reasonable range

    def test_should_determine_correct_urgency_when_no_positions_need_attention(self, portfolio_monitor):
        """Test urgency determination with no positions needing attention."""
        # Arrange
        positions_needing_attention = []
        max_deviation = 0.02

        # Act
        urgency = portfolio_monitor._determine_rebalancing_urgency(positions_needing_attention, max_deviation)

        # Assert
        assert urgency == UrgencyLevel.LOW

    def test_should_determine_correct_urgency_when_critical_deviation(self, portfolio_monitor, mocker):
        """Test urgency determination with critical deviation."""
        # Arrange
        positions_needing_attention = [mocker.MagicMock()]
        max_deviation = 0.25

        # Act
        urgency = portfolio_monitor._determine_rebalancing_urgency(positions_needing_attention, max_deviation)

        # Assert
        assert urgency == UrgencyLevel.CRITICAL

    def test_should_determine_correct_urgency_when_high_deviation(self, portfolio_monitor, mocker):
        """Test urgency determination with high deviation."""
        # Arrange
        positions_needing_attention = [mocker.MagicMock()]
        max_deviation = 0.18

        # Act
        urgency = portfolio_monitor._determine_rebalancing_urgency(positions_needing_attention, max_deviation)

        # Assert
        assert urgency == UrgencyLevel.HIGH

    def test_should_determine_correct_urgency_when_multiple_positions(self, portfolio_monitor, mocker):
        """Test urgency determination with multiple positions."""
        # Arrange
        positions_needing_attention = [mocker.MagicMock(), mocker.MagicMock(), mocker.MagicMock()]
        max_deviation = 0.08

        # Act
        urgency = portfolio_monitor._determine_rebalancing_urgency(positions_needing_attention, max_deviation)

        # Assert
        assert urgency == UrgencyLevel.MEDIUM

    def test_should_get_correct_health_status_description_when_excellent_score(self, portfolio_monitor):
        """Test health status description for excellent score."""
        # Act
        description = portfolio_monitor._get_health_status_description(9.5)

        # Assert
        assert "Excellent" in description

    def test_should_get_correct_health_status_description_when_poor_score(self, portfolio_monitor):
        """Test health status description for poor score."""
        # Act
        description = portfolio_monitor._get_health_status_description(2.5)

        # Assert
        assert "Critical" in description

    @pytest.mark.asyncio
    async def test_should_generate_alert_when_called(self, portfolio_monitor):
        """Test alert generation."""
        # Arrange
        portfolio_id = "test_portfolio"
        alert_type = AlertType.DEVIATION_ALERT
        severity = AlertSeverity.WARNING
        title = "Test Alert"
        message = "Test message"
        affected_positions = ["AAPL", "GOOGL"]
        current_deviations = {"AAPL": 0.05, "GOOGL": 0.08}
        recommended_actions = ["Review portfolio", "Consider rebalancing"]

        # Act
        alert = await portfolio_monitor._generate_alert(
            portfolio_id=portfolio_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            affected_positions=affected_positions,
            current_deviations=current_deviations,
            recommended_actions=recommended_actions,
        )

        # Assert
        assert isinstance(alert, PortfolioAlert)
        assert alert.portfolio_id == portfolio_id
        assert alert.alert_type == alert_type
        assert alert.severity == severity
        assert alert.title == title
        assert alert.message == message
        assert alert.affected_positions == affected_positions
        assert alert.current_deviations == current_deviations
        assert alert.recommended_actions == recommended_actions
        assert not alert.acknowledged
        assert not alert.resolved

    @pytest.mark.asyncio
    async def test_should_acknowledge_alert_when_valid_alert_id_provided(self, portfolio_monitor):
        """Test alert acknowledgment."""
        # Arrange
        portfolio_id = "test_portfolio"
        alert = await portfolio_monitor._generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.DEVIATION_ALERT,
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            message="Test message",
            affected_positions=[],
            current_deviations={},
            recommended_actions=[],
        )

        # Act
        result = await portfolio_monitor.acknowledge_alert(portfolio_id, alert.alert_id)

        # Assert
        assert result is True
        assert alert.acknowledged is True

    @pytest.mark.asyncio
    async def test_should_not_acknowledge_alert_when_invalid_alert_id_provided(self, portfolio_monitor):
        """Test alert acknowledgment with invalid ID."""
        # Arrange
        portfolio_id = "test_portfolio"

        # Act
        result = await portfolio_monitor.acknowledge_alert(portfolio_id, "invalid_alert_id")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_should_resolve_alert_when_valid_alert_id_provided(self, portfolio_monitor):
        """Test alert resolution."""
        # Arrange
        portfolio_id = "test_portfolio"
        resolution_notes = "Issue resolved by rebalancing"
        alert = await portfolio_monitor._generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.DEVIATION_ALERT,
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            message="Test message",
            affected_positions=[],
            current_deviations={},
            recommended_actions=[],
        )

        # Act
        result = await portfolio_monitor.resolve_alert(portfolio_id, alert.alert_id, resolution_notes)

        # Assert
        assert result is True
        assert alert.resolved is True
        assert alert.resolution_notes == resolution_notes

    @pytest.mark.asyncio
    async def test_should_get_active_alerts_when_requested(self, portfolio_monitor):
        """Test getting active alerts."""
        # Arrange
        portfolio_id = "test_portfolio"

        # Generate resolved alert
        resolved_alert = await portfolio_monitor._generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.DEVIATION_ALERT,
            severity=AlertSeverity.WARNING,
            title="Resolved Alert",
            message="Test message",
            affected_positions=[],
            current_deviations={},
            recommended_actions=[],
        )
        resolved_alert.resolved = True

        # Generate active alert
        active_alert = await portfolio_monitor._generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.MULTIPLE_POSITIONS_ALERT,
            severity=AlertSeverity.ERROR,
            title="Active Alert",
            message="Test message",
            affected_positions=[],
            current_deviations={},
            recommended_actions=[],
        )

        # Act
        active_alerts = await portfolio_monitor.get_active_alerts(portfolio_id)

        # Assert
        assert len(active_alerts) == 1
        assert active_alerts[0] == active_alert

    def test_should_get_monitoring_statistics_when_requested(self, portfolio_monitor):
        """Test getting monitoring statistics."""
        # Act
        stats = portfolio_monitor.get_monitoring_statistics()

        # Assert
        assert isinstance(stats, dict)
        assert "total_portfolios_monitored" in stats
        assert "active_monitoring_tasks" in stats
        assert "total_alerts_generated" in stats
        assert "monitoring_rules_configured" in stats
        assert stats["total_portfolios_monitored"] == 0  # No portfolios monitored yet


class TestMonitoringRule:
    """Test cases for MonitoringRule class."""

    def test_should_create_monitoring_rule_when_valid_data_provided(self):
        """Test monitoring rule creation with valid data."""
        # Arrange & Act
        rule = MonitoringRule(
            rule_id="test_rule",
            rule_name="Test Rule",
            max_deviation_threshold=0.08,
            min_check_interval_hours=2,
            alert_on_deviation=True,
            alert_on_multiple_positions=True,
            min_positions_for_alert=3,
            enable_auto_rebalancing=False,
            auto_rebalance_threshold=0.12,
            max_auto_rebalance_frequency_days=14,
        )

        # Assert
        assert rule.rule_id == "test_rule"
        assert rule.rule_name == "Test Rule"
        assert rule.max_deviation_threshold == 0.08
        assert rule.min_check_interval_hours == 2
        assert rule.alert_on_deviation is True
        assert rule.alert_on_multiple_positions is True
        assert rule.min_positions_for_alert == 3
        assert rule.enable_auto_rebalancing is False
        assert rule.auto_rebalance_threshold == 0.12
        assert rule.max_auto_rebalance_frequency_days == 14

    def test_should_use_default_values_when_not_specified(self):
        """Test monitoring rule creation with default values."""
        # Arrange & Act
        rule = MonitoringRule(rule_id="test_rule", rule_name="Test Rule")

        # Assert
        assert rule.enabled is True
        assert rule.max_deviation_threshold == 0.10
        assert rule.min_check_interval_hours == 1
        assert rule.alert_on_deviation is True
        assert rule.alert_on_multiple_positions is True
        assert rule.min_positions_for_alert == 2
        assert rule.enable_auto_rebalancing is False
        assert rule.auto_rebalance_threshold == 0.15
        assert rule.max_auto_rebalance_frequency_days == 7

    def test_should_raise_validation_error_when_invalid_threshold_provided(self):
        """Test monitoring rule validation with invalid threshold."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            MonitoringRule(
                rule_id="test_rule",
                rule_name="Test Rule",
                max_deviation_threshold=1.5,  # Invalid: > 1.0
            )

    def test_should_raise_validation_error_when_invalid_interval_provided(self):
        """Test monitoring rule validation with invalid interval."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            MonitoringRule(
                rule_id="test_rule",
                rule_name="Test Rule",
                min_check_interval_hours=0,  # Invalid: < 1
            )


class TestPortfolioAlert:
    """Test cases for PortfolioAlert class."""

    def test_should_create_portfolio_alert_when_valid_data_provided(self):
        """Test portfolio alert creation with valid data."""
        # Arrange & Act
        alert = PortfolioAlert(
            alert_id="test_alert_123",
            portfolio_id="test_portfolio",
            alert_type=AlertType.DEVIATION_ALERT,
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            message="Test alert message",
            affected_positions=["AAPL", "GOOGL"],
            current_deviations={"AAPL": 0.05, "GOOGL": -0.03},
            recommended_actions=["Review portfolio", "Consider rebalancing"],
        )

        # Assert
        assert alert.alert_id == "test_alert_123"
        assert alert.portfolio_id == "test_portfolio"
        assert alert.alert_type == AlertType.DEVIATION_ALERT
        assert alert.severity == AlertSeverity.WARNING
        assert alert.title == "Test Alert"
        assert alert.message == "Test alert message"
        assert alert.affected_positions == ["AAPL", "GOOGL"]
        assert alert.current_deviations == {"AAPL": 0.05, "GOOGL": -0.03}
        assert alert.recommended_actions == ["Review portfolio", "Consider rebalancing"]
        assert alert.acknowledged is False
        assert alert.resolved is False
        assert alert.resolution_notes is None

    def test_should_have_timestamp_when_created(self):
        """Test that alert has timestamp when created."""
        # Arrange & Act
        alert = PortfolioAlert(
            alert_id="test_alert_123",
            portfolio_id="test_portfolio",
            alert_type=AlertType.DEVIATION_ALERT,
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            message="Test alert message",
        )

        # Assert
        assert isinstance(alert.timestamp, datetime)
        assert alert.timestamp <= datetime.now()


class TestPortfolioHealthDashboard:
    """Test cases for PortfolioHealthDashboard class."""

    def test_should_create_health_dashboard_when_valid_data_provided(self):
        """Test health dashboard creation with valid data."""
        # Arrange
        from finwiz.quantitative.portfolio_monitor import MonitoringStatus

        monitoring_status = MonitoringStatus(
            portfolio_id="test_portfolio",
            last_check_timestamp=datetime.now(),
            next_check_timestamp=datetime.now() + timedelta(hours=1),
            monitoring_active=True,
            positions_monitored=4,
            positions_out_of_tolerance=1,
            active_alerts=0,
            unacknowledged_alerts=0,
            price_data_freshness_minutes=5,
            monitoring_health_score=8.5,
        )

        rebalancing_need = RebalancingNeed(
            symbol="AAPL",
            current_weight=0.35,
            target_weight=0.4,
            deviation=-0.05,
            tolerance_band=0.05,
            needs_rebalancing=True,
            urgency_score=0.8,
        )

        # Act
        dashboard = PortfolioHealthDashboard(
            portfolio_id="test_portfolio",
            overall_health_score=7.5,
            health_status="Good - Minor deviations within acceptable range",
            max_deviation=0.08,
            avg_deviation=0.04,
            positions_needing_attention=[rebalancing_need],
            rebalancing_urgency=UrgencyLevel.MEDIUM,
            estimated_rebalancing_cost=25.50,
            days_since_last_rebalance=14,
            monitoring_status=monitoring_status,
            recent_alerts=[],
        )

        # Assert
        assert dashboard.portfolio_id == "test_portfolio"
        assert dashboard.overall_health_score == 7.5
        assert dashboard.health_status == "Good - Minor deviations within acceptable range"
        assert dashboard.max_deviation == 0.08
        assert dashboard.avg_deviation == 0.04
        assert len(dashboard.positions_needing_attention) == 1
        assert dashboard.rebalancing_urgency == UrgencyLevel.MEDIUM
        assert dashboard.estimated_rebalancing_cost == 25.50
        assert dashboard.days_since_last_rebalance == 14
        assert dashboard.monitoring_status == monitoring_status
        assert dashboard.recent_alerts == []

    def test_should_have_dashboard_timestamp_when_created(self):
        """Test that dashboard has timestamp when created."""
        # Arrange
        from finwiz.quantitative.portfolio_monitor import MonitoringStatus

        monitoring_status = MonitoringStatus(
            portfolio_id="test_portfolio",
            last_check_timestamp=datetime.now(),
            next_check_timestamp=datetime.now() + timedelta(hours=1),
            monitoring_active=True,
            positions_monitored=0,
            positions_out_of_tolerance=0,
            active_alerts=0,
            unacknowledged_alerts=0,
            price_data_freshness_minutes=5,
            monitoring_health_score=8.5,
        )

        # Act
        dashboard = PortfolioHealthDashboard(
            portfolio_id="test_portfolio",
            overall_health_score=8.0,
            health_status="Good",
            max_deviation=0.03,
            avg_deviation=0.02,
            positions_needing_attention=[],
            rebalancing_urgency=UrgencyLevel.LOW,
            estimated_rebalancing_cost=0.0,
            monitoring_status=monitoring_status,
        )

        # Assert
        assert isinstance(dashboard.dashboard_timestamp, datetime)
        assert dashboard.dashboard_timestamp <= datetime.now()
