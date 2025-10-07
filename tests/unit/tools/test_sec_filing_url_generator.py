"""
Unit tests for SEC Filing URL Generator.

Tests the SECFilingURLGenerator class for generating valid SEC filing URLs,
CIK lookup, URL verification, and error handling.
"""

import pytest
from finwiz.tools.sec_filing_url_generator import SECFilingURLGenerator


class TestSECFilingURLGenerator:
    """Test suite for SECFilingURLGenerator."""

    @pytest.fixture
    def generator(self):
        """Create generator instance for testing."""
        return SECFilingURLGenerator(timeout=5.0)

    def test_should_initialize_with_default_timeout(self):
        """Test that generator initializes with default timeout."""
        # Act
        generator = SECFilingURLGenerator()

        # Assert
        assert generator.timeout == 10.0
        assert generator._cik_cache == {}

    def test_should_initialize_with_custom_timeout(self):
        """Test that generator initializes with custom timeout."""
        # Act
        generator = SECFilingURLGenerator(timeout=5.0)

        # Assert
        assert generator.timeout == 5.0

    def test_should_get_cik_for_valid_ticker(self, generator, mocker):
        """Test CIK lookup for valid ticker."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "0": {"ticker": "AAPL", "cik_str": 320193},
            "1": {"ticker": "MSFT", "cik_str": 789019},
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_client = mocker.Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)

        mocker.patch("httpx.Client", return_value=mock_client)

        # Act
        cik = generator.get_cik("AAPL")

        # Assert
        assert cik == "0000320193"
        assert "AAPL" in generator._cik_cache
        assert generator._cik_cache["AAPL"] == "0000320193"

    def test_should_return_none_for_invalid_ticker(self, generator, mocker):
        """Test CIK lookup returns None for invalid ticker."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "0": {"ticker": "AAPL", "cik_str": 320193},
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_client = mocker.Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)

        mocker.patch("httpx.Client", return_value=mock_client)

        # Act
        cik = generator.get_cik("INVALID")

        # Assert
        assert cik is None
        assert generator._cik_cache["INVALID"] is None

    def test_should_use_cached_cik(self, generator, mocker):
        """Test that CIK lookup uses cache on subsequent calls."""
        # Arrange
        generator._cik_cache["AAPL"] = "0000320193"
        mock_client = mocker.patch("httpx.Client")

        # Act
        cik = generator.get_cik("AAPL")

        # Assert
        assert cik == "0000320193"
        mock_client.assert_not_called()

    def test_should_handle_api_error_gracefully(self, generator, mocker):
        """Test that CIK lookup handles API errors gracefully."""
        # Arrange
        mock_client = mocker.Mock()
        mock_client.get.side_effect = Exception("API Error")
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)

        mocker.patch("httpx.Client", return_value=mock_client)

        # Act
        cik = generator.get_cik("AAPL")

        # Assert
        assert cik is None

    def test_should_normalize_ticker_to_uppercase(self, generator, mocker):
        """Test that ticker is normalized to uppercase."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "0": {"ticker": "AAPL", "cik_str": 320193},
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_client = mocker.Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)

        mocker.patch("httpx.Client", return_value=mock_client)

        # Act
        cik = generator.get_cik("aapl")

        # Assert
        assert cik == "0000320193"
        assert "AAPL" in generator._cik_cache

    def test_should_generate_company_browse_url(self, generator):
        """Test generation of company browse URL."""
        # Act
        url = generator.get_company_browse_url("0000320193")

        # Assert
        assert "www.sec.gov/cgi-bin/browse-edgar" in url
        assert "CIK=0000320193" in url
        assert "action=getcompany" in url

    def test_should_generate_browse_url_with_filing_type(self, generator):
        """Test browse URL generation with filing type filter."""
        # Act
        url = generator.get_company_browse_url("0000320193", "10-K")

        # Assert
        assert "www.sec.gov/cgi-bin/browse-edgar" in url
        assert "CIK=0000320193" in url
        assert "type=10-K" in url

    def test_should_pad_cik_to_ten_digits(self, generator):
        """Test that CIK is zero-padded to 10 digits."""
        # Act
        url = generator.get_company_browse_url("320193")

        # Assert
        assert "CIK=0000320193" in url

    def test_should_get_filing_url_for_valid_ticker(self, generator, mocker):
        """Test filing URL generation for valid ticker."""
        # Arrange
        mocker.patch.object(generator, "get_cik", return_value="0000320193")

        # Act
        url = generator.get_filing_url("AAPL", "10-K")

        # Assert
        assert url is not None
        assert "www.sec.gov/cgi-bin/browse-edgar" in url
        assert "CIK=0000320193" in url
        assert "type=10-K" in url

    def test_should_return_none_when_cik_not_found(self, generator, mocker):
        """Test that filing URL returns None when CIK not found."""
        # Arrange
        mocker.patch.object(generator, "get_cik", return_value=None)

        # Act
        url = generator.get_filing_url("INVALID")

        # Assert
        assert url is None

    def test_should_verify_url_when_requested(self, generator, mocker):
        """Test URL verification when verify=True."""
        # Arrange
        mocker.patch.object(generator, "get_cik", return_value="0000320193")
        mocker.patch.object(generator, "verify_url", return_value=True)

        # Act
        url = generator.get_filing_url("AAPL", "10-K", verify=True)

        # Assert
        assert url is not None
        generator.verify_url.assert_called_once()

    def test_should_return_none_when_verification_fails(self, generator, mocker):
        """Test that None is returned when URL verification fails."""
        # Arrange
        mocker.patch.object(generator, "get_cik", return_value="0000320193")
        mocker.patch.object(generator, "verify_url", return_value=False)

        # Act
        url = generator.get_filing_url("AAPL", "10-K", verify=True)

        # Assert
        assert url is None

    def test_should_verify_url_successfully(self, generator, mocker):
        """Test successful URL verification."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 200

        mock_client = mocker.Mock()
        mock_client.head.return_value = mock_response
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)

        mocker.patch("httpx.Client", return_value=mock_client)

        # Act
        result = generator.verify_url("https://www.sec.gov/test")

        # Assert
        assert result is True

    def test_should_fail_verification_for_non_200_status(self, generator, mocker):
        """Test URL verification fails for non-200 status."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.status_code = 404

        mock_client = mocker.Mock()
        mock_client.head.return_value = mock_response
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)

        mocker.patch("httpx.Client", return_value=mock_client)

        # Act
        result = generator.verify_url("https://www.sec.gov/test")

        # Assert
        assert result is False

    def test_should_handle_verification_error(self, generator, mocker):
        """Test URL verification handles errors gracefully."""
        # Arrange
        mock_client = mocker.Mock()
        mock_client.head.side_effect = Exception("Network error")
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)

        mocker.patch("httpx.Client", return_value=mock_client)

        # Act
        result = generator.verify_url("https://www.sec.gov/test")

        # Assert
        assert result is False

    def test_should_get_filing_metadata(self, generator, mocker):
        """Test getting complete filing metadata."""
        # Arrange
        mocker.patch.object(generator, "get_cik", return_value="0000320193")
        mocker.patch.object(
            generator,
            "get_filing_url",
            return_value="https://www.sec.gov/cgi-bin/browse-edgar?CIK=0000320193&type=10-K",
        )

        # Act
        metadata = generator.get_filing_metadata("AAPL", "10-K")

        # Assert
        assert metadata is not None
        assert metadata["ticker"] == "AAPL"
        assert metadata["cik"] == "0000320193"
        assert metadata["filing_type"] == "10-K"
        assert metadata["filing_url"] is not None
        assert metadata["browse_url"] is not None
        assert metadata["available"] is True

    def test_should_return_none_metadata_when_cik_not_found(self, generator, mocker):
        """Test metadata returns None when CIK not found."""
        # Arrange
        mocker.patch.object(generator, "get_cik", return_value=None)

        # Act
        metadata = generator.get_filing_metadata("INVALID")

        # Assert
        assert metadata is None

    def test_should_clear_cache(self, generator):
        """Test cache clearing."""
        # Arrange
        generator._cik_cache["AAPL"] = "0000320193"
        generator._cik_cache["MSFT"] = "0000789019"

        # Act
        generator.clear_cache()

        # Assert
        assert len(generator._cik_cache) == 0

    def test_should_handle_whitespace_in_ticker(self, generator, mocker):
        """Test that whitespace in ticker is handled."""
        # Arrange
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "0": {"ticker": "AAPL", "cik_str": 320193},
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_client = mocker.Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)

        mocker.patch("httpx.Client", return_value=mock_client)

        # Act
        cik = generator.get_cik("  AAPL  ")

        # Assert
        assert cik == "0000320193"
        assert "AAPL" in generator._cik_cache

    def test_should_normalize_filing_type_to_uppercase(self, generator, mocker):
        """Test that filing type is normalized to uppercase."""
        # Arrange
        mocker.patch.object(generator, "get_cik", return_value="0000320193")

        # Act
        url = generator.get_filing_url("AAPL", "10-k")

        # Assert
        assert url is not None
        assert "type=10-K" in url
