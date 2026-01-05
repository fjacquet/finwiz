"""
Unit tests for tool routing helpers.

Tests the externalized tool routing logic to ensure correct tool selection
based on asset class and optimization mode.
"""

import pytest

from finwiz.crews.helpers.tool_routing import (
    get_minimal_risk_tools,
    get_tools_for_asset_class,
)


class TestGetToolsForAssetClass:
    """Test suite for get_tools_for_asset_class function."""

    def test_should_return_tools_for_stock(self, mocker):
        """Test that tools are returned for stock asset class."""
        # Arrange
        mock_perf_config = mocker.patch("finwiz.crews.helpers.tool_routing.get_performance_config_manager")
        mock_perf_config.return_value.should_use_minimal_tools.return_value = False
        mock_stock_tools = mocker.patch("finwiz.crews.helpers.tool_routing.get_stock_crew_tools")
        mock_stock_tools.return_value = [mocker.Mock(), mocker.Mock()]
        mock_robust = mocker.patch("finwiz.crews.helpers.tool_routing.make_tools_robust")
        mock_robust.return_value = [mocker.Mock(), mocker.Mock()]

        # Act
        tools = get_tools_for_asset_class("stock")

        # Assert
        assert len(tools) == 2
        mock_stock_tools.assert_called_once()

    def test_should_return_tools_for_etf(self, mocker):
        """Test that tools are returned for ETF asset class."""
        # Arrange
        mock_perf_config = mocker.patch("finwiz.crews.helpers.tool_routing.get_performance_config_manager")
        mock_perf_config.return_value.should_use_minimal_tools.return_value = False
        mock_etf_tools = mocker.patch("finwiz.crews.helpers.tool_routing.get_etf_crew_tools")
        mock_etf_tools.return_value = [mocker.Mock(), mocker.Mock()]
        mock_robust = mocker.patch("finwiz.crews.helpers.tool_routing.make_tools_robust")
        mock_robust.return_value = [mocker.Mock(), mocker.Mock()]

        # Act
        tools = get_tools_for_asset_class("etf")

        # Assert
        assert len(tools) == 2
        mock_etf_tools.assert_called_once()

    def test_should_return_tools_for_crypto(self, mocker):
        """Test that tools are returned for crypto asset class."""
        # Arrange
        mock_perf_config = mocker.patch("finwiz.crews.helpers.tool_routing.get_performance_config_manager")
        mock_perf_config.return_value.should_use_minimal_tools.return_value = False
        mock_crypto_tools = mocker.patch("finwiz.crews.helpers.tool_routing.get_crypto_crew_tools")
        mock_crypto_tools.return_value = [mocker.Mock(), mocker.Mock()]
        mock_robust = mocker.patch("finwiz.crews.helpers.tool_routing.make_tools_robust")
        mock_robust.return_value = [mocker.Mock(), mocker.Mock()]

        # Act
        tools = get_tools_for_asset_class("crypto")

        # Assert
        assert len(tools) == 2
        mock_crypto_tools.assert_called_once()

    def test_should_raise_error_when_asset_class_is_invalid(self, mocker):
        """Test that ValueError is raised for invalid asset class."""
        # Arrange
        mock_perf_config = mocker.patch("finwiz.crews.helpers.tool_routing.get_performance_config_manager")
        mock_perf_config.return_value.should_use_minimal_tools.return_value = False
        mock_robust = mocker.patch("finwiz.crews.helpers.tool_routing.make_tools_robust")

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid asset_class"):
            get_tools_for_asset_class("invalid")

    def test_should_return_minimal_tools_when_minimal_is_true(self, mocker):
        """Test that minimal tools are returned when minimal=True."""
        # Arrange
        mock_perf_config = mocker.patch("finwiz.crews.helpers.tool_routing.get_performance_config_manager")
        mock_perf_config.return_value.should_use_minimal_tools.return_value = False
        mock_minimal = mocker.patch("finwiz.crews.helpers.tool_routing.get_minimal_risk_tools")
        mock_minimal.return_value = [mocker.Mock()]

        # Act
        tools = get_tools_for_asset_class("stock", minimal=True)

        # Assert
        assert len(tools) == 1
        mock_minimal.assert_called_once_with("stock", None)

    def test_should_pass_prefetched_data_to_tool_factories(self, mocker):
        """Test that prefetched data is passed to tool factories."""
        # Arrange
        mock_perf_config = mocker.patch("finwiz.crews.helpers.tool_routing.get_performance_config_manager")
        mock_perf_config.return_value.should_use_minimal_tools.return_value = False
        prefetched_data = {"AAPL": {"price": 150.0}}
        mock_stock_tools = mocker.patch("finwiz.crews.helpers.tool_routing.get_stock_crew_tools")
        mock_stock_tools.return_value = [mocker.Mock()]
        mock_robust = mocker.patch("finwiz.crews.helpers.tool_routing.make_tools_robust")
        mock_robust.return_value = [mocker.Mock()]

        # Act
        get_tools_for_asset_class("stock", prefetched_data=prefetched_data)

        # Assert - RAG params removed, only include_quantitative and prefetched_data remain
        mock_stock_tools.assert_called_once_with(
            include_quantitative=True,
            prefetched_data=prefetched_data,
        )


class TestGetMinimalRiskTools:
    """Test suite for get_minimal_risk_tools function."""

    def test_should_return_correct_number_of_tools(self, mocker):
        """Test that correct number of minimal tools are returned."""
        # Arrange - Mock the robust wrapper to return a fixed list
        mock_robust = mocker.patch("finwiz.crews.helpers.tool_routing.make_tools_robust")
        mock_robust.return_value = [mocker.Mock(), mocker.Mock(), mocker.Mock()]

        # Act
        tools = get_minimal_risk_tools("stock")

        # Assert
        assert len(tools) == 3
        # Verify make_tools_robust was called with a list of tools
        assert mock_robust.called
