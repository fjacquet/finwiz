"""Unit tests for FearGreedAdapter."""

from types import SimpleNamespace

import pytest

from finwiz.data.adapters.base_adapter import DataAcquisitionError
from finwiz.data.adapters.fear_greed_adapter import FearGreedAdapter, _score_to_label


class TestScoreToLabel:
    """Tests for score-to-label classification."""

    def test_extreme_fear(self):
        assert _score_to_label(0) == "Extreme Fear"
        assert _score_to_label(25) == "Extreme Fear"

    def test_fear(self):
        assert _score_to_label(26) == "Fear"
        assert _score_to_label(45) == "Fear"

    def test_neutral(self):
        assert _score_to_label(46) == "Neutral"
        assert _score_to_label(55) == "Neutral"

    def test_greed(self):
        assert _score_to_label(56) == "Greed"
        assert _score_to_label(75) == "Greed"

    def test_extreme_greed(self):
        assert _score_to_label(76) == "Extreme Greed"
        assert _score_to_label(100) == "Extreme Greed"


class TestFearGreedAdapter:
    """Tests for FearGreedAdapter."""

    def test_is_available_always_true(self):
        adapter = FearGreedAdapter()
        assert adapter.is_available() is True

    def test_primary_library_success(self, mocker):
        mock_fg = mocker.patch("fear_and_greed.get")
        mock_fg.return_value = SimpleNamespace(value=35.0, description="Fear")

        adapter = FearGreedAdapter()
        value, label = adapter.get_fear_greed()
        assert value == 35
        assert label == "Fear"

    def test_http_fallback_when_library_fails(self, mocker):
        mock_fg = mocker.patch("fear_and_greed.get", side_effect=ConnectionError("Library failed"))

        mock_response = mocker.MagicMock()
        mock_response.json.return_value = {"fear_and_greed": {"score": 72}}
        mock_response.raise_for_status.return_value = None
        mocker.patch("requests.get", return_value=mock_response)

        adapter = FearGreedAdapter()
        value, label = adapter.get_fear_greed()
        assert value == 72
        assert label == "Greed"

    def test_raises_when_all_fail(self, mocker):
        mocker.patch("fear_and_greed.get", side_effect=ConnectionError("Library failed"))
        mocker.patch("requests.get", side_effect=ConnectionError("HTTP failed"))

        adapter = FearGreedAdapter()
        with pytest.raises(DataAcquisitionError, match="Fear & Greed index unavailable"):
            adapter.get_fear_greed()

    def test_session_caching(self, mocker):
        mock_fg = mocker.patch("fear_and_greed.get")
        mock_fg.return_value = SimpleNamespace(value=50.0, description="Neutral")

        adapter = FearGreedAdapter()
        result1 = adapter.get_fear_greed()
        result2 = adapter.get_fear_greed()

        assert result1 == result2
        # Library called only once
        assert mock_fg.call_count == 1
