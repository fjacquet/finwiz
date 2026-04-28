# tests/unit/analysis/test_helpers.py
from finwiz.analysis._helpers import (
    _filter_numeric_values,
    _summarize_metrics,
    _today_french,
    _truncate_text,
)


def test_today_french_returns_long_date_string() -> None:
    out = _today_french()
    assert any(month in out for month in ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"])


def test_filter_numeric_values_drops_non_numeric() -> None:
    assert _filter_numeric_values({"a": 1, "b": "x", "c": 2.5, "d": None}) == {"a": 1.0, "c": 2.5}


def test_truncate_text_caps_length() -> None:
    assert len(_truncate_text("x" * 1000, max_chars=100)) <= 100 + 3  # +3 for "..." ellipsis


def test_summarize_metrics_returns_string() -> None:
    out = _summarize_metrics({"pe_ratio": 18.5, "roe": 0.22}, max_items=10)
    assert "pe_ratio" in out
