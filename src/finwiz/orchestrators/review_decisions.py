"""Portfolio review decision-making and HTML generation."""

from __future__ import annotations

import logging
from typing import Any

from bs4 import BeautifulSoup

from finwiz.utils.grading_system import (
    get_grade_css_styles,
    get_portfolio_grade_summary,
    score_to_grade,
)

logger = logging.getLogger(__name__)


def generate_holdings_table(holdings: list[dict[str, Any]]) -> str:
    """
    Generate HTML table for holdings with letter grades.

    Args:
        holdings: List of holding dictionaries

    Returns:
        HTML string for holdings table

    """
    if not holdings:
        # Use bs4 for simple paragraph
        soup = BeautifulSoup("", "html.parser")
        p = soup.new_tag("p")
        p.string = "No holdings found."
        soup.append(p)
        return soup.prettify(formatter="html")

    # Calculate portfolio grade summary
    scores = [holding.get("composite_score", 0) for holding in holdings]
    grade_summary = get_portfolio_grade_summary(scores)

    # Create main soup container
    soup = BeautifulSoup("", "html.parser")

    # Add CSS styles
    style = soup.new_tag("style")
    style.string = get_grade_css_styles()
    soup.append(style)

    # Generate grade summary using BeautifulSoup
    grade_div = soup.new_tag("div", **{"class": "grade-summary"})

    # Title
    title = soup.new_tag("h4")
    title.string = "📊 Bulletin du Portefeuille"
    grade_div.append(title)

    # Average grade paragraph
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

    # Distribution paragraph
    dist_p = soup.new_tag("p")
    dist_strong = soup.new_tag("strong")
    dist_strong.string = "Répartition des notes :"
    dist_p.append(dist_strong)
    grade_div.append(dist_p)

    # Distribution list
    grade_ul = soup.new_tag("ul")
    for grade, data in grade_summary["distribution"].items():
        grade_info = score_to_grade(0.5)  # Get emoji for grade
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

    # Create holdings table
    table = soup.new_tag("table", **{"class": "holdings-table"})

    # Count deep vs shallow analysis
    deep_count = sum(1 for h in holdings if h.get("crew_analysis_used"))
    shallow_count = len(holdings) - deep_count

    # Add analysis depth summary
    if deep_count > 0:
        analysis_summary = soup.new_tag("div", **{"class": "analysis-summary"})
        summary_title = soup.new_tag("h4")
        summary_title.string = "📊 Profondeur d'Analyse"
        analysis_summary.append(summary_title)

        summary_p = soup.new_tag("p")
        summary_p.append(f"🔍 Analyse Approfondie: {deep_count} positions | ")
        summary_p.append(f"⚡ Validation Rapide: {shallow_count} positions")
        analysis_summary.append(summary_p)

        soup.append(analysis_summary)

    # Table header
    thead = soup.new_tag("thead")
    header_row = soup.new_tag("tr")
    headers = [
        "Ticker",
        "Nom",
        "Type",
        "Analyse",
        "Décision",
        "Note",
        "Scores",
        "Risque",
        "Alternatives A+",
    ]
    for header_text in headers:
        th = soup.new_tag("th")
        th.string = header_text
        header_row.append(th)
    thead.append(header_row)
    table.append(thead)

    # Table body
    tbody = soup.new_tag("tbody")
    for holding in holdings:
        decision_class = "keep" if holding.get("decision") == "KEEP" else "sell"
        risk_score = holding.get("risk", {}).get("score", 0)
        composite_score = holding.get("composite_score", 0)

        # Get grade information
        grade_info = score_to_grade(composite_score)

        # Check if deep analysis was used
        crew_analysis_used = holding.get("crew_analysis_used")
        is_deep_analysis = crew_analysis_used is not None

        # Create table row
        tr = soup.new_tag("tr")

        # Ticker cell
        td_ticker = soup.new_tag("td")
        td_ticker.string = holding.get("ticker", "N/A")
        tr.append(td_ticker)

        # Name cell
        td_name = soup.new_tag("td")
        td_name.string = holding.get("name", "N/A")
        tr.append(td_name)

        # Asset class cell
        td_asset = soup.new_tag("td")
        td_asset.string = holding.get("asset_class", "N/A").upper()
        tr.append(td_asset)

        # Analysis depth indicator cell
        td_analysis = soup.new_tag("td")
        if is_deep_analysis:
            analysis_span = soup.new_tag("span", **{"class": "analysis-deep"})
            analysis_span.string = "🔍 Deep"
            td_analysis.append(analysis_span)
            # Add crew name as tooltip
            if crew_analysis_used:
                crew_small = soup.new_tag("small")
                crew_small.string = f" ({crew_analysis_used})"
                td_analysis.append(crew_small)
        else:
            analysis_span = soup.new_tag("span", **{"class": "analysis-quick"})
            analysis_span.string = "⚡ Quick"
            td_analysis.append(analysis_span)
        tr.append(td_analysis)

        # Decision cell
        td_decision = soup.new_tag("td", **{"class": decision_class})
        td_decision.string = holding.get("decision", "N/A")
        tr.append(td_decision)

        # Grade cell with badge
        td_grade = soup.new_tag("td")
        grade_span = soup.new_tag("span", **{"class": f"grade-badge {grade_info.css_class}"})
        grade_span.string = f"{grade_info.emoji} {grade_info.grade}"
        td_grade.append(grade_span)
        tr.append(td_grade)

        # Scores cell (show detailed metrics if available from deep analysis)
        td_scores = soup.new_tag("td")
        if is_deep_analysis:
            # Extract scores from rationale bullets
            rationale_bullets = holding.get("rationale_bullets", [])
            scores_list = soup.new_tag("ul", **{"class": "scores-list"})
            for bullet in rationale_bullets:
                if "Score" in bullet or "score" in bullet:
                    score_li = soup.new_tag("li")
                    score_li.string = bullet
                    scores_list.append(score_li)
            if scores_list.contents:
                td_scores.append(scores_list)
            else:
                td_scores.string = f"{composite_score:.2f}"
        else:
            td_scores.string = f"{composite_score:.2f}"
        tr.append(td_scores)

        # Risk cell
        td_risk = soup.new_tag("td")
        td_risk.string = f"{risk_score:.1f}/10"
        tr.append(td_risk)

        # Alternatives cell
        td_alternatives = soup.new_tag("td")
        alternatives = holding.get("alternatives", [])
        if alternatives:
            alt_count = len(alternatives)
            alt_span = soup.new_tag("span", **{"class": "alternatives-available"})
            alt_span.string = f"💎 {alt_count} A+ disponible{'s' if alt_count > 1 else ''}"
            td_alternatives.append(alt_span)

            # Add alternatives list
            alt_list = soup.new_tag("ul", **{"class": "alternatives-list"})
            for alt in alternatives[:3]:  # Show top 3
                alt_li = soup.new_tag("li")
                alt_ticker = alt.get("ticker", "N/A")
                alt_grade = alt.get("grade", "A+")
                alt_score = alt.get("composite_score", 0)
                alt_li.string = f"{alt_ticker} ({alt_grade}, {alt_score:.2f})"
                alt_list.append(alt_li)
            td_alternatives.append(alt_list)
        else:
            td_alternatives.string = "-"
        tr.append(td_alternatives)

        tbody.append(tr)

    table.append(tbody)
    soup.append(table)

    return soup.prettify(formatter="html")


def generate_trades_table(trades: list[dict[str, Any]]) -> str:
    """
    Generate HTML table for trade recommendations.

    Args:
        trades: List of trade dictionaries

    Returns:
        HTML string for trades table

    """
    if not trades:
        # Use bs4 for simple paragraph
        soup = BeautifulSoup("", "html.parser")
        p = soup.new_tag("p")
        p.string = "No trades recommended."
        soup.append(p)
        return soup.prettify(formatter="html")

    # Create main soup container
    soup = BeautifulSoup("", "html.parser")

    # Create trades table
    table = soup.new_tag("table", **{"class": "trades-table"})

    # Table header
    thead = soup.new_tag("thead")
    header_row = soup.new_tag("tr")
    headers = ["Symbol", "Action", "Quantity", "Price", "Value", "Cost", "Priority"]
    for header_text in headers:
        th = soup.new_tag("th")
        th.string = header_text
        header_row.append(th)
    thead.append(header_row)
    table.append(thead)

    # Table body
    tbody = soup.new_tag("tbody")
    for trade in trades:
        action_class = trade.get("action", "").lower()

        # Create table row
        tr = soup.new_tag("tr")

        # Symbol cell
        td_symbol = soup.new_tag("td")
        td_symbol.string = trade.get("symbol", "N/A")
        tr.append(td_symbol)

        # Action cell
        td_action = soup.new_tag("td", **{"class": action_class})
        td_action.string = trade.get("action", "N/A")
        tr.append(td_action)

        # Quantity cell
        td_quantity = soup.new_tag("td")
        td_quantity.string = f"{trade.get('quantity', 0):.2f}"
        tr.append(td_quantity)

        # Price cell
        td_price = soup.new_tag("td")
        td_price.string = f"${trade.get('current_price', 0):.2f}"
        tr.append(td_price)

        # Value cell
        td_value = soup.new_tag("td")
        td_value.string = f"${trade.get('trade_value', 0):.2f}"
        tr.append(td_value)

        # Cost cell
        td_cost = soup.new_tag("td")
        td_cost.string = f"${trade.get('total_estimated_cost', 0):.2f}"
        tr.append(td_cost)

        # Priority cell
        td_priority = soup.new_tag("td")
        td_priority.string = str(trade.get("priority", 0))
        tr.append(td_priority)

        tbody.append(tr)

    table.append(tbody)
    soup.append(table)

    return soup.prettify(formatter="html")


def add_portfolio_review_sections(generator: Any, review_data: dict[str, Any]) -> None:
    """
    Add portfolio review sections to HTML report generator.

    Args:
        generator: HTML report generator instance
        review_data: Portfolio review data dictionary

    """
    # Extract holdings and processing summary
    if "portfolio_review" in review_data:
        # New format with processing summary
        holdings = review_data["portfolio_review"].get("holdings", [])
        processing_summary = review_data.get("processing_summary")
    else:
        # Legacy format
        holdings = review_data.get("holdings", [])
        processing_summary = None

    keep_count = sum(1 for h in holdings if h.get("decision") == "KEEP")
    sell_count = sum(1 for h in holdings if h.get("decision") == "SELL")

    # Create portfolio overview using bs4
    soup = BeautifulSoup("", "html.parser")
    overview_div = soup.new_tag("div", **{"class": "portfolio-overview"})

    # Title
    title = soup.new_tag("h3")
    title.string = "Portfolio Overview"
    overview_div.append(title)

    # Metrics grid
    metrics_grid = soup.new_tag("div", **{"class": "metrics-grid"})

    # Total holdings metric
    total_metric = soup.new_tag("div", **{"class": "metric"})
    total_label = soup.new_tag("span", **{"class": "metric-label"})
    total_label.string = "Total Holdings:"
    total_value = soup.new_tag("span", **{"class": "metric-value"})
    total_value.string = str(len(holdings))
    total_metric.append(total_label)
    total_metric.append(total_value)
    metrics_grid.append(total_metric)

    # Keep recommendations metric
    keep_metric = soup.new_tag("div", **{"class": "metric"})
    keep_label = soup.new_tag("span", **{"class": "metric-label"})
    keep_label.string = "Keep Recommendations:"
    keep_value = soup.new_tag("span", **{"class": "metric-value keep"})
    keep_value.string = str(keep_count)
    keep_metric.append(keep_label)
    keep_metric.append(keep_value)
    metrics_grid.append(keep_metric)

    # Sell recommendations metric
    sell_metric = soup.new_tag("div", **{"class": "metric"})
    sell_label = soup.new_tag("span", **{"class": "metric-label"})
    sell_label.string = "Sell Recommendations:"
    sell_value = soup.new_tag("span", **{"class": "metric-value sell"})
    sell_value.string = str(sell_count)
    sell_metric.append(sell_label)
    sell_metric.append(sell_value)
    metrics_grid.append(sell_metric)

    overview_div.append(metrics_grid)
    soup.append(overview_div)

    # Add processing summary if available
    if processing_summary:
        summary_div = soup.new_tag("div", **{"class": "processing-summary"})

        summary_title = soup.new_tag("h4")
        summary_title.string = "Processing Summary"
        summary_div.append(summary_title)

        # Processing metrics
        summary_list = soup.new_tag("ul")

        # Total processed
        total_li = soup.new_tag("li")
        total_li.string = f"Total holdings in CSV: {processing_summary['total_holdings']}"
        summary_list.append(total_li)

        # Successfully processed
        success_li = soup.new_tag("li")
        success_li.string = f"Successfully processed: {processing_summary['processed_successfully']}"
        summary_list.append(success_li)

        # Warnings
        if processing_summary["processed_with_warnings"] > 0:
            warning_li = soup.new_tag("li")
            warning_li.string = f"Processed with warnings: {processing_summary['processed_with_warnings']}"
            summary_list.append(warning_li)

        # Failed
        if processing_summary["failed_to_process"] > 0:
            failed_li = soup.new_tag("li")
            failed_li.string = f"Failed to process: {processing_summary['failed_to_process']}"
            summary_list.append(failed_li)

        # By asset class
        by_class_li = soup.new_tag("li")
        by_class_li.string = f"By asset class: {processing_summary['by_asset_class']}"
        summary_list.append(by_class_li)

        summary_div.append(summary_list)

        # Validation failures
        if processing_summary.get("validation_failures"):
            failures_title = soup.new_tag("h5")
            failures_title.string = "Validation Issues"
            summary_div.append(failures_title)

            failures_list = soup.new_tag("ul")
            for failure in processing_summary["validation_failures"]:
                failure_li = soup.new_tag("li")
                failure_li.string = f"{failure['ticker']}: {failure['reason']}"
                failures_list.append(failure_li)
            summary_div.append(failures_list)

        soup.append(summary_div)

    overview_content = soup.prettify(formatter="html")
    generator.add_section("Portfolio Overview", overview_content, "portfolio", order=1)

    # Holdings analysis with validation status
    holdings_content = generate_holdings_table(holdings)
    generator.add_section("Holdings Analysis", holdings_content, "analysis", order=2)


def add_rebalancing_sections(generator: Any, rebalancing_data: dict[str, Any]) -> None:
    """
    Add rebalancing sections to HTML report generator.

    Args:
        generator: HTML report generator instance
        rebalancing_data: Rebalancing data dictionary

    """
    # Rebalancing summary
    execution_summary = rebalancing_data.get("execution_summary", {})
    cost_analysis = rebalancing_data.get("cost_analysis", {})

    # Create rebalancing summary using bs4
    soup = BeautifulSoup("", "html.parser")
    summary_div = soup.new_tag("div", **{"class": "rebalancing-summary"})

    # Title
    title = soup.new_tag("h3")
    title.string = "Rebalancing Summary"
    summary_div.append(title)

    # Metrics grid
    metrics_grid = soup.new_tag("div", **{"class": "metrics-grid"})

    # Trades required metric
    trades_metric = soup.new_tag("div", **{"class": "metric"})
    trades_label = soup.new_tag("span", **{"class": "metric-label"})
    trades_label.string = "Trades Required:"
    trades_value = soup.new_tag("span", **{"class": "metric-value"})
    trades_value.string = str(execution_summary.get("total_trades_required", 0))
    trades_metric.append(trades_label)
    trades_metric.append(trades_value)
    metrics_grid.append(trades_metric)

    # Total cost metric
    cost_metric = soup.new_tag("div", **{"class": "metric"})
    cost_label = soup.new_tag("span", **{"class": "metric-label"})
    cost_label.string = "Total Cost:"
    cost_value = soup.new_tag("span", **{"class": "metric-value"})
    cost_value.string = f"${cost_analysis.get('total_transaction_costs', 0):.2f}"
    cost_metric.append(cost_label)
    cost_metric.append(cost_value)
    metrics_grid.append(cost_metric)

    # Recommendation metric
    rec_metric = soup.new_tag("div", **{"class": "metric"})
    rec_label = soup.new_tag("span", **{"class": "metric-label"})
    rec_label.string = "Recommendation:"
    rec_value = soup.new_tag("span", **{"class": "metric-value"})
    rec_value.string = rebalancing_data.get("overall_recommendation", "N/A")
    rec_metric.append(rec_label)
    rec_metric.append(rec_value)
    metrics_grid.append(rec_metric)

    summary_div.append(metrics_grid)
    soup.append(summary_div)

    summary_content = soup.prettify(formatter="html")
    generator.add_section("Rebalancing Summary", summary_content, "financial", order=3)

    # Trade recommendations
    trades = rebalancing_data.get("trade_recommendations", [])
    if trades:
        trades_content = generate_trades_table(trades)
        generator.add_section("Trade Recommendations", trades_content, "opportunity", order=4)
