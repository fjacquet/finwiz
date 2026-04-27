"""Hypothesis property tests for stage contract invariants."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from finwiz.schemas.run_ledger import CoverageSummary, TrustBanner
from finwiz.schemas.stage_contract import StageOutcome


@given(
    analyzed=st.integers(min_value=0, max_value=100),
    degraded=st.integers(min_value=0, max_value=100),
    failed=st.integers(min_value=0, max_value=100),
    total=st.integers(min_value=0, max_value=300),
)
def test_banner_state_is_one_of_four(analyzed: int, degraded: int, failed: int, total: int) -> None:
    """For any valid coverage tuple, the banner state is one of 4 known values."""
    if analyzed + degraded + failed > total:
        return  # invalid input — CoverageSummary's validator would reject this
    summary = CoverageSummary(analyzed=analyzed, degraded=degraded, failed=failed, total=total)
    banner = TrustBanner.from_coverage(summary)
    assert banner.state in {"green", "amber", "red", "blocked"}


@given(st.sampled_from(list(StageOutcome)))
def test_str_enum_round_trip(outcome: StageOutcome) -> None:
    """StageOutcome serialises and round-trips via its string value."""
    assert StageOutcome(outcome.value) == outcome


@given(
    analyzed=st.integers(min_value=1, max_value=50),
    total=st.integers(min_value=1, max_value=50),
)
def test_green_state_implies_no_block(analyzed: int, total: int) -> None:
    """When the banner is green, decisions are NOT blocked."""
    if analyzed != total:
        return  # green requires analyzed == total
    s = CoverageSummary(analyzed=analyzed, degraded=0, failed=0, total=total)
    banner = TrustBanner.from_coverage(s)
    if banner.state == "green":
        assert banner.block_decisions is False
