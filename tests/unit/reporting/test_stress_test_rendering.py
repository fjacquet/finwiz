"""Tests for stress test section rendering in HTML report."""

from finwiz.reporting.section_generators import generate_stress_test_section


def _make_stress_result(
    name: str = "Market Crash -20%",
    description: str = "Simulates a 20% broad market decline",
    scenario_type: str = "market_crash",
    impact_pct: float = -0.12,
    projected_pnl: float = -24000.0,
    holding_impacts: list | None = None,
    most_affected: list | None = None,
    least_affected: list | None = None,
) -> dict:
    """Build a sample PortfolioStressTestResult dict for testing."""
    if holding_impacts is None:
        holding_impacts = [
            {
                "ticker": "AAPL",
                "asset_type": "stock",
                "sector": "Technology",
                "beta": 1.25,
                "current_weight_pct": 8.0,
                "projected_change_pct": -0.25,
                "projected_pnl": -5000.0,
                "sensitivity_label": "HIGH",
            },
            {
                "ticker": "JNJ",
                "asset_type": "stock",
                "sector": "Healthcare",
                "beta": 0.65,
                "current_weight_pct": 4.0,
                "projected_change_pct": -0.06,
                "projected_pnl": -600.0,
                "sensitivity_label": "LOW",
            },
            {
                "ticker": "XOM",
                "asset_type": "stock",
                "sector": "Energy",
                "beta": 0.95,
                "current_weight_pct": 5.0,
                "projected_change_pct": -0.10,
                "projected_pnl": -1000.0,
                "sensitivity_label": "MEDIUM",
            },
        ]
    return {
        "scenario": {
            "name": name,
            "description": description,
            "scenario_type": scenario_type,
            "market_shock_pct": -0.20,
            "rate_change_bps": 0,
            "target_sector": None,
            "sector_shock_pct": 0.0,
            "non_target_spillover_pct": 0.0,
        },
        "total_portfolio_impact_pct": impact_pct,
        "total_projected_pnl": projected_pnl,
        "holding_impacts": holding_impacts,
        "most_affected": most_affected or ["AAPL", "XOM"],
        "least_affected": least_affected or ["JNJ"],
        "run_timestamp": "2026-02-08T12:00:00Z",
    }


class TestStressTestSectionRendersWithData:
    """Verify stress test section renders correctly with data."""

    def test_contains_scenario_name(self):
        html = generate_stress_test_section([_make_stress_result()])
        assert "Market Crash -20%" in html

    def test_contains_section_header(self):
        html = generate_stress_test_section([_make_stress_result()])
        assert "Analyse de Stress du Portefeuille" in html

    def test_contains_impact_percentage(self):
        html = generate_stress_test_section([_make_stress_result(impact_pct=-0.12)])
        assert "-12.0%" in html

    def test_contains_holding_tickers(self):
        html = generate_stress_test_section([_make_stress_result()])
        assert "AAPL" in html
        assert "JNJ" in html
        assert "XOM" in html

    def test_contains_sensitivity_labels(self):
        html = generate_stress_test_section([_make_stress_result()])
        assert "HIGH" in html
        assert "MEDIUM" in html
        assert "LOW" in html

    def test_contains_most_and_least_affected(self):
        html = generate_stress_test_section([_make_stress_result()])
        assert "Plus affectes" in html
        assert "Moins affectes" in html

    def test_contains_projected_pnl(self):
        html = generate_stress_test_section([_make_stress_result(projected_pnl=-24000.0)])
        assert "-24,000" in html

    def test_renders_multiple_scenarios(self):
        results = [
            _make_stress_result(name="Crash"),
            _make_stress_result(name="Rate Shock"),
        ]
        html = generate_stress_test_section(results)
        assert "Crash" in html
        assert "Rate Shock" in html


class TestStressTestSectionEmptyWhenNoData:
    """Verify section returns empty string when no data."""

    def test_returns_empty_for_none(self):
        assert generate_stress_test_section(None) == ""

    def test_returns_empty_for_empty_list(self):
        assert generate_stress_test_section([]) == ""


class TestStressTestSectionColorCoding:
    """Verify color coding for sensitivity and impact."""

    def test_high_sensitivity_has_red(self):
        html = generate_stress_test_section([_make_stress_result()])
        # HIGH sensitivity should have red color (#dc3545)
        assert "dc3545" in html

    def test_low_sensitivity_has_green(self):
        html = generate_stress_test_section([_make_stress_result()])
        # LOW sensitivity should have green color (#28a745)
        assert "28a745" in html

    def test_medium_sensitivity_has_orange(self):
        html = generate_stress_test_section([_make_stress_result()])
        # MEDIUM sensitivity should have orange color (#fd7e14)
        assert "fd7e14" in html

    def test_large_impact_colored_red(self):
        """Impact > 15% should be red."""
        html = generate_stress_test_section([_make_stress_result(impact_pct=-0.20)])
        # -20% total impact should be red
        assert "-20.0%" in html
        assert "dc3545" in html

    def test_small_impact_colored_green(self):
        """Impact < 5% should be green."""
        html = generate_stress_test_section([_make_stress_result(impact_pct=-0.03)])
        assert "-3.0%" in html
        assert "28a745" in html
