"""Crypto facts from the info dict the composer already fetched."""

from finwiz.analysis.fact_pack.sources import crypto_source

BTC = {
    "quoteType": "CRYPTOCURRENCY",
    "name": "Bitcoin",
    "description": "Bitcoin (BTC) is a cryptocurrency launched in 2010.",
    "startDate": 1278979200,
    "circulatingSupply": 20080456,
    "maxSupply": 21000000,
    "marketCap": 1604790386688,
    "volume24HrMarketCapPercent": 0.0125254495,
    "coinMarketCapLink": "https://coinmarketcap.com/currencies/bitcoin/",
}
ETH = {
    **BTC,
    "name": "Ethereum",
    "description": "Ethereum (ETH) is a cryptocurrency.",
    "startDate": 1438905600,
    "circulatingSupply": 122023856,
    "maxSupply": 0,
    "coinMarketCapLink": "https://coinmarketcap.com/currencies/ethereum/",
}


class TestCryptoFacts:
    def test_a_capped_asset_records_its_cap(self):
        facts, _ = crypto_source.crypto_facts("BTC-USD", BTC)
        assert facts.supply_is_capped is True
        assert facts.max_supply == 21000000.0
        assert facts.circulating_supply == 20080456.0

    def test_a_zero_max_supply_means_uncapped_not_unknown(self):
        """maxSupply == 0 is Ethereum's monetary policy, not a missing field."""
        facts, _ = crypto_source.crypto_facts("ETH-USD", ETH)
        assert facts.supply_is_capped is False
        assert facts.max_supply is None

    def test_an_absent_max_supply_is_also_uncapped_but_distinguishable_by_nothing_else(self):
        facts, _ = crypto_source.crypto_facts("XYZ-USD", {k: v for k, v in BTC.items() if k != "maxSupply"})
        assert facts.supply_is_capped is False
        assert facts.max_supply is None

    def test_the_launch_year_comes_from_start_date(self):
        facts, _ = crypto_source.crypto_facts("BTC-USD", BTC)
        assert facts.launched_year == 2010

    def test_the_coinmarketcap_link_is_the_citation(self):
        _, citations = crypto_source.crypto_facts("BTC-USD", BTC)
        assert citations == ("https://coinmarketcap.com/currencies/bitcoin/",)

    def test_a_non_http_citation_is_dropped(self):
        _, citations = crypto_source.crypto_facts("BTC-USD", {**BTC, "coinMarketCapLink": "javascript:alert(1)"})
        assert citations == ()

    def test_an_info_without_a_description_yields_none(self):
        facts, citations = crypto_source.crypto_facts("BTC-USD", {"quoteType": "CRYPTOCURRENCY"})
        assert facts is None
        assert citations == ()

    def test_an_oddly_typed_field_degrades_that_field_only(self):
        facts, _ = crypto_source.crypto_facts("BTC-USD", {**BTC, "marketCap": "lots", "startDate": "yesterday"})
        assert facts.market_cap is None
        assert facts.launched_year is None
        assert facts.circulating_supply == 20080456.0
