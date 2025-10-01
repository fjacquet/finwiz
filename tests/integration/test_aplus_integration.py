"""
Unit tests for A+ Opportunity Integration into Report Data.

Tests the integration of A+ opportunities into the reporting system
with portfolio allocation updates and availability status tracking.
"""

from datetime import datetime
from pathlib import Path

import pytest

from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.schemas.integration import APlusOpportunityCollection


class TestAPlusIntegration:
    """Test suite for A+ opportunity integration functionality."""

    @pytest.fixture
    def mock_integration_manager(self, mocker):
        """Create a mock integration manager."""
        manager = mocker.Mock(spec=CrewDataIntegrationManager)
        manager.output_dir = Path("output")
        manager.logger = mocker.Mock()
        return manager

    @pytest.fixture
    def data_accessor(self, mock_integration_manager, mocker):
        """Create data accessor with mocked dependencies."""
        mocker.patch("finwiz.integration.data_accessor.APlusDataExtractor")
        accessor = CrewDataAccessor(mock_integration_manager)
        return accessor

    @pytest.fixture
    def sample_aplus_opportunities(self):
        """Create sample A+ opportunities collection."""
        return APlusOpportunityCollection(
            etf_opportunities=["VWCE", "IWDA"],
            stock_opportunities=["NVDA", "AVGO", "ADBE"],
            crypto_opportunities=["BTC", "ETH"],
            discovery_summary=(
                "Analysis identified 7 high-quality investment opportunities with strong fundamentals and growth potential."
            ),
            confidence_score=0.85,
            validation_timestamp=datetime.now(),
            allocation_recommendations=[
                {"asset_type": "stock", "symbol": "NVDA", "allocation": "5-8% for aggressive growth", "grade": "A+", "rank": 1},
                {"asset_type": "etf", "symbol": "VWCE", "allocation": "Core global equity position", "grade": "A+", "rank": 1},
                {"asset_type": "crypto", "symbol": "BTC", "allocation": "2.0% of total portfolio", "grade": "A+", "rank": 1},
            ],
            replacement_notes=[
                "NVDA: Fits growth-maximizing equity sleeve",
                "VWCE: Can replace IWDA+EMIM for simplicity",
                "BTC: Acts as core ballast in crypto allocation",
            ],
        )

    def test_should_get_aplus_opportunities_when_discovery_data_available(self, data_accessor, sample_aplus_opportunities):
        """Test A+ opportunities extraction when discovery data is available."""
        # Arrange
        data_accessor.integration_manager.get_crew_data_with_freshness_check.return_value = {"discovery_data": "mock_data"}
        data_accessor.aplus_extractor.extract_aplus_opportunities.return_value = sample_aplus_opportunities

        # Act
        result = data_accessor.get_aplus_opportunities(max_age_hours=24)

        # Assert
        assert result is not None
        assert result == sample_aplus_opportunities
        assert len(result.stock_opportunities) == 3
        assert len(result.etf_opportunities) == 2
        assert len(result.crypto_opportunities) == 2
        assert result.confidence_score == 0.85

        # Verify integration manager was called correctly
        data_accessor.integration_manager.get_crew_data_with_freshness_check.assert_called_once_with(
            "discovery", 24, warn_on_stale=True
        )

    def test_should_return_none_when_discovery_data_unavailable(self, data_accessor):
        """Test A+ opportunities extraction when discovery data is unavailable."""
        # Arrange
        data_accessor.integration_manager.get_crew_data_with_freshness_check.return_value = None

        # Act
        result = data_accessor.get_aplus_opportunities(max_age_hours=24)

        # Assert
        assert result is None

    def test_should_return_none_when_extraction_fails(self, data_accessor):
        """Test A+ opportunities extraction when extractor fails."""
        # Arrange
        data_accessor.integration_manager.get_crew_data_with_freshness_check.return_value = {"discovery_data": "mock_data"}
        data_accessor.aplus_extractor.extract_aplus_opportunities.return_value = None

        # Act
        result = data_accessor.get_aplus_opportunities(max_age_hours=24)

        # Assert
        assert result is None

    def test_should_handle_extraction_errors_gracefully(self, data_accessor):
        """Test A+ opportunities extraction handles errors gracefully."""
        # Arrange
        data_accessor.integration_manager.get_crew_data_with_freshness_check.return_value = {"discovery_data": "mock_data"}
        data_accessor.aplus_extractor.extract_aplus_opportunities.side_effect = Exception("Extraction error")

        # Act
        result = data_accessor.get_aplus_opportunities(max_age_hours=24)

        # Assert
        assert result is None

    def test_should_generate_consolidated_reporter_input_with_aplus_opportunities(
        self, data_accessor, sample_aplus_opportunities, mocker
    ):
        """Test consolidated reporter input generation with A+ opportunities."""
        # Arrange
        base_consolidated_data = {"stock": {"mock": "stock_data"}, "etf": {"mock": "etf_data"}, "crypto": {"mock": "crypto_data"}}

        data_accessor.get_consolidated_data = mocker.Mock(return_value=base_consolidated_data)
        data_accessor.get_consolidated_market_sentiment = mocker.Mock(return_value={"sentiment": "positive"})
        data_accessor.get_consolidated_ticker_validation = mocker.Mock(return_value={"validation": "passed"})
        data_accessor.get_aplus_opportunities = mocker.Mock(return_value=sample_aplus_opportunities)
        data_accessor.check_data_availability = mocker.Mock(return_value={"status": "complete"})

        # Act
        result = data_accessor.get_consolidated_reporter_input(max_age_hours=24)

        # Assert
        assert result is not None
        assert "aplus_opportunities" in result
        assert "portfolio_allocation_updates" in result
        assert "aplus_availability_status" in result

        # Check A+ opportunities data
        aplus_data = result["aplus_opportunities"]
        assert aplus_data["stock_opportunities"] == ["NVDA", "AVGO", "ADBE"]
        assert aplus_data["etf_opportunities"] == ["VWCE", "IWDA"]
        assert aplus_data["crypto_opportunities"] == ["BTC", "ETH"]
        assert aplus_data["confidence_score"] == 0.85
        assert len(aplus_data["allocation_recommendations"]) == 3
        assert len(aplus_data["replacement_notes"]) == 3

        # Check portfolio allocation updates
        updates = result["portfolio_allocation_updates"]
        assert len(updates) > 0

        # Check availability status
        status = result["aplus_availability_status"]
        assert status["available"] is True
        assert status["total_opportunities"] == 7

    def test_should_generate_consolidated_reporter_input_without_aplus_opportunities(self, data_accessor, mocker):
        """Test consolidated reporter input generation when A+ opportunities are unavailable."""
        # Arrange
        base_consolidated_data = {"stock": {"mock": "stock_data"}, "etf": {"mock": "etf_data"}}

        data_accessor.get_consolidated_data = mocker.Mock(return_value=base_consolidated_data)
        data_accessor.get_consolidated_market_sentiment = mocker.Mock(return_value={"sentiment": "neutral"})
        data_accessor.get_consolidated_ticker_validation = mocker.Mock(return_value={"validation": "passed"})
        data_accessor.get_aplus_opportunities = mocker.Mock(return_value=None)
        data_accessor.check_data_availability = mocker.Mock(return_value={"status": "partial"})

        # Act
        result = data_accessor.get_consolidated_reporter_input(max_age_hours=24)

        # Assert
        assert result is not None
        assert result["aplus_opportunities"] is None
        assert result["portfolio_allocation_updates"] == []

        # Check availability status indicates unavailable
        status = result["aplus_availability_status"]
        assert status["available"] is False
        assert status["status"] == "UNAVAILABLE"
        assert status["total_opportunities"] == 0

    def test_should_generate_portfolio_allocation_updates_from_aplus_opportunities(self, data_accessor, sample_aplus_opportunities):
        """Test portfolio allocation updates generation from A+ opportunities."""
        # Act
        updates = data_accessor._generate_portfolio_allocation_updates(sample_aplus_opportunities)

        # Assert
        assert len(updates) >= 3  # At least one for each allocation recommendation

        # Check stock update (NVDA)
        nvda_updates = [u for u in updates if u.get("symbol") == "NVDA"]
        assert len(nvda_updates) >= 1
        nvda_update = nvda_updates[0]
        assert nvda_update["action"] == "ADD_OR_INCREASE"
        assert nvda_update["asset_type"] == "stock"
        assert nvda_update["grade"] == "A+"
        assert nvda_update["priority"] == "HIGH"
        assert "5-8%" in nvda_update["recommended_allocation"]

        # Check ETF update (VWCE)
        vwce_updates = [u for u in updates if u.get("symbol") == "VWCE"]
        assert len(vwce_updates) >= 1
        vwce_update = vwce_updates[0]
        assert vwce_update["asset_type"] == "etf"
        assert vwce_update["grade"] == "A+"

        # Check crypto update (BTC)
        btc_updates = [u for u in updates if u.get("symbol") == "BTC"]
        assert len(btc_updates) >= 1
        btc_update = btc_updates[0]
        assert btc_update["asset_type"] == "crypto"
        assert btc_update["allocation_percentage"] == 2.0  # Should parse "2.0% of total portfolio"

        # Check replacement updates
        replacement_updates = [u for u in updates if u["action"] == "REPLACE_OR_SUBSTITUTE"]
        assert len(replacement_updates) >= 3  # One for each replacement note

    def test_should_parse_allocation_percentages_correctly(self, data_accessor):
        """Test allocation percentage parsing from various text formats."""
        # Test cases with expected results
        test_cases = [
            ("5-8% for aggressive growth", 5.0),
            ("2.0% of total portfolio", 2.0),
            ("1.5% allocation", 1.5),
            ("Core global equity position", None),  # No percentage
            ("10% maximum", 10.0),
            ("0.5% minimum", 0.5),
        ]

        for allocation_text, expected in test_cases:
            result = data_accessor._parse_allocation_percentage(allocation_text)
            assert result == expected, f"Failed for '{allocation_text}': expected {expected}, got {result}"

    def test_should_get_aplus_availability_status_when_opportunities_available(self, data_accessor, sample_aplus_opportunities):
        """Test A+ availability status when opportunities are available."""
        # Act
        status = data_accessor._get_aplus_availability_status(sample_aplus_opportunities)

        # Assert
        assert status["available"] is True
        assert status["status"] == "HIGH_CONFIDENCE"  # confidence_score = 0.85
        assert status["confidence_score"] == 0.85
        assert status["total_opportunities"] == 7
        assert status["by_asset_type"]["stocks"] == 3
        assert status["by_asset_type"]["etfs"] == 2
        assert status["by_asset_type"]["cryptos"] == 2
        assert status["has_allocation_recommendations"] is True
        assert status["has_replacement_notes"] is True

    def test_should_get_aplus_availability_status_when_opportunities_unavailable(self, data_accessor):
        """Test A+ availability status when opportunities are unavailable."""
        # Act
        status = data_accessor._get_aplus_availability_status(None)

        # Assert
        assert status["available"] is False
        assert status["status"] == "UNAVAILABLE"
        assert status["total_opportunities"] == 0
        assert status["by_asset_type"]["stocks"] == 0
        assert status["by_asset_type"]["etfs"] == 0
        assert status["by_asset_type"]["cryptos"] == 0

    def test_should_get_aplus_availability_status_with_different_confidence_levels(self, data_accessor):
        """Test A+ availability status with different confidence levels."""
        # Test medium confidence
        medium_confidence_opportunities = APlusOpportunityCollection(
            etf_opportunities=["VWCE"],
            stock_opportunities=["NVDA"],
            crypto_opportunities=["BTC"],
            discovery_summary="Medium confidence analysis with some opportunities identified.",
            confidence_score=0.7,  # Medium confidence
            validation_timestamp=datetime.now(),
            allocation_recommendations=[],
            replacement_notes=[],
        )

        status = data_accessor._get_aplus_availability_status(medium_confidence_opportunities)
        assert status["status"] == "MEDIUM_CONFIDENCE"

        # Test low confidence
        low_confidence_opportunities = APlusOpportunityCollection(
            etf_opportunities=["VWCE"],
            stock_opportunities=[],
            crypto_opportunities=[],
            discovery_summary="Low confidence analysis with limited opportunities identified.",
            confidence_score=0.4,  # Low confidence
            validation_timestamp=datetime.now(),
            allocation_recommendations=[],
            replacement_notes=[],
        )

        status = data_accessor._get_aplus_availability_status(low_confidence_opportunities)
        assert status["status"] == "LOW_CONFIDENCE"

        # Test empty opportunities
        empty_opportunities = APlusOpportunityCollection(
            etf_opportunities=[],
            stock_opportunities=[],
            crypto_opportunities=[],
            discovery_summary="No opportunities identified in current market conditions.",
            confidence_score=0.9,  # High confidence but no opportunities
            validation_timestamp=datetime.now(),
            allocation_recommendations=[],
            replacement_notes=[],
        )

        status = data_accessor._get_aplus_availability_status(empty_opportunities)
        assert status["status"] == "EMPTY"

    def test_should_handle_consolidated_reporter_input_errors_gracefully(self, data_accessor, mocker):
        """Test consolidated reporter input generation handles errors gracefully."""
        # Arrange
        data_accessor.get_consolidated_data = mocker.Mock(side_effect=Exception("Consolidation error"))

        # Act
        result = data_accessor.get_consolidated_reporter_input(max_age_hours=24)

        # Assert
        assert result == {}  # Should return empty dict on error

    def test_should_handle_portfolio_allocation_update_errors_gracefully(self, data_accessor):
        """Test portfolio allocation updates generation handles errors gracefully."""
        # Arrange - Create malformed opportunities that might cause errors
        malformed_opportunities = APlusOpportunityCollection(
            etf_opportunities=["VWCE"],
            stock_opportunities=["NVDA"],
            crypto_opportunities=["BTC"],
            discovery_summary="Test opportunities with malformed data.",
            confidence_score=0.8,
            validation_timestamp=datetime.now(),
            allocation_recommendations=[
                {
                    # Missing required fields to test error handling
                    "symbol": "NVDA"
                }
            ],
            replacement_notes=["Invalid note format without colon"],
        )

        # Act
        updates = data_accessor._generate_portfolio_allocation_updates(malformed_opportunities)

        # Assert
        assert isinstance(updates, list)  # Should still return a list even with errors
        # Should handle malformed data gracefully

    def test_should_initialize_aplus_extractor_correctly(self, mock_integration_manager, mocker):
        """Test that A+ extractor is initialized correctly in data accessor."""
        # Arrange
        mock_extractor_class = mocker.patch("finwiz.integration.data_accessor.APlusDataExtractor")

        # Act
        accessor = CrewDataAccessor(mock_integration_manager)

        # Assert
        mock_extractor_class.assert_called_once_with(mock_integration_manager.output_dir)
        assert accessor.aplus_extractor is not None
