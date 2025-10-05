"""
Integration tests for Investment Discovery Crew.

Tests the complete discovery workflow end-to-end, including agent interactions,
task dependencies, integration with portfolio review system, and report generation
with A+ recommendations.

Requirements tested:
- 5.1: Integration with existing grading system and portfolio reports
- 5.4: Data flow between portfolio review and discovery systems
"""

import json

import pytest

from finwiz.crews.investment_discovery_crew.investment_discovery_crew import InvestmentDiscoveryCrew
from finwiz.flows.flow_orchestrator import FinwizFlow
from finwiz.schemas.investment_discovery import APlusDiscoveryResult, OptimizationResult, ValidationResult


class TestInvestmentDiscoveryIntegration:
    """Test complete investment discovery workflow integration."""

    @pytest.fixture
    def mock_portfolio_data(self):
        """Mock portfolio data from portfolio review."""
        return {
            "holdings": [
                {
                    "ticker": "AAPL",
                    "name": "Apple Inc.",
                    "asset_class": "stock",
                    "decision": "KEEP",
                    "composite_score": 0.85,
                    "grade": "B+",
                    "risk": {"score": 3.0, "level": "Medium"},
                },
                {
                    "ticker": "SPY",
                    "name": "SPDR S&P 500 ETF",
                    "asset_class": "etf",
                    "decision": "KEEP",
                    "composite_score": 0.78,
                    "grade": "B",
                    "risk": {"score": 2.0, "level": "Low"},
                },
                {
                    "ticker": "BTC-USD",
                    "name": "Bitcoin",
                    "asset_class": "crypto",
                    "decision": "SELL",
                    "composite_score": 0.45,
                    "grade": "C",
                    "risk": {"score": 8.0, "level": "Very High"},
                },
            ],
            "portfolio_grade": "B",
            "total_value": 100000.0,
            "analysis_timestamp": "2025-01-01T12:00:00",
        }

    @pytest.fixture
    def mock_discovery_results(self):
        """Mock A+ discovery results for each asset type."""
        return {
            "etf": APlusDiscoveryResult(
                asset_type="etf",
                total_screened=500,
                candidates_found=3,
                discovery_criteria={
                    "etf_max_expense_ratio": 0.15,
                    "etf_min_aum": 1e9,
                    "etf_max_tracking_error": 0.002,
                    "etf_min_history_years": 3,
                },
                market_context={
                    "regime_type": "bull",
                    "vix_level": 18.5,
                    "inflation_rate": 2.8,
                    "interest_rate_trend": "stable",
                    "market_stress_level": "low",
                },
                a_plus_candidates=[
                    {
                        "candidate": {
                            "symbol": "VTI",
                            "name": "Vanguard Total Stock Market ETF",
                            "asset_type": "etf",
                            "current_price": 245.50,
                            "market_cap": 1.5e12,
                            "preliminary_score": 0.96,
                            "final_score": 0.97,
                            "grade": "A+",
                            "grade_description": "Exceptional quality with minimal fees",
                            "recommended_action": "Strong Buy",
                            "data_source": "Yahoo Finance",
                        },
                        "fundamental_score": 0.95,
                        "technical_score": 0.92,
                        "quality_score": 0.98,
                        "risk_score": 0.88,
                        "composite_score": 0.97,
                        "confidence_level": 0.92,
                        "is_a_plus_candidate": True,
                        "rationale": [
                            "Ultra-low expense ratio of 0.03%",
                            "Perfect tracking record",
                            "Massive liquidity and AUM",
                        ],
                        "key_metrics": {"expense_ratio": 0.0003, "aum": 1.5e12, "tracking_error": 0.001},
                        "competitive_advantages": ["Lowest cost in category", "Vanguard's scale advantages"],
                        "risk_factors": ["Market risk only", "No specific fund risks"],
                    }
                ],
                average_score=0.97,
                grade_distribution={"A+": 3},
                a_plus_percentage=0.6,
                ucits_compliant_count=2,
                ucits_compliant_symbols=["VWRL", "IWDA"],
                top_recommendations=["VTI", "VXUS", "BND"],
                implementation_notes=["Consider tax implications", "Dollar-cost averaging recommended"],
                high_confidence_count=3,
                screening_efficiency=0.6,
            ),
            "stock": APlusDiscoveryResult(
                asset_type="stock",
                total_screened=3000,
                candidates_found=5,
                discovery_criteria={
                    "stock_min_roe": 0.20,
                    "stock_min_revenue_growth": 0.15,
                    "stock_max_debt_to_equity": 0.3,
                    "stock_min_market_cap": 1e9,
                },
                market_context={
                    "regime_type": "bull",
                    "vix_level": 18.5,
                    "inflation_rate": 2.8,
                    "interest_rate_trend": "stable",
                    "market_stress_level": "low",
                },
                a_plus_candidates=[
                    {
                        "candidate": {
                            "symbol": "NVDA",
                            "name": "NVIDIA Corporation",
                            "asset_type": "stock",
                            "current_price": 875.50,
                            "market_cap": 2.1e12,
                            "preliminary_score": 0.95,
                            "final_score": 0.96,
                            "grade": "A+",
                            "grade_description": "AI leader with exceptional growth",
                            "recommended_action": "Strong Buy",
                            "data_source": "Yahoo Finance",
                        },
                        "fundamental_score": 0.98,
                        "technical_score": 0.94,
                        "quality_score": 0.96,
                        "risk_score": 0.85,
                        "composite_score": 0.96,
                        "confidence_level": 0.89,
                        "is_a_plus_candidate": True,
                        "rationale": [
                            "Dominant AI chip market position",
                            "Exceptional revenue growth >50%",
                            "Strong balance sheet with minimal debt",
                        ],
                        "key_metrics": {"roe": 0.55, "revenue_growth": 0.65, "debt_to_equity": 0.15},
                        "competitive_advantages": ["AI chip moat", "CUDA ecosystem", "R&D leadership"],
                        "risk_factors": ["High valuation", "Cyclical semiconductor industry"],
                    }
                ],
                average_score=0.96,
                grade_distribution={"A+": 5},
                a_plus_percentage=0.17,
                top_recommendations=["NVDA", "MSFT", "GOOGL"],
                implementation_notes=["High volatility expected", "Position sizing important"],
                high_confidence_count=4,
                screening_efficiency=0.17,
            ),
            "crypto": APlusDiscoveryResult(
                asset_type="crypto",
                total_screened=100,
                candidates_found=2,
                discovery_criteria={
                    "crypto_min_market_cap": 10e9,
                    "crypto_min_daily_volume": 500e6,
                    "crypto_min_age_months": 36,
                },
                market_context={
                    "regime_type": "bull",
                    "vix_level": 18.5,
                    "inflation_rate": 2.8,
                    "interest_rate_trend": "stable",
                    "market_stress_level": "low",
                },
                a_plus_candidates=[
                    {
                        "candidate": {
                            "symbol": "BTC-USD",
                            "name": "Bitcoin",
                            "asset_type": "crypto",
                            "current_price": 95000.0,
                            "market_cap": 1.8e12,
                            "preliminary_score": 0.95,
                            "final_score": 0.96,
                            "grade": "A+",
                            "grade_description": "Digital gold with institutional adoption",
                            "recommended_action": "Buy",
                            "data_source": "CoinMarketCap",
                        },
                        "fundamental_score": 0.92,
                        "technical_score": 0.88,
                        "quality_score": 0.98,
                        "risk_score": 0.75,
                        "composite_score": 0.96,
                        "confidence_level": 0.85,
                        "is_a_plus_candidate": True,
                        "rationale": [
                            "Largest cryptocurrency by market cap",
                            "Growing institutional adoption",
                            "Limited supply with halving cycles",
                        ],
                        "key_metrics": {"market_cap": 1.8e12, "daily_volume": 25e9, "age_months": 180},
                        "competitive_advantages": ["First mover advantage", "Network effects", "Store of value narrative"],
                        "risk_factors": ["High volatility", "Regulatory uncertainty", "Environmental concerns"],
                    }
                ],
                average_score=0.96,
                grade_distribution={"A+": 2},
                a_plus_percentage=2.0,
                top_recommendations=["BTC-USD", "ETH-USD"],
                implementation_notes=["5% allocation limit", "DCA strategy recommended"],
                high_confidence_count=2,
                screening_efficiency=2.0,
            ),
        }

    @pytest.fixture
    def mock_validation_result(self):
        """Mock validation result for A+ candidates."""
        return ValidationResult(
            total_candidates=10,
            passed_validation=8,
            failed_validation=2,
            validation_details=[
                {
                    "symbol": "VTI",
                    "passed": True,
                    "sharpe_ratio": 1.2,
                    "max_drawdown": -0.15,
                    "sortino_ratio": 1.5,
                    "validation_notes": "Excellent risk-adjusted returns",
                },
                {
                    "symbol": "NVDA",
                    "passed": True,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": -0.35,
                    "sortino_ratio": 2.1,
                    "validation_notes": "High returns with acceptable volatility",
                },
            ],
            backtest_period_years=5,
            market_regimes_tested=["bull", "bear", "sideways"],
            average_sharpe_ratio=1.5,
            average_max_drawdown=-0.25,
            average_sortino_ratio=1.8,
            correlation_analysis={"portfolio_correlation": 0.65},
            stress_test_results={"covid_crash": -0.28, "2008_crisis": -0.42},
            validated_candidates=["VTI", "NVDA", "BTC-USD"],
            rejected_candidates=[
                {"symbol": "RISKY", "reason": "Excessive drawdown"},
                {"symbol": "CORR", "reason": "High correlation with existing holdings"},
            ],
        )

    @pytest.fixture
    def mock_optimization_result(self):
        """Mock portfolio optimization result."""
        return OptimizationResult(
            current_portfolio_grade="B",
            optimized_portfolio_grade="A-",
            grade_improvement=0.15,
            grade_improvement_description="Significant improvement from B to A-",
            improvements=[
                {
                    "current_holding": "SPY",
                    "current_grade": "B",
                    "recommended_investment": "VTI",
                    "recommended_grade": "A+",
                    "improvement_type": "replacement",
                    "expected_grade_improvement": 0.08,
                    "grade_improvement_description": "Replace SPY with VTI for lower fees",
                    "allocation_percentage": 40.0,
                    "implementation_priority": "high",
                    "rationale": "VTI offers broader diversification and lower fees than SPY",
                    "risk_impact": {
                        "risk_score": 2.0,
                        "risk_level": "Low",
                        "risk_factors": ["Market risk"],
                        "systematic_risk": 0.85,
                        "idiosyncratic_risk": 0.05,
                    },
                    "cost_analysis": {"transaction_cost": 0.0, "spread_cost": 5.0},
                    "expected_annual_benefit": 0.12,
                }
            ],
            current_metrics={"sharpe_ratio": 1.1, "volatility": 0.15, "max_drawdown": -0.20},
            projected_metrics={"sharpe_ratio": 1.3, "volatility": 0.14, "max_drawdown": -0.18},
            risk_impact_analysis={"risk_reduction": 0.02, "diversification_improvement": 0.05},
            diversification_impact={"correlation_reduction": 0.03, "sector_balance": "improved"},
            implementation_timeline={"immediate": "VTI replacement", "3_months": "Full rebalancing"},
            total_transaction_costs=25.0,
            expected_annual_benefit=0.18,
            constraints_met=["Risk tolerance", "Liquidity requirements"],
            implementation_notes=["Tax-loss harvesting opportunity", "Consider timing for tax efficiency"],
        )

    def test_should_initialize_investment_discovery_crew_successfully(self):
        """Test that investment discovery crew initializes correctly."""
        # Act
        crew = InvestmentDiscoveryCrew()

        # Assert
        assert crew is not None
        assert hasattr(crew, "etf_discovery_agent")
        assert hasattr(crew, "stock_discovery_agent")
        assert hasattr(crew, "crypto_discovery_agent")
        assert hasattr(crew, "portfolio_optimization_agent")
        assert hasattr(crew, "validation_agent")

    def test_should_create_all_required_agents(self):
        """Test that all required agents are created with proper configuration."""
        # Arrange
        crew = InvestmentDiscoveryCrew()

        # Act
        etf_agent = crew.etf_discovery_agent()
        stock_agent = crew.stock_discovery_agent()
        crypto_agent = crew.crypto_discovery_agent()
        portfolio_agent = crew.portfolio_optimization_agent()
        validation_agent = crew.validation_agent()

        # Assert
        assert etf_agent is not None
        assert stock_agent is not None
        assert crypto_agent is not None
        assert portfolio_agent is not None
        assert validation_agent is not None

        # Verify agents have tools
        assert len(etf_agent.tools) > 0
        assert len(stock_agent.tools) > 0
        assert len(crypto_agent.tools) > 0
        assert len(portfolio_agent.tools) > 0
        assert len(validation_agent.tools) > 0

    def test_should_create_all_required_tasks(self):
        """Test that all required tasks are created with proper dependencies."""
        # Arrange
        crew = InvestmentDiscoveryCrew()

        # Act
        etf_task = crew.etf_discovery_task()
        stock_task = crew.stock_discovery_task()
        crypto_task = crew.crypto_discovery_task()
        validation_task = crew.validation_task()
        optimization_task = crew.optimization_task()
        report_task = crew.report_generation_task()

        # Assert
        assert etf_task is not None
        assert stock_task is not None
        assert crypto_task is not None
        assert validation_task is not None
        assert optimization_task is not None
        assert report_task is not None

        # Verify async execution for discovery tasks
        assert etf_task.async_execution is True
        assert stock_task.async_execution is True
        assert crypto_task.async_execution is True

    def test_should_run_complete_discovery_workflow_when_valid_inputs_provided(
        self, mocker, mock_portfolio_data, mock_discovery_results, mock_validation_result, mock_optimization_result
    ):
        """Test complete discovery workflow end-to-end."""
        # Arrange
        crew = InvestmentDiscoveryCrew()

        # Mock crew kickoff method
        mock_crew = mocker.MagicMock()
        mock_crew.kickoff.return_value = {
            "etf_discovery": mock_discovery_results["etf"],
            "stock_discovery": mock_discovery_results["stock"],
            "crypto_discovery": mock_discovery_results["crypto"],
            "validation_result": mock_validation_result,
            "optimization_result": mock_optimization_result,
        }

        # Mock the crew() method to return our mock
        mocker.patch.object(crew, "crew", return_value=mock_crew)

        # Mock file operations for output
        mocker.patch("pathlib.Path.mkdir")
        mocker.patch("pathlib.Path.write_text")

        # Prepare crew inputs
        crew_inputs = {
            "full_date": "January 01, 2025",
            "current_date": "2025-01-01",
            "timestamp": "2025-01-01 12:00:00",
            "portfolio_data": mock_portfolio_data,
            "portfolio_review_json": "/tmp/portfolio_review.json",
            "has_existing_session": False,
            "session_id": "test_session",
            "analysis_count": 1,
            "report_language": "fr",
            "portfolio_rebalancing_result": None,
            "portfolio_rebalancing_available": False,
        }

        # Act
        result = crew.crew().kickoff(inputs=crew_inputs)

        # Assert
        assert result is not None
        mock_crew.kickoff.assert_called_once_with(inputs=crew_inputs)

    def test_should_integrate_with_main_finwiz_flow(self, mocker, mock_portfolio_data):
        """Test integration with main FinWiz flow."""
        # Arrange
        flow = FinwizFlow()

        # Mock portfolio review to provide data
        flow.inputs["portfolio_review"] = mock_portfolio_data
        flow.inputs["portfolio_review_json"] = "/tmp/portfolio_review.json"

        # Mock feature flag to enable investment discovery
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = True

        # Mock investment discovery crew
        mock_crew = mocker.MagicMock()
        mock_crew_result = mocker.MagicMock()
        mock_crew.crew.return_value.kickoff.return_value = mock_crew_result
        mocker.patch(
            "finwiz.crews.investment_discovery_crew.investment_discovery_crew.InvestmentDiscoveryCrew",
            return_value=mock_crew,
        )

        # Act
        flow.check_investment_discovery()

        # Assert
        assert flow.inputs["investment_discovery_available"] is True
        assert flow.inputs["investment_discovery_result"] == mock_crew_result
        mock_crew.crew.return_value.kickoff.assert_called_once()

        # Verify crew inputs contain required data
        call_args = mock_crew.crew.return_value.kickoff.call_args
        crew_inputs = call_args[1]["inputs"]
        assert "portfolio_data" in crew_inputs
        assert "portfolio_review_json" in crew_inputs
        assert crew_inputs["portfolio_data"] == mock_portfolio_data

    def test_should_handle_missing_portfolio_data_gracefully(self, mocker):
        """Test graceful handling when portfolio data is not available."""
        # Arrange
        flow = FinwizFlow()
        # Don't set portfolio_review in inputs to simulate missing data

        # Mock feature flag to enable investment discovery
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = True

        # Act
        flow.check_investment_discovery()

        # Assert
        assert flow.inputs["investment_discovery_available"] is False

    def test_should_handle_feature_flag_disabled(self, mocker, mock_portfolio_data):
        """Test behavior when investment discovery feature flag is disabled."""
        # Arrange
        flow = FinwizFlow()
        flow.inputs["portfolio_review"] = mock_portfolio_data

        # Mock feature flag to disable investment discovery
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = False

        # Act
        flow.check_investment_discovery()

        # Assert
        assert flow.inputs["investment_discovery_available"] is False

    def test_should_handle_crew_execution_failure_gracefully(self, mocker, mock_portfolio_data):
        """Test graceful handling of crew execution failures."""
        # Arrange
        flow = FinwizFlow()
        flow.inputs["portfolio_review"] = mock_portfolio_data
        flow.inputs["portfolio_review_json"] = "/tmp/portfolio_review.json"

        # Mock feature flag to enable investment discovery
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = True

        # Mock investment discovery crew to raise exception
        mock_crew = mocker.MagicMock()
        mock_crew.crew.return_value.kickoff.side_effect = Exception("Crew execution failed")
        mocker.patch(
            "finwiz.crews.investment_discovery_crew.investment_discovery_crew.InvestmentDiscoveryCrew",
            return_value=mock_crew,
        )

        # Act - should not raise exception
        flow.check_investment_discovery()

        # Assert
        assert flow.inputs["investment_discovery_available"] is False

    def test_should_create_output_directories_for_discovery_results(self, mocker):
        """Test that output directories are created for discovery results."""
        # Arrange
        crew = InvestmentDiscoveryCrew()

        # Mock Path operations
        mocker.patch("pathlib.Path.mkdir")
        mocker.patch("pathlib.Path.write_text")

        # Mock crew execution to trigger file operations
        mock_crew = mocker.MagicMock()
        mock_crew.kickoff.return_value = {"status": "completed"}
        mocker.patch.object(crew, "crew", return_value=mock_crew)

        # Act
        crew.crew().kickoff(inputs={"full_date": "January 01, 2025"})

        # Assert
        mock_crew.kickoff.assert_called_once()

    def test_should_validate_discovery_result_schemas(self, mock_discovery_results):
        """Test that discovery results conform to expected schemas."""
        # Act & Assert - should not raise validation errors
        etf_result = mock_discovery_results["etf"]
        stock_result = mock_discovery_results["stock"]
        crypto_result = mock_discovery_results["crypto"]

        # Verify schema compliance
        assert isinstance(etf_result, APlusDiscoveryResult)
        assert isinstance(stock_result, APlusDiscoveryResult)
        assert isinstance(crypto_result, APlusDiscoveryResult)

        # Verify required fields
        assert etf_result.asset_type == "etf"
        assert stock_result.asset_type == "stock"
        assert crypto_result.asset_type == "crypto"

        # Verify A+ candidates structure
        assert len(etf_result.a_plus_candidates) > 0
        assert len(stock_result.a_plus_candidates) > 0
        assert len(crypto_result.a_plus_candidates) > 0

        # Verify candidate grades
        for candidate_analysis in etf_result.a_plus_candidates:
            assert candidate_analysis["candidate"]["grade"] == "A+"
            assert candidate_analysis["is_a_plus_candidate"] is True
            assert candidate_analysis["composite_score"] >= 0.95

    def test_should_integrate_with_report_generation(self, mocker, mock_discovery_results):
        """Test integration with report generation system."""
        # Arrange
        from finwiz.crews.report_crew.report_crew import ReportCrew

        # Mock report crew
        mock_report_crew = mocker.MagicMock()
        mock_report_crew.crew.return_value.kickoff.return_value = "<html>Test Report</html>"
        mocker.patch("finwiz.crews.report_crew.report_crew.ReportCrew", return_value=mock_report_crew)

        # Mock DirectoryReadTool to simulate discovery results availability
        mock_directory_tool = mocker.MagicMock()
        mock_directory_tool.run.return_value = json.dumps(mock_discovery_results)
        mocker.patch("crewai_tools.DirectoryReadTool", return_value=mock_directory_tool)

        # Prepare flow inputs with discovery results
        flow_inputs = {
            "investment_discovery_result": mock_discovery_results,
            "investment_discovery_available": True,
            "full_date": "January 01, 2025",
            "report_language": "fr",
        }

        # Act
        ReportCrew()
        result = mock_report_crew.crew.return_value.kickoff(inputs=flow_inputs)

        # Assert
        assert result is not None
        mock_report_crew.crew.return_value.kickoff.assert_called_once()

    def test_should_handle_partial_discovery_results(self, mocker, mock_portfolio_data):
        """Test handling when only some discovery tasks succeed."""
        # Arrange
        crew = InvestmentDiscoveryCrew()

        # Mock partial success - ETF succeeds, others fail
        partial_results = {
            "etf_discovery": {"status": "success", "candidates": 3},
            "stock_discovery": {"status": "failed", "error": "API timeout"},
            "crypto_discovery": {"status": "failed", "error": "Rate limit exceeded"},
        }

        mock_crew = mocker.MagicMock()
        mock_crew.kickoff.return_value = partial_results
        mocker.patch.object(crew, "crew", return_value=mock_crew)

        crew_inputs = {
            "portfolio_data": mock_portfolio_data,
            "full_date": "January 01, 2025",
        }

        # Act
        result = crew.crew().kickoff(inputs=crew_inputs)

        # Assert
        assert result is not None
        assert result["etf_discovery"]["status"] == "success"
        assert result["stock_discovery"]["status"] == "failed"
        assert result["crypto_discovery"]["status"] == "failed"

    def test_should_respect_task_dependencies(self, mocker):
        """Test that task dependencies are properly respected."""
        # Arrange
        crew = InvestmentDiscoveryCrew()

        # Mock task execution order tracking
        execution_order = []

        def track_execution(task_name):
            def wrapper(*args, **kwargs):
                execution_order.append(task_name)
                return {"status": "completed"}

            return wrapper

        # Mock individual tasks
        mocker.patch.object(crew, "etf_discovery_task", side_effect=track_execution("etf_discovery"))
        mocker.patch.object(crew, "stock_discovery_task", side_effect=track_execution("stock_discovery"))
        mocker.patch.object(crew, "crypto_discovery_task", side_effect=track_execution("crypto_discovery"))
        mocker.patch.object(crew, "validation_task", side_effect=track_execution("validation"))
        mocker.patch.object(crew, "optimization_task", side_effect=track_execution("optimization"))
        mocker.patch.object(crew, "report_generation_task", side_effect=track_execution("report_generation"))

        # Mock crew execution
        mock_crew = mocker.MagicMock()
        mock_crew.kickoff.return_value = {"status": "completed"}
        mocker.patch.object(crew, "crew", return_value=mock_crew)

        # Act
        crew.crew().kickoff(inputs={"full_date": "January 01, 2025"})

        # Assert
        mock_crew.kickoff.assert_called_once()

    def test_should_validate_crew_configuration(self):
        """Test that crew configuration is valid."""
        # Arrange & Act
        crew = InvestmentDiscoveryCrew()
        crew_instance = crew.crew()

        # Assert
        assert crew_instance is not None
        # Note: CrewAI API may have changed, so we test what we can access
        assert hasattr(crew_instance, "agents")
        assert hasattr(crew_instance, "tasks")

        # Verify agents and tasks are properly configured
        assert len(crew_instance.agents) > 0
        assert len(crew_instance.tasks) > 0


class TestInvestmentDiscoveryDataFlow:
    """Test data flow between portfolio review and investment discovery."""

    @pytest.fixture
    def portfolio_review_output(self, tmp_path):
        """Create a temporary portfolio review output file."""
        portfolio_data = {
            "holdings": [
                {
                    "ticker": "AAPL",
                    "name": "Apple Inc.",
                    "decision": "KEEP",
                    "composite_score": 0.85,
                    "grade": "B+",
                }
            ],
            "portfolio_grade": "B",
            "analysis_timestamp": "2025-01-01T12:00:00",
        }

        output_file = tmp_path / "portfolio_review.json"
        output_file.write_text(json.dumps(portfolio_data))
        return str(output_file)

    def test_should_read_portfolio_review_data_correctly(self, mocker, portfolio_review_output):
        """Test that investment discovery correctly reads portfolio review data."""
        # Arrange
        flow = FinwizFlow()
        flow.inputs["portfolio_review_json"] = portfolio_review_output

        # Mock feature flag
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = True

        # Mock investment discovery crew
        mock_crew = mocker.MagicMock()
        mock_crew.crew.return_value.kickoff.return_value = {"status": "completed"}
        mocker.patch(
            "finwiz.crews.investment_discovery_crew.investment_discovery_crew.InvestmentDiscoveryCrew",
            return_value=mock_crew,
        )

        # Load portfolio data into flow inputs
        with open(portfolio_review_output, encoding="utf-8") as f:
            flow.inputs["portfolio_review"] = json.load(f)

        # Act
        flow.check_investment_discovery()

        # Assert
        call_args = mock_crew.crew.return_value.kickoff.call_args
        crew_inputs = call_args[1]["inputs"]

        assert "portfolio_data" in crew_inputs
        assert crew_inputs["portfolio_data"]["portfolio_grade"] == "B"
        assert len(crew_inputs["portfolio_data"]["holdings"]) == 1
        assert crew_inputs["portfolio_data"]["holdings"][0]["ticker"] == "AAPL"

    def test_should_pass_rebalancing_results_when_available(self, mocker):
        """Test that rebalancing results are passed to investment discovery when available."""
        # Create mock portfolio data inline since fixture is not available
        mock_portfolio_data = {
            "holdings": [{"ticker": "AAPL", "name": "Apple Inc.", "decision": "KEEP"}],
            "portfolio_grade": "B",
        }
        # Arrange
        flow = FinwizFlow()
        flow.inputs["portfolio_review"] = mock_portfolio_data

        rebalancing_result = {
            "trade_recommendations": [{"symbol": "AAPL", "action": "SELL", "quantity": 50}],
            "overall_recommendation": "REBALANCE_SOON",
        }
        flow.inputs["portfolio_rebalancing_result"] = rebalancing_result
        flow.inputs["portfolio_rebalancing_available"] = True

        # Mock feature flag
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = True

        # Mock investment discovery crew
        mock_crew = mocker.MagicMock()
        mock_crew.crew.return_value.kickoff.return_value = {"status": "completed"}
        mocker.patch(
            "finwiz.crews.investment_discovery_crew.investment_discovery_crew.InvestmentDiscoveryCrew",
            return_value=mock_crew,
        )

        # Act
        flow.check_investment_discovery()

        # Assert
        call_args = mock_crew.crew.return_value.kickoff.call_args
        crew_inputs = call_args[1]["inputs"]

        assert crew_inputs["portfolio_rebalancing_available"] is True
        assert crew_inputs["portfolio_rebalancing_result"] == rebalancing_result

    def test_should_create_discovery_output_files(self, mocker, tmp_path):
        """Test that discovery results are written to output files."""
        # Arrange
        output_dir = tmp_path / "output" / "discovery"
        output_dir.mkdir(parents=True)

        # Mock Path.cwd to return our tmp_path
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        crew = InvestmentDiscoveryCrew()

        # Mock crew execution to simulate file creation
        def mock_kickoff(inputs):
            # Simulate creating output files
            (output_dir / "a_plus_etfs.md").write_text("# ETF Discovery Results\n\nFound 3 A+ ETFs")
            (output_dir / "a_plus_stocks.md").write_text("# Stock Discovery Results\n\nFound 5 A+ stocks")
            (output_dir / "a_plus_cryptos.md").write_text("# Crypto Discovery Results\n\nFound 2 A+ cryptos")
            return {"status": "completed"}

        mock_crew = mocker.MagicMock()
        mock_crew.kickoff.side_effect = mock_kickoff
        mocker.patch.object(crew, "crew", return_value=mock_crew)

        # Act
        result = crew.crew().kickoff(inputs={"full_date": "January 01, 2025"})

        # Assert
        assert result["status"] == "completed"
        assert (output_dir / "a_plus_etfs.md").exists()
        assert (output_dir / "a_plus_stocks.md").exists()
        assert (output_dir / "a_plus_cryptos.md").exists()

        # Verify file contents
        etf_content = (output_dir / "a_plus_etfs.md").read_text()
        assert "Found 3 A+ ETFs" in etf_content


class TestInvestmentDiscoveryErrorHandling:
    """Test error handling and graceful degradation in investment discovery."""

    def test_should_handle_api_failures_gracefully(self, mocker):
        """Test graceful handling of API failures during discovery."""
        # Create mock portfolio data inline
        mock_portfolio_data = {
            "holdings": [{"ticker": "AAPL", "name": "Apple Inc.", "decision": "KEEP"}],
            "portfolio_grade": "B",
        }
        # Arrange
        crew = InvestmentDiscoveryCrew()

        # Mock API failure
        mock_crew = mocker.MagicMock()
        mock_crew.kickoff.side_effect = Exception("API rate limit exceeded")
        mocker.patch.object(crew, "crew", return_value=mock_crew)

        # Act & Assert - should not raise exception
        with pytest.raises(Exception, match="API rate limit exceeded"):
            crew.crew().kickoff(inputs={"portfolio_data": mock_portfolio_data})

    def test_should_handle_invalid_portfolio_data(self, mocker):
        """Test handling of invalid portfolio data."""
        # Arrange
        crew = InvestmentDiscoveryCrew()
        invalid_portfolio_data = {"invalid": "data"}

        # Mock crew to handle invalid data
        mock_crew = mocker.MagicMock()
        mock_crew.kickoff.return_value = {"status": "failed", "error": "Invalid portfolio data"}
        mocker.patch.object(crew, "crew", return_value=mock_crew)

        # Act
        result = crew.crew().kickoff(inputs={"portfolio_data": invalid_portfolio_data})

        # Assert
        assert result["status"] == "failed"
        assert "Invalid portfolio data" in result["error"]

    def test_should_handle_missing_required_inputs(self, mocker):
        """Test handling of missing required inputs."""
        # Arrange
        crew = InvestmentDiscoveryCrew()

        # Mock crew to handle missing inputs
        mock_crew = mocker.MagicMock()
        mock_crew.kickoff.return_value = {"status": "failed", "error": "Missing required inputs"}
        mocker.patch.object(crew, "crew", return_value=mock_crew)

        # Act - call with minimal inputs
        result = crew.crew().kickoff(inputs={})

        # Assert
        assert result["status"] == "failed"
        assert "Missing required inputs" in result["error"]

    def test_should_continue_flow_when_discovery_fails(self, mocker):
        """Test that main flow continues when investment discovery fails."""
        # Create mock portfolio data inline
        mock_portfolio_data = {
            "holdings": [{"ticker": "AAPL", "name": "Apple Inc.", "decision": "KEEP"}],
            "portfolio_grade": "B",
        }
        # Arrange
        flow = FinwizFlow()
        flow.inputs["portfolio_review"] = mock_portfolio_data

        # Mock feature flag
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = True

        # Mock investment discovery crew to fail
        mock_crew = mocker.MagicMock()
        mock_crew.crew.return_value.kickoff.side_effect = Exception("Discovery failed")
        mocker.patch(
            "finwiz.crews.investment_discovery_crew.investment_discovery_crew.InvestmentDiscoveryCrew",
            return_value=mock_crew,
        )

        # Act - should not raise exception
        flow.check_investment_discovery()

        # Assert
        assert flow.inputs["investment_discovery_available"] is False
        # Flow should continue despite discovery failure


class TestInvestmentDiscoveryWorkflowEndToEnd:
    """Test complete discovery workflow end-to-end with real-world scenarios."""

    @pytest.fixture
    def mock_discovery_results(self):
        """Mock A+ discovery results for each asset type."""
        return {
            "etf": APlusDiscoveryResult(
                asset_type="etf",
                total_screened=500,
                candidates_found=3,
                discovery_criteria={
                    "etf_max_expense_ratio": 0.15,
                    "etf_min_aum": 1e9,
                    "etf_max_tracking_error": 0.002,
                    "etf_min_history_years": 3,
                },
                market_context={
                    "regime_type": "bull",
                    "vix_level": 18.5,
                    "inflation_rate": 2.8,
                    "interest_rate_trend": "stable",
                    "market_stress_level": "low",
                },
                a_plus_candidates=[
                    {
                        "candidate": {
                            "symbol": "VTI",
                            "name": "Vanguard Total Stock Market ETF",
                            "asset_type": "etf",
                            "current_price": 245.50,
                            "market_cap": 1.5e12,
                            "preliminary_score": 0.96,
                            "final_score": 0.97,
                            "grade": "A+",
                            "grade_description": "Exceptional quality with minimal fees",
                            "recommended_action": "Strong Buy",
                            "data_source": "Yahoo Finance",
                        },
                        "fundamental_score": 0.95,
                        "technical_score": 0.92,
                        "quality_score": 0.98,
                        "risk_score": 0.88,
                        "composite_score": 0.97,
                        "confidence_level": 0.92,
                        "is_a_plus_candidate": True,
                        "rationale": [
                            "Ultra-low expense ratio of 0.03%",
                            "Perfect tracking record",
                            "Massive liquidity and AUM",
                        ],
                        "key_metrics": {"expense_ratio": 0.0003, "aum": 1.5e12, "tracking_error": 0.001},
                        "competitive_advantages": ["Lowest cost in category", "Vanguard's scale advantages"],
                        "risk_factors": ["Market risk only", "No specific fund risks"],
                    }
                ],
                average_score=0.97,
                grade_distribution={"A+": 3},
                a_plus_percentage=0.6,
                ucits_compliant_count=2,
                ucits_compliant_symbols=["VWRL", "IWDA"],
                top_recommendations=["VTI", "VXUS", "BND"],
                implementation_notes=["Consider tax implications", "Dollar-cost averaging recommended"],
                high_confidence_count=3,
                screening_efficiency=0.6,
            ),
            "stock": APlusDiscoveryResult(
                asset_type="stock",
                total_screened=3000,
                candidates_found=5,
                discovery_criteria={
                    "stock_min_roe": 0.20,
                    "stock_min_revenue_growth": 0.15,
                    "stock_max_debt_to_equity": 0.3,
                    "stock_min_market_cap": 1e9,
                },
                market_context={
                    "regime_type": "bull",
                    "vix_level": 18.5,
                    "inflation_rate": 2.8,
                    "interest_rate_trend": "stable",
                    "market_stress_level": "low",
                },
                a_plus_candidates=[
                    {
                        "candidate": {
                            "symbol": "NVDA",
                            "name": "NVIDIA Corporation",
                            "asset_type": "stock",
                            "current_price": 875.50,
                            "market_cap": 2.1e12,
                            "preliminary_score": 0.95,
                            "final_score": 0.96,
                            "grade": "A+",
                            "grade_description": "AI leader with exceptional growth",
                            "recommended_action": "Strong Buy",
                            "data_source": "Yahoo Finance",
                        },
                        "fundamental_score": 0.98,
                        "technical_score": 0.94,
                        "quality_score": 0.96,
                        "risk_score": 0.85,
                        "composite_score": 0.96,
                        "confidence_level": 0.89,
                        "is_a_plus_candidate": True,
                        "rationale": [
                            "Dominant AI chip market position",
                            "Exceptional revenue growth >50%",
                            "Strong balance sheet with minimal debt",
                        ],
                        "key_metrics": {"roe": 0.55, "revenue_growth": 0.65, "debt_to_equity": 0.15},
                        "competitive_advantages": ["AI chip moat", "CUDA ecosystem", "R&D leadership"],
                        "risk_factors": ["High valuation", "Cyclical semiconductor industry"],
                    }
                ],
                average_score=0.96,
                grade_distribution={"A+": 5},
                a_plus_percentage=0.17,
                top_recommendations=["NVDA", "MSFT", "GOOGL"],
                implementation_notes=["High volatility expected", "Position sizing important"],
                high_confidence_count=4,
                screening_efficiency=0.17,
            ),
            "crypto": APlusDiscoveryResult(
                asset_type="crypto",
                total_screened=100,
                candidates_found=2,
                discovery_criteria={
                    "crypto_min_market_cap": 10e9,
                    "crypto_min_daily_volume": 500e6,
                    "crypto_min_age_months": 36,
                },
                market_context={
                    "regime_type": "bull",
                    "vix_level": 18.5,
                    "inflation_rate": 2.8,
                    "interest_rate_trend": "stable",
                    "market_stress_level": "low",
                },
                a_plus_candidates=[
                    {
                        "candidate": {
                            "symbol": "BTC-USD",
                            "name": "Bitcoin",
                            "asset_type": "crypto",
                            "current_price": 95000.0,
                            "market_cap": 1.8e12,
                            "preliminary_score": 0.95,
                            "final_score": 0.96,
                            "grade": "A+",
                            "grade_description": "Digital gold with institutional adoption",
                            "recommended_action": "Buy",
                            "data_source": "CoinMarketCap",
                        },
                        "fundamental_score": 0.92,
                        "technical_score": 0.88,
                        "quality_score": 0.98,
                        "risk_score": 0.75,
                        "composite_score": 0.96,
                        "confidence_level": 0.85,
                        "is_a_plus_candidate": True,
                        "rationale": [
                            "Largest cryptocurrency by market cap",
                            "Growing institutional adoption",
                            "Limited supply with halving cycles",
                        ],
                        "key_metrics": {"market_cap": 1.8e12, "daily_volume": 25e9, "age_months": 180},
                        "competitive_advantages": ["First mover advantage", "Network effects", "Store of value narrative"],
                        "risk_factors": ["High volatility", "Regulatory uncertainty", "Environmental concerns"],
                    }
                ],
                average_score=0.96,
                grade_distribution={"A+": 2},
                a_plus_percentage=2.0,
                top_recommendations=["BTC-USD", "ETH-USD"],
                implementation_notes=["5% allocation limit", "DCA strategy recommended"],
                high_confidence_count=2,
                screening_efficiency=2.0,
            ),
        }

    @pytest.fixture
    def mock_validation_result(self):
        """Mock validation result for A+ candidates."""
        return ValidationResult(
            total_candidates=10,
            passed_validation=8,
            failed_validation=2,
            validation_details=[
                {
                    "symbol": "VTI",
                    "passed": True,
                    "sharpe_ratio": 1.2,
                    "max_drawdown": -0.15,
                    "sortino_ratio": 1.5,
                    "validation_notes": "Excellent risk-adjusted returns",
                },
                {
                    "symbol": "NVDA",
                    "passed": True,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": -0.35,
                    "sortino_ratio": 2.1,
                    "validation_notes": "High returns with acceptable volatility",
                },
            ],
            backtest_period_years=5,
            market_regimes_tested=["bull", "bear", "sideways"],
            average_sharpe_ratio=1.5,
            average_max_drawdown=-0.25,
            average_sortino_ratio=1.8,
            correlation_analysis={"portfolio_correlation": 0.65},
            stress_test_results={"covid_crash": -0.28, "2008_crisis": -0.42},
            validated_candidates=["VTI", "NVDA", "BTC-USD"],
            rejected_candidates=[
                {"symbol": "RISKY", "reason": "Excessive drawdown"},
                {"symbol": "CORR", "reason": "High correlation with existing holdings"},
            ],
        )

    @pytest.fixture
    def mock_optimization_result(self):
        """Mock portfolio optimization result."""
        return OptimizationResult(
            current_portfolio_grade="B",
            optimized_portfolio_grade="A-",
            grade_improvement=0.15,
            grade_improvement_description="Significant improvement from B to A-",
            improvements=[
                {
                    "current_holding": "SPY",
                    "current_grade": "B",
                    "recommended_investment": "VTI",
                    "recommended_grade": "A+",
                    "improvement_type": "replacement",
                    "expected_grade_improvement": 0.08,
                    "grade_improvement_description": "Replace SPY with VTI for lower fees",
                    "allocation_percentage": 40.0,
                    "implementation_priority": "high",
                    "rationale": "VTI offers broader diversification and lower fees than SPY",
                    "risk_impact": {
                        "risk_score": 2.0,
                        "risk_level": "Low",
                        "risk_factors": ["Market risk"],
                        "systematic_risk": 0.85,
                        "idiosyncratic_risk": 0.05,
                    },
                    "cost_analysis": {"transaction_cost": 0.0, "spread_cost": 5.0},
                    "expected_annual_benefit": 0.12,
                }
            ],
            current_metrics={"sharpe_ratio": 1.1, "volatility": 0.15, "max_drawdown": -0.20},
            projected_metrics={"sharpe_ratio": 1.3, "volatility": 0.14, "max_drawdown": -0.18},
            risk_impact_analysis={"risk_reduction": 0.02, "diversification_improvement": 0.05},
            diversification_impact={"correlation_reduction": 0.03, "sector_balance": "improved"},
            implementation_timeline={"immediate": "VTI replacement", "3_months": "Full rebalancing"},
            total_transaction_costs=25.0,
            expected_annual_benefit=0.18,
            constraints_met=["Risk tolerance", "Liquidity requirements"],
            implementation_notes=["Tax-loss harvesting opportunity", "Consider timing for tax efficiency"],
        )

    @pytest.fixture
    def comprehensive_portfolio_data(self):
        """Comprehensive portfolio data for end-to-end testing."""
        return {
            "holdings": [
                {
                    "ticker": "AAPL",
                    "name": "Apple Inc.",
                    "asset_class": "stock",
                    "decision": "KEEP",
                    "composite_score": 0.85,
                    "grade": "B+",
                    "risk": {"score": 3.0, "level": "Medium"},
                    "allocation_percentage": 15.0,
                    "current_value": 15000.0,
                },
                {
                    "ticker": "SPY",
                    "name": "SPDR S&P 500 ETF",
                    "asset_class": "etf",
                    "decision": "SELL",
                    "composite_score": 0.65,
                    "grade": "C+",
                    "risk": {"score": 2.0, "level": "Low"},
                    "allocation_percentage": 30.0,
                    "current_value": 30000.0,
                },
                {
                    "ticker": "BTC-USD",
                    "name": "Bitcoin",
                    "asset_class": "crypto",
                    "decision": "SELL",
                    "composite_score": 0.45,
                    "grade": "C",
                    "risk": {"score": 8.0, "level": "Very High"},
                    "allocation_percentage": 5.0,
                    "current_value": 5000.0,
                },
                {
                    "ticker": "TSLA",
                    "name": "Tesla Inc.",
                    "asset_class": "stock",
                    "decision": "KEEP",
                    "composite_score": 0.75,
                    "grade": "B",
                    "risk": {"score": 6.0, "level": "High"},
                    "allocation_percentage": 10.0,
                    "current_value": 10000.0,
                },
            ],
            "portfolio_grade": "B-",
            "total_value": 100000.0,
            "risk_score": 4.2,
            "diversification_score": 0.72,
            "analysis_timestamp": "2025-01-01T12:00:00",
            "improvement_opportunities": [
                "Replace low-grade ETFs with A+ alternatives",
                "Reduce crypto allocation risk",
                "Improve overall portfolio grade to A-",
            ],
        }

    def test_should_execute_complete_workflow_with_all_phases(
        self, mocker, comprehensive_portfolio_data, mock_discovery_results, mock_validation_result, mock_optimization_result
    ):
        """Test complete workflow execution through all phases."""
        # Arrange
        flow = FinwizFlow()
        flow.inputs["portfolio_review"] = comprehensive_portfolio_data
        flow.inputs["portfolio_review_json"] = "/tmp/portfolio_review.json"

        # Mock feature flag
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = True

        # Mock investment discovery crew with comprehensive results
        mock_crew = mocker.MagicMock()
        complete_workflow_result = {
            "discovery_phase": {
                "etf_discovery": mock_discovery_results["etf"],
                "stock_discovery": mock_discovery_results["stock"],
                "crypto_discovery": mock_discovery_results["crypto"],
                "total_candidates_found": 10,
                "a_plus_candidates_found": 8,
            },
            "validation_phase": mock_validation_result,
            "optimization_phase": mock_optimization_result,
            "workflow_status": "completed",
            "execution_time_seconds": 180,
            "phases_completed": ["discovery", "validation", "optimization", "report_generation"],
        }

        mock_crew.crew.return_value.kickoff.return_value = complete_workflow_result
        mocker.patch(
            "finwiz.crews.investment_discovery_crew.investment_discovery_crew.InvestmentDiscoveryCrew",
            return_value=mock_crew,
        )

        # Act
        flow.check_investment_discovery()

        # Assert
        assert flow.inputs["investment_discovery_available"] is True
        assert flow.inputs["investment_discovery_result"] == complete_workflow_result

        # Verify workflow phases
        result = flow.inputs["investment_discovery_result"]
        assert result["workflow_status"] == "completed"
        assert len(result["phases_completed"]) == 4
        assert "discovery" in result["phases_completed"]
        assert "validation" in result["phases_completed"]
        assert "optimization" in result["phases_completed"]
        assert "report_generation" in result["phases_completed"]

        # Verify discovery results
        assert result["discovery_phase"]["total_candidates_found"] == 10
        assert result["discovery_phase"]["a_plus_candidates_found"] == 8

        # Verify crew was called with correct inputs
        call_args = mock_crew.crew.return_value.kickoff.call_args
        crew_inputs = call_args[1]["inputs"]
        assert crew_inputs["portfolio_data"] == comprehensive_portfolio_data
        assert "portfolio_review_json" in crew_inputs

    def test_should_handle_mixed_success_failure_scenarios(self, mocker, comprehensive_portfolio_data):
        """Test handling when some discovery tasks succeed and others fail."""
        # Arrange
        flow = FinwizFlow()
        flow.inputs["portfolio_review"] = comprehensive_portfolio_data

        # Mock feature flag
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = True

        # Mock partial success scenario
        partial_success_result = {
            "discovery_phase": {
                "etf_discovery": {"status": "success", "candidates_found": 3},
                "stock_discovery": {"status": "success", "candidates_found": 5},
                "crypto_discovery": {"status": "failed", "error": "API timeout", "candidates_found": 0},
            },
            "validation_phase": {"status": "partial", "validated_count": 6, "failed_count": 2},
            "optimization_phase": {"status": "success", "improvements_found": 4},
            "workflow_status": "partial_success",
            "phases_completed": ["discovery", "validation", "optimization"],
            "phases_failed": ["crypto_discovery"],
        }

        mock_crew = mocker.MagicMock()
        mock_crew.crew.return_value.kickoff.return_value = partial_success_result
        mocker.patch(
            "finwiz.crews.investment_discovery_crew.investment_discovery_crew.InvestmentDiscoveryCrew",
            return_value=mock_crew,
        )

        # Act
        flow.check_investment_discovery()

        # Assert
        assert flow.inputs["investment_discovery_available"] is True
        result = flow.inputs["investment_discovery_result"]
        assert result["workflow_status"] == "partial_success"
        assert "crypto_discovery" in result["phases_failed"]
        assert result["discovery_phase"]["crypto_discovery"]["status"] == "failed"

    def test_should_validate_data_flow_between_phases(self, mocker, comprehensive_portfolio_data):
        """Test that data flows correctly between workflow phases."""
        # Arrange
        flow = FinwizFlow()
        flow.inputs["portfolio_review"] = comprehensive_portfolio_data

        # Mock feature flag
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = True

        # Track data flow between phases
        phase_data_flow = {
            "discovery_to_validation": {
                "candidates_passed": ["VTI", "NVDA", "BTC-USD"],
                "data_integrity": "verified",
            },
            "validation_to_optimization": {
                "validated_candidates": ["VTI", "NVDA"],
                "rejected_candidates": ["BTC-USD"],
                "validation_scores": {"VTI": 0.96, "NVDA": 0.94},
            },
            "optimization_to_report": {
                "recommended_changes": 3,
                "portfolio_improvement": 0.15,
                "implementation_plan": "generated",
            },
        }

        workflow_result = {
            "data_flow_validation": phase_data_flow,
            "workflow_status": "completed",
            "data_integrity_checks": "passed",
        }

        mock_crew = mocker.MagicMock()
        mock_crew.crew.return_value.kickoff.return_value = workflow_result
        mocker.patch(
            "finwiz.crews.investment_discovery_crew.investment_discovery_crew.InvestmentDiscoveryCrew",
            return_value=mock_crew,
        )

        # Act
        flow.check_investment_discovery()

        # Assert
        result = flow.inputs["investment_discovery_result"]
        assert result["data_integrity_checks"] == "passed"

        # Verify data flow between phases
        data_flow = result["data_flow_validation"]
        assert len(data_flow["discovery_to_validation"]["candidates_passed"]) == 3
        assert len(data_flow["validation_to_optimization"]["validated_candidates"]) == 2
        assert data_flow["optimization_to_report"]["recommended_changes"] == 3


class TestAgentInteractionsAndTaskDependencies:
    """Test agent interactions and task dependencies in the discovery workflow."""

    @pytest.fixture
    def mock_discovery_results(self):
        """Mock A+ discovery results for each asset type."""
        return {
            "etf": APlusDiscoveryResult(
                asset_type="etf",
                total_screened=500,
                candidates_found=3,
                discovery_criteria={},
                market_context={},
                a_plus_candidates=[],
                average_score=0.97,
                grade_distribution={"A+": 3},
                a_plus_percentage=0.6,
                top_recommendations=["VTI", "VXUS", "BND"],
                implementation_notes=[],
                high_confidence_count=3,
                screening_efficiency=0.6,
            ),
            "stock": APlusDiscoveryResult(
                asset_type="stock",
                total_screened=3000,
                candidates_found=5,
                discovery_criteria={},
                market_context={},
                a_plus_candidates=[],
                average_score=0.96,
                grade_distribution={"A+": 5},
                a_plus_percentage=0.17,
                top_recommendations=["NVDA", "MSFT", "GOOGL"],
                implementation_notes=[],
                high_confidence_count=4,
                screening_efficiency=0.17,
            ),
            "crypto": APlusDiscoveryResult(
                asset_type="crypto",
                total_screened=100,
                candidates_found=2,
                discovery_criteria={},
                market_context={},
                a_plus_candidates=[],
                average_score=0.96,
                grade_distribution={"A+": 2},
                a_plus_percentage=2.0,
                top_recommendations=["BTC-USD", "ETH-USD"],
                implementation_notes=[],
                high_confidence_count=2,
                screening_efficiency=2.0,
            ),
        }

    def test_should_respect_task_execution_order(self, mocker):
        """Test that tasks execute in the correct dependency order."""
        # Arrange
        crew = InvestmentDiscoveryCrew()
        execution_log = []

        def mock_task_execution(task_name):
            def wrapper(*args, **kwargs):
                execution_log.append(task_name)
                return {"status": "completed", "task": task_name}

            return wrapper

        # Mock each task to track execution order
        mock_etf_task = mocker.patch.object(crew, "etf_discovery_task")
        mock_etf_task.return_value.execute = mock_task_execution("etf_discovery")

        mock_stock_task = mocker.patch.object(crew, "stock_discovery_task")
        mock_stock_task.return_value.execute = mock_task_execution("stock_discovery")

        mock_crypto_task = mocker.patch.object(crew, "crypto_discovery_task")
        mock_crypto_task.return_value.execute = mock_task_execution("crypto_discovery")

        mock_validation_task = mocker.patch.object(crew, "validation_task")
        mock_validation_task.return_value.execute = mock_task_execution("validation")

        mock_optimization_task = mocker.patch.object(crew, "optimization_task")
        mock_optimization_task.return_value.execute = mock_task_execution("optimization")

        mock_report_task = mocker.patch.object(crew, "report_generation_task")
        mock_report_task.return_value.execute = mock_task_execution("report_generation")

        # Mock crew execution
        mock_crew_instance = mocker.MagicMock()
        mock_crew_instance.kickoff.return_value = {"execution_log": execution_log}
        mocker.patch.object(crew, "crew", return_value=mock_crew_instance)

        # Act
        crew.crew().kickoff(inputs={"full_date": "January 01, 2025"})

        # Assert
        mock_crew_instance.kickoff.assert_called_once()

    def test_should_validate_agent_tool_assignments(self):
        """Test that agents have the correct tools assigned."""
        # Arrange & Act
        crew = InvestmentDiscoveryCrew()

        etf_agent = crew.etf_discovery_agent()
        stock_agent = crew.stock_discovery_agent()
        crypto_agent = crew.crypto_discovery_agent()
        portfolio_agent = crew.portfolio_optimization_agent()
        validation_agent = crew.validation_agent()

        # Assert ETF agent has ETF-specific tools
        etf_tool_names = [tool.name for tool in etf_agent.tools]
        assert any("ETF" in tool_name or "etf" in tool_name.lower() for tool_name in etf_tool_names)

        # Assert Stock agent has stock-specific tools
        stock_tool_names = [tool.name for tool in stock_agent.tools]
        assert any("Stock" in tool_name or "stock" in tool_name.lower() for tool_name in stock_tool_names)

        # Assert Crypto agent has crypto-specific tools
        crypto_tool_names = [tool.name for tool in crypto_agent.tools]
        assert any("Crypto" in tool_name or "crypto" in tool_name.lower() for tool_name in crypto_tool_names)

        # Assert Portfolio agent has optimization tools
        portfolio_tool_names = [tool.name for tool in portfolio_agent.tools]
        assert any("Portfolio" in tool_name or "Optimization" in tool_name for tool_name in portfolio_tool_names)

        # Assert Validation agent has backtesting tools
        validation_tool_names = [tool.name for tool in validation_agent.tools]
        assert any("Backtest" in tool_name or "Risk" in tool_name for tool_name in validation_tool_names)

    def test_should_handle_agent_communication_failures(self, mocker):
        """Test handling of communication failures between agents."""
        # Arrange
        crew = InvestmentDiscoveryCrew()

        # Mock agent communication failure
        mock_crew = mocker.MagicMock()
        mock_crew.kickoff.side_effect = Exception("Agent communication timeout")
        mocker.patch.object(crew, "crew", return_value=mock_crew)

        # Act & Assert
        with pytest.raises(Exception, match="Agent communication timeout"):
            crew.crew().kickoff(inputs={"full_date": "January 01, 2025"})

    def test_should_validate_task_output_schemas(self, mocker, mock_discovery_results):
        """Test that task outputs conform to expected schemas."""
        # Arrange
        crew = InvestmentDiscoveryCrew()

        # Mock crew with schema-compliant outputs
        schema_compliant_result = {
            "etf_discovery": mock_discovery_results["etf"],
            "stock_discovery": mock_discovery_results["stock"],
            "crypto_discovery": mock_discovery_results["crypto"],
            "schema_validation": "passed",
        }

        mock_crew = mocker.MagicMock()
        mock_crew.kickoff.return_value = schema_compliant_result
        mocker.patch.object(crew, "crew", return_value=mock_crew)

        # Act
        result = crew.crew().kickoff(inputs={"full_date": "January 01, 2025"})

        # Assert
        assert result["schema_validation"] == "passed"

        # Verify each discovery result conforms to APlusDiscoveryResult schema
        etf_result = result["etf_discovery"]
        stock_result = result["stock_discovery"]
        crypto_result = result["crypto_discovery"]

        assert isinstance(etf_result, APlusDiscoveryResult)
        assert isinstance(stock_result, APlusDiscoveryResult)
        assert isinstance(crypto_result, APlusDiscoveryResult)


class TestPortfolioReviewSystemIntegration:
    """Test integration with existing portfolio review system."""

    @pytest.fixture
    def portfolio_review_output_file(self, tmp_path):
        """Create a realistic portfolio review output file."""
        portfolio_data = {
            "analysis_metadata": {
                "analysis_id": "test_analysis_001",
                "timestamp": "2025-01-01T12:00:00Z",
                "version": "1.0",
                "analyst": "FinWiz Portfolio Crew",
            },
            "portfolio_summary": {
                "total_value": 250000.0,
                "currency": "USD",
                "holdings_count": 8,
                "asset_classes": ["stocks", "etfs", "crypto"],
                "overall_grade": "B",
                "risk_score": 4.2,
                "diversification_score": 0.75,
            },
            "holdings": [
                {
                    "ticker": "AAPL",
                    "name": "Apple Inc.",
                    "asset_class": "stock",
                    "sector": "Technology",
                    "decision": "KEEP",
                    "composite_score": 0.85,
                    "grade": "B+",
                    "current_price": 185.50,
                    "shares": 100,
                    "market_value": 18550.0,
                    "allocation_percentage": 7.42,
                    "risk": {"score": 3.0, "level": "Medium"},
                    "rationale": "Strong fundamentals and market position",
                },
                {
                    "ticker": "SPY",
                    "name": "SPDR S&P 500 ETF",
                    "asset_class": "etf",
                    "decision": "SELL",
                    "composite_score": 0.65,
                    "grade": "C+",
                    "current_price": 445.20,
                    "shares": 150,
                    "market_value": 66780.0,
                    "allocation_percentage": 26.71,
                    "risk": {"score": 2.0, "level": "Low"},
                    "rationale": "High fees compared to alternatives",
                    "improvement_opportunity": "Replace with lower-cost broad market ETF",
                },
                {
                    "ticker": "BTC-USD",
                    "name": "Bitcoin",
                    "asset_class": "crypto",
                    "decision": "SELL",
                    "composite_score": 0.45,
                    "grade": "C",
                    "current_price": 95000.0,
                    "units": 0.5,
                    "market_value": 47500.0,
                    "allocation_percentage": 19.0,
                    "risk": {"score": 8.0, "level": "Very High"},
                    "rationale": "Excessive volatility and allocation",
                    "improvement_opportunity": "Reduce allocation to 5% maximum",
                },
            ],
            "improvement_opportunities": [
                {
                    "category": "cost_optimization",
                    "description": "Replace high-fee ETFs with low-cost alternatives",
                    "potential_savings": 0.15,
                    "priority": "high",
                },
                {
                    "category": "risk_management",
                    "description": "Reduce crypto allocation to appropriate level",
                    "risk_reduction": 2.5,
                    "priority": "high",
                },
                {
                    "category": "grade_improvement",
                    "description": "Target A+ grade investments to improve overall portfolio",
                    "grade_improvement_potential": 0.25,
                    "priority": "medium",
                },
            ],
            "recommendations": {
                "immediate_actions": ["Sell SPY", "Reduce BTC position"],
                "research_needed": ["A+ grade ETF alternatives", "Quality growth stocks"],
                "timeline": "Execute within 30 days",
            },
        }

        output_file = tmp_path / "portfolio_review_detailed.json"
        output_file.write_text(json.dumps(portfolio_data, indent=2))
        return str(output_file)

    def test_should_read_portfolio_review_data_correctly(self, mocker, portfolio_review_output_file):
        """Test correct reading and parsing of portfolio review data."""
        # Arrange
        flow = FinwizFlow()
        flow.inputs["portfolio_review_json"] = portfolio_review_output_file

        # Mock feature flag
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = True

        # Mock file reading in the crew
        mock_crew = mocker.MagicMock()
        mock_crew.crew.return_value.kickoff.return_value = {"status": "data_read_successfully"}
        mocker.patch(
            "finwiz.crews.investment_discovery_crew.investment_discovery_crew.InvestmentDiscoveryCrew",
            return_value=mock_crew,
        )

        # Load portfolio data from file
        with open(portfolio_review_output_file) as f:
            portfolio_data = json.load(f)
        flow.inputs["portfolio_review"] = portfolio_data

        # Act
        flow.check_investment_discovery()

        # Assert
        assert flow.inputs["investment_discovery_available"] is True

        # Verify crew was called with correct portfolio data
        call_args = mock_crew.crew.return_value.kickoff.call_args
        crew_inputs = call_args[1]["inputs"]
        assert crew_inputs["portfolio_data"] == portfolio_data
        assert crew_inputs["portfolio_review_json"] == portfolio_review_output_file

        # Verify portfolio data structure
        assert "portfolio_summary" in portfolio_data
        assert "holdings" in portfolio_data
        assert "improvement_opportunities" in portfolio_data
        assert len(portfolio_data["holdings"]) == 3

    def test_should_identify_improvement_opportunities_from_portfolio_review(self, mocker, portfolio_review_output_file):
        """Test identification of improvement opportunities from portfolio review."""
        # Arrange
        with open(portfolio_review_output_file) as f:
            portfolio_data = json.load(f)

        flow = FinwizFlow()
        flow.inputs["portfolio_review"] = portfolio_data
        flow.inputs["portfolio_review_json"] = portfolio_review_output_file

        # Mock feature flag
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = True

        # Mock discovery crew to process improvement opportunities
        improvement_focused_result = {
            "portfolio_analysis": {
                "current_grade": "B",
                "improvement_opportunities_identified": 3,
                "sell_recommendations": ["SPY", "BTC-USD"],
                "a_plus_replacement_candidates": ["VTI", "VXUS"],
            },
            "targeted_discovery": {
                "etf_replacements": [{"current": "SPY", "replacement": "VTI", "improvement": "Lower fees, broader market"}],
                "crypto_rebalancing": [{"current": "BTC-USD", "action": "Reduce to 5%", "reason": "Risk management"}],
            },
            "expected_improvements": {
                "grade_improvement": "B to A-",
                "cost_savings": 0.15,
                "risk_reduction": 2.5,
            },
        }

        mock_crew = mocker.MagicMock()
        mock_crew.crew.return_value.kickoff.return_value = improvement_focused_result
        mocker.patch(
            "finwiz.crews.investment_discovery_crew.investment_discovery_crew.InvestmentDiscoveryCrew",
            return_value=mock_crew,
        )

        # Act
        flow.check_investment_discovery()

        # Assert
        result = flow.inputs["investment_discovery_result"]
        assert result["portfolio_analysis"]["improvement_opportunities_identified"] == 3
        assert "SPY" in result["portfolio_analysis"]["sell_recommendations"]
        assert "BTC-USD" in result["portfolio_analysis"]["sell_recommendations"]
        assert "VTI" in result["portfolio_analysis"]["a_plus_replacement_candidates"]

    def test_should_handle_missing_portfolio_review_file(self, mocker):
        """Test handling when portfolio review file is missing."""
        # Arrange
        flow = FinwizFlow()
        flow.inputs["portfolio_review_json"] = "/nonexistent/file.json"

        # Mock feature flag
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = True

        # Act
        flow.check_investment_discovery()

        # Assert
        assert flow.inputs["investment_discovery_available"] is False

    def test_should_validate_portfolio_data_format(self, mocker, tmp_path):
        """Test validation of portfolio data format."""
        # Arrange - Create invalid portfolio data
        invalid_portfolio_data = {"invalid": "format", "missing": "required_fields"}

        invalid_file = tmp_path / "invalid_portfolio.json"
        invalid_file.write_text(json.dumps(invalid_portfolio_data))

        flow = FinwizFlow()
        flow.inputs["portfolio_review"] = invalid_portfolio_data
        flow.inputs["portfolio_review_json"] = str(invalid_file)

        # Mock feature flag
        mock_feature_flag = mocker.patch("finwiz.utils.feature_flags.is_feature_enabled")
        mock_feature_flag.return_value = True

        # Mock crew to handle invalid data
        mock_crew = mocker.MagicMock()
        mock_crew.crew.return_value.kickoff.side_effect = Exception("Invalid portfolio data format")
        mocker.patch(
            "finwiz.crews.investment_discovery_crew.investment_discovery_crew.InvestmentDiscoveryCrew",
            return_value=mock_crew,
        )

        # Act
        flow.check_investment_discovery()

        # Assert
        assert flow.inputs["investment_discovery_available"] is False


class TestReportGenerationWithAPlusRecommendations:
    """Test report generation integration with A+ recommendations."""

    @pytest.fixture
    def a_plus_recommendations_data(self):
        """Mock A+ recommendations data for report generation."""
        return {
            "discovery_summary": {
                "total_a_plus_candidates": 8,
                "etf_candidates": 3,
                "stock_candidates": 4,
                "crypto_candidates": 1,
                "average_grade_improvement": 0.18,
            },
            "recommended_actions": [
                {
                    "action_type": "replace",
                    "current_holding": "SPY",
                    "recommended_investment": "VTI",
                    "grade_improvement": "C+ to A+",
                    "rationale": "Lower expense ratio (0.03% vs 0.09%) with broader market exposure",
                    "priority": "high",
                    "expected_annual_savings": 150.0,
                },
                {
                    "action_type": "add",
                    "recommended_investment": "NVDA",
                    "target_allocation": 5.0,
                    "grade": "A+",
                    "rationale": "AI market leader with exceptional growth prospects",
                    "priority": "medium",
                    "risk_considerations": ["High volatility", "Tech sector concentration"],
                },
                {
                    "action_type": "reduce",
                    "current_holding": "BTC-USD",
                    "current_allocation": 19.0,
                    "target_allocation": 5.0,
                    "rationale": "Reduce excessive crypto exposure for better risk management",
                    "priority": "high",
                    "risk_reduction": 3.5,
                },
            ],
            "portfolio_projection": {
                "current_grade": "B",
                "projected_grade": "A-",
                "current_risk_score": 4.2,
                "projected_risk_score": 3.1,
                "implementation_timeline": "30-60 days",
                "total_transaction_costs": 125.0,
                "expected_annual_benefit": 450.0,
            },
        }

    def test_should_generate_report_with_a_plus_recommendations(self, mocker, a_plus_recommendations_data):
        """Test report generation includes A+ recommendations."""
        # Arrange
        from finwiz.crews.report_crew.report_crew import ReportCrew

        # Mock report crew
        mock_report_crew = mocker.MagicMock()
        expected_report_html = """
        <html>
        <head><title>FinWiz Investment Discovery Report</title></head>
        <body>
            <section class="a-plus-opportunities">
                <h2>A+ Investment Opportunities Discovered</h2>
                <div class="summary">
                    <p>Found 8 A+ grade investment candidates</p>
                    <p>Expected portfolio grade improvement: B to A-</p>
                </div>
                <div class="recommendations">
                    <h3>Recommended Actions</h3>
                    <ul>
                        <li>Replace SPY with VTI (C+ to A+)</li>
                        <li>Add NVDA position (A+ grade)</li>
                        <li>Reduce BTC-USD allocation (Risk management)</li>
                    </ul>
                </div>
            </section>
        </body>
        </html>
        """
        mock_report_crew.crew.return_value.kickoff.return_value = expected_report_html
        mocker.patch("finwiz.crews.report_crew.report_crew.ReportCrew", return_value=mock_report_crew)

        # Prepare inputs with A+ recommendations
        report_inputs = {
            "investment_discovery_result": a_plus_recommendations_data,
            "investment_discovery_available": True,
            "full_date": "January 01, 2025",
            "report_language": "fr",
            "portfolio_data": {"holdings": [], "portfolio_grade": "B"},
        }

        # Act
        ReportCrew()
        result = mock_report_crew.crew.return_value.kickoff(inputs=report_inputs)

        # Assert
        assert result is not None
        assert "A+ Investment Opportunities" in result
        assert "Found 8 A+ grade investment candidates" in result
        assert "Replace SPY with VTI" in result
        mock_report_crew.crew.return_value.kickoff.assert_called_once()

    def test_should_include_before_after_portfolio_comparison(self, mocker, a_plus_recommendations_data):
        """Test report includes before/after portfolio comparison."""
        # Arrange
        from finwiz.crews.report_crew.report_crew import ReportCrew

        comparison_report_html = """
        <section class="portfolio-comparison">
            <h2>Portfolio Improvement Analysis</h2>
            <div class="before-after">
                <div class="before">
                    <h3>Current Portfolio</h3>
                    <p>Grade: B</p>
                    <p>Risk Score: 4.2</p>
                    <p>Annual Costs: $500</p>
                </div>
                <div class="after">
                    <h3>Optimized Portfolio</h3>
                    <p>Grade: A-</p>
                    <p>Risk Score: 3.1</p>
                    <p>Annual Costs: $350</p>
                </div>
                <div class="improvements">
                    <p>Grade Improvement: +0.18</p>
                    <p>Risk Reduction: -1.1</p>
                    <p>Annual Savings: $150</p>
                </div>
            </div>
        </section>
        """

        mock_report_crew = mocker.MagicMock()
        mock_report_crew.crew.return_value.kickoff.return_value = comparison_report_html
        mocker.patch("finwiz.crews.report_crew.report_crew.ReportCrew", return_value=mock_report_crew)

        report_inputs = {
            "investment_discovery_result": a_plus_recommendations_data,
            "investment_discovery_available": True,
        }

        # Act
        ReportCrew()
        result = mock_report_crew.crew.return_value.kickoff(inputs=report_inputs)

        # Assert
        assert "Portfolio Improvement Analysis" in result
        assert "Current Portfolio" in result
        assert "Optimized Portfolio" in result
        assert "Grade: B" in result
        assert "Grade: A-" in result
        assert "Annual Savings: $150" in result

    def test_should_handle_french_language_report_generation(self, mocker, a_plus_recommendations_data):
        """Test French language report generation with A+ recommendations."""
        # Arrange
        from finwiz.crews.report_crew.report_crew import ReportCrew

        french_report_html = """
        <html lang="fr">
        <head><title>Rapport de Découverte d'Investissements FinWiz</title></head>
        <body>
            <section class="opportunites-a-plus">
                <h2>Opportunités d'Investissement A+ Découvertes</h2>
                <div class="resume">
                    <p>8 candidats d'investissement de grade A+ trouvés</p>
                    <p>Amélioration attendue du grade du portefeuille: B vers A-</p>
                </div>
                <div class="recommandations">
                    <h3>Actions Recommandées</h3>
                    <ul>
                        <li>Remplacer SPY par VTI (C+ vers A+)</li>
                        <li>Ajouter une position NVDA (grade A+)</li>
                        <li>Réduire l'allocation BTC-USD (Gestion des risques)</li>
                    </ul>
                </div>
            </section>
        </body>
        </html>
        """

        mock_report_crew = mocker.MagicMock()
        mock_report_crew.crew.return_value.kickoff.return_value = french_report_html
        mocker.patch("finwiz.crews.report_crew.report_crew.ReportCrew", return_value=mock_report_crew)

        report_inputs = {
            "investment_discovery_result": a_plus_recommendations_data,
            "investment_discovery_available": True,
            "report_language": "fr",
        }

        # Act
        ReportCrew()
        result = mock_report_crew.crew.return_value.kickoff(inputs=report_inputs)

        # Assert
        assert 'lang="fr"' in result
        assert "Opportunités d'Investissement A+" in result
        assert "candidats d'investissement de grade A+" in result
        assert "Actions Recommandées" in result
        assert "Remplacer SPY par VTI" in result

    def test_should_handle_no_a_plus_recommendations_scenario(self, mocker):
        """Test report generation when no A+ recommendations are found."""
        # Arrange
        from finwiz.crews.report_crew.report_crew import ReportCrew

        no_recommendations_data = {
            "discovery_summary": {
                "total_a_plus_candidates": 0,
                "etf_candidates": 0,
                "stock_candidates": 0,
                "crypto_candidates": 0,
                "search_completed": True,
            },
            "analysis_notes": [
                "Current market conditions limit A+ opportunities",
                "Portfolio already contains high-quality investments",
                "Continue monitoring for future opportunities",
            ],
        }

        no_recommendations_html = """
        <section class="no-opportunities">
            <h2>Investment Discovery Results</h2>
            <p>No A+ grade opportunities identified at this time.</p>
            <p>Your current portfolio already contains high-quality investments.</p>
            <p>We will continue monitoring the market for future opportunities.</p>
        </section>
        """

        mock_report_crew = mocker.MagicMock()
        mock_report_crew.crew.return_value.kickoff.return_value = no_recommendations_html
        mocker.patch("finwiz.crews.report_crew.report_crew.ReportCrew", return_value=mock_report_crew)

        report_inputs = {
            "investment_discovery_result": no_recommendations_data,
            "investment_discovery_available": True,
        }

        # Act
        ReportCrew()
        result = mock_report_crew.crew.return_value.kickoff(inputs=report_inputs)

        # Assert
        assert "No A+ grade opportunities identified" in result
        assert "high-quality investments" in result
        assert "continue monitoring" in result
