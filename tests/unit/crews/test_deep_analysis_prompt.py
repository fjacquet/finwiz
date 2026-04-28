"""Smoke test: tasks.yaml has FACT PACK section with v5.2 placeholders."""

from __future__ import annotations

from pathlib import Path

import yaml

TASKS_YAML = Path("src/finwiz/crews/deep_analysis/config/tasks.yaml")


def test_tasks_yaml_includes_fact_pack_section() -> None:
    raw = TASKS_YAML.read_text(encoding="utf-8")
    # The FACT PACK block must mention the 4 placeholders we render
    assert "{corporate_structure}" in raw
    assert "{recent_events}" in raw
    assert "{leadership}" in raw
    assert "{fact_pack_freshness}" in raw


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


def test_tasks_yaml_perplexity_budget_is_one() -> None:
    """Perplexity call budget must be reduced to 1 (fact pack pre-loads common checks)."""
    raw = TASKS_YAML.read_text(encoding="utf-8")
    assert "Maximum 1 appel" in raw or "Maximum 1 call" in raw
