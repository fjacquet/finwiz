"""Tests for reporting/report_section_generators.py module."""

from datetime import datetime

from finwiz.reporting.section_generators import (
    _get_recommendation_badge,
    generate_deep_analysis_section,
    generate_discovery_section,
    generate_executive_summary,
    generate_holdings_analysis,
    generate_performance_metrics,
    generate_portfolio_overview,
    generate_recommendations,
)
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import HoldingDecision, PortfolioReview


def _make_risk(score: float = 2.5, level: str = "Medium") -> RiskAssessmentStandardized:
    """Create a valid RiskAssessmentStandardized object for testing."""
    return RiskAssessmentStandardized(score=score, level=level)


def _make_holding(
    ticker: str = "TEST",
    name: str = "Test Company",
    asset_class: str = "stock",
    grade: str = "B",
    composite_score: float = 0.7,
    recommended_action: str = "HOLD",
    rationale_bullets: list | None = None,
) -> HoldingDecision:
    """Create a valid HoldingDecision object for testing."""
    return HoldingDecision(
        ticker=ticker,
        name=name,
        asset_class=asset_class,
        currency="USD",
        decision="KEEP",
        composite_score=composite_score,
        grade=grade,
        grade_description=f"Grade {grade} holding",
        recommended_action=recommended_action,
        risk=_make_risk(),
        rationale_bullets=rationale_bullets or [],
    )


def _make_portfolio_review(holdings: list | None = None) -> PortfolioReview:
    """Create a valid PortfolioReview object for testing."""
    return PortfolioReview(
        as_of=datetime.now(),
        holdings=holdings or [],
    )


class TestGenerateExecutiveSummary:
    """Tests for generate_executive_summary function."""

    def test_should_generate_summary_with_all_stats(self):
        """Test generation of executive summary with complete stats."""
        stats = {
            "portfolio_grade": "A",
            "average_score": 0.85,
            "total_holdings": 10,
            "a_plus_count": 3,
            "underperforming_count": 2,
            "recommendation_counts": {"BUY": 5, "HOLD": 3, "SELL": 2},
        }
        html = generate_executive_summary(stats)
        assert "Executive Summary" in html
        assert "Portfolio Grade" in html
        assert "grade-a" in html
        assert "0.850" in html
        assert "10" in html  # Total positions

    def test_should_handle_a_plus_grade(self):
        """Test that A+ grade is formatted correctly."""
        stats = {
            "portfolio_grade": "A+",
            "average_score": 0.95,
            "total_holdings": 5,
            "a_plus_count": 5,
            "underperforming_count": 0,
            "recommendation_counts": {"BUY": 5, "HOLD": 0, "SELL": 0},
        }
        html = generate_executive_summary(stats)
        assert "grade-a-plus" in html
        assert "A+" in html

    def test_should_display_sell_count(self):
        """Test that SELL count is displayed correctly."""
        stats = {
            "portfolio_grade": "B",
            "average_score": 0.65,
            "total_holdings": 20,
            "a_plus_count": 2,
            "underperforming_count": 8,
            "recommendation_counts": {"BUY": 2, "HOLD": 10, "SELL": 8},
        }
        html = generate_executive_summary(stats)
        assert "8" in html  # SELL count
        assert "SELL Recommendations" in html


class TestGeneratePortfolioOverview:
    """Tests for generate_portfolio_overview function."""

    def test_should_generate_overview_with_asset_distribution(self):
        """Test generation of portfolio overview with asset distribution."""
        review = _make_portfolio_review()
        stats = {
            "total_holdings": 10,
            "asset_counts": {"stock": 5, "etf": 3, "crypto": 2},
            "grade_counts": {"A+": 1, "A": 2, "B": 3, "C": 2, "D": 1, "F": 1},
        }
        html = generate_portfolio_overview(review, stats)
        assert "Portfolio Overview" in html
        assert "Asset Class Distribution" in html
        assert "Grade Distribution" in html

    def test_should_calculate_percentages_correctly(self):
        """Test that percentages are calculated correctly."""
        review = _make_portfolio_review()
        stats = {
            "total_holdings": 10,
            "asset_counts": {"stock": 5, "etf": 3, "crypto": 2},
            "grade_counts": {"A+": 2, "A": 3, "B": 3, "C": 1, "D": 1, "F": 0},
        }
        html = generate_portfolio_overview(review, stats)
        assert "50.0%" in html  # 5/10 stocks
        assert "30.0%" in html  # 3/10 ETFs

    def test_should_handle_zero_total_holdings(self):
        """Test handling of zero total holdings (edge case)."""
        review = _make_portfolio_review()
        stats = {
            "total_holdings": 0,
            "asset_counts": {"stock": 0, "etf": 0, "crypto": 0},
            "grade_counts": {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
        }
        html = generate_portfolio_overview(review, stats)
        assert "0.0%" in html


class TestGetRecommendationBadge:
    """Tests for _get_recommendation_badge function."""

    def test_should_return_buy_badge_for_a_plus(self):
        """Test BUY badge for A+ grade."""
        badge = _get_recommendation_badge("A+", None)
        assert "badge-buy" in badge
        assert "BUY" in badge

    def test_should_return_buy_badge_for_a(self):
        """Test BUY badge for A grade."""
        badge = _get_recommendation_badge("A", None)
        assert "badge-buy" in badge
        assert "BUY" in badge

    def test_should_return_sell_badge_for_d(self):
        """Test SELL badge for D grade."""
        badge = _get_recommendation_badge("D", None)
        assert "badge-sell" in badge
        assert "SELL" in badge

    def test_should_return_sell_badge_for_f(self):
        """Test SELL badge for F grade."""
        badge = _get_recommendation_badge("F", None)
        assert "badge-sell" in badge
        assert "SELL" in badge

    def test_should_return_sell_badge_for_na(self):
        """Test SELL badge for N/A grade."""
        badge = _get_recommendation_badge("N/A", None)
        assert "badge-sell" in badge
        assert "SELL" in badge

    def test_should_return_hold_badge_for_b(self):
        """Test HOLD badge for B grade."""
        badge = _get_recommendation_badge("B", None)
        assert "badge-hold" in badge
        assert "HOLD" in badge

    def test_should_return_hold_badge_for_c(self):
        """Test HOLD badge for C grade."""
        badge = _get_recommendation_badge("C", None)
        assert "badge-hold" in badge
        assert "HOLD" in badge

    def test_should_fallback_to_recommended_action_buy(self):
        """Test fallback to recommended_action with BUY."""
        badge = _get_recommendation_badge("X", "STRONG BUY")
        assert "badge-buy" in badge
        assert "BUY" in badge

    def test_should_fallback_to_recommended_action_sell(self):
        """Test fallback to recommended_action with SELL."""
        badge = _get_recommendation_badge("X", "SELL")
        assert "badge-sell" in badge
        assert "SELL" in badge

    def test_should_default_to_hold_for_unknown(self):
        """Test default HOLD badge for unknown grade."""
        badge = _get_recommendation_badge("X", None)
        assert "badge-hold" in badge
        assert "HOLD" in badge


class TestGenerateHoldingsAnalysis:
    """Tests for generate_holdings_analysis function."""

    def test_should_generate_empty_table_for_no_holdings(self):
        """Test generation of empty holdings table."""
        html = generate_holdings_analysis([])
        assert "Detailed Holdings Analysis" in html
        assert "<tbody>" in html

    def test_should_generate_holdings_rows(self):
        """Test generation of holdings rows."""
        holdings = [
            _make_holding(
                ticker="AAPL",
                name="Apple Inc.",
                asset_class="stock",
                grade="A",
                composite_score=0.85,
                recommended_action="BUY",
                rationale_bullets=["Strong fundamentals"],
            ),
            _make_holding(
                ticker="GOOGL",
                name="Alphabet Inc.",
                asset_class="stock",
                grade="B",
                composite_score=0.72,
                recommended_action="HOLD",
                rationale_bullets=["Stable growth"],
            ),
        ]
        html = generate_holdings_analysis(holdings)
        assert "AAPL" in html
        assert "Apple Inc." in html
        assert "GOOGL" in html
        assert "0.850" in html  # Score formatted to 3 decimals

    def test_should_sort_holdings_by_grade_and_score(self):
        """Test that holdings are sorted by grade and score."""
        holdings = [
            _make_holding(ticker="BAD", grade="F", composite_score=0.2),
            _make_holding(ticker="BEST", grade="A+", composite_score=0.95),
            _make_holding(ticker="GOOD", grade="A", composite_score=0.85),
        ]
        html = generate_holdings_analysis(holdings)
        # A+ should appear before A, which should appear before F
        a_plus_pos = html.find("A+")
        a_pos = html.find('grade-a">')
        f_pos = html.find("grade-f")
        assert a_plus_pos < f_pos

    def test_should_handle_minimal_holding(self):
        """Test handling of holdings with minimal but valid data."""
        holdings = [
            _make_holding(
                ticker="MIN",
                name="Minimal",
                grade="C",
                composite_score=0.5,
            ),
        ]
        html = generate_holdings_analysis(holdings)
        assert "MIN" in html
        assert "0.500" in html


class TestGenerateRecommendations:
    """Tests for generate_recommendations function."""

    def test_should_generate_recommendations_section(self):
        """Test generation of recommendations section."""
        stats = {
            "recommendation_counts": {"SELL": 3, "BUY": 5, "HOLD": 2},
            "a_plus_count": 5,
            "a_plus_holdings": [],
        }
        html = generate_recommendations(stats)
        assert "Strategic Recommendations" in html
        assert "Priority Actions" in html
        assert "3" in html  # SELL count

    def test_should_display_a_plus_holdings(self):
        """Test display of A+ holdings in recommendations."""
        holding = _make_holding(ticker="AAPL", grade="A+", composite_score=0.95)
        stats = {
            "recommendation_counts": {"SELL": 0, "BUY": 1, "HOLD": 0},
            "a_plus_count": 1,
            "a_plus_holdings": [holding],
        }
        html = generate_recommendations(stats)
        assert "AAPL" in html
        assert "A+" in html
        assert "0.950" in html

    def test_should_display_discovery_count(self):
        """Test display of discovery opportunities count."""
        stats = {
            "recommendation_counts": {"SELL": 0, "BUY": 0, "HOLD": 0},
            "a_plus_count": 0,
            "a_plus_holdings": [],
        }
        discovery = {"opportunities": [{"ticker": "NEW1"}, {"ticker": "NEW2"}]}
        html = generate_recommendations(stats, discovery)
        assert "2" in html  # Discovery count

    def test_should_handle_no_discovery_results(self):
        """Test handling when no discovery results available."""
        stats = {
            "recommendation_counts": {"SELL": 0, "BUY": 0, "HOLD": 0},
            "a_plus_count": 0,
            "a_plus_holdings": [],
        }
        html = generate_recommendations(stats, None)
        assert "0" in html  # Zero discoveries


class TestGenerateDeepAnalysisSection:
    """Tests for generate_deep_analysis_section function."""

    def test_should_generate_not_available_message_when_none(self):
        """Test generation of not available message when results are None."""
        html = generate_deep_analysis_section(None)
        assert "Deep Analysis" in html
        assert "not available" in html
        assert "DEEP_PORTFOLIO_ANALYSIS=true" in html

    def test_should_generate_stats_when_results_available(self):
        """Test generation of stats when results are available."""
        results = {
            "successful_analyses": 8,
            "failed_analyses": 2,
            "total_holdings": 10,
        }
        html = generate_deep_analysis_section(results)
        assert "Python Deep Analysis" in html
        assert "8" in html  # Successful
        assert "2" in html  # Failed
        assert "80.0%" in html  # Success rate

    def test_should_display_no_analysis_needed_message(self):
        """Test message when all holdings have good grades."""
        results = {
            "successful_analyses": 0,
            "failed_analyses": 0,
            "total_holdings": 5,
        }
        html = generate_deep_analysis_section(results)
        assert "No Deep Analysis Needed" in html

    def test_should_display_completed_message(self):
        """Test completed message when analyses run."""
        results = {
            "successful_analyses": 5,
            "failed_analyses": 0,
            "total_holdings": 5,
        }
        html = generate_deep_analysis_section(results)
        assert "Deep Analysis Completed" in html


class TestGeneratePerformanceMetrics:
    """Tests for generate_performance_metrics function."""

    def test_should_generate_not_available_when_none(self):
        """Test generation of not available message when results are None."""
        html = generate_performance_metrics(None)
        assert "Performance Metrics" in html
        assert "not available" in html

    def test_should_generate_not_available_when_no_metrics(self):
        """Test generation of not available when no metrics key."""
        html = generate_performance_metrics({"other_data": "value"})
        assert "not available" in html

    def test_should_display_performance_stats(self):
        """Test display of performance statistics."""
        results = {
            "performance_metrics": {
                "total_execution_time_seconds": 45.5,
                "average_time_per_holding": 4.55,
                "llm_calls_made": 0,
                "estimated_cost_usd": 0.0,
                "speedup_vs_ai": "15x",
                "cost_reduction": "100%",
                "holdings_per_second": 2.2,
            }
        }
        html = generate_performance_metrics(results)
        assert "Performance Metrics" in html
        assert "45.5s" in html  # Total time
        assert "4.55s" in html  # Average time
        assert "$0.00" in html  # Cost

    def test_should_display_efficiency_metrics(self):
        """Test display of efficiency metrics."""
        results = {
            "performance_metrics": {
                "total_execution_time_seconds": 10,
                "average_time_per_holding": 1,
                "llm_calls_made": 0,
                "estimated_cost_usd": 0,
                "speedup_vs_ai": "20x",
                "cost_reduction": "100%",
                "holdings_per_second": 10.0,
            }
        }
        html = generate_performance_metrics(results)
        assert "Exceptional Performance" in html
        assert "20x" in html  # Speedup
        assert "10.0" in html  # Holdings per second


class TestGenerateDiscoverySection:
    """Tests for generate_discovery_section function."""

    def test_should_generate_not_available_when_none(self):
        """Test generation of not available message when results are None."""
        html = generate_discovery_section(None)
        assert "Discovered Opportunities" in html
        assert "No new opportunities discovered" in html

    def test_should_generate_not_available_when_no_opportunities(self):
        """Test generation of not available when no opportunities key."""
        html = generate_discovery_section({"other_data": "value"})
        assert "No new opportunities discovered" in html

    def test_should_display_opportunities_list(self):
        """Test display of discovered opportunities."""
        results = {
            "opportunities": [
                {
                    "ticker": "NEW1",
                    "name": "New Company 1",
                    "grade": "A+",
                    "composite_score": 0.92,
                    "recommendation": "BUY",
                    "rationale": "Excellent growth potential",
                },
                {
                    "ticker": "NEW2",
                    "name": "New Company 2",
                    "grade": "A",
                    "composite_score": 0.88,
                    "recommendation": "BUY",
                    "rationale": "Strong fundamentals",
                },
            ]
        }
        html = generate_discovery_section(results)
        assert "2 New Opportunities Identified" in html
        assert "NEW1" in html
        assert "NEW2" in html
        assert "0.920" in html  # Score

    def test_should_classify_opportunities_by_type(self):
        """Test classification of opportunities by asset class."""
        results = {
            "opportunities": [
                {"ticker": "AAPL", "name": "Apple", "grade": "A+", "composite_score": 0.9},
                {"ticker": "SPY", "name": "S&P 500 ETF", "grade": "A", "composite_score": 0.85},
                {"ticker": "BTC", "name": "Bitcoin", "grade": "A+", "composite_score": 0.88},
            ]
        }
        html = generate_discovery_section(results)
        # Check that classification counts are displayed
        assert "Stocks:" in html
        assert "ETFs:" in html
        assert "Crypto:" in html

    def test_should_truncate_long_rationale(self):
        """Test that long rationales are truncated."""
        long_rationale = "A" * 200
        results = {
            "opportunities": [
                {
                    "ticker": "TEST",
                    "name": "Test",
                    "grade": "A+",
                    "composite_score": 0.9,
                    "rationale": long_rationale,
                }
            ]
        }
        html = generate_discovery_section(results)
        assert "..." in html  # Truncated indicator

    def test_should_display_usage_instructions(self):
        """Test display of how to use opportunities."""
        results = {"opportunities": [{"ticker": "TEST", "grade": "A+", "composite_score": 0.9}]}
        html = generate_discovery_section(results)
        assert "How to Use These Opportunities" in html
        assert "Replacement" in html
        assert "Diversification" in html
        assert "DCA" in html

    def test_conviction_picks_renders_when_a_grades_present(self):
        """Conviction Picks callout appears when at least one A/A+ candidate exists."""
        results = {
            "opportunities": [
                {"ticker": "LRCX", "name": "Lam Research", "grade": "A", "composite_score": 0.88},
                {"ticker": "GOOG", "name": "Alphabet", "grade": "B+", "composite_score": 0.82},
                {"ticker": "AMD", "name": "AMD", "grade": "C+", "composite_score": 0.71},
            ]
        }
        html = generate_discovery_section(results)
        assert "Conviction Picks" in html
        assert "1 A/A+ Candidates" in html
        # A/A+ picks appear ahead of the broader table — LRCX in conviction block
        conviction_idx = html.index("Conviction Picks")
        main_list_idx = html.index("Discovered Opportunities List")
        assert conviction_idx < main_list_idx

    def test_conviction_picks_hidden_when_no_a_grades(self):
        """No callout when every candidate is B or lower."""
        results = {
            "opportunities": [
                {"ticker": "GOOG", "name": "Alphabet", "grade": "B+", "composite_score": 0.82},
                {"ticker": "AMD", "name": "AMD", "grade": "C+", "composite_score": 0.71},
            ]
        }
        html = generate_discovery_section(results)
        assert "Conviction Picks" not in html

    def test_conviction_picks_sorts_by_score_descending(self):
        """Multiple A/A+ candidates are ordered by composite_score."""
        results = {
            "opportunities": [
                {"ticker": "MID", "name": "Mid", "grade": "A", "composite_score": 0.87},
                {"ticker": "TOP", "name": "Top", "grade": "A+", "composite_score": 0.96},
                {"ticker": "LOW", "name": "Low", "grade": "A", "composite_score": 0.85},
            ]
        }
        html = generate_discovery_section(results)
        conviction_block = html.split("Discovered Opportunities List")[0]
        assert conviction_block.index("TOP") < conviction_block.index("MID") < conviction_block.index("LOW")


class TestEdgeCases:
    """Test edge cases for report section generators."""

    def test_executive_summary_with_special_characters_in_grade(self):
        """Test executive summary with special characters in grade."""
        stats = {
            "portfolio_grade": "B+",
            "average_score": 0.75,
            "total_holdings": 5,
            "a_plus_count": 0,
            "underperforming_count": 1,
            "recommendation_counts": {"BUY": 2, "HOLD": 2, "SELL": 1},
        }
        html = generate_executive_summary(stats)
        assert "b-plus" in html  # Grade class formatting

    def test_holdings_analysis_with_empty_rationale(self):
        """Test holdings analysis with empty rationale bullets."""
        holdings = [
            _make_holding(
                ticker="TEST",
                grade="B",
                composite_score=0.7,
                rationale_bullets=[],
            )
        ]
        html = generate_holdings_analysis(holdings)
        assert "Python analysis" in html  # Fallback rationale

    def test_discovery_section_with_missing_fields(self):
        """Test discovery section with opportunities missing fields."""
        results = {
            "opportunities": [
                {"ticker": "MINIMAL"},  # Missing most fields
            ]
        }
        html = generate_discovery_section(results)
        assert "MINIMAL" in html
        assert "N/A" in html  # Default name
