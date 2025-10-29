"""
URL validation utility to prevent placeholder and invalid URLs in reports.

This module provides comprehensive URL validation to ensure that only real,
valid URLs are included in reports and analysis outputs.
"""

import re
from urllib.parse import urlparse

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class URLValidator:
    """
    Validates URLs to prevent placeholder and invalid URLs in reports.

    This validator ensures that:
    - URLs have valid format and protocol
    - URLs are not placeholder/test domains
    - URLs are not empty or None
    """

    # Forbidden URL patterns that indicate placeholders or test data
    FORBIDDEN_PATTERNS = [
        "example.com",
        "test.com",
        "sample.com",
        "placeholder.com",
        "dummy.com",
        "fake.com",
        "mock.com",
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    ]

    # Valid URL protocols
    VALID_PROTOCOLS = ["http", "https"]

    def __init__(self) -> None:
        """Initialize URL validator."""
        self.logger = logger

    def is_valid_url(self, url: str | None, context: str = "") -> bool:
        """
        Check if URL is valid and not a placeholder.

        Args:
            url: URL to validate
            context: Context for logging (e.g., "SEC filing", "news article")

        Returns:
            True if URL is valid, False otherwise

        """
        if not url:
            self.logger.debug(f"URL validation failed ({context}): URL is None or empty")
            return False

        # Check if URL is a string
        if not isinstance(url, str):
            self.logger.warning(f"URL validation failed ({context}): URL is not a string: {type(url)}")
            return False

        # Strip whitespace
        url = url.strip()

        if not url:
            self.logger.debug(f"URL validation failed ({context}): URL is empty after stripping")
            return False

        # Check for forbidden patterns
        url_lower = url.lower()
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in url_lower:
                self.logger.warning(f"URL validation failed ({context}): Contains forbidden pattern '{pattern}': {url}")
                return False

        # Parse URL to validate structure
        try:
            parsed = urlparse(url)

            # Check for valid protocol
            if not parsed.scheme:
                self.logger.warning(f"URL validation failed ({context}): No protocol specified: {url}")
                return False

            if parsed.scheme not in self.VALID_PROTOCOLS:
                self.logger.warning(f"URL validation failed ({context}): Invalid protocol '{parsed.scheme}': {url}")
                return False

            # Check for valid domain
            if not parsed.netloc:
                self.logger.warning(f"URL validation failed ({context}): No domain specified: {url}")
                return False

            # Check domain format (basic validation)
            domain_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
            if not re.match(domain_pattern, parsed.netloc.split(":")[0]):  # Remove port if present
                self.logger.warning(f"URL validation failed ({context}): Invalid domain format: {url}")
                return False

            self.logger.debug(f"URL validation passed ({context}): {url}")
            return True

        except Exception as e:
            self.logger.error(f"URL validation failed ({context}): Exception during parsing: {e}")
            return False

    def validate_and_sanitize(self, url: str | None, context: str = "") -> str | None:
        """
        Validate URL and return sanitized version or None if invalid.

        Args:
            url: URL to validate and sanitize
            context: Context for logging

        Returns:
            Sanitized URL if valid, None otherwise

        """
        if not self.is_valid_url(url, context):
            return None

        # Sanitize URL (strip whitespace, ensure lowercase protocol)
        url = url.strip()
        parsed = urlparse(url)

        # Reconstruct URL with lowercase protocol
        sanitized = f"{parsed.scheme.lower()}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            sanitized += f"?{parsed.query}"
        if parsed.fragment:
            sanitized += f"#{parsed.fragment}"

        return sanitized

    def get_url_or_message(self, url: str | None, context: str = "", unavailable_message: str = "URL not available") -> str:
        """
        Get validated URL or unavailable message.

        Args:
            url: URL to validate
            context: Context for logging
            unavailable_message: Message to return if URL is invalid

        Returns:
            Validated URL or unavailable message

        """
        validated_url = self.validate_and_sanitize(url, context)

        if validated_url:
            return validated_url
        else:
            self.logger.info(f"URL not available ({context}), returning message: {unavailable_message}")
            return unavailable_message

    def filter_valid_urls(self, urls: list[str | None], context: str = "") -> list[str]:
        """
        Filter list of URLs to only include valid ones.

        Args:
            urls: List of URLs to filter
            context: Context for logging

        Returns:
            List of valid URLs

        """
        valid_urls = []
        rejected_count = 0

        for url in urls:
            validated = self.validate_and_sanitize(url, context)
            if validated:
                valid_urls.append(validated)
            else:
                rejected_count += 1

        if rejected_count > 0:
            self.logger.info(f"Filtered {rejected_count} invalid URLs from {len(urls)} total ({context})")

        return valid_urls

    def validate_url_dict(self, data: dict, url_fields: list[str], context: str = "") -> dict:
        """
        Validate URL fields in a dictionary and replace invalid ones with None.

        Args:
            data: Dictionary containing URL fields
            url_fields: List of field names that contain URLs
            context: Context for logging

        Returns:
            Dictionary with validated URLs (invalid ones set to None)

        """
        validated_data = data.copy()

        for field in url_fields:
            if field in validated_data:
                url = validated_data[field]
                validated_url = self.validate_and_sanitize(url, f"{context}.{field}")
                validated_data[field] = validated_url

        return validated_data


# Global validator instance
_url_validator = None


def get_url_validator() -> URLValidator:
    """Get global URL validator instance."""
    global _url_validator
    if _url_validator is None:
        _url_validator = URLValidator()
    return _url_validator


def is_valid_url(url: str | None, context: str = "") -> bool:
    """
    Check if URL is valid (convenience function).

    Args:
        url: URL to validate
        context: Context for logging

    Returns:
        True if URL is valid, False otherwise

    """
    validator = get_url_validator()
    return validator.is_valid_url(url, context)


def validate_and_sanitize_url(url: str | None, context: str = "") -> str | None:
    """
    Validate and sanitize URL (convenience function).

    Args:
        url: URL to validate and sanitize
        context: Context for logging

    Returns:
        Sanitized URL if valid, None otherwise

    """
    validator = get_url_validator()
    return validator.validate_and_sanitize(url, context)


def get_url_or_message(url: str | None, context: str = "", unavailable_message: str = "URL not available") -> str:
    """
    Get validated URL or unavailable message (convenience function).

    Args:
        url: URL to validate
        context: Context for logging
        unavailable_message: Message to return if URL is invalid

    Returns:
        Validated URL or unavailable message

    """
    validator = get_url_validator()
    return validator.get_url_or_message(url, context, unavailable_message)
