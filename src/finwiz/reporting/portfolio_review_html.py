"""
Portfolio review HTML generation.

This module handles all HTML presentation concerns for portfolio review:
- HTML table generation for holdings and trades
- Section builders for HTML reports

Separated from business logic for maintainability.
"""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from finwiz.scoring.grading_system import (
    get_grade_css_styles,
    get_portfolio_grade_summary,
    score_to_grade,
)

# =============================================================================
# HTML Table Generators
# =============================================================================


def generate_holdings_table(holdings: list[dict[str, Any]]) -> str:
    """Generate HTML table for holdings with letter grades."""
    if not holdings:
        soup = BeautifulSoup("", "html.parser")
        p = soup.new_tag("p")
        p.string = "No holdings found."
        soup.append(p)
        return soup.prettify(formatter="html")

    # Calculate portfolio grade summary
    scores = [holding.get("composite_score", 0) for holding in holdings]
    grade_summary = get_portfolio_grade_summary(scores)

    soup = BeautifulSoup("", "html.parser")

    # Add CSS styles
    style = soup.new_tag("style")
    style.string = get_grade_css_styles()
    soup.append(style)

    # Generate grade summary
    grade_div = soup.new_tag("div", attrs={"class": "grade-summary"})

    title = soup.new_tag("h4")
    title.string = "📊 Bulletin du Portefeuille"
    grade_div.append(title)

    avg_p = soup.new_tag("p")
    avg_strong = soup.new_tag("strong")
    avg_strong.string = "Moyenne générale :"
    avg_p.append(avg_strong)
    avg_p.append(f" {grade_summary['grade_info'].emoji} ")

    grade_strong = soup.new_tag("strong")
    grade_strong.string = grade_summary["average_grade"]
    avg_p.append(grade_strong)
    avg_p.append(f" ({grade_summary['average_percentage']:.0f}%)")
    grade_div.append(avg_p)

    # Distribution
    dist_p = soup.new_tag("p")
    dist_strong = soup.new_tag("strong")
    dist_strong.string = "Répartition des notes :"
    dist_p.append(dist_strong)
    grade_div.append(dist_p)

    grade_ul = soup.new_tag("ul")
    for grade, data in grade_summary["distribution"].items():
        grade_info = score_to_grade(0.5)
        for test_score in [0.98, 0.90, 0.82, 0.77, 0.72, 0.67, 0.55, 0.25]:
            test_grade_info = score_to_grade(test_score)
            if test_grade_info.grade == grade:
                grade_info = test_grade_info
                break

        li = soup.new_tag("li")
        li.append(f"{grade_info.emoji} ")
        strong = soup.new_tag("strong")
        strong.string = grade
        li.append(strong)
        li.append(f": {data['count']} positions ({data['percentage']:.0f}%)")
        grade_ul.append(li)

    grade_div.append(grade_ul)
    soup.append(grade_div)

    # Analysis depth summary
    deep_count = sum(1 for h in holdings if h.get("crew_analysis_used"))
    shallow_count = len(holdings) - deep_count

    if deep_count > 0:
        analysis_summary = soup.new_tag("div", attrs={"class": "analysis-summary"})
        summary_title = soup.new_tag("h4")
        summary_title.string = "📊 Profondeur d'Analyse"
        analysis_summary.append(summary_title)

        summary_p = soup.new_tag("p")
        summary_p.append(f"🔍 Analyse Approfondie: {deep_count} positions | ")
        summary_p.append(f"⚡ Validation Rapide: {shallow_count} positions")
        analysis_summary.append(summary_p)

        soup.append(analysis_summary)

    # Holdings table
    table = soup.new_tag("table", attrs={"class": "holdings-table"})

    # Header
    thead = soup.new_tag("thead")
    header_row = soup.new_tag("tr")
    headers = ["Ticker", "Nom", "Type", "Analyse", "Décision", "Note", "Scores", "Risque", "Alternatives A+"]
    for header_text in headers:
        th = soup.new_tag("th")
        th.string = header_text
        header_row.append(th)
    thead.append(header_row)
    table.append(thead)

    # Body
    tbody = soup.new_tag("tbody")
    for holding in holdings:
        decision_class = "keep" if holding.get("decision") == "KEEP" else "sell"
        risk_score = holding.get("risk", {}).get("score", 0)
        composite_score = holding.get("composite_score", 0)
        grade_info = score_to_grade(composite_score)

        crew_analysis_used = holding.get("crew_analysis_used")
        is_deep_analysis = crew_analysis_used is not None

        tr = soup.new_tag("tr")

        # Ticker
        td = soup.new_tag("td")
        td.string = holding.get("ticker", "N/A")
        tr.append(td)

        # Name
        td = soup.new_tag("td")
        td.string = holding.get("name", "N/A")
        tr.append(td)

        # Asset class
        td = soup.new_tag("td")
        td.string = holding.get("asset_class", "N/A").upper()
        tr.append(td)

        # Analysis type
        td = soup.new_tag("td")
        if is_deep_analysis:
            span = soup.new_tag("span", attrs={"class": "analysis-deep"})
            span.string = "🔍 Deep"
            td.append(span)
            if crew_analysis_used:
                small = soup.new_tag("small")
                small.string = f" ({crew_analysis_used})"
                td.append(small)
        else:
            span = soup.new_tag("span", attrs={"class": "analysis-quick"})
            span.string = "⚡ Quick"
            td.append(span)
        tr.append(td)

        # Decision
        td = soup.new_tag("td", attrs={"class": decision_class})
        td.string = holding.get("decision", "N/A")
        tr.append(td)

        # Grade
        td = soup.new_tag("td")
        span = soup.new_tag("span", attrs={"class": f"grade-badge {grade_info.css_class}"})
        span.string = f"{grade_info.emoji} {grade_info.grade}"
        td.append(span)
        tr.append(td)

        # Scores
        td = soup.new_tag("td")
        td.string = f"{composite_score:.2f}"
        tr.append(td)

        # Risk
        td = soup.new_tag("td")
        td.string = f"{risk_score:.1f}/10"
        tr.append(td)

        # Alternatives
        td = soup.new_tag("td")
        alternatives = holding.get("alternatives", [])
        if alternatives:
            alt_count = len(alternatives)
            span = soup.new_tag("span", attrs={"class": "alternatives-available"})
            span.string = f"💎 {alt_count} A+ disponible{'s' if alt_count > 1 else ''}"
            td.append(span)
        else:
            td.string = "-"
        tr.append(td)

        tbody.append(tr)

    table.append(tbody)
    soup.append(table)

    return soup.prettify(formatter="html")


def generate_trades_table(trades: list[dict[str, Any]]) -> str:
    """Generate HTML table for trade recommendations."""
    if not trades:
        soup = BeautifulSoup("", "html.parser")
        p = soup.new_tag("p")
        p.string = "No trades recommended."
        soup.append(p)
        return soup.prettify(formatter="html")

    soup = BeautifulSoup("", "html.parser")
    table = soup.new_tag("table", attrs={"class": "trades-table"})

    # Header
    thead = soup.new_tag("thead")
    header_row = soup.new_tag("tr")
    headers = ["Symbol", "Action", "Quantity", "Price", "Value", "Cost", "Priority"]
    for header_text in headers:
        th = soup.new_tag("th")
        th.string = header_text
        header_row.append(th)
    thead.append(header_row)
    table.append(thead)

    # Body
    tbody = soup.new_tag("tbody")
    for trade in trades:
        action_class = trade.get("action", "").lower()

        tr = soup.new_tag("tr")

        td = soup.new_tag("td")
        td.string = trade.get("symbol", "N/A")
        tr.append(td)

        td = soup.new_tag("td", attrs={"class": action_class})
        td.string = trade.get("action", "N/A")
        tr.append(td)

        td = soup.new_tag("td")
        td.string = f"{trade.get('quantity', 0):.2f}"
        tr.append(td)

        td = soup.new_tag("td")
        td.string = f"${trade.get('current_price', 0):.2f}"
        tr.append(td)

        td = soup.new_tag("td")
        td.string = f"${trade.get('trade_value', 0):.2f}"
        tr.append(td)

        td = soup.new_tag("td")
        td.string = f"${trade.get('total_estimated_cost', 0):.2f}"
        tr.append(td)

        td = soup.new_tag("td")
        td.string = str(trade.get("priority", 0))
        tr.append(td)

        tbody.append(tr)

    table.append(tbody)
    soup.append(table)

    return soup.prettify(formatter="html")


# =============================================================================
# Section Builders for HTML Reports
# =============================================================================


def add_portfolio_review_sections(generator: Any, review_data: dict[str, Any]) -> None:
    """Add portfolio review sections to HTML report generator."""
    if "portfolio_review" in review_data:
        holdings = review_data["portfolio_review"].get("holdings", [])
        processing_summary = review_data.get("processing_summary")
    else:
        holdings = review_data.get("holdings", [])
        processing_summary = None

    keep_count = sum(1 for h in holdings if h.get("decision") == "KEEP")
    sell_count = sum(1 for h in holdings if h.get("decision") == "SELL")

    soup = BeautifulSoup("", "html.parser")
    overview_div = soup.new_tag("div", attrs={"class": "portfolio-overview"})

    title = soup.new_tag("h3")
    title.string = "Portfolio Overview"
    overview_div.append(title)

    metrics_grid = soup.new_tag("div", attrs={"class": "metrics-grid"})

    # Total holdings
    metric = soup.new_tag("div", attrs={"class": "metric"})
    label = soup.new_tag("span", attrs={"class": "metric-label"})
    label.string = "Total Holdings:"
    value = soup.new_tag("span", attrs={"class": "metric-value"})
    value.string = str(len(holdings))
    metric.append(label)
    metric.append(value)
    metrics_grid.append(metric)

    # Keep count
    metric = soup.new_tag("div", attrs={"class": "metric"})
    label = soup.new_tag("span", attrs={"class": "metric-label"})
    label.string = "Keep Recommendations:"
    value = soup.new_tag("span", attrs={"class": "metric-value keep"})
    value.string = str(keep_count)
    metric.append(label)
    metric.append(value)
    metrics_grid.append(metric)

    # Sell count
    metric = soup.new_tag("div", attrs={"class": "metric"})
    label = soup.new_tag("span", attrs={"class": "metric-label"})
    label.string = "Sell Recommendations:"
    value = soup.new_tag("span", attrs={"class": "metric-value sell"})
    value.string = str(sell_count)
    metric.append(label)
    metric.append(value)
    metrics_grid.append(metric)

    overview_div.append(metrics_grid)
    soup.append(overview_div)

    # Processing summary if available
    if processing_summary:
        _add_processing_summary(soup, processing_summary)

    overview_content = soup.prettify(formatter="html")
    generator.add_section("Portfolio Overview", overview_content, "portfolio", order=1)

    # Holdings analysis
    holdings_content = generate_holdings_table(holdings)
    generator.add_section("Holdings Analysis", holdings_content, "analysis", order=2)


def _add_processing_summary(soup: BeautifulSoup, processing_summary: dict[str, Any]) -> None:
    """Add processing summary section to soup."""
    summary_div = soup.new_tag("div", attrs={"class": "processing-summary"})

    summary_title = soup.new_tag("h4")
    summary_title.string = "Processing Summary"
    summary_div.append(summary_title)

    summary_list = soup.new_tag("ul")

    li = soup.new_tag("li")
    li.string = f"Total holdings in CSV: {processing_summary['total_holdings']}"
    summary_list.append(li)

    li = soup.new_tag("li")
    li.string = f"Successfully processed: {processing_summary['processed_successfully']}"
    summary_list.append(li)

    if processing_summary["processed_with_warnings"] > 0:
        li = soup.new_tag("li")
        li.string = f"Processed with warnings: {processing_summary['processed_with_warnings']}"
        summary_list.append(li)

    if processing_summary["failed_to_process"] > 0:
        li = soup.new_tag("li")
        li.string = f"Failed to process: {processing_summary['failed_to_process']}"
        summary_list.append(li)

    li = soup.new_tag("li")
    li.string = f"By asset class: {processing_summary['by_asset_class']}"
    summary_list.append(li)

    summary_div.append(summary_list)
    soup.append(summary_div)


def add_rebalancing_sections(generator: Any, rebalancing_data: dict[str, Any]) -> None:
    """Add rebalancing sections to HTML report generator."""
    execution_summary = rebalancing_data.get("execution_summary", {})
    cost_analysis = rebalancing_data.get("cost_analysis", {})

    soup = BeautifulSoup("", "html.parser")
    summary_div = soup.new_tag("div", attrs={"class": "rebalancing-summary"})

    title = soup.new_tag("h3")
    title.string = "Rebalancing Summary"
    summary_div.append(title)

    metrics_grid = soup.new_tag("div", attrs={"class": "metrics-grid"})

    # Trades required
    metric = soup.new_tag("div", attrs={"class": "metric"})
    label = soup.new_tag("span", attrs={"class": "metric-label"})
    label.string = "Trades Required:"
    value = soup.new_tag("span", attrs={"class": "metric-value"})
    value.string = str(execution_summary.get("total_trades_required", 0))
    metric.append(label)
    metric.append(value)
    metrics_grid.append(metric)

    # Total cost
    metric = soup.new_tag("div", attrs={"class": "metric"})
    label = soup.new_tag("span", attrs={"class": "metric-label"})
    label.string = "Total Cost:"
    value = soup.new_tag("span", attrs={"class": "metric-value"})
    value.string = f"${cost_analysis.get('total_transaction_costs', 0):.2f}"
    metric.append(label)
    metric.append(value)
    metrics_grid.append(metric)

    # Recommendation
    metric = soup.new_tag("div", attrs={"class": "metric"})
    label = soup.new_tag("span", attrs={"class": "metric-label"})
    label.string = "Recommendation:"
    value = soup.new_tag("span", attrs={"class": "metric-value"})
    value.string = rebalancing_data.get("overall_recommendation", "N/A")
    metric.append(label)
    metric.append(value)
    metrics_grid.append(metric)

    summary_div.append(metrics_grid)
    soup.append(summary_div)

    summary_content = soup.prettify(formatter="html")
    generator.add_section("Rebalancing Summary", summary_content, "financial", order=3)

    # Trade recommendations
    trades = rebalancing_data.get("trade_recommendations", [])
    if trades:
        trades_content = generate_trades_table(trades)
        generator.add_section("Trade Recommendations", trades_content, "opportunity", order=4)


# =============================================================================
# Public API Exports
# =============================================================================

__all__ = [
    "generate_holdings_table",
    "generate_trades_table",
    "add_portfolio_review_sections",
    "add_rebalancing_sections",
]
