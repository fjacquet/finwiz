"""Tests for finwiz.quantitative.data_processors.DataProcessor.save_cache_metadata.

Covers the cache-metadata write path: it must survive a caller mutating the
metadata dict from another thread, must not choke on non-JSON-native values
(e.g. ``datetime``), and must never let a write failure escape and abort a
production run -- while still being loud about failures that are not simple
I/O hiccups.
"""

import json
import logging
from datetime import datetime

from finwiz.quantitative.config import QuantConfig
from finwiz.quantitative.data_processors import DataProcessor

LOGGER_NAME = "finwiz.quantitative.data_processors.DataProcessor"


class _UnstringifiableValue:
    """A value that even ``default=str`` cannot serialize."""

    def __str__(self) -> str:
        raise RuntimeError("cannot stringify this value")


def test_save_cache_metadata_writes_valid_json(tmp_path):
    """Happy path: a plain metadata dict round-trips through the file."""
    processor = DataProcessor(QuantConfig())
    target = tmp_path / "cache_metadata.json"

    processor.save_cache_metadata({"symbol": "AAPL", "row_count": 10}, target)

    assert json.loads(target.read_text(encoding="utf-8")) == {"symbol": "AAPL", "row_count": 10}


def test_save_cache_metadata_serializes_datetime_via_default_str(tmp_path):
    """Reproduces the original bug: a datetime value used to raise TypeError,
    which the bare `except Exception` swallowed into a log line, leaving no
    file on disk at all.
    """
    processor = DataProcessor(QuantConfig())
    target = tmp_path / "cache_metadata.json"

    processor.save_cache_metadata({"fetched_at": datetime(2026, 8, 15, 12, 30)}, target)

    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["fetched_at"] == "2026-08-15 12:30:00"


def test_save_cache_metadata_snapshot_is_unaffected_by_concurrent_mutation(tmp_path, mocker):
    """Deterministic proof that save_cache_metadata serializes an isolated
    snapshot, not the caller's live dict.

    A threaded version of this test (real OS thread mutating `metadata`
    while save_cache_metadata ran) proved the mechanism but only failed on
    the exact scheduling that happened to trigger the race, and an earlier,
    unbounded-growth version of that thread caused a runaway feedback loop
    with json.dump's per-write GIL yield points (minutes of CPU before it
    was killed). Neither is acceptable as a regression guard: a race that
    only sometimes fires gives false confidence, and a revert of the fix
    could sail through CI green.

    Instead, force the mutation to land at a controlled point: patch
    json.dump itself so that, at the exact moment save_cache_metadata hands
    off to it, the *caller's* dict gets a key added and a key removed --
    simulating a concurrent writer's mutation landing right then. Against
    the fix, that mutation cannot reach the snapshot (a different object,
    already copied before this point), so the write is untouched and
    matches the pre-mutation content. Against a reverted fix (dumping
    `cache_metadata` directly, no snapshot), the mutated object *is* the one
    being serialized, so the write reflects the mutation and this assertion
    fails -- verified by temporarily reverting the snapshot line (see
    task-14-report.md for that evidence).
    """
    processor = DataProcessor(QuantConfig())
    cache_metadata = {f"seed{i}": i for i in range(20)}
    expected_snapshot = dict(cache_metadata)
    target = tmp_path / "cache_metadata.json"
    real_dump = json.dump

    def mutate_then_dump(obj, fp, **kwargs):
        cache_metadata["added_concurrently"] = -1
        del cache_metadata["seed0"]
        return real_dump(obj, fp, **kwargs)

    mocker.patch("finwiz.quantitative.data_processors.json.dump", side_effect=mutate_then_dump)

    processor.save_cache_metadata(cache_metadata, target)  # must not raise

    assert json.loads(target.read_text(encoding="utf-8")) == expected_snapshot


def test_save_cache_metadata_os_error_is_swallowed_and_logged(tmp_path, caplog):
    """A filesystem failure (e.g. the parent directory does not exist) is a
    best-effort cache miss, not a reason to crash the caller.
    """
    processor = DataProcessor(QuantConfig())
    target = tmp_path / "missing_dir" / "cache_metadata.json"

    caplog.set_level(logging.ERROR, logger=LOGGER_NAME)
    processor.save_cache_metadata({"symbol": "AAPL"}, target)  # must not raise

    assert not target.exists()
    assert any("Error saving cache metadata" in r.message for r in caplog.records)


def test_save_cache_metadata_unserializable_value_is_swallowed_but_logged_loudly(tmp_path, caplog):
    """A value that survives ``default=str`` being present but still can't be
    turned into a string is a programming error, not an I/O hiccup. It must
    still never propagate out of save_cache_metadata, but it must be logged
    with enough detail (a traceback) to actually be noticed -- unlike the
    original one-line swallow.
    """
    processor = DataProcessor(QuantConfig())
    target = tmp_path / "cache_metadata.json"

    caplog.set_level(logging.ERROR, logger=LOGGER_NAME)
    processor.save_cache_metadata({"bad": _UnstringifiableValue()}, target)  # must not raise

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.exc_info is not None
