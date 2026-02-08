"""Tests for predefined stress test scenarios."""

from finwiz.quantitative.stress_testing.scenarios import (
    ALL_SCENARIOS,
    ENERGY_CRISIS,
    MODERATE_CRASH,
    RATE_HIKE_100BPS,
    SEVERE_CRASH,
    TECH_CRASH,
    get_default_scenarios,
)
from finwiz.schemas.stress_test import StressScenarioType


class TestPredefinedScenarios:
    def test_moderate_crash(self):
        assert MODERATE_CRASH.market_shock_pct == -0.15
        assert MODERATE_CRASH.scenario_type == StressScenarioType.MARKET_CRASH

    def test_severe_crash(self):
        assert SEVERE_CRASH.market_shock_pct == -0.30

    def test_rate_hike(self):
        assert RATE_HIKE_100BPS.rate_change_bps == 100
        assert RATE_HIKE_100BPS.scenario_type == StressScenarioType.RATE_SHOCK

    def test_tech_crash(self):
        assert TECH_CRASH.target_sector == "Technology"
        assert TECH_CRASH.sector_shock_pct == -0.35
        assert TECH_CRASH.non_target_spillover_pct == -0.08

    def test_energy_crisis(self):
        assert ENERGY_CRISIS.target_sector == "Energy"
        assert ENERGY_CRISIS.sector_shock_pct == -0.40

    def test_all_scenarios_count(self):
        assert len(ALL_SCENARIOS) == 6

    def test_get_default_scenarios(self):
        defaults = get_default_scenarios()
        assert len(defaults) == 3
        names = [s.name for s in defaults]
        assert "Moderate Market Correction" in names
        assert "Technology Sector Crash" in names
