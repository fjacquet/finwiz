"""Tests for finwiz.quantitative.data_processors.DataProcessor.save_cache_metadata.

Covers the cache-metadata write path: it must survive a caller mutating the
metadata dict from another thread, must not choke on non-JSON-native values
(e.g. ``datetime``), and must never let a write failure escape and abort a
production run -- while still being loud about failures that are not simple
I/O hiccups.
"""

import json
import logging
import threading
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


def test_save_cache_metadata_survives_concurrent_mutation(tmp_path):
    """The caller owns the dict and may mutate it from another thread while
    save_cache_metadata is serializing it; the write must not fail.

    The churn thread adds and evicts keys in a rolling window rather than
    growing the dict unboundedly. An unbounded churner races json.dump's
    per-write GIL yield points: the dict balloons between dump calls, each
    call takes longer, which gives the churner even more time to grow it
    further -- a runaway that made an earlier version of this test run for
    minutes. A bounded window still exercises the exact defect (dict size
    changing mid-iteration) without that blowup.
    """
    processor = DataProcessor(QuantConfig())
    metadata = {f"seed{i}": i for i in range(500)}
    target = tmp_path / "cache_metadata.json"
    stop = threading.Event()
    errors: list[BaseException] = []
    window = 200

    def churn():
        i = 0
        while not stop.is_set():
            metadata[f"k{i}"] = i
            if i >= window:
                metadata.pop(f"k{i - window}", None)
            i += 1

    writer = threading.Thread(target=churn, daemon=True)
    writer.start()
    try:
        for _ in range(50):
            try:
                processor.save_cache_metadata(metadata, target)
            except BaseException as exc:  # the test is the assertion
                errors.append(exc)
    finally:
        stop.set()
        writer.join(timeout=2.0)

    assert errors == []
    assert json.loads(target.read_text(encoding="utf-8"))


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
