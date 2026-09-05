"""The gate's thresholds are settings; its severities are not."""

from __future__ import annotations

import pytest

from finwiz.config import settings as settings_module
from finwiz.config.settings import RunGateSettings, get_settings, reset_settings


@pytest.fixture(autouse=True)
def _fresh_settings():
    reset_settings()
    yield
    reset_settings()


class TestRunGateSettings:
    def test_defaults_match_the_spec(self) -> None:
        gate = RunGateSettings()
        assert (gate.min_coverage_ratio, gate.min_priced_ratio, gate.max_stale_ratio) == (0.95, 0.95, 0.25)

    def test_is_nested_on_finwiz_settings(self) -> None:
        assert isinstance(get_settings().gate, RunGateSettings)

    def test_env_override_through_the_nested_delimiter(self, monkeypatch) -> None:
        monkeypatch.setenv("FINWIZ_GATE__MAX_STALE_RATIO", "0.10")
        reset_settings()
        assert get_settings().gate.max_stale_ratio == pytest.approx(0.10)

    def test_ratios_are_bounded(self) -> None:
        with pytest.raises(ValueError):
            RunGateSettings(max_stale_ratio=1.5)

    def test_module_exposes_no_severity_knob(self) -> None:
        """Moving a check between FAIL and WARN is a design decision, made in code."""
        assert not [f for f in RunGateSettings.model_fields if "severity" in f or "fail" in f or "warn" in f]
        assert not hasattr(settings_module, "GateSeveritySettings")
