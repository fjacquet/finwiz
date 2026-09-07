"""CSS asset file loads correctly through the legacy function API."""

import re

from finwiz.reporting.css_styles import get_report_css


class TestReportCssAsset:
    def test_returns_nonempty_css(self):
        css = get_report_css()
        assert len(css) > 5000  # the stylesheet is ~330 lines
        assert ":root" in css  # design-token variables block
        assert "@media" in css  # responsive queries preserved

    def test_is_cached_across_calls(self):
        assert get_report_css() is get_report_css()  # functools.cache — no re-read per report


class TestTrustBannerCss:
    """The colour-coded data-quality banner (render_trust_banner) must actually be styled.

    python_report_generator.py applies trust-banner-{green,amber,red,blocked}
    classes but report_styles.css had zero rules for any of them -- a status
    signal invisible to the family reading the report.
    """

    def test_all_four_trust_banner_states_have_css_rules(self):
        css = get_report_css()
        for cls in ("trust-banner-green", "trust-banner-amber", "trust-banner-red", "trust-banner-blocked"):
            assert f".{cls}" in css, f"missing CSS rule for .{cls}"

    def test_trust_banner_states_are_visually_distinct(self):
        """Each state must declare its own colours in its own dedicated rule.

        The naive version of this test searched for ``.trust-banner-green``
        anywhere in the stylesheet. That matched the *grouped* selector
        (``.trust-banner-green, .trust-banner-amber, ... {``) which lists all
        four names on one line, so all four extracted blocks were suffixes of
        the same shared body and differed only by leading offset. The assertion
        passed even when every state declared identical colours -- it never
        tested distinctness at all. Anchor on the single-class rule instead.
        """
        css = get_report_css()
        blocks = {}
        for cls in ("trust-banner-green", "trust-banner-amber", "trust-banner-red", "trust-banner-blocked"):
            match = re.search(rf"^\s*\.{re.escape(cls)}\s*\{{(.*?)\}}", css, re.DOTALL | re.MULTILINE)
            assert match is not None, f"no dedicated rule for .{cls} (only a grouped selector?)"
            blocks[cls] = match.group(1).strip()

        # Every state must resolve to its own rule body -- no two states may
        # share a verbatim block, or they'd be indistinguishable at a glance.
        assert len(set(blocks.values())) == 4, f"states share a rule body: {blocks}"
        # And each dedicated rule must actually set a colour, not merely exist.
        for cls, body in blocks.items():
            assert "background" in body or "color" in body, f".{cls} declares no colour: {body!r}"


def _classes_in(html: str) -> set[str]:
    """Every space-separated token that ever appears inside a `class="..."` attribute."""
    classes: set[str] = set()
    for attr_value in re.findall(r'class="([^"]+)"', html):
        classes.update(attr_value.split())
    return classes


class TestPostureAndBannerClassesAreStyled:
    """A class emitted in the markup with no matching CSS rule is an invisible
    signal -- exactly the trust-banner-* and .verdict defects this test exists
    to catch before the next one ships (Task 10/11 review)."""

    def test_every_class_on_the_posture_page_and_trust_banner_has_a_css_rule(self):
        from finwiz.reporting.python_report_generator import render_trust_banner
        from finwiz.reporting.sections.posture_page import generate_posture_page
        from finwiz.schemas.run_ledger import CoverageSummary, TrustBanner

        css = get_report_css()

        posture_html = generate_posture_page(
            {
                "holdings_covered": 26,
                "holdings_total": 64,
                "value_covered_pct": 38.2,
                "uncovered_tickers": ["TSLA"],
                "competitive_verdict": "Moats solides.",
                "swot_verdict": "Équilibré.",
                "strategic_score": 0.71,
                "confidence": 0.83,
                "dominant_themes": ["Résilience énergétique"],
                "portfolio_strengths": ["Moats larges"],
            },
            holdings_strategic={"AAPL": {"swot": {"strategic_score": 0.6}}},
        )
        banner_html = "".join(
            render_trust_banner(TrustBanner.from_coverage(CoverageSummary(analyzed=a, degraded=d, failed=f, total=5))) for a, d, f in [(5, 0, 0), (4, 1, 0), (1, 0, 4), (0, 0, 0)]
        )

        classes = _classes_in(posture_html) | _classes_in(banner_html)
        missing = sorted(cls for cls in classes if f".{cls}" not in css)

        assert not missing, f"classes with no matching CSS rule: {missing}"
