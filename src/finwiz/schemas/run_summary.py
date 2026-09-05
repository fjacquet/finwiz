"""The run gate's contract: what a run measured, what it was held to, what it concluded.

Every measured input carries ``available``. "We could not measure this" is a
value here, not an absence -- a check whose input is unavailable FAILs as
"not measured" rather than being skipped. Phase counts have no flag because
an absent phase result is honestly a zero.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Verdict(StrEnum):
    """PASS and WARN exit 0; FAIL exits 1; ERROR -- the gate could not evaluate -- exits 2."""

    PASS = "PASS"  # noqa: S105
    WARN = "WARN"
    FAIL = "FAIL"
    ERROR = "ERROR"


class Severity(StrEnum):
    """FAIL: the report is not trustworthy. WARN: a known gap is still a gap."""

    FAIL = "FAIL"
    WARN = "WARN"


class CoverageInput(BaseModel):
    """From ``RunLedger.coverage()``."""

    available: bool = False
    analyzed: int = Field(default=0, ge=0)
    degraded: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    total: int = Field(default=0, ge=0)


class ValuationInput(BaseModel):
    """Priced holdings -- ``weight is not None`` -- over all holdings. The hero's denominator."""

    available: bool = False
    priced: int = Field(default=0, ge=0)
    total: int = Field(default=0, ge=0)


class FactPackInput(BaseModel):
    """The persisted workstream-C freshness summary."""

    available: bool = False
    fresh: int = Field(default=0, ge=0)
    recent: int = Field(default=0, ge=0)
    stale: int = Field(default=0, ge=0)
    missing: int = Field(default=0, ge=0)
    total: int = Field(default=0, ge=0)
    oldest_stale_fetched_at: datetime | None = None


class PhasesInput(BaseModel):
    """Outcomes of the phases the roadmap tracks as known gaps."""

    discovery_candidates: int = Field(default=0, ge=0)
    alternatives_found: int = Field(default=0, ge=0)
    underperformers: int = Field(default=0, ge=0)
    stress_scenarios: int = Field(default=0, ge=0)
    optimal_allocation: bool = False


class CostInput(BaseModel):
    """From the cost monitor's summary. ``cost_known`` is False if any crew was unpriced."""

    available: bool = False
    total_usd: float = Field(default=0.0, ge=0.0)
    call_count: int = Field(default=0, ge=0)
    cost_known: bool = False
    unpriced_crews: list[str] = Field(default_factory=list)


class GateCheck(BaseModel):
    """One check: what was observed, what it was held to, whether it passed."""

    name: str
    severity: Severity
    passed: bool
    observed: str
    threshold: str
    detail: str = ""


class RunSummary(BaseModel):
    """One document per run. Written to ``output/run_summary.json``."""

    run_id: str
    started_at: datetime | None = None
    finished_at: datetime
    duration_seconds: float | None = Field(default=None, ge=0.0)
    coverage: CoverageInput = Field(default_factory=CoverageInput)
    valuation: ValuationInput = Field(default_factory=ValuationInput)
    fact_pack: FactPackInput = Field(default_factory=FactPackInput)
    phases: PhasesInput = Field(default_factory=PhasesInput)
    cost: CostInput = Field(default_factory=CostInput)
    checks: list[GateCheck] = Field(default_factory=list)
    verdict: Verdict
