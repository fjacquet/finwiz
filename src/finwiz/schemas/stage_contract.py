"""Stage contract types: outcome enum, provenance, and result envelope."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class StageOutcome(StrEnum):
    """Result of executing a single pipeline stage.

    OK       - stage produced its expected payload
    DEGRADED - stage produced a fallback payload (qualify stage only)
    FAILED   - stage did not produce any payload
    """

    OK = "ok"
    DEGRADED = "degraded"
    FAILED = "failed"


StageName = Literal["collect", "quantify", "qualify", "synthesize", "emit"]


class StageProvenance(BaseModel):
    """Diagnostic record produced by every stage execution."""

    stage: StageName
    outcome: StageOutcome
    reason: str | None = None
    duration_ms: int
    retries_used: int = 0
    fallback_used: str | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _check_degraded_only_in_qualify(self) -> StageProvenance:
        """Invariant I1: only the `qualify` stage may emit DEGRADED."""
        if self.outcome == StageOutcome.DEGRADED and self.stage != "qualify":
            raise ValueError(f"DEGRADED outcome forbidden for stage '{self.stage}'; only 'qualify' may degrade")
        return self

    @model_validator(mode="after")
    def _check_fallback_implies_degraded(self) -> StageProvenance:
        """Invariant I3: fallback_used populated ⇒ outcome == DEGRADED."""
        if self.fallback_used is not None and self.outcome != StageOutcome.DEGRADED:
            raise ValueError(f"fallback_used='{self.fallback_used}' requires outcome=DEGRADED, got {self.outcome}")
        return self
