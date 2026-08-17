"""Tests for the EUR allocation hero + holdings allocation columns (modern-fintech redesign).

Covers the newly surfaced per-holding ``weight`` / ``eur_value`` data and the
portfolio ``total_value_eur`` hero, including the graceful "no Quantity" path.
"""

from __future__ import annotations

from datetime import datetime

from finwiz.reporting.sections.holdings import generate_holdings_analysis
from finwiz.reporting.sections.portfolio_summary import (
    _fmt_eur,
    generate_allocation_section,
)
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import HoldingDecision, PortfolioReview


def _make_risk() -> RiskAssessmentStandardized:
    return RiskAssessmentStandardized(score=2.5, level="Medium")


def _make_holding(
    ticker: str = "TEST",
    name: str = "Test Company",
    asset_class: str = "stock",
    grade: str = "B",
    composite_score: float = 0.7,
    weight: float | None = None,
    eur_value: float | None = None,
    native_currency: str | None = None,
) -> HoldingDecision:
    return HoldingDecision(
        ticker=ticker,
        name=name,
        asset_class=asset_class,
        currency="USD",
        decision="KEEP",
        composite_score=composite_score,
        grade=grade,
        grade_description=f"Grade {grade} holding",
        recommended_action="HOLD",
        risk=_make_risk(),
        rationale_bullets=["Solid fundamentals"],
        weight=weight,
        eur_value=eur_value,
        native_currency=native_currency,
    )


def _weighted_review() -> PortfolioReview:
    holdings = [
        _make_holding("AAPL", "Apple Inc.", "stock", "A", 0.82, weight=0.3742, eur_value=20120.0, native_currency="USD"),
        _make_holding("MSFT", "Microsoft Corp.", "stock", "A", 0.80, weight=0.25, eur_value=13443.0, native_currency="USD"),
        _make_holding("VWCE", "Vanguard FTSE All-World", "etf", "B", 0.70, weight=0.20, eur_value=10754.4, native_currency="EUR"),
        _make_holding("SAP", "SAP SE", "stock", "B", 0.68, weight=0.10, eur_value=5377.2, native_currency="EUR"),
        _make_holding("BTC-USD", "Bitcoin", "crypto", "C", 0.55, weight=0.0758, eur_value=4077.4, native_currency="USD"),
    ]
    return PortfolioReview(as_of=datetime.now(), holdings=holdings, total_value_eur=53772.0)


def _bare_review() -> PortfolioReview:
    holdings = [
        _make_holding("AAPL", "Apple Inc.", "stock", "A", 0.82),
        _make_holding("MSFT", "Microsoft Corp.", "stock", "A", 0.80),
    ]
    return PortfolioReview(as_of=datetime.now(), holdings=holdings, total_value_eur=None)


class TestFmtEur:
    def test_formats_with_space_thousands_and_euro(self) -> None:
        out = _fmt_eur(53772.0)
        assert "53 772 €" == out

    def test_smaller_value(self) -> None:
        assert _fmt_eur(4077.4) == "4 077 €"

    def test_none_returns_dash(self) -> None:
        assert _fmt_eur(None) == "—"


class TestGenerateAllocationSection:
    def test_renders_hero_total(self) -> None:
        html = generate_allocation_section(_weighted_review())
        assert "value-hero" in html
        assert "Valeur totale du portefeuille" in html
        # The formatted total must appear (digits + euro sign).
        assert "53 772 €" in html
        # Meta line: number of positions + asset classes.
        assert "5 positions" in html

    def test_weight_bars_present_and_top_holding_widest(self) -> None:
        html = generate_allocation_section(_weighted_review())
        assert "weight-bar" in html
        assert "weight-bar-fill" in html
        # Top holding is AAPL at 0.3742 -> 37.4% fill width.
        assert "width: 37.4%" in html
        # eur values present
        assert "20 120 €" in html

    def test_holdings_sorted_by_weight_desc(self) -> None:
        html = generate_allocation_section(_weighted_review())
        # AAPL (37.4%) must appear before MSFT (25%) which appears before BTC (7.6%).
        assert html.index("AAPL") < html.index("MSFT") < html.index("BTC-USD")

    def test_graceful_when_no_total_or_weights(self) -> None:
        html = generate_allocation_section(_bare_review())
        # French info note mentioning the Quantity column.
        assert "Quantity" in html
        # No "None" or "0 €" leak.
        assert "None" not in html
        assert "0 €" not in html
        # Hero shell still rendered.
        assert "value-hero" in html

    def test_no_none_leak_in_weighted_path(self) -> None:
        html = generate_allocation_section(_weighted_review())
        assert "None" not in html


class TestHoldingsAllocationColumns:
    def test_weighted_holdings_show_poids_and_valeur(self) -> None:
        html = generate_holdings_analysis(_weighted_review().holdings)
        assert "Poids" in html
        assert "Valeur (€)" in html
        # Weight bar in the table + eur value.
        assert "weight-bar" in html
        assert "20 120 €" in html

    def test_none_allocation_renders_dash(self) -> None:
        holding = _make_holding("ZZZ", "No Alloc Co", grade="B", weight=None, eur_value=None)
        html = generate_holdings_analysis([holding])
        assert "—" in html
        assert "None" not in html

    def test_thead_and_tbody_column_counts_match(self) -> None:
        review = _weighted_review()
        html = generate_holdings_analysis(review.holdings)
        # Count <th> in the (single) header row.
        thead = html.split("<thead>")[1].split("</thead>")[0]
        n_th = thead.count("<th>")
        # First data row in tbody.
        tbody = html.split("<tbody>")[1].split("</tbody>")[0]
        first_row = tbody.split("</tr>")[0]
        n_td = first_row.count("<td")
        assert n_th == n_td, f"header cols {n_th} != row cols {n_td}"

    def test_pending_row_column_count_matches_header(self) -> None:
        pending = _make_holding("PEND", "Pending Co", grade="N/A", composite_score=0.0)
        html = generate_holdings_analysis([pending])
        thead = html.split("<thead>")[1].split("</thead>")[0]
        n_th = thead.count("<th>")
        tbody = html.split("<tbody>")[1].split("</tbody>")[0]
        first_row = tbody.split("</tr>")[0]
        n_td = first_row.count("<td")
        assert n_th == n_td, f"header cols {n_th} != pending row cols {n_td}"


class TestTotalAndCountDescribeTheSameSet:
    """The position count must describe the money shown beside it.

    ``total_value_eur`` is priced holdings only (the schema says so), but the
    hero captioned it with ``len(holdings)`` — every holding, priced or not. A
    2026-08-17 run rendered 30 positions summing to 34 046 EUR under the label
    "64 positions": the total understated the portfolio by roughly half, and
    every weight was inflated by the missing denominator (ASML shown at 23.3 %).
    Nothing on the page said so.
    """

    def test_the_count_matches_the_priced_holdings_the_total_is_built_from(self) -> None:
        review = PortfolioReview(
            as_of=datetime(2026, 8, 17),
            total_value_eur=3000.0,
            holdings=[
                _make_holding(ticker="AAA", weight=0.6, eur_value=1800.0),
                _make_holding(ticker="BBB", weight=0.4, eur_value=1200.0),
                _make_holding(ticker="NESN.SW"),
                _make_holding(ticker="UBSG.SW"),
            ],
        )

        html = generate_allocation_section(review)

        assert "2 positions" in html
        assert "4 positions" not in html

    def test_unpriced_holdings_are_disclosed_not_silently_dropped(self) -> None:
        review = PortfolioReview(
            as_of=datetime(2026, 8, 17),
            total_value_eur=3000.0,
            holdings=[
                _make_holding(ticker="AAA", weight=1.0, eur_value=3000.0),
                _make_holding(ticker="NESN.SW"),
                _make_holding(ticker="UBSG.SW"),
            ],
        )

        html = generate_allocation_section(review)

        assert "2" in html
        assert "non valoris" in html.lower(), "unpriced holdings vanish with no disclosure"

    def test_a_fully_priced_portfolio_says_nothing_extra(self) -> None:
        """The disclosure must appear only when something is actually missing."""
        review = PortfolioReview(
            as_of=datetime(2026, 8, 17),
            total_value_eur=3000.0,
            holdings=[
                _make_holding(ticker="AAA", weight=0.6, eur_value=1800.0),
                _make_holding(ticker="BBB", weight=0.4, eur_value=1200.0),
            ],
        )

        html = generate_allocation_section(review)

        assert "2 positions" in html
        assert "non valoris" not in html.lower()
