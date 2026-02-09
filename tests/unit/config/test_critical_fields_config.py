"""Tests for critical fields configuration and sanity checks."""

import pytest

from finwiz.config.critical_fields_config import CriticalFieldError, validate_critical_fields


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
