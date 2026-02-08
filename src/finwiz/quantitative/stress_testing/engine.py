"""Portfolio stress test engine with scenario-based impact calculations.

All calculations are deterministic Python (AI Minimalism principle).
Uses beta-adjusted returns for market crashes, duration-based impact
for rate shocks, and sector mapping for sector-specific shocks.
"""

from datetime import datetime
from typing import Any

from finwiz.schemas.stress_test import (
    HoldingStressImpact,
    PortfolioStressTestResult,
    StressScenarioType,
    StressTestScenario,
)
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Sectors sensitive to interest rate changes
_RATE_SENSITIVE_GROWTH = {"Technology", "Communication Services", "Consumer Discretionary"}
_RATE_SENSITIVE_FIXED = {"Real Estate", "Utilities"}
_RATE_BENEFICIARIES = {"Financials"}


class PortfolioStressTestEngine:
    """Runs stress scenarios against a portfolio of holdings.

    Each holding dict must contain:
        ticker: str
        weight: float (portfolio weight as decimal, e.g. 0.05 for 5%)
        asset_type: str ("stock", "etf", "crypto")

    Optional fields:
        sector: str (GICS sector name)
        beta: float (market beta, default 1.0)
        duration: float (bond duration in years, for rate shock)
    """

    def __init__(self, holdings: list[dict[str, Any]]) -> None:
        self.holdings = holdings
        self.logger = logger

    def run_scenario(self, scenario: StressTestScenario) -> PortfolioStressTestResult:
        """Run a single stress scenario and return portfolio-level results."""
        impacts: list[HoldingStressImpact] = []

        for holding in self.holdings:
            if scenario.scenario_type == StressScenarioType.MARKET_CRASH:
                impact = self._apply_market_crash(holding, scenario)
            elif scenario.scenario_type == StressScenarioType.RATE_SHOCK:
                impact = self._apply_rate_shock(holding, scenario)
            elif scenario.scenario_type == StressScenarioType.SECTOR_SHOCK:
                impact = self._apply_sector_shock(holding, scenario)
            else:
                continue
            impacts.append(impact)

        # Weighted portfolio impact
        total_impact = sum(i.projected_change_pct * i.current_weight_pct / 100 for i in impacts)

        # Sort by absolute impact for most/least affected
        sorted_impacts = sorted(impacts, key=lambda i: abs(i.projected_change_pct), reverse=True)
        most_affected = [i.ticker for i in sorted_impacts[:3]]
        least_affected = [i.ticker for i in sorted_impacts[-3:]] if len(sorted_impacts) >= 3 else []

        return PortfolioStressTestResult(
            scenario=scenario,
            total_portfolio_impact_pct=total_impact,
            holding_impacts=impacts,
            most_affected=most_affected,
            least_affected=least_affected,
            run_timestamp=datetime.now().isoformat(),
        )

    def run_all_predefined(self) -> list[PortfolioStressTestResult]:
        """Run all predefined default scenarios."""
        from finwiz.quantitative.stress_testing.scenarios import get_default_scenarios

        results = []
        for scenario in get_default_scenarios():
            try:
                result = self.run_scenario(scenario)
                results.append(result)
                self.logger.info(f"Stress Test: {scenario.name} -- portfolio impact: {result.total_portfolio_impact_pct:.1%}")
            except Exception as e:
                self.logger.warning(f"Stress test '{scenario.name}' failed: {e}")
        return results

    def _apply_market_crash(self, holding: dict, scenario: StressTestScenario) -> HoldingStressImpact:
        """Beta-adjusted market crash impact."""
        beta = holding.get("beta", 1.0) or 1.0
        asset_type = holding.get("asset_type", "stock")

        # Crypto is more volatile (1.5x multiplier)
        multiplier = 1.5 if asset_type == "crypto" else 1.0
        # Bonds have inverse/reduced correlation
        if asset_type == "bond":
            multiplier = -0.3

        change_pct = scenario.market_shock_pct * beta * multiplier

        return HoldingStressImpact(
            ticker=holding["ticker"],
            asset_type=asset_type,
            sector=holding.get("sector"),
            beta=beta,
            current_weight_pct=holding.get("weight", 0) * 100,
            projected_change_pct=change_pct,
            sensitivity_label=self._classify_sensitivity(change_pct),
        )

    def _apply_rate_shock(self, holding: dict, scenario: StressTestScenario) -> HoldingStressImpact:
        """Duration and sector-based rate shock impact."""
        asset_type = holding.get("asset_type", "stock")
        sector = holding.get("sector", "Unknown")
        duration = holding.get("duration", 0.0) or 0.0
        rate_decimal = scenario.rate_change_bps / 10000

        if asset_type in ("bond", "fixed_income") or duration > 0:
            # Fixed income: price drops with rate * duration
            change_pct = -duration * rate_decimal
        elif sector in _RATE_SENSITIVE_GROWTH:
            # Growth stocks hurt by higher rates (DCF discount)
            change_pct = -rate_decimal * 5  # ~5x rate sensitivity
        elif sector in _RATE_SENSITIVE_FIXED:
            # REITs, utilities hurt by higher rates
            change_pct = -rate_decimal * 4
        elif sector in _RATE_BENEFICIARIES:
            # Banks benefit from wider spreads
            change_pct = rate_decimal * 2
        elif asset_type == "crypto":
            # Crypto hurt by tighter monetary conditions
            change_pct = -rate_decimal * 8
        else:
            # Generic equity: mild negative
            change_pct = -rate_decimal * 2

        return HoldingStressImpact(
            ticker=holding["ticker"],
            asset_type=asset_type,
            sector=sector,
            beta=holding.get("beta"),
            current_weight_pct=holding.get("weight", 0) * 100,
            projected_change_pct=change_pct,
            sensitivity_label=self._classify_sensitivity(change_pct),
        )

    def _apply_sector_shock(self, holding: dict, scenario: StressTestScenario) -> HoldingStressImpact:
        """Sector-specific shock with spillover to other sectors."""
        sector = holding.get("sector", "Unknown")

        if sector == scenario.target_sector:
            change_pct = scenario.sector_shock_pct
        else:
            change_pct = scenario.non_target_spillover_pct

        return HoldingStressImpact(
            ticker=holding["ticker"],
            asset_type=holding.get("asset_type", "stock"),
            sector=sector,
            beta=holding.get("beta"),
            current_weight_pct=holding.get("weight", 0) * 100,
            projected_change_pct=change_pct,
            sensitivity_label=self._classify_sensitivity(change_pct),
        )

    @staticmethod
    def _classify_sensitivity(impact_pct: float) -> str:
        """Classify impact magnitude into sensitivity label."""
        abs_impact = abs(impact_pct)
        if abs_impact >= 0.15:
            return "HIGH"
        if abs_impact >= 0.05:
            return "MEDIUM"
        return "LOW"
