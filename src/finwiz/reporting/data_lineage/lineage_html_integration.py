"""
Lineage HTML Integration Utility.

Provides functions to integrate data lineage into HTML reports.
"""

import logging
from typing import Any

from finwiz.schemas.data_lineage import DataLineage
from finwiz.reporting.data_lineage.lineage_visualizer import LineageVisualizer

logger = logging.getLogger(__name__)


def generate_lineage_section_html(lineage_dict: dict[str, Any] | None, ticker: str) -> str:
    """
    Generate HTML section for data lineage.

    Args:
        lineage_dict: Lineage data as dictionary (from DeepAnalysisResult.lineage)
        ticker: Ticker symbol

    Returns:
        HTML string with lineage section

    """
    if not lineage_dict:
        return """
        <div class="lineage-section" style="margin-top: 30px; padding: 20px; background-color: #f9f9f9; border-radius: 5px;">
            <h2>📊 Data Lineage</h2>
            <p><em>Data lineage not available for this analysis.</em></p>
        </div>
        """

    try:
        # Convert dict back to DataLineage object
        lineage = DataLineage.model_validate(lineage_dict)

        # Generate Mermaid.js diagram
        visualizer = LineageVisualizer()
        mermaid_code = visualizer.generate_mermaid_flowchart(lineage, direction="TD", include_values=True)

        # Count sources by type
        sources_by_type: dict[str, int] = {}
        for source in lineage.sources:
            sources_by_type[source.source_type] = sources_by_type.get(source.source_type, 0) + 1

        # Get defaulted fields
        defaulted_fields = [s.field_name for s in lineage.sources if s.source_type == "default"]

        # Build HTML
        html = f"""
        <div class="lineage-section" style="margin-top: 30px; padding: 20px; background-color: #f9f9f9; border-radius: 5px;">
            <h2>📊 Data Lineage</h2>

            <div class="lineage-summary" style="margin-bottom: 20px;">
                <h3>Summary</h3>
                <ul>
                    <li><strong>Ticker:</strong> {lineage.ticker}</li>
                    <li><strong>Asset Class:</strong> {lineage.asset_class}</li>
                    <li><strong>Analysis Timestamp:</strong> {lineage.analysis_timestamp}</li>
                    <li><strong>Data Sources:</strong> {len(lineage.sources)} total</li>
                    <li><strong>Calculations:</strong> {len(lineage.calculations)} steps</li>
                    <li><strong>Completeness:</strong> {lineage.completeness * 100:.1f}%</li>
                </ul>

                <h4>Data Sources by Type</h4>
                <ul>
        """

        for source_type, count in sources_by_type.items():
            emoji = "🔵" if source_type == "api" else "🟡" if source_type == "default" else "🟢"
            html += f"                    <li>{emoji} <strong>{source_type}:</strong> {count}</li>\n"

        html += "                </ul>\n"

        if defaulted_fields:
            html += f"""
                <div class="warning" style="background-color: #fff3cd; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <strong>⚠️ Note:</strong> {len(defaulted_fields)} field(s) used default values: {", ".join(defaulted_fields)}
                </div>
            """

        html += """
            </div>

            <div class="lineage-diagram" style="background-color: white; padding: 20px; border-radius: 5px; margin-top: 20px;">
                <h3>Calculation Flow</h3>
                <div class="mermaid">
        """

        html += mermaid_code

        html += """
                </div>
            </div>

            <div class="lineage-export" style="margin-top: 20px;">
                <h3>Export Options</h3>
                <p>
                    <em>Note: Export functionality requires additional integration with report generation system.</em>
                </p>
                <ul>
                    <li>📄 Export lineage as JSON</li>
                    <li>🐍 Generate Python reproducibility code</li>
                    <li>📊 Generate R reproducibility code</li>
                    <li>🖼️ Export diagram as PNG/SVG</li>
                </ul>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({ startOnLoad: true, theme: 'default' });
        </script>
        """

        return html

    except Exception as e:
        logger.error(f"Failed to generate lineage section for {ticker}: {e}")
        return f"""
        <div class="lineage-section" style="margin-top: 30px; padding: 20px; background-color: #fff3cd; border-radius: 5px;">
            <h2>📊 Data Lineage</h2>
            <p><strong>⚠️ Error:</strong> Failed to generate lineage visualization: {str(e)}</p>
        </div>
        """


def add_lineage_to_report_data(report_data: dict[str, Any], lineage_dict: dict[str, Any] | None) -> dict[str, Any]:
    """
    Add lineage information to report data dictionary.

    Args:
        report_data: Report data dictionary
        lineage_dict: Lineage data as dictionary

    Returns:
        Updated report data with lineage information

    """
    if not lineage_dict:
        report_data["has_lineage"] = False
        report_data["lineage_html"] = ""
        return report_data

    try:
        lineage = DataLineage.model_validate(lineage_dict)

        report_data["has_lineage"] = True
        report_data["lineage"] = lineage_dict
        report_data["lineage_summary"] = {
            "total_sources": len(lineage.sources),
            "total_calculations": len(lineage.calculations),
            "completeness": lineage.completeness,
            "defaulted_fields": [s.field_name for s in lineage.sources if s.source_type == "default"],
        }

        # Generate HTML section
        ticker = report_data.get("ticker", lineage.ticker)
        report_data["lineage_html"] = generate_lineage_section_html(lineage_dict, ticker)

        return report_data

    except Exception as e:
        logger.error(f"Failed to add lineage to report data: {e}")
        report_data["has_lineage"] = False
        report_data["lineage_html"] = ""
        return report_data


def get_lineage_quality_badge(lineage_dict: dict[str, Any] | None) -> str:
    """
    Get HTML badge indicating data quality based on lineage.

    Args:
        lineage_dict: Lineage data as dictionary

    Returns:
        HTML string with quality badge

    """
    if not lineage_dict:
        return '<span class="badge" style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 3px;">ℹ️ No Lineage</span>'

    try:
        lineage = DataLineage.model_validate(lineage_dict)

        # Count defaulted fields
        defaulted_count = sum(1 for s in lineage.sources if s.source_type == "default")
        total_sources = len(lineage.sources)

        if total_sources == 0:
            return '<span class="badge" style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 3px;">ℹ️ No Data</span>'

        default_ratio = defaulted_count / total_sources if total_sources > 0 else 0

        if default_ratio == 0:
            # All data from real sources
            return '<span class="badge" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 3px;">✅ High Quality Data</span>'
        elif default_ratio < 0.3:
            # Less than 30% defaults
            return '<span class="badge" style="background-color: #ffc107; color: black; padding: 5px 10px; border-radius: 3px;">⚠️ Some Estimates</span>'
        else:
            # 30% or more defaults
            return '<span class="badge" style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 3px;">⚠️ Limited Data</span>'

    except Exception as e:
        logger.error(f"Failed to generate quality badge: {e}")
        return '<span class="badge" style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 3px;">⚠️ Error</span>'
