"""Predefined stress test scenarios for portfolio analysis."""

from finwiz.schemas.stress_test import StressScenarioType, StressTestScenario

MODERATE_CRASH = StressTestScenario(
    name="Moderate Market Correction",
    scenario_type=StressScenarioType.MARKET_CRASH,
    description="A 15% broad market decline similar to typical corrections",
    market_shock_pct=-0.15,
)

SEVERE_CRASH = StressTestScenario(
    name="Severe Market Crash (2008-style)",
    scenario_type=StressScenarioType.MARKET_CRASH,
    description="A 30% broad market crash similar to 2008 financial crisis",
    market_shock_pct=-0.30,
)

RATE_HIKE_100BPS = StressTestScenario(
    name="Moderate Rate Hike (+100bps)",
    scenario_type=StressScenarioType.RATE_SHOCK,
    description="Central bank raises rates by 100 basis points",
    rate_change_bps=100,
)

RATE_HIKE_300BPS = StressTestScenario(
    name="Aggressive Rate Tightening (+300bps)",
    scenario_type=StressScenarioType.RATE_SHOCK,
    description="Aggressive monetary tightening with 300bps rate increase",
    rate_change_bps=300,
)

TECH_CRASH = StressTestScenario(
    name="Technology Sector Crash",
    scenario_type=StressScenarioType.SECTOR_SHOCK,
    description="Technology sector drops 35% with 8% spillover to other sectors",
    target_sector="Technology",
    sector_shock_pct=-0.35,
    non_target_spillover_pct=-0.08,
)

ENERGY_CRISIS = StressTestScenario(
    name="Energy Crisis",
    scenario_type=StressScenarioType.SECTOR_SHOCK,
    description="Energy sector drops 40% with 10% spillover from supply shock",
    target_sector="Energy",
    sector_shock_pct=-0.40,
    non_target_spillover_pct=-0.10,
)

ALL_SCENARIOS = [MODERATE_CRASH, SEVERE_CRASH, RATE_HIKE_100BPS, RATE_HIKE_300BPS, TECH_CRASH, ENERGY_CRISIS]


def get_default_scenarios() -> list[StressTestScenario]:
    """Get the default set of scenarios for a standard stress test run."""
    return [MODERATE_CRASH, RATE_HIKE_100BPS, TECH_CRASH]
