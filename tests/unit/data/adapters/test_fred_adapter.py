"""Unit tests for FREDAdapter macro data adapter."""

import pandas as pd
import pytest

from finwiz.data.adapters.fred_adapter import FRED_SERIES, FREDAdapter


class TestFREDAdapter:
    """Tests for FREDAdapter."""

    def test_is_available_with_key(self, mocker):
        mocker.patch.dict("os.environ", {"FRED_API_KEY": "test_key"})
        adapter = FREDAdapter()
        assert adapter.is_available() is True

    def test_is_available_without_key(self, mocker):
        mocker.patch.dict("os.environ", {}, clear=True)
        adapter = FREDAdapter()
        adapter.api_key = None
        assert adapter.is_available() is False

    def test_get_macro_snapshot_success(self, mocker):
        mocker.patch.dict("os.environ", {"FRED_API_KEY": "test_key"})
        adapter = FREDAdapter()

        mock_fred_cls = mocker.patch("fredapi.Fred")
        mock_fred = mock_fred_cls.return_value

        def mock_get_series(series_id, **kwargs):
            values = {
                "FEDFUNDS": 5.25,
                "CPIAUCSL": 3.2,
                "UNRATE": 3.7,
                "A191RL1Q225SBEA": 2.1,
                "DGS10": 4.5,
                "DGS2": 4.8,
                "VIXCLS": 22.5,
            }
            return pd.Series([values.get(series_id, 0.0)])

        mock_fred.get_series.side_effect = mock_get_series

        snapshot = adapter.get_macro_snapshot()
        assert snapshot.fed_rate == 5.25
        assert snapshot.cpi_yoy == 3.2
        assert snapshot.unemployment_rate == 3.7
        assert snapshot.gdp_growth == 2.1
        assert snapshot.treasury_10y == 4.5
        assert snapshot.treasury_2y == 4.8
        assert snapshot.vix == 22.5

    def test_yield_curve_spread_computed(self, mocker):
        mocker.patch.dict("os.environ", {"FRED_API_KEY": "test_key"})
        adapter = FREDAdapter()

        mock_fred_cls = mocker.patch("fredapi.Fred")
        mock_fred = mock_fred_cls.return_value

        def mock_get_series(series_id, **kwargs):
            values = {"DGS10": 4.5, "DGS2": 4.8}
            if series_id in values:
                return pd.Series([values[series_id]])
            return pd.Series(dtype=float)

        mock_fred.get_series.side_effect = mock_get_series

        snapshot = adapter.get_macro_snapshot()
        assert snapshot.yield_curve_spread is not None
        assert abs(snapshot.yield_curve_spread - (-0.3)) < 1e-10

    def test_session_level_caching(self, mocker):
        mocker.patch.dict("os.environ", {"FRED_API_KEY": "test_key"})
        adapter = FREDAdapter()

        mock_fred_cls = mocker.patch("fredapi.Fred")
        mock_fred = mock_fred_cls.return_value
        mock_fred.get_series.return_value = pd.Series([5.25])

        # First call
        snapshot1 = adapter.get_macro_snapshot()
        # Second call should return cached
        snapshot2 = adapter.get_macro_snapshot()

        assert snapshot1 is snapshot2
        # Fred constructor called only once
        assert mock_fred_cls.call_count == 1

    def test_partial_failure_handled(self, mocker):
        mocker.patch.dict("os.environ", {"FRED_API_KEY": "test_key"})
        adapter = FREDAdapter()

        mock_fred_cls = mocker.patch("fredapi.Fred")
        mock_fred = mock_fred_cls.return_value

        def mock_get_series(series_id, **kwargs):
            if series_id == "FEDFUNDS":
                return pd.Series([5.25])
            if series_id == "VIXCLS":
                raise ConnectionError("API timeout")
            return pd.Series(dtype=float)

        mock_fred.get_series.side_effect = mock_get_series

        snapshot = adapter.get_macro_snapshot()
        assert snapshot.fed_rate == 5.25
        assert snapshot.vix is None  # Failed gracefully

    def test_no_api_key_raises(self, mocker):
        mocker.patch.dict("os.environ", {}, clear=True)
        adapter = FREDAdapter()
        adapter.api_key = None
        with pytest.raises(RuntimeError, match="FRED_API_KEY"):
            adapter.get_macro_snapshot()

    def test_all_fred_series_defined(self):
        """All expected macro fields have FRED series mappings."""
        expected_fields = {"fed_rate", "cpi_yoy", "unemployment_rate", "gdp_growth", "treasury_10y", "treasury_2y", "vix"}
        assert set(FRED_SERIES.keys()) == expected_fields
