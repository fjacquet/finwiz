"""Tests for the dedicated strategic posture page.

The posture is analyst-length: PESTEL/SWOT/Porter synthesis across a whole
portfolio. Moving it off the family artifact only fixes readability if this
page (1) puts coverage before the score so a reader can't mistake "one
holding's opinion" for "the portfolio's opinion", (2) actually renders the
aggregated SWOT and dominant themes instead of dropping the data the family
already paid for, and (3) keeps verdicts in the open with detail behind a
disclosure rather than reproducing the wall-of-prose defect on a new page.
"""

from __future__ import annotations

from finwiz.reporting.sections.posture_page import generate_posture_page


def _full_posture(**overrides: object) -> dict[str, object]:
    posture: dict[str, object] = {
        "holdings_covered": 64,
        "holdings_total": 64,
        "value_covered_pct": 100.0,
        "uncovered_tickers": [],
        "macro_verdict": "Environnement porteur.",
        "competitive_verdict": "Moats solides.",
        "swot_verdict": "Équilibré.",
        "strategic_score": 0.71,
        "confidence": 0.83,
        "macro_environment_summary": "- **Politique** : durcissement",
        "competitive_landscape_summary": "- Moats **larges** en tech",
        "overall_assessment": "- Portefeuille **globalement** solide",
        "dominant_themes": ["Résilience énergétique", "IA générative", "Consolidation bancaire"],
        "portfolio_strengths": ["Moats larges en tech", "Diversification géographique"],
        "portfolio_weaknesses": ["Concentration sur les valeurs de croissance"],
        "portfolio_opportunities": ["Transition énergétique"],
        "portfolio_threats": ["Durcissement réglementaire"],
    }
    posture.update(overrides)
    return posture


class TestCoverageLeads:
    def test_coverage_leads_the_page(self) -> None:
        """Coverage is the first thing a reader sees, not a footnote."""
        html = generate_posture_page(
            {
                "holdings_covered": 26,
                "holdings_total": 64,
                "value_covered_pct": 38.2,
                "uncovered_tickers": ["TSLA"],
                "macro_verdict": "Environnement porteur.",
                "competitive_verdict": "Moats solides.",
                "swot_verdict": "Équilibré.",
                "strategic_score": 0.71,
                "confidence": 0.83,
                "macro_environment_summary": "- **Politique** : durcissement",
            }
        )

        assert "26 / 64" in html
        assert html.index("26 / 64") < html.index("Environnement porteur.")

    def test_score_never_appears_before_coverage(self) -> None:
        html = generate_posture_page(_full_posture())

        assert html.index("64 / 64") < html.index("71 %")

    def test_uncovered_tickers_are_named(self) -> None:
        html = generate_posture_page(_full_posture(holdings_covered=26, holdings_total=64, uncovered_tickers=["TSLA", "NVDA"]))

        assert "TSLA" in html
        assert "NVDA" in html


class TestCoverageVisualDistinction:
    """The one visual cue that a score doesn't speak for the whole portfolio."""

    def test_incomplete_coverage_is_visually_distinct_from_complete(self) -> None:
        complete_html = generate_posture_page(_full_posture())
        incomplete_html = generate_posture_page(_full_posture(holdings_covered=26, holdings_total=64, uncovered_tickers=["TSLA"]))

        # Not merely "a class attribute is present" — the class must resolve
        # to a real, different visual rule in the page's own stylesheet, and
        # the two coverage states must not resolve to the same rule.
        css = complete_html.split("<style>", 1)[1].split("</style>", 1)[0]
        assert ".warning" in css
        assert ".highlight" in css

        assert 'class="highlight warning"' in incomplete_html
        assert 'class="highlight success"' in complete_html

    def test_complete_coverage_does_not_use_the_warning_class(self) -> None:
        """The stylesheet itself always defines .warning; only the *banner's own*
        class must not invoke it when coverage is complete."""
        html = generate_posture_page(_full_posture())
        body = html.split("</style>", 1)[1]

        assert 'class="highlight warning"' not in body


class TestDetailDisclosure:
    def test_detail_is_behind_a_disclosure(self) -> None:
        html = generate_posture_page(_full_posture())
        # Search only the body: the page's own <style> block can legitimately
        # contain the literal text "<details>" (a CSS comment, a doc block) --
        # an unscoped search would pass even if the real element were missing.
        body = html.split("</style>", 1)[1]

        assert "<details>" in body
        assert "<strong>Politique</strong>" in body  # markdown rendered, not literal
        assert "**" not in body

    def test_verdicts_are_visible_without_expanding(self) -> None:
        """Each theme's verdict precedes *its own* disclosure, not merely the
        page's first one — three theme blocks each pair a verdict with detail."""
        html = generate_posture_page(_full_posture())
        body = html.split("</style>", 1)[1]

        for verdict in ("Environnement porteur.", "Moats solides.", "Équilibré."):
            verdict_pos = body.index(verdict)
            assert verdict_pos < body.index("<details>", verdict_pos)


class TestDominantThemes:
    def test_dominant_themes_render_near_the_top(self) -> None:
        html = generate_posture_page(_full_posture())
        # Scoped to the body, not the whole document: the <style> block can
        # legitimately contain the literal text "<details>" (e.g. in a CSS
        # comment), which would otherwise resolve to the wrong occurrence and
        # make this ordering assertion pass or fail for the wrong reason.
        body = html.split("</style>", 1)[1]

        assert "Résilience énergétique" in body
        assert "IA générative" in body
        assert "Consolidation bancaire" in body
        # Prominent: after coverage, before the analyst-length theme blocks.
        assert body.index("Résilience énergétique") < body.index("<details>")

    def test_missing_dominant_themes_does_not_crash(self) -> None:
        posture = _full_posture()
        del posture["dominant_themes"]

        html = generate_posture_page(posture)

        assert "Posture Stratégique" in html


class TestAggregatedSwot:
    def test_all_four_swot_lists_appear(self) -> None:
        html = generate_posture_page(_full_posture())

        assert "Moats larges en tech" in html
        assert "Diversification géographique" in html
        assert "Concentration sur les valeurs de croissance" in html
        assert "Transition énergétique" in html
        assert "Durcissement réglementaire" in html

    def test_empty_swot_lists_do_not_render_an_empty_section(self) -> None:
        posture = _full_posture(
            portfolio_strengths=[],
            portfolio_weaknesses=[],
            portfolio_opportunities=[],
            portfolio_threats=[],
        )

        html = generate_posture_page(posture)

        assert "Posture Stratégique" in html


class TestPerHolding:
    def test_holdings_strategic_renders_a_scannable_score_table(self) -> None:
        holdings_strategic = {
            "AAPL": {
                "pestel": {"strategic_score": 0.62},
                "swot": {"strategic_score": 0.75},
                "five_forces": {"strategic_score": 0.80},
            },
            "MSFT": {
                "pestel": {"strategic_score": 0.70},
                "swot": {"strategic_score": 0.68},
                "five_forces": {"strategic_score": 0.72},
            },
        }

        html = generate_posture_page(_full_posture(), holdings_strategic=holdings_strategic)

        assert "AAPL" in html
        assert "MSFT" in html
        assert "<table" in html

    def test_missing_framework_on_a_holding_does_not_crash(self) -> None:
        holdings_strategic = {"AAPL": {"pestel": {"strategic_score": 0.62}}}

        html = generate_posture_page(_full_posture(), holdings_strategic=holdings_strategic)

        assert "AAPL" in html

    def test_table_has_a_plain_language_legend(self) -> None:
        """PESTEL/SWOT/Porter as bare column headers teach a family reader
        nothing -- a one-sentence gloss must explain what each score means."""
        holdings_strategic = {"AAPL": {"pestel": {"strategic_score": 0.62}}}

        html = generate_posture_page(_full_posture(), holdings_strategic=holdings_strategic)
        table_section = html[html.index("Par ligne") :]

        assert "PESTEL" in table_section
        assert "SWOT" in table_section
        assert "Porter" in table_section
        # A glance-level gloss, not a tutorial: exactly one sentence.
        legend = table_section[table_section.index("<p", table_section.index("</h2>")) : table_section.index("</p>") + len("</p>")]
        assert legend.count(".") == 1

    def test_no_holdings_strategic_does_not_render_a_bare_ticker_list(self) -> None:
        html = generate_posture_page(_full_posture(), holdings_strategic=None)

        assert "Par ligne" not in html

    def test_empty_holdings_strategic_does_not_render_an_empty_section(self) -> None:
        html = generate_posture_page(_full_posture(), holdings_strategic={})

        assert "<table" not in html


class TestOptionalFieldsAbsent:
    def test_minimal_posture_does_not_crash(self) -> None:
        html = generate_posture_page(
            {
                "holdings_covered": 0,
                "holdings_total": 0,
                "value_covered_pct": 0.0,
                "macro_verdict": "",
                "competitive_verdict": "",
                "swot_verdict": "",
                "strategic_score": 0.0,
                "confidence": 0.0,
            }
        )

        assert "Posture Stratégique" in html
        assert "**" not in html

    def test_no_citations_does_not_crash_and_omits_sources(self) -> None:
        html = generate_posture_page(_full_posture(), citations=None)

        assert "Sources" not in html


class TestStandaloneDocument:
    def test_returns_a_complete_html_document(self) -> None:
        html = generate_posture_page(_full_posture())

        assert html.startswith("<!DOCTYPE html>")
        assert "<html" in html
        assert "</html>" in html
        assert 'lang="fr"' in html


class TestFamilySectionSummarisesAndLinksOut:
    """The family artifact carries a verdict and a link, not the analysis (Task 11).

    ``generate_strategic_posture_section`` lives in
    ``finwiz.reporting.sections.portfolio_summary`` and is re-exported through
    the ``section_generators`` facade; tests import from the facade because
    that's the stable public surface.
    """

    def test_family_section_summarises_and_links_out(self) -> None:
        from finwiz.reporting.section_generators import generate_strategic_posture_section

        html = generate_strategic_posture_section(_full_posture())

        assert "Environnement porteur." in html
        assert "Moats solides." in html
        assert "Équilibré." in html
        assert "finwiz_posture_strategique.html" in html
        assert "PESTEL" not in html
        assert "SWOT" not in html
        assert "Porter" not in html
        assert len(html) < 2000

    def test_coverage_appears_beside_the_score_not_alone(self) -> None:
        from finwiz.reporting.section_generators import generate_strategic_posture_section

        html = generate_strategic_posture_section(_full_posture(holdings_covered=26, holdings_total=64))

        assert "26/64" in html
        # The score paragraph itself must carry the coverage fraction --
        # never the score alone. That's the defect this whole branch removes.
        para = html.split("<p><strong>", 1)[1].split("</p>", 1)[0]
        assert "26/64" in para
        assert "71 %" in para

    def test_model_supplied_verdicts_are_escaped(self) -> None:
        from finwiz.reporting.section_generators import generate_strategic_posture_section

        html = generate_strategic_posture_section(_full_posture(macro_verdict="<script>alert(1)</script>"))

        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_no_posture_renders_nothing(self) -> None:
        from finwiz.reporting.section_generators import generate_strategic_posture_section

        assert generate_strategic_posture_section(None) == ""
