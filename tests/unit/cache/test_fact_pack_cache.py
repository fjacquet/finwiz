"""Tests for FactPackCache (v5.2)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from finwiz.cache.fact_pack_cache import FactPackCache
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack


def _build_fp(days_old: float = 0) -> FactPack:
    fetched = datetime.now(UTC) - timedelta(days=days_old)
    return FactPack(
        corporate_structure="x",
        recent_events=[],
        leadership="x",
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
        assert loaded.corporate_structure == "x"
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

    def test_get_returns_none_for_too_old(self, tmp_path: Path) -> None:
        cache = FactPackCache(cache_dir=tmp_path)
        fp = _build_fp(days_old=0)
        cache.put("DELL", fp)
        path = tmp_path / "DELL.json"
        data = json.loads(path.read_text())
        too_old = (datetime.now(UTC) - timedelta(days=20)).isoformat()
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
        import pytest

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
