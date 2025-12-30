"""
Unit tests for crew integration in HybridAnalysisFlow.

Tests the crew selection, execution, and output conversion methods.
"""

import pytest

from finwiz.flows.hybrid_analysis_flow import HybridAnalysisFlow
from finwiz.validation.ai_output_validator import AIOutputError


class TestCrewSelection:
    """Test crew selection based on asset class."""

    def test_get_stock_crew(self, mocker):
        """Test that StockCrew is returned for stock asset class."""
        # Arrange
        flow = HybridAnalysisFlow()
        mock_stock_crew = mocker.Mock()
        # Patch where the crew is imported (inside the method)
        mocker.patch("finwiz.crews.stock_crew.stock_crew.StockCrew", return_value=mock_stock_crew)

        # Act
        crew = flow._get_analysis_crew("stock")

        # Assert
        assert crew is not None
        assert crew == mock_stock_crew

    def test_get_etf_crew(self, mocker):
        """Test that EtfCrew is returned for etf asset class."""
        # Arrange
        flow = HybridAnalysisFlow()
        mock_etf_crew = mocker.Mock()
        # Patch where the crew is imported (inside the method)
        mocker.patch("finwiz.crews.etf_crew.etf_crew.EtfCrew", return_value=mock_etf_crew)

        # Act
        crew = flow._get_analysis_crew("etf")

        # Assert
        assert crew is not None
        assert crew == mock_etf_crew

    def test_get_crypto_crew(self, mocker):
        """Test that CryptoCrew is returned for crypto asset class."""
        # Arrange
        flow = HybridAnalysisFlow()
        mock_crypto_crew = mocker.Mock()
        # Patch where the crew is imported (inside the method)
        mocker.patch("finwiz.crews.crypto_crew.crypto_crew.CryptoCrew", return_value=mock_crypto_crew)

        # Act
        crew = flow._get_analysis_crew("crypto")

        # Assert
        assert crew is not None
        assert crew == mock_crypto_crew

    def test_invalid_asset_class_raises_error(self):
        """Test that invalid asset class raises ValueError."""
        # Arrange
        flow = HybridAnalysisFlow()

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported asset class"):
            flow._get_analysis_crew("invalid")

    def test_case_insensitive_asset_class(self, mocker):
        """Test that asset class matching is case-insensitive."""
        # Arrange
        flow = HybridAnalysisFlow()
        mock_stock_crew = mocker.Mock()
        # Patch where the crew is imported (inside the method)
        mocker.patch("finwiz.crews.stock_crew.stock_crew.StockCrew", return_value=mock_stock_crew)

        # Act
        crew_upper = flow._get_analysis_crew("STOCK")
        crew_mixed = flow._get_analysis_crew("Stock")

        # Assert
        assert crew_upper == mock_stock_crew
        assert crew_mixed == mock_stock_crew


class TestRawOutputExtraction:
    """Test extraction of raw output from crew results."""

    def test_extract_from_raw_attribute(self, mocker):
        """Test extraction when crew result has .raw attribute."""
        # Arrange
        flow = HybridAnalysisFlow()
        mock_result = mocker.Mock()
        mock_result.raw = {"test": "data"}

        # Act
        output = flow._extract_raw_output(mock_result)

        # Assert
        assert output == {"test": "data"}

    def test_extract_from_output_attribute(self, mocker):
        """Test extraction when crew result has .output attribute."""
        # Arrange
        flow = HybridAnalysisFlow()
        mock_result = mocker.Mock(spec=["output"])
        mock_result.output = {"test": "data"}
        del mock_result.raw  # Ensure .raw doesn't exist

        # Act
        output = flow._extract_raw_output(mock_result)

        # Assert
        assert output == {"test": "data"}

    def test_extract_from_dict(self):
        """Test extraction when crew result is already a dict."""
        # Arrange
        flow = HybridAnalysisFlow()
        mock_result = {"test": "data"}

        # Act
        output = flow._extract_raw_output(mock_result)

        # Assert
        assert output == {"test": "data"}

    def test_extract_from_pydantic_model(self, mocker):
        """Test extraction when crew result is a Pydantic model."""
        # Arrange
        flow = HybridAnalysisFlow()
        mock_result = mocker.Mock()
        mock_result.model_dump = mocker.Mock(return_value={"test": "data"})
        # Remove other attributes
        del mock_result.raw
        del mock_result.output

        # Act
        output = flow._extract_raw_output(mock_result)

        # Assert
        assert output == {"test": "data"}
        mock_result.model_dump.assert_called_once()

    def test_extract_from_invalid_type_raises_error(self):
        """Test that invalid crew result type raises AIOutputError."""
        # Arrange
        flow = HybridAnalysisFlow()
        mock_result = "invalid string result"

        # Act & Assert
        with pytest.raises(AIOutputError, match="Raw output extraction failed"):
            flow._extract_raw_output(mock_result)


class TestCrewExecution:
    """Test crew execution with mocked crews."""

    def test_execute_crew_calls_kickoff(self, mocker):
        """Test that _execute_crew calls crew.kickoff with inputs."""
        # Arrange
        flow = HybridAnalysisFlow()
        mock_crew_instance = mocker.Mock()
        mock_crew_obj = mocker.Mock()
        mock_crew_obj.kickoff = mocker.Mock(return_value={"result": "data"})
        mock_crew_instance.crew = mocker.Mock(return_value=mock_crew_obj)

        flow._get_analysis_crew = mocker.Mock(return_value=mock_crew_instance)

        inputs = {"ticker": "AAPL", "asset_class": "stock"}

        # Act
        result = flow._execute_crew("stock", inputs)

        # Assert
        flow._get_analysis_crew.assert_called_once_with("stock")
        mock_crew_instance.crew.assert_called_once()
        mock_crew_obj.kickoff.assert_called_once_with(inputs=inputs)
        assert result == {"result": "data"}

    def test_execute_crew_propagates_errors(self, mocker):
        """Test that crew execution errors are propagated."""
        # Arrange
        flow = HybridAnalysisFlow()
        mock_crew_instance = mocker.Mock()
        mock_crew_obj = mocker.Mock()
        mock_crew_obj.kickoff = mocker.Mock(side_effect=Exception("Crew failed"))
        mock_crew_instance.crew = mocker.Mock(return_value=mock_crew_obj)

        flow._get_analysis_crew = mocker.Mock(return_value=mock_crew_instance)

        inputs = {"ticker": "AAPL", "asset_class": "stock"}

        # Act & Assert
        with pytest.raises(Exception, match="Crew failed"):
            flow._execute_crew("stock", inputs)
