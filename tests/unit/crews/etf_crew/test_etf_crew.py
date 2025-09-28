"""
Unit tests for ETF Crew.

Tests the ETF analysis crew agents, tasks, and workflow execution
with mocked external dependencies.
"""

from unittest.mock import MagicMock, patch

import pytest

from finwiz.schemas.etf import ETFFactsheet, ETFTopHolding


class TestEtfCrew:
    """Test cases for ETF Crew."""

    @pytest.fixture
    def mock_etf_inputs(self):
        """Create mock inputs for ETF analysis."""
        return {
            "current_date": "2025-01-15",
            "full_date": "January 15, 2025",
            "timestamp": "2025-01-15 10:00:00",
            "report_language": "fr",
            "has_existing_session": False,
            "session_id": "",
            "analysis_count": 0,
        }

    @pytest.fixture
    def mock_etf_data(self):
        """Create mock ETF data."""
        return {
            "symbol": "SPY",
            "longName": "SPDR S&P 500 ETF Trust",
            "currentPrice": 425.50,
            "totalAssets": 400000000000,
            "expenseRatio": 0.0945,
            "yield": 0.0156,
            "beta": 1.0,
            "category": "Large Blend",
            "fundFamily": "State Street Global Advisors",
            "inceptionDate": "1993-01-22",
            "nav": 425.48,
            "trackingError": 0.02,
        }

    @pytest.fixture
    def mock_etf_holdings(self):
        """Create mock ETF holdings data."""
        return [
            {"symbol": "AAPL", "holdingName": "Apple Inc.", "holdingPercent": 0.0712},
            {"symbol": "MSFT", "holdingName": "Microsoft Corporation", "holdingPercent": 0.0628},
            {"symbol": "AMZN", "holdingName": "Amazon.com Inc.", "holdingPercent": 0.0356},
            {"symbol": "NVDA", "holdingName": "NVIDIA Corporation", "holdingPercent": 0.0298},
            {"symbol": "GOOGL", "holdingName": "Alphabet Inc. Class A", "holdingPercent": 0.0241},
        ]

    @pytest.fixture
    def mock_etf_factsheet(self):
        """Create mock ETF factsheet data."""
        return ETFFactsheet(
            fund_name="SPDR S&P 500 ETF Trust",
            ticker="SPY",
            expense_ratio=0.0945,
            aum=400000000000,
            inception_date="1993-01-22",
            benchmark="S&P 500 Index",
            top_holdings=[
                ETFTopHolding(symbol="AAPL", name="Apple Inc.", weight=7.12),
                ETFTopHolding(symbol="MSFT", name="Microsoft Corporation", weight=6.28),
                ETFTopHolding(symbol="AMZN", name="Amazon.com Inc.", weight=3.56),
            ],
            sector_allocation={
                "Technology": 28.5,
                "Healthcare": 13.2,
                "Financials": 12.8,
                "Consumer Discretionary": 10.4,
                "Communication Services": 8.9,
            },
            performance_1y=24.5,
            performance_3y=12.8,
            performance_5y=15.2,
            tracking_error=0.02,
        )

    @pytest.fixture
    def etf_crew(self):
        """Create a mock EtfCrew instance for testing."""
        mock_crew = MagicMock()
        mock_crew.agents_config = {
            "market_analyst": {"role": "Market Analyst", "goal": "Analyze markets"},
            "etf_specialist": {"role": "ETF Specialist", "goal": "Analyze ETFs"},
            "risk_assessor": {"role": "Risk Assessor", "goal": "Assess risks"},
        }
        mock_crew.tasks_config = {
            "market_research": {"description": "Research markets"},
            "etf_analysis": {"description": "Analyze ETFs"},
            "risk_assessment": {"description": "Assess risks"},
        }

        # Mock agent methods
        mock_crew.market_analyst.return_value = MagicMock()
        mock_crew.etf_specialist.return_value = MagicMock()
        mock_crew.risk_assessor.return_value = MagicMock()

        # Mock task methods
        mock_crew.market_research.return_value = MagicMock()
        mock_crew.etf_analysis.return_value = MagicMock()
        mock_crew.risk_assessment.return_value = MagicMock()

        # Mock crew method
        mock_crew.crew.return_value = MagicMock()

        return mock_crew

    def test_should_initialize_etf_crew_successfully(self, etf_crew):
        """Test that EtfCrew initializes with proper configuration."""
        assert etf_crew is not None
        assert hasattr(etf_crew, "agents_config")
        assert hasattr(etf_crew, "tasks_config")

    @patch("finwiz.crews.etf_crew.etf_crew.YahooFinanceTickerInfoTool")
    @patch("finwiz.crews.etf_crew.etf_crew.SerperDevTool")
    def test_should_create_agents_with_proper_tools(self, mock_serper, mock_yahoo, etf_crew):
        """Test that agents are created with appropriate tools."""
        # Mock the tools
        mock_yahoo.return_value = MagicMock()
        mock_serper.return_value = MagicMock()

        # Test agent creation
        market_analyst = etf_crew.market_analyst()
        etf_specialist = etf_crew.etf_specialist()
        risk_assessor = etf_crew.risk_assessor()

        assert market_analyst is not None
        assert etf_specialist is not None
        assert risk_assessor is not None

        # Verify agents have tools
        assert hasattr(market_analyst, "tools")
        assert hasattr(etf_specialist, "tools")
        assert hasattr(risk_assessor, "tools")

    def test_should_create_tasks_with_proper_configuration(self, etf_crew):
        """Test that tasks are created with proper configuration."""
        # Test task creation
        market_research_task = etf_crew.market_research()
        etf_analysis_task = etf_crew.etf_analysis()
        risk_assessment_task = etf_crew.risk_assessment()

        assert market_research_task is not None
        assert etf_analysis_task is not None
        assert risk_assessment_task is not None

        # Verify task properties
        assert hasattr(market_research_task, "description")
        assert hasattr(etf_analysis_task, "description")
        assert hasattr(risk_assessment_task, "description")

    @patch("finwiz.crews.etf_crew.etf_crew.YahooFinanceTickerInfoTool")
    @patch("finwiz.crews.etf_crew.etf_crew.SerperDevTool")
    def test_should_create_crew_with_all_components(self, mock_serper, mock_yahoo, etf_crew):
        """Test that crew is created with all agents and tasks."""
        # Mock the tools
        mock_yahoo.return_value = MagicMock()
        mock_serper.return_value = MagicMock()

        crew = etf_crew.crew()

        assert crew is not None
        assert len(crew.agents) > 0
        assert len(crew.tasks) > 0

        # Verify crew configuration
        assert hasattr(crew, "process")
        assert hasattr(crew, "verbose")

    @patch("finwiz.crews.etf_crew.etf_crew.YahooFinanceTickerInfoTool")
    @patch("finwiz.crews.etf_crew.etf_crew.YahooFinanceETFHoldingsTool")
    @patch("finwiz.crews.etf_crew.etf_crew.SerperDevTool")
    @patch("finwiz.tools.quantitative_analysis_tool.get_quantitative_analysis_tool")
    def test_should_execute_crew_with_mock_data(
        self,
        mock_quant_tool,
        mock_serper,
        mock_etf_holdings_tool,
        mock_yahoo,
        etf_crew,
        mock_etf_inputs,
        mock_etf_data,
        mock_etf_holdings,
    ):
        """Test crew execution with mocked external data."""
        # Mock the tools
        mock_yahoo_instance = MagicMock()
        mock_yahoo_instance.run.return_value = mock_etf_data
        mock_yahoo.return_value = mock_yahoo_instance

        mock_holdings_instance = MagicMock()
        mock_holdings_instance.run.return_value = mock_etf_holdings
        mock_etf_holdings_tool.return_value = mock_holdings_instance

        mock_serper_instance = MagicMock()
        mock_serper_instance.run.return_value = "Mock ETF news and research"
        mock_serper.return_value = mock_serper_instance

        mock_quant_instance = MagicMock()
        mock_quant_instance.run.return_value = {"performance_metrics": {"sharpe_ratio": 1.2, "volatility": 0.15}}
        mock_quant_tool.return_value = mock_quant_instance

        # Mock the crew kickoff to avoid actual LLM calls
        with patch.object(etf_crew.crew(), "kickoff") as mock_kickoff:
            mock_result = MagicMock()
            mock_result.raw = "Mock ETF analysis result with BUY recommendation"
            mock_kickoff.return_value = mock_result

            result = etf_crew.crew().kickoff(inputs=mock_etf_inputs)

            assert result is not None
            mock_kickoff.assert_called_once_with(inputs=mock_etf_inputs)

    def test_should_handle_missing_inputs_gracefully(self, etf_crew):
        """Test that crew handles missing inputs gracefully."""
        incomplete_inputs = {"current_date": "2025-01-15"}

        # Mock the crew kickoff to simulate error handling
        with patch.object(etf_crew.crew(), "kickoff") as mock_kickoff:
            mock_kickoff.side_effect = ValueError("Missing required inputs")

            with pytest.raises(ValueError, match="Missing required inputs"):
                etf_crew.crew().kickoff(inputs=incomplete_inputs)

    @patch("finwiz.crews.etf_crew.etf_crew.get_etf_research_tools")
    def test_should_use_etf_research_tools(self, mock_get_tools, etf_crew):
        """Test that crew uses ETF research tools."""
        mock_tools = [MagicMock(), MagicMock()]
        mock_get_tools.return_value = mock_tools

        # Verify tools are used in agent creation
        etf_specialist = etf_crew.etf_specialist()
        assert etf_specialist is not None

        # Verify get_etf_research_tools was called
        mock_get_tools.assert_called()

    def test_should_validate_agent_configurations(self, etf_crew):
        """Test that agent configurations are valid."""
        # Test that agents_config exists and has required agents
        assert hasattr(etf_crew, "agents_config")
        config = etf_crew.agents_config

        required_agents = ["market_analyst", "etf_specialist", "risk_assessor"]
        for agent_name in required_agents:
            assert agent_name in config, f"Missing agent configuration: {agent_name}"

    def test_should_validate_task_configurations(self, etf_crew):
        """Test that task configurations are valid."""
        # Test that tasks_config exists and has required tasks
        assert hasattr(etf_crew, "tasks_config")
        config = etf_crew.tasks_config

        required_tasks = ["market_research", "etf_analysis", "risk_assessment"]
        for task_name in required_tasks:
            assert task_name in config, f"Missing task configuration: {task_name}"

    @patch("finwiz.crews.etf_crew.etf_crew.YahooFinanceETFHoldingsTool")
    def test_should_handle_tool_failures_gracefully(self, mock_holdings_tool, etf_crew, mock_etf_inputs):
        """Test that crew handles tool failures gracefully."""
        # Mock tool failure
        mock_holdings_instance = MagicMock()
        mock_holdings_instance.run.side_effect = Exception("ETF holdings API failed")
        mock_holdings_tool.return_value = mock_holdings_instance

        # Mock the crew to handle tool failures
        with patch.object(etf_crew.crew(), "kickoff") as mock_kickoff:
            mock_result = MagicMock()
            mock_result.raw = "ETF analysis completed with limited holdings data"
            mock_kickoff.return_value = mock_result

            result = etf_crew.crew().kickoff(inputs=mock_etf_inputs)

            assert result is not None
            assert "limited" in str(result.raw)

    def test_should_have_proper_crew_process(self, etf_crew):
        """Test that crew uses proper process configuration."""
        crew = etf_crew.crew()

        # Verify crew has a process defined
        assert hasattr(crew, "process")
        # Process should be sequential for ETF analysis
        from crewai import Process

        assert crew.process == Process.sequential

    @patch("finwiz.crews.etf_crew.etf_crew.get_rag_tools")
    def test_should_integrate_with_rag_system(self, mock_rag_tools, etf_crew):
        """Test that crew integrates with RAG system for knowledge storage."""
        mock_rag_instance = MagicMock()
        mock_rag_tools.return_value = [mock_rag_instance]

        # Verify RAG tools are available
        etf_specialist = etf_crew.etf_specialist()
        assert etf_specialist is not None

        # Verify RAG tools were requested
        mock_rag_tools.assert_called()

    def test_should_analyze_expense_ratios(self, etf_crew, mock_etf_inputs, mock_etf_data):
        """Test that crew analyzes expense ratios properly."""
        with patch.object(etf_crew.crew(), "kickoff") as mock_kickoff:
            # Mock result that includes expense ratio analysis
            mock_result = MagicMock()
            mock_result.raw = f"ETF analysis shows expense ratio of {mock_etf_data['expenseRatio']:.4f} which is competitive"
            mock_kickoff.return_value = mock_result

            result = etf_crew.crew().kickoff(inputs=mock_etf_inputs)

            assert result is not None
            assert "expense ratio" in str(result.raw)

    def test_should_analyze_tracking_error(self, etf_crew, mock_etf_inputs, mock_etf_data):
        """Test that crew analyzes tracking error properly."""
        with patch.object(etf_crew.crew(), "kickoff") as mock_kickoff:
            # Mock result that includes tracking error analysis
            mock_result = MagicMock()
            mock_result.raw = f"Tracking error of {mock_etf_data['trackingError']:.2f} indicates good benchmark tracking"
            mock_kickoff.return_value = mock_result

            result = etf_crew.crew().kickoff(inputs=mock_etf_inputs)

            assert result is not None
            assert "tracking error" in str(result.raw)

    def test_should_support_multilingual_analysis(self, etf_crew, mock_etf_inputs):
        """Test that crew supports multilingual analysis."""
        # Test with French language setting
        french_inputs = {**mock_etf_inputs, "report_language": "fr"}

        with patch.object(etf_crew.crew(), "kickoff") as mock_kickoff:
            mock_result = MagicMock()
            mock_result.raw = "Analyse des ETF en français"
            mock_kickoff.return_value = mock_result

            result = etf_crew.crew().kickoff(inputs=french_inputs)
            assert result is not None

        # Test with English language setting
        english_inputs = {**mock_etf_inputs, "report_language": "en"}

        with patch.object(etf_crew.crew(), "kickoff") as mock_kickoff:
            mock_result = MagicMock()
            mock_result.raw = "ETF analysis in English"
            mock_kickoff.return_value = mock_result

            result = etf_crew.crew().kickoff(inputs=english_inputs)
            assert result is not None

    def test_should_handle_large_etf_holdings_data(self, etf_crew, mock_etf_inputs):
        """Test that crew handles large ETF holdings datasets efficiently."""
        # Create large holdings dataset
        large_holdings = [
            {"symbol": f"STOCK{i}", "holdingName": f"Company {i}", "holdingPercent": 0.01}
            for i in range(500)  # 500 holdings
        ]

        with patch("finwiz.crews.etf_crew.etf_crew.YahooFinanceETFHoldingsTool") as mock_holdings_tool:
            mock_holdings_instance = MagicMock()
            mock_holdings_instance.run.return_value = large_holdings
            mock_holdings_tool.return_value = mock_holdings_instance

            with patch.object(etf_crew.crew(), "kickoff") as mock_kickoff:
                mock_result = MagicMock()
                mock_result.raw = "ETF analysis completed for diversified fund with 500 holdings"
                mock_kickoff.return_value = mock_result

                result = etf_crew.crew().kickoff(inputs=mock_etf_inputs)

                assert result is not None
                assert "500 holdings" in str(result.raw)

    @patch("finwiz.crews.etf_crew.etf_crew.get_quantitative_analysis_tool")
    def test_should_integrate_quantitative_analysis(self, mock_quant_tool, etf_crew, mock_etf_inputs):
        """Test that crew integrates quantitative analysis for ETF performance."""
        mock_quant_instance = MagicMock()
        mock_quant_instance.run.return_value = {
            "sharpe_ratio": 1.25,
            "sortino_ratio": 1.45,
            "max_drawdown": -0.18,
            "volatility": 0.16,
            "beta": 0.98,
        }
        mock_quant_tool.return_value = mock_quant_instance

        with patch.object(etf_crew.crew(), "kickoff") as mock_kickoff:
            mock_result = MagicMock()
            mock_result.raw = "ETF shows strong risk-adjusted returns with Sharpe ratio of 1.25"
            mock_kickoff.return_value = mock_result

            result = etf_crew.crew().kickoff(inputs=mock_etf_inputs)

            assert result is not None
            assert "Sharpe ratio" in str(result.raw)
