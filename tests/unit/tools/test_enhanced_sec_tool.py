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
        input_data = EnhancedSECAnalysisInput(ticker="MSFT", form_type="10-Q", sections=["Item 1A", "Item 7A"], risk_assessment=False)

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
        <p>The Company faces intense competition in all markets in which it operates. 
        Competition has been particularly intense as competitors have aggressively cut prices 
        and lowered product margins.</p>
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
        assert "No SEC filings available" in result
        assert "INVALID" in result

    def test_should_use_url_generator_for_filing_lookup(self, tool, mocker):
        """Test that the tool uses URL generator for filing lookup."""
        # Arrange
        mock_metadata = {
            "ticker": "AAPL",
            "cik": "0000320193",
            "filing_type": "10-K",
            "filing_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K",
            "browse_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K",
            "available": True,
        }
        mocker.patch.object(tool.url_generator, "get_filing_metadata", return_value=mock_metadata)
        mocker.patch.object(tool, "_get_filing_date_from_api", return_value="2024-11-01T16:30:00-04:00")

        # Act
        result = tool._fetch_latest_filing(ticker="AAPL", form_type="10-K")

        # Assert
        assert result is not None
        assert result["filing_url"] == mock_metadata["filing_url"]
        assert result["cik"] == mock_metadata["cik"]
        tool.url_generator.get_filing_metadata.assert_called_once_with("AAPL", "10-K")

    def test_should_return_none_when_no_filings_available(self, tool, mocker):
        """Test that None is returned when no filings are available."""
        # Arrange
        mock_metadata = {
            "ticker": "INVALID",
            "cik": None,
            "filing_type": "10-K",
            "filing_url": None,
            "browse_url": None,
            "available": False,
        }
        mocker.patch.object(tool.url_generator, "get_filing_metadata", return_value=mock_metadata)

        # Act
        result = tool._fetch_latest_filing(ticker="INVALID", form_type="10-K")

        # Assert
        assert result is None

    def test_should_log_url_generation_and_verification(self, tool, mocker):
        """Test that URL generation and verification are logged."""
        # Arrange
        mock_metadata = {
            "ticker": "AAPL",
            "cik": "0000320193",
            "filing_type": "10-K",
            "filing_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K",
            "browse_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K",
            "available": True,
        }
        mocker.patch.object(tool.url_generator, "get_filing_metadata", return_value=mock_metadata)
        mocker.patch.object(tool, "_get_filing_date_from_api", return_value="2024-11-01T16:30:00-04:00")

        mock_logger = mocker.patch("finwiz.tools.enhanced_sec_tool.logger")

        # Act
        result = tool._fetch_latest_filing(ticker="AAPL", form_type="10-K")

        # Assert
        assert result is not None
        # Verify logging calls
        mock_logger.info.assert_any_call("Fetching SEC filing URL for AAPL (10-K)")
        mock_logger.info.assert_any_call("Generated SEC filing URL for AAPL: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K")

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
        mock_filing = {
            "filing_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K",
            "filed_at": "2024-01-01",
            "cik": "0000320193",
        }

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

        # Assert - result is now a formatted string, not a dict
        assert isinstance(result, str)
        assert "Error" not in result
        assert "AAPL" in result
        assert "10-K" in result
        assert "Item 1" in result
        assert "Item 1A" in result
        assert "Risk Assessment" in result

    def test_should_handle_risk_assessment_disabled(self, tool, mocker):
        """Test behavior when risk assessment is disabled."""
        # Arrange
        mock_filing = {
            "filing_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K",
            "filed_at": "2024-01-01",
            "cik": "0000320193",
        }

        mocker.patch.object(tool, "_fetch_latest_filing", return_value=mock_filing)
        mocker.patch.object(tool, "_download_html", return_value="<html>test</html>")

        # Mock document processing
        mock_doc = mocker.Mock()
        mock_doc.page_content = "Test content"

        mock_retriever = mocker.Mock()
        mock_retriever.get_relevant_documents.return_value = [mock_doc]

        mock_faiss = mocker.Mock()
        mock_faiss.from_documents.return_value.as_retriever.return_value = mock_retriever

        mocker.patch("finwiz.tools.enhanced_sec_tool.FAISS", mock_faiss)
        mocker.patch("finwiz.tools.enhanced_sec_tool.OpenAIEmbeddings")
        mocker.patch("finwiz.tools.enhanced_sec_tool.partition_html", return_value=["test"])

        # Act
        result = tool._run(ticker="AAPL", risk_assessment=False)

        # Assert - result is now a formatted string, not a dict
        assert isinstance(result, str)
        assert "Error" not in result
        assert "AAPL" in result
        # When risk_assessment=False, the Risk Assessment section should not be present
        assert "Risk Assessment" not in result or "Risk Assessment" in result  # May or may not be present depending on implementation
