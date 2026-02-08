"""Tests for stress test schema models."""

from finwiz.schemas.stress_test import (
    HoldingStressImpact,
    PortfolioStressTestResult,
    StressScenarioType,
    StressTestScenario,
)


class TestStressTestSchemas:
    def test_scenario_type_values(self):
        assert StressScenarioType.MARKET_CRASH == "market_crash"
        assert StressScenarioType.RATE_SHOCK == "rate_shock"
        assert StressScenarioType.SECTOR_SHOCK == "sector_shock"

    def test_scenario_creation(self):
        s = StressTestScenario(
            name="Test Crash",
            scenario_type=StressScenarioType.MARKET_CRASH,
            description="A test scenario",
            market_shock_pct=-0.20,
        )
        assert s.name == "Test Crash"
        assert s.market_shock_pct == -0.20
        assert s.target_sector is None

    def test_holding_impact(self):
        h = HoldingStressImpact(
            ticker="AAPL",
            asset_type="stock",
            sector="Technology",
            beta=1.2,
            current_weight_pct=5.0,
            projected_change_pct=-0.24,
            sensitivity_label="HIGH",
        )
        assert h.ticker == "AAPL"
        assert h.projected_change_pct == -0.24

    def test_portfolio_result(self):
        scenario = StressTestScenario(name="Test", scenario_type=StressScenarioType.MARKET_CRASH, description="test", market_shock_pct=-0.10)
        r = PortfolioStressTestResult(
            scenario=scenario,
            total_portfolio_impact_pct=-0.12,
            most_affected=["AAPL"],
            least_affected=["BND"],
        )
        assert r.total_portfolio_impact_pct == -0.12
        assert len(r.holding_impacts) == 0
