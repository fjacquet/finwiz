"""Stage contract types: outcome enum, provenance, and result envelope."""

from __future__ import annotations

from enum import StrEnum


class StageOutcome(StrEnum):
    """Result of executing a single pipeline stage.

    OK       - stage produced its expected payload
    DEGRADED - stage produced a fallback payload (qualify stage only)
    FAILED   - stage did not produce any payload
    """

    OK = "ok"
    DEGRADED = "degraded"
    FAILED = "failed"
