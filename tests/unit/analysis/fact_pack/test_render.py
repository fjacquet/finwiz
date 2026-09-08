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
        assert lines == ["NVDA (NVIDIA Corp) —"]
        assert "None" not in lines[0]

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


class TestPreviouslyUnrenderedFields:
    """turnover, sector_weights and volume_24h_market_cap_pct were collected on
    every run, stored in every cached pack, and read by nothing — neither scored
    nor rendered, so they reached neither the model nor the reader. That was the
    worst of the available states: the data was paid for and thrown away. See #186.

    All three are fractions at source, verified against real cached packs
    (a fund at turnover 1.1228, BTC at 0.0145), so _pct is the correct formatter.
    """

    def test_a_funds_turnover_is_rendered_as_a_percentage(self):
        pack = _pack("etf", FundFacts(issuer="iShares", turnover=1.1228))
        assert ("Rotation annuelle", "112,28 %") in to_rows(pack)

    def test_a_zero_turnover_is_shown_rather_than_treated_as_missing(self):
        """0.0 is a real fact — an index fund that did not trade all year.
        The same `is not None` distinction the expense ratio already makes."""
        pack = _pack("etf", FundFacts(issuer="iShares", turnover=0.0))
        assert ("Rotation annuelle", "0,00 %") in to_rows(pack)

    def test_sector_weights_render_as_a_list_largest_first(self):
        pack = _pack("etf", FundFacts(issuer="iShares", sector_weights={"realestate": 0.02, "technology": 0.41, "basic_materials": 0.09}))
        sectors = next(value for label, value in to_rows(pack) if label == "Secteurs")
        assert sectors == ["Technology 41,00 %", "Basic materials 9,00 %", "Realestate 2,00 %"]

    def test_sector_weights_are_capped_so_the_tail_does_not_pad_the_prompt(self):
        pack = _pack("etf", FundFacts(issuer="iShares", sector_weights={f"sector_{i}": (20 - i) / 100 for i in range(11)}))
        sectors = next(value for label, value in to_rows(pack) if label == "Secteurs")
        assert len(sectors) == 5

    def test_a_crypto_liquidity_ratio_is_rendered(self):
        pack = _pack("crypto", CryptoFacts(description="Bitcoin", circulating_supply=19_000_000.0, volume_24h_market_cap_pct=0.014470552))
        assert ("Volume 24 h / capitalisation", "1,45 %") in to_rows(pack)

    def test_the_new_rows_reach_the_model_not_just_the_report(self):
        """to_prompt_block is built from to_rows, so rendering reaches both
        consumers. This asserts the half that is easy to forget."""
        pack = _pack("etf", FundFacts(issuer="iShares", turnover=1.1228, sector_weights={"technology": 0.41}))
        block = to_prompt_block(pack)
        assert "Rotation annuelle : 112,28 %" in block
        assert "Technology 41,00 %" in block


class TestRowValueContract:
    """A row's value is a plain str for prose and a list[str] for a
    genuinely list-shaped fact (holdings, recent events, allocation
    buckets) -- never a newline-joined string with a "- " marker per item.
    Each of to_rows()'s three consumers (the prompt, the report card, the
    report-table cell) used to decode that joined string by hand,
    differently, and the prompt's decoding was wrong (see TestPromptBlock).
    """

    def test_a_holdings_row_is_a_list_not_a_joined_string(self):
        pack = _pack("etf", FundFacts(issuer="iShares", top_holdings=[FundHolding(symbol="NVDA", name="NVIDIA Corp", weight=0.0777)]))
        value = next(value for label, value in to_rows(pack) if label == "Principales lignes")
        assert value == ["NVDA (NVIDIA Corp) 7,77 %"]

    def test_an_allocation_row_is_a_list_of_buckets(self):
        pack = _pack("etf", FundFacts(issuer="iShares", asset_mix={"stockPosition": 0.9942, "cashPosition": 0.0058}))
        value = next(value for label, value in to_rows(pack) if label == "Allocation")
        assert value == ["stockPosition 99,42 %", "cashPosition 0,58 %"]

    def test_a_recent_events_row_is_a_list_not_a_joined_string(self):
        pack = _pack("stock", EquityFacts(business_summary="Builds planes.", leadership="Guillaume Faury (CEO)", recent_events=["Airbus wins order"], events_from_filings=False))
        value = next(value for label, value in to_rows(pack) if label.startswith("Événements récents"))
        assert value == ["Airbus wins order"]

    def test_prose_rows_stay_plain_strings(self):
        pack = _pack("stock", EquityFacts(business_summary="Designs phones.", leadership="Tim Cook (CEO)"))
        assert all(isinstance(value, str) for _, value in to_rows(pack))


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

    def test_a_list_valued_row_is_indented_beneath_its_label_not_top_level(self):
        """The bug this fixes: prefixing every holding with its own
        top-level "- " read to the model as sibling facts about the fund,
        inside the one block the prompt itself calls AUTORITAIRE.
        """
        pack = _pack(
            "etf",
            FundFacts(
                issuer="iShares",
                top_holdings=[
                    FundHolding(symbol="MSFT", name="Microsoft", weight=0.07),
                    FundHolding(symbol="NVDA", name="NVIDIA", weight=0.06),
                ],
            ),
        )
        lines = to_prompt_block(pack).split("\n")
        label_idx = lines.index("- Principales lignes :")
        assert lines[label_idx + 1] == "  - MSFT (Microsoft) 7,00 %"
        assert lines[label_idx + 2] == "  - NVDA (NVIDIA) 6,00 %"
        # Neither holding is a top-level fact sitting alongside "- Émetteur".
        assert not any(line.startswith("- MSFT") or line.startswith("- NVDA") for line in lines)
