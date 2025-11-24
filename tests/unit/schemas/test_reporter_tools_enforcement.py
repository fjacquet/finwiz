from __future__ import annotations

from pathlib import Path

import yaml


def test_final_reporter_has_no_tools() -> None:
    agents_yaml = Path(__file__).resolve().parents[3] / "src/finwiz/crews/report_crew/config/agents.yaml"
    assert agents_yaml.exists(), f"agents.yaml not found at {agents_yaml}"

    data = yaml.safe_load(agents_yaml.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "agents.yaml should load to a mapping"

    assert "investment_reporter" in data, "investment_reporter agent missing"
    reporter = data["investment_reporter"] or {}
    # No tools key, or if present it must be empty/falsy
    assert not reporter.get("tools"), "investment_reporter must not declare any tools"
