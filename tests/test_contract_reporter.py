from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from finwiz.schemas import (
    MarketSentiment,
    ReporterInput,
    RiskAssessmentStandardized,
    TenKInsight,
)


def _sample_tenk() -> TenKInsight:
    return TenKInsight(
        ticker="MSFT",
        filing_url="https://www.sec.gov/Archives/edgar/data/0000789019/000156459024000000/msft-20240630x10k.htm",
        filed_at=datetime(2024, 7, 31, 9, 0, tzinfo=timezone.utc),
        section="Item 7",
        excerpt="Management discusses revenue growth driven by cloud adoption and AI services.",
        sec_citation="10-K (2024), Item 7",
    )


def _sample_sentiment() -> MarketSentiment:
    return MarketSentiment(
        ticker="MSFT",
        mean_score=0.4,
        counts={"pos": 7, "neu": 3, "neg": 2},
        top_pos=[],
        top_neg=[],
    )


def test_reporter_input_minimal_valid() -> None:
    rpt = ReporterInput(
        ten_k_insights=[_sample_tenk()],
        stock_sentiments=[_sample_sentiment()],
        stock_risks=[RiskAssessmentStandardized(score=3.2, level="Medium")],
        etf_factsheets=[],
        etf_holdings=[],
        etf_risks=[],
        crypto_theses=[],
        crypto_risks=[],
        as_of=date.today(),
    )
    assert rpt.as_of <= date.today()


def test_reporter_input_extra_forbidden() -> None:
    payload = {
        "ten_k_insights": [],
        "stock_sentiments": [],
        "stock_risks": [],
        "etf_factsheets": [],
        "etf_holdings": [],
        "etf_risks": [],
        "crypto_theses": [],
        "crypto_risks": [],
        "as_of": date.today().isoformat(),
        "unexpected": True,
    }
    with pytest.raises(ValidationError):
        ReporterInput.model_validate(payload)
