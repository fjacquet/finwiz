"""Tests for url_validator module."""

import pytest


class TestURLValidator:
    """Tests for URLValidator class."""

    def test_init(self):
        """Test URLValidator initialization."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()
        assert validator.logger is not None

    def test_is_valid_url_valid_https(self):
        """Test valid HTTPS URL."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()
        assert validator.is_valid_url("https://www.google.com") is True
        assert validator.is_valid_url("https://finance.yahoo.com/quote/AAPL") is True

    def test_is_valid_url_valid_http(self):
        """Test valid HTTP URL."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()
        assert validator.is_valid_url("http://www.example-real.com") is True

    def test_is_valid_url_none(self):
        """Test None URL returns False."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()
        assert validator.is_valid_url(None) is False

    def test_is_valid_url_empty_string(self):
        """Test empty string URL returns False."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()
        assert validator.is_valid_url("") is False
        assert validator.is_valid_url("   ") is False

    def test_is_valid_url_not_string(self):
        """Test non-string URL returns False."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()
        assert validator.is_valid_url(123) is False
        assert validator.is_valid_url(["url"]) is False

    def test_is_valid_url_forbidden_patterns(self):
        """Test forbidden patterns are rejected."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        forbidden_urls = [
            "https://example.com/page",
            "https://test.com/api",
            "https://sample.com",
            "https://placeholder.com/data",
            "https://dummy.com",
            "https://fake.com",
            "https://mock.com",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://0.0.0.0",
        ]

        for url in forbidden_urls:
            assert validator.is_valid_url(url, context="test") is False

    def test_is_valid_url_no_protocol(self):
        """Test URL without protocol is rejected."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()
        assert validator.is_valid_url("www.google.com") is False

    def test_is_valid_url_invalid_protocol(self):
        """Test URL with invalid protocol is rejected."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()
        assert validator.is_valid_url("ftp://files.example.com") is False
        assert validator.is_valid_url("file:///path/to/file") is False

    def test_is_valid_url_no_domain(self):
        """Test URL without domain is rejected."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()
        assert validator.is_valid_url("https://") is False

    def test_is_valid_url_invalid_domain_format(self):
        """Test URL with invalid domain format is rejected."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()
        assert validator.is_valid_url("https://-invalid.com") is False
        assert validator.is_valid_url("https://invalid-.com") is False

    def test_is_valid_url_with_port(self):
        """Test URL with port is valid."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()
        assert validator.is_valid_url("https://api.service.com:8443/endpoint") is True

    def test_is_valid_url_with_context(self):
        """Test URL validation with context for logging."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()
        result = validator.is_valid_url(
            "https://finance.yahoo.com", context="SEC filing"
        )
        assert result is True

    def test_validate_and_sanitize_valid_url(self):
        """Test validate_and_sanitize returns sanitized URL."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        # Test whitespace stripping
        result = validator.validate_and_sanitize("  https://www.google.com  ")
        assert result == "https://www.google.com"

    def test_validate_and_sanitize_with_query(self):
        """Test validate_and_sanitize preserves query string."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        result = validator.validate_and_sanitize(
            "https://api.example-real.com/data?param=value"
        )
        assert "?param=value" in result

    def test_validate_and_sanitize_with_fragment(self):
        """Test validate_and_sanitize preserves fragment."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        result = validator.validate_and_sanitize(
            "https://docs.example-real.com/page#section"
        )
        assert "#section" in result

    def test_validate_and_sanitize_invalid_url(self):
        """Test validate_and_sanitize returns None for invalid URL."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        assert validator.validate_and_sanitize(None) is None
        assert validator.validate_and_sanitize("invalid") is None
        assert validator.validate_and_sanitize("https://example.com") is None

    def test_validate_and_sanitize_lowercase_protocol(self):
        """Test validate_and_sanitize lowercases protocol."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        result = validator.validate_and_sanitize("HTTPS://WWW.GOOGLE.COM")
        assert result.startswith("https://")

    def test_get_url_or_message_valid_url(self):
        """Test get_url_or_message returns URL when valid."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        result = validator.get_url_or_message("https://finance.yahoo.com")
        assert result == "https://finance.yahoo.com"

    def test_get_url_or_message_invalid_url(self):
        """Test get_url_or_message returns message when invalid."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        result = validator.get_url_or_message(None, unavailable_message="N/A")
        assert result == "N/A"

    def test_get_url_or_message_custom_message(self):
        """Test get_url_or_message with custom unavailable message."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        result = validator.get_url_or_message(
            "https://example.com",  # Forbidden
            unavailable_message="Link unavailable",
        )
        assert result == "Link unavailable"

    def test_filter_valid_urls_all_valid(self):
        """Test filter_valid_urls with all valid URLs."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        urls = [
            "https://finance.yahoo.com",
            "https://sec.gov/filing",
            "https://news.google.com",
        ]

        result = validator.filter_valid_urls(urls)
        assert len(result) == 3

    def test_filter_valid_urls_mixed(self):
        """Test filter_valid_urls with mixed valid/invalid URLs."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        urls = [
            "https://finance.yahoo.com",
            None,
            "https://example.com",  # Forbidden
            "invalid-url",
            "https://sec.gov",
        ]

        result = validator.filter_valid_urls(urls)
        assert len(result) == 2
        assert "https://finance.yahoo.com" in result
        assert "https://sec.gov" in result

    def test_filter_valid_urls_all_invalid(self):
        """Test filter_valid_urls with all invalid URLs."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        urls = [None, "", "https://example.com", "https://localhost"]

        result = validator.filter_valid_urls(urls)
        assert result == []

    def test_validate_url_dict(self):
        """Test validate_url_dict validates specified fields."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        data = {
            "name": "Company",
            "website": "https://company-site.com",
            "sec_url": "https://sec.gov/filing/12345",
            "bad_url": "https://example.com",
            "other_field": "not a url",
        }

        result = validator.validate_url_dict(
            data,
            url_fields=["website", "sec_url", "bad_url"],
        )

        assert result["name"] == "Company"
        assert result["website"] == "https://company-site.com"
        assert result["sec_url"] == "https://sec.gov/filing/12345"
        assert result["bad_url"] is None  # Invalid - forbidden pattern
        assert result["other_field"] == "not a url"

    def test_validate_url_dict_missing_fields(self):
        """Test validate_url_dict handles missing fields gracefully."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        data = {"name": "Company"}

        result = validator.validate_url_dict(
            data,
            url_fields=["website", "sec_url"],
        )

        assert result == {"name": "Company"}


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_url_validator_singleton(self):
        """Test get_url_validator returns singleton."""
        from finwiz.utils.url_validator import get_url_validator

        v1 = get_url_validator()
        v2 = get_url_validator()

        assert v1 is v2

    def test_is_valid_url_function(self):
        """Test is_valid_url convenience function."""
        from finwiz.utils.url_validator import is_valid_url

        assert is_valid_url("https://finance.yahoo.com") is True
        assert is_valid_url("https://example.com") is False
        assert is_valid_url(None) is False

    def test_validate_and_sanitize_url_function(self):
        """Test validate_and_sanitize_url convenience function."""
        from finwiz.utils.url_validator import validate_and_sanitize_url

        result = validate_and_sanitize_url("  https://yahoo.com  ")
        assert result == "https://yahoo.com"

        assert validate_and_sanitize_url(None) is None

    def test_get_url_or_message_function(self):
        """Test get_url_or_message convenience function."""
        from finwiz.utils.url_validator import get_url_or_message

        result = get_url_or_message("https://yahoo.com")
        assert result == "https://yahoo.com"

        result = get_url_or_message(None, unavailable_message="N/A")
        assert result == "N/A"


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_url_with_special_characters_in_path(self):
        """Test URL with special characters in path."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        # URL with encoded characters
        url = "https://api.service.com/data%20file?query=value%20with%20spaces"
        assert validator.is_valid_url(url) is True

    def test_url_with_subdomain(self):
        """Test URL with multiple subdomains."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        url = "https://api.v2.finance.company.com/endpoint"
        assert validator.is_valid_url(url) is True

    def test_url_with_long_path(self):
        """Test URL with long path."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        url = "https://company.com/path/to/very/deep/nested/resource/file.html"
        assert validator.is_valid_url(url) is True

    def test_forbidden_pattern_case_insensitive(self):
        """Test forbidden patterns are case insensitive."""
        from finwiz.utils.url_validator import URLValidator

        validator = URLValidator()

        assert validator.is_valid_url("https://EXAMPLE.COM") is False
        assert validator.is_valid_url("https://Example.Com") is False
        assert validator.is_valid_url("https://LOCALHOST:8080") is False
