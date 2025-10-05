"""
Unit tests for the RiskManager class.

Tests cover concentration limits, turnover monitoring, volatility-based recommendations,
tax-loss harvesting awareness, and position size validation.
"""

from datetime import datetime, timedelta

import pytest

from finwiz.quantitative.risk_manager import (
    ConcentrationLimits,
    RiskLevel,
    RiskManager,
    RiskManagerConfig,
    RiskWarningType,
    TaxLossHarvestingConfig,
    TurnoverLimits,
    VolatilityThresholds,
)
from finwiz.schemas.portfolio_rebalancing import (
    CostAnalysis,
    ExecutionSummary,
    Holding,
    PortfolioAnalysis,
    PortfolioConfiguration,
    RebalancingResult,
    TradeAction,
    TradeRecommendation,
    UrgencyLevel,
)


class TestRiskManager:
    """Test cases for RiskManager class."""

    @pytest.fixture
    def risk_manager(self) -> RiskManager:
        """Create a RiskManager instance with default configuration."""
        return RiskManager()

    @pytest.fixture
    def custom_risk_manager(self) -> RiskManager:
        """Create a RiskManager instance with custom configuration."""
        config = RiskManagerConfig(
            concentration_limits=ConcentrationLimits(
                max_single_position=0.15,
                max_sector_concentration=0.25,
                max_top_5_positions=0.50,
                min_number_positions=8,
            ),
            turnover_limits=TurnoverLimits(
                max_annual_turnover=0.8,
                max_monthly_turnover=0.20,
                warning_threshold=0.40,
            ),
            volatility_thresholds=VolatilityThresholds(
                low_volatility_threshold=0.12,
                high_volatility_threshold=0.25,
                extreme_volatility_threshold=0.40,
            ),
        )
        return RiskManager(config)

    @pytest.fixture
    def sample_portfolio_config(self) -> PortfolioConfiguration:
        """Create a sample portfolio configuration."""
        holdings = [
            Holding(symbol="AAPL", shares=100, cost_basis=150.0, acquisition_date=datetime.now() - timedelta(days=200)),
            Holding(symbol="GOOGL", shares=50, cost_basis=2000.0, acquisition_date=datetime.now() - timedelta(days=400)),
            Holding(symbol="MSFT", shares=75, cost_basis=250.0, acquisition_date=datetime.now() - timedelta(days=100)),
            Holding(symbol="TSLA", shares=25, cost_basis=800.0, acquisition_date=datetime.now() - timedelta(days=50)),
        ]

        return PortfolioConfiguration(
            holdings=holdings,
            target_weights={"AAPL": 0.30, "GOOGL": 0.25, "MSFT": 0.25, "TSLA": 0.20},
            tolerance_bands={"AAPL": 0.05, "GOOGL": 0.05, "MSFT": 0.05, "TSLA": 0.05},
            available_capital=10000.0,
        )

    @pytest.fixture
    def sample_rebalancing_result(self) -> RebalancingResult:
        """Create a sample rebalancing result."""
        current_portfolio = PortfolioAnalysis(
            total_value=500000.0,
            weightings={"AAPL": 0.35, "GOOGL": 0.20, "MSFT": 0.30, "TSLA": 0.15},
            deviations_from_target={"AAPL": 0.05, "GOOGL": -0.05, "MSFT": 0.05, "TSLA": -0.05},
            positions_needing_rebalancing=["AAPL", "GOOGL", "MSFT", "TSLA"],
        )

        projected_portfolio = PortfolioAnalysis(
            total_value=510000.0,
            weightings={"AAPL": 0.30, "GOOGL": 0.25, "MSFT": 0.25, "TSLA": 0.20},
            deviations_from_target={"AAPL": 0.00, "GOOGL": 0.00, "MSFT": 0.00, "TSLA": 0.00},
            positions_needing_rebalancing=[],
        )

        trade_recommendations = [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.SELL,
                quantity=50,
                current_price=180.0,
                trade_value=9000.0,
                estimated_commission=5.0,
                estimated_spread_cost=10.0,
                total_estimated_cost=15.0,
                current_weight=0.35,
                target_weight=0.30,
                weight_deviation=0.05,
                projected_weight_after_trade=0.30,
                priority=1,
                urgency=UrgencyLevel.MEDIUM,
                rationale="Reduce overweight position",
            ),
            TradeRecommendation(
                symbol="GOOGL",
                action=TradeAction.BUY,
                quantity=10,
                current_price=2200.0,
                trade_value=22000.0,
                estimated_commission=5.0,
                estimated_spread_cost=20.0,
                total_estimated_cost=25.0,
                current_weight=0.20,
                target_weight=0.25,
                weight_deviation=-0.05,
                projected_weight_after_trade=0.25,
                priority=2,
                urgency=UrgencyLevel.MEDIUM,
                rationale="Increase underweight position",
            ),
        ]

        cost_analysis = CostAnalysis(
            total_transaction_costs=40.0,
            commission_costs=10.0,
            spread_costs=30.0,
            cost_as_percentage=0.008,
        )

        execution_summary = ExecutionSummary(
            total_trades_required=2,
            positions_requiring_action=2,
            positions_within_tolerance=2,
            estimated_execution_time="5 minutes",
            capital_required=13000.0,
        )

        return RebalancingResult(
            current_portfolio=current_portfolio,
            trade_recommendations=trade_recommendations,
            projected_portfolio=projected_portfolio,
            cost_analysis=cost_analysis,
            current_risk_score=6.0,
            projected_risk_score=4.0,
            risk_improvement=2.0,
            execution_summary=execution_summary,
            overall_recommendation="REBALANCE_NOW",
            next_review_date=datetime.now() + timedelta(days=30),
        )

    def test_should_initialize_with_default_config_when_no_config_provided(self):
        """Test RiskManager initialization with default configuration."""
        # Act
        risk_manager = RiskManager()

        # Assert
        assert risk_manager.config is not None
        assert risk_manager.config.concentration_limits.max_single_position == 0.20
        assert risk_manager.config.turnover_limits.max_monthly_turnover == 0.25
        assert risk_manager.config.volatility_thresholds.high_volatility_threshold == 0.30

    def test_should_initialize_with_custom_config_when_config_provided(self):
        """Test RiskManager initialization with custom configuration."""
        # Arrange
        config = RiskManagerConfig(
            concentration_limits=ConcentrationLimits(max_single_position=0.15),
        )

        # Act
        risk_manager = RiskManager(config)

        # Assert
        assert risk_manager.config.concentration_limits.max_single_position == 0.15

    def test_should_detect_concentration_violations_when_position_exceeds_limit(
        self, risk_manager, sample_portfolio_config, mocker
    ):
        """Test detection of concentration limit violations."""
        # Arrange
        # Create result with high concentration
        high_concentration_result = mocker.Mock()
        high_concentration_result.projected_portfolio.weightings = {
            "AAPL": 0.60,  # Very high concentration to ensure risk score > 5
            "GOOGL": 0.20,
            "MSFT": 0.15,
            "TSLA": 0.05,
        }
        high_concentration_result.current_portfolio.total_value = 500000.0
        high_concentration_result.trade_recommendations = []

        # Act
        risk_assessment = risk_manager.assess_rebalancing_risks(sample_portfolio_config, high_concentration_result)

        # Assert
        concentration_warnings = [w for w in risk_assessment.warnings if w.warning_type == RiskWarningType.CONCENTRATION]
        assert len(concentration_warnings) > 0
        assert any("AAPL" in w.message for w in concentration_warnings)
        assert risk_assessment.concentration_risk > 4.0  # HHI calculation gives 4.25 for this scenario

    def test_should_detect_excessive_turnover_when_trades_exceed_limit(
        self, risk_manager, sample_portfolio_config, sample_rebalancing_result
    ):
        """Test detection of excessive portfolio turnover."""
        # Arrange
        # Modify trade recommendations to create high turnover (>25% monthly limit)
        # Portfolio value is 500k, so need >125k total trade value for >25% turnover
        large_trades = [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.SELL,
                quantity=800,  # Very large trade
                current_price=180.0,
                trade_value=144000.0,  # 144k
                estimated_commission=50.0,
                estimated_spread_cost=100.0,
                total_estimated_cost=150.0,
                current_weight=0.35,
                target_weight=0.30,
                weight_deviation=0.05,
                projected_weight_after_trade=0.30,
                priority=1,
                urgency=UrgencyLevel.HIGH,
                rationale="Large rebalancing trade",
            ),
            TradeRecommendation(
                symbol="GOOGL",
                action=TradeAction.BUY,
                quantity=65,  # Very large trade
                current_price=2200.0,
                trade_value=143000.0,  # 143k
                estimated_commission=50.0,
                estimated_spread_cost=100.0,
                total_estimated_cost=150.0,
                current_weight=0.20,
                target_weight=0.25,
                weight_deviation=-0.05,
                projected_weight_after_trade=0.25,
                priority=2,
                urgency=UrgencyLevel.HIGH,
                rationale="Large rebalancing trade",
            ),
        ]
        # Total trade value: 287k, Portfolio: 500k, Turnover: 287k/(2*500k) = 28.7% > 25% limit
        sample_rebalancing_result.trade_recommendations = large_trades

        # Act
        risk_assessment = risk_manager.assess_rebalancing_risks(sample_portfolio_config, sample_rebalancing_result)

        # Assert
        turnover_warnings = [w for w in risk_assessment.warnings if w.warning_type == RiskWarningType.TURNOVER]
        assert len(turnover_warnings) > 0
        assert risk_assessment.turnover_risk > 5.0

    def test_should_recommend_wider_tolerance_when_volatility_high(
        self, risk_manager, sample_portfolio_config, sample_rebalancing_result
    ):
        """Test volatility-based tolerance recommendations."""
        # Arrange
        high_volatility = 0.45  # 45% volatility

        # Act
        risk_assessment = risk_manager.assess_rebalancing_risks(sample_portfolio_config, sample_rebalancing_result, high_volatility)

        # Assert
        volatility_warnings = [w for w in risk_assessment.warnings if w.warning_type == RiskWarningType.VOLATILITY]
        assert len(volatility_warnings) > 0
        assert risk_assessment.volatility_risk > 7.0
        assert risk_assessment.recommended_tolerance_adjustment is not None
        assert risk_assessment.recommended_tolerance_adjustment >= 0.10

    def test_should_detect_tax_implications_when_short_term_gains_present(
        self, risk_manager, sample_portfolio_config, sample_rebalancing_result
    ):
        """Test detection of tax implications for short-term gains."""
        # Arrange
        # Modify holding to have short-term gains
        sample_portfolio_config.holdings[0].acquisition_date = datetime.now() - timedelta(days=100)  # Short-term
        sample_portfolio_config.holdings[0].cost_basis = 120.0  # Lower than current price

        # Act
        risk_assessment = risk_manager.assess_rebalancing_risks(sample_portfolio_config, sample_rebalancing_result)

        # Assert
        tax_warnings = [w for w in risk_assessment.warnings if w.warning_type == RiskWarningType.TAX_IMPLICATIONS]
        assert len(tax_warnings) > 0
        assert any("short-term capital gains" in w.message for w in tax_warnings)

    def test_should_detect_tax_loss_harvesting_opportunities(
        self, risk_manager, sample_portfolio_config, sample_rebalancing_result
    ):
        """Test detection of tax-loss harvesting opportunities."""
        # Arrange
        # Modify holding to have losses
        sample_portfolio_config.holdings[0].cost_basis = 250.0  # Higher than current price

        # Act
        risk_assessment = risk_manager.assess_rebalancing_risks(sample_portfolio_config, sample_rebalancing_result)

        # Assert
        tax_warnings = [w for w in risk_assessment.warnings if w.warning_type == RiskWarningType.TAX_IMPLICATIONS]
        assert len(tax_warnings) > 0
        assert any("tax loss" in w.message for w in tax_warnings)

    def test_should_warn_about_large_position_sizes(self, risk_manager, sample_portfolio_config, sample_rebalancing_result):
        """Test warnings for large position sizes."""
        # Arrange
        # Create large trade (>10% of portfolio)
        large_trade = TradeRecommendation(
            symbol="AAPL",
            action=TradeAction.SELL,
            quantity=300,
            current_price=180.0,
            trade_value=54000.0,  # >10% of 500k portfolio
            estimated_commission=25.0,
            estimated_spread_cost=50.0,
            total_estimated_cost=75.0,
            current_weight=0.35,
            target_weight=0.30,
            weight_deviation=0.05,
            projected_weight_after_trade=0.30,
            priority=1,
            urgency=UrgencyLevel.HIGH,
            rationale="Large position adjustment",
        )
        sample_rebalancing_result.trade_recommendations = [large_trade]

        # Act
        risk_assessment = risk_manager.assess_rebalancing_risks(sample_portfolio_config, sample_rebalancing_result)

        # Assert
        position_warnings = [w for w in risk_assessment.warnings if w.warning_type == RiskWarningType.POSITION_SIZE]
        assert len(position_warnings) > 0

    def test_should_warn_about_market_impact_for_large_quantities(
        self, risk_manager, sample_portfolio_config, sample_rebalancing_result
    ):
        """Test market impact warnings for large quantities."""
        # Arrange
        # Create trade with large quantity
        large_quantity_trade = TradeRecommendation(
            symbol="AAPL",
            action=TradeAction.SELL,
            quantity=1500,  # Large quantity
            current_price=180.0,
            trade_value=270000.0,
            estimated_commission=50.0,
            estimated_spread_cost=100.0,
            total_estimated_cost=150.0,
            current_weight=0.35,
            target_weight=0.30,
            weight_deviation=0.05,
            projected_weight_after_trade=0.30,
            priority=1,
            urgency=UrgencyLevel.HIGH,
            rationale="Large quantity trade",
        )
        sample_rebalancing_result.trade_recommendations = [large_quantity_trade]

        # Act
        risk_assessment = risk_manager.assess_rebalancing_risks(sample_portfolio_config, sample_rebalancing_result)

        # Assert
        market_impact_warnings = [w for w in risk_assessment.warnings if w.warning_type == RiskWarningType.MARKET_IMPACT]
        assert len(market_impact_warnings) > 0

    def test_should_calculate_appropriate_risk_scores(self, risk_manager, sample_portfolio_config, sample_rebalancing_result):
        """Test calculation of various risk scores."""
        # Act
        risk_assessment = risk_manager.assess_rebalancing_risks(sample_portfolio_config, sample_rebalancing_result)

        # Assert
        assert 0 <= risk_assessment.overall_risk_score <= 10
        assert 0 <= risk_assessment.concentration_risk <= 10
        assert 0 <= risk_assessment.turnover_risk <= 10
        assert 0 <= risk_assessment.volatility_risk <= 10
        assert 0 <= risk_assessment.tax_efficiency_score <= 10

    def test_should_recommend_appropriate_rebalancing_frequency(
        self, risk_manager, sample_portfolio_config, sample_rebalancing_result
    ):
        """Test rebalancing frequency recommendations."""
        # Act
        risk_assessment = risk_manager.assess_rebalancing_risks(sample_portfolio_config, sample_rebalancing_result)

        # Assert
        assert risk_assessment.rebalancing_frequency_recommendation is not None
        assert len(risk_assessment.rebalancing_frequency_recommendation) > 0

    def test_should_validate_safe_rebalancing_when_no_critical_risks(
        self, risk_manager, sample_portfolio_config, sample_rebalancing_result
    ):
        """Test validation of safe rebalancing scenarios."""
        # Act
        is_safe, blocking_issues = risk_manager.validate_rebalancing_safety(sample_portfolio_config, sample_rebalancing_result)

        # Assert
        assert is_safe is True
        assert len(blocking_issues) == 0

    def test_should_block_unsafe_rebalancing_when_critical_risks_present(self, risk_manager, sample_portfolio_config, mocker):
        """Test blocking of unsafe rebalancing scenarios."""
        # Arrange
        # Create unsafe rebalancing result with extreme concentration
        unsafe_result = mocker.Mock()
        unsafe_result.projected_portfolio.weightings = {
            "AAPL": 0.80,  # Extreme concentration
            "GOOGL": 0.10,
            "MSFT": 0.05,
            "TSLA": 0.05,
        }
        unsafe_result.current_portfolio.total_value = 500000.0
        unsafe_result.trade_recommendations = []

        # Act
        is_safe, blocking_issues = risk_manager.validate_rebalancing_safety(
            sample_portfolio_config,
            unsafe_result,
            market_volatility=0.60,  # Extreme volatility
        )

        # Assert
        assert is_safe is False
        assert len(blocking_issues) > 0

    def test_should_handle_disabled_tax_awareness(self, sample_portfolio_config, sample_rebalancing_result):
        """Test handling when tax awareness is disabled."""
        # Arrange
        config = RiskManagerConfig(tax_config=TaxLossHarvestingConfig(enable_tax_awareness=False))
        risk_manager = RiskManager(config)

        # Act
        risk_assessment = risk_manager.assess_rebalancing_risks(sample_portfolio_config, sample_rebalancing_result)

        # Assert
        tax_warnings = [w for w in risk_assessment.warnings if w.warning_type == RiskWarningType.TAX_IMPLICATIONS]
        assert len(tax_warnings) == 0
        assert risk_assessment.tax_efficiency_score == 5.0  # Neutral score

    def test_should_handle_missing_cost_basis_gracefully(self, risk_manager, sample_portfolio_config, sample_rebalancing_result):
        """Test handling of missing cost basis information."""
        # Arrange
        # Remove cost basis from holdings
        for holding in sample_portfolio_config.holdings:
            holding.cost_basis = None

        # Act
        risk_assessment = risk_manager.assess_rebalancing_risks(sample_portfolio_config, sample_rebalancing_result)

        # Assert
        # Should not crash and should still provide assessment
        assert risk_assessment is not None
        assert 0 <= risk_assessment.overall_risk_score <= 10

    def test_should_calculate_correct_turnover_ratio(self, risk_manager, sample_portfolio_config, sample_rebalancing_result):
        """Test correct calculation of turnover ratio."""
        # Arrange
        total_trade_value = sum(abs(trade.trade_value) for trade in sample_rebalancing_result.trade_recommendations)
        portfolio_value = sample_rebalancing_result.current_portfolio.total_value
        expected_turnover = total_trade_value / (2 * portfolio_value)

        # Act
        turnover_risk = risk_manager._calculate_turnover_risk(sample_rebalancing_result)

        # Assert
        expected_risk = min(expected_turnover * 20, 10.0)
        assert abs(turnover_risk - expected_risk) < 0.01

    def test_should_calculate_correct_concentration_risk(self, risk_manager, sample_rebalancing_result):
        """Test correct calculation of concentration risk using HHI."""
        # Arrange
        weights = list(sample_rebalancing_result.projected_portfolio.weightings.values())
        expected_hhi = sum(w**2 for w in weights)
        expected_risk = min(expected_hhi * 10, 10.0)

        # Act
        concentration_risk = risk_manager._calculate_concentration_risk(sample_rebalancing_result)

        # Assert
        assert abs(concentration_risk - expected_risk) < 0.01

    def test_should_scale_volatility_risk_correctly(self, risk_manager):
        """Test correct scaling of volatility risk."""
        # Test low volatility
        low_vol_risk = risk_manager._calculate_volatility_risk(0.10)
        assert low_vol_risk == 2.0

        # Test medium volatility
        medium_vol_risk = risk_manager._calculate_volatility_risk(0.25)
        assert 2.0 < medium_vol_risk < 6.0

        # Test high volatility
        high_vol_risk = risk_manager._calculate_volatility_risk(0.50)
        assert high_vol_risk > 7.0

    def test_should_recommend_tolerance_adjustment_for_high_volatility(self, risk_manager, mocker):
        """Test tolerance adjustment recommendations for high volatility."""
        # Arrange
        volatility_warning = mocker.Mock()
        volatility_warning.warning_type = RiskWarningType.VOLATILITY
        volatility_warning.risk_level = RiskLevel.HIGH

        # Act
        adjustment = risk_manager._recommend_tolerance_adjustment([volatility_warning], market_volatility=0.35)

        # Assert
        assert adjustment is not None
        assert adjustment >= 0.08

    def test_should_recommend_frequency_based_on_risk_level(self, risk_manager, mocker):
        """Test rebalancing frequency recommendations based on risk levels."""
        # Test high risk scenario
        high_risk_warnings = [
            mocker.Mock(risk_level=RiskLevel.HIGH),
            mocker.Mock(risk_level=RiskLevel.HIGH),
            mocker.Mock(risk_level=RiskLevel.CRITICAL),
        ]
        frequency = risk_manager._recommend_rebalancing_frequency(high_risk_warnings, 0.40)
        assert "Delay" in frequency or "risks subside" in frequency

        # Test low risk scenario
        low_risk_warnings = [mocker.Mock(risk_level=RiskLevel.LOW)]
        frequency = risk_manager._recommend_rebalancing_frequency(low_risk_warnings, 0.15)
        assert "Monthly" in frequency or "standard" in frequency
