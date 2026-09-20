"""Field descriptions are prompt text: they travel inside the json_schema response_format.

Every field the research or crew model fills must carry a French, specific
description. English filler ("Comprehensive", "Key", "List of") is the
signature of the generic descriptions this replaced.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from finwiz.analysis.fact_pack_research import _FactPackRaw
from finwiz.analysis.stages.qualify import _QualitativeInsightsRaw
from finwiz.schemas.hybrid_analysis.qualitative import (
    ActionPlan,
    ContextualRiskInsights,
    FundamentalContextInsights,
    InvestmentSynthesis,
    ScenarioProbabilities,
    SecAnalysisInsights,
    TechnicalStrategyInsights,
)
from finwiz.schemas.hybrid_analysis.strategic import (
    FiveForcesAnalysis,
    ForceRating,
    PortfolioPostureNarrative,
    SwotAnalysis,
)
from finwiz.schemas.perplexity import NewsDigest, NewsHeadline

_ENGLISH_FILLER = ("Comprehensive", "Key ", "List of", "AI's ", "Identified")

MODEL_FILLED: list[type[BaseModel]] = [
    SecAnalysisInsights,
    FundamentalContextInsights,
    TechnicalStrategyInsights,
    ContextualRiskInsights,
    ScenarioProbabilities,
    ActionPlan,
    InvestmentSynthesis,
    _QualitativeInsightsRaw,
    SwotAnalysis,
    ForceRating,
    FiveForcesAnalysis,
    PortfolioPostureNarrative,
    _FactPackRaw,
    NewsHeadline,
    NewsDigest,
]


@pytest.mark.parametrize("model", MODEL_FILLED, ids=lambda m: m.__name__)
def test_every_field_has_a_french_description(model: type[BaseModel]) -> None:
    for name, field in model.model_fields.items():
        description = field.description or ""
        assert len(description) >= 25, f"{model.__name__}.{name}: description missing or too short"
        for filler in _ENGLISH_FILLER:
            assert filler not in description, f"{model.__name__}.{name}: English filler {filler!r} in description"
