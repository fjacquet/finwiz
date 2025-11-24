"""
Unit tests for AlertManager integration in flow orchestrator.

Tests the critical failure alert functionality when deep analysis
experiences high failure rates.
"""

from datetime import datetime

import pytest
from pytest import approx

from finwiz.monitoring.alerting import AlertManager, AlertSeverity, AlertType


class TestAlertManagerIntegration:
    """Test suite for AlertManager integration in flow orchestrator."""

    @pytest.mark.asyncio
    async def test_should_create_critical_alert_when_failure_rate_exceeds_50_percent(self, mocker):
        """Test that critical alert is created when failure rate > 50%."""
        # Arrange
        # Mock ConfigurationManager to avoid environment dependencies
        mock_config_manager = mocker.Mock()
        mock_config_manager.get_setting = mocker.Mock(side_effect=lambda key, default: default)
        mocker.patch("finwiz.monitoring.alerting.get_configuration_manager", return_value=mock_config_manager)

        alert_manager = AlertManager()

        failed_holdings = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META"]
        total_holdings = 10
        failure_rate = len(failed_holdings) / total_holdings

        # Act
        alert = await alert_manager.create_alert(
            alert_type=AlertType.ERROR_RATE,
            severity=AlertSeverity.CRITICAL,
            title=f"Critical: High Deep Analysis Failure Rate ({failure_rate:.1%})",
            message=(
                f"Deep portfolio analysis experienced a critical failure rate of {failure_rate:.1%}. "
                f"{len(failed_holdings)} out of {total_holdings} holdings failed analysis. "
                f"This may indicate systemic issues with data sources, API connectivity, or crew execution. "
                f"Immediate investigation recommended."
            ),
            metadata={
                "failed_holdings": failed_holdings,
                "total_holdings": total_holdings,
                "successful_holdings": 4,
                "failure_rate": failure_rate,
                "timeout_holdings": ["AAPL", "GOOGL"],
                "retry_counts": {"AAPL": 3, "GOOGL": 3, "MSFT": 2},
                "flow_uuid": "test-uuid",
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Assert
        assert alert is not None
        assert alert.type == AlertType.ERROR_RATE
        assert alert.severity == AlertSeverity.CRITICAL
        assert "60.0%" in alert.title
        assert "6 out of 10" in alert.message
        assert alert.metadata["failed_holdings"] == failed_holdings
        assert alert.metadata["total_holdings"] == 10
        assert alert.metadata["failure_rate"] == approx(0.6)

    def test_should_calculate_failure_rate_correctly(self):
        """Test that failure rate calculation is accurate."""
        # Arrange
        failed_holdings = ["TICK1", "TICK2", "TICK3", "TICK4", "TICK5", "TICK6", "TICK7", "TICK8", "TICK9", "TICK10", "TICK11"]
        total_holdings = 20

        # Act
        failure_rate = len(failed_holdings) / total_holdings

        # Assert
        assert failure_rate == approx(0.55)  # 11/20
        assert failure_rate > 0.5  # Should trigger alert

    @pytest.mark.asyncio
    async def test_should_include_comprehensive_metadata_in_alert(self, mocker):
        """Test that alert includes comprehensive metadata for debugging."""
        # Arrange
        # Mock ConfigurationManager to avoid environment dependencies
        mock_config_manager = mocker.Mock()
        mock_config_manager.get_setting = mocker.Mock(side_effect=lambda key, default: default)
        mocker.patch("finwiz.monitoring.alerting.get_configuration_manager", return_value=mock_config_manager)

        alert_manager = AlertManager()

        # Act
        alert = await alert_manager.create_alert(
            alert_type=AlertType.ERROR_RATE,
            severity=AlertSeverity.CRITICAL,
            title="Test Alert",
            message="Test message",
            metadata={
                "failed_holdings": ["AAPL", "GOOGL"],
                "total_holdings": 10,
                "successful_holdings": 8,
                "failure_rate": 0.2,
                "timeout_holdings": [],
                "retry_counts": {"AAPL": 2},
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Assert - Verify all required metadata fields
        assert "failed_holdings" in alert.metadata
        assert "total_holdings" in alert.metadata
        assert "successful_holdings" in alert.metadata
        assert "failure_rate" in alert.metadata
        assert "timeout_holdings" in alert.metadata
        assert "retry_counts" in alert.metadata
        assert "timestamp" in alert.metadata

        # Verify metadata values
        assert isinstance(alert.metadata["failed_holdings"], list)
        assert isinstance(alert.metadata["total_holdings"], int)
        assert isinstance(alert.metadata["successful_holdings"], int)
        assert isinstance(alert.metadata["failure_rate"], float)
        assert 0.0 <= alert.metadata["failure_rate"] <= 1.0

    def test_should_handle_zero_holdings_gracefully(self):
        """Test that alert logic handles zero holdings without errors."""
        # Arrange
        failed_holdings = []
        total_holdings = 0

        # Act - Calculate failure rate with zero holdings
        if total_holdings > 0:
            failure_rate = len(failed_holdings) / total_holdings
        else:
            failure_rate = 0.0

        # Assert - should not trigger alert (no division by zero)
        assert failure_rate == approx(0.0)
        assert failure_rate <= 0.5  # Would not trigger alert
