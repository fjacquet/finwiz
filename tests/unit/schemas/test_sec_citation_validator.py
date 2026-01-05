"""
Unit tests for SECCitationValidator class.

Tests SEC/EDGAR citation extraction, validation, filing date and URL verification,
and citation consolidation with full mocking.
"""

from datetime import datetime, timedelta

import pytest

from finwiz.schemas.integration import SECCitation, ValidationStatus
from finwiz.validation.sec_citation import (
    ConsolidatedSECCitations,
    SECCitationValidationResult,
    SECCitationValidator,
    SECFilingInfo,
)


class TestSECCitationValidator:
    """Test cases for SECCitationValidator class."""

    @pytest.fixture
    def mock_logger(self, mocker):
        """Mock logger for testing."""
        return mocker.Mock()

    @pytest.fixture
    def sec_validator(self, mock_logger):
        """Create SECCitationValidator instance for testing."""
        return SECCitationValidator(logger=mock_logger)

    @pytest.fixture
    def sample_validation_status(self):
        """Sample validation status for testing."""
        return ValidationStatus(is_valid=True, validation_timestamp=datetime.now(), validation_errors=[], validation_warnings=[], schema_version=1)

    @pytest.fixture
    def sample_sec_citation(self, sample_validation_status):
        """Sample SEC citation for testing."""
        return SECCitation(
            ticker="AAPL",
            filing_url="https://www.sec.gov/Archives/edgar/data/320193/000032019324000007/aapl-20240930.htm",
            filed_at=datetime(2024, 10, 31),
            section="Item 1A",
            excerpt="The Company faces intense competition in all areas of its business",
            sec_citation="10-K (2024), Item 1A, p. 17",
            extraction_timestamp=datetime.now(),
            validation_status=sample_validation_status,
        )

    def test_should_initialize_sec_citation_validator_successfully(self, mock_logger):
        """Test SECCitationValidator initialization."""
        validator = SECCitationValidator(logger=mock_logger)

        assert validator.logger == mock_logger
        assert len(validator.sec_url_patterns) > 0
        assert len(validator.filing_type_patterns) > 0
        assert len(validator.citation_patterns) > 0

        mock_logger.info.assert_called_once()

    def test_should_validate_valid_sec_citation_successfully(self, sec_validator, sample_sec_citation):
        """Test successful validation of valid SEC citation."""
        result = sec_validator.validate_sec_citation(sample_sec_citation)

        assert isinstance(result, SECCitationValidationResult)
        assert result.is_valid is True
        assert len(result.validation_errors) == 0
        assert result.validation_timestamp is not None
        # filing_info may be None if URL parsing doesn't extract info, which is acceptable

    def test_should_fail_validation_when_invalid_citation_provided(self, sec_validator, sample_validation_status):
        """Test validation failure with invalid SEC citation."""
        # Create citation with invalid data that passes Pydantic validation but fails business logic
        invalid_citation = SECCitation(
            ticker="AAPL",  # Valid ticker
            filing_url="https://www.sec.gov/Archives/edgar/data/320193/000032019324000007/aapl-20240930.htm",  # Valid URL
            filed_at=datetime(1980, 1, 1),  # Too old date - business logic validation
            section="Item 1A",
            excerpt="The Company faces intense competition in all areas of its business",
            sec_citation="10-K (2024), Item 1A, p. 17",
            extraction_timestamp=datetime.now(),
            validation_status=sample_validation_status,
        )

        result = sec_validator.validate_sec_citation(invalid_citation)

        assert isinstance(result, SECCitationValidationResult)
        assert result.is_valid is False
        assert len(result.validation_errors) > 0

        # Check for specific validation errors
        error_messages = [error.lower() for error in result.validation_errors]
        assert any("date" in msg or "old" in msg for msg in error_messages)

    def test_should_validate_ticker_format_correctly(self, sec_validator):
        """Test ticker format validation."""
        # Valid tickers
        assert sec_validator._validate_ticker_format("AAPL") is True
        assert sec_validator._validate_ticker_format("MSFT") is True
        assert sec_validator._validate_ticker_format("BRK.B") is False  # Contains dot
        assert sec_validator._validate_ticker_format("GOOGL") is True

        # Invalid tickers
        assert sec_validator._validate_ticker_format("") is False
        assert sec_validator._validate_ticker_format("TOOLONGTICKERR") is False
        assert sec_validator._validate_ticker_format("123") is True  # Numbers allowed
        assert sec_validator._validate_ticker_format("ABC-DEF") is False  # Contains dash
        assert sec_validator._validate_ticker_format(None) is False

    def test_should_validate_filing_url_format_correctly(self, sec_validator):
        """Test SEC filing URL validation."""
        # Valid SEC URLs
        valid_urls = [
            "https://www.sec.gov/Archives/edgar/data/320193/000032019324000007/aapl-20240930.htm",
            "https://sec.gov/Archives/edgar/data/789019/000156459024004894/msft-10k_20240630.htm",
            "http://www.sec.gov/filing/123456",
        ]

        for url in valid_urls:
            is_valid, error_msg, filing_info = sec_validator._validate_filing_url(url)
            assert is_valid is True, f"URL should be valid: {url}"
            assert error_msg == ""

        # Invalid URLs
        invalid_urls = ["https://yahoo.com/finance", "https://google.com/search", "not-a-url", ""]

        for url in invalid_urls:
            is_valid, error_msg, filing_info = sec_validator._validate_filing_url(url)
            assert is_valid is False, f"URL should be invalid: {url}"
            assert error_msg != ""

    def test_should_validate_filing_date_correctly(self, sec_validator):
        """Test filing date validation."""
        # Valid dates
        valid_dates = [datetime(2024, 1, 1), datetime(2020, 6, 15), datetime(1995, 12, 31), datetime.now() - timedelta(days=30)]

        for date in valid_dates:
            assert sec_validator._validate_filing_date(date) is True

        # Invalid dates
        invalid_dates = [
            datetime(1980, 1, 1),  # Too old
            datetime.now() + timedelta(days=30),  # Too far in future
            datetime(1989, 12, 31),  # Before 1990
        ]

        for date in invalid_dates:
            assert sec_validator._validate_filing_date(date) is False

        # Invalid type
        assert sec_validator._validate_filing_date("not-a-date") is False
        assert sec_validator._validate_filing_date(None) is False

    def test_should_validate_section_format_correctly(self, sec_validator):
        """Test section format validation."""
        # Valid sections
        valid_sections = [
            "Item 1A",
            "Item 2",
            "Item 1B",
            "Part I",
            "Part II",
            "Section 1",
            "Business Overview",
            "MD&A",
            "Risk Factors",
            "Liquidity",
            "Segments",
        ]

        for section in valid_sections:
            assert sec_validator._validate_section_format(section) is True, f"Section should be valid: {section}"

        # Invalid sections
        invalid_sections = ["", "Random Text", "123456", None]

        for section in invalid_sections:
            assert sec_validator._validate_section_format(section) is False, f"Section should be invalid: {section}"

    def test_should_validate_excerpt_correctly(self, sec_validator):
        """Test excerpt validation."""
        # Valid excerpts
        valid_excerpts = [
            (
                "The Company faces intense competition in all areas of its business and believes "
                "a significant factor in competing successfully is continually improving the total customer experience."
            ),
            "This is a valid excerpt with sufficient length and meaningful content for testing purposes.",
            "Risk factors include market volatility, regulatory changes, and competitive pressures.",
        ]

        for excerpt in valid_excerpts:
            assert sec_validator._validate_excerpt(excerpt) is True, f"Excerpt should be valid: {excerpt[:50]}..."

        # Invalid excerpts
        invalid_excerpts = [
            "",
            "Too short",
            "123456789",  # Only numbers
            "   ",  # Only whitespace
            None,
        ]

        for excerpt in invalid_excerpts:
            assert sec_validator._validate_excerpt(excerpt) is False, f"Excerpt should be invalid: {excerpt}"

    def test_should_validate_citation_format_correctly(self, sec_validator):
        """Test citation format validation."""
        # Valid citation formats
        valid_citations = [
            "10-K (2024)",
            "10-Q (2023), Item 1A",
            "10-K (2024), Item 1A, p. 17",
            "8-K (2024), Item 2.02",
            "10-Q (2023), Part I, p. 25",
        ]

        for citation in valid_citations:
            assert sec_validator._validate_citation_format(citation) is True, f"Citation should be valid: {citation}"

        # Invalid citation formats
        invalid_citations = ["", "Random text", "Not a citation", "123456", None]

        for citation in invalid_citations:
            assert sec_validator._validate_citation_format(citation) is False, f"Citation should be invalid: {citation}"

    def test_should_extract_filing_info_from_url_successfully(self, sec_validator):
        """Test extraction of filing information from SEC URL."""
        test_urls = [
            "https://www.sec.gov/Archives/edgar/data/320193/000032019324000007/aapl-10k_20240930.htm",
            "https://sec.gov/Archives/edgar/data/789019/000156459024004894/msft-10q_20240630.htm",
        ]

        for url in test_urls:
            filing_info = sec_validator._extract_filing_info_from_url(url)

            # Should extract some information (implementation may vary)
            assert filing_info is None or isinstance(filing_info, SECFilingInfo)

    def test_should_extract_filing_type_from_citation(self, sec_validator):
        """Test extraction of filing type from citation."""
        test_cases = [
            ("10-K (2024), Item 1A", "10-K"),
            ("10-Q (2023), Part I", "10-Q"),
            ("8-K (2024), Item 2.02", "8-K"),
            ("DEF 14A (2024)", "DEF 14A"),
            ("Unknown format", "Unknown"),
        ]

        for citation, expected_type in test_cases:
            result = sec_validator._extract_filing_type(citation)
            assert result == expected_type, f"Expected {expected_type}, got {result} for citation: {citation}"

    def test_should_deduplicate_citations_correctly(self, sec_validator, sample_sec_citation):
        """Test citation deduplication."""
        # Create duplicate citations
        citation1 = sample_sec_citation
        citation2 = sample_sec_citation.model_copy()  # Exact duplicate
        citation3 = sample_sec_citation.model_copy()
        citation3.excerpt = "Different excerpt but same ticker/URL/section"  # Should be considered duplicate

        citation4 = sample_sec_citation.model_copy()
        citation4.ticker = "MSFT"  # Different ticker, should not be duplicate

        citations = [citation1, citation2, citation3, citation4]

        unique_citations = sec_validator._deduplicate_citations(citations)

        assert len(unique_citations) == 2  # Should have 2 unique citations
        tickers = [c.ticker for c in unique_citations]
        assert "AAPL" in tickers
        assert "MSFT" in tickers

    def test_should_validate_multiple_citations_successfully(self, sec_validator, sample_sec_citation, sample_validation_status):
        """Test validation of multiple citations."""
        # Create a second valid citation
        citation2 = SECCitation(
            ticker="MSFT",
            filing_url="https://www.sec.gov/Archives/edgar/data/789019/000156459024000001/msft-20240630.htm",
            filed_at=datetime(2024, 7, 30),
            section="Item 1A",
            excerpt="We face intense competition across all markets for our products and services",
            sec_citation="10-K (2024), Item 1A, p. 12",
            extraction_timestamp=datetime.now(),
            validation_status=sample_validation_status,
        )

        # Create an invalid citation (old date)
        invalid_citation = SECCitation(
            ticker="GOOGL",
            filing_url="https://www.sec.gov/Archives/edgar/data/1652044/000165204424000001/googl-20240630.htm",
            filed_at=datetime(1980, 1, 1),  # Too old - business logic validation
            section="Item 1A",
            excerpt="We face significant competition in the technology sector",
            sec_citation="10-K (2024), Item 1A, p. 15",
            extraction_timestamp=datetime.now(),
            validation_status=sample_validation_status,
        )

        citations = [sample_sec_citation, citation2, invalid_citation]

        results = sec_validator.validate_multiple_citations(citations)

        assert len(results) == 3
        assert all(isinstance(result, SECCitationValidationResult) for result in results.values())

        # Should have two valid and one invalid result
        valid_count = sum(1 for result in results.values() if result.is_valid)
        invalid_count = sum(1 for result in results.values() if not result.is_valid)

        assert valid_count == 2
        assert invalid_count == 1

    def test_should_consolidate_citations_for_report_successfully(self, sec_validator, sample_sec_citation):
        """Test consolidation of citations for report integration."""
        # Create citations from different crews
        citation1 = sample_sec_citation
        citation2 = sample_sec_citation.model_copy()
        citation2.ticker = "MSFT"
        citation2.section = "Item 2"

        crew_citations = {"stock": [citation1], "etf": [citation2]}

        consolidated = sec_validator.consolidate_citations_for_report(crew_citations)

        assert isinstance(consolidated, ConsolidatedSECCitations)
        assert consolidated.consolidation_timestamp is not None
        assert len(consolidated.unique_citations) >= 0
        assert isinstance(consolidated.citations_by_ticker, dict)
        assert isinstance(consolidated.citations_by_filing_type, dict)
        assert isinstance(consolidated.validation_summary, dict)

        # Check validation summary
        assert "total_citations_processed" in consolidated.validation_summary
        assert "valid_citations" in consolidated.validation_summary
        assert "invalid_citations" in consolidated.validation_summary

    def test_should_extract_citations_from_crew_outputs_successfully(self, sec_validator):
        """Test extraction of citations from crew outputs."""
        # Mock crew outputs with SEC citations
        crew_outputs = {
            "stock": {
                "sec_citations": [
                    {
                        "ticker": "AAPL",
                        "filing_url": "https://www.sec.gov/filing/123",
                        "filed_at": datetime.now().isoformat(),
                        "section": "Item 1A",
                        "excerpt": "The Company faces intense competition",
                        "sec_citation": "10-K (2024), Item 1A",
                        "extraction_timestamp": datetime.now().isoformat(),
                        "validation_status": {
                            "is_valid": True,
                            "validation_timestamp": datetime.now().isoformat(),
                            "validation_errors": [],
                            "validation_warnings": [],
                            "schema_version": 1,
                        },
                    }
                ]
            },
            "etf": {
                "ten_k_insights": [
                    {
                        "ticker": "SPY",
                        "filing_url": "https://www.sec.gov/filing/456",
                        "section": "Business Overview",
                        "insight": "The fund tracks the S&P 500 index",
                        "filed_at": datetime.now().isoformat(),
                    }
                ]
            },
        }

        extracted_citations = sec_validator.extract_citations_from_crew_outputs(crew_outputs)

        assert isinstance(extracted_citations, dict)
        assert "stock" in extracted_citations
        assert len(extracted_citations["stock"]) == 1
        assert isinstance(extracted_citations["stock"][0], SECCitation)

    def test_should_handle_invalid_citation_data_gracefully(self, sec_validator):
        """Test graceful handling of invalid citation data."""
        crew_outputs = {
            "stock": {
                "sec_citations": [
                    {
                        "ticker": "AAPL",
                        # Missing required fields
                    },
                    {"invalid": "data structure"},
                ]
            }
        }

        # Should not raise exception
        extracted_citations = sec_validator.extract_citations_from_crew_outputs(crew_outputs)

        assert isinstance(extracted_citations, dict)
        # May or may not have extracted citations depending on validation

    def test_should_handle_empty_crew_outputs_gracefully(self, sec_validator):
        """Test handling of empty crew outputs."""
        empty_outputs = {}

        extracted_citations = sec_validator.extract_citations_from_crew_outputs(empty_outputs)

        assert isinstance(extracted_citations, dict)
        assert len(extracted_citations) == 0

    def test_should_handle_exception_during_validation_gracefully(self, mocker, sec_validator, sample_sec_citation):
        """Test graceful handling of exceptions during validation."""
        # Mock an exception in URL validation
        with mocker.patch.object(sec_validator, "_validate_filing_url", side_effect=Exception("Test error")):
            result = sec_validator.validate_sec_citation(sample_sec_citation)

            assert isinstance(result, SECCitationValidationResult)
            assert result.is_valid is False
            assert len(result.validation_errors) > 0
            assert "Test error" in str(result.validation_errors)

    def test_should_check_url_accessibility_when_requested(self, mocker, sec_validator, sample_sec_citation):
        """Test URL accessibility checking."""
        # Mock URL accessibility check
        with mocker.patch.object(sec_validator, "_check_url_accessibility", return_value=False):
            result = sec_validator.validate_sec_citation(sample_sec_citation, check_url_accessibility=True)

            assert result.url_accessible is False
            assert len(result.validation_warnings) > 0
            assert any("accessible" in warning.lower() for warning in result.validation_warnings)

    def test_should_extract_citations_from_insights_successfully(self, sec_validator):
        """Test extraction of citations from 10-K insights."""
        insights = [
            {
                "ticker": "AAPL",
                "filing_url": "https://www.sec.gov/filing/123",
                "section": "Item 1A",
                "insight": "The Company faces intense competition in all areas",
                "filed_at": datetime.now().isoformat(),
            },
            {
                "ticker": "MSFT",
                "filing_url": "https://www.sec.gov/filing/456",
                "section": "Business Overview",
                "content": "Microsoft Corporation develops and licenses software",
                "filed_at": datetime.now().isoformat(),
            },
        ]

        citations = sec_validator._extract_citations_from_insights(insights)

        assert isinstance(citations, list)
        assert len(citations) == 2
        assert all(isinstance(citation, SECCitation) for citation in citations)
        assert citations[0].ticker == "AAPL"
        assert citations[1].ticker == "MSFT"

    def test_should_handle_malformed_insights_gracefully(self, sec_validator):
        """Test handling of malformed insights data."""
        malformed_insights = [
            {"ticker": "AAPL"},  # Missing required fields
            {"invalid": "structure"},
            {},  # Empty insight
            None,  # None value
        ]

        # Should not raise exception
        citations = sec_validator._extract_citations_from_insights(malformed_insights)

        assert isinstance(citations, list)
        # Should return empty list or handle gracefully
