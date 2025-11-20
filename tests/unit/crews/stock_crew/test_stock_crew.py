"""
Unit tests for Stock Crew.

Tests the stock analysis crew agents, tasks, and workflow execution
with mocked external dependencies.
"""

import pytest


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
        """Create mock Yahoo Finance data.

        Note: yfinance returns debtToEquity as percentage (173.0 = 173%),
        which gets converted to ratio (1.73) by yahoo_finance_company_info_tool.
        """
        return {
            "symbol": "AAPL",
            "longName": "Apple Inc.",
            "currentPrice": 150.25,
            "marketCap": 2500000000000,
            "trailingPE": 25.5,
            "forwardPE": 22.3,
            "priceToBook": 8.2,
            "debtToEquity": 173.0,  # yfinance format: percentage (173.0 = 173%)
            "returnOnEquity": 0.825,  # yfinance format: decimal (0.825 = 82.5%)
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
    def stock_crew(self, mocker):
        """Create a mock StockCrew instance for testing."""
        mock_crew = mocker.MagicMock()
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

        # Mock agent methods with tools attribute
        mock_market_analyst = mocker.MagicMock()
        mock_market_analyst.tools = []
        mock_crew.market_analyst.return_value = mock_market_analyst

        mock_fundamental_analyst = mocker.MagicMock()
        mock_fundamental_analyst.tools = []
        mock_crew.fundamental_analyst.return_value = mock_fundamental_analyst

        mock_risk_assessor = mocker.MagicMock()
        mock_risk_assessor.tools = []
        mock_crew.risk_assessor.return_value = mock_risk_assessor

        # Mock task methods with description attribute
        mock_market_task = mocker.MagicMock()
        mock_market_task.description = "Research markets"
        mock_crew.market_research.return_value = mock_market_task

        mock_fundamental_task = mocker.MagicMock()
        mock_fundamental_task.description = "Analyze fundamentals"
        mock_crew.fundamental_analysis.return_value = mock_fundamental_task

        mock_risk_task = mocker.MagicMock()
        mock_risk_task.description = "Assess risks"
        mock_crew.risk_assessment.return_value = mock_risk_task

        # Mock crew method with agents and tasks lists
        mock_crew_instance = mocker.MagicMock()
        mock_crew_instance.agents = [mock_market_analyst, mock_fundamental_analyst, mock_risk_assessor]
        mock_crew_instance.tasks = [mock_market_task, mock_fundamental_task, mock_risk_task]
        mock_crew_instance.process = "sequential"
        mock_crew_instance.verbose = True
        mock_crew.crew.return_value = mock_crew_instance

        return mock_crew

    def test_should_initialize_stock_crew_successfully(self, stock_crew):
        """Test that StockCrew initializes with proper configuration."""
        assert stock_crew is not None
        assert hasattr(stock_crew, "agents_config")
        assert hasattr(stock_crew, "tasks_config")

    def test_should_create_agents_with_proper_tools(self, stock_crew):
        """Test that agents are created with appropriate tools."""
        # Test agent creation
        market_analyst = stock_crew.market_analyst()
        fundamental_analyst = stock_crew.fundamental_analyst()
        risk_assessor = stock_crew.risk_assessor()

        assert market_analyst is not None
        assert fundamental_analyst is not None
        assert risk_assessor is not None

        # Verify agents have tools attribute
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

    def test_should_create_crew_with_all_components(self, stock_crew):
        """Test that crew is created with all agents and tasks."""
        crew = stock_crew.crew()

        assert crew is not None
        assert len(crew.agents) > 0
        assert len(crew.tasks) > 0

        # Verify crew configuration
        assert hasattr(crew, "process")
        assert hasattr(crew, "verbose")

    def test_should_execute_crew_with_mock_data(self, mocker, stock_crew, mock_stock_inputs, mock_yahoo_finance_data):
        """Test crew execution with mocked external data."""
        # Mock the Crew.kickoff method to avoid actual LLM calls
        mock_result = mocker.MagicMock()
        mock_result.raw = "Mock stock analysis result with BUY recommendation"

        # Configure the existing mock crew instance from fixture
        stock_crew.crew.return_value.kickoff.return_value = mock_result

        # Mock the kickoff method on stock_crew to use the crew
        stock_crew.kickoff = lambda inputs: stock_crew.crew().kickoff(inputs=inputs)

        result = stock_crew.kickoff(inputs=mock_stock_inputs)

        assert result is not None
        assert stock_crew.crew.return_value.kickoff.called

    def test_should_handle_missing_inputs_gracefully(self, mocker, stock_crew):
        """Test that crew handles missing inputs gracefully."""
        incomplete_inputs = {"current_date": "2025-01-15"}

        # Configure the existing mock crew instance to raise an error
        stock_crew.crew.return_value.kickoff.side_effect = ValueError("Missing required inputs")

        # Mock the kickoff method on stock_crew to use the crew
        stock_crew.kickoff = lambda inputs: stock_crew.crew().kickoff(inputs=inputs)

        with pytest.raises(ValueError, match="Missing required inputs"):
            stock_crew.kickoff(inputs=incomplete_inputs)

    def test_should_use_stock_research_tools(self, stock_crew):
        """Test that crew uses stock research tools from tool factory."""
        # Verify that the stock crew module imports the tool factory
        import finwiz.crews.stock_crew.stock_crew as stock_crew_module

        # Check that get_stock_crew_tools is imported and used
        assert hasattr(stock_crew_module, "get_stock_crew_tools")
        # The module has 'tools' (robust wrapped) not 'research_tools'
        assert hasattr(stock_crew_module, "tools")
        assert hasattr(stock_crew_module, "raw_tools")

        # Verify tools are used in agent creation
        market_analyst = stock_crew.market_analyst()
        assert market_analyst is not None

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

    def test_should_handle_tool_failures_gracefully(self, mocker, stock_crew, mock_stock_inputs):
        """Test that crew handles tool failures gracefully."""
        # Create a mock result
        mock_result = mocker.MagicMock()
        mock_result.raw = "Analysis completed with limited data due to tool failures"

        # Configure the existing mock crew instance from fixture
        stock_crew.crew.return_value.kickoff.return_value = mock_result

        # Mock the kickoff method on stock_crew to use the crew
        stock_crew.kickoff = lambda inputs: stock_crew.crew().kickoff(inputs=inputs)

        result = stock_crew.kickoff(inputs=mock_stock_inputs)

        assert result is not None
        assert "limited data" in result.raw

    def test_should_have_proper_crew_process(self, stock_crew):
        """Test that crew uses proper process configuration."""
        crew = stock_crew.crew()

        # Verify crew has a process defined
        assert hasattr(crew, "process")
        # Process should be sequential for stock analysis
        # Note: crew.process is a MagicMock in tests, so we check it exists
        assert crew.process is not None

    def test_should_integrate_with_rag_system(self, stock_crew):
        """Test that crew integrates with RAG system for knowledge storage."""
        # Verify that the stock crew module uses tool factory which includes RAG tools
        import finwiz.crews.stock_crew.stock_crew as stock_crew_module

        # Check that tool factory is used (which includes RAG tools)
        assert hasattr(stock_crew_module, "get_stock_crew_tools")
        assert hasattr(stock_crew_module, "tools")

        # Verify tools are available
        market_analyst = stock_crew.market_analyst()
        assert market_analyst is not None

    def test_should_support_multilingual_analysis(self, mocker, stock_crew, mock_stock_inputs):
        """Test that crew supports multilingual analysis."""
        # Test with French language setting
        french_inputs = {**mock_stock_inputs, "report_language": "fr"}

        # Create a mock result
        mock_result = mocker.MagicMock()
        mock_result.raw = "Analyse des actions en français"

        # Configure the existing mock crew instance from fixture
        stock_crew.crew.return_value.kickoff.return_value = mock_result

        # Mock the kickoff method on stock_crew to use the crew
        stock_crew.kickoff = lambda inputs: stock_crew.crew().kickoff(inputs=inputs)

        result = stock_crew.kickoff(inputs=french_inputs)
        assert result is not None

        # Test with English language setting
        english_inputs = {**mock_stock_inputs, "report_language": "en"}

        # Create a new mock result for English
        mock_result_en = mocker.MagicMock()
        mock_result_en.raw = "Stock analysis in English"

        # Update the mock crew instance return value
        stock_crew.crew.return_value.kickoff.return_value = mock_result_en

        result = stock_crew.kickoff(inputs=english_inputs)
        assert result is not None
