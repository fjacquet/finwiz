"""
Unit tests for tool factory module.

Tests verify that factory functions return correct tool sets with proper
configuration based on optional parameters.
"""

from crewai.tools import BaseTool

from finwiz.tools.tool_factories import (
    get_crypto_crew_tools,
    get_etf_crew_tools,
    get_stock_crew_tools,
)


class TestStockCrewToolFactory:
    """Tests for stock crew tool factory."""

    def test_should_return_list_of_base_tools_when_called(self, mocker):
        """Test that factory returns list of BaseTool instances."""
        # Arrange
        mock_stock_tools = mocker.patch("finwiz.tools.tool_factories.get_stock_research_tools")
        mock_stock_tools.return_value = [mocker.Mock(spec=BaseTool)]

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = [mocker.Mock(spec=BaseTool)]

        # Act
        tools = get_stock_crew_tools()

        # Assert
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert all(isinstance(t, BaseTool) for t in tools)

    def test_should_include_quantitative_tool_when_flag_is_true(self, mocker):
        """Test that quantitative tool is included when flag is True."""
        # Arrange
        mock_stock_tools = mocker.patch("finwiz.tools.tool_factories.get_stock_research_tools")
        mock_stock_tools.return_value = []

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = []

        # Act
        tools = get_stock_crew_tools(include_quantitative=True)

        # Assert
        mock_quant_tool.assert_called_once()

    def test_should_exclude_quantitative_tool_when_flag_is_false(self, mocker):
        """Test that quantitative tool is excluded when flag is False."""
        # Arrange
        mock_stock_tools = mocker.patch("finwiz.tools.tool_factories.get_stock_research_tools")
        mock_stock_tools.return_value = []

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = []

        # Act
        tools = get_stock_crew_tools(include_quantitative=False)

        # Assert
        mock_quant_tool.assert_not_called()

    def test_should_include_rag_tools_when_flag_is_true(self, mocker):
        """Test that RAG tools are included when flag is True."""
        # Arrange
        mock_stock_tools = mocker.patch("finwiz.tools.tool_factories.get_stock_research_tools")
        mock_stock_tools.return_value = []

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = [mocker.Mock(spec=BaseTool)]

        # Act
        tools = get_stock_crew_tools(include_rag=True)

        # Assert
        mock_rag_tools.assert_called_once_with(collection_suffix="stock")

    def test_should_exclude_rag_tools_when_flag_is_false(self, mocker):
        """Test that RAG tools are excluded when flag is False."""
        # Arrange
        mock_stock_tools = mocker.patch("finwiz.tools.tool_factories.get_stock_research_tools")
        mock_stock_tools.return_value = []

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = []

        # Act
        tools = get_stock_crew_tools(include_rag=False)

        # Assert
        mock_rag_tools.assert_not_called()

    def test_should_pass_collection_suffix_to_rag_tools(self, mocker):
        """Test that collection_suffix parameter is passed to RAG tools."""
        # Arrange
        mock_stock_tools = mocker.patch("finwiz.tools.tool_factories.get_stock_research_tools")
        mock_stock_tools.return_value = []

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = []

        # Act
        tools = get_stock_crew_tools(collection_suffix="custom_stock")

        # Assert
        mock_rag_tools.assert_called_once_with(collection_suffix="custom_stock")


class TestCryptoCrewToolFactory:
    """Tests for crypto crew tool factory."""

    def test_should_return_list_of_base_tools_when_called(self, mocker):
        """Test that factory returns list of BaseTool instances."""
        # Arrange
        mock_crypto_tools = mocker.patch("finwiz.tools.tool_factories.get_crypto_research_tools")
        mock_crypto_tools.return_value = [mocker.Mock(spec=BaseTool)]

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = [mocker.Mock(spec=BaseTool)]

        # Act
        tools = get_crypto_crew_tools()

        # Assert
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert all(isinstance(t, BaseTool) for t in tools)

    def test_should_include_quantitative_tool_when_flag_is_true(self, mocker):
        """Test that quantitative tool is included when flag is True."""
        # Arrange
        mock_crypto_tools = mocker.patch("finwiz.tools.tool_factories.get_crypto_research_tools")
        mock_crypto_tools.return_value = []

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = []

        # Act
        tools = get_crypto_crew_tools(include_quantitative=True)

        # Assert
        mock_quant_tool.assert_called_once()

    def test_should_exclude_quantitative_tool_when_flag_is_false(self, mocker):
        """Test that quantitative tool is excluded when flag is False."""
        # Arrange
        mock_crypto_tools = mocker.patch("finwiz.tools.tool_factories.get_crypto_research_tools")
        mock_crypto_tools.return_value = []

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = []

        # Act
        tools = get_crypto_crew_tools(include_quantitative=False)

        # Assert
        mock_quant_tool.assert_not_called()

    def test_should_pass_collection_suffix_to_rag_tools(self, mocker):
        """Test that collection_suffix parameter is passed to RAG tools."""
        # Arrange
        mock_crypto_tools = mocker.patch("finwiz.tools.tool_factories.get_crypto_research_tools")
        mock_crypto_tools.return_value = []

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = []

        # Act
        tools = get_crypto_crew_tools(collection_suffix="custom_crypto")

        # Assert
        mock_rag_tools.assert_called_once_with(collection_suffix="custom_crypto")


class TestETFCrewToolFactory:
    """Tests for ETF crew tool factory."""

    def test_should_return_list_of_base_tools_when_called(self, mocker):
        """Test that factory returns list of BaseTool instances."""
        # Arrange
        mock_etf_tools = mocker.patch("finwiz.tools.tool_factories.get_etf_research_tools")
        mock_etf_tools.return_value = [mocker.Mock(spec=BaseTool)]

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = [mocker.Mock(spec=BaseTool)]

        # Act
        tools = get_etf_crew_tools()

        # Assert
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert all(isinstance(t, BaseTool) for t in tools)

    def test_should_include_quantitative_tool_when_flag_is_true(self, mocker):
        """Test that quantitative tool is included when flag is True."""
        # Arrange
        mock_etf_tools = mocker.patch("finwiz.tools.tool_factories.get_etf_research_tools")
        mock_etf_tools.return_value = []

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = []

        # Act
        tools = get_etf_crew_tools(include_quantitative=True)

        # Assert
        mock_quant_tool.assert_called_once()

    def test_should_exclude_quantitative_tool_when_flag_is_false(self, mocker):
        """Test that quantitative tool is excluded when flag is False."""
        # Arrange
        mock_etf_tools = mocker.patch("finwiz.tools.tool_factories.get_etf_research_tools")
        mock_etf_tools.return_value = []

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = []

        # Act
        tools = get_etf_crew_tools(include_quantitative=False)

        # Assert
        mock_quant_tool.assert_not_called()

    def test_should_pass_collection_suffix_to_rag_tools(self, mocker):
        """Test that collection_suffix parameter is passed to RAG tools."""
        # Arrange
        mock_etf_tools = mocker.patch("finwiz.tools.tool_factories.get_etf_research_tools")
        mock_etf_tools.return_value = []

        mock_quant_tool = mocker.patch("finwiz.tools.tool_factories.get_quantitative_analysis_tool")
        mock_quant_tool.return_value = mocker.Mock(spec=BaseTool)

        mock_rag_tools = mocker.patch("finwiz.tools.tool_factories.get_rag_tools")
        mock_rag_tools.return_value = []

        # Act
        tools = get_etf_crew_tools(collection_suffix="custom_etf")

        # Assert
        mock_rag_tools.assert_called_once_with(collection_suffix="custom_etf")
