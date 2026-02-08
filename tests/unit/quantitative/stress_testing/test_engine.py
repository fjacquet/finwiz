"""Tests for PortfolioStressTestEngine."""

import pytest

from finwiz.quantitative.stress_testing.engine import PortfolioStressTestEngine
from finwiz.schemas.stress_test import StressScenarioType, StressTestScenario


def _stock(ticker: str, weight: float = 0.05, beta: float = 1.0, sector: str = "Technology") -> dict:
    return {"ticker": ticker, "weight": weight, "asset_type": "stock", "beta": beta, "sector": sector}


def _crypto(ticker: str, weight: float = 0.02) -> dict:
    return {"ticker": ticker, "weight": weight, "asset_type": "crypto", "beta": 1.0}


CRASH = StressTestScenario(name="Crash", scenario_type=StressScenarioType.MARKET_CRASH, description="test", market_shock_pct=-0.20)
RATE = StressTestScenario(name="Rate", scenario_type=StressScenarioType.RATE_SHOCK, description="test", rate_change_bps=200)
SECTOR = StressTestScenario(
    name="Sector",
    scenario_type=StressScenarioType.SECTOR_SHOCK,
    description="test",
    target_sector="Technology",
    sector_shock_pct=-0.35,
    non_target_spillover_pct=-0.05,
)


class TestMarketCrash:
    def test_high_beta_more_impact(self):
        holdings = [_stock("AAPL", beta=1.5), _stock("KO", beta=0.6)]
        engine = PortfolioStressTestEngine(holdings)
        result = engine.run_scenario(CRASH)

        impacts = {i.ticker: i for i in result.holding_impacts}
        assert abs(impacts["AAPL"].projected_change_pct) > abs(impacts["KO"].projected_change_pct)

    def test_crypto_amplified(self):
        holdings = [_stock("AAPL", beta=1.0), _crypto("BTC")]
        engine = PortfolioStressTestEngine(holdings)
        result = engine.run_scenario(CRASH)

        impacts = {i.ticker: i for i in result.holding_impacts}
        # Crypto has 1.5x multiplier vs stock at same beta
        assert abs(impacts["BTC"].projected_change_pct) > abs(impacts["AAPL"].projected_change_pct)

    def test_portfolio_impact_weighted(self):
        holdings = [_stock("AAPL", weight=1.0, beta=1.0)]  # 100% weight
        engine = PortfolioStressTestEngine(holdings)
        result = engine.run_scenario(CRASH)
        assert result.total_portfolio_impact_pct == pytest.approx(-0.20)


class TestRateShock:
    def test_growth_hurt_by_rates(self):
        holdings = [_stock("AAPL", sector="Technology")]
        engine = PortfolioStressTestEngine(holdings)
        result = engine.run_scenario(RATE)
        assert result.holding_impacts[0].projected_change_pct < 0

    def test_financials_benefit(self):
        holdings = [_stock("JPM", sector="Financials")]
        engine = PortfolioStressTestEngine(holdings)
        result = engine.run_scenario(RATE)
        assert result.holding_impacts[0].projected_change_pct > 0

    def test_crypto_hurt_by_rates(self):
        holdings = [_crypto("BTC")]
        engine = PortfolioStressTestEngine(holdings)
        result = engine.run_scenario(RATE)
        assert result.holding_impacts[0].projected_change_pct < 0


class TestSectorShock:
    def test_target_sector_full_impact(self):
        holdings = [_stock("AAPL", sector="Technology")]
        engine = PortfolioStressTestEngine(holdings)
        result = engine.run_scenario(SECTOR)
        assert result.holding_impacts[0].projected_change_pct == -0.35

    def test_non_target_spillover(self):
        holdings = [_stock("XOM", sector="Energy")]
        engine = PortfolioStressTestEngine(holdings)
        result = engine.run_scenario(SECTOR)
        assert result.holding_impacts[0].projected_change_pct == -0.05


class TestSensitivityClassification:
    def test_high(self):
        assert PortfolioStressTestEngine._classify_sensitivity(-0.20) == "HIGH"

    def test_medium(self):
        assert PortfolioStressTestEngine._classify_sensitivity(-0.10) == "MEDIUM"

    def test_low(self):
        assert PortfolioStressTestEngine._classify_sensitivity(-0.03) == "LOW"


class TestRunAllPredefined:
    def test_returns_default_scenarios(self):
        holdings = [_stock("AAPL"), _stock("MSFT"), _crypto("BTC")]
        engine = PortfolioStressTestEngine(holdings)
        results = engine.run_all_predefined()
        assert len(results) == 3  # get_default_scenarios returns 3

    def test_most_and_least_affected(self):
        holdings = [_stock("AAPL", beta=2.0), _stock("KO", beta=0.3), _stock("MSFT", beta=1.0)]
        engine = PortfolioStressTestEngine(holdings)
        result = engine.run_scenario(CRASH)
        assert result.most_affected[0] == "AAPL"  # highest beta = most impact
