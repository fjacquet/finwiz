"""Lightweight fixed-window text chunking.

Replaces ``langchain_text_splitters.CharacterTextSplitter`` for the SEC tool:
the only behaviour needed is splitting a long string into overlapping
fixed-size character windows. Chunks expose ``page_content`` so existing
consumers that read ``doc.page_content`` keep working unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    """A chunk of text with a langchain-Document-compatible ``page_content``."""

    # ``page_content``-only is intentional (langchain ``Document`` compatibility);
    # extend only if a consumer needs metadata.
    page_content: str


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> list[TextChunk]:
    """Split *text* into fixed-size character windows with overlap.

    Args:
        text: Source text.
        chunk_size: Max characters per chunk (must be > 0).
        overlap: Overlap between consecutive chunks (0 <= overlap < chunk_size).

    Returns:
        List of ``TextChunk``; empty for empty/whitespace-only input.
        All-whitespace windows are skipped (they carry no content), and the
        final window may be shorter than ``chunk_size``.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")
    cleaned = text.strip()
    if not cleaned:
        return []
    step = chunk_size - overlap
    chunks: list[TextChunk] = []
    for start in range(0, len(cleaned), step):
        window = cleaned[start : start + chunk_size]
        if window.strip():
            chunks.append(TextChunk(page_content=window))
        if start + chunk_size >= len(cleaned):
            break
    return chunks
