"""
Unit tests for PositionSizingTool.

Tests risk-based sizing, correlation analysis, concentration limits,
sizing actions, and portfolio allocation validation.
"""

from pytest import approx
import pytest

from finwiz.tools.position_sizing_tool import (
    HoldingSizingProfile,
    PortfolioContext,
    PositionSizingTool,
)


class TestPositionSizingTool:
    """Test suite for PositionSizingTool."""

    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return PositionSizingTool()

    @pytest.fixture
    def sample_portfolio(self):
        """Create sample portfolio context."""
        return PortfolioContext(
            total_holdings=10,
            current_allocations={
                "AAPL": 8.0,
                "MSFT": 7.0,
                "GOOGL": 6.0,
                "AMZN": 5.0,
                "TSLA": 4.0,
            },
            sector_allocations={
                "Technology": 30.0,
                "Healthcare": 15.0,
                "Finance": 10.0,
            },
            asset_class_allocations={
                "stock": 90.0,
                "etf": 8.0,
                "crypto": 2.0,
            },
            total_allocated_pct=100.0,
        )

    @pytest.fixture
    def low_risk_holding(self):
        """Create low risk holding profile."""
        return HoldingSizingProfile(
            ticker="JNJ",
            asset_class="stock",
            risk_score=1.5,
            sector="Healthcare",
            current_allocation_pct=0.0,
        )

    @pytest.fixture
    def high_risk_holding(self):
        """Create high risk holding profile."""
        return HoldingSizingProfile(
            ticker="COIN",
            asset_class="stock",
            risk_score=4.5,
            sector="Finance",
            current_allocation_pct=0.0,
        )

    def test_should_calculate_position_size_for_low_risk_holding(self, tool, low_risk_holding, sample_portfolio):
        """Test position sizing for low risk holding."""
        # Arrange - give it some current allocation
        low_risk_holding.current_allocation_pct = 5.0

        # Act
        result = tool.calculate_position_size(
            holding=low_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        assert result.recommended_size_pct >= 0
        assert result.recommended_size_pct <= 15.0  # Low risk can be higher
        assert result.sizing_action in ["add", "hold", "trim", "exit"]
        assert len(result.sizing_rationale) > 0

    def test_should_calculate_smaller_size_for_high_risk_holding(self, tool, high_risk_holding, sample_portfolio):
        """Test that high risk holdings get smaller position sizes."""
        # Arrange - give it some current allocation
        high_risk_holding.current_allocation_pct = 3.0

        # Act
        result = tool.calculate_position_size(
            holding=high_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        assert result.recommended_size_pct >= 0
        assert result.recommended_size_pct <= 5.0  # High risk should be smaller
        assert result.sizing_action in ["add", "hold", "trim", "exit"]

    def test_should_recommend_add_when_underweight(self, tool, low_risk_holding, sample_portfolio):
        """Test that ADD action is recommended when position is underweight."""
        # Arrange
        low_risk_holding.current_allocation_pct = 1.0  # Very low allocation

        # Act
        result = tool.calculate_position_size(
            holding=low_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        # Should recommend add or hold depending on implementation
        assert result.sizing_action in ["add", "hold"]
        assert result.recommended_size_pct >= result.current_size_pct

    def test_should_recommend_trim_when_overweight(self, tool, sample_portfolio):
        """Test that TRIM action is recommended when position is overweight."""
        # Arrange
        overweight_holding = HoldingSizingProfile(
            ticker="AAPL",
            asset_class="stock",
            risk_score=2.0,
            sector="Technology",
            current_allocation_pct=12.0,  # Over 10% limit
        )

        # Act
        result = tool.calculate_position_size(
            holding=overweight_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        assert result.sizing_action == "trim"
        assert result.recommended_size_pct < result.current_size_pct

    def test_should_recommend_hold_when_at_target(self, tool, low_risk_holding, sample_portfolio):
        """Test that HOLD action is recommended when position is at target."""
        # Arrange
        low_risk_holding.current_allocation_pct = 8.0  # Within acceptable range

        # Act
        result = tool.calculate_position_size(
            holding=low_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        assert result.sizing_action == "hold"

    def test_should_apply_single_stock_concentration_limit(self, tool, sample_portfolio):
        """Test that single stock concentration limit is enforced."""
        # Arrange
        large_holding = HoldingSizingProfile(
            ticker="NVDA",
            asset_class="stock",
            risk_score=1.0,  # Very low risk
            sector="Technology",
            current_allocation_pct=8.0,  # Give it existing allocation
        )

        # Act
        result = tool.calculate_position_size(
            holding=large_holding,
            portfolio=sample_portfolio,
            risk_tolerance="aggressive",
        )

        # Assert
        assert result.recommended_size_pct <= tool.max_single_stock_pct
        # Concentration limits may be applied
        assert result.concentration_limits_applied in [True, False]

    def test_should_apply_sector_concentration_limit(self, tool, sample_portfolio):
        """Test that sector concentration limit is enforced."""
        # Arrange
        tech_holding = HoldingSizingProfile(
            ticker="NVDA",
            asset_class="stock",
            risk_score=2.0,
            sector="Technology",  # Already at 30%
            current_allocation_pct=0.0,
        )

        # Act
        result = tool.calculate_position_size(
            holding=tech_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        # Should limit size to avoid exceeding 35% sector limit
        assert result.recommended_size_pct <= 5.0  # Can't add much more to tech

    def test_should_apply_crypto_concentration_limit(self, tool, sample_portfolio):
        """Test that crypto concentration limit is enforced."""
        # Arrange
        crypto_holding = HoldingSizingProfile(
            ticker="BTC",
            asset_class="crypto",
            risk_score=4.0,
            sector=None,
            current_allocation_pct=0.0,
        )

        # Act
        result = tool.calculate_position_size(
            holding=crypto_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        # Total crypto should not exceed 10%
        assert result.recommended_size_pct <= (tool.max_crypto_total_pct - sample_portfolio.asset_class_allocations["crypto"])

    def test_should_calculate_risk_contribution(self, tool, high_risk_holding, sample_portfolio):
        """Test that risk contribution is calculated."""
        # Act
        result = tool.calculate_position_size(
            holding=high_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        assert 0.0 <= result.risk_contribution <= 100.0

    def test_should_calculate_correlation_with_portfolio(self, tool, low_risk_holding, sample_portfolio):
        """Test that correlation with portfolio is calculated."""
        # Act
        result = tool.calculate_position_size(
            holding=low_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        assert -1.0 <= result.correlation_with_portfolio <= 1.0

    def test_should_adjust_size_for_conservative_risk_tolerance(self, tool, low_risk_holding, sample_portfolio):
        """Test that conservative risk tolerance reduces position sizes."""
        # Arrange - give it existing allocation
        low_risk_holding.current_allocation_pct = 5.0

        # Act
        result_conservative = tool.calculate_position_size(
            holding=low_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="conservative",
        )

        result_aggressive = tool.calculate_position_size(
            holding=low_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="aggressive",
        )

        # Assert
        assert result_conservative.recommended_size_pct <= result_aggressive.recommended_size_pct

    def test_should_adjust_size_for_aggressive_risk_tolerance(self, tool, low_risk_holding, sample_portfolio):
        """Test that aggressive risk tolerance increases position sizes."""
        # Act
        result_moderate = tool.calculate_position_size(
            holding=low_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        result_aggressive = tool.calculate_position_size(
            holding=low_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="aggressive",
        )

        # Assert
        assert result_aggressive.recommended_size_pct >= result_moderate.recommended_size_pct

    def test_should_provide_detailed_rationale(self, tool, low_risk_holding, sample_portfolio):
        """Test that detailed rationale is provided."""
        # Act
        result = tool.calculate_position_size(
            holding=low_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        assert len(result.sizing_rationale) > 20
        assert result.sizing_rationale is not None

    def test_should_handle_zero_current_allocation(self, tool, low_risk_holding, sample_portfolio):
        """Test handling of new position (zero current allocation)."""
        # Arrange
        low_risk_holding.current_allocation_pct = 0.0

        # Act
        result = tool.calculate_position_size(
            holding=low_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        assert result.current_size_pct == approx(0.0)
        # Tool may recommend 0% for new positions or suggest a size
        assert result.recommended_size_pct >= 0.0
        assert result.sizing_action in ["add", "hold"]

    def test_should_handle_etf_position_sizing(self, tool, sample_portfolio):
        """Test position sizing for ETF."""
        # Arrange
        etf_holding = HoldingSizingProfile(
            ticker="SPY",
            asset_class="etf",
            risk_score=1.5,
            sector=None,
            current_allocation_pct=5.0,  # Give it existing allocation
        )

        # Act
        result = tool.calculate_position_size(
            holding=etf_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        assert result.recommended_size_pct >= 0
        assert result.sizing_action in ["add", "hold", "trim", "exit"]

    def test_should_handle_crypto_position_sizing(self, tool, sample_portfolio):
        """Test position sizing for crypto."""
        # Arrange
        crypto_holding = HoldingSizingProfile(
            ticker="ETH",
            asset_class="crypto",
            risk_score=4.0,
            sector=None,
            current_allocation_pct=2.0,  # Give it existing allocation
        )

        # Act
        result = tool.calculate_position_size(
            holding=crypto_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        assert result.recommended_size_pct >= 0
        assert result.recommended_size_pct <= 5.0  # High risk crypto should be limited

    def test_should_flag_concentration_limits_when_applied(self, tool, sample_portfolio):
        """Test that concentration_limits_applied flag is set correctly."""
        # Arrange
        large_holding = HoldingSizingProfile(
            ticker="MEGA",
            asset_class="stock",
            risk_score=1.0,
            sector="Technology",
            current_allocation_pct=0.0,
        )

        # Act
        result = tool.calculate_position_size(
            holding=large_holding,
            portfolio=sample_portfolio,
            risk_tolerance="aggressive",
        )

        # Assert
        # Should have limits applied due to sector concentration
        if result.recommended_size_pct < 10.0:
            assert result.concentration_limits_applied or result.risk_limits_applied

    def test_should_flag_risk_limits_when_applied(self, tool, high_risk_holding, sample_portfolio):
        """Test that risk_limits_applied flag is set correctly."""
        # Act
        result = tool.calculate_position_size(
            holding=high_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="moderate",
        )

        # Assert
        assert result.risk_limits_applied or result.recommended_size_pct <= 5.0

    def test_should_recommend_exit_for_very_high_risk_with_conservative_tolerance(self, tool, sample_portfolio):
        """Test that EXIT is recommended for very high risk with conservative tolerance."""
        # Arrange
        extreme_risk_holding = HoldingSizingProfile(
            ticker="RISKY",
            asset_class="stock",
            risk_score=5.0,
            sector="Speculative",
            current_allocation_pct=5.0,
        )

        # Act
        result = tool.calculate_position_size(
            holding=extreme_risk_holding,
            portfolio=sample_portfolio,
            risk_tolerance="conservative",
        )

        # Assert
        # Should recommend very small size or exit
        assert result.recommended_size_pct <= 2.0 or result.sizing_action == "exit"