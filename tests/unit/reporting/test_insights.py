"""Tests for the consolidated-report quintessence cards and LLM cost summary.

Deterministic Python rendering only — no coverage on the LLM that produced the
distilled data. Covers escaping, fail-soft omission, and sub-block rendering.
"""

from __future__ import annotations

from dataclasses import dataclass

from finwiz.reporting.sections.insights import (
    _fact_pack_block,
    generate_cost_summary_section,
    generate_holdings_insight_cards,
)


@dataclass
class _Holding:
    ticker: str
    grade: str


def _full_insight() -> dict:
    return {
        "thesis": "Durable compounder with widening moat.",
        "bull_case": "AI demand re-rates multiple.",
        "bear_case": "Regulation compresses margins.",
        "scenario_probabilities": {"bull": 0.3, "base": 0.5, "bear": 0.2},
        "final_recommendation": "BUY",
        "recommendation_confidence": "HIGH",
        "immediate_actions": ["Initiate 2% position", "Set stop at -15%"],
        "moat": "Switching costs across the install base.",
        "top_sec_risk": "Customer concentration in top 3 accounts.",
        "growth_drivers": ["Cloud migration", "New silicon cycle"],
        "competitive_positioning": "Clear category leader.",
        "key_risks": ["Antitrust scrutiny", "Pricing pressure"],
        "price_target_rationale": "Accumulate below $150; trim above $220.",
        "fact_pack": {
            "rows": [
                ["Structure", "Single operating entity, no recent divestitures."],
                ["Direction", "CEO Jane Doe since 2019."],
            ],
            "freshness": "fresh",
            "source_citations": ["https://example.com/a", "javascript:alert(1)"],
        },
        "report_link": "stock/AAPL_report.html",
    }


def test_cards_render_core_quintessence() -> None:
    html = generate_holdings_insight_cards({"AAPL": _full_insight()}, [_Holding("AAPL", "A")])
    assert "Durable compounder" in html
    assert "AI demand re-rates" in html  # bull
    assert "Regulation compresses" in html  # bear
    assert "Switching costs" in html  # moat
    assert "Customer concentration" in html  # SEC risk
    assert "Antitrust scrutiny" in html  # key risks
    assert "Single operating entity" in html  # fact-pack fact
    assert "Initiate 2% position" in html  # action item
    assert "stock/AAPL_report.html" in html  # full deep-dive link
    assert "<details" in html and "<summary>" in html


def test_cards_render_scenario_probability_bar() -> None:
    html = generate_holdings_insight_cards({"AAPL": _full_insight()}, [_Holding("AAPL", "A")])
    # Bar widths normalized from probabilities; labels expose the percentages.
    assert "Haussier 30%" in html
    assert "Neutre 50%" in html
    assert "Baissier 20%" in html


def test_cards_only_safe_citations_rendered() -> None:
    html = generate_holdings_insight_cards({"AAPL": _full_insight()}, [_Holding("AAPL", "A")])
    assert "https://example.com/a" in html
    assert "javascript:alert(1)" not in html


def test_cards_escape_injection() -> None:
    malicious = {
        "thesis": "<script>alert('xss')</script>",
        "final_recommendation": "BUY",
        "moat": "<img src=x onerror=alert(1)>",
    }
    html = generate_holdings_insight_cards({"<b>EVIL</b>": malicious}, [])
    assert "<script>alert('xss')</script>" not in html
    assert "&lt;script&gt;" in html
    assert "<img src=x" not in html
    assert "<b>EVIL</b>" not in html  # ticker escaped


def test_cards_empty_returns_empty_string() -> None:
    assert generate_holdings_insight_cards(None, []) == ""
    assert generate_holdings_insight_cards({}, []) == ""


def test_cards_omit_absent_subblocks() -> None:
    minimal = {"thesis": "Only a thesis here.", "final_recommendation": "HOLD"}
    html = generate_holdings_insight_cards({"XYZ": minimal}, [_Holding("XYZ", "B")])
    assert "Only a thesis here." in html
    assert "Faits vérifiés" not in html  # no fact pack
    assert "Scénario haussier" not in html  # no bull case
    assert "Actions immédiates" not in html  # no actions


def test_cards_grade_from_holdings_takes_precedence() -> None:
    insight = {"thesis": "t", "final_recommendation": "BUY", "grade": "C"}
    html = generate_holdings_insight_cards({"AAPL": insight}, [_Holding("AAPL", "A+")])
    assert "grade-a-plus" in html  # holding grade wins over insight grade


class TestFactPackBlockValueContract:
    """render.py's to_rows() returns list[str] for a genuinely list-shaped
    value (holdings, recent events, allocation buckets) and str for prose.
    _fact_pack_block must dispatch on the real type rather than sniffing
    for "\\n" in the value -- the old heuristic mis-rendered a single event
    (no newline, so it read as prose with a stray "- " marker) and
    mis-rendered a business_summary that happened to contain a raw newline
    (yfinance's longBusinessSummary is unedited scraped text) as a <ul>.
    """

    def test_a_list_value_renders_as_a_bulleted_list(self) -> None:
        html = _fact_pack_block({"rows": [["Principales lignes", ["MSFT (Microsoft) 7,00 %", "NVDA (NVIDIA) 6,00 %"]]]})
        assert "<ul>" in html
        assert "<li>MSFT (Microsoft) 7,00 %</li>" in html
        assert "<li>NVDA (NVIDIA) 6,00 %</li>" in html

    def test_a_single_event_renders_without_a_stray_leading_dash(self) -> None:
        html = _fact_pack_block({"rows": [["Événements récents (presse)", ["Airbus wins order"]]]})
        assert "<li>Airbus wins order</li>" in html
        assert "- Airbus wins order" not in html

    def test_a_business_summary_with_an_embedded_newline_renders_as_prose(self) -> None:
        summary = "Designs phones.\nAlso sells services."
        html = _fact_pack_block({"rows": [["Structure", summary]]})
        assert "<ul>" not in html
        assert "<p>" in html
        assert "Designs phones." in html

    def test_an_old_shape_string_value_still_renders_without_crashing(self) -> None:
        """A `*_enriched.json` written before this contract still carries
        the old newline-joined-with-dash-markers string for a list-shaped
        field. It now renders as one prose paragraph rather than a <ul> --
        not the ideal rendering for old data, but the block still renders
        (nothing lost, nothing crashes) with no migration required.
        """
        html = _fact_pack_block({"rows": [["Principales lignes", "- MSFT (Microsoft) 7,00 %\n- NVDA (NVIDIA) 6,00 %"]]})
        assert "Principales lignes" in html
        assert "MSFT" in html


def test_cost_summary_renders_real_figures() -> None:
    summary = {
        "total_cost": 1.2345,
        "call_count": 42,
        "per_crew": {
            "deep_analysis": {"cost": 1.0, "calls": 30, "tokens": {"prompt": 1000, "completion": 500}},
            "stock_crew": {"cost": 0.2345, "calls": 12, "tokens": {"prompt": 200, "completion": 100}},
        },
    }
    html = generate_cost_summary_section(summary)
    assert "$1.23" in html
    assert "42" in html
    assert "deep_analysis" in html
    assert "1,500" in html  # token total formatted


def test_cost_summary_derives_call_count_when_zero() -> None:
    summary = {
        "total_cost": 0.5,
        "call_count": 0,  # buggy monitor; derive from per-crew
        "per_crew": {"deep_analysis": {"cost": 0.5, "calls": 7, "tokens": {"prompt": 1, "completion": 1}}},
    }
    html = generate_cost_summary_section(summary)
    assert "7" in html


def test_cost_summary_degrades_to_empty() -> None:
    assert generate_cost_summary_section(None) == ""
    assert generate_cost_summary_section({}) == ""
    assert generate_cost_summary_section({"total_cost": 0.0, "call_count": 0, "per_crew": {}}) == ""
