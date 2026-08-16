"""ETF discovery analyzer must never fabricate opportunities.

`analyze_etf_opportunities` routes through `NewcomerDiscoveryPipeline`. On
pipeline failure it must return an empty, honestly-labelled result — never
the old hardcoded VTI/VXUS/BND fallback opportunities.
"""

import inspect

from finwiz.scoring import etf_analyzer
from finwiz.scoring.etf_analyzer import analyze_etf_opportunities


def test_pipeline_failure_yields_no_opportunities(mocker):
    mocker.patch(
        "finwiz.scoring.discovery.pipeline.NewcomerDiscoveryPipeline",
        side_effect=RuntimeError("universe fetch exploded"),
    )

    result = analyze_etf_opportunities("test-session")

    assert result["opportunities"] == []
    assert result["performance_metrics"]["opportunities_found"] == 0
    assert result["performance_metrics"]["method"] == "newcomer_discovery_failed"
    assert "error" in result["performance_metrics"]


def test_pipeline_success_is_labelled_distinctly_from_failure(mocker):
    """A run that legitimately finds nothing must not look like a failure."""
    mock_pipeline_cls = mocker.patch("finwiz.scoring.discovery.pipeline.NewcomerDiscoveryPipeline")
    mock_pipeline = mock_pipeline_cls.return_value
    mock_pipeline.discover.return_value = mocker.Mock()
    mock_pipeline._to_legacy_format.return_value = {
        "opportunities": [],
        "analysis_summary": "Discovered 0 etf newcomer candidates",
        "performance_metrics": {
            "execution_time_seconds": 0.01,
            "opportunities_found": 0,
            "cost_usd": 0.0,
            "llm_calls_made": 0,
            "method": "newcomer_discovery_pipeline",
        },
    }

    result = analyze_etf_opportunities("test-session")

    assert result["opportunities"] == []
    assert result["performance_metrics"]["method"] == "newcomer_discovery_pipeline"
    assert "error" not in result["performance_metrics"]


def test_no_hardcoded_tickers_remain_in_module():
    source = inspect.getsource(etf_analyzer)
    for invented in ("VTI", "VXUS", "BND"):
        assert invented not in source
