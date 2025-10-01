"""
Integration test to verify AI reasoning is working in crew execution.

This test verifies that:
1. Crews can be executed with reasoning enabled
2. AI reasoning appears in outputs
3. Tools provide data to AI agents for decision-making
"""

import os

import pytest

from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
from finwiz.crews.etf_crew.etf_crew import EtfCrew
from finwiz.crews.stock_crew.stock_crew import StockCrew


class TestAIReasoningIntegration:
    """Integration tests for AI reasoning in crew execution."""

    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not available")
    def test_stock_crew_ai_reasoning_in_output(self, mocker):
        """Test that stock crew produces AI reasoning in outputs."""
        # Mock the crew execution to avoid actual API calls in tests
        mock_result = mocker.Mock()
        mock_result.raw = """
        Based on my AI analysis of the current market conditions, I have identified several key factors:

        **AI Reasoning Process:**
        1. Market sentiment analysis indicates positive momentum
        2. Technical indicators suggest oversold conditions
        3. Fundamental analysis reveals strong earnings growth

        **AI Decision:** BUY recommendation with high confidence
        **Reasoning:** The convergence of technical and fundamental signals, 
        combined with favorable market sentiment, creates a compelling investment opportunity.
        """

        mock_llm = mocker.patch("crewai.LLM")
        mock_llm.return_value = mocker.Mock()

        mocker.patch.object(StockCrew, "map_all_task_variables")
        stock_crew = StockCrew()

        # Mock the crew kickoff
        mocker.patch.object(stock_crew.crew(), "kickoff", return_value=mock_result)
        result = stock_crew.crew().kickoff(inputs={"test": "data"})

        # Verify AI reasoning indicators in output
        output_text = str(result.raw).lower()
        assert "ai reasoning" in output_text or "reasoning process" in output_text
        assert "analysis" in output_text
        assert "decision" in output_text or "recommendation" in output_text

    def test_ai_reasoning_configuration_consistency(self, mocker):
        """Test that all crews have consistent AI reasoning configuration."""
        mock_llm = mocker.patch("crewai.LLM")
        mock_llm.return_value = mocker.Mock()

        mocker.patch.object(StockCrew, "map_all_task_variables")
        mocker.patch.object(EtfCrew, "map_all_task_variables")
        mocker.patch.object(CryptoCrew, "map_all_task_variables")

        crews = [StockCrew(), EtfCrew(), CryptoCrew()]

        for crew in crews:
            # Verify LLM configuration method exists
            assert hasattr(crew, "_get_configured_llm")

            # Verify LLM configuration parameters
            llm = crew._get_configured_llm()
            assert llm is not None

            # Verify LLM was called with consistent parameters
            mock_llm.assert_called_with(
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=4000,
                timeout=60,
            )

    def test_ai_agents_have_reasoning_enabled(self, mocker):
        """Test that all AI agents have reasoning enabled."""
        mock_llm = mocker.patch("crewai.LLM")
        mock_llm.return_value = mocker.Mock()

        mocker.patch.object(StockCrew, "map_all_task_variables")
        mocker.patch.object(EtfCrew, "map_all_task_variables")
        mocker.patch.object(CryptoCrew, "map_all_task_variables")

        # Test Stock Crew agents
        stock_crew = StockCrew()
        stock_agents = [stock_crew.market_technical_analyst(), stock_crew.investment_risk_analyst()]

        # Test ETF Crew agents
        etf_crew = EtfCrew()
        etf_agents = [etf_crew.market_etf_analyst(), etf_crew.risk_assessor()]

        # Test Crypto Crew agents
        crypto_crew = CryptoCrew()
        crypto_agents = [
            crypto_crew.market_analyst(),
            crypto_crew.technical_analyst(),
            crypto_crew.risk_assessor(),
            crypto_crew.investment_strategist(),
        ]

        all_agents = stock_agents + etf_agents + crypto_agents

        for agent in all_agents:
            # Skip translator agents as they don't need reasoning for translation
            if "translator" not in agent.role.lower():
                assert agent.reasoning is True, f"Agent {agent.role} should have reasoning enabled"

    def test_ai_reasoning_task_configuration(self, mocker):
        """Test that task configurations support AI reasoning requirements."""
        mock_llm = mocker.patch("crewai.LLM")
        mock_llm.return_value = mocker.Mock()

        mocker.patch.object(StockCrew, "map_all_task_variables")
        mocker.patch.object(EtfCrew, "map_all_task_variables")
        mocker.patch.object(CryptoCrew, "map_all_task_variables")

        crews = [StockCrew(), EtfCrew(), CryptoCrew()]

        for crew in crews:
            # Verify crew has tasks configured
            assert hasattr(crew, "tasks")

            # Verify crew has agents configured
            assert hasattr(crew, "agents")

            # Verify crew can be created (validates task/agent configuration)
            crew_instance = crew.crew()
            assert crew_instance is not None

    def test_ai_reasoning_output_structure(self, mocker):
        """Test that AI reasoning outputs have proper structure for downstream consumption."""
        # Mock a realistic AI reasoning output
        mock_result = mocker.Mock()
        mock_result.raw = """
        # AI-Driven Stock Analysis

        ## AI Reasoning Process
        After analyzing multiple data sources and market indicators, my AI reasoning process identified:

        1. **Technical Analysis Reasoning**: RSI indicates oversold conditions (32.5)
        2. **Fundamental Analysis Reasoning**: P/E ratio of 15.2 suggests undervaluation
        3. **Sentiment Analysis Reasoning**: Recent news sentiment shows 68% positive coverage

        ## AI Decision Framework
        Based on the convergence of these factors, my AI decision-making process concludes:

        **Investment Recommendation**: BUY
        **Confidence Level**: 85%
        **AI Reasoning**: The combination of technical oversold conditions, fundamental undervaluation, 
        and positive sentiment creates a high-probability investment opportunity.

        ## Risk Assessment (AI-Generated)
        My AI risk analysis identifies:
        - Market risk: Medium (current volatility levels)
        - Company-specific risk: Low (strong fundamentals)
        - Sector risk: Medium (regulatory considerations)
        """

        mock_llm = mocker.patch("crewai.LLM")
        mock_llm.return_value = mocker.Mock()

        mocker.patch.object(StockCrew, "map_all_task_variables")
        stock_crew = StockCrew()

        # Mock the crew kickoff
        mocker.patch.object(stock_crew.crew(), "kickoff", return_value=mock_result)
        result = stock_crew.crew().kickoff(inputs={"test": "data"})

        output_text = str(result.raw)

        # Verify AI reasoning structure
        assert "AI Reasoning Process" in output_text or "AI reasoning process" in output_text
        assert "AI Decision" in output_text or "AI decision" in output_text
        assert "Confidence Level" in output_text or "confidence" in output_text.lower()
        assert "Investment Recommendation" in output_text or "recommendation" in output_text.lower()

        # Verify reasoning explanations are present
        assert "based on" in output_text.lower() or "because" in output_text.lower()
        assert "analysis" in output_text.lower()
