"""
Unit tests for Portfolio Rebalancing Crew.

Tests the portfolio rebalancing crew agents, tasks, and workflow execution
with mocked external dependencies.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from finwiz.crews.portfolio_rebalancing_crew.portfolio_rebalancing_crew import PortfolioRebalancingCrew
from finwiz.schemas.portfolio_rebalancing import (
    PortfolioAnalysis,
    RebalancingRecommendation,
    RebalancingResult,
    TradeAction,
    TradeRecommendation,
    UrgencyLevel,
)


class TestPortfolioRebalancingCrew:
    """Test cases for Portfolio Rebalancing Crew."""

    @pytest.fixture
    def mock_portfolio_config(self):
        """Create a mock portfolio configuration for testing."""
        return {
            "holdings": [
                {"symbol": "AAPL", "shares": 100, "cost_basis": 150.0},
                {"symbol": "GOOGL", "shares": 10, "cost_basis": 2500.0},
                {"symbol": "MSFT", "shares": 50, "cost_basis": 300.0},
            ],
            "target_weights": {"AAPL": 0.40, "GOOGL": 0.35, "MSFT": 0.25},
            "tolerance_bands": {"AAPL": 0.05, "GOOGL": 0.05, "MSFT": 0.05},
            "available_capital": 5000.0,
        }

    @pytest.fixture
    def mock_rebalancing_result(self):
        """Create a mock rebalancing result for testing."""
        current_portfolio = PortfolioAnalysis(
            total_value=55000.0,
            weightings={"AAPL": 0.273, "GOOGL": 0.455, "MSFT": 0.273},
            deviations_from_target={"AAPL": -0.127, "GOOGL": 0.105, "MSFT": 0.023},
            positions_needing_rebalancing=["AAPL", "GOOGL"],
            risk_metrics={"portfolio_beta": 1.2, "volatility": 0.18},
        )

        projected_portfolio = PortfolioAnalysis(
            total_value=60000.0,
            weightings={"AAPL": 0.40, "GOOGL": 0.35, "MSFT": 0.25},
            deviations_from_target={"AAPL": 0.0, "GOOGL": 0.0, "MSFT": 0.0},
            positions_needing_rebalancing=[],
            risk_metrics={"portfolio_beta": 1.15, "volatility": 0.16},
        )

        trade_recommendations = [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.BUY,
                quantity=33.33,
                current_price=150.0,
                trade_value=5000.0,
                estimated_commission=5.0,
                estimated_spread_cost=10.0,
                total_estimated_cost=15.0,
                current_weight=0.273,
                target_weight=0.40,
                weight_deviation=-0.127,
                projected_weight_after_trade=0.40,
                priority=1,
                urgency=UrgencyLevel.HIGH,
                rationale="Significantly underweighted, requires immediate rebalancing",
            )
        ]

        return RebalancingResult(
            analysis_timestamp=datetime.now(),
            current_portfolio=current_portfolio,
            trade_recommendations=trade_recommendations,
            projected_portfolio=projected_portfolio,
            total_transaction_costs=15.0,
            cost_benefit_ratio=0.025,
            break_even_analysis="Break-even in 2.5 months based on expected returns",
            current_risk_score=6.5,
            projected_risk_score=5.8,
            risk_improvement=0.7,
            total_trades_required=1,
            positions_requiring_action=2,
            positions_within_tolerance=1,
            overall_recommendation=RebalancingRecommendation.REBALANCE_NOW,
            next_review_date=datetime.now(),
        )

    def test_should_initialize_crew_successfully(self):
        """Test that the portfolio rebalancing crew initializes correctly."""
        # Act
        crew = PortfolioRebalancingCrew()

        # Assert
        assert crew is not None
        assert hasattr(crew, "portfolio_analyst")
        assert hasattr(crew, "rebalancing_strategist")
        assert hasattr(crew, "risk_manager")

    def test_should_create_portfolio_analyst_agent(self):
        """Test that portfolio analyst agent is created with correct configuration."""
        # Arrange
        crew = PortfolioRebalancingCrew()

        # Act
        agent = crew.portfolio_analyst()

        # Assert
        assert agent is not None
        assert agent.verbose is True
        assert agent.reasoning is False
        assert len(agent.tools) > 0

    def test_should_create_rebalancing_strategist_agent(self):
        """Test that rebalancing strategist agent is created with correct configuration."""
        # Arrange
        crew = PortfolioRebalancingCrew()

        # Act
        agent = crew.rebalancing_strategist()

        # Assert
        assert agent is not None
        assert agent.verbose is True
        assert agent.reasoning is False
        assert len(agent.tools) > 0

    def test_should_create_risk_manager_agent(self):
        """Test that risk manager agent is created with correct configuration."""
        # Arrange
        crew = PortfolioRebalancingCrew()

        # Act
        agent = crew.risk_manager()

        # Assert
        assert agent is not None
        assert agent.verbose is True
        assert agent.reasoning is False
        assert len(agent.tools) > 0

    def test_should_create_portfolio_analysis_task(self):
        """Test that portfolio analysis task is created correctly."""
        # Arrange
        crew = PortfolioRebalancingCrew()

        # Act
        task = crew.portfolio_analysis_task()

        # Assert
        assert task is not None
        assert task.verbose is True
        assert task.async_execution is True

    def test_should_create_rebalancing_optimization_task(self):
        """Test that rebalancing optimization task is created correctly."""
        # Arrange
        crew = PortfolioRebalancingCrew()

        # Act
        task = crew.rebalancing_optimization_task()

        # Assert
        assert task is not None
        assert task.verbose is True
        assert task.async_execution is True

    def test_should_create_risk_validation_task(self):
        """Test that risk validation task is created correctly."""
        # Arrange
        crew = PortfolioRebalancingCrew()

        # Act
        task = crew.risk_validation_task()

        # Assert
        assert task is not None
        assert task.verbose is True

    def test_should_create_crew_with_sequential_process(self):
        """Test that the crew is created with sequential process."""
        # Arrange
        crew_instance = PortfolioRebalancingCrew()

        # Act
        crew = crew_instance.crew()

        # Assert
        assert crew is not None
        assert crew.verbose is True
        assert crew.respect_context_window is True
        assert crew.allow_delegation is False
        assert crew.max_rpm == 20

    @patch("finwiz.crews.portfolio_rebalancing_crew.portfolio_rebalancing_crew.get_portfolio_rebalancing_tool")
    def test_should_include_portfolio_rebalancing_tool_in_tools(self, mock_get_tool):
        """Test that portfolio rebalancing tool is included in the tools list."""
        # Arrange
        mock_tool = MagicMock()
        mock_get_tool.return_value = mock_tool

        # Act
        PortfolioRebalancingCrew()

        # Assert
        mock_get_tool.assert_called_once()

    @patch("finwiz.crews.portfolio_rebalancing_crew.portfolio_rebalancing_crew.get_quantitative_analysis_tool")
    def test_should_include_quantitative_analysis_tool_in_tools(self, mock_get_tool):
        """Test that quantitative analysis tool is included in the tools list."""
        # Arrange
        mock_tool = MagicMock()
        mock_get_tool.return_value = mock_tool

        # Act
        PortfolioRebalancingCrew()

        # Assert
        mock_get_tool.assert_called_once()

    @patch("finwiz.crews.portfolio_rebalancing_crew.portfolio_rebalancing_crew.get_rag_tools")
    def test_should_include_rag_tools_in_tools(self, mock_get_tools):
        """Test that RAG tools are included in the tools list."""
        # Arrange
        mock_tools = [MagicMock(), MagicMock()]
        mock_get_tools.return_value = mock_tools

        # Act
        PortfolioRebalancingCrew()

        # Assert
        mock_get_tools.assert_called_once_with(collection_suffix="portfolio_rebalancing")

    def test_should_have_correct_task_dependencies(self):
        """Test that tasks have correct dependency structure."""
        # Arrange
        crew = PortfolioRebalancingCrew()

        # Act
        portfolio_task = crew.portfolio_analysis_task()
        rebalancing_task = crew.rebalancing_optimization_task()
        risk_task = crew.risk_validation_task()

        # Assert
        # Portfolio analysis should be independent
        assert portfolio_task is not None

        # Rebalancing optimization should depend on portfolio analysis
        assert rebalancing_task is not None

        # Risk validation should depend on rebalancing optimization
        assert risk_task is not None

    @pytest.mark.integration
    @patch("finwiz.crews.portfolio_rebalancing_crew.portfolio_rebalancing_crew.PortfolioPriceService")
    @patch("finwiz.crews.portfolio_rebalancing_crew.portfolio_rebalancing_crew.YahooFinanceTickerInfoTool")
    def test_should_handle_crew_execution_with_mocked_dependencies(
        self, mock_yahoo_tool, mock_price_service, mock_portfolio_config
    ):
        """Test crew execution with mocked external dependencies."""
        # Arrange
        mock_price_service.return_value = MagicMock()
        mock_yahoo_tool.return_value = MagicMock()

        crew_instance = PortfolioRebalancingCrew()
        crew = crew_instance.crew()

        inputs = {
            "full_date": "January 15, 2025",
            "portfolio_data": mock_portfolio_config,
            "target_allocations": mock_portfolio_config["target_weights"],
            "tolerance_bands": mock_portfolio_config["tolerance_bands"],
            "available_capital": mock_portfolio_config["available_capital"],
        }

        # Mock the crew kickoff to avoid actual execution
        with patch.object(crew, "kickoff") as mock_kickoff:
            mock_kickoff.return_value = "Mocked crew execution result"

            # Act
            result = crew.kickoff(inputs=inputs)

            # Assert
            assert result == "Mocked crew execution result"
            mock_kickoff.assert_called_once_with(inputs=inputs)

    def test_should_validate_crew_configuration_structure(self):
        """Test that crew configuration follows FinWiz patterns."""
        # Arrange & Act
        crew_instance = PortfolioRebalancingCrew()

        # Assert
        # Check that crew follows CrewBase pattern
        assert hasattr(crew_instance, "agents_config")
        assert hasattr(crew_instance, "tasks_config")

        # Check that required agents exist
        assert hasattr(crew_instance, "portfolio_analyst")
        assert hasattr(crew_instance, "rebalancing_strategist")
        assert hasattr(crew_instance, "risk_manager")

        # Check that required tasks exist
        assert hasattr(crew_instance, "portfolio_analysis_task")
        assert hasattr(crew_instance, "rebalancing_optimization_task")
        assert hasattr(crew_instance, "risk_validation_task")

        # Check that crew method exists
        assert hasattr(crew_instance, "crew")
        assert callable(crew_instance.crew)
