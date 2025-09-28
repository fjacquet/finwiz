"""
Unit tests for CrewDataAccessor with fully mocked data scenarios.

Tests the enhanced data accessor functionality including market sentiment
consolidation and ticker validation consolidation with no file system access.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.schemas.integration import DataAvailabilityReport, DataAvailabilityStatus, IntegrationErrorType


class TestCrewDataAccessor:
    """Test suite for CrewDataAccessor with mocked data scenarios."""

    @pytest.fixture
    def mock_integration_manager(self):
        """Create a mock integration manager."""
        manager = Mock(spec=CrewDataIntegrationManager)
        manager.logger = Mock()
        return manager

    @pytest.fixture
    def data_accessor(self, mock_integration_manager):
        """Create a data accessor with mocked integration manager."""
        return CrewDataAccessor(mock_integration_manager)

    @pytest.fixture
    def current_time(self):
        """Fixed current time for consistent testing."""
        return datetime(2024, 1, 15, 12, 0, 0)

    def test_should_retrieve_stock_data_with_freshness_check(self, data_accessor, mock_integration_manager):
        """Test stock data retrieval with freshness validation."""
        # Arrange
        expected_data = {
            "ten_k_insights": [{"ticker": "AAPL", "insight": "Strong fundamentals"}],
            "validated_tickers": [{"symbol": "AAPL", "is_valid": True}],
            "market_sentiments": [{"positive": 0.7, "neutral": 0.2, "negative": 0.1}],
        }
        mock_integration_manager.get_crew_data_with_freshness_check.return_value = expected_data

        # Act
        result = data_accessor.get_stock_data(max_age_hours=24)

        # Assert
        assert result == expected_data
        mock_integration_manager.get_crew_data_with_freshness_check.assert_called_once_with("stock", 24, warn_on_stale=True)

    def test_should_retrieve_etf_data_with_freshness_check(self, data_accessor, mock_integration_manager):
        """Test ETF data retrieval with freshness validation."""
        # Arrange
        expected_data = {
            "validated_etfs": [{"symbol": "VTI", "is_valid": True}],
            "factsheets": [{"symbol": "VTI", "expense_ratio": 0.03}],
        }
        mock_integration_manager.get_crew_data_with_freshness_check.return_value = expected_data

        # Act
        result = data_accessor.get_etf_data(max_age_hours=12)

        # Assert
        assert result == expected_data
        mock_integration_manager.get_crew_data_with_freshness_check.assert_called_once_with("etf", 12, warn_on_stale=True)

    def test_should_retrieve_crypto_data_with_freshness_check(self, data_accessor, mock_integration_manager):
        """Test crypto data retrieval with freshness validation."""
        # Arrange
        expected_data = {
            "validated_symbols": [{"symbol": "BTC", "is_valid": True}],
            "crypto_theses": [{"symbol": "BTC", "thesis": "Digital gold narrative"}],
        }
        mock_integration_manager.get_crew_data_with_freshness_check.return_value = expected_data

        # Act
        result = data_accessor.get_crypto_data(max_age_hours=6)

        # Assert
        assert result == expected_data
        mock_integration_manager.get_crew_data_with_freshness_check.assert_called_once_with("crypto", 6, warn_on_stale=True)

    def test_should_retrieve_discovery_data_with_freshness_check(self, data_accessor, mock_integration_manager):
        """Test discovery data retrieval with freshness validation."""
        # Arrange
        expected_data = {
            "a_plus_opportunities": {
                "etf_opportunities": ["VTI", "VXUS"],
                "stock_opportunities": ["AAPL", "MSFT"],
                "crypto_opportunities": ["BTC"],
            }
        }
        mock_integration_manager.get_crew_data_with_freshness_check.return_value = expected_data

        # Act
        result = data_accessor.get_discovery_data(max_age_hours=48)

        # Assert
        assert result == expected_data
        mock_integration_manager.get_crew_data_with_freshness_check.assert_called_once_with("discovery", 48, warn_on_stale=True)

    def test_should_return_none_when_data_unavailable(self, data_accessor, mock_integration_manager):
        """Test graceful handling when crew data is unavailable."""
        # Arrange
        mock_integration_manager.get_crew_data_with_freshness_check.return_value = None

        # Act
        result = data_accessor.get_stock_data()

        # Assert
        assert result is None
        mock_integration_manager.get_crew_data_with_freshness_check.assert_called_once_with("stock", 24, warn_on_stale=True)

    def test_should_consolidate_data_from_all_available_crews(self, data_accessor, mock_integration_manager):
        """Test consolidation of data from all available crews."""
        # Arrange
        crew_data_map = {
            "stock": {"analysis": "stock_analysis", "tickers": ["AAPL", "MSFT"]},
            "etf": {"analysis": "etf_analysis", "etfs": ["VTI", "VXUS"]},
            "crypto": {"analysis": "crypto_analysis", "symbols": ["BTC", "ETH"]},
            "discovery": {"opportunities": ["AAPL", "VTI", "BTC"]},
            "portfolio": None,  # Unavailable
        }

        def mock_get_crew_data(crew_name, max_age_hours, warn_on_stale):
            return crew_data_map.get(crew_name)

        mock_integration_manager.get_crew_data_with_freshness_check.side_effect = mock_get_crew_data

        # Act
        result = data_accessor.get_consolidated_data(max_age_hours=24)

        # Assert
        assert len(result) == 4  # 4 crews with data, 1 without
        assert "stock" in result
        assert "etf" in result
        assert "crypto" in result
        assert "discovery" in result
        assert "portfolio" not in result

        assert result["stock"]["analysis"] == "stock_analysis"
        assert result["etf"]["analysis"] == "etf_analysis"
        assert result["crypto"]["analysis"] == "crypto_analysis"

        # Verify all crews were checked
        assert mock_integration_manager.get_crew_data_with_freshness_check.call_count == 5

    def test_should_handle_consolidation_errors_gracefully(self, data_accessor, mock_integration_manager):
        """Test graceful error handling during data consolidation."""
        # Arrange
        mock_integration_manager.get_crew_data_with_freshness_check.side_effect = Exception("Data access error")

        # Act
        result = data_accessor.get_consolidated_data()

        # Assert
        assert result == {}
        mock_integration_manager.logger.error.assert_called()

    def test_should_consolidate_market_sentiment_from_multiple_crews(self, data_accessor, mock_integration_manager, current_time):
        """Test market sentiment consolidation across crews."""
        # Arrange
        stock_data = {
            "market_sentiments": [
                {
                    "positive": 0.6,
                    "neutral": 0.3,
                    "negative": 0.1,
                    "source_url": "https://example.com/stock-news",
                    "date": "2024-01-15",
                    "source": "Financial Times",
                    "confidence": 0.8,
                },
                {
                    "positive": 0.7,
                    "neutral": 0.2,
                    "negative": 0.1,
                    "source_url": "https://example.com/stock-analysis",
                    "date": "2024-01-14",
                    "source": "Bloomberg",
                    "confidence": 0.9,
                },
            ]
        }

        crypto_data = {
            "market_analysis": {
                "sentiment": {
                    "positive_score": 0.5,
                    "neutral_score": 0.3,
                    "negative_score": 0.2,
                    "url": "https://example.com/crypto-sentiment",
                    "published_date": "2024-01-15",
                    "source_name": "CoinDesk",
                    "confidence": 0.7,
                }
            }
        }

        def mock_get_crew_data(crew_name, max_age_hours, warn_on_stale):
            if crew_name == "stock":
                return stock_data
            elif crew_name == "crypto":
                return crypto_data
            return None

        mock_integration_manager.get_crew_data_with_freshness_check.side_effect = mock_get_crew_data

        with patch("finwiz.integration.data_accessor.datetime") as datetime_mock:
            datetime_mock.now.return_value = current_time

            # Act
            result = data_accessor.get_consolidated_market_sentiment(max_age_hours=24)

            # Assert
            assert "aggregated_scores" in result
            assert "top_sources" in result
            assert "crew_sentiments" in result
            assert "data_quality" in result

            # Check aggregated scores
            agg_scores = result["aggregated_scores"]
            assert agg_scores["total_sources"] == 3
            assert agg_scores["positive"] > 0
            assert agg_scores["neutral"] > 0
            assert agg_scores["negative"] > 0

            # Check top sources
            assert len(result["top_sources"]) <= 3
            assert all("crew" in source for source in result["top_sources"])
            assert all("confidence" in source for source in result["top_sources"])

            # Check crew-specific sentiments
            assert "stock" in result["crew_sentiments"]
            assert "crypto" in result["crew_sentiments"]
            assert result["crew_sentiments"]["stock"]["source_count"] == 2
            assert result["crew_sentiments"]["crypto"]["source_count"] == 1

            # Check data quality assessment
            assert result["data_quality"] in ["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]

    def test_should_handle_missing_sentiment_data_gracefully(self, data_accessor, mock_integration_manager, current_time):
        """Test sentiment consolidation when no sentiment data is available."""
        # Arrange
        mock_integration_manager.get_crew_data_with_freshness_check.return_value = None

        with patch("finwiz.integration.data_accessor.datetime") as datetime_mock:
            datetime_mock.now.return_value = current_time

            # Act
            result = data_accessor.get_consolidated_market_sentiment()

            # Assert
            assert result["aggregated_scores"]["total_sources"] == 0
            assert len(result["top_sources"]) == 0
            assert len(result["crew_sentiments"]) == 0
            assert result["data_quality"] == "INSUFFICIENT"

    def test_should_consolidate_ticker_validation_from_all_crews(self, data_accessor, mock_integration_manager, current_time):
        """Test ticker validation consolidation across all crews."""
        # Arrange
        stock_data = {
            "validated_tickers": [
                {
                    "symbol": "AAPL",
                    "is_valid": True,
                    "validation_source": "yahoo_finance",
                    "validation_timestamp": "2024-01-15T12:00:00",
                    "market": "NASDAQ",
                    "sector": "Technology",
                    "company_name": "Apple Inc.",
                    "validation_errors": [],
                    "alternative_suggestions": [],
                },
                {
                    "symbol": "INVALID",
                    "is_valid": False,
                    "validation_source": "yahoo_finance",
                    "validation_timestamp": "2024-01-15T12:00:00",
                    "validation_errors": ["Symbol not found"],
                    "alternative_suggestions": ["INVLD", "INV"],
                },
            ]
        }

        etf_data = {
            "validated_etfs": [
                {
                    "symbol": "VTI",
                    "is_valid": True,
                    "validation_source": "yahoo_finance",
                    "validation_timestamp": "2024-01-15T12:00:00",
                    "fund_name": "Vanguard Total Stock Market ETF",
                    "issuer": "Vanguard",
                    "expense_ratio": 0.03,
                    "validation_errors": [],
                }
            ]
        }

        crypto_data = {
            "validated_symbols": [
                {
                    "symbol": "BTC",
                    "is_valid": True,
                    "validation_source": "coinmarketcap",
                    "validation_timestamp": "2024-01-15T12:00:00",
                    "full_name": "Bitcoin",
                    "market_cap_rank": 1,
                    "is_active": True,
                    "validation_errors": [],
                }
            ]
        }

        def mock_get_crew_data(crew_name, max_age_hours, warn_on_stale):
            if crew_name == "stock":
                return stock_data
            elif crew_name == "etf":
                return etf_data
            elif crew_name == "crypto":
                return crypto_data
            return None

        mock_integration_manager.get_crew_data_with_freshness_check.side_effect = mock_get_crew_data

        with patch("finwiz.integration.data_accessor.datetime") as datetime_mock:
            datetime_mock.now.return_value = current_time

            # Act
            result = data_accessor.get_consolidated_ticker_validation(max_age_hours=24)

            # Assert
            assert "validated_tickers" in result
            assert "validated_etfs" in result
            assert "validated_cryptos" in result
            assert "validation_summary" in result
            assert "failed_validations" in result

            # Check ticker validation results
            assert len(result["validated_tickers"]) == 2
            assert result["validated_tickers"][0]["symbol"] == "AAPL"
            assert result["validated_tickers"][0]["is_valid"] is True
            assert result["validated_tickers"][1]["symbol"] == "INVALID"
            assert result["validated_tickers"][1]["is_valid"] is False

            # Check ETF validation results
            assert len(result["validated_etfs"]) == 1
            assert result["validated_etfs"][0]["symbol"] == "VTI"
            assert result["validated_etfs"][0]["is_valid"] is True

            # Check crypto validation results
            assert len(result["validated_cryptos"]) == 1
            assert result["validated_cryptos"][0]["symbol"] == "BTC"
            assert result["validated_cryptos"][0]["is_valid"] is True

            # Check validation summary
            summary = result["validation_summary"]
            assert summary["total_symbols"] == 4
            assert summary["valid_symbols"] == 3
            assert summary["invalid_symbols"] == 1
            assert summary["validation_rate"] == 75.0

            # Check failed validations
            assert len(result["failed_validations"]) == 1
            failed = result["failed_validations"][0]
            assert failed["symbol"] == "INVALID"
            assert failed["crew"] == "stock"
            assert len(failed["alternatives"]) == 2
            assert len(failed["recovery_suggestions"]) > 0

    def test_should_handle_ticker_validation_errors_gracefully(self, data_accessor, mock_integration_manager, current_time):
        """Test ticker validation consolidation error handling."""
        # Arrange
        mock_integration_manager.get_crew_data_with_freshness_check.side_effect = Exception("Validation error")

        with patch("finwiz.integration.data_accessor.datetime") as datetime_mock:
            datetime_mock.now.return_value = current_time

            # Act
            result = data_accessor.get_consolidated_ticker_validation()

            # Assert
            assert result["validation_summary"]["total_symbols"] == 0
            assert len(result["validated_tickers"]) == 0
            assert len(result["validated_etfs"]) == 0
            assert len(result["validated_cryptos"]) == 0
            assert "error" in result
            mock_integration_manager.logger.error.assert_called()

    def test_should_provide_detailed_error_reporting_with_file_paths(self, data_accessor, mock_integration_manager):
        """Test detailed error reporting with specific file paths."""
        # Arrange
        mock_freshness_report = Mock()
        mock_freshness_report.fresh_data = ["stock"]
        mock_freshness_report.stale_data = ["etf"]
        mock_freshness_report.missing_data = ["crypto", "discovery"]
        mock_freshness_report.check_timestamp = datetime(2024, 1, 15, 12, 0, 0)
        mock_freshness_report.recommendations = ["Run missing crews", "Refresh stale data"]

        mock_integration_manager.check_data_freshness.return_value = mock_freshness_report
        mock_integration_manager.output_dir = Mock()
        mock_integration_manager.output_dir.__truediv__ = lambda self, other: f"/mock/output/{other}"
        mock_integration_manager.get_refresh_recommendations.return_value = ["crypto", "discovery", "etf"]

        # Act
        result = data_accessor.check_data_availability(max_age_hours=24)

        # Assert
        assert isinstance(result, DataAvailabilityReport)
        assert result.stock_available is True
        assert result.etf_available is True  # Available but stale
        assert result.crypto_available is False
        assert result.discovery_available is False
        assert result.portfolio_available is False

        assert "etf" in result.stale_data
        assert "crypto" in result.missing_data
        assert "discovery" in result.missing_data

        assert result.overall_status == DataAvailabilityStatus.PARTIAL
        assert len(result.integration_errors) >= 3  # 2 missing + 1 stale

        # Check error details
        missing_errors = [e for e in result.integration_errors if e.error_type == IntegrationErrorType.MISSING_DATA]
        stale_errors = [e for e in result.integration_errors if e.error_type == IntegrationErrorType.STALE_DATA]

        assert len(missing_errors) == 2
        assert len(stale_errors) == 1

        for error in missing_errors:
            assert error.expected_path is not None
            assert len(error.recovery_suggestions) > 0

    def test_should_handle_data_availability_check_errors(self, data_accessor, mock_integration_manager):
        """Test error handling during data availability checks."""
        # Arrange
        mock_integration_manager.check_data_freshness.side_effect = Exception("Freshness check failed")

        # Act
        result = data_accessor.check_data_availability()

        # Assert
        assert isinstance(result, DataAvailabilityReport)
        assert result.overall_status == DataAvailabilityStatus.UNAVAILABLE
        assert not result.stock_available
        assert not result.etf_available
        assert not result.crypto_available
        assert not result.discovery_available
        assert not result.portfolio_available

        assert len(result.integration_errors) == 1
        assert result.integration_errors[0].error_type == IntegrationErrorType.ACCESS_ERROR
        assert "Data availability check failed" in result.integration_errors[0].error_message

    def test_should_generate_stale_data_warnings_with_specific_ages(self, data_accessor, mock_integration_manager):
        """Test generation of stale data warnings with specific age information."""
        # Arrange
        mock_freshness_report = Mock()
        mock_freshness_report.stale_data = ["stock", "etf"]

        mock_integration_manager.check_data_freshness.return_value = mock_freshness_report

        # Mock freshness checker
        mock_freshness_checker = Mock()
        mock_integration_manager.freshness_checker = mock_freshness_checker

        # Mock freshness results for individual crews
        def mock_freshness_check(crew_name, max_age_hours):
            if crew_name == "stock":
                result = Mock()
                result.freshness_status.age_hours = 36.5
                return result
            elif crew_name == "etf":
                result = Mock()
                result.freshness_status.age_hours = 48.2
                return result
            return None

        mock_freshness_checker.check_data_freshness_for_crew.side_effect = mock_freshness_check

        # Act
        warnings = data_accessor.get_stale_data_warnings(max_age_hours=24)

        # Assert
        assert len(warnings) == 2
        assert "stock crew data is 36.5 hours old" in warnings[0]
        assert "etf crew data is 48.2 hours old" in warnings[1]
        assert "threshold: 24 hours" in warnings[0]
        assert "threshold: 24 hours" in warnings[1]

    def test_should_handle_stale_data_warning_errors(self, data_accessor, mock_integration_manager):
        """Test error handling in stale data warning generation."""
        # Arrange
        mock_integration_manager.check_data_freshness.side_effect = Exception("Freshness check error")

        # Act
        warnings = data_accessor.get_stale_data_warnings()

        # Assert
        assert len(warnings) == 1
        assert "Error checking data staleness" in warnings[0]
        mock_integration_manager.logger.error.assert_called()
