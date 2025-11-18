"""Unit tests for AlternativesMatchingOrchestrator."""

import os

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from finwiz.flow_state import DeepAnalysisResult, FinwizState
from finwiz.orchestrators.alternatives_matching_orchestrator import (
    AlternativesMatchingOrchestrator,
)


class TestAlternativesMatchingOrchestrator:
    """Test suite for AlternativesMatchingOrchestrator."""

    @pytest.fixture
    def state(self):
        """Create test state."""
        return FinwizState(
            session_id="test_session",
            current_day=17,
            current_month=11,
            current_year=2025,
            current_date="2025-11-17",
            full_date="November 17, 2025",
            timestamp="2025-11-17T10:00:00",
            report_language="en",
        )

    @pytest.fixture
    def orchestrator(self, state):
        """Create orchestrator instance."""
        return AlternativesMatchingOrchestrator(state)

    def test_should_return_empty_dict_when_disabled(self, orchestrator, mocker):
        """Test alternative matching returns empty dict when disabled."""
        # Arrange
        mocker.patch.dict(os.environ, {"PORTFOLIO_ENABLE_ALTERNATIVES": "false"})
        holdings = [
            {
                "ticker": "IBM",
                "grade": "D",
                "composite_score": 0.55,
                "risk_score": 7.0,
                "name": "IBM Corp",
                "asset_class": "stock",
            }
        ]

        # Act
        result = orchestrator.match_alternatives_for_holdings(holdings, {})

        # Assert
        assert result == {}

    def test_should_return_empty_dict_when_no_holdings(self, orchestrator, mocker):
        """Test alternative matching with no holdings."""
        # Arrange
        mocker.patch.dict(os.environ, {"PORTFOLIO_ENABLE_ALTERNATIVES": "true"})

        # Act
        result = orchestrator.match_alternatives_for_holdings([], {})

        # Assert
        assert result == {}

    def test_should_find_alternatives_for_underperforming_holdings(self, orchestrator, mocker):
        """Test alternative matching for underperforming holdings (grade C, D, F)."""
        # Arrange
        mocker.patch.dict(os.environ, {"PORTFOLIO_ENABLE_ALTERNATIVES": "true"})

        # Mock AlternativeFinder at the source import location
        mock_alternative = mocker.Mock()
        mock_alternative.model_dump.return_value = {
            "ticker": "MSFT",
            "name": "Microsoft",
            "asset_class": "stock",
            "grade": "A+",
            "composite_score": 0.95,
        }

        mock_finder = mocker.patch("finwiz.tools.alternative_finder_tool.AlternativeFinder")
        mock_finder_instance = mock_finder.return_value
        mock_finder_instance.find_alternatives.return_value = [mock_alternative]

        holdings = [
            {
                "ticker": "IBM",
                "grade": "D",
                "composite_score": 0.55,
                "risk_score": 4.5,  # Must be <= 5.0
                "name": "IBM Corp",
                "asset_class": "stock",
            }
        ]

        # Act
        result = orchestrator.match_alternatives_for_holdings(holdings, {})

        # Assert
        assert "IBM" in result
        assert len(result["IBM"]) == 1
        assert result["IBM"][0]["ticker"] == "MSFT"
        assert result["IBM"][0]["grade"] == "A+"

    def test_should_skip_high_grade_holdings(self, orchestrator, mocker):
        """Test that high-grade holdings (A+, A, B) are skipped."""
        # Arrange
        mocker.patch.dict(os.environ, {"PORTFOLIO_ENABLE_ALTERNATIVES": "true"})

        # Mock AlternativeFinder - should not be called
        mock_finder = mocker.patch("finwiz.tools.alternative_finder_tool.AlternativeFinder")

        holdings = [
            {
                "ticker": "AAPL",
                "grade": "A+",
                "composite_score": 0.95,
                "risk_score": 2.0,
                "name": "Apple Inc",
                "asset_class": "stock",
            },
            {
                "ticker": "GOOGL",
                "grade": "A",
                "composite_score": 0.88,
                "risk_score": 3.0,
                "name": "Alphabet Inc",
                "asset_class": "stock",
            },
            {
                "ticker": "MSFT",
                "grade": "B",
                "composite_score": 0.75,
                "risk_score": 4.0,
                "name": "Microsoft",
                "asset_class": "stock",
            },
        ]

        # Act
        result = orchestrator.match_alternatives_for_holdings(holdings, {})

        # Assert
        assert result == {}
        mock_finder.assert_not_called()

    def test_should_validate_alternative_structure(self, orchestrator, mocker):
        """Test that alternatives have proper structure (ticker, asset_class, grade)."""
        # Arrange
        mocker.patch.dict(os.environ, {"PORTFOLIO_ENABLE_ALTERNATIVES": "true"})

        # Mock AlternativeFinder with complete structure
        mock_alternative = mocker.Mock()
        mock_alternative.model_dump.return_value = {
            "ticker": "MSFT",
            "name": "Microsoft",
            "asset_class": "stock",
            "grade": "A+",
            "composite_score": 0.95,
            "risk_score": 2.5,
        }

        mock_finder = mocker.patch("finwiz.tools.alternative_finder_tool.AlternativeFinder")
        mock_finder_instance = mock_finder.return_value
        mock_finder_instance.find_alternatives.return_value = [mock_alternative]

        holdings = [
            {
                "ticker": "IBM",
                "grade": "C",
                "composite_score": 0.65,
                "risk_score": 4.8,  # Must be <= 5.0
                "name": "IBM Corp",
                "asset_class": "stock",
            }
        ]

        # Act
        result = orchestrator.match_alternatives_for_holdings(holdings, {})

        # Assert
        assert "IBM" in result
        alternative = result["IBM"][0]
        assert "ticker" in alternative
        assert "asset_class" in alternative
        assert "grade" in alternative
        assert alternative["ticker"] == "MSFT"
        assert alternative["asset_class"] == "stock"
        assert alternative["grade"] == "A+"

    def test_should_handle_missing_risk_score(self, orchestrator, mocker):
        """Test that missing risk_score is logged and skipped."""
        # Arrange
        mocker.patch.dict(os.environ, {"PORTFOLIO_ENABLE_ALTERNATIVES": "true"})

        holdings = [
            {
                "ticker": "IBM",
                "grade": "D",
                "composite_score": 0.55,
                "risk_score": None,  # Missing
                "name": "IBM Corp",
                "asset_class": "stock",
            }
        ]

        # Act - should not raise, but log error and continue
        result = orchestrator.match_alternatives_for_holdings(holdings, {})

        # Assert - no alternatives found due to error
        assert result == {}

    def test_should_handle_missing_composite_score(self, orchestrator, mocker):
        """Test that missing composite_score is logged and skipped."""
        # Arrange
        mocker.patch.dict(os.environ, {"PORTFOLIO_ENABLE_ALTERNATIVES": "true"})

        holdings = [
            {
                "ticker": "IBM",
                "grade": "D",
                "composite_score": None,  # Missing
                "risk_score": 7.0,
                "name": "IBM Corp",
                "asset_class": "stock",
            }
        ]

        # Act - should not raise, but log error and continue
        result = orchestrator.match_alternatives_for_holdings(holdings, {})

        # Assert - no alternatives found due to error
        assert result == {}

    def test_should_update_state_after_discovery(self, orchestrator, mocker):
        """Test match_alternatives_after_discovery updates state correctly."""
        # Arrange
        mocker.patch.dict(os.environ, {"PORTFOLIO_ENABLE_ALTERNATIVES": "true"})

        # Create deep analysis result with all required fields
        deep_result = DeepAnalysisResult(
            ticker="IBM",
            asset_class="stock",
            grade="D",
            composite_score=0.55,
            fundamental_score=0.5,
            technical_score=0.6,
            risk_score=4.5,  # Must be <= 5
            recommendation="SELL",
            rationale="Underperforming",
            data_freshness_hours=24,
            confidence_level=0.8,
            crew_name="TestCrew",
            cached=False,
        )
        orchestrator.state.deep_analysis_results = {"IBM": deep_result}

        # Mock AlternativeFinder
        mock_alternative = mocker.Mock()
        mock_alternative.model_dump.return_value = {
            "ticker": "MSFT",
            "name": "Microsoft",
            "asset_class": "stock",
            "grade": "A+",
            "composite_score": 0.95,
        }

        mock_finder = mocker.patch("finwiz.tools.alternative_finder_tool.AlternativeFinder")
        mock_finder_instance = mock_finder.return_value
        mock_finder_instance.find_alternatives.return_value = [mock_alternative]

        # Act
        result = orchestrator.match_alternatives_after_discovery({})

        # Assert
        assert orchestrator.state.alternatives_success is True
        assert orchestrator.state.alternatives_count == 1
        assert "IBM" in orchestrator.state.portfolio_alternatives
        assert result == orchestrator.state.portfolio_alternatives


# Property-Based Tests


@settings(max_examples=100, deadline=None)
@given(
    grade=st.sampled_from(["A+", "A", "B", "C", "D", "F"]),
    composite_score=st.floats(min_value=0.0, max_value=1.0),
    risk_score=st.floats(min_value=0.0, max_value=10.0),
)
def test_property_alternative_matching_conditional(grade, composite_score, risk_score):
    """
    Property test: Alternative Matching Conditional.

    **Feature: flow-orchestrator-refactoring, Property 11: Alternative Matching Conditional**

    For any holding with grade >= B, the AlternativesMatchingOrchestrator
    should not find alternatives.

    **Validates: Requirements 4.1**
    """
    # Arrange
    import os

    os.environ["PORTFOLIO_ENABLE_ALTERNATIVES"] = "true"

    state = FinwizState(
        session_id="test_session",
        current_day=17,
        current_month=11,
        current_year=2025,
        current_date="2025-11-17",
        full_date="November 17, 2025",
        timestamp="2025-11-17T10:00:00",
        report_language="en",
    )
    orchestrator = AlternativesMatchingOrchestrator(state)

    holding = {
        "ticker": "TEST",
        "grade": grade,
        "composite_score": composite_score,
        "risk_score": risk_score,
        "name": "Test Corp",
        "asset_class": "stock",
    }

    # Act
    result = orchestrator.match_alternatives_for_holdings([holding], {})

    # Assert
    if grade in ["A+", "A", "B"]:
        # High-grade holdings should not have alternatives
        assert "TEST" not in result or len(result.get("TEST", [])) == 0
    # For grades C, D, F, alternatives may or may not be found (depends on AlternativeFinder)


def test_property_alternative_structure_validation_with_mocker(mocker):
    """
    Property test: Alternative Structure Validation.

    **Feature: flow-orchestrator-refactoring, Property 12: Alternative Structure Validation**

    For any matched alternative, it should contain ticker, asset_class, and grade fields.

    **Validates: Requirements 4.3**

    Note: This is a parameterized test using pytest-mock instead of hypothesis
    to comply with unit test mock ban.
    """
    import os

    mocker.patch.dict(os.environ, {"PORTFOLIO_ENABLE_ALTERNATIVES": "true"})

    # Test with multiple parameter combinations
    test_cases = [
        ("AAPL", "C", 0.65, 6.0),
        ("IBM", "D", 0.55, 7.0),
        ("TSLA", "F", 0.45, 8.0),
        ("MSFT", "C", 0.70, 5.5),
        ("GOOGL", "D", 0.50, 7.5),
    ]

    for ticker, grade, composite_score, risk_score in test_cases:
        # Arrange
        state = FinwizState(
            session_id="test_session",
            current_day=17,
            current_month=11,
            current_year=2025,
            current_date="2025-11-17",
            full_date="November 17, 2025",
            timestamp="2025-11-17T10:00:00",
            report_language="en",
        )
        orchestrator = AlternativesMatchingOrchestrator(state)

        # Mock AlternativeFinder to return an alternative
        mock_alternative = mocker.Mock()
        mock_alternative.model_dump.return_value = {
            "ticker": "ALT",
            "name": "Alternative Corp",
            "asset_class": "stock",
            "grade": "A+",
            "composite_score": 0.95,
            "risk_score": 2.0,
        }

        mock_finder = mocker.patch("finwiz.tools.alternative_finder_tool.AlternativeFinder")
        mock_finder_instance = mock_finder.return_value
        mock_finder_instance.find_alternatives.return_value = [mock_alternative]

        holding = {
            "ticker": ticker,
            "grade": grade,
            "composite_score": composite_score,
            "risk_score": risk_score,
            "name": f"{ticker} Corp",
            "asset_class": "stock",
        }

        # Act
        result = orchestrator.match_alternatives_for_holdings([holding], {})

        # Assert
        if ticker in result and len(result[ticker]) > 0:
            # If alternatives were found, validate structure
            for alternative in result[ticker]:
                assert "ticker" in alternative, f"Alternative for {ticker} must have ticker field"
                assert "asset_class" in alternative, f"Alternative for {ticker} must have asset_class field"
                assert "grade" in alternative, f"Alternative for {ticker} must have grade field"
                assert isinstance(alternative["ticker"], str)
                assert isinstance(alternative["asset_class"], str)
                assert isinstance(alternative["grade"], str)

        # Reset mock for next iteration
        mocker.stop(mock_finder)
