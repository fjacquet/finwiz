"""Tests for critical fields configuration and sanity checks."""

import pytest

from finwiz.config.critical_fields_config import CriticalFieldError, normalize_volatility, validate_critical_fields


def _make_stock_data(**overrides):
    """Create minimal valid stock data with all critical fields."""
    base = {
        "current_price": 50.0,
        "roe": 0.15,
        "debt_to_equity": 0.8,
        "revenue_growth": 0.10,
        "volatility": 0.25,
        "beta": 1.1,
    }
    base.update(overrides)
    return base


class TestRoeSanityCheck:
    """Tests for ROE sanity check in validate_critical_fields."""

    def test_should_accept_roe_zero(self):
        """ROE=0.0 is valid for pre-profit companies (e.g. RBRK, NTNX)."""
        data = _make_stock_data(roe=0.0)
        validate_critical_fields("RBRK", "stock", data)  # Should not raise

    def test_should_accept_negative_roe(self):
        """ROE=-0.50459 is valid for temporarily unprofitable companies (e.g. KUD.SW)."""
        data = _make_stock_data(roe=-0.50459)
        validate_critical_fields("KUD.SW", "stock", data)  # Should not raise

    def test_should_accept_moderate_positive_roe(self):
        """ROE=1.5 (150%) is valid for high-growth companies."""
        data = _make_stock_data(roe=1.5)
        validate_critical_fields("TEST", "stock", data)  # Should not raise

    def test_should_flag_extreme_positive_roe(self):
        """ROE=6.0 (600%) is extreme and likely a data error."""
        data = _make_stock_data(roe=6.0)
        with pytest.raises(CriticalFieldError):
            validate_critical_fields("TEST", "stock", data)

    def test_should_flag_extreme_negative_roe(self):
        """ROE=-6.0 (-600%) is extreme and likely a data error."""
        data = _make_stock_data(roe=-6.0)
        with pytest.raises(CriticalFieldError):
            validate_critical_fields("TEST", "stock", data)


class TestNormalizeVolatility:
    """Tests for normalize_volatility() — coercing raw volatility to the fractional scale."""

    def test_fractional_volatility_passes_through(self):
        """Values already on the fractional scale (0.25 = 25%) are returned unchanged."""
        assert normalize_volatility(0.25) == 0.25

    def test_percent_scaled_volatility_is_rescaled(self):
        """Values on the percent scale (25.3 = 25.3%) are rescaled to fractional."""
        assert normalize_volatility(25.3) == pytest.approx(0.253)

    def test_absurd_volatility_is_rejected(self):
        """Values above the absurd ceiling are neither real fractional nor percent readings — reject as None."""
        assert normalize_volatility(900.0) is None

    def test_negative_volatility_is_rejected(self):
        """Negative volatility is not physically meaningful — reject as None."""
        assert normalize_volatility(-0.25) is None

    def test_none_stays_none(self):
        """A missing reading stays missing."""
        assert normalize_volatility(None) is None

    def test_zero_is_preserved_not_treated_as_missing(self):
        """A genuine 0.0 volatility reading must not be coerced to None."""
        assert normalize_volatility(0.0) == 0.0

    def test_ceiling_boundary_is_rejected(self):
        """Exactly the absurd ceiling (500.0) is rejected, not silently accepted as a valid 500% reading (Ruling 13)."""
        assert normalize_volatility(500.0) is None

    def test_just_below_ceiling_is_still_rescaled(self):
        """Just under the ceiling is still treated as percent-scaled and rescaled, not rejected."""
        assert normalize_volatility(499.9) == pytest.approx(4.999)

    def test_rescale_threshold_boundary_passes_through_unchanged(self):
        """Exactly 5.0 sits at the rescale threshold (not > 5.0) and is left unchanged, not divided by 100."""
        assert normalize_volatility(5.0) == 5.0


class TestVolatilityGateNormalization:
    """Tests that validate_critical_fields normalizes volatility before the sanity check runs."""

    def test_percent_scaled_volatility_no_longer_rejected_by_gate(self):
        """A percent-scaled volatility (25.3) must not be reported as an invalid value by the gate."""
        data = _make_stock_data(volatility=25.3)
        validate_critical_fields("TEST", "stock", data)  # Should not raise

    def test_gate_normalizes_volatility_in_place(self):
        """After validation, the normalized fractional value replaces the raw percent-scaled one."""
        data = _make_stock_data(volatility=25.3)
        validate_critical_fields("TEST", "stock", data)
        assert data["volatility"] == pytest.approx(0.253)

    def test_absurd_volatility_still_fails_the_gate(self):
        """An absurd volatility reading (900.0) is still rejected, just as a units error rather than merely missing."""
        data = _make_stock_data(volatility=900.0)
        with pytest.raises(CriticalFieldError):
            validate_critical_fields("TEST", "stock", data)

    def test_absurd_volatility_reported_as_invalid_not_missing(self):
        """Risk A fix: a present-but-absurd volatility must be named honestly as invalid, not masked as missing."""
        data = _make_stock_data(volatility=900.0)
        with pytest.raises(CriticalFieldError) as exc_info:
            validate_critical_fields("TEST", "stock", data)
        assert "volatility (invalid value: 900.0)" in exc_info.value.missing_fields

    def test_negative_volatility_reported_as_invalid_not_missing(self):
        """A present-but-negative volatility must also be named as invalid, not masked as missing."""
        data = _make_stock_data(volatility=-5.0)
        with pytest.raises(CriticalFieldError) as exc_info:
            validate_critical_fields("TEST", "stock", data)
        assert "volatility (invalid value: -5.0)" in exc_info.value.missing_fields

    def test_none_volatility_still_reported_as_missing(self):
        """A raw None must still fall through to the ordinary "(missing)" message, not "(invalid value)"."""
        data = _make_stock_data(volatility=None)
        with pytest.raises(CriticalFieldError) as exc_info:
            validate_critical_fields("TEST", "stock", data)
        assert "volatility (missing)" in exc_info.value.missing_fields

    def test_gate_accepts_zero_volatility(self):
        """A genuine 0.0 volatility must pass the gate through validate_critical_fields itself, not just the bare function."""
        data = _make_stock_data(volatility=0.0)
        validate_critical_fields("TEST", "stock", data)  # Should not raise
        assert data["volatility"] == 0.0

    def test_gate_rejects_ceiling_boundary_volatility(self):
        """A volatility of exactly 500.0 must still fail the gate (Ruling 13 boundary)."""
        data = _make_stock_data(volatility=500.0)
        with pytest.raises(CriticalFieldError) as exc_info:
            validate_critical_fields("TEST", "stock", data)
        assert "volatility (invalid value: 500.0)" in exc_info.value.missing_fields

    def test_gate_accepts_rescale_threshold_boundary_volatility(self):
        """A volatility of exactly 5.0 sits at the rescale threshold and must pass the gate unchanged."""
        data = _make_stock_data(volatility=5.0)
        validate_critical_fields("TEST", "stock", data)  # Should not raise
        assert data["volatility"] == 5.0
