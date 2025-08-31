"""Test data fixtures for reporter input validation tests."""

from typing import Any


def get_complete_input() -> dict[str, Any]:
    """Return complete valid input data for reporter tests."""
    return {
        "schema_version": 1,
        "ten_k_insights": [
            {
                "schema_version": 1,
                "ticker": "AAPL",
                "filing_url": "https://sec.gov/filing/123",
                "filed_at": "2024-01-01T00:00:00Z",
                "section": "Item 1A",
                "excerpt": "This is a sample excerpt from the 10-K filing that meets minimum length requirements.",
                "sec_citation": "10-K (2024), Item 1A, p. 17",
            }
        ],
        "stock_sentiments": [
            {
                "schema_version": 1,
                "ticker": "AAPL",
                "mean_score": 0.5,
                "counts": {"pos": 10, "neu": 5, "neg": 2},
                "top_pos": [],
                "top_neg": [],
            }
        ],
        "stock_risks": [
            {
                "scale": "0_5",
                "score": 2.5,
                "level": "Medium",
                "risk_factors": ["Market volatility", "Regulatory risk"],
            }
        ],
        "etf_factsheets": [
            {
                "schema_version": 1,
                "ticker": "SPY",
                "issuer": "State Street",
                "expense_ratio": 0.09,
                "tracking_diff": 0.02,
                "replication_method": "physical",
                "factsheet_url": "https://example.com/spy-factsheet",
                "as_of": "2025-01-01",
                "factsheet_highlights": ["Low cost", "High liquidity"],
                "top_holdings": [],
            }
        ],
        "etf_holdings": [
            {
                "ticker": "AAPL",
                "weight_pct": 7.5,
                "source_url": "https://example.com/holdings",
                "as_of": "2025-01-01",
            }
        ],
        "etf_risks": [{"scale": "0_5", "score": 1.5, "level": "Low", "risk_factors": ["Market risk"]}],
        "crypto_theses": [
            {
                "schema_version": 1,
                "symbol": "BTC",
                "thesis_bullets": [
                    "Digital gold narrative strengthening",
                    "Institutional adoption increasing",
                ],
                "references": ["https://example.com/btc-analysis"],
            }
        ],
        "crypto_risks": [
            {
                "scale": "0_5",
                "score": 4.5,
                "level": "High",
                "risk_factors": ["Volatility", "Regulatory uncertainty"],
            }
        ],
        "as_of": "2025-01-01",
    }


def get_minimal_input() -> dict[str, Any]:
    """Return minimal valid input data for reporter tests."""
    return {
        "schema_version": 1,
        "ten_k_insights": [],
        "stock_sentiments": [],
        "stock_risks": [],
        "etf_factsheets": [],
        "etf_holdings": [],
        "etf_risks": [],
        "crypto_theses": [],
        "crypto_risks": [],
        "as_of": "2025-01-01",
    }


def get_invalid_input_missing_required() -> dict[str, Any]:
    """Return input data missing required fields."""
    return {
        "schema_version": 1,
        # Missing required fields like ten_k_insights, etc.
        "as_of": "2025-01-01",
    }
