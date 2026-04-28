"""Run ledger entry, coverage summary, and trust banner schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from finwiz.schemas.stage_contract import StageName, StageOutcome


class RunLedgerEntry(BaseModel):
    """One row of the persistent run ledger.

    Written as JSONL to ``output/run_ledger/<run_id>.jsonl``.
    """

    run_id: str
    ticker: str
    started_at: datetime
    finished_at: datetime
    stage: StageName
    outcome: StageOutcome
    reason: str | None = None
    fallback_used: str | None = None
    retries_used: int = 0
    cost_usd: float = 0.0

    model_config = ConfigDict(extra="forbid")


class CoverageSummary(BaseModel):
    """Aggregate counts derived from the ledger."""

    analyzed: int  # holdings whose final stage emitted OK
    degraded: int  # holdings whose final stage emitted DEGRADED
    failed: int  # holdings whose pipeline did not produce a verdict
    total: int  # holdings attempted

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _check_counts(self) -> CoverageSummary:
        if any(v < 0 for v in (self.analyzed, self.degraded, self.failed, self.total)):
            raise ValueError("counts must be non-negative")
        if self.analyzed + self.degraded + self.failed > self.total:
            raise ValueError("analyzed + degraded + failed cannot exceed total")
        return self


class TrustBanner(BaseModel):
    """User-visible trust banner derived deterministically from coverage."""

    state: Literal["green", "amber", "red", "blocked"]
    analyzed: int
    degraded: int
    failed: int
    total: int
    message: str
    block_decisions: bool

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_coverage(cls, summary: CoverageSummary) -> TrustBanner:
        """Apply the deterministic state-rule ladder (top-to-bottom, first match)."""
        analyzed = summary.analyzed
        degraded = summary.degraded
        failed = summary.failed
        total = summary.total

        state: Literal["green", "amber", "red", "blocked"]
        message: str
        block: bool

        if total == 0 or analyzed == 0:
            state = "blocked"
            message = "Aucune analyse complète n'a été produite. NE PAS prendre de décisions sur ce rapport."
            block = True
        elif 2 * failed > total:
            state = "red"
            message = f"{failed}/{total} holdings ont échoué. NE PAS prendre de décisions sur ce rapport."
            block = True
        elif degraded > 0 or failed > 0:
            state = "amber"
            parts = []
            if degraded:
                parts.append(f"{degraded} en mode dégradé (proxy quantitatif)")
            if failed:
                parts.append(f"{failed} en attente d'analyse")
            message = "Confiance partielle: " + ", ".join(parts) + "."
            block = False
        else:
            state = "green"
            message = f"Analyse complète: {analyzed}/{total} holdings."
            block = False

        return cls(
            state=state,
            analyzed=analyzed,
            degraded=degraded,
            failed=failed,
            total=total,
            message=message,
            block_decisions=block,
        )
