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
