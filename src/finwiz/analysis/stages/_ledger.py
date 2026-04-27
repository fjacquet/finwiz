"""Persistent run ledger: append-only JSONL + in-memory accessors."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from threading import Lock

from finwiz.schemas.run_ledger import (
    CoverageSummary,
    RunLedgerEntry,
    TrustBanner,
)
from finwiz.schemas.stage_contract import StageOutcome

_TERMINAL_STAGE = "emit"


class RunLedger:
    """Append-only ledger of stage outcomes for one pipeline kickoff."""

    def __init__(self, run_id: str, artifact_dir: Path, total: int = 0) -> None:
        self.run_id = run_id
        self.entries: list[RunLedgerEntry] = []
        self._total = total
        self._lock = Lock()
        artifact_dir.mkdir(parents=True, exist_ok=True)
        self._artifact = artifact_dir / f"{run_id}.jsonl"

    def set_total(self, total: int) -> None:
        with self._lock:
            self._total = total

    def record(self, entry: RunLedgerEntry) -> None:
        with self._lock:
            self.entries.append(entry)
            with self._artifact.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry.model_dump(mode="json"), default=str))
                f.write("\n")

    def _by_ticker_terminal_outcome(self) -> dict[str, StageOutcome]:
        """Outcome of the terminal `emit` stage per ticker.

        A ticker without a terminal-stage record is treated as FAILED
        (pipeline did not reach `emit`).
        """
        seen: dict[str, StageOutcome] = {}
        for entry in self.entries:
            if entry.stage == _TERMINAL_STAGE:
                seen[entry.ticker] = entry.outcome
        return seen

    def _all_tickers_attempted(self) -> set[str]:
        return {e.ticker for e in self.entries}

    def coverage(self) -> CoverageSummary:
        terminal = self._by_ticker_terminal_outcome()
        analyzed = sum(1 for o in terminal.values() if o == StageOutcome.OK)
        # Degraded propagates: emit emits OK but a *prior* qualify was DEGRADED.
        # Count tickers whose qualify was DEGRADED but whose emit was OK.
        degraded_qualifies = {e.ticker for e in self.entries if e.stage == "qualify" and e.outcome == StageOutcome.DEGRADED}
        degraded = sum(1 for ticker, terminal_outcome in terminal.items() if ticker in degraded_qualifies and terminal_outcome == StageOutcome.OK)
        analyzed_clean = analyzed - degraded
        attempted = self._all_tickers_attempted()
        failed = len(attempted) - analyzed
        total = max(self._total, len(attempted))
        return CoverageSummary(
            analyzed=analyzed_clean,
            degraded=degraded,
            failed=failed,
            total=total,
        )

    def failed_tickers(self) -> list[str]:
        terminal = self._by_ticker_terminal_outcome()
        attempted = sorted(self._all_tickers_attempted())
        return [t for t in attempted if terminal.get(t) != StageOutcome.OK]

    def to_banner(self) -> TrustBanner:
        return TrustBanner.from_coverage(self.coverage())

    def entries_for(self, ticker: str) -> list[RunLedgerEntry]:
        return [e for e in self.entries if e.ticker == ticker]

    def append_many(self, entries: Iterable[RunLedgerEntry]) -> None:
        for e in entries:
            self.record(e)
