from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from finwiz.schemas import MarketSentiment, TenKInsight


def test_tenk_insight_valid() -> None:
    item = TenKInsight(
        ticker="AAPL",
        filing_url="https://www.sec.gov/Archives/edgar/data/0000320193/000032019324000066/aapl-20230930.htm",
        filed_at=datetime(2024, 1, 31, 12, 0, tzinfo=UTC),
        section="Item 1A",
        excerpt="Risk factors include supply chain disruptions and currency fluctuations impacting margins.",
        sec_citation="10-K (2024), Item 1A",
    )
    data = item.model_dump()
    assert data["ticker"] == "AAPL"


def test_market_sentiment_valid() -> None:
    ms = MarketSentiment(
        ticker="AAPL",
        mean_score=0.25,
        counts={"pos": 10, "neu": 5, "neg": 3},
        top_pos=[],
        top_neg=[],
    )
    assert -1.0 <= ms.mean_score <= 1.0


def test_market_sentiment_extra_forbidden() -> None:
    payload = {
        "ticker": "AAPL",
        "mean_score": 0.1,
        "counts": {"pos": 1, "neu": 1, "neg": 1},
        "top_pos": [],
        "top_neg": [],
        "unexpected": 1,
    }
    with pytest.raises(ValidationError):
        MarketSentiment.model_validate(payload)