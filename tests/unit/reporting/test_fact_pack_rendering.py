"""Tests for fact pack provenance footer rendering (v5.2)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from finwiz.reporting.section_generators import _fact_pack_provenance_footer
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack


def _build_fp(days_old: float = 0, citations: list[str] | None = None) -> FactPack:
    fetched = datetime.now(UTC) - timedelta(days=days_old)
    return FactPack(
        corporate_structure="x",
        recent_events=[],
        leadership="x",
        fetched_at=fetched,
        freshness=FactPack.derive_freshness(fetched),
        confidence=0.85,
        source_citations=citations or [],
    )


class TestProvenanceFooter:
    def test_fresh_renders_green_pill(self) -> None:
        html = _fact_pack_provenance_footer(_build_fp(days_old=0))
        assert "pill-green" in html
        assert "Faits actuels" in html

    def test_recent_renders_neutral_pill(self) -> None:
        html = _fact_pack_provenance_footer(_build_fp(days_old=5))
        assert "pill-neutral" in html
        assert "Faits vérifiés" in html

    def test_stale_renders_amber_pill_with_confidence(self) -> None:
        html = _fact_pack_provenance_footer(_build_fp(days_old=10))
        assert "pill-amber" in html
        assert "⚠️" in html
        assert "0.85" in html

    def test_none_renders_muted_note(self) -> None:
        html = _fact_pack_provenance_footer(None)
        assert "Faits non vérifiés" in html
        assert "muted" in html

    def test_citations_render_as_footnote_links(self) -> None:
        fp = _build_fp(days_old=0, citations=["https://example.com/a", "https://example.com/b"])
        html = _fact_pack_provenance_footer(fp)
        assert "[1]" in html
        assert "[2]" in html
        assert 'href="https://example.com/a"' in html
        assert 'rel="noopener"' in html

    def test_malicious_url_in_citation_is_escaped(self) -> None:
        # Defense in depth — escape html in URLs even though our schema validates them
        fp = _build_fp(days_old=0, citations=['"><script>alert(1)</script>'])
        html = _fact_pack_provenance_footer(fp)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html or "&quot;" in html

    def test_french_date_format_in_pill(self) -> None:
        fp = _build_fp(days_old=0)
        html = _fact_pack_provenance_footer(fp)
        # Today's date in French should appear with a French month
        french_months = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        assert any(m in html for m in french_months)
