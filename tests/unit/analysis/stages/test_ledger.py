from datetime import UTC, datetime
from pathlib import Path

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.schemas.run_ledger import RunLedgerEntry
from finwiz.schemas.stage_contract import StageOutcome


def _entry(ticker: str, stage: str, outcome: StageOutcome) -> RunLedgerEntry:
    now = datetime(2026, 4, 27, 9, 0, tzinfo=UTC)
    return RunLedgerEntry(
        run_id="r1",
        ticker=ticker,
        started_at=now,
        finished_at=now,
        stage=stage,
        outcome=outcome,
    )


def test_ledger_records_entries_in_memory(tmp_path: Path) -> None:
    ledger = RunLedger(run_id="r1", artifact_dir=tmp_path)
    ledger.record(_entry("AAPL", "collect", StageOutcome.OK))
    ledger.record(_entry("AAPL", "emit", StageOutcome.OK))
    assert len(ledger.entries) == 2


def test_ledger_writes_jsonl(tmp_path: Path) -> None:
    ledger = RunLedger(run_id="r1", artifact_dir=tmp_path)
    ledger.record(_entry("AAPL", "collect", StageOutcome.OK))
    artifact = tmp_path / "r1.jsonl"
    assert artifact.exists()
    lines = artifact.read_text().splitlines()
    assert len(lines) == 1
    assert "AAPL" in lines[0]


def test_ledger_coverage_counts_terminal_stage_only(tmp_path: Path) -> None:
    ledger = RunLedger(run_id="r1", artifact_dir=tmp_path, total=2)
    # AAPL succeeds end-to-end
    for s in ("collect", "quantify", "qualify", "synthesize", "emit"):
        ledger.record(_entry("AAPL", s, StageOutcome.OK))
    # MSFT degrades at qualify
    ledger.record(_entry("MSFT", "collect", StageOutcome.OK))
    ledger.record(_entry("MSFT", "quantify", StageOutcome.OK))
    ledger.record(_entry("MSFT", "qualify", StageOutcome.DEGRADED))
    ledger.record(_entry("MSFT", "synthesize", StageOutcome.OK))
    ledger.record(_entry("MSFT", "emit", StageOutcome.OK))
    summary = ledger.coverage()
    assert summary.analyzed == 1
    assert summary.degraded == 1
    assert summary.failed == 0
    assert summary.total == 2


def test_ledger_failed_tickers_lists_unanalyzed(tmp_path: Path) -> None:
    ledger = RunLedger(run_id="r1", artifact_dir=tmp_path, total=2)
    ledger.record(_entry("AAPL", "collect", StageOutcome.OK))
    ledger.record(_entry("AAPL", "emit", StageOutcome.OK))
    ledger.record(_entry("MSFT", "collect", StageOutcome.FAILED))
    assert ledger.failed_tickers() == ["MSFT"]
