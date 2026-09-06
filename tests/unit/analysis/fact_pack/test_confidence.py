"""Confidence is scored over the fields that apply to each class."""

from finwiz.analysis.fact_pack.confidence import score
from finwiz.analysis.fact_pack.fragment import PLACEHOLDER
from finwiz.schemas.hybrid_analysis.fact_pack import CryptoFacts, EquityFacts, FundFacts, FundHolding


def _fund(**overrides) -> FundFacts:
    base = {
        "issuer": "BlackRock Asset Management Ireland - ETF",
        "legal_type": "Exchange Traded Fund",
        "expense_ratio": 0.002,
        "top_holdings": [FundHolding(symbol="NVDA", name="NVIDIA Corp", weight=0.0777)],
        "asset_mix": {"stockPosition": 0.9942},
    }
    return FundFacts(**{**base, **overrides})


class TestEquity:
    def test_filings_backed_equity_scores_one(self):
        facts = EquityFacts(business_summary="Designs phones.", leadership="Tim Cook (CEO)", recent_events=["2026-09-01 8-K"], events_from_filings=True)
        assert score(facts, has_citation=True) == 1.0

    def test_news_backed_equity_scores_0_85(self):
        facts = EquityFacts(business_summary="Builds planes.", leadership="Guillaume Faury (CEO)", recent_events=["Airbus wins order"], events_from_filings=False)
        assert score(facts, has_citation=True) == 0.85

    def test_placeholders_do_not_count_as_populated(self):
        facts = EquityFacts(business_summary=PLACEHOLDER, leadership=PLACEHOLDER, recent_events=[], events_from_filings=False)
        assert score(facts, has_citation=False) == 0.0


class TestFund:
    def test_a_complete_fund_scores_one(self):
        assert score(_fund(), has_citation=True) == 1.0

    def test_a_fund_without_top_holdings_scores_0_75(self):
        """AEEM.PA returns zero holdings while 2B7K.DE returns ten."""
        assert score(_fund(top_holdings=[]), has_citation=True) == 0.75

    def test_the_expense_ratio_carries_the_most_weight(self):
        without_ter = score(_fund(expense_ratio=None), has_citation=True)
        without_holdings = score(_fund(top_holdings=[]), has_citation=True)
        assert without_ter < without_holdings

    def test_a_zero_expense_ratio_still_counts_as_known(self):
        """0.0 is a real, remarkable fee — not a missing value."""
        assert score(_fund(expense_ratio=0.0), has_citation=True) == 1.0


class TestCrypto:
    def test_a_capped_asset_scores_one(self):
        facts = CryptoFacts(description="Bitcoin is...", launched_year=2010, circulating_supply=20080456.0, max_supply=21000000.0, supply_is_capped=True, market_cap=1.6e12)
        assert score(facts, has_citation=True) == 1.0

    def test_an_uncapped_asset_also_scores_one(self):
        """No cap is a monetary policy, not missing data. Ethereum must not be
        penalised for differing from Bitcoin."""
        facts = CryptoFacts(description="Ethereum is...", launched_year=2015, circulating_supply=122023856.0, max_supply=None, supply_is_capped=False, market_cap=4.0e11)
        assert score(facts, has_citation=True) == 1.0

    def test_unknown_supply_scores_lower_than_uncapped_supply(self):
        unknown = CryptoFacts(description="Something", launched_year=2020, circulating_supply=None, max_supply=None, supply_is_capped=False, market_cap=1.0)
        uncapped = CryptoFacts(description="Something", launched_year=2020, circulating_supply=585445184.0, max_supply=None, supply_is_capped=False, market_cap=1.0)
        assert score(unknown, has_citation=True) < score(uncapped, has_citation=True)
