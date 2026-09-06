"""A fragment is one source's partial answer; only the composer builds a FactPack.

Sources deliberately cannot return a ``FactPack``. Keeping them to fragments is
what makes "which source said what" answerable after the fact, and it is what
lets the merge rule guarantee that a paid LLM can only add to a deterministic
answer, never replace one.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

# Same sentinel the Perplexity path has always written for an unknown field.
# Imported by value rather than from fact_pack_research to keep this module free
# of any dependency on the LLM path.
PLACEHOLDER = "Information indisponible"


@dataclass(frozen=True)
class FactPackFragment:
    """One source's contribution. Every field is optional by construction."""

    corporate_structure: str | None = None
    leadership: str | None = None
    recent_events: tuple[str, ...] = ()
    citations: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    events_from_filings: bool = False


def _populated(value: str | None) -> bool:
    return bool(value and value.strip() and value.strip() != PLACEHOLDER)


def merge_fragments(*fragments: FactPackFragment) -> FactPackFragment:
    """Merge in argument order: the first non-empty value for a field wins.

    Argument order is the precedence, and callers pass a fixed per-asset-class
    list, so two runs over identical inputs compose identically.
    """
    merged = FactPackFragment()
    citations: list[str] = []
    sources: list[str] = []

    for fragment in fragments:
        if not _populated(merged.corporate_structure) and _populated(fragment.corporate_structure):
            merged = replace(merged, corporate_structure=fragment.corporate_structure)
        if not _populated(merged.leadership) and _populated(fragment.leadership):
            merged = replace(merged, leadership=fragment.leadership)
        if not merged.recent_events and fragment.recent_events:
            merged = replace(merged, recent_events=fragment.recent_events, events_from_filings=fragment.events_from_filings)
        for url in fragment.citations:
            if url not in citations:
                citations.append(url)
        for source in fragment.sources:
            if source not in sources:
                sources.append(source)

    return replace(merged, citations=tuple(citations), sources=tuple(sources))
