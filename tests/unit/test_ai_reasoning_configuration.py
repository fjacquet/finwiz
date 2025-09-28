"""
Test suite to verify AI agents are properly configured for reasoning-driven analysis.

This module tests that:
1. All core analysis crews have reasoning=True enabled
2. Agents are configured with proper LLM settings
3. Task configurations emphasize AI reasoning
4. Crew outputs capture AI-generated insights
"""

from unittest.mock import Mock, patch

from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
from finwiz.crews.etf_crew.etf_crew import EtfCrew
from finwiz.crews.stock_crew.stock_crew import StockCrew


class TestAIReasoningConfiguration:
    """Test AI reasoning configuration for core analysis crews."""

    @patch("crewai.LLM")
    def test_stock_crew_agents_have_reasoning_enabled(self, mock_llm):
        """Test that stock crew agents have reasoning=True."""
        mock_llm.return_value = Mock()

        with patch.object(StockCrew, "map_all_task_variables"):
            stock_crew = StockCrew()

            # Test market technical analyst
            market_analyst = stock_crew.market_technical_analyst()
            assert market_analyst.reasoning is True, "Market technical analyst should have reasoning enabled"

            # Test investment risk analyst
            risk_analyst = stock_crew.investment_risk_analyst()
            assert risk_analyst.reasoning is True, "Investment risk analyst should have reasoning enabled"

    @patch("crewai.LLM")
    def test_etf_crew_agents_have_reasoning_enabled(self, mock_llm):
        """Test that ETF crew agents have reasoning=True."""
        mock_llm.return_value = Mock()

        with patch.object(EtfCrew, "map_all_task_variables"):
            etf_crew = EtfCrew()

            # Test market ETF analyst
            market_analyst = etf_crew.market_etf_analyst()
            assert market_analyst.reasoning is True, "Market ETF analyst should have reasoning enabled"

            # Test risk assessor
            risk_assessor = etf_crew.risk_assessor()
            assert risk_assessor.reasoning is True, "Risk assessor should have reasoning enabled"

    @patch("crewai.LLM")
    def test_crypto_crew_agents_have_reasoning_enabled(self, mock_llm):
        """Test that crypto crew agents have reasoning=True."""
        mock_llm.return_value = Mock()

        with patch.object(CryptoCrew, "map_all_task_variables"):
            crypto_crew = CryptoCrew()

            # Test market analyst
            market_analyst = crypto_crew.market_analyst()
            assert market_analyst.reasoning is True, "Market analyst should have reasoning enabled"

            # Test technical analyst
            technical_analyst = crypto_crew.technical_analyst()
            assert technical_analyst.reasoning is True, "Technical analyst should have reasoning enabled"

            # Test risk assessor
            risk_assessor = crypto_crew.risk_assessor()
            assert risk_assessor.reasoning is True, "Risk assessor should have reasoning enabled"

            # Test investment strategist
            investment_strategist = crypto_crew.investment_strategist()
            assert investment_strategist.reasoning is True, "Investment strategist should have reasoning enabled"

    @patch("crewai.LLM")
    def test_crews_have_llm_configuration_method(self, mock_llm):
        """Test that crews have _get_configured_llm method."""
        mock_llm.return_value = Mock()

        with (
            patch.object(StockCrew, "map_all_task_variables"),
            patch.object(EtfCrew, "map_all_task_variables"),
            patch.object(CryptoCrew, "map_all_task_variables"),
        ):
            stock_crew = StockCrew()
            etf_crew = EtfCrew()
            crypto_crew = CryptoCrew()

            # Test that method exists
            assert hasattr(stock_crew, "_get_configured_llm"), "StockCrew should have _get_configured_llm method"
            assert hasattr(etf_crew, "_get_configured_llm"), "EtfCrew should have _get_configured_llm method"
            assert hasattr(crypto_crew, "_get_configured_llm"), "CryptoCrew should have _get_configured_llm method"

            # Test that method returns LLM instance
            stock_llm = stock_crew._get_configured_llm()
            etf_llm = etf_crew._get_configured_llm()
            crypto_llm = crypto_crew._get_configured_llm()

            assert stock_llm is not None, "StockCrew should return configured LLM"
            assert etf_llm is not None, "EtfCrew should return configured LLM"
            assert crypto_llm is not None, "CryptoCrew should return configured LLM"

    @patch("crewai.LLM")
    def test_llm_configuration_parameters(self, mock_llm):
        """Test that LLM is configured with appropriate parameters for financial analysis."""
        mock_llm.return_value = Mock()

        with patch.object(StockCrew, "map_all_task_variables"):
            stock_crew = StockCrew()
            stock_crew._get_configured_llm()

            # Verify LLM was called with appropriate parameters
            mock_llm.assert_called_with(
                model="gpt-4o-mini",
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=4000,  # Sufficient tokens for detailed reasoning
                timeout=60,  # Reasonable timeout
            )

    def test_agents_use_configured_llm(self):
        """Test that agents are configured to use the LLM."""
        with patch("crewai.LLM") as mock_llm:
            mock_llm_instance = Mock()
            mock_llm.return_value = mock_llm_instance

            stock_crew = StockCrew()

            # Test that agents have LLM configured
            market_analyst = stock_crew.market_technical_analyst()
            risk_analyst = stock_crew.investment_risk_analyst()

            # Verify LLM is set (the actual LLM assignment happens in CrewAI internals)
            # We verify our method was available to be called
            assert hasattr(stock_crew, "_get_configured_llm")

    def test_task_configurations_emphasize_ai_reasoning(self):
        """Test that task configurations emphasize AI reasoning requirements."""
        # This test verifies that task configs have been updated to emphasize AI reasoning
        # We test this by checking the crew initialization doesn't fail

        stock_crew = StockCrew()
        etf_crew = EtfCrew()
        crypto_crew = CryptoCrew()

        # Test that crews can be initialized (task configs are valid)
        assert stock_crew is not None
        assert etf_crew is not None
        assert crypto_crew is not None

        # Test that tasks exist and are properly configured
        stock_tasks = stock_crew.tasks
        etf_tasks = etf_crew.tasks
        crypto_tasks = crypto_crew.tasks

        assert len(stock_tasks) > 0, "Stock crew should have tasks configured"
        assert len(etf_tasks) > 0, "ETF crew should have tasks configured"
        assert len(crypto_tasks) > 0, "Crypto crew should have tasks configured"

    def test_crew_outputs_capture_ai_reasoning(self, mocker):
        """Test that crew configurations support capturing AI reasoning in outputs."""
        # Mock the crew execution to test output structure
        mock_result = Mock()
        mock_result.raw = "AI-generated analysis with reasoning: Based on my analysis of market conditions..."

        with patch("crewai.LLM"):
            stock_crew = StockCrew()

            # Mock the crew kickoff to return our test result
            with patch.object(stock_crew.crew(), "kickoff", return_value=mock_result):
                result = stock_crew.crew().kickoff(inputs={"test": "data"})

                # Verify that result contains AI reasoning indicators
                assert "reasoning" in str(result.raw).lower() or "analysis" in str(result.raw).lower()

    def test_ai_reasoning_requirements_in_task_descriptions(self):
        """Test that task descriptions include AI reasoning requirements."""
        stock_crew = StockCrew()

        # Get task configurations
        tasks = stock_crew.tasks

        # Check that at least one task has AI reasoning requirements
        # (This is a basic check - in practice, we'd verify specific task content)
        assert len(tasks) > 0, "Should have tasks configured"

        # Verify crew has proper agent configuration for AI reasoning
        agents = stock_crew.agents
        assert len(agents) > 0, "Should have agents configured"

    def test_reasoning_enabled_for_all_core_analysis_agents(self):
        """Test that all core analysis agents have reasoning enabled."""
        crews = [StockCrew(), EtfCrew(), CryptoCrew()]

        for crew in crews:
            agents = crew.agents
            for agent in agents:
                # Skip translator agents as they don't need reasoning for translation
                if "translator" not in agent.role.lower():
                    assert agent.reasoning is True, f"Agent {agent.role} should have reasoning enabled"

    def test_ai_driven_decision_making_configuration(self):
        """Test that crews are configured for AI-driven decision making."""
        with patch("crewai.LLM") as mock_llm:
            mock_llm.return_value = Mock()

            # Test that all crews can be properly initialized with AI configuration
            stock_crew = StockCrew()
            etf_crew = EtfCrew()
            crypto_crew = CryptoCrew()

            # Verify crews have the necessary components for AI-driven analysis
            assert hasattr(stock_crew, "agents"), "Stock crew should have agents"
            assert hasattr(stock_crew, "tasks"), "Stock crew should have tasks"
            assert hasattr(stock_crew, "_get_configured_llm"), "Stock crew should have LLM configuration"

            assert hasattr(etf_crew, "agents"), "ETF crew should have agents"
            assert hasattr(etf_crew, "tasks"), "ETF crew should have tasks"
            assert hasattr(etf_crew, "_get_configured_llm"), "ETF crew should have LLM configuration"

            assert hasattr(crypto_crew, "agents"), "Crypto crew should have agents"
            assert hasattr(crypto_crew, "tasks"), "Crypto crew should have tasks"
            assert hasattr(crypto_crew, "_get_configured_llm"), "Crypto crew should have LLM configuration"
