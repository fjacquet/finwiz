"""HTML table generators for portfolio review reports."""

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
