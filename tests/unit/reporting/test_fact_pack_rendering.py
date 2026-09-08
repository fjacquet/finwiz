"""Tests for fact pack provenance footer rendering (v5.2)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from finwiz.reporting.section_generators import _fact_pack_provenance_footer
from finwiz.schemas.hybrid_analysis.fact_pack import EquityFacts, FactPack


def _build_fp(days_old: float = 0, citations: list[str] | None = None, sources_used: list[str] | None = None) -> FactPack:
    fetched = datetime.now(UTC) - timedelta(days=days_old)
    return FactPack(
        asset_class="stock",
        details=EquityFacts(business_summary="x", leadership="x"),
        fetched_at=fetched,
        freshness=FactPack.derive_freshness(fetched),
        confidence=0.85,
        source_citations=citations or [],
        sources_used=sources_used or [],
    )


class TestSourcesLabel:
    """The pill tooltip reads "Vérifié via {label}" — it is prose for a reader.

    sources_used holds internal identifiers. Rendering them raw put strings like
    "yfinance.funds_data" into a financial report, and put
    "composer.schema_fallback" there as if the exception backstop were a place
    facts came from. See #174.
    """

    def test_internal_identifiers_are_not_shown_to_the_reader(self) -> None:
        html = _fact_pack_provenance_footer(_build_fp(sources_used=["yfinance.info", "yfinance.sec_filings"]))
        assert "Yahoo Finance" in html
        assert "dépôts SEC" in html
        assert "yfinance" not in html

    def test_the_schema_fallback_marker_is_not_rendered_as_provenance(self) -> None:
        """It marks a pack the exception backstop assembled — a diagnostic, not a source."""
        html = _fact_pack_provenance_footer(_build_fp(sources_used=["yfinance.info", "composer.schema_fallback"]))
        assert "Yahoo Finance" in html
        assert "schema_fallback" not in html
        assert "composer" not in html

    def test_a_pack_built_only_by_the_backstop_falls_back_to_the_generic_phrase(self) -> None:
        """Dropping the diagnostic must not leave an empty "Vérifié via" claim."""
        html = _fact_pack_provenance_footer(_build_fp(sources_used=["composer.schema_fallback"]))
        assert "sources structurées" in html
        assert "schema_fallback" not in html

    def test_the_same_provider_is_named_once(self) -> None:
        """A fund pack draws on yfinance.info and yfinance.funds_data; the reader
        should see "Yahoo Finance", not it twice."""
        label = _fact_pack_provenance_footer(_build_fp(sources_used=["yfinance.info", "yfinance.funds_data"]))
        assert label.count("Yahoo Finance") == 1

    def test_an_unlabelled_identifier_is_omitted_rather_than_leaked(self) -> None:
        """Adding a source without adding its label degrades to the generic
        phrase; it must never print the raw identifier into a report."""
        html = _fact_pack_provenance_footer(_build_fp(sources_used=["some.new_source_nobody_labelled"]))
        assert "some.new_source" not in html
        assert "sources structurées" in html


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

    def test_malicious_url_in_citation_is_filtered_out(self) -> None:
        """Defense in depth: non-http(s) citation URLs are dropped entirely.

        `_is_safe_url` runs at render time, after Pydantic validation, so even
        a stale cache that somehow holds a `"><script>` payload won't reach
        the rendered HTML — the URL has no http/https scheme and is filtered
        before escaping.
        """
        fp = _build_fp(days_old=0, citations=['"><script>alert(1)</script>'])
        html = _fact_pack_provenance_footer(fp)
        assert "<script>" not in html
        assert "alert(1)" not in html
        # No "Sources:" footer because all citations were filtered out
        assert "Sources:" not in html

    def test_javascript_url_in_citation_filtered_out(self) -> None:
        """`javascript:` URLs are blocked even when the rest looks innocuous."""
        fp = _build_fp(
            days_old=0,
            citations=[
                "javascript:alert(1)",
                "https://example.com/safe",
            ],
        )
        html = _fact_pack_provenance_footer(fp)
        # The javascript: URL must not survive
        assert "javascript:" not in html
        assert "alert(1)" not in html
        # The https:// URL is preserved
        assert 'href="https://example.com/safe"' in html
        # The footer renders only the safe link, numbered [1]
        assert "[1]" in html
        assert "[2]" not in html

    def test_data_url_in_citation_filtered_out(self) -> None:
        """`data:` URLs are blocked too — only http/https survive _is_safe_url."""
        fp = _build_fp(
            days_old=0,
            citations=["data:text/html,<script>alert(1)</script>"],
        )
        html = _fact_pack_provenance_footer(fp)
        assert "data:" not in html
        assert "<script>" not in html
        assert "Sources:" not in html

    def test_french_date_format_in_pill(self) -> None:
        fp = _build_fp(days_old=0)
        html = _fact_pack_provenance_footer(fp)
        # Today's date in French should appear with a French month
        french_months = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        assert any(m in html for m in french_months)
