"""Unit tests for macro schemas (MacroSnapshot)."""

import pytest
from pydantic import ValidationError

from finwiz.schemas.macro import MacroSnapshot


class TestMacroSnapshot:
    """Tests for MacroSnapshot schema validation."""

    def test_empty_snapshot(self):
        s = MacroSnapshot()
        assert s.fed_rate is None
        assert s.cpi_yoy is None
        assert s.vix is None
        assert s.fear_greed_index is None
        assert s.data_sources == {}

    def test_full_snapshot(self):
        s = MacroSnapshot(
            fed_rate=5.25,
            cpi_yoy=3.2,
            unemployment_rate=3.7,
            gdp_growth=2.1,
            treasury_10y=4.5,
            treasury_2y=4.8,
            yield_curve_spread=-0.3,
            vix=22.5,
            fear_greed_index=35,
            fear_greed_label="Fear",
            data_sources={"fed_rate": "FRED:FEDFUNDS", "vix": "FRED:VIXCLS"},
        )
        assert s.fed_rate == 5.25
        assert s.yield_curve_spread == -0.3
        assert s.fear_greed_index == 35
        assert s.fear_greed_label == "Fear"

    def test_fear_greed_range(self):
        s = MacroSnapshot(fear_greed_index=0)
        assert s.fear_greed_index == 0
        s = MacroSnapshot(fear_greed_index=100)
        assert s.fear_greed_index == 100

    def test_fear_greed_out_of_range(self):
        with pytest.raises(ValidationError):
            MacroSnapshot(fear_greed_index=-1)
        with pytest.raises(ValidationError):
            MacroSnapshot(fear_greed_index=101)

    def test_fear_greed_invalid_label(self):
        with pytest.raises(ValidationError):
            MacroSnapshot(fear_greed_label="Very Scared")

    def test_fear_greed_valid_labels(self):
        for label in ("Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"):
            s = MacroSnapshot(fear_greed_label=label)
            assert s.fear_greed_label == label

    def test_is_recession_signal_inverted_curve(self):
        s = MacroSnapshot(yield_curve_spread=-0.5)
        assert s.is_recession_signal() is True

    def test_is_recession_signal_normal_curve(self):
        s = MacroSnapshot(yield_curve_spread=1.5)
        assert s.is_recession_signal() is False

    def test_is_recession_signal_no_data(self):
        s = MacroSnapshot()
        assert s.is_recession_signal() is False

    def test_get_market_regime_high_vix(self):
        s = MacroSnapshot(vix=35.0)
        assert s.get_market_regime() == "high_volatility"

    def test_get_market_regime_elevated_vix(self):
        s = MacroSnapshot(vix=25.0)
        assert s.get_market_regime() == "elevated_volatility"

    def test_get_market_regime_recession_risk(self):
        s = MacroSnapshot(vix=15.0, yield_curve_spread=-0.3)
        assert s.get_market_regime() == "recession_risk"

    def test_get_market_regime_normal(self):
        s = MacroSnapshot(vix=15.0, yield_curve_spread=1.0)
        assert s.get_market_regime() == "normal"

    def test_get_market_regime_unknown(self):
        s = MacroSnapshot()
        assert s.get_market_regime() == "unknown"

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            MacroSnapshot(unknown_field="bad")

    def test_serialization_roundtrip(self):
        s = MacroSnapshot(fed_rate=5.25, vix=22.5, fear_greed_index=50, fear_greed_label="Neutral")
        json_str = s.model_dump_json()
        restored = MacroSnapshot.model_validate_json(json_str)
        assert restored.fed_rate == s.fed_rate
        assert restored.vix == s.vix
        assert restored.fear_greed_index == s.fear_greed_index
