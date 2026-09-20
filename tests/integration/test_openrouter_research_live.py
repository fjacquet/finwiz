"""One live web-grounded SWOT call. Costs about $0.02; skipped without a key."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

from finwiz.analysis.strategic_research import SYSTEM_FR, _swot_prompt
from finwiz.infrastructure.research.openrouter_structured import openrouter_structured
from finwiz.schemas.hybrid_analysis.strategic import SwotAnalysis

# dotenv_values() reads the file without mutating os.environ, unlike
# load_dotenv() -- this module is imported at COLLECTION time on every
# default `make test` (marker deselection happens after import), so a
# load_dotenv() here loaded the whole .env into every test's environment.
# The .env file is checked first (the source of truth for local dev),
# os.getenv as a fallback for CI/shell-exported keys; either way _KEY is
# captured once here, at collection time, before tests/conftest.py's
# autouse isolation fixture clears OPENROUTER_API_KEY per test.
_KEY = dotenv_values(Path(__file__).resolve().parents[2] / ".env").get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")

pytestmark = [pytest.mark.integration, pytest.mark.skipif(not _KEY, reason="OPENROUTER_API_KEY not set")]


async def test_live_swot_validates_and_reports_cost():
    result = await openrouter_structured(
        prompt=_swot_prompt("SAN.PA", "Healthcare", "Pharmaceuticals", "Sanofi", "20 septembre 2026"),
        schema=SwotAnalysis,
        system=SYSTEM_FR,
        timeout=90.0,
        api_key=_KEY,
    )

    assert result is not None
    assert isinstance(result.data, SwotAnalysis)
    assert result.data.strengths
    assert result.cost_usd is not None and result.cost_usd > 0
    assert result.citations
