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

    def test_transient_failure_retried_and_recovers(self, mocker):
        """Tenacity retries transient errors and recovers on third attempt."""
        mocker.patch.dict("os.environ", {"FRED_API_KEY": "test_key"})
        adapter = FREDAdapter()

        mock_fred_cls = mocker.patch("fredapi.Fred")
        mock_fred = mock_fred_cls.return_value

        call_counts: dict[str, int] = {s: 0 for s in FRED_SERIES.values()}

        def mock_get_series(series_id, **kwargs):
            call_counts[series_id] += 1
            if series_id == "FEDFUNDS" and call_counts[series_id] < 3:
                raise ConnectionError("transient 500")
            return pd.Series([5.25])

        mock_fred.get_series.side_effect = mock_get_series

        # Speed up the test by patching sleep
        mocker.patch("tenacity.nap.time.sleep", return_value=None)

        snapshot = adapter.get_macro_snapshot()
        assert snapshot.fed_rate == 5.25
        assert call_counts["FEDFUNDS"] == 3  # 2 failures + 1 success

    def test_all_series_fail_falls_back_to_cache(self, mocker, tmp_path):
        """When all FRED series fail, loads the on-disk JSON cache."""
        mocker.patch.dict("os.environ", {"FRED_API_KEY": "test_key"})

        # Pre-seed an on-disk cache.
        from finwiz.data.adapters import fred_adapter as fred_module
        from finwiz.schemas.macro import MacroSnapshot

        cache_path = tmp_path / "fred_snapshot.json"
        cached = MacroSnapshot(
            fed_rate=4.0,
            cpi_yoy=3.0,
            unemployment_rate=4.2,
            treasury_10y=4.5,
            treasury_2y=4.8,
            vix=18.0,
            data_sources={"fed_rate": "FRED:FEDFUNDS"},
        )
        cache_path.write_text(cached.model_dump_json(), encoding="utf-8")
        mocker.patch.object(fred_module, "FRED_CACHE_PATH", cache_path)

        adapter = FREDAdapter()
        mock_fred_cls = mocker.patch("fredapi.Fred")
        mock_fred = mock_fred_cls.return_value
        mock_fred.get_series.side_effect = ConnectionError("down")
        mocker.patch("tenacity.nap.time.sleep", return_value=None)

        snapshot = adapter.get_macro_snapshot()
        assert snapshot.fed_rate == 4.0  # from cache
        assert snapshot.vix == 18.0

    def test_successful_snapshot_is_persisted(self, mocker, tmp_path):
        """A successful snapshot is written to disk as JSON."""
        mocker.patch.dict("os.environ", {"FRED_API_KEY": "test_key"})

        from finwiz.data.adapters import fred_adapter as fred_module

        cache_path = tmp_path / "fred_snapshot.json"
        mocker.patch.object(fred_module, "FRED_CACHE_PATH", cache_path)

        adapter = FREDAdapter()
        mock_fred_cls = mocker.patch("fredapi.Fred")
        mock_fred = mock_fred_cls.return_value
        mock_fred.get_series.return_value = pd.Series([5.25])

        adapter.get_macro_snapshot()
        assert cache_path.exists()

        # Verify it's valid Pydantic JSON
        from finwiz.schemas.macro import MacroSnapshot

        reloaded = MacroSnapshot.model_validate_json(cache_path.read_text())
        assert reloaded.fed_rate == 5.25


class TestCPIIsARateNotAnIndexLevel:
    """CPIAUCSL is an index level, not a rate.

    Taking its latest observation as ``cpi_yoy`` put "IPC (Inflation) 332.8 %"
    in the family report and pinned the indicator permanently red, since the
    scorer's band tops out at 5 %. The field must carry the year-over-year
    rate its name promises, which FRED computes server-side via ``units=pc1``.
    """

    def test_cpi_is_requested_as_percent_change_from_a_year_ago(self, mocker):
        mocker.patch.dict("os.environ", {"FRED_API_KEY": "test_key"})
        adapter = FREDAdapter()

        mock_fred_cls = mocker.patch("fredapi.Fred")
        mock_fred = mock_fred_cls.return_value
        mock_fred.get_series.return_value = pd.Series([2.4])

        adapter.get_macro_snapshot()

        cpi_calls = [c for c in mock_fred.get_series.call_args_list if c.args and c.args[0] == "CPIAUCSL"]
        assert cpi_calls, "CPIAUCSL was never requested"
        assert cpi_calls[0].kwargs.get("units") == "pc1", "CPI fetched as a raw index level, not a YoY rate"

    def test_other_series_are_not_transformed(self, mocker):
        """Only CPI needs a transform; asking for pc1 on a rate would double-derive it."""
        mocker.patch.dict("os.environ", {"FRED_API_KEY": "test_key"})
        adapter = FREDAdapter()

        mock_fred_cls = mocker.patch("fredapi.Fred")
        mock_fred = mock_fred_cls.return_value
        mock_fred.get_series.return_value = pd.Series([4.1])

        adapter.get_macro_snapshot()

        for call in mock_fred.get_series.call_args_list:
            if call.args and call.args[0] != "CPIAUCSL":
                assert "units" not in call.kwargs, f"{call.args[0]} was transformed unexpectedly"

    def test_the_transform_is_recorded_in_data_sources(self, mocker):
        """A silently transformed series is unauditable; the source must say so."""
        mocker.patch.dict("os.environ", {"FRED_API_KEY": "test_key"})
        adapter = FREDAdapter()

        mock_fred_cls = mocker.patch("fredapi.Fred")
        mock_fred = mock_fred_cls.return_value
        mock_fred.get_series.return_value = pd.Series([2.4])

        snapshot = adapter.get_macro_snapshot()

        assert snapshot.data_sources["cpi_yoy"] == "FRED:CPIAUCSL(pc1)"
        assert snapshot.data_sources["fed_rate"] == "FRED:FEDFUNDS"
