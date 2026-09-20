"""The deep-analysis prompt must keep a long static prefix for implicit prompt caching.

OpenRouter applies Gemini's implicit cache when two requests share a prefix
longer than ~1 024 tokens. CrewAI renders the agent goal into the system
prompt and the task description into the user turn, so the cacheable prefix
is exactly: system prompt + the text of the description before its first
placeholder. These tests pin that prefix so a future prompt edit cannot move
per-holding data back to the top.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

import yaml

from finwiz.analysis._helpers import _build_crew_inputs
from finwiz.analysis.deep_analysis_pipeline import AnalysisContext
from finwiz.schemas.hybrid_analysis import QuantitativeAnalysis
from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONFIG = _REPO_ROOT / "src/finwiz/crews/deep_analysis/config"

# Static French instruction text is ~3 500 characters (~1 200 tokens), just
# above the Flash cache threshold. Guard a little below that so a wording
# tweak does not flap the test, but a reorder cannot pass.
_MIN_STATIC_PREFIX_CHARS = 3000

_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


def _agent_goal() -> str:
    agents = yaml.safe_load((_CONFIG / "agents.yaml").read_text(encoding="utf-8"))
    return agents["asset_analyst"]["goal"]


def _task_description() -> str:
    tasks = yaml.safe_load((_CONFIG / "tasks.yaml").read_text(encoding="utf-8"))
    return tasks["deep_qualitative_analysis_task"]["description"]


def test_agent_goal_has_no_placeholder() -> None:
    """The goal lands in the system prompt; one placeholder there breaks the prefix for every holding."""
    assert "{" not in _agent_goal()


def test_task_description_starts_with_a_long_static_block() -> None:
    description = _task_description()
    first = description.find("{")
    assert first != -1, "the description must still interpolate per-holding data"
    assert first >= _MIN_STATIC_PREFIX_CHARS, f"first placeholder at char {first}; static prefix too short for the cache threshold"


def test_every_placeholder_is_a_crew_input_key() -> None:
    """A renamed placeholder would raise at kickoff; catch it here instead."""
    ctx = AnalysisContext(ticker="TEST", asset_class="stock", company_name="Test Co")
    # Same minimal valid shape as tests/unit/analysis/test_helpers.py::_make_quant.
    quant = QuantitativeAnalysis(
        composite_score=0.65,
        fundamental_score=0.70,
        technical_score=0.60,
        risk_score=2.5,
        grade="B",
        preliminary_recommendation="HOLD",
        fundamental_metrics={"roe": 0.15},
        technical_indicators={"rsi": 55.0},
        risk_metrics={"volatility": 0.18},
        calculation_timestamp=datetime.now(UTC),
        data_quality=DataQualityMetrics(completeness_score=0.9, freshness_score=1.0, accuracy_confidence=0.85, source_reliability=0.85, missing_fields=[]),
        confidence_level=0.85,
        python_rationale="fixture rationale for prompt layout test",
    )
    inputs = _build_crew_inputs(ctx, quant)

    placeholders = set(_PLACEHOLDER.findall(_task_description()))
    assert placeholders, "no placeholder found; the regex or the template is wrong"
    assert placeholders <= set(inputs), f"placeholders without a crew input: {placeholders - set(inputs)}"
