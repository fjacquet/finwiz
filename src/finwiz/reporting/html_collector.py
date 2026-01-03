"""
HTML report path collection functions for report consolidation.

Extracted from report_consolidator.py for modularity.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from finwiz.tools.logger import get_logger

if TYPE_CHECKING:
    from finwiz.schemas.crew_exports import ConsolidatedReportExport

logger = get_logger(__name__)


# Crew name to asset class mapping
CREW_ASSET_CLASSES = {
    "stock_crew": "stock",
    "etf_crew": "etf",
    "crypto_crew": "crypto",
    "deep_analysis_crew": "mixed",
    "discovery_crew": "discovery",
    "rebalancing_crew": "rebalancing",
}


@dataclass
class HTMLReportPath:
    """Represents a path to an individual HTML report."""

    ticker: str
    crew: str
    path: str
    asset_class: str = ""


def collect_html_report_paths(crew_export_paths: dict[str, list[str]]) -> list[HTMLReportPath]:
    """
    Collect paths to individual HTML reports for linking in final report.

    Searches for HTML report files alongside JSON exports and in expected
    locations. This enables the final consolidated report to link to
    individual detailed reports.

    Args:
        crew_export_paths: Dict mapping crew names to list of export file paths

    Returns:
        List of HTMLReportPath objects for all found HTML reports

    """
    html_paths: list[HTMLReportPath] = []

    for crew_name, json_paths in crew_export_paths.items():
        asset_class = CREW_ASSET_CLASSES.get(crew_name, "unknown")

        for json_path_str in json_paths:
            html_path_obj = _find_html_for_json(json_path_str, crew_name, asset_class)
            if html_path_obj:
                html_paths.append(html_path_obj)

    logger.info(f"Collected {len(html_paths)} HTML report paths")
    return html_paths


def _find_html_for_json(json_path_str: str, crew_name: str, asset_class: str) -> HTMLReportPath | None:
    """Find HTML report file for a given JSON export path."""
    json_path = Path(json_path_str)

    # Try common HTML report naming patterns
    possible_html_paths = [
        json_path.with_suffix(".html"),  # Same name with .html
        json_path.parent / f"{json_path.stem}_report.html",  # *_report.html
        json_path.parent / f"{json_path.stem.replace('_export', '_report')}.html",  # Replace _export with _report
    ]

    for html_path in possible_html_paths:
        if html_path.exists():
            ticker = _extract_ticker_from_path(json_path, crew_name)
            logger.debug(f"Found HTML report: {html_path}")
            return HTMLReportPath(
                ticker=ticker,
                crew=crew_name.replace("_crew", ""),
                path=str(html_path),
                asset_class=asset_class,
            )

    return None


def _extract_ticker_from_path(json_path: Path, crew_name: str) -> str:
    """Extract ticker symbol from file path."""
    stem = json_path.stem
    ticker = stem.replace("_export", "").replace("_deep", "").upper()

    # Handle special cases
    if crew_name == "discovery_crew":
        return "DISCOVERY"
    elif crew_name == "rebalancing_crew":
        return "REBALANCING"

    return ticker


def add_html_paths_to_analyses(
    consolidated: ConsolidatedReportExport,
    html_paths: list[HTMLReportPath],
) -> ConsolidatedReportExport:
    """
    Add HTML report paths to individual analysis objects.

    This allows the final report template to include "View Full Report"
    links for each analysis.

    Args:
        consolidated: The consolidated report export
        html_paths: List of HTML report paths to add

    Returns:
        Updated consolidated report with HTML paths added

    """
    # Create lookup by ticker
    path_lookup: dict[str, str] = {hp.ticker: hp.path for hp in html_paths}

    # Add paths to each analysis type
    _add_paths_to_list(consolidated.stock_analyses, path_lookup)
    _add_paths_to_list(consolidated.etf_analyses, path_lookup)
    _add_paths_to_list(consolidated.crypto_analyses, path_lookup)
    _add_paths_to_deep_analyses(consolidated.deep_analyses, path_lookup)

    # Add paths to discovery and rebalancing results
    if consolidated.discovery_results and "DISCOVERY" in path_lookup:
        consolidated.discovery_results.report_html_path = path_lookup["DISCOVERY"]

    if consolidated.rebalancing_results and "REBALANCING" in path_lookup:
        consolidated.rebalancing_results.report_html_path = path_lookup["REBALANCING"]

    logger.info("Added HTML paths to consolidated analyses")
    return consolidated


def _add_paths_to_list(analyses: list, path_lookup: dict[str, str]) -> None:
    """Add HTML paths to a list of analyses."""
    for analysis in analyses:
        if hasattr(analysis, "ticker") and analysis.ticker in path_lookup:
            analysis.report_html_path = path_lookup[analysis.ticker]


def _add_paths_to_deep_analyses(analyses: list, path_lookup: dict[str, str]) -> None:
    """Add HTML paths to deep analysis objects."""
    for analysis in analyses:
        ticker = getattr(analysis, "ticker", None)
        if ticker and ticker in path_lookup:
            if hasattr(analysis, "report_html_path"):
                analysis.report_html_path = path_lookup[ticker]
