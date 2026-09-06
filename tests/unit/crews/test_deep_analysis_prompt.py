"""Smoke test: tasks.yaml has FACT PACK section with v5.2 placeholders."""

from __future__ import annotations

from pathlib import Path

import yaml

TASKS_YAML = Path("src/finwiz/crews/deep_analysis/config/tasks.yaml")


def test_tasks_yaml_includes_fact_pack_section() -> None:
    raw = TASKS_YAML.read_text(encoding="utf-8")
    # The FACT PACK block is rendered by finwiz.analysis.fact_pack.render as one
    # pre-labeled block, so the prompt template carries a single placeholder for it.
    assert "{fact_pack_block}" in raw
    assert "FACT PACK" in raw


def test_tasks_yaml_does_not_claim_perplexity_verification() -> None:
    """The v5.2 fact pack is sourced from yfinance/SEC/news, not Perplexity.

    Claiming "vérifié via Perplexity" in the prompt was false under the
    per-asset-class design and must not reappear.
    """
    raw = TASKS_YAML.read_text(encoding="utf-8")
    assert "vérifié via Perplexity" not in raw


def test_tasks_yaml_contains_anti_hallucination_rule() -> None:
    raw = TASKS_YAML.read_text(encoding="utf-8")
    # Must say FACT PACK is authoritative
    assert "AUTORITAIRE" in raw or "autoritaire" in raw


def test_tasks_yaml_is_valid_yaml() -> None:
    """Ensure the file parses as valid YAML after edits."""
    raw = TASKS_YAML.read_text(encoding="utf-8")
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    assert "deep_qualitative_analysis_task" in parsed


def test_tasks_yaml_has_no_external_tool_block() -> None:
    """Round-2 fix (2026-04-29): the asset_analyst agent runs with zero tools.

    The fact_pack stage already runs Perplexity deterministically before
    qualify, so the prompt must NOT advertise a verification tool the agent
    doesn't have. Mismatch between prompt and reality risks the LLM emitting
    unsupported tool calls — and was a major contributor to the 600s budget
    exhaustion on the 2026-04-29 run (DELL spent 24 minutes in the agent
    reasoning loop).
    """
    raw = TASKS_YAML.read_text(encoding="utf-8")
    assert "OUTIL DE VÉRIFICATION" not in raw
    assert "Perplexity Sonar Search" not in raw
    assert "Maximum 1 appel" not in raw  # old budget directive must be gone
