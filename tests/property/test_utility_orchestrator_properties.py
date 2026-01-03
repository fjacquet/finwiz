"""
Property-based tests for grading system and UtilityOrchestrator.

Tests universal properties using Hypothesis for:
- Grade distribution aggregation (centralized in grading_system.py)
- URL validation and correction
"""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.utility_orchestrator import UtilityOrchestrator
from finwiz.scoring.grading_system import count_grade_distribution


@given(
    results=st.dictionaries(
        keys=st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=("Lu",))),
        values=st.fixed_dictionaries(
            {
                "grade": st.sampled_from(["A+", "A", "B+", "B", "C+", "C", "D", "F"]),
            }
        ),
        min_size=1,
        max_size=20,
    )
)
@settings(max_examples=100)
def test_property_grade_distribution_aggregation(results):
    """
    **Feature: grading-system, Property: Grade Distribution Aggregation**

    For any set of analysis results with grades, count_grade_distribution
    should count all grades correctly.
    """
    # Act
    distribution = count_grade_distribution(results)

    # Assert - Total count should equal number of results
    total_count = sum(distribution.values())
    assert total_count == len(results)

    # Assert - Each grade should be counted correctly
    for ticker, data in results.items():
        grade = data["grade"]
        expected_count = sum(1 for d in results.values() if d["grade"] == grade)
        assert distribution[grade] == expected_count


@given(
    urls=st.dictionaries(
        keys=st.sampled_from(["10-K", "10-Q", "8-K", "DEF 14A"]),
        values=st.one_of(
            st.just(""),  # Empty URL
            st.just("invalid-url"),  # Invalid URL
            st.just("https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K"),  # Valid URL
        ),
        min_size=1,
        max_size=4,
    ),
    ticker=st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=("Lu",))),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_url_validation_and_correction(urls, ticker, mocker):
    """
    **Feature: flow-orchestrator-refactoring, Property 24: URL Validation and Correction**

    For any malformed SEC URL, the UtilityOrchestrator should fix it to a valid format.

    Validates: Requirements 9.4
    """
    # Arrange
    state = FinwizState()
    orch = UtilityOrchestrator(state)

    # Mock the URL generator and validator
    mock_generator = mocker.Mock()
    mock_generator.get_filing_metadata.return_value = {"filing_url": "https://www.sec.gov/valid-generated-url"}

    mock_validator = mocker.Mock()

    # Valid URLs pass validation, invalid ones fail
    def is_valid(url, context):
        return url.startswith("https://www.sec.gov/cgi-bin/browse-edgar")

    mock_validator.is_valid_url.side_effect = is_valid

    # Act
    validated = orch.validate_and_fix_sec_urls(
        urls=urls,
        ticker=ticker,
        url_generator=mock_generator,
        url_validator=mock_validator,
    )

    # Assert - All returned URLs should be non-empty strings
    for filing_type, url in validated.items():
        assert isinstance(url, str)
        assert len(url) > 0

    # Assert - Number of validated URLs should not exceed input URLs
    assert len(validated) <= len(urls)
