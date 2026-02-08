"""Unit tests for TiingoAdapter async interface."""

import pytest

from finwiz.data.adapters.base_adapter import DataAcquisitionError
from finwiz.data.adapters.tiingo_adapter import TiingoAdapter


class TestTiingoAdapter:
    """Test TiingoAdapter async interface compliance."""

    def test_should_be_unavailable_without_api_key(self, mocker):
        """Adapter reports unavailable when no API key set."""
        mocker.patch.dict("os.environ", {}, clear=True)
        adapter = TiingoAdapter()
        assert adapter.is_available() is False

    def test_should_be_available_with_api_key(self, mocker):
        """Adapter reports available when API key is set."""
        mocker.patch.dict("os.environ", {"TIINGO_API_KEY": "test-key"})
        adapter = TiingoAdapter()
        assert adapter.is_available() is True

    def test_should_have_correct_source_name(self, mocker):
        """Source name is tiingo."""
        mocker.patch.dict("os.environ", {}, clear=True)
        adapter = TiingoAdapter()
        assert adapter.source_name == "tiingo"

    def test_should_initialize_with_timeout(self, mocker):
        """Adapter stores timeout from BaseDataAdapter."""
        mocker.patch.dict("os.environ", {}, clear=True)
        adapter = TiingoAdapter(timeout_seconds=5.0)
        assert adapter.timeout_seconds == 5.0

    @pytest.mark.asyncio
    async def test_should_raise_when_unavailable(self, mocker):
        """get_fundamental_data raises when no API key."""
        mocker.patch.dict("os.environ", {}, clear=True)
        adapter = TiingoAdapter()
        with pytest.raises(DataAcquisitionError, match="not available"):
            await adapter.get_fundamental_data("AAPL")

    @pytest.mark.asyncio
    async def test_should_return_fundamental_data(self, mocker):
        """get_fundamental_data returns FundamentalData on success."""
        mocker.patch.dict("os.environ", {"TIINGO_API_KEY": "test-key"})
        adapter = TiingoAdapter(timeout_seconds=5.0)

        mocker.patch.object(
            adapter,
            "get_fundamentals",
            return_value={"roe": 0.18, "debt_to_equity": 0.6, "revenue_growth": 0.12, "profit_margin": 0.10},
        )

        result = await adapter.get_fundamental_data("AAPL")

        assert result.ticker == "AAPL"
        assert result.source == "Tiingo"
        assert result.return_on_equity == 0.18
        assert result.confidence == 0.75
