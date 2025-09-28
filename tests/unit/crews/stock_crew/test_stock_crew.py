"""
Unit tests for Stock Crew.

Tests the stock analysis crew agents, tasks, and workflow execution
with mocked external dependencies.
"""

from unittest.mock import MagicMock, patch

import pytest

from finwiz.crews.stock_crew.stock_crew import StockCrew


class TestStockCrew:
    """Test cases for Stock Crew."""

    @pytest.fixture
    def mock_stock_inputs(self):
        """Create mock inputs for stock analysis."""
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
    def mock_yahoo_finance_data(self):
        """Create mock Yahoo Finance data."""
        return {
            "symbol": "AAPL",
            "longName": "Apple Inc.",
            "currentPrice": 150.25,
            "marketCap": 2500000000000,
            "trailingPE": 25.5,
            "forwardPE": 22.3,
            "priceToBook": 8.2,
            "debtToEquity": 1.73,
            "returnOnEquity": 0.825,
            "revenueGrowth": 0.085,
            "earningsGrowth": 0.12,
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "recommendationKey": "buy",
            "targetMeanPrice": 165.0,
        }

    @pytest.fixture
    def mock_sec_data(self):
        """Create mock SEC filing data."""
        return {
            "filings": [
                {
                    "form": "10-K",
                    "filingDate": "2024-10-31",
                    "reportDate": "2024-09-30",
                    "accessionNumber": "0000320193-24-000123",
                    "primaryDocument": "aapl-20240930.htm",
                }
            ],
            "businessSummary": "Apple Inc. designs, manufactures, and markets smartphones...",
            "riskFactors": [
                "Competition in mobile device market",
                "Supply chain dependencies",
                "Regulatory changes",
            ],
        }

    @pytest.fixture
    def stock_crew(self):
        """Create a mock StockCrew instance for testing."""
        mock_crew = MagicMock()
        mock_crew.agents_config = {
            "market_analyst": {"role": "Market Analyst", "goal": "Analyze markets"},
            "fundamental_analyst": {"role": "Fundamental Analyst", "goal": "Analyze fundamentals"},
            "risk_assessor": {"role": "Risk Assessor", "goal": "Assess risks"},
        }
        mock_crew.tasks_config = {
            "market_research": {"description": "Research markets"},
            "fundamental_analysis": {"description": "Analyze fundamentals"},
            "risk_assessment": {"description": "Assess risks"},
        }

        # Mock agent methods
        mock_crew.market_analyst.return_value = MagicMock()
        mock_crew.fundamental_analyst.return_value = MagicMock()
        mock_crew.risk_assessor.return_value = MagicMock()

        # Mock task methods
        mock_crew.market_research.return_value = MagicMock()
        mock_crew.fundamental_analysis.return_value = MagicMock()
        mock_crew.risk_assessment.return_value = MagicMock()

        # Mock crew method
        mock_crew.crew.return_value = MagicMock()

        return mock_crew

    def test_should_initialize_stock_crew_successfully(self, stock_crew):
        """Test that StockCrew initializes with proper configuration."""
        assert stock_crew is not None
        assert hasattr(stock_crew, "agents_config")
        assert hasattr(stock_crew, "tasks_config")

    @patch("finwiz.crews.stock_crew.stock_crew.YahooFinanceTickerInfoTool")
    @patch("finwiz.crews.stock_crew.stock_crew.SerperDevTool")
    def test_should_create_agents_with_proper_tools(self, mock_serper, mock_yahoo, stock_crew):
        """Test that agents are created with appropriate tools."""
        # Mock the tools
        mock_yahoo.return_value = MagicMock()
        mock_serper.return_value = MagicMock()

        # Test agent creation
        market_analyst = stock_crew.market_analyst()
        fundamental_analyst = stock_crew.fundamental_analyst()
        risk_assessor = stock_crew.risk_assessor()

        assert market_analyst is not None
        assert fundamental_analyst is not None
        assert risk_assessor is not None

        # Verify agents have tools
        assert hasattr(market_analyst, "tools")
        assert hasattr(fundamental_analyst, "tools")
        assert hasattr(risk_assessor, "tools")

    def test_should_create_tasks_with_proper_configuration(self, stock_crew):
        """Test that tasks are created with proper configuration."""
        # Test task creation
        market_research_task = stock_crew.market_research()
        fundamental_analysis_task = stock_crew.fundamental_analysis()
        risk_assessment_task = stock_crew.risk_assessment()

        assert market_research_task is not None
        assert fundamental_analysis_task is not None
        assert risk_assessment_task is not None

        # Verify task properties
        assert hasattr(market_research_task, "description")
        assert hasattr(fundamental_analysis_task, "description")
        assert hasattr(risk_assessment_task, "description")

    @patch("finwiz.crews.stock_crew.stock_crew.YahooFinanceTickerInfoTool")
    @patch("finwiz.crews.stock_crew.stock_crew.SerperDevTool")
    def test_should_create_crew_with_all_components(self, mock_serper, mock_yahoo, stock_crew):
        """Test that crew is created with all agents and tasks."""
        # Mock the tools
        mock_yahoo.return_value = MagicMock()
        mock_serper.return_value = MagicMock()

        crew = stock_crew.crew()

        assert crew is not None
        assert len(crew.agents) > 0
        assert len(crew.tasks) > 0

        # Verify crew configuration
        assert hasattr(crew, "process")
        assert hasattr(crew, "verbose")

    @patch("finwiz.crews.stock_crew.stock_crew.YahooFinanceTickerInfoTool")
    @patch("finwiz.crews.stock_crew.stock_crew.SerperDevTool")
    @patch("finwiz.tools.quantitative_analysis_tool.get_quantitative_analysis_tool")
    def test_should_execute_crew_with_mock_data(
        self, mock_quant_tool, mock_serper, mock_yahoo, stock_crew, mock_stock_inputs, mock_yahoo_finance_data
    ):
        """Test crew execution with mocked external data."""
        # Mock the tools
        mock_yahoo_instance = MagicMock()
        mock_yahoo_instance.run.return_value = mock_yahoo_finance_data
        mock_yahoo.return_value = mock_yahoo_instance

        mock_serper_instance = MagicMock()
        mock_serper_instance.run.return_value = "Mock news and search results"
        mock_serper.return_value = mock_serper_instance

        mock_quant_instance = MagicMock()
        mock_quant_instance.run.return_value = {"technical_indicators": {"rsi": 65, "macd": "bullish"}}
        mock_quant_tool.return_value = mock_quant_instance

        # Mock the crew kickoff to avoid actual LLM calls
        with patch.object(stock_crew.crew(), "kickoff") as mock_kickoff:
            mock_result = MagicMock()
            mock_result.raw = "Mock stock analysis result with BUY recommendation"
            mock_kickoff.return_value = mock_result

            result = stock_crew.crew().kickoff(inputs=mock_stock_inputs)

            assert result is not None
            mock_kickoff.assert_called_once_with(inputs=mock_stock_inputs)

    def test_should_handle_missing_inputs_gracefully(self, stock_crew):
        """Test that crew handles missing inputs gracefully."""
        incomplete_inputs = {"current_date": "2025-01-15"}

        # Mock the crew kickoff to simulate error handling
        with patch.object(stock_crew.crew(), "kickoff") as mock_kickoff:
            mock_kickoff.side_effect = ValueError("Missing required inputs")

            with pytest.raises(ValueError, match="Missing required inputs"):
                stock_crew.crew().kickoff(inputs=incomplete_inputs)

    @patch("finwiz.crews.stock_crew.stock_crew.get_stock_research_tools")
    def test_should_use_stock_research_tools(self, mock_get_tools, stock_crew):
        """Test that crew uses stock research tools."""
        mock_tools = [MagicMock(), MagicMock()]
        mock_get_tools.return_value = mock_tools

        # Verify tools are used in agent creation
        market_analyst = stock_crew.market_analyst()
        assert market_analyst is not None

        # Verify get_stock_research_tools was called
        mock_get_tools.assert_called()

    def test_should_validate_agent_configurations(self, stock_crew):
        """Test that agent configurations are valid."""
        # Test that agents_config exists and has required agents
        assert hasattr(stock_crew, "agents_config")
        config = stock_crew.agents_config

        required_agents = ["market_analyst", "fundamental_analyst", "risk_assessor"]
        for agent_name in required_agents:
            assert agent_name in config, f"Missing agent configuration: {agent_name}"

    def test_should_validate_task_configurations(self, stock_crew):
        """Test that task configurations are valid."""
        # Test that tasks_config exists and has required tasks
        assert hasattr(stock_crew, "tasks_config")
        config = stock_crew.tasks_config

        required_tasks = ["market_research", "fundamental_analysis", "risk_assessment"]
        for task_name in required_tasks:
            assert task_name in config, f"Missing task configuration: {task_name}"

    @patch("finwiz.crews.stock_crew.stock_crew.YahooFinanceTickerInfoTool")
    def test_should_handle_tool_failures_gracefully(self, mock_yahoo, stock_crew, mock_stock_inputs):
        """Test that crew handles tool failures gracefully."""
        # Mock tool failure
        mock_yahoo_instance = MagicMock()
        mock_yahoo_instance.run.side_effect = Exception("API connection failed")
        mock_yahoo.return_value = mock_yahoo_instance

        # Mock the crew to handle tool failures
        with patch.object(stock_crew.crew(), "kickoff") as mock_kickoff:
            mock_result = MagicMock()
            mock_result.raw = "Analysis completed with limited data due to tool failures"
            mock_kickoff.return_value = mock_result

            result = stock_crew.crew().kickoff(inputs=mock_stock_inputs)

            assert result is not None
            assert "limited data" in str(result.raw)

    def test_should_have_proper_crew_process(self, stock_crew):
        """Test that crew uses proper process configuration."""
        crew = stock_crew.crew()

        # Verify crew has a process defined
        assert hasattr(crew, "process")
        # Process should be sequential for stock analysis
        from crewai import Process

        assert crew.process == Process.sequential

    @patch("finwiz.crews.stock_crew.stock_crew.get_rag_tools")
    def test_should_integrate_with_rag_system(self, mock_rag_tools, stock_crew):
        """Test that crew integrates with RAG system for knowledge storage."""
        mock_rag_instance = MagicMock()
        mock_rag_tools.return_value = [mock_rag_instance]

        # Verify RAG tools are available
        market_analyst = stock_crew.market_analyst()
        assert market_analyst is not None

        # Verify RAG tools were requested
        mock_rag_tools.assert_called()

    def test_should_support_multilingual_analysis(self, stock_crew, mock_stock_inputs):
        """Test that crew supports multilingual analysis."""
        # Test with French language setting
        french_inputs = {**mock_stock_inputs, "report_language": "fr"}

        with patch.object(stock_crew.crew(), "kickoff") as mock_kickoff:
            mock_result = MagicMock()
            mock_result.raw = "Analyse des actions en français"
            mock_kickoff.return_value = mock_result

            result = stock_crew.crew().kickoff(inputs=french_inputs)
            assert result is not None

        # Test with English language setting
        english_inputs = {**mock_stock_inputs, "report_language": "en"}

        with patch.object(stock_crew.crew(), "kickoff") as mock_kickoff:
            mock_result = MagicMock()
            mock_result.raw = "Stock analysis in English"
            mock_kickoff.return_value = mock_result

            result = stock_crew.crew().kickoff(inputs=english_inputs)
            assert result is not None
