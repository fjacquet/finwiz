"""Live network test for the FX provider. Excluded from default `make test`."""

import pytest

from finwiz.data import fx_rates


@pytest.mark.integration
def test_live_chf_eur_rate_is_plausible():
    fx_rates.clear_fx_cache()
    rate = fx_rates.get_fx_rate("CHF", "EUR")

    assert rate is not None
    assert 0.5 < rate < 2.0  # sanity band, not a precise assertion
