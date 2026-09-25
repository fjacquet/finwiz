"""Tests for ResearchCache: on-disk reuse of successful web-research results."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import BaseModel

from finwiz.cache.research_cache import ResearchCache
from finwiz.infrastructure.research.openrouter_structured import Citation, ResearchResult

_DAY = timedelta(hours=24)


class _Payload(BaseModel):
    value: str


class _Other(BaseModel):
    count: int


def _result(value: str = "ok") -> ResearchResult[_Payload]:
    return ResearchResult(data=_Payload(value=value), citations=(Citation(url="https://a", title="t", content="c"),), cost_usd=0.02, prompt_tokens=100, completion_tokens=50)


def _only_file(tmp_path: Path) -> Path:
    files = list(tmp_path.rglob("*.json"))
    assert len(files) == 1
    return files[0]


def test_put_then_get_round_trips_data_and_citations(tmp_path: Path) -> None:
    cache = ResearchCache(cache_dir=tmp_path)
    cache.put("swot", "AAPL|stock", _result("fresh"))

    hit = cache.get("swot", "AAPL|stock", _Payload, max_age=_DAY)

    assert hit is not None
    assert hit.data == _Payload(value="fresh")
    assert hit.citations == (Citation(url="https://a", title="t", content="c"),)


def test_hit_reports_zero_cost_and_tokens(tmp_path: Path) -> None:
    cache = ResearchCache(cache_dir=tmp_path)
    cache.put("swot", "AAPL|stock", _result())

    hit = cache.get("swot", "AAPL|stock", _Payload, max_age=_DAY)

    assert hit is not None
    assert (hit.cost_usd, hit.prompt_tokens, hit.completion_tokens) == (0.0, 0, 0)


def test_missing_entry_is_a_miss(tmp_path: Path) -> None:
    assert ResearchCache(cache_dir=tmp_path).get("swot", "AAPL|stock", _Payload, max_age=_DAY) is None


def test_keys_and_kinds_do_not_collide(tmp_path: Path) -> None:
    cache = ResearchCache(cache_dir=tmp_path)
    cache.put("swot", "AAPL|stock", _result("swot"))
    cache.put("porter", "AAPL|stock", _result("porter"))

    assert cache.get("swot", "MSFT|stock", _Payload, max_age=_DAY) is None
    assert cache.get("porter", "AAPL|stock", _Payload, max_age=_DAY).data.value == "porter"  # type: ignore[union-attr]
    assert cache.get("swot", "AAPL|stock", _Payload, max_age=_DAY).data.value == "swot"  # type: ignore[union-attr]


def test_entry_older_than_max_age_is_a_miss(tmp_path: Path) -> None:
    cache = ResearchCache(cache_dir=tmp_path)
    cache.put("news", "AAPL", _result())
    path = _only_file(tmp_path)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["fetched_at"] = (datetime.now(UTC) - timedelta(hours=25)).isoformat()
    path.write_text(json.dumps(envelope), encoding="utf-8")

    assert cache.get("news", "AAPL", _Payload, max_age=_DAY) is None


def test_corrupt_file_is_a_miss(tmp_path: Path) -> None:
    cache = ResearchCache(cache_dir=tmp_path)
    cache.put("swot", "AAPL|stock", _result())
    _only_file(tmp_path).write_text("{not json", encoding="utf-8")

    assert cache.get("swot", "AAPL|stock", _Payload, max_age=_DAY) is None


def test_entry_that_no_longer_fits_the_schema_is_a_miss(tmp_path: Path) -> None:
    cache = ResearchCache(cache_dir=tmp_path)
    cache.put("swot", "AAPL|stock", _result())

    assert cache.get("swot", "AAPL|stock", _Other, max_age=_DAY) is None


def test_key_is_hashed_so_it_cannot_escape_the_cache_dir(tmp_path: Path) -> None:
    cache = ResearchCache(cache_dir=tmp_path / "research")
    cache.put("news", "../../etc/passwd|stock", _result())

    assert _only_file(tmp_path).parent == tmp_path / "research" / "news"


def test_invalid_kind_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        ResearchCache(cache_dir=tmp_path).put("../x", "AAPL", _result())
