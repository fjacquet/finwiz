"""Tests for backtesting performance NaN handling."""

from finwiz.quantitative.backtesting_performance import _safe_int


class TestSafeInt:
    """Tests for _safe_int helper that guards against NaN."""

    def test_should_convert_normal_int(self):
        """Normal integer values pass through unchanged."""
        assert _safe_int(5) == 5

    def test_should_convert_normal_float_to_int(self):
        """Normal float values are truncated to int."""
        assert _safe_int(3.0) == 3

    def test_should_return_default_for_nan(self):
        """NaN should return the default value."""
        assert _safe_int(float("nan")) == 0

    def test_should_return_default_for_none(self):
        """None should return the default value."""
        assert _safe_int(None) == 0

    def test_should_return_custom_default_for_nan(self):
        """NaN with custom default should return that default."""
        assert _safe_int(float("nan"), default=-1) == -1

    def test_should_return_default_for_string(self):
        """Non-numeric strings should return the default."""
        assert _safe_int("invalid") == 0

    def test_should_handle_zero(self):
        """Zero is a valid value, not NaN."""
        assert _safe_int(0) == 0

    def test_should_handle_negative_int(self):
        """Negative integers pass through."""
        assert _safe_int(-3) == -3
