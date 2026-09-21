"""The crypto branch passes gaps through instead of inventing values.

I4: these tests used to assert on the *source text* of the crypto branch
(`inspect.getsource` + string slicing), which restates the implementation
rather than the behaviour and passes for any expression that avoids the
exact literals checked for — including a reintroduced default. Replaced with
behavioural tests that drive `_extract_holding_data` with a `perf_dict`
missing `market_cap` and assert the value arrives as `None`, never a
fabricated constant. The "still scored" half of spec §6's claim is covered
separately, through `DeepAnalysisScorer.calculate_composite_score`, in
`tests/unit/scoring/test_critical_fields_validation.py`
(`test_missing_crypto_market_cap_is_scored_not_dropped`).
"""

from dataclasses import dataclass

from finwiz.flow_state_models import DeepAnalysisResult
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import HoldingDecision
from finwiz.scoring.portfolio_deep_analyzer import PortfolioDeepAnalyzer


@dataclass
class _StubHolding:
    """Minimal stand-in for HoldingDecision: _extract_holding_data reads only these two fields."""

    ticker: str
    asset_class: str


def _patch_quant_tool(mocker, *, performance: dict, technical: dict | None = None):
    """Patch QuantitativeAnalysisTool._run to return the given performance/technical dicts."""

    def fake_run(self, *, symbol, asset_class, analysis_type):
        if analysis_type == "performance":
            return performance
        return technical or {}

    mocker.patch(
        "finwiz.tools.quantitative_analysis_tool.QuantitativeAnalysisTool._run",
        fake_run,
    )


def test_missing_crypto_market_cap_arrives_as_none_not_fabricated(mocker):
    _patch_quant_tool(
        mocker,
        performance={
            "current_price": 50000.0,
            "volatility": 0.60,
            "max_drawdown": -0.30,
            "beta": 1.0,
            "volume_24h": 1e9,
            "age_years": 5.0,
            # market_cap deliberately absent — CoinGecko-only field
        },
    )

    analyzer = PortfolioDeepAnalyzer()
    data = analyzer._extract_holding_data(_StubHolding(ticker="BTC-USD", asset_class="crypto"))

    assert data is not None
    assert data["market_cap"] is None
    # Real fields still pass through untouched
    assert data["volume_24h"] == 1e9
    assert data["age_years"] == 5.0


def test_crypto_branch_never_reintroduces_a_fabricated_default(mocker):
    """No source-fed value the branch itself could substitute — market_cap,
    volume_24h and age_years must all come from perf_dict.get(...), which
    returns None on absence, not from perf_dict.get(field, <constant>).
    """
    _patch_quant_tool(
        mocker,
        performance={
            "current_price": 50000.0,
            "volatility": 0.60,
            "max_drawdown": -0.30,
            "beta": 1.0,
            # every crypto-specific field absent
        },
    )

    analyzer = PortfolioDeepAnalyzer()
    data = analyzer._extract_holding_data(_StubHolding(ticker="ZZZ-USD", asset_class="crypto"))

    assert data is not None
    for field in ("market_cap", "volume_24h", "age_years"):
        assert data[field] is None, f"{field} was fabricated instead of staying None: {data[field]!r}"


def test_resolved_crypto_fields_pass_through_unchanged(mocker):
    """The happy path: real values from perf_dict reach the scorer input untouched."""
    _patch_quant_tool(
        mocker,
        performance={
            "current_price": 81114.0,
            "volatility": 0.55,
            "max_drawdown": -0.25,
            "beta": 1.2,
            "market_cap": 1_629_408_510_367.0,
            "volume_24h": 23_900_006_504.0,
            "age_years": 17.0,
        },
    )

    analyzer = PortfolioDeepAnalyzer()
    data = analyzer._extract_holding_data(_StubHolding(ticker="BTC-USD", asset_class="crypto"))

    assert data is not None
    assert data["market_cap"] == 1_629_408_510_367.0
    assert data["volume_24h"] == 23_900_006_504.0
    assert data["age_years"] == 17.0


def _holding() -> HoldingDecision:
    return HoldingDecision(
        asset_class="crypto",
        name="Bitcoin",
        ticker="BTC-USD",
        currency="USD",
        decision="KEEP",
        composite_score=0.5,
        grade="C",
        grade_description="Placeholder",
        recommended_action="Analyse en attente",
        risk=RiskAssessmentStandardized(score=3.0, level="Medium"),
    )


def test_rationale_bullet_is_unavailable_when_fundamental_score_is_none():
    """LIVE-3 (post-PR review, findings.md): the crypto branch of
    _extract_holding_data never sets circulating_supply/max_supply, so the
    supply component is always excluded on this path -- when perf_dict also
    lacks market_cap/volume_24h/age_years, fundamental_score is None. The
    rationale bullet used to format it with `:.3f`, raising TypeError.
    """
    analyzer = PortfolioDeepAnalyzer()
    holding = _holding()
    result = DeepAnalysisResult(
        ticker="BTC-USD",
        asset_class="crypto",
        crew_name="PythonDeepAnalyzer",
        composite_score=0.5,
        grade="C",
        recommendation="HOLD",
        rationale="No fundamental component survived",
        risk_details={},
        fundamental_score=None,
        technical_score=0.5,
        risk_score=0.5,
        data_freshness_hours=1.0,
        confidence_level=0.5,
    )

    analyzer._update_holding_with_analysis(holding, result)

    assert "📊 Fundamental: unavailable" in holding.rationale_bullets
    assert not any("None" in bullet for bullet in holding.rationale_bullets)


def test_rationale_bullet_is_unavailable_when_technical_score_is_none():
    """Sibling of the fundamental-score fix, found on re-review: technical_score
    is float | None on DeepAnalysisResult (flow_state_models.py) too, and was
    formatted with `:.3f` unguarded.
    """
    analyzer = PortfolioDeepAnalyzer()
    holding = _holding()
    result = DeepAnalysisResult(
        ticker="BTC-USD",
        asset_class="crypto",
        crew_name="PythonDeepAnalyzer",
        composite_score=0.5,
        grade="C",
        recommendation="HOLD",
        rationale="No technical component survived",
        risk_details={},
        fundamental_score=0.5,
        technical_score=None,
        risk_score=0.5,
        data_freshness_hours=1.0,
        confidence_level=0.5,
    )

    analyzer._update_holding_with_analysis(holding, result)

    assert "📈 Technical: unavailable" in holding.rationale_bullets
    assert not any("None" in bullet for bullet in holding.rationale_bullets)


def test_rationale_bullet_is_unavailable_when_risk_score_is_none():
    """Sibling of the fundamental-score fix, found on re-review: risk_score is
    float | None on DeepAnalysisResult too. Unlike fundamental_score, it also
    feeds holding.risk.score -- a required, non-Optional float with no
    "unavailable" representation -- so that update must be skipped (not
    fabricated) rather than just the bullet text guarded.
    """
    analyzer = PortfolioDeepAnalyzer()
    holding = _holding()
    result = DeepAnalysisResult(
        ticker="BTC-USD",
        asset_class="crypto",
        crew_name="PythonDeepAnalyzer",
        composite_score=0.5,
        grade="C",
        recommendation="HOLD",
        rationale="No risk component survived",
        risk_details={},
        fundamental_score=0.5,
        technical_score=0.5,
        risk_score=None,
        data_freshness_hours=1.0,
        confidence_level=0.5,
    )

    analyzer._update_holding_with_analysis(holding, result)

    assert "⚠️ Risk: unavailable" in holding.rationale_bullets
    assert not any("None" in bullet for bullet in holding.rationale_bullets)
    # holding.risk.score is a required float with no None representation --
    # the pre-existing value must survive untouched rather than be fabricated.
    assert holding.risk.score == 3.0
    assert holding.risk.level == "Medium"
