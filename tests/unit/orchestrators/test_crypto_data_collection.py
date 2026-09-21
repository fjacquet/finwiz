"""The crypto collection path reports real data or nothing — never a stand-in."""

from datetime import datetime

from finwiz.data.crypto_source_orchestrator import CryptoLineage, CryptoOrchestrationResult
from finwiz.orchestrators.deep_analysis_data_collector import DeepAnalysisDataCollector
from finwiz.scoring.crew_export_generator import CrewExportGenerator

FABRICATED_VALUES = {1e9, 10e9, 100e9, 3.0, 5.0}


class _FakeState:
    full_date = "2026-09-20"


def _collector(mocker):
    mocker.patch("finwiz.data.data_source_orchestrator.DataSourceOrchestrator", autospec=True)
    mocker.patch("finwiz.data.crypto_source_orchestrator.CryptoSourceOrchestrator", autospec=True)
    return DeepAnalysisDataCollector(_FakeState())


def _resolved():
    return CryptoOrchestrationResult(
        ticker="BTC-USD",
        timestamp=datetime.now(),
        price=81114.0,
        market_cap=1629408510367.0,
        volume_24h=23900006504.0,
        circulating_supply=20087096.0,
        max_supply=21000000.0,
        lineage=CryptoLineage(price_source="coingecko", market_cap_source="coingecko", volume_24h_source="coingecko", supply_source="coingecko"),
        confidence=1.0,
        sources_succeeded=["coingecko", "kraken"],
    )


def _empty():
    return CryptoOrchestrationResult(ticker="BTC-USD", timestamp=datetime.now(), confidence=0.0, sources_failed=["coingecko", "kraken"])


def test_resolved_data_reaches_collected_data(mocker):
    collector = _collector(mocker)
    mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.return_value": _resolved()}, create=True)

    result = collector._collect_crypto_data("BTC-USD", {"current_price": 81061.41})

    assert result["market_cap"] == 1629408510367.0
    assert result["volume_24h"] == 23900006504.0
    assert result["circulating_supply"] == 20087096.0
    assert result["max_supply"] == 21000000.0


def test_unresolved_fields_are_none_not_fabricated(mocker):
    collector = _collector(mocker)
    mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.return_value": _empty()}, create=True)

    result = collector._collect_crypto_data("BTC-USD", {})

    assert result["market_cap"] is None
    assert result["volume_24h"] is None
    assert result["circulating_supply"] is None
    for key in ("market_cap", "volume_24h", "age_years"):
        assert result[key] not in FABRICATED_VALUES


def test_age_comes_from_the_curated_table(mocker):
    collector = _collector(mocker)
    mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.return_value": _resolved()}, create=True)
    mocker.patch("finwiz.orchestrators.deep_analysis_data_collector.crypto_age_years", return_value=17.0)

    result = collector._collect_crypto_data("BTC-USD", {})

    assert result["age_years"] == 17.0


def test_uncurated_symbol_has_no_age(mocker):
    collector = _collector(mocker)
    mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.return_value": _resolved()}, create=True)
    mocker.patch("finwiz.orchestrators.deep_analysis_data_collector.crypto_age_years", return_value=None)

    result = collector._collect_crypto_data("DOGE-USD", {})

    assert result["age_years"] is None


def test_yfinance_price_is_handed_to_the_orchestrator(mocker):
    collector = _collector(mocker)
    fake = mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.return_value": _resolved()}, create=True)

    collector._collect_crypto_data("BTC-USD", {"current_price": 81061.41})

    fake.fetch.assert_called_once_with("BTC-USD", yfinance_price=81061.41)


def test_lineage_and_confidence_are_carried_for_the_report(mocker):
    """Regression for I1: crypto_info is a nested dict that flatten_collected_data()
    silently dropped (not a top-level scalar, not in the nested-section allowlist).
    Assert on the production path — collect through flatten — not the pre-flatten
    private dict, which passed even while the flattened output lost everything.
    """
    collector = _collector(mocker)
    mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.return_value": _resolved()}, create=True)

    raw = collector._collect_crypto_data("BTC-USD", {})
    flattened = collector.flatten_collected_data(raw)

    assert flattened["crypto_confidence"] == 1.0
    assert flattened["crypto_market_cap_source"] == "coingecko"
    assert flattened["crypto_price_source"] == "coingecko"
    assert flattened["crypto_volume_24h_source"] == "coingecko"
    assert flattened["crypto_supply_source"] == "coingecko"


def test_orchestrator_failure_does_not_crash_the_holding(mocker):
    collector = _collector(mocker)
    mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.side_effect": RuntimeError("boom")}, create=True)

    result = collector._collect_crypto_data("BTC-USD", {})

    assert result["market_cap"] is None
    assert result["volume_24h"] is None


def test_construction_failure_does_not_abort_the_collector(mocker):
    """LIVE-5 (post-PR review, findings.md): CryptoSourceOrchestrator() builds
    CoinGeckoAdapter/KrakenAdapter eagerly. Building it unconditionally in
    __init__ let a construction failure (missing config, import error) abort
    DeepAnalysisDataCollector.__init__ for stock- and ETF-only runs that never
    touch crypto. Lazy construction defers the failure to first crypto use,
    where it is already caught by _collect_crypto_data's except block.
    """
    mocker.patch("finwiz.data.data_source_orchestrator.DataSourceOrchestrator", autospec=True)
    mocker.patch("finwiz.data.crypto_source_orchestrator.CryptoSourceOrchestrator", side_effect=RuntimeError("boom"))

    collector = DeepAnalysisDataCollector(_FakeState())  # must not raise

    result = collector._collect_crypto_data("BTC-USD", {})

    assert result["market_cap"] is None
    assert result["volume_24h"] is None


def test_missing_market_cap_is_reported_for_crypto():
    generator = CrewExportGenerator()

    missing = generator._identify_missing_fields({"asset_class": "crypto", "current_price": 81114.0, "market_cap": None, "volume_24h": 1.0})

    assert "market_cap" in missing


def test_market_cap_is_not_demanded_of_equities():
    generator = CrewExportGenerator()

    missing = generator._identify_missing_fields({"asset_class": "stock", "current_price": 100.0, "volume": 1.0})

    assert "market_cap" not in missing
