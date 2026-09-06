"""Tests for FactPackCache (v5.3)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

import pytest

from finwiz.cache.fact_pack_cache import FactPackCache
from finwiz.schemas.hybrid_analysis.fact_pack import CryptoFacts, EquityFacts, FactPack, FundFacts, FundHolding


def _build_fp(days_old: float = 0) -> FactPack:
    fetched = datetime.now(UTC) - timedelta(days=days_old)
    return FactPack(
        asset_class="stock",
        details=EquityFacts(business_summary="x", leadership="x", recent_events=[], events_from_filings=False),
        fetched_at=fetched,
        freshness=FactPack.derive_freshness(fetched),
        confidence=0.5,
        source_citations=[],
    )


class TestFactPackCache:
    def test_put_then_get_round_trips(self, tmp_path: Path) -> None:
        cache = FactPackCache(cache_dir=tmp_path)
        fp = _build_fp(days_old=0)
        cache.put("DELL", fp)
        loaded = cache.get("DELL")
        assert loaded is not None
        assert loaded.details.kind == "equity"
        assert loaded.details.business_summary == "x"
        assert loaded.freshness == "fresh"

    def test_get_returns_none_when_missing(self, tmp_path: Path) -> None:
        cache = FactPackCache(cache_dir=tmp_path)
        assert cache.get("UNKNOWN") is None

    def test_get_returns_stale_entry_marked_stale(self, tmp_path: Path) -> None:
        cache = FactPackCache(cache_dir=tmp_path)
        fp = _build_fp(days_old=0)  # fresh now
        cache.put("DELL", fp)
        # Manually rewrite the cached file with an old fetched_at
        path = tmp_path / "DELL.json"
        data = json.loads(path.read_text())
        old_time = (datetime.now(UTC) - timedelta(days=10)).isoformat()
        data["payload"]["fetched_at"] = old_time
        # Don't update freshness — derive_freshness will recompute on load
        path.write_text(json.dumps(data, default=str))
        loaded = cache.get("DELL")
        assert loaded is not None
        assert loaded.freshness == "stale"

    def test_get_returns_stale_entry_within_new_horizon_not_evicted(self, tmp_path: Path) -> None:
        """A 20d-old entry used to be evicted under the old 15-day cliff. It now
        falls within the widened stale band (7-90d) so a rate-limited run can
        still be rescued by it — see fact_pack.py's _STALE_HORIZON_DAYS.
        """
        cache = FactPackCache(cache_dir=tmp_path)
        fp = _build_fp(days_old=0)
        cache.put("DELL", fp)
        path = tmp_path / "DELL.json"
        data = json.loads(path.read_text())
        twenty_days = (datetime.now(UTC) - timedelta(days=20)).isoformat()
        data["payload"]["fetched_at"] = twenty_days
        path.write_text(json.dumps(data, default=str))
        loaded = cache.get("DELL")
        assert loaded is not None
        assert loaded.freshness == "stale"

    def test_get_returns_none_for_too_old(self, tmp_path: Path) -> None:
        cache = FactPackCache(cache_dir=tmp_path)
        fp = _build_fp(days_old=0)
        cache.put("DELL", fp)
        path = tmp_path / "DELL.json"
        data = json.loads(path.read_text())
        too_old = (datetime.now(UTC) - timedelta(days=95)).isoformat()
        data["payload"]["fetched_at"] = too_old
        path.write_text(json.dumps(data, default=str))
        assert cache.get("DELL") is None

    def test_get_returns_none_on_schema_version_mismatch(self, tmp_path: Path) -> None:
        cache = FactPackCache(cache_dir=tmp_path)
        path = tmp_path / "DELL.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": "0.0",  # WRONG
                    "cached_at": datetime.now(UTC).isoformat(),
                    "payload": _build_fp().model_dump(mode="json"),
                }
            )
        )
        assert cache.get("DELL") is None

    def test_invalidate_returns_true_when_existed(self, tmp_path: Path) -> None:
        cache = FactPackCache(cache_dir=tmp_path)
        cache.put("DELL", _build_fp())
        assert cache.invalidate("DELL") is True
        assert cache.get("DELL") is None

    def test_invalidate_returns_false_when_missing(self, tmp_path: Path) -> None:
        cache = FactPackCache(cache_dir=tmp_path)
        assert cache.invalidate("UNKNOWN") is False

    def test_invalidate_all(self, tmp_path: Path) -> None:
        cache = FactPackCache(cache_dir=tmp_path)
        cache.put("AAPL", _build_fp())
        cache.put("DELL", _build_fp())
        cache.put("MSFT", _build_fp())
        assert cache.invalidate_all() == 3
        assert cache.get("AAPL") is None

    def test_get_rejects_path_traversal_ticker(self, tmp_path: Path) -> None:
        """Path-traversal attempts must raise, not write outside the cache dir."""
        cache = FactPackCache(cache_dir=tmp_path)
        for evil in ["../../etc/passwd", "..", "/", "../foo", "a/b", "a\\b"]:
            with pytest.raises(ValueError, match="invalid ticker"):
                cache.get(evil)
            with pytest.raises(ValueError, match="invalid ticker"):
                cache.put(evil, _build_fp())
            with pytest.raises(ValueError, match="invalid ticker"):
                cache.invalidate(evil)

    def test_legitimate_ticker_formats_accepted(self, tmp_path: Path) -> None:
        """Yahoo / Kraken formats with dots, dashes, colons all work."""
        cache = FactPackCache(cache_dir=tmp_path)
        for ok in ["AAPL", "BRK.B", "BTC-USD", "^GSPC", "DELL"]:
            cache.put(ok, _build_fp())
            assert cache.get(ok) is not None


class TestRoundTripPerAssetClass:
    """A discriminated union serialised to disk and re-validated is exactly
    where a tag mismatch would appear — this is the only place in the system
    that round-trips FactPack through JSON, so each class gets a dedicated
    write/read/assert-kind test.
    """

    @staticmethod
    def _envelope(asset_class: Literal["stock", "etf", "crypto"], details: EquityFacts | FundFacts | CryptoFacts) -> FactPack:
        fetched_at = datetime.now(UTC)
        return FactPack(
            asset_class=asset_class,
            details=details,
            fetched_at=fetched_at,
            freshness=FactPack.derive_freshness(fetched_at),
            confidence=0.8,
            source_citations=[],
        )

    def test_equity_pack_round_trips_with_kind_intact(self, tmp_path: Path) -> None:
        cache = FactPackCache(cache_dir=tmp_path)
        fp = self._envelope(
            "stock",
            EquityFacts(business_summary="Designs phones.", leadership="Tim Cook (CEO)", recent_events=[], events_from_filings=False),
        )
        cache.put("AAPL", fp)
        loaded = cache.get("AAPL")
        assert loaded is not None
        assert loaded.details.kind == "equity"
        assert loaded.details.leadership == "Tim Cook (CEO)"

    def test_fund_pack_round_trips_with_kind_intact(self, tmp_path: Path) -> None:
        cache = FactPackCache(cache_dir=tmp_path)
        fp = self._envelope(
            "etf",
            FundFacts(
                issuer="BlackRock Asset Management Ireland - ETF",
                legal_type="Exchange Traded Fund",
                inception_year=2020,
                expense_ratio=0.002,
                top_holdings=[FundHolding(symbol="NVDA", name="NVIDIA Corp", weight=0.077756)],
                asset_mix={"stockPosition": 0.9942},
            ),
        )
        cache.put("2B7K.DE", fp)
        loaded = cache.get("2B7K.DE")
        assert loaded is not None
        assert loaded.details.kind == "fund"
        assert loaded.details.top_holdings[0].symbol == "NVDA"

    def test_crypto_pack_round_trips_with_kind_intact(self, tmp_path: Path) -> None:
        cache = FactPackCache(cache_dir=tmp_path)
        fp = self._envelope(
            "crypto",
            CryptoFacts(
                description="Bitcoin is a peer-to-peer electronic cash system.",
                launched_year=2009,
                circulating_supply=20080456.0,
                max_supply=21000000.0,
                supply_is_capped=True,
                market_cap=1.6e12,
            ),
        )
        cache.put("BTC-USD", fp)
        loaded = cache.get("BTC-USD")
        assert loaded is not None
        assert loaded.details.kind == "crypto"
        assert loaded.details.supply_is_capped is True
        assert loaded.details.max_supply == 21000000.0
