"""Tests for the coverage wiring at the strategic-posture call site.

Task 6 made ``PortfolioStrategicPosture`` require ``holdings_covered`` /
``holdings_total`` / ``value_covered_pct`` / ``uncovered_tickers`` as
keyword-only arguments to ``synthesize_portfolio_posture_sync``. Its only
production caller, ``ReportEnrichmentMixin._synthesize_portfolio_strategic``,
was not updated — every call raised ``TypeError``, which the method's
blanket ``except Exception`` swallowed as "non-fatal", silently dropping the
whole strategic-posture section from every report.

These tests pin:
  - the coverage numbers (count AND value) are computed correctly from real
    portfolio holdings, not fabricated;
  - a gap is always named, never averaged away;
  - the call site actually threads ``portfolio_review.holdings`` through to
    ``_synthesize_portfolio_strategic`` (the seam a stale-signature bug like
    this one lives in);
  - a genuine programming error (TypeError/AttributeError) propagates
    instead of being logged as "non-fatal" and hidden.
"""

from __future__ import annotations

from typing import Any

import pytest

from finwiz.orchestrators.reporting.enrichment import ReportEnrichmentMixin
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.hybrid_analysis.strategic import (
    FiveForcesAnalysis,
    PestelAnalysis,
    PortfolioStrategicPosture,
    StrategicAnalysis,
    SwotAnalysis,
)
from finwiz.schemas.portfolio_review import HoldingDecision


def _risk() -> RiskAssessmentStandardized:
    return RiskAssessmentStandardized(score=2.5, level="Medium")


def _holding(ticker: str, *, eur_value: float | None = None) -> HoldingDecision:
    return HoldingDecision(
        ticker=ticker,
        name=f"{ticker} Inc.",
        asset_class="stock",
        currency="USD",
        decision="KEEP",
        composite_score=0.7,
        grade="B",
        grade_description="Solide",
        recommended_action="Conserver",
        risk=_risk(),
        eur_value=eur_value,
    )


def _valid_strategic() -> dict[str, Any]:
    return StrategicAnalysis(
        pestel=PestelAnalysis(strategic_score=0.6, confidence=0.7),
        swot=SwotAnalysis(strategic_score=0.5, confidence=0.6),
        five_forces=FiveForcesAnalysis(strategic_score=0.4, confidence=0.5),
    ).model_dump()


def _valid_posture(**overrides: Any) -> PortfolioStrategicPosture:
    base = {
        "holdings_covered": 1,
        "holdings_total": 1,
        "value_covered_pct": 100.0,
        "macro_verdict": "Macro favorable.",
        "competitive_verdict": "Moats solides.",
        "swot_verdict": "Forces dominantes.",
        "strategic_score": 0.71,
        "confidence": 0.83,
    }
    base.update(overrides)
    return PortfolioStrategicPosture(**base)


def _mixin() -> ReportEnrichmentMixin:
    """A bare mixin with a stubbed logger.

    ``enrichment.py`` declares ``logger: Any`` as a bare annotation (no
    assignment), so a plain ``ReportEnrichmentMixin()`` instance has no
    ``logger`` attribute at runtime — ``self.logger.warning(...)`` inside the
    broad ``except`` would itself raise ``AttributeError``. Stub it directly;
    ``mocker.patch.object`` can't patch an attribute that doesn't exist.
    """
    mixin = ReportEnrichmentMixin()
    mixin.logger = _StubLogger()
    return mixin


class _StubLogger:
    def __init__(self) -> None:
        self.warnings: list[str] = []
        self.infos: list[str] = []
        self.errors: list[str] = []
        self.debugs: list[str] = []

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        # **kwargs absorbs exc_info/stack_info/etc. -- matching real
        # logging.Logger's signature so a call site can pass exc_info=True.
        self.warnings.append(msg % args if args else msg)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.infos.append(msg % args if args else msg)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.errors.append(msg % args if args else msg)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.debugs.append(msg % args if args else msg)


def test_uncovered_holdings_are_named_in_the_posture(mocker):
    """A gap must be named, not averaged away."""
    mixin = _mixin()
    mocker.patch.object(mixin, "_extract_holdings_strategic", return_value={"AAPL": _valid_strategic()})
    mocker.patch(
        "finwiz.analysis.strategic_research.synthesize_portfolio_posture_sync",
        return_value=_valid_posture(holdings_covered=1, holdings_total=3, uncovered_tickers=["MSFT", "TSLA"]),
    )

    holdings = [_holding("AAPL"), _holding("MSFT"), _holding("TSLA")]
    result = mixin._synthesize_portfolio_strategic({}, holdings=holdings)

    assert result["holdings_covered"] == 1
    assert result["holdings_total"] == 3
    assert sorted(result["uncovered_tickers"]) == ["MSFT", "TSLA"]


def test_value_covered_pct_is_value_weighted_not_count_weighted(mocker):
    """1-of-3 by count must not silently read as 33% when that holding is 90% of the value."""
    mixin = _mixin()
    mocker.patch.object(mixin, "_extract_holdings_strategic", return_value={"AAPL": _valid_strategic()})
    captured: dict[str, Any] = {}

    def _fake_synthesize(_holdings_strategic, **kwargs):
        captured.update(kwargs)
        return _valid_posture(**kwargs)

    mocker.patch("finwiz.analysis.strategic_research.synthesize_portfolio_posture_sync", side_effect=_fake_synthesize)

    # AAPL (covered) is 900 of 1000 total EUR value -> 90% covered by value,
    # even though only 1 of 3 holdings (33%) is covered by count.
    holdings = [
        _holding("AAPL", eur_value=900.0),
        _holding("MSFT", eur_value=50.0),
        _holding("TSLA", eur_value=50.0),
    ]
    mixin._synthesize_portfolio_strategic({}, holdings=holdings)

    assert captured["value_covered_pct"] == pytest.approx(90.0)
    assert captured["holdings_covered"] == 1
    assert captured["holdings_total"] == 3


def test_value_covered_pct_falls_back_to_count_proxy_without_fabricating(mocker):
    """No priced holdings anywhere -> honest count-based proxy, not a fabricated 100%."""
    mixin = _mixin()
    mocker.patch.object(mixin, "_extract_holdings_strategic", return_value={"AAPL": _valid_strategic()})
    captured: dict[str, Any] = {}

    def _fake_synthesize(_holdings_strategic, **kwargs):
        captured.update(kwargs)
        return _valid_posture(**kwargs)

    mocker.patch("finwiz.analysis.strategic_research.synthesize_portfolio_posture_sync", side_effect=_fake_synthesize)

    # No eur_value anywhere in the portfolio -> nothing to weight by value.
    holdings = [_holding("AAPL"), _holding("MSFT")]
    mixin._synthesize_portfolio_strategic({}, holdings=holdings)

    # Count-based proxy: 1 of 2 covered = 50%, never a fabricated 100.0.
    assert captured["value_covered_pct"] == pytest.approx(50.0)
    assert any(("value" in w.lower() and "fallback" in w.lower()) or "proxy" in w.lower() for w in mixin.logger.warnings), (
        f"expected a logged warning about the value-coverage fallback, got: {mixin.logger.warnings}"
    )


def test_call_site_threads_portfolio_holdings_into_synthesis(mocker):
    """The break this task fixes was exactly this: the caller not passing what the callee now requires."""
    import datetime as _dt

    from finwiz.schemas.portfolio_review import PortfolioReview

    mixin = _mixin()
    mixin.state = mocker.Mock(session_id="s1", stress_test_results=None, macro_snapshot=None, run_ledger=None, deep_analysis_coverage=None, opportunity_shortlist=None)

    portfolio_review = PortfolioReview(as_of=_dt.datetime.now(), holdings=[_holding("AAPL", eur_value=100.0)])

    mocker.patch.object(mixin, "_read_discovery_results", return_value=None)
    mocker.patch.object(mixin, "_extract_holdings_sentiment", return_value=None)
    mocker.patch.object(mixin, "_collect_economic_calendar", return_value=None)
    mocker.patch.object(mixin, "_extract_holdings_insights", return_value=None)
    mocker.patch.object(mixin, "_load_opportunity_shortlist", return_value=None)
    mocker.patch.object(mixin, "_read_live_cost_summary", return_value=None)
    mocker.patch.object(mixin, "_iter_enriched_records", return_value=iter([]))
    mocker.patch("finwiz.reporting.python_report_generator.generate_python_report", return_value="output/report.html")

    spy = mocker.spy(mixin, "_synthesize_portfolio_strategic")

    mixin._generate_python_report(portfolio_review, deep_analysis_results={})

    assert spy.call_args.kwargs["holdings"] == portfolio_review.holdings


def test_programming_error_propagates_instead_of_being_logged_as_non_fatal(mocker):
    """TypeError/AttributeError are bugs, not runtime failures -- they must not be swallowed."""
    mixin = _mixin()
    mocker.patch.object(mixin, "_extract_holdings_strategic", side_effect=AttributeError("boom"))

    with pytest.raises(AttributeError):
        mixin._synthesize_portfolio_strategic({}, holdings=[_holding("AAPL")])


def test_genuine_runtime_failure_still_returns_none(mocker):
    """API-down / parse-error style failures remain best-effort: log and return None."""
    mixin = _mixin()
    mocker.patch.object(mixin, "_extract_holdings_strategic", return_value={"AAPL": _valid_strategic()})
    mocker.patch(
        "finwiz.analysis.strategic_research.synthesize_portfolio_posture_sync",
        side_effect=RuntimeError("Perplexity is down"),
    )

    result = mixin._synthesize_portfolio_strategic({}, holdings=[_holding("AAPL")])

    assert result is None
    assert mixin.logger.warnings, "a runtime failure should still be logged"


def _wired_mixin(mocker) -> ReportEnrichmentMixin:
    """A mixin with every ``_generate_python_report`` dependency stubbed except
    the posture-page write path, so tests can isolate that wiring."""
    mixin = _mixin()
    mixin.state = mocker.Mock(
        session_id="s1",
        stress_test_results=None,
        macro_snapshot=None,
        run_ledger=None,
        deep_analysis_coverage=None,
        opportunity_shortlist=None,
    )
    mocker.patch.object(mixin, "_read_discovery_results", return_value=None)
    mocker.patch.object(mixin, "_extract_holdings_sentiment", return_value=None)
    mocker.patch.object(mixin, "_collect_economic_calendar", return_value=None)
    mocker.patch.object(mixin, "_extract_holdings_insights", return_value=None)
    mocker.patch.object(mixin, "_load_opportunity_shortlist", return_value=None)
    mocker.patch.object(mixin, "_read_live_cost_summary", return_value=None)
    mocker.patch.object(mixin, "_iter_enriched_records", return_value=iter([]))
    return mixin


def test_posture_page_is_written_beside_the_family_report(mocker, tmp_path):
    """Until the page is written to disk, it's code that nothing calls."""
    import datetime as _dt

    from finwiz.schemas.portfolio_review import PortfolioReview

    mixin = _wired_mixin(mocker)
    report_path = str(tmp_path / "finwiz_family_financial_plan.html")
    mocker.patch.object(mixin, "_extract_holdings_strategic", return_value={"AAPL": _valid_strategic()})
    mocker.patch.object(mixin, "_synthesize_portfolio_strategic", return_value=_valid_posture().model_dump(mode="json"))
    mocker.patch("finwiz.reporting.python_report_generator.generate_python_report", return_value=report_path)

    portfolio_review = PortfolioReview(as_of=_dt.datetime.now(), holdings=[_holding("AAPL", eur_value=100.0)])

    result_path = mixin._generate_python_report(portfolio_review, deep_analysis_results={"AAPL": {}})

    assert result_path == report_path
    posture_path = tmp_path / "finwiz_posture_strategique.html"
    assert posture_path.exists()
    html = posture_path.read_text(encoding="utf-8")
    assert "Posture Stratégique" in html
    assert "AAPL" in html  # holdings_strategic was threaded through


def test_no_posture_skips_the_page_write(mocker, tmp_path):
    """Nothing to write beats writing a page for a posture that doesn't exist."""
    import datetime as _dt

    from finwiz.schemas.portfolio_review import PortfolioReview

    mixin = _wired_mixin(mocker)
    report_path = str(tmp_path / "finwiz_family_financial_plan.html")
    mocker.patch.object(mixin, "_extract_holdings_strategic", return_value=None)
    mocker.patch.object(mixin, "_synthesize_portfolio_strategic", return_value=None)
    mocker.patch("finwiz.reporting.python_report_generator.generate_python_report", return_value=report_path)

    portfolio_review = PortfolioReview(as_of=_dt.datetime.now(), holdings=[_holding("AAPL", eur_value=100.0)])

    result_path = mixin._generate_python_report(portfolio_review, deep_analysis_results={"AAPL": {}})

    assert result_path == report_path
    assert not (tmp_path / "finwiz_posture_strategique.html").exists()


def test_posture_page_write_failure_does_not_break_the_family_report(mocker, tmp_path):
    """A broken companion page must never take down the primary deliverable --
    but the failure must still be visible, not swallowed silently (Task 7)."""
    import datetime as _dt

    from finwiz.schemas.portfolio_review import PortfolioReview

    mixin = _wired_mixin(mocker)
    report_path = str(tmp_path / "finwiz_family_financial_plan.html")
    mocker.patch.object(mixin, "_extract_holdings_strategic", return_value=None)
    mocker.patch.object(mixin, "_synthesize_portfolio_strategic", return_value=_valid_posture().model_dump(mode="json"))
    mocker.patch("finwiz.reporting.python_report_generator.generate_python_report", return_value=report_path)
    mocker.patch(
        "finwiz.reporting.sections.posture_page.generate_posture_page",
        side_effect=RuntimeError("boom"),
    )

    portfolio_review = PortfolioReview(as_of=_dt.datetime.now(), holdings=[_holding("AAPL", eur_value=100.0)])

    result_path = mixin._generate_python_report(portfolio_review, deep_analysis_results={"AAPL": {}})

    assert result_path == report_path
    assert not (tmp_path / "finwiz_posture_strategique.html").exists()
    assert mixin.logger.warnings, "the write failure must be logged, not swallowed silently"
