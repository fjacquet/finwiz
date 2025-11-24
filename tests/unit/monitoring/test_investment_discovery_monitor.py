"""
Unit tests for Investment Discovery Monitor.

Tests the monitoring system for investment discovery operations,
including metrics collection, alerting, and dashboard functionality.
"""

from pytest import approx
from datetime import datetime, timedelta

import pytest

from finwiz.monitoring.investment_discovery_monitor import (
    DiscoveryMetrics,
    InvestmentDiscoveryMonitor,
    QualityMetrics,
    get_discovery_monitor,
    monitor_discovery_health,
)
from finwiz.schemas.investment_discovery import APlusDiscoveryResult, InvestmentCandidate


class TestInvestmentDiscoveryMonitor:
    """Test cases for InvestmentDiscoveryMonitor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = InvestmentDiscoveryMonitor(output_dir="test_output")

        # Create test discovery result
        self.test_candidate = InvestmentCandidate(
            symbol="TEST",
            name="Test Investment",
            asset_type="stock",
            current_price=100.0,
            market_cap=1000000000.0,
            preliminary_score=0.95,
            final_score=0.95,
            grade="A+",
            grade_description="Exceptional investment with outstanding fundamentals",
            recommended_action="BUY",
            data_source="test_data",
        )

        from finwiz.schemas.investment_discovery import APlusAnalysis, APlusCriteria, MarketRegime

        self.test_criteria = APlusCriteria()
        self.test_market_context = MarketRegime(regime_type="bull", vix_level=15.0, inflation_rate=2.5, interest_rate_trend="stable", market_stress_level="low")

        # Create APlusAnalysis with the test candidate
        self.test_analysis = APlusAnalysis(
            candidate=self.test_candidate,
            fundamental_score=0.95,
            technical_score=0.90,
            quality_score=0.92,
            risk_score=0.88,
            composite_score=0.95,
            confidence_level=0.90,
            is_a_plus_candidate=True,
            rationale=["Strong fundamentals", "Excellent technical indicators"],
        )

        self.test_result = APlusDiscoveryResult(
            asset_type="stock",
            total_screened=100,
            candidates_found=1,
            discovery_criteria=self.test_criteria,
            market_context=self.test_market_context,
            average_score=0.95,
            a_plus_percentage=1.0,
            a_plus_candidates=[self.test_analysis],
        )

    def test_should_initialize_monitor_with_default_values(self):
        """Test monitor initialization with default values."""
        monitor = InvestmentDiscoveryMonitor()

        assert monitor.discovery_metrics.total_discoveries == 0
        assert monitor.discovery_metrics.a_plus_discoveries == 0
        assert monitor.discovery_metrics.discovery_success_rate == approx(0.0)
        assert len(monitor.discovery_history) == 0
        assert len(monitor.alert_history) == 0

    def test_should_record_discovery_start(self, mocker):
        """Test recording discovery start."""
        discovery_id = "test_discovery_001"
        asset_type = "stock"

        mock_counter = mocker.patch.object(self.monitor.metrics_collector, "record_counter")
        self.monitor.record_discovery_start(discovery_id, asset_type)

        mock_counter.assert_called_once_with("discovery.started", tags={"asset_type": asset_type, "discovery_id": discovery_id})

    def test_should_record_successful_discovery_completion(self, mocker):
        """Test recording successful discovery completion."""
        discovery_id = "test_discovery_001"
        duration = 120.5

        mock_counter = mocker.patch.object(self.monitor.metrics_collector, "record_counter")
        mock_histogram = mocker.patch.object(self.monitor.metrics_collector, "record_histogram")
        mock_gauge = mocker.patch.object(self.monitor.metrics_collector, "record_gauge")

        self.monitor.record_discovery_completion(discovery_id, self.test_result, duration, success=True)

        # Check metrics updates
        assert self.monitor.discovery_metrics.total_discoveries == 1
        assert self.monitor.discovery_metrics.a_plus_discoveries == 1
        assert self.monitor.discovery_metrics.discovery_success_rate == approx(1.0)
        assert self.monitor.discovery_metrics.avg_discovery_time == duration
        assert len(self.monitor.discovery_times) == 1

        # Check grade distribution
        assert self.monitor.discovery_metrics.grade_distribution["A+"] == 1

        # Check asset type distribution
        assert self.monitor.discovery_metrics.asset_type_distribution["stock"] == 1

        # Check metrics collector calls
        mock_counter.assert_called_with("discovery.completed", tags={"asset_type": "stock", "success": "true"})
        mock_histogram.assert_called_with("discovery.duration", duration, tags={"asset_type": "stock"})
        mock_gauge.assert_called_with("discovery.a_plus_count", 1, tags={"asset_type": "stock"})

    def test_should_record_failed_discovery_completion(self, mocker):
        """Test recording failed discovery completion."""
        discovery_id = "test_discovery_002"
        duration = 60.0

        mock_counter = mocker.patch.object(self.monitor.metrics_collector, "record_counter")
        self.monitor.record_discovery_completion(discovery_id, self.test_result, duration, success=False)

        # Check error tracking
        assert self.monitor.discovery_metrics.discovery_errors == 1
        assert self.monitor.discovery_metrics.total_discoveries == 1
        assert self.monitor.discovery_metrics.discovery_success_rate == approx(0.0)

        # Check metrics collector call
        mock_counter.assert_called_with("discovery.failed", tags={"asset_type": "stock"})

    def test_should_record_validation_result(self, mocker):
        """Test recording validation results."""
        symbol = "TEST"
        validation_passed = True
        validation_score = 0.85

        mock_counter = mocker.patch.object(self.monitor.metrics_collector, "record_counter")
        mock_gauge = mocker.patch.object(self.monitor.metrics_collector, "record_gauge")

        self.monitor.record_validation_result(symbol, validation_passed, validation_score)

        mock_counter.assert_called_with("validation.completed", tags={"result": "pass"})
        mock_gauge.assert_called_with("validation.score", validation_score, tags={"symbol": symbol})

    def test_should_record_grade_change(self, mocker):
        """Test recording grade changes."""
        symbol = "TEST"
        old_grade = "A+"
        new_grade = "B+"
        days_since_discovery = 30

        mock_counter = mocker.patch.object(self.monitor.metrics_collector, "record_counter")
        self.monitor.record_grade_change(symbol, old_grade, new_grade, days_since_discovery)

        # Check grade change tracking
        assert len(self.monitor.grade_changes[symbol]) == 1
        change = self.monitor.grade_changes[symbol][0]
        assert change["old_grade"] == old_grade
        assert change["new_grade"] == new_grade
        assert change["days_since_discovery"] == days_since_discovery

        mock_counter.assert_called_with("grade.changed", tags={"from_grade": old_grade, "to_grade": new_grade, "symbol": symbol})

    def test_should_record_recommendation_feedback(self, mocker):
        """Test recording recommendation feedback."""
        symbol = "TEST"
        accepted = True
        portfolio_improvement = 0.15

        mock_counter = mocker.patch.object(self.monitor.metrics_collector, "record_counter")
        mock_gauge = mocker.patch.object(self.monitor.metrics_collector, "record_gauge")

        self.monitor.record_recommendation_feedback(symbol, accepted, portfolio_improvement)

        mock_counter.assert_called_with("recommendation.feedback", tags={"accepted": "true", "symbol": symbol})
        mock_gauge.assert_called_with("portfolio.improvement", portfolio_improvement, tags={"symbol": symbol})

    def test_should_check_alert_conditions_no_discoveries(self):
        """Test alert conditions when no discoveries have been made."""
        # Set last discovery time to more than 24 hours ago
        self.monitor.discovery_metrics.last_discovery_time = datetime.now() - timedelta(hours=25)

        alerts = self.monitor.check_alert_conditions()

        # Should trigger multiple alerts: discovery_rate, success_rate, and quality
        assert len(alerts) == 3
        alert_types = {alert["type"] for alert in alerts}
        assert "discovery_rate" in alert_types
        assert "success_rate" in alert_types
        assert "quality" in alert_types

        # Check discovery_rate alert
        discovery_alert = next(a for a in alerts if a["type"] == "discovery_rate")
        assert discovery_alert["severity"] == "warning"
        assert "No discoveries in" in discovery_alert["message"]

    def test_should_check_alert_conditions_high_error_rate(self):
        """Test alert conditions for high error rate."""
        # Set up high error rate scenario
        self.monitor.discovery_metrics.total_discoveries = 10
        self.monitor.discovery_metrics.discovery_errors = 2  # 20% error rate

        alerts = self.monitor.check_alert_conditions()

        error_alerts = [a for a in alerts if a["type"] == "error_rate"]
        assert len(error_alerts) == 1
        assert error_alerts[0]["severity"] == "critical"
        assert "High error rate" in error_alerts[0]["message"]

    def test_should_check_alert_conditions_low_success_rate(self):
        """Test alert conditions for low success rate."""
        # Set up low success rate scenario
        self.monitor.discovery_metrics.discovery_success_rate = 0.7  # 70% success rate

        alerts = self.monitor.check_alert_conditions()

        success_alerts = [a for a in alerts if a["type"] == "success_rate"]
        assert len(success_alerts) == 1
        assert success_alerts[0]["severity"] == "warning"
        assert "Low success rate" in success_alerts[0]["message"]

    def test_should_check_alert_conditions_slow_discovery(self):
        """Test alert conditions for slow discovery times."""
        # Set up slow discovery scenario
        self.monitor.discovery_times = [700.0, 800.0, 900.0]  # > 600s threshold
        self.monitor.discovery_metrics.avg_discovery_time = 800.0

        alerts = self.monitor.check_alert_conditions()

        performance_alerts = [a for a in alerts if a["type"] == "performance"]
        assert len(performance_alerts) == 1
        assert performance_alerts[0]["severity"] == "warning"
        assert "Slow discovery time" in performance_alerts[0]["message"]

    def test_should_get_dashboard_data(self, mocker):
        """Test getting dashboard data."""
        # Set up some test data
        self.monitor.discovery_metrics.total_discoveries = 5
        self.monitor.discovery_metrics.a_plus_discoveries = 2

        mock_perf = mocker.patch.object(self.monitor.metrics_collector, "get_performance_summary", return_value={"test": "performance"})
        mock_health = mocker.patch.object(self.monitor.metrics_collector, "get_health_status", return_value={"status": "healthy"})

        dashboard_data = self.monitor.get_dashboard_data()

        assert "discovery_metrics" in dashboard_data
        assert "quality_metrics" in dashboard_data
        assert "recent_alerts" in dashboard_data
        assert "performance_summary" in dashboard_data
        assert "health_status" in dashboard_data
        assert "timestamp" in dashboard_data

        assert dashboard_data["discovery_metrics"]["total_discoveries"] == 5
        assert dashboard_data["discovery_metrics"]["a_plus_discoveries"] == 2

    def test_should_export_metrics_json(self, mocker):
        """Test exporting metrics in JSON format."""
        mock_file = mocker.MagicMock()
        mock_open = mocker.patch("builtins.open", create=True)
        mock_open.return_value.__enter__.return_value = mock_file
        mock_json_dump = mocker.patch("json.dump")

        export_file = self.monitor.export_metrics("json")

        assert export_file.endswith(".json")
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once()

    def test_should_raise_error_for_unsupported_export_format(self):
        """Test error handling for unsupported export formats."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            self.monitor.export_metrics("xml")

    def test_should_update_calculated_metrics(self):
        """Test updating calculated metrics."""
        # Set up test data
        self.monitor.discovery_metrics.total_discoveries = 10
        self.monitor.discovery_metrics.discovery_errors = 2
        self.monitor.discovery_times = [100.0, 200.0, 300.0]

        self.monitor._update_calculated_metrics()

        assert self.monitor.discovery_metrics.discovery_success_rate == approx(0.8)  # 8/10
        assert self.monitor.discovery_metrics.avg_discovery_time == approx(200.0)  # (100+200+300)/3

    def test_should_update_quality_metrics(self):
        """Test updating quality metrics."""
        # Set up grade change data
        self.monitor.grade_changes["TEST1"] = [{"old_grade": "A+", "new_grade": "A+", "days_since_discovery": 30}]
        self.monitor.grade_changes["TEST2"] = [{"old_grade": "A+", "new_grade": "B+", "days_since_discovery": 45}]

        self.monitor._update_quality_metrics()

        # Should be 50% retention rate (1 out of 2 A+ stayed A+)
        assert self.monitor.quality_metrics.grade_retention_rate == approx(0.5)

    def test_should_store_discovery_record(self):
        """Test storing discovery records."""
        discovery_id = "test_001"
        duration = 150.0
        success = True

        initial_count = len(self.monitor.discovery_history)

        self.monitor._store_discovery_record(discovery_id, self.test_result, duration, success)

        assert len(self.monitor.discovery_history) == initial_count + 1

        record = self.monitor.discovery_history[-1]
        assert record["discovery_id"] == discovery_id
        assert record["duration"] == duration
        assert record["success"] == success
        assert record["asset_type"] == "stock"
        assert record["candidates_count"] == 1
        assert record["a_plus_count"] == 1


class TestGlobalMonitorFunctions:
    """Test cases for global monitor functions."""

    def test_should_get_discovery_monitor_singleton(self, mocker):
        """Test getting discovery monitor singleton."""
        monitor1 = get_discovery_monitor()
        monitor2 = get_discovery_monitor()

        assert monitor1 is monitor2

    @pytest.mark.asyncio
    async def test_should_monitor_discovery_health(self, mocker):
        """Test monitoring discovery health."""
        mock_monitor = mocker.MagicMock()
        mock_monitor.check_alert_conditions.return_value = []
        mock_monitor.metrics_collector.get_health_status.return_value = {"status": "healthy"}
        mock_monitor.get_dashboard_data.return_value = {
            "discovery_metrics": {"total_discoveries": 5},
            "quality_metrics": {"grade_retention_rate": 0.8},
        }
        mock_get_monitor = mocker.patch("finwiz.monitoring.investment_discovery_monitor.get_discovery_monitor", return_value=mock_monitor)

        health_data = await monitor_discovery_health()

        assert "health_status" in health_data
        assert "active_alerts" in health_data
        assert "discovery_metrics" in health_data
        assert "quality_metrics" in health_data

        assert health_data["health_status"]["status"] == "healthy"
        assert health_data["discovery_metrics"]["total_discoveries"] == 5


class TestDiscoveryMetrics:
    """Test cases for DiscoveryMetrics dataclass."""

    def test_should_initialize_with_defaults(self):
        """Test DiscoveryMetrics initialization with default values."""
        metrics = DiscoveryMetrics()

        assert metrics.total_discoveries == 0
        assert metrics.a_plus_discoveries == 0
        assert metrics.discovery_success_rate == approx(0.0)
        assert metrics.avg_discovery_time == approx(0.0)
        assert metrics.grade_distribution == {}
        assert metrics.asset_type_distribution == {}
        assert metrics.last_discovery_time is None
        assert metrics.discovery_errors == 0
        assert metrics.validation_pass_rate == approx(0.0)


class TestQualityMetrics:
    """Test cases for QualityMetrics dataclass."""

    def test_should_initialize_with_defaults(self):
        """Test QualityMetrics initialization with default values."""
        metrics = QualityMetrics()

        assert metrics.grade_retention_rate == approx(0.0)
        assert metrics.recommendation_acceptance_rate == approx(0.0)
        assert metrics.portfolio_improvement_rate == approx(0.0)
        assert metrics.false_positive_rate == approx(0.0)
        assert metrics.discovery_precision == approx(0.0)
        assert metrics.discovery_recall == approx(0.0)