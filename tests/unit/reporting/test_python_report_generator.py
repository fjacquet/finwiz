"""Tests for render_trust_banner in python_report_generator."""

import pytest

from finwiz.reporting.python_report_generator import render_trust_banner
from finwiz.schemas.run_ledger import CoverageSummary, TrustBanner


@pytest.mark.parametrize(
    ("summary", "expected_class"),
    [
        (CoverageSummary(analyzed=5, degraded=0, failed=0, total=5), "trust-banner-green"),
        (CoverageSummary(analyzed=4, degraded=1, failed=0, total=5), "trust-banner-amber"),
        (CoverageSummary(analyzed=1, degraded=0, failed=4, total=5), "trust-banner-red"),
        (CoverageSummary(analyzed=0, degraded=0, failed=0, total=5), "trust-banner-blocked"),
    ],
)
def test_render_trust_banner_uses_state_class(summary: CoverageSummary, expected_class: str) -> None:
    """render_trust_banner picks the CSS class that matches TrustBanner.state."""
    banner = TrustBanner.from_coverage(summary)
    html = render_trust_banner(banner)
    assert expected_class in html
    assert banner.message in html


def test_render_trust_banner_includes_block_decisions_attribute() -> None:
    """render_trust_banner writes data-block-decisions when the banner blocks decisions."""
    banner = TrustBanner.from_coverage(CoverageSummary(analyzed=1, degraded=0, failed=4, total=5))
    html = render_trust_banner(banner)
    assert 'data-block-decisions="true"' in html


def test_render_trust_banner_block_decisions_false_for_green() -> None:
    """render_trust_banner emits data-block-decisions=false for a green banner."""
    banner = TrustBanner.from_coverage(CoverageSummary(analyzed=5, degraded=0, failed=0, total=5))
    html = render_trust_banner(banner)
    assert 'data-block-decisions="false"' in html


def test_render_trust_banner_contains_counts() -> None:
    """render_trust_banner embeds analyzed/total/degraded/failed counts."""
    summary = CoverageSummary(analyzed=3, degraded=1, failed=1, total=5)
    banner = TrustBanner.from_coverage(summary)
    html = render_trust_banner(banner)
    assert "3/5" in html
    assert "1 dégradés" in html
    assert "1 échoués" in html
