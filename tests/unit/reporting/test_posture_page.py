"""Tests for the dedicated strategic posture page.

The posture is analyst-length: SWOT/Porter synthesis across a whole
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
        "competitive_verdict": "Moats solides.",
        "swot_verdict": "Équilibré.",
        "strategic_score": 0.71,
        "confidence": 0.83,
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


class TestMacroRemoved:
    """PESTEL moved out of FinWiz; the macro section has no producer here."""

    def test_the_macro_block_is_gone_from_the_posture_page(self) -> None:
        html = generate_posture_page(_full_posture())

        assert "Environnement Macro" not in html
        assert "PESTEL" not in html


class TestCoverageLeads:
    def test_coverage_leads_the_page(self) -> None:
        """Coverage is the first thing a reader sees, not a footnote."""
        html = generate_posture_page(
            {
                "holdings_covered": 26,
                "holdings_total": 64,
                "value_covered_pct": 38.2,
                "uncovered_tickers": ["TSLA"],
                "competitive_verdict": "Moats solides.",
                "swot_verdict": "Équilibré.",
                "strategic_score": 0.71,
                "confidence": 0.83,
                "competitive_landscape_summary": "- Moats **larges** en tech",
            }
        )

        assert "26 / 64" in html
        assert html.index("26 / 64") < html.index("Moats solides.")

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
        assert "<strong>larges</strong>" in body  # markdown rendered, not literal
        assert "**" not in body

    def test_verdicts_are_visible_without_expanding(self) -> None:
        """Each theme's verdict precedes *its own* disclosure, not merely the
        page's first one — two theme blocks each pair a verdict with detail."""
        html = generate_posture_page(_full_posture())
        body = html.split("</style>", 1)[1]

        for verdict in ("Moats solides.", "Équilibré."):
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
                "swot": {"strategic_score": 0.75},
                "five_forces": {"strategic_score": 0.80},
            },
            "MSFT": {
                "swot": {"strategic_score": 0.68},
                "five_forces": {"strategic_score": 0.72},
            },
        }

        html = generate_posture_page(_full_posture(), holdings_strategic=holdings_strategic)

        assert "AAPL" in html
        assert "MSFT" in html
        assert "<table" in html

    def test_missing_framework_on_a_holding_does_not_crash(self) -> None:
        holdings_strategic = {"AAPL": {"swot": {"strategic_score": 0.62}}}

        html = generate_posture_page(_full_posture(), holdings_strategic=holdings_strategic)

        assert "AAPL" in html

    def test_table_has_a_plain_language_legend(self) -> None:
        """SWOT/Porter as bare column headers teach a family reader
        nothing -- a one-sentence gloss must explain what each score means."""
        holdings_strategic = {"AAPL": {"swot": {"strategic_score": 0.62}}}

        html = generate_posture_page(_full_posture(), holdings_strategic=holdings_strategic)
        table_section = html[html.index("Par ligne") :]

        assert "SWOT" in table_section
        assert "Porter" in table_section
        assert "PESTEL" not in table_section
        # A glance-level gloss, not a tutorial: exactly one sentence.
        legend = table_section[table_section.index("<p", table_section.index("</h2>")) : table_section.index("</p>") + len("</p>")]
        assert legend.count(".") == 1

    def test_the_per_holding_table_has_two_score_columns(self) -> None:
        holdings_strategic = {"AAPL": {"swot": {"strategic_score": 0.7}, "five_forces": {"strategic_score": 0.6}}}

        html = generate_posture_page(_full_posture(), holdings_strategic=holdings_strategic)

        assert "<th>SWOT</th>" in html
        assert "<th>Porter</th>" in html
        assert "<th>PESTEL</th>" not in html

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
        # NOTE: deliberately no `"**" not in html` here. This posture's verdicts
        # and lists are empty, so such an assertion could never fail for the
        # property it names. The real markdown property is pinned by
        # TestModelAuthoredSurfacesAreRendered below, against model-shaped text.

    def test_no_citations_does_not_crash_and_omits_sources(self) -> None:
        html = generate_posture_page(_full_posture(), citations=None)

        assert "Sources" not in html


_MODEL_SHAPED = {
    "competitive_verdict": "Moats *larges* mais sous pression [2].",
    "swot_verdict": "Équilibre **fragile** entre croissance et dette [3].",
    "dominant_themes": ["**Résilience** énergétique", "IA *générative* [1]"],
    "portfolio_strengths": ["Moats **larges** en tech [2]"],
    "portfolio_weaknesses": ["Concentration *excessive* [3]"],
    "portfolio_opportunities": ["Transition **énergétique**"],
    "portfolio_threats": ["Durcissement *réglementaire* [1]"],
}


class TestModelAuthoredSurfacesAreRendered:
    """Every model-authored surface goes through the render boundary, not bare escape().

    The original report's defect was 42 literal ``**`` markers and 470 dangling
    ``[n]`` markers. The three prose fields were fixed via
    ``render_markdown_fragment``; verdicts, dominant-theme badges and SWOT list
    items are four *new* model-authored surfaces created on the same branch, and
    each reproduced the defect by calling ``escape()`` directly.

    Not a security property -- ``escape()`` holds either way (pinned separately
    below). This is readability: a family reader must never see raw markdown or
    a citation marker pointing at nothing.
    """

    def _body(self) -> str:
        html = generate_posture_page(_full_posture(**_MODEL_SHAPED))
        return html.split("</style>", 1)[1]

    def test_no_literal_bold_markers_survive_on_any_surface(self) -> None:
        assert "**" not in self._body()

    def test_bold_becomes_strong_on_verdicts_themes_and_swot_items(self) -> None:
        body = self._body()

        assert "<strong>fragile</strong>" in body  # theme verdict
        assert "<strong>Résilience</strong>" in body  # dominant-theme badge
        assert "<strong>larges</strong>" in body  # SWOT list item

    def test_italic_becomes_em(self) -> None:
        body = self._body()

        assert "<em>larges</em>" in body  # competitive verdict
        assert "<em>générative</em>" in body  # dominant-theme badge
        assert "<em>excessive</em>" in body  # SWOT list item

    def test_dangling_citation_markers_are_stripped_not_shown(self) -> None:
        """No citations are supplied, so every [n] points at nothing."""
        body = self._body()

        for marker in ("[1]", "[2]", "[3]"):
            assert marker not in body

    def test_markup_in_model_text_is_still_escaped_not_executed(self) -> None:
        """Routing through the render boundary must stay escape-first."""
        html = generate_posture_page(
            _full_posture(
                swot_verdict="<script>alert(1)</script>",
                dominant_themes=["<img src=x onerror=alert(1)>"],
                portfolio_strengths=["<script>alert(2)</script>"],
            )
        )
        body = html.split("</style>", 1)[1]

        assert "<script>" not in body
        assert "<img" not in body
        assert "&lt;script&gt;" in body


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

        assert "Moats solides." in html
        assert "Équilibré." in html
        assert "finwiz_posture_strategique.html" in html
        assert "macro" not in html.lower()
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

        html = generate_strategic_posture_section(_full_posture(swot_verdict="<script>alert(1)</script>"))

        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_model_shaped_verdicts_render_as_html_not_raw_markdown(self) -> None:
        """The family artifact's two verdict <li>s are model-authored too."""
        from finwiz.reporting.section_generators import generate_strategic_posture_section

        html = generate_strategic_posture_section(_full_posture(**_MODEL_SHAPED))

        assert "**" not in html
        assert "[2]" not in html
        assert "[3]" not in html
        assert "<strong>fragile</strong>" in html
        assert "<em>larges</em>" in html


class TestMissingPostureIsVisibleToTheReader:
    """A posture that failed this run must say so, not vanish.

    Making macro_verdict/competitive_verdict/swot_verdict/strategic_score/
    confidence required was the right call -- a posture built from nothing can
    no longer report a confident midpoint by omission. But it also means a
    truncated or partial model response now fails validation and loses the
    *entire* posture, where before it produced a degraded one. Failing loudly is
    correct; failing silently *to the reader* converts "wrong data" into "lost
    data". The reader cannot otherwise distinguish "synthesis failed this run"
    from "this report never had a posture".
    """

    def _section(self) -> str:
        from finwiz.reporting.section_generators import generate_strategic_posture_section

        return generate_strategic_posture_section(None)

    def test_no_posture_renders_a_visible_unavailable_block(self) -> None:
        assert "indisponible" in self._section().lower()

    def test_the_block_uses_the_reports_existing_warning_convention(self) -> None:
        assert 'class="highlight warning"' in self._section()

    def test_the_block_does_not_link_to_a_page_that_was_never_written(self) -> None:
        """_write_posture_page returns early without a posture, so the companion
        page does not exist. A link to it would be a dead link."""
        assert "finwiz_posture_strategique.html" not in self._section()

    def test_no_score_is_shown_without_a_posture(self) -> None:
        """The block explains an absence; it must not print 0 % as if measured."""
        section = self._section()

        assert "%" not in section

    def test_an_empty_dict_is_treated_the_same_as_none(self) -> None:
        from finwiz.reporting.section_generators import generate_strategic_posture_section

        assert "indisponible" in generate_strategic_posture_section({}).lower()

    def test_a_real_posture_still_renders_no_unavailable_block(self) -> None:
        from finwiz.reporting.section_generators import generate_strategic_posture_section

        html = generate_strategic_posture_section(_full_posture())

        assert "indisponible" not in html.lower()
        assert "finwiz_posture_strategique.html" in html
