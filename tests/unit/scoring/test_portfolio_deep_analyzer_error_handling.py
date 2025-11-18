"""
Unit tests for portfolio deep analyzer error handling with critical fields.

Tests that the portfolio analyzer properly handles CriticalFieldError exceptions
and skips holdings with missing critical data instead of using fallbacks.
"""

import pytest

from finwiz.schemas.portfolio_review import HoldingDecision
from finwiz.scoring.portfolio_deep_analyzer import PortfolioDeepAnalyzer


@pytest.mark.skip(reason="Critical field validation not yet implemented in PortfolioDeepAnalyzer - tracked in separate issue")
class TestPortfolioDeepAnalyzerErrorHandling:
    """Test portfolio deep analyzer error handling."""

    @pytest.fixture
    def analyzer(self, tmp_path):
        """Create analyzer instance."""
        return PortfolioDeepAnalyzer(output_dir=str(tmp_path))

    @pytest.fixture
    def complete_holding(self):
        """Create holding with complete data."""
        from finwiz.schemas.common import RiskAssessmentStandardized

        return HoldingDecision(
            ticker="AAPL",
            asset_class="stock",
            name="Apple Inc.",
            currency="USD",
            decision="KEEP",
            composite_score=0.85,
            grade="A",
            grade_description="Excellent investment",
            recommended_action="Hold position",
            risk=RiskAssessmentStandardized(score=2.5, level="Medium", risk_factors=["Market volatility", "Sector concentration"]),
            rationale_bullets=["Strong fundamentals"],
            citations=["Yahoo Finance"],
        )

    @pytest.fixture
    def incomplete_holding(self):
        """Create holding with missing critical data."""
        from finwiz.schemas.common import RiskAssessmentStandardized

        return HoldingDecision(
            ticker="BADSTOCK",
            asset_class="stock",
            name="Bad Stock Inc.",
            currency="USD",
            decision="KEEP",
            composite_score=0.50,
            grade="C",
            grade_description="Below average investment",
            recommended_action="Review position",
            risk=RiskAssessmentStandardized(score=3.5, level="High", risk_factors=["High volatility", "Missing data", "Poor fundamentals"]),
            rationale_bullets=["Unknown fundamentals"],
            citations=["Limited data"],
        )

    def test_should_analyze_holding_with_complete_data(self, analyzer, complete_holding):
        """Test that holdings with complete data are analyzed successfully."""
        # Act
        results = analyzer.analyze_portfolio_holdings([complete_holding], session_id="test")

        # Assert
        assert results["successful_analyses"] == 1
        assert results["failed_analyses"] == 0
        assert "AAPL" in results["deep_analysis_results"]
        assert results["deep_analysis_results"]["AAPL"].ticker == "AAPL"

    def test_should_skip_holding_with_missing_critical_fields(self, analyzer, incomplete_holding):
        """Test that holdings with missing critical fields are skipped."""
        # Act
        results = analyzer.analyze_portfolio_holdings([incomplete_holding], session_id="test")

        # Assert
        assert results["successful_analyses"] == 0
        assert results["failed_analyses"] == 1
        assert "BADSTOCK" not in results["deep_analysis_results"]
        assert "skipped_holdings" in results
        assert len(results["skipped_holdings"]) == 1

        # Verify skipped holding details
        skipped = results["skipped_holdings"][0]
        assert skipped["ticker"] == "BADSTOCK"
        assert skipped["asset_class"] == "stock"
        assert "Missing critical fields" in skipped["reason"]

    def test_should_handle_mixed_portfolio(self, analyzer, complete_holding, incomplete_holding):
        """Test handling of portfolio with both complete and incomplete holdings."""
        # Act
        results = analyzer.analyze_portfolio_holdings([complete_holding, incomplete_holding], session_id="test")

        # Assert
        assert results["successful_analyses"] == 1  # AAPL analyzed
        assert results["failed_analyses"] == 1  # BADSTOCK skipped
        assert "AAPL" in results["deep_analysis_results"]
        assert "BADSTOCK" not in results["deep_analysis_results"]
        assert len(results["skipped_holdings"]) == 1

    def test_should_continue_after_skipping_holding(self, analyzer, complete_holding, incomplete_holding):
        """Test that analysis continues after skipping a holding."""
        # Arrange - Create portfolio with incomplete holding first
        holdings = [incomplete_holding, complete_holding]

        # Act
        results = analyzer.analyze_portfolio_holdings(holdings, session_id="test")

        # Assert - Should skip first, analyze second
        assert results["successful_analyses"] == 1
        assert results["failed_analyses"] == 1
        assert "AAPL" in results["deep_analysis_results"]

    def test_should_track_skipped_holdings_separately(self, analyzer, incomplete_holding):
        """Test that skipped holdings are tracked separately from failures."""
        # Act
        results = analyzer.analyze_portfolio_holdings([incomplete_holding], session_id="test")

        # Assert
        assert "skipped_holdings" in results
        skipped = results["skipped_holdings"][0]
        assert "recommendation" in skipped
        assert "Verify data sources" in skipped["recommendation"]

    def test_should_log_skipped_holdings_summary(self, analyzer, incomplete_holding, caplog):
        """Test that skipped holdings are logged in summary."""
        # Act
        results = analyzer.analyze_portfolio_holdings([incomplete_holding], session_id="test")

        # Assert - Check logs contain skipped holdings summary
        assert "SKIPPED HOLDINGS SUMMARY" in caplog.text
        assert "BADSTOCK" in caplog.text
        assert "Missing critical fields" in caplog.text


class TestCriticalFieldErrorPropagation:
    """Test that CriticalFieldError is properly caught and handled."""

    def test_should_catch_critical_field_error_from_scorer(self, mocker):
        """Test that CriticalFieldError from scorer is caught and handled."""
        from finwiz.config.critical_fields_config import CriticalFieldError
        from finwiz.schemas.common import RiskAssessmentStandardized

        # Arrange
        analyzer = PortfolioDeepAnalyzer()
        holding = HoldingDecision(
            ticker="TEST",
            asset_class="stock",
            name="Test",
            currency="USD",
            decision="KEEP",
            composite_score=0.50,
            grade="C",
            grade_description="Test holding",
            recommended_action="Test",
            risk=RiskAssessmentStandardized(score=3.0, level="Medium", risk_factors=["Test risk"]),
            rationale_bullets=["Test"],
            citations=["Test"],
        )

        # Mock scorer to raise CriticalFieldError
        mock_scorer = mocker.patch.object(analyzer, "scorer")
        mock_scorer.calculate_composite_score.side_effect = CriticalFieldError(ticker="TEST", asset_class="stock", missing_fields=["roe", "debt_to_equity"])

        # Mock data extraction to return valid data
        mocker.patch.object(analyzer, "_extract_holding_data", return_value={"current_price": 1.0})

        # Act
        results = analyzer.analyze_portfolio_holdings([holding], session_id="test")

        # Assert
        assert results["failed_analyses"] == 1
        assert "skipped_holdings" in results
        assert len(results["skipped_holdings"]) == 1
        assert results["skipped_holdings"][0]["ticker"] == "TEST"
