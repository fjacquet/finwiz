"""Tests for the local fixed-window text chunker."""

import pytest

from finwiz.tools._text_chunking import TextChunk, chunk_text


def test_splits_into_overlapping_windows():
    text = "x" * 5000
    chunks = chunk_text(text, chunk_size=2000, overlap=200)
    assert all(isinstance(c, TextChunk) for c in chunks)
    assert all(len(c.page_content) <= 2000 for c in chunks)
    assert len(chunks) >= 3
    # consecutive windows overlap by `overlap` characters
    assert chunks[0].page_content[-200:] == chunks[1].page_content[:200]


def test_short_text_single_chunk():
    out = chunk_text("hello world", chunk_size=2000)
    assert len(out) == 1
    assert out[0].page_content == "hello world"


def test_empty_or_whitespace_returns_empty():
    assert chunk_text("   ") == []
    assert chunk_text("") == []


def test_invalid_params_raise():
    with pytest.raises(ValueError):
        chunk_text("x", chunk_size=0)
    with pytest.raises(ValueError):
        chunk_text("x", chunk_size=100, overlap=100)


def test_overlap_zero_no_overlap():
    # Distinct per-window content so the "no overlap" assertion is meaningful.
    source = "".join(chr(ord("a") + i // 1000) * 1 for i in range(4000))
    chunks = chunk_text(source, chunk_size=1000, overlap=0)
    assert len(chunks) == 4
    assert all(len(c.page_content) == 1000 for c in chunks)
    # with zero overlap, consecutive windows are distinct slices that
    # reconstruct the source exactly
    assert chunks[0].page_content != chunks[1].page_content
    assert "".join(c.page_content for c in chunks) == source


def test_tail_shorter_than_chunk_is_captured():
    text = "".join(str(i % 10) for i in range(4100))
    chunks = chunk_text(text, chunk_size=2000, overlap=200)
    # trailing characters must not be lost
    assert chunks[-1].page_content.endswith(text[-10:])
    # every character index appears in at least one chunk
    covered = "".join(c.page_content for c in chunks)
    for ch in text:
        assert ch in covered


def test_all_whitespace_window_skipped():
    # The middle window is entirely whitespace and must be dropped, while the
    # "A" and "B" content windows survive.
    text = "A" * 100 + " " * 4000 + "B" * 100
    chunks = chunk_text(text, chunk_size=2000, overlap=0)
    assert all(c.page_content.strip() for c in chunks)
    joined = "".join(c.page_content for c in chunks)
    assert "A" in joined
    assert "B" in joined
