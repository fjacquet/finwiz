"""
Unit tests for Enhanced SEC Analysis Tool.

Tests the enhanced SEC filing analysis capabilities including
10-K insights extraction, standardized risk scoring, and proper
citation formatting.
"""

import pytest

from finwiz.tools.enhanced_sec_tool import (
    EnhancedSECAnalysisInput,
    EnhancedSECAnalysisTool,
    StandardizedRiskScoringTool,
)


class TestEnhancedSECAnalysisInput:
    """Test the input schema for Enhanced SEC Analysis Tool."""

    def test_should_create_valid_input_with_defaults(self):
        """Test creating input with default values."""
        # Arrange & Act
        input_data = EnhancedSECAnalysisInput(ticker="AAPL")

        # Assert
        assert input_data.ticker == "AAPL"
        assert input_data.form_type == "10-K"
        assert input_data.sections == ["Item 1", "Item 1A", "Item 7"]
        assert input_data.risk_assessment is True

    def test_should_create_valid_input_with_custom_values(self):
        """Test creating input with custom values."""
        # Arrange & Act
        input_data = EnhancedSECAnalysisInput(
            ticker="MSFT", form_type="10-Q", sections=["Item 1A", "Item 7A"], risk_assessment=False
        )

        # Assert
        assert input_data.ticker == "MSFT"
        assert input_data.form_type == "10-Q"
        assert input_data.sections == ["Item 1A", "Item 7A"]
        assert input_data.risk_assessment is False


class TestEnhancedSECAnalysisTool:
    """Test the Enhanced SEC Analysis Tool functionality."""

    @pytest.fixture
    def tool(self):
        """Create an instance of the Enhanced SEC Analysis Tool."""
        return EnhancedSECAnalysisTool()

    @pytest.fixture
    def mock_filing_data(self):
        """Mock SEC filing data for testing."""
        return {
            "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000007/aapl-20240930.htm",
            "filed_at": "2024-11-01T16:30:00-04:00",
        }

    @pytest.fixture
    def mock_html_content(self):
        """Mock HTML content from SEC filing."""
        return """
        <html>
        <body>
        <div>Item 1. Business</div>
        <p>Apple Inc. designs, manufactures and markets smartphones, personal computers, tablets, wearables and accessories.</p>
        <div>Item 1A. Risk Factors</div>
        <p>The Company faces intense competition in all markets in which it operates. Competition has been particularly intense as competitors have aggressively cut prices and lowered product margins.</p>
        <div>Item 7. Management's Discussion and Analysis</div>
        <p>Net sales increased during 2024 compared to 2023 due to higher net sales of iPhone, Services and Mac.</p>
        </body>
        </html>
        """

    def test_should_return_error_when_no_filing_found(self, tool, mocker):
        """Test error handling when no SEC filing is found."""
        # Arrange
        mocker.patch.object(tool, "_fetch_latest_filing", return_value=None)

        # Act
        result = tool._run(ticker="INVALID", form_type="10-K")

        # Assert
        assert "error" in result
        assert "No 10-K filing found for ticker INVALID" in result["error"]
        assert result["ticker"] == "INVALID"
        assert result["form_type"] == "10-K"

    def test_should_return_error_when_missing_api_key(self, tool, mocker):
        """Test error handling when SEC API key is missing."""
        # Arrange
        mocker.patch.dict("os.environ", {}, clear=True)

        # Act
        result = tool._run(ticker="AAPL", form_type="10-K")

        # Assert
        assert "error" in result
        assert "Missing environment/config" in result["error"]

    def test_should_extract_insights_successfully(self, tool, mocker, mock_filing_data, mock_html_content):
        """Test successful insights extraction from SEC filing."""
        # Arrange
        mock_get = mocker.patch("finwiz.tools.enhanced_sec_tool.requests.get")
        mock_get.return_value.text = mock_html_content
        mock_get.return_value.raise_for_status = mocker.Mock()

        mocker.patch.object(tool, "_fetch_latest_filing", return_value=mock_filing_data)

        # Mock FAISS and OpenAI embeddings
        mock_retriever = mocker.Mock()
        mock_doc = mocker.Mock()
        mock_doc.page_content = (
            "Apple Inc. designs, manufactures and markets smartphones, personal computers, tablets, wearables and accessories."
        )
        mock_retriever.get_relevant_documents.return_value = [mock_doc]

        mock_faiss = mocker.Mock()
        mock_faiss.from_documents.return_value.as_retriever.return_value = mock_retriever

        mocker.patch("finwiz.tools.enhanced_sec_tool.FAISS", mock_faiss)
        mocker.patch("finwiz.tools.enhanced_sec_tool.OpenAIEmbeddings")
        mocker.patch("finwiz.tools.enhanced_sec_tool.partition_html", return_value=[mock_html_content])

        # Act
        result = tool._run(ticker="AAPL", form_type="10-K", sections=["Item 1"])

        # Assert
        assert "error" not in result
        assert result["ticker"] == "AAPL"
        assert result["form_type"] == "10-K"
        assert result["filing_url"] == mock_filing_data["filing_url"]
        assert "insights" in result
        assert len(result["insights"]) > 0
        assert "risk_assessment" in result

    def test_should_identify_risk_factors_correctly(self, tool):
        """Test risk factor identification from content."""
        # Arrange
        risk_content = [
            "The Company faces intense competition in all markets. Regulatory changes may impact operations. ",
            "Cybersecurity threats are increasing.",
            "Credit risk from customer defaults. Supply chain disruptions may occur. Litigation risks exist.",
        ]

        # Act
        risk_factors = tool._identify_risk_factors(risk_content)

        # Assert
        assert len(risk_factors) > 0
        assert any("competition" in factor.lower() for factor in risk_factors)
        assert any("regulatory" in factor.lower() for factor in risk_factors)
        assert any("cybersecurity" in factor.lower() for factor in risk_factors)

    def test_should_calculate_risk_score_correctly(self, tool):
        """Test risk score calculation based on risk factors."""
        # Arrange
        low_risk_factors = ["Market volatility risk", "Competitive risk"]
        high_risk_factors = [
            "Cybersecurity risk",
            "Litigation risk",
            "Regulatory risk",
            "Credit risk",
            "Operational risk",
        ]

        # Act
        low_score = tool._calculate_risk_score(low_risk_factors)
        high_score = tool._calculate_risk_score(high_risk_factors)

        # Assert
        assert 0.0 <= low_score <= 5.0
        assert 0.0 <= high_score <= 5.0
        assert high_score > low_score

    def test_should_map_score_to_level_correctly(self, tool):
        """Test mapping of numerical scores to risk levels."""
        # Arrange & Act & Assert
        assert tool._map_score_to_level(1.0) == "Low"
        assert tool._map_score_to_level(2.0) == "Medium"
        assert tool._map_score_to_level(3.5) == "High"
        assert tool._map_score_to_level(4.5) == "Very High"

    def test_should_perform_comprehensive_risk_assessment(self, tool, mock_filing_data):
        """Test comprehensive risk assessment functionality."""
        # Arrange
        insights = [
            {
                "ticker": "AAPL",
                "section": "Item 1A",
                "excerpt": "Competition risk, regulatory risk, cybersecurity threats, credit risk from customers",
            },
            {
                "ticker": "AAPL",
                "section": "Item 1",
                "excerpt": "Business operations and competitive advantages",
            },
        ]

        # Act
        risk_assessment = tool._perform_risk_assessment(insights, "AAPL", mock_filing_data)

        # Assert
        assert risk_assessment["ticker"] == "AAPL"
        assert risk_assessment["scale"] == "0_5"
        assert 0.0 <= risk_assessment["score"] <= 5.0
        assert risk_assessment["level"] in ["Low", "Medium", "High", "Very High"]
        assert len(risk_assessment["risk_factors"]) <= 10
        assert risk_assessment["filing_source"] == mock_filing_data["filing_url"]


class TestStandardizedRiskScoringTool:
    """Test the Standardized Risk Scoring Tool."""

    @pytest.fixture
    def tool(self):
        """Create an instance of the Standardized Risk Scoring Tool."""
        return StandardizedRiskScoringTool()

    def test_should_return_methodology_information(self, tool):
        """Test that the tool returns methodology information."""
        # Act
        result = tool._run(symbol="AAPL", asset_class="stock")

        # Assert
        assert result["tool"] == "StandardizedRiskScoringTool"
        assert result["symbol"] == "AAPL"
        assert result["asset_class"] == "stock"
        assert "methodology" in result
        assert "0-5 scale" in result["methodology"]


class TestIntegrationScenarios:
    """Test integration scenarios for enhanced SEC analysis."""

    @pytest.fixture
    def tool(self):
        """Create tool instance for integration tests."""
        return EnhancedSECAnalysisTool()

    def test_should_handle_multiple_sections_analysis(self, tool, mocker):
        """Test analysis of multiple SEC sections."""
        # Arrange
        mock_filing = {"filing_url": "https://sec.gov/test", "filed_at": "2024-01-01"}

        mocker.patch.object(tool, "_fetch_latest_filing", return_value=mock_filing)
        mocker.patch.object(tool, "_download_html", return_value="<html>test content</html>")

        # Mock document processing
        mock_doc = mocker.Mock()
        mock_doc.page_content = "Test content for section analysis"

        mock_retriever = mocker.Mock()
        mock_retriever.get_relevant_documents.return_value = [mock_doc]

        mock_faiss = mocker.Mock()
        mock_faiss.from_documents.return_value.as_retriever.return_value = mock_retriever

        mocker.patch("finwiz.tools.enhanced_sec_tool.FAISS", mock_faiss)
        mocker.patch("finwiz.tools.enhanced_sec_tool.OpenAIEmbeddings")
        mocker.patch("finwiz.tools.enhanced_sec_tool.partition_html", return_value=["test"])

        # Act
        result = tool._run(ticker="AAPL", sections=["Item 1", "Item 1A", "Item 7"], risk_assessment=True)

        # Assert
        assert "error" not in result
        assert result["sections_analyzed"] == ["Item 1", "Item 1A", "Item 7"]
        assert "insights" in result
        assert "risk_assessment" in result

    def test_should_handle_risk_assessment_disabled(self, tool, mocker):
        """Test behavior when risk assessment is disabled."""
        # Arrange
        mock_filing = {"filing_url": "https://sec.gov/test", "filed_at": "2024-01-01"}

        mocker.patch.object(tool, "_fetch_latest_filing", return_value=mock_filing)
        mocker.patch.object(tool, "_download_html", return_value="<html>test</html>")
        mocker.patch.object(tool, "_extract_section_insights", return_value=[])

        # Act
        result = tool._run(ticker="AAPL", risk_assessment=False)

        # Assert
        assert "error" not in result
        assert result["risk_assessment"] is None
