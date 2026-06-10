"""Direct unit tests for the decomposed context-preparation loaders."""

import pytest

from finwiz.crews.helpers.context_preparation import (
    _load_backtesting_data,
    _load_discovery_data,
    _load_reporter_input,
    _summarize_availability,
    _track_crew_availability,
    _track_portfolio_stats,
)


class TestLoadReporterInput:
    """Tests for _load_reporter_input."""

    def test_promotes_portfolio_review_to_top_level(self, mocker):
        """portfolio_review must be extracted from consolidated_crew_data['portfolio']."""
        holdings = [{"ticker": "AAPL"}, {"ticker": "MSFT"}]
        mock_accessor = mocker.MagicMock()
        mock_accessor.get_consolidated_reporter_input.return_value = {
            "consolidated_crew_data": {"portfolio": {"holdings": holdings}},
        }
        mocker.patch("finwiz.crews.helpers.context_preparation.DeepAnalysisExtractor.load_deep_analysis_html_files", return_value={})

        result = _load_reporter_input(mock_accessor, max_age_hours=24)

        assert result["portfolio_review"] == {"holdings": holdings}
        mock_accessor.get_consolidated_reporter_input.assert_called_once_with(24)

    def test_sets_portfolio_review_none_when_missing(self, mocker):
        """portfolio_review must be None when 'portfolio' key absent from consolidated_crew_data."""
        mock_accessor = mocker.MagicMock()
        mock_accessor.get_consolidated_reporter_input.return_value = {"consolidated_crew_data": {}}
        mocker.patch("finwiz.crews.helpers.context_preparation.DeepAnalysisExtractor.load_deep_analysis_html_files", return_value={})

        result = _load_reporter_input(mock_accessor, max_age_hours=1)

        assert result["portfolio_review"] is None

    def test_attaches_deep_analysis_html_content(self, mocker):
        """deep_analysis_html_content must equal whatever load_deep_analysis_html_files returns."""
        html_content = {"AAPL": "<html>...</html>"}
        mock_accessor = mocker.MagicMock()
        mock_accessor.get_consolidated_reporter_input.return_value = {"consolidated_crew_data": {}}
        mocker.patch("finwiz.crews.helpers.context_preparation.DeepAnalysisExtractor.load_deep_analysis_html_files", return_value=html_content)

        result = _load_reporter_input(mock_accessor, max_age_hours=24)

        assert result["deep_analysis_html_content"] == html_content


class TestTrackCrewAvailability:
    """Tests for _track_crew_availability."""

    def _make_report(self, mocker, *, stock=True, etf=True, crypto=True):
        r = mocker.MagicMock()
        r.stock_available = stock
        r.etf_available = etf
        r.crypto_available = crypto
        r.data_freshness_summary = {}
        return r

    def test_marks_all_three_crews_available(self, mocker):
        """When all asset types are available the tracker receives three 'available' calls."""
        tracker = mocker.MagicMock()
        report = self._make_report(mocker)
        mocker.patch("finwiz.crews.helpers.context_preparation.DataAgeExtractor.extract_age_from_summary", return_value=2.5)
        integrated = {"stock_analysis_data": [1, 2], "etf_analysis_data": [3], "crypto_analysis_data": []}

        _track_crew_availability(integrated, report, tracker, max_age_hours=24)

        sources = {c.kwargs["source"]: c.kwargs["status"] for c in tracker.track_data_source.call_args_list}
        assert sources["stock_crew"] == "available"
        assert sources["etf_crew"] == "available"
        assert sources["crypto_crew"] == "available"

    def test_marks_unavailable_when_asset_missing(self, mocker):
        """When etf_available is False the tracker gets status='unavailable' for etf_crew."""
        tracker = mocker.MagicMock()
        report = self._make_report(mocker, etf=False)
        mocker.patch("finwiz.crews.helpers.context_preparation.DataAgeExtractor.extract_age_from_summary", return_value=1.0)

        _track_crew_availability({}, report, tracker, max_age_hours=24)

        etf_call = next(c for c in tracker.track_data_source.call_args_list if c.kwargs["source"] == "etf_crew")
        assert etf_call.kwargs["status"] == "unavailable"
        assert "ETF" in etf_call.kwargs["error_message"]

    def test_passes_record_count_to_tracker(self, mocker):
        """record_count must equal len(integrated_data[data_key])."""
        tracker = mocker.MagicMock()
        report = self._make_report(mocker, etf=False, crypto=False)
        mocker.patch("finwiz.crews.helpers.context_preparation.DataAgeExtractor.extract_age_from_summary", return_value=0.5)

        _track_crew_availability({"stock_analysis_data": ["a", "b", "c"]}, report, tracker, max_age_hours=24)

        stock_call = next(c for c in tracker.track_data_source.call_args_list if c.kwargs["source"] == "stock_crew")
        assert stock_call.kwargs["record_count"] == 3


class TestTrackPortfolioStats:
    """Tests for _track_portfolio_stats."""

    def _make_report(self, mocker, *, portfolio=True):
        r = mocker.MagicMock()
        r.portfolio_available = portfolio
        r.data_freshness_summary = {}
        return r

    def test_tracks_unavailable_when_portfolio_not_present(self, mocker):
        tracker = mocker.MagicMock()
        _track_portfolio_stats({}, self._make_report(mocker, portfolio=False), tracker, max_age_hours=24)

        tracker.track_data_source.assert_called_once_with(source="portfolio_review", status="unavailable", error_message="Portfolio review data not found")

    def test_builds_deep_analysis_summary_when_holdings_exist(self, mocker):
        """deep_analysis_summary must be populated from portfolio holdings."""
        tracker = mocker.MagicMock()
        mocker.patch("finwiz.crews.helpers.context_preparation.DataAgeExtractor.extract_age_from_summary", return_value=1.0)
        holdings = [
            {"ticker": "AAPL", "crew_analysis_used": True, "alternatives": ["ALT1"]},
            {"ticker": "MSFT", "crew_analysis_used": True, "alternatives": []},
            {"ticker": "BTC", "crew_analysis_used": False},
        ]
        integrated = {"portfolio_review": {"holdings": holdings}}

        _track_portfolio_stats(integrated, self._make_report(mocker), tracker, max_age_hours=24)

        summary = integrated["deep_analysis_summary"]
        assert summary["total_holdings"] == 3
        assert summary["deep_analysis_count"] == 2
        assert summary["shallow_analysis_count"] == 1
        assert summary["holdings_with_alternatives"] == 1
        assert summary["deep_analysis_percentage"] == pytest.approx(200 / 3)

    def test_sets_deep_analysis_summary_none_when_no_crew_analysis(self, mocker):
        """deep_analysis_summary must be None when no holding has crew_analysis_used."""
        tracker = mocker.MagicMock()
        mocker.patch("finwiz.crews.helpers.context_preparation.DataAgeExtractor.extract_age_from_summary", return_value=1.0)
        integrated = {"portfolio_review": {"holdings": [{"ticker": "AAPL", "crew_analysis_used": False}]}}

        _track_portfolio_stats(integrated, self._make_report(mocker), tracker, max_age_hours=24)

        assert integrated["deep_analysis_summary"] is None


class TestLoadDiscoveryData:
    """Tests for _load_discovery_data."""

    def test_uses_accessor_status_and_tracks_unavailable(self, mocker):
        """When discovery has no results the tracker records it as unavailable."""
        accessor = mocker.MagicMock()
        tracker = mocker.MagicMock()
        mocker.patch(
            "finwiz.crews.helpers.context_preparation.DiscoveryStatusHelper.get_discovery_status",
            return_value={"has_results": False, "message": "Discovery not run", "status": "not_run"},
        )

        result = _load_discovery_data(accessor, inputs=None, availability_tracker=tracker)

        assert result["discovery_status"]["has_results"] is False
        assert result["aplus_discovery_results"] is None
        assert result["aplus_opportunities_summary"] == "Discovery not run"
        tracker.track_data_source.assert_called_once_with(source="aplus_discovery", status="unavailable", error_message="Discovery not run")

    def test_prefers_aplus_opportunities_from_inputs_over_file(self, mocker):
        """When inputs['aplus_opportunities'] is present it is preferred over file loading."""
        accessor = mocker.MagicMock()
        tracker = mocker.MagicMock()
        mocker.patch(
            "finwiz.crews.helpers.context_preparation.DiscoveryStatusHelper.get_discovery_status",
            return_value={"has_results": True, "message": "available", "status": "available"},
        )
        in_memory = [{"ticker": "NVDA", "grade": "A+"}]
        accessor.get_opportunities_summary.return_value = "1 A+ opportunity found"

        result = _load_discovery_data(accessor, inputs={"aplus_opportunities": in_memory}, availability_tracker=tracker)

        assert result["aplus_discovery_results"] == in_memory
        accessor.load_discovery_results.assert_not_called()

    def test_falls_back_to_file_load_when_inputs_empty(self, mocker):
        """When inputs are absent the accessor.load_discovery_results is called."""
        accessor = mocker.MagicMock()
        tracker = mocker.MagicMock()
        mocker.patch(
            "finwiz.crews.helpers.context_preparation.DiscoveryStatusHelper.get_discovery_status",
            return_value={"has_results": True, "message": "available", "status": "available"},
        )
        file_results = {"stocks": {"a_plus_candidates": [{"ticker": "AMD"}]}}
        accessor.load_discovery_results.return_value = file_results
        accessor.get_opportunities_summary.return_value = "1 A+ opportunity found"

        result = _load_discovery_data(accessor, inputs=None, availability_tracker=tracker)

        accessor.load_discovery_results.assert_called_once()
        assert result["aplus_discovery_results"] == file_results


class TestLoadBacktestingData:
    """Tests for _load_backtesting_data."""

    def test_marks_backtesting_unavailable_when_no_data(self, mocker):
        """When BacktestingStatusHelper returns has_backtesting_data=False the tracker marks it unavailable."""
        accessor = mocker.MagicMock()
        extractor = mocker.MagicMock()
        tracker = mocker.MagicMock()
        mocker.patch(
            "finwiz.crews.helpers.context_preparation.BacktestingStatusHelper.get_backtesting_status",
            return_value={"has_backtesting_data": False, "message": "No backtesting", "status": "not_available"},
        )
        mocker.patch(
            "finwiz.crews.helpers.context_preparation._extract_backtesting_data_from_results",
            return_value={"has_backtesting_data": False, "message": "No backtesting", "status": "not_available"},
        )

        result = _load_backtesting_data(accessor, extractor, inputs=None, availability_tracker=tracker)

        assert result["backtesting_data"] is None
        assert result["backtesting_summary"] is None
        assert result["backtesting_status"]["has_data"] is False
        tracker.track_data_source.assert_called_once_with(source="backtesting", status="unavailable", error_message="No backtesting")

    def test_populates_backtesting_data_when_available(self, mocker):
        """When backtesting data exists it is included in the result under expected keys."""
        accessor = mocker.MagicMock()
        extractor = mocker.MagicMock()
        tracker = mocker.MagicMock()
        candidates = {"NVDA": {"metrics": {}, "formatted_display": "", "available_metrics": []}}
        mocker.patch(
            "finwiz.crews.helpers.context_preparation.BacktestingStatusHelper.get_backtesting_status",
            return_value={"has_backtesting_data": True, "validation_results": []},
        )
        mocker.patch(
            "finwiz.crews.helpers.context_preparation._extract_backtesting_data_from_results",
            return_value={
                "has_backtesting_data": True,
                "message": "Backtesting data available for 1 candidates",
                "status": "available",
                "backtesting_by_candidate": candidates,
                "summary": {"total_candidates_tested": 1},
                "total_candidates": 1,
            },
        )

        result = _load_backtesting_data(accessor, extractor, inputs=None, availability_tracker=tracker)

        assert result["backtesting_data"] == candidates
        assert result["backtesting_summary"] == {"total_candidates_tested": 1}
        assert result["backtesting_status"]["has_data"] is True
        tracker.track_data_source.assert_called_once_with(source="backtesting", status="available", record_count=1)


class TestSummarizeAvailability:
    """Tests for _summarize_availability."""

    def test_returns_model_dump_and_formatted(self, mocker):
        """The result must contain both data_availability_summary and *_formatted."""
        tracker = mocker.MagicMock()
        summary_mock = mocker.MagicMock()
        summary_mock.model_dump.return_value = {"total_sources": 3, "available_sources": 2, "unavailable_sources": 1, "stale_sources": 0}
        summary_mock.total_sources = 3
        summary_mock.available_sources = 2
        summary_mock.unavailable_sources = 1
        summary_mock.stale_sources = 0
        tracker.get_availability_summary.return_value = summary_mock
        tracker.format_summary_for_report.return_value = "formatted report"

        result = _summarize_availability(tracker)

        assert result["data_availability_summary"] == {"total_sources": 3, "available_sources": 2, "unavailable_sources": 1, "stale_sources": 0}
        assert result["data_availability_summary_formatted"] == "formatted report"
        tracker.get_availability_summary.assert_called_once()
        tracker.format_summary_for_report.assert_called_once_with(summary_mock)
