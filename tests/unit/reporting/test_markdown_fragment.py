"""Tests for the escape-first markdown render boundary.

``render_markdown_fragment`` is the only place model-authored text (Perplexity
prose, which quotes live web pages verbatim) is allowed to become HTML. Every
test here either proves a markdown convention renders correctly, or proves an
injection vector is neutralized.
"""

from __future__ import annotations

from finwiz.reporting.markdown_fragment import render_markdown_fragment, render_markdown_inline


class TestEscapeBoundary:
    def test_html_in_model_output_is_escaped_not_executed(self) -> None:
        """Perplexity quotes live web pages into its output. Treat it as text."""
        out = render_markdown_fragment("<script>alert(1)</script> et **gras**")

        assert "<script>" not in out
        assert "&lt;script&gt;" in out
        assert "<strong>gras</strong>" in out

    def test_tag_shaped_text_is_escaped(self) -> None:
        out = render_markdown_fragment("<b>hello</b>")

        assert "<b>hello</b>" not in out
        assert "&lt;b&gt;hello&lt;/b&gt;" in out

    def test_french_apostrophes_render_cleanly_as_text(self) -> None:
        """quote=True (the html.escape default) would turn every apostrophe into
        &#x27;, which is noisy for French prose rendered as text content (not an
        attribute). Apostrophes and accented characters must survive untouched.
        """
        out = render_markdown_fragment("L'inflation reste élevée, dit l'expert français.")

        assert "&#x27;" not in out
        assert "&apos;" not in out
        assert "L'inflation" in out
        assert "élevée" in out
        assert "français" in out


class TestBoldAndItalic:
    def test_bullets_and_bold_become_html(self) -> None:
        out = render_markdown_fragment("- **Politique** : durcissement\n- Économique : porteur")

        assert out.count("<li>") == 2
        assert "<strong>Politique</strong>" in out

    def test_italic_renders_as_em(self) -> None:
        out = render_markdown_fragment("Un ton *prudent* domine.")

        assert "<em>prudent</em>" in out


class TestNestedBullets:
    def test_two_level_bullets_render_nested_ul(self) -> None:
        raw = "- **Politique / Régulation**\n  - Durcissement de la surveillance\n  - Nouvelle taxe carbone\n- **Économie**\n  - Ralentissement attendu"
        out = render_markdown_fragment(raw)

        assert "<li><strong>Politique / Régulation</strong><ul><li>Durcissement de la surveillance</li><li>Nouvelle taxe carbone</li></ul></li>" in out
        assert "<li><strong>Économie</strong><ul><li>Ralentissement attendu</li></ul></li>" in out
        assert out.count("<ul>") == 3  # one outer list + one nested list per top-level item
        assert out.count("<li>") == 5  # 2 top-level + 3 nested

    def test_deeper_indentation_flattens_to_one_nested_level(self) -> None:
        """Real output only has two meaningful levels. A third level of indentation
        must not produce doubly-nested <ul><ul>; it flattens into the single nested
        level instead of being dropped or breaking structure.
        """
        raw = "- Top\n  - Sub A\n    - Sub Sub B\n- Top2"
        out = render_markdown_fragment(raw)

        assert "<ul><ul>" not in out
        assert out.count("<ul>") == 2  # outer + one nested list under "Top" (Top2 has none)
        assert "<li>Top<ul><li>Sub A</li><li>Sub Sub B</li></ul></li>" in out
        assert "<li>Top2</li>" in out

    def test_flat_bullets_are_not_wrongly_nested(self) -> None:
        """The original bug: stripping indentation before checking it flattened
        genuine sub-bullets into the top level. Guard the non-nested case too.
        """
        out = render_markdown_fragment("- Un\n- Deux\n- Trois")

        assert out.count("<li>") == 3
        assert "<ul>" not in out.replace("<ul>", "", 1)  # exactly one <ul>, no nested lists


class TestCitations:
    def test_citation_marker_without_a_source_is_removed(self) -> None:
        """A number that looks like sourcing must not point at nothing."""
        out = render_markdown_fragment("Un fait[7].", citations=["https://a.example"])

        assert "[7]" not in out
        assert "<a " not in out

    def test_citation_marker_with_a_source_becomes_a_link(self) -> None:
        out = render_markdown_fragment("Un fait[1].", citations=["https://a.example"])

        assert 'href="https://a.example"' in out

    def test_no_citations_supplied_strips_every_marker(self) -> None:
        """Known limitation (see module docstring): no caller threads citations
        through today. Every marker must still be removed cleanly rather than
        left dangling as a bare, meaningless '[3]' in the rendered report.
        """
        out = render_markdown_fragment("Fait A[1]. Fait B[2].")

        assert "[1]" not in out
        assert "[2]" not in out
        assert "<a " not in out


class TestOrderOfOperations:
    """Markup insertion (citations produce a real <a> tag) must happen AFTER the
    bold/italic regexes run, not before — otherwise those regexes scan text that
    already contains inserted HTML, and a citation URL containing '*' characters
    could be misread as a bold/italic delimiter and corrupt the anchor markup.
    """

    def test_bold_italic_and_citation_survive_together(self) -> None:
        out = render_markdown_fragment("**gras**[1] et *italique*", citations=["https://a.example"])

        assert "<strong>gras</strong>" in out
        assert "<em>italique</em>" in out
        assert out.count("<a ") == 1
        assert 'href="https://a.example"' in out
        # The anchor must be a single well-formed tag, not split by a stray <strong>/<em>
        assert '<sup><a href="https://a.example" rel="noopener noreferrer" target="_blank">1</a></sup>' in out

    def test_citation_url_containing_asterisks_is_not_bolded(self) -> None:
        """If citation substitution ran before bold/italic, '**evil**' inside the
        URL would be turned into <strong>evil</strong>, corrupting the href
        attribute. Substituting citations last prevents the regexes from ever
        seeing the inserted markup.
        """
        out = render_markdown_fragment("Un fait[1].", citations=["https://a.example/**evil**"])

        assert "<strong>" not in out
        assert 'href="https://a.example/**evil**"' in out


class TestCitationUrlInjection:
    """A citation URL is model-supplied data (Perplexity's own return_citations
    list) and must never become an executable href.
    """

    def test_javascript_url_is_not_linked(self) -> None:
        out = render_markdown_fragment("Fait[1].", citations=["javascript:alert(1)"])

        assert "javascript:" not in out
        assert "<a " not in out

    def test_data_url_is_not_linked(self) -> None:
        out = render_markdown_fragment("Fait[1].", citations=["data:text/html,<script>alert(1)</script>"])

        assert "data:" not in out
        assert "<script>" not in out
        assert "<a " not in out

    def test_attribute_breaking_quote_in_citation_url_is_neutralized(self) -> None:
        malicious = 'https://a.example/"><script>alert(1)</script>'
        out = render_markdown_fragment("Fait[1].", citations=[malicious])

        assert "<script>alert(1)</script>" not in out
        assert "&quot;" in out


class TestEmptyInput:
    def test_empty_string_renders_empty(self) -> None:
        assert render_markdown_fragment("") == ""

    def test_whitespace_only_text_produces_no_paragraph(self) -> None:
        assert "<p>" not in render_markdown_fragment("   \n  \n")


class TestInlineSibling:
    """``render_markdown_inline`` is the same boundary without block wrapping.

    Verdicts, dominant-theme badges and SWOT list items are model-authored, but
    they land inside a ``<p class="verdict">``, a ``<span class="badge">`` or an
    ``<li>`` that the caller already owns. ``render_markdown_fragment`` would
    nest a ``<p>`` (or a whole ``<ul>``) inside them. The inline sibling exists
    so those surfaces can stop calling bare ``escape()`` -- which is what
    reintroduced literal ``**`` and dangling ``[n]`` markers on the posture and
    family pages -- without inheriting block markup they cannot host.
    """

    def test_no_block_wrapping(self) -> None:
        out = render_markdown_inline("Un verdict simple.")

        assert out == "Un verdict simple."
        assert "<p>" not in out

    def test_a_leading_dash_is_text_not_a_list(self) -> None:
        """A one-line fragment starting with '- ' must not become a <ul>."""
        out = render_markdown_inline("- Moats larges")

        assert "<ul>" not in out
        assert "<li>" not in out
        assert "Moats larges" in out

    def test_bold_and_italic_render(self) -> None:
        out = render_markdown_inline("Le **durcissement** reste *net*.")

        assert "<strong>durcissement</strong>" in out
        assert "<em>net</em>" in out
        assert "**" not in out

    def test_dangling_citation_marker_is_stripped(self) -> None:
        out = render_markdown_inline("Un fait[7].")

        assert "[7]" not in out
        assert "<sup>" not in out

    def test_citation_marker_links_when_a_source_exists(self) -> None:
        out = render_markdown_inline("Un fait[1].", citations=["https://example.com/a"])

        assert '<sup><a href="https://example.com/a"' in out

    def test_html_is_escaped_not_executed(self) -> None:
        out = render_markdown_inline("<script>alert(1)</script>")

        assert "<script>" not in out
        assert "&lt;script&gt;" in out

    def test_empty_and_none_render_empty(self) -> None:
        assert render_markdown_inline("") == ""
        assert render_markdown_inline(None) == ""

    def test_non_string_input_is_coerced(self) -> None:
        """Posture fields come from a model_dump; a list item may not be a str."""
        assert render_markdown_inline(42) == "42"

    def test_multiline_text_collapses_to_one_line(self) -> None:
        """Inline surfaces have no block structure to express a line break."""
        out = render_markdown_inline("Première ligne\nseconde ligne")

        assert "\n" not in out
        assert "Première ligne seconde ligne" in out
