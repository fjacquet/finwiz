"""Tests for the invalidate_fact_pack CLI."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from finwiz.cache.fact_pack_cache import FactPackCache
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack
from scripts.invalidate_fact_pack import main


def _seed(tmp_path: Path) -> FactPackCache:
    cache = FactPackCache(cache_dir=tmp_path)
    fp = FactPack(
        corporate_structure="x",
        recent_events=[],
        leadership="x",
        fetched_at=datetime.now(UTC),
        freshness="fresh",
        confidence=0.5,
        source_citations=[],
    )
    cache.put("DELL", fp)
    cache.put("AAPL", fp)
    return cache


def test_cli_invalidates_single_ticker(tmp_path: Path, mocker: Any) -> None:
    mocker.patch("scripts.invalidate_fact_pack.FactPackCache", lambda: FactPackCache(cache_dir=tmp_path))
    cache = _seed(tmp_path)
    rc = main(["invalidate_fact_pack.py", "DELL"])
    assert rc == 0
    assert cache.get("DELL") is None
    assert cache.get("AAPL") is not None


def test_cli_invalidate_all(tmp_path: Path, mocker: Any) -> None:
    mocker.patch("scripts.invalidate_fact_pack.FactPackCache", lambda: FactPackCache(cache_dir=tmp_path))
    cache = _seed(tmp_path)
    rc = main(["invalidate_fact_pack.py", "--all"])
    assert rc == 0
    assert cache.get("DELL") is None
    assert cache.get("AAPL") is None


def test_cli_returns_1_when_ticker_missing(tmp_path: Path, mocker: Any) -> None:
    mocker.patch("scripts.invalidate_fact_pack.FactPackCache", lambda: FactPackCache(cache_dir=tmp_path))
    rc = main(["invalidate_fact_pack.py", "UNKNOWN"])
    assert rc == 1


def test_cli_usage_error_returns_2(tmp_path: Path) -> None:
    rc = main(["invalidate_fact_pack.py"])
    assert rc == 2
