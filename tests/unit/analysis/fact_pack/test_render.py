"""One module owns the labels, so the prompt and the report cannot drift apart."""

from datetime import UTC, datetime

from finwiz.analysis.fact_pack.render import to_prompt_block, to_rows
from finwiz.schemas.hybrid_analysis.fact_pack import CryptoFacts, EquityFacts, FactPack, FundFacts, FundHolding


def _pack(asset_class, details) -> FactPack:
    fetched_at = datetime.now(UTC)
    return FactPack(
        asset_class=asset_class, details=details, fetched_at=fetched_at, freshness=FactPack.derive_freshness(fetched_at), confidence=1.0, source_citations=[], sources_used=[]
    )


class TestLabels:
    def test_an_equity_is_described_in_company_terms(self):
        pack = _pack("stock", EquityFacts(business_summary="Designs phones.", leadership="Tim Cook (CEO)", recent_events=["2026-09-01 8-K: Changes"], events_from_filings=True))
        labels = [label for label, _ in to_rows(pack)]
        assert "Structure" in labels
        assert "Direction" in labels

    def test_a_fund_is_never_asked_about_a_director(self):
        pack = _pack(
            "etf", FundFacts(issuer="iShares", legal_type="Exchange Traded Fund", expense_ratio=0.002, top_holdings=[FundHolding(symbol="NVDA", name="NVIDIA Corp", weight=0.0777)])
        )
        labels = [label for label, _ in to_rows(pack)]
        assert "Direction" not in labels
        assert "Émetteur" in labels
        assert "Frais courants" in labels

    def test_a_holding_with_an_unknown_weight_renders_as_a_dash_not_a_crash(self):
        """FundHolding.weight is float | None (a NaN/out-of-range yfinance
        weight is kept as an unknown weight, not dropped) -- _pct already
        handles None, so this is the "nearly free downstream" half of that
        fix: a None weight must render as the same dash used elsewhere for
        an unknown figure, never "None" or a TypeError from `value * 100`.
        """
        pack = _pack("etf", FundFacts(issuer="iShares", top_holdings=[FundHolding(symbol="NVDA", name="NVIDIA Corp", weight=None)]))
        lines = next(value for label, value in to_rows(pack) if label == "Principales lignes")
        assert "NVDA" in lines
        assert "—" in lines
        assert "None" not in lines

    def test_the_expense_ratio_is_rendered_as_a_percentage(self):
        pack = _pack("etf", FundFacts(issuer="iShares", expense_ratio=0.002))
        assert any("0,20 %" in value for _, value in to_rows(pack))

    def test_an_uncapped_supply_says_so_rather_than_showing_zero(self):
        pack = _pack("crypto", CryptoFacts(description="Ethereum is...", circulating_supply=122023856.0, max_supply=None, supply_is_capped=False))
        supply = next(value for label, value in to_rows(pack) if label == "Offre")
        assert "0" != supply.strip()
        assert "aucun plafond" in supply.lower()

    def test_a_capped_supply_states_the_cap(self):
        pack = _pack("crypto", CryptoFacts(description="Bitcoin is...", circulating_supply=20080456.0, max_supply=21000000.0, supply_is_capped=True))
        supply = next(value for label, value in to_rows(pack) if label == "Offre")
        assert "21" in supply


class TestPromptBlock:
    def test_the_block_carries_every_row(self):
        pack = _pack("etf", FundFacts(issuer="iShares", expense_ratio=0.002))
        block = to_prompt_block(pack)
        for label, value in to_rows(pack):
            assert label in block
            assert value in block

    def test_the_block_names_freshness_and_confidence(self):
        pack = _pack("stock", EquityFacts(business_summary="Designs phones.", leadership="Tim Cook (CEO)"))
        block = to_prompt_block(pack)
        assert "fresh" in block
        assert "1.00" in block
