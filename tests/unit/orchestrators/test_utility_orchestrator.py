"""
Unit tests for UtilityOrchestrator.

Tests SEC URL extraction and URL validation/fixing.
"""

import pytest

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.utility_orchestrator import UtilityOrchestrator


class TestUtilityOrchestrator:
    """Test suite for UtilityOrchestrator."""

    @pytest.fixture
    def state(self):
        """Create a FinwizState instance for testing."""
        return FinwizState()

    @pytest.fixture
    def orchestrator(self, state):
        """Create a UtilityOrchestrator instance for testing."""
        return UtilityOrchestrator(state)

    def test_extract_sec_filing_urls_from_deep_analysis(self, orchestrator, state):
        """Test SEC URL extraction from deep analysis results."""
        # Arrange
        state.deep_analysis_results = {
            "AAPL": {
                "asset_class": "stock",
                "sec_filing_urls": {
                    "10-K": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K",
                    "10-Q": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-Q",
                },
            },
            "GOOGL": {
                "asset_class": "stock",
                "sec_filings": {
                    "10-K": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001652044&type=10-K",
                },
            },
        }

        # Act
        urls = orchestrator.extract_sec_filing_urls(crew_output=None)

        # Assert
        assert "AAPL" in urls
        assert "10-K" in urls["AAPL"]
        assert "10-Q" in urls["AAPL"]
        assert "GOOGL" in urls
        assert "10-K" in urls["GOOGL"]

    def test_extract_sec_filing_urls_skips_non_stock_holdings(self, orchestrator, state):
        """Test that SEC URL extraction skips non-stock holdings."""
        # Arrange
        state.deep_analysis_results = {
            "BTC": {
                "asset_class": "crypto",
                "sec_filing_urls": {"10-K": "https://example.com"},
            },
            "SPY": {
                "asset_class": "etf",
                "sec_filing_urls": {"10-K": "https://example.com"},
            },
        }

        # Act
        urls = orchestrator.extract_sec_filing_urls(crew_output=None)

        # Assert
        assert len(urls) == 0

    def test_validate_and_fix_sec_urls_keeps_valid_urls(self, orchestrator, mocker):
        """Test that valid URLs are kept unchanged."""
        # Arrange
        urls = {
            "10-K": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K",
            "10-Q": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-Q",
        }
        mock_validator = mocker.Mock()
        mock_validator.is_valid_url.return_value = True

        # Act
        validated = orchestrator.validate_and_fix_sec_urls(
            urls=urls,
            ticker="AAPL",
            url_validator=mock_validator,
        )

        # Assert
        assert validated == urls

    def test_validate_and_fix_sec_urls_regenerates_invalid_urls(self, orchestrator, mocker):
        """Test that invalid URLs are regenerated."""
        # Arrange
        urls = {
            "10-K": "invalid-url",
            "10-Q": "",
        }
        mock_validator = mocker.Mock()
        mock_validator.is_valid_url.return_value = False

        mock_generator = mocker.Mock()
        mock_generator.get_filing_metadata.return_value = {"filing_url": "https://www.sec.gov/valid-url"}

        # Act
        validated = orchestrator.validate_and_fix_sec_urls(
            urls=urls,
            ticker="AAPL",
            url_generator=mock_generator,
            url_validator=mock_validator,
        )

        # Assert
        assert validated["10-K"] == "https://www.sec.gov/valid-url"
        assert validated["10-Q"] == "https://www.sec.gov/valid-url"
        assert mock_generator.get_filing_metadata.call_count == 2

    def test_extract_sec_filing_urls_handles_exceptions(self, orchestrator, state):
        """Test that extract_sec_filing_urls handles exceptions gracefully."""
        # Arrange - set invalid data that will cause an exception
        state.deep_analysis_results = None

        # Act
        urls = orchestrator.extract_sec_filing_urls(crew_output=None)

        # Assert - should return empty dict on exception
        assert urls == {}

    def test_extract_sec_filing_urls_from_stock_analysis(self, orchestrator, state):
        """Test SEC URL extraction from stock analysis result."""
        # Arrange
        state.stock_analysis_result = {
            "sec_filing_urls": {
                "MSFT": {
                    "10-K": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000789019&type=10-K",
                },
            },
        }

        # Act
        urls = orchestrator.extract_sec_filing_urls(crew_output=None)

        # Assert
        assert "MSFT" in urls
        assert "10-K" in urls["MSFT"]
