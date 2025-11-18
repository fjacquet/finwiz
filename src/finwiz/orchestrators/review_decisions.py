"""Portfolio review decision-making and section builders."""

from __future__ import annotations

import logging
from typing import Any

from bs4 import BeautifulSoup

from finwiz.orchestrators.review_html_tables import (
    generate_holdings_table,
    generate_trades_table,
)

logger = logging.getLogger(__name__)


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
