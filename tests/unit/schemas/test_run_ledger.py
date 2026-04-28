from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from finwiz.schemas.run_ledger import (
    CoverageSummary,
    RunLedgerEntry,
    TrustBanner,
)
from finwiz.schemas.stage_contract import StageOutcome


def test_ledger_entry_minimum_fields() -> None:
    entry = RunLedgerEntry(
        run_id="01HZ...",
        ticker="DELL",
        started_at=datetime(2026, 4, 27, 9, 0, tzinfo=UTC),
        finished_at=datetime(2026, 4, 27, 9, 0, 1, tzinfo=UTC),
        stage="collect",
        outcome=StageOutcome.OK,
    )
    assert entry.cost_usd == 0.0
    assert entry.retries_used == 0


def test_ledger_entry_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        RunLedgerEntry(
            run_id="x",
            ticker="X",
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
            stage="collect",
            outcome=StageOutcome.OK,
            unknown_field=1,
        )


@pytest.mark.parametrize(
    ("analyzed", "degraded", "failed", "total", "expected_state", "expected_block"),
    [
        # blocked
        (0, 0, 0, 0, "blocked", True),
        (0, 0, 0, 5, "blocked", True),
        (0, 0, 5, 5, "blocked", True),  # zero analyzed even with attempts
        # red — strictly more than half failed (2 * failed > total)
        (1, 0, 4, 5, "red", True),  # 2*4=8 > 5
        (10, 0, 11, 21, "red", True),  # 2*11=22 > 21
        # amber — degraded > 0 OR 0 < failed and 2*failed <= total
        (4, 1, 0, 5, "amber", False),
        (4, 0, 1, 5, "amber", False),  # 2*1=2 <= 5
        (10, 0, 10, 21, "amber", False),  # 2*10=20 <= 21, not blocked
        # green — all OK
        (5, 0, 0, 5, "green", False),
    ],
)
def test_banner_state_rules(
    analyzed: int,
    degraded: int,
    failed: int,
    total: int,
    expected_state: str,
    expected_block: bool,
) -> None:
    summary = CoverageSummary(analyzed=analyzed, degraded=degraded, failed=failed, total=total)
    banner = TrustBanner.from_coverage(summary)
    assert banner.state == expected_state
    assert banner.block_decisions is expected_block
    assert banner.message  # non-empty


def test_banner_message_red_includes_warning() -> None:
    banner = TrustBanner.from_coverage(CoverageSummary(analyzed=1, degraded=0, failed=4, total=5))
    assert "NE PAS" in banner.message
