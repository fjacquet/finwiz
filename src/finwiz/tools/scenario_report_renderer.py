"""
Scenario report HTML renderer using BeautifulSoup4.

Extracted from ScenarioComparisonReportGenerator for focused HTML generation.
"""

from typing import Any

from bs4 import BeautifulSoup


def render_scenario_report_template(template_data: dict[str, Any]) -> str:
    """Render the scenario report HTML template using BeautifulSoup4."""
    soup = BeautifulSoup("", "html.parser")
    html = soup.new_tag("html", lang="en")

    # Build document sections
    head = _build_head(soup, template_data)
    body = _build_body(soup, template_data)

    html.append(head)
    html.append(body)
    soup.append(html)

    return "<!DOCTYPE html>\n" + soup.prettify(formatter="html")


def _build_head(soup: BeautifulSoup, template_data: dict[str, Any]) -> Any:
    """Build HTML head section."""
    head = soup.new_tag("head")

    charset_meta = soup.new_tag("meta")
    charset_meta["charset"] = "UTF-8"
    viewport_meta = soup.new_tag("meta")
    viewport_meta["name"] = "viewport"
    viewport_meta["content"] = "width=device-width, initial-scale=1.0"
    title_tag = soup.new_tag("title")
    title_tag.string = template_data["title"]

    style_tag = soup.new_tag("style")
    style_tag.string = """
    body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
    .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
    .section { margin-bottom: 30px; }
    .section h2 { color: #333; border-bottom: 2px solid #007acc; padding-bottom: 5px; }
    .section h3 { color: #555; }
    table { width: 100%; border-collapse: collapse; margin: 10px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; font-weight: bold; }
    .metric { display: inline-block; margin: 10px; padding: 10px; background: #f9f9f9; border-radius: 5px; }
    .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; }
    .recommendation { background: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; }
    .key-finding { background: #e2e3e5; padding: 8px; margin: 5px 0; border-radius: 3px; }
    """

    head.append(charset_meta)
    head.append(viewport_meta)
    head.append(title_tag)
    head.append(style_tag)
    return head


def _build_body(soup: BeautifulSoup, template_data: dict[str, Any]) -> Any:
    """Build HTML body with all sections."""
    body = soup.new_tag("body")

    body.append(_build_header_section(soup, template_data))
    body.append(_build_executive_summary_section(soup, template_data))
    body.append(_build_analysis_overview_section(soup, template_data))
    body.append(_build_whatif_section(soup, template_data))
    body.append(_build_monte_carlo_section(soup, template_data))
    body.append(_build_sensitivity_section(soup, template_data))
    body.append(_build_recommendations_section(soup, template_data))
    body.append(_build_comparisons_section(soup, template_data))
    body.append(_build_footer(soup, template_data))

    return body


def _build_header_section(soup: BeautifulSoup, template_data: dict[str, Any]) -> Any:
    """Build header section."""
    header_div = soup.new_tag("div")
    header_div["class"] = "header"
    header_h1 = soup.new_tag("h1")
    header_h1.string = template_data["title"]
    header_div.append(header_h1)

    gen_p = soup.new_tag("p")
    gen_strong = soup.new_tag("strong")
    gen_strong.string = "Generated:"
    gen_p.append(gen_strong)
    gen_p.append(f" {template_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    header_div.append(gen_p)

    portfolio_p = soup.new_tag("p")
    portfolio_strong = soup.new_tag("strong")
    portfolio_strong.string = "Portfolio ID:"
    portfolio_p.append(portfolio_strong)
    portfolio_p.append(f" {template_data['summary_sections']['analysis_metadata']['portfolio_id']}")
    header_div.append(portfolio_p)

    return header_div


def _build_executive_summary_section(soup: BeautifulSoup, template_data: dict[str, Any]) -> Any:
    """Build executive summary section."""
    exec_section = soup.new_tag("div")
    exec_section["class"] = "section"
    exec_h2 = soup.new_tag("h2")
    exec_h2.string = "Executive Summary"
    exec_section.append(exec_h2)

    exec_p = soup.new_tag("p")
    exec_p.string = template_data["summary_sections"]["executive_summary"]
    exec_section.append(exec_p)

    findings_h3 = soup.new_tag("h3")
    findings_h3.string = "Key Findings"
    exec_section.append(findings_h3)

    for finding in template_data["summary_sections"]["key_findings"]:
        finding_div = soup.new_tag("div")
        finding_div["class"] = "key-finding"
        finding_div.string = finding
        exec_section.append(finding_div)

    return exec_section


def _build_analysis_overview_section(soup: BeautifulSoup, template_data: dict[str, Any]) -> Any:
    """Build analysis overview section."""
    overview_section = soup.new_tag("div")
    overview_section["class"] = "section"
    overview_h2 = soup.new_tag("h2")
    overview_h2.string = "Analysis Overview"
    overview_section.append(overview_h2)

    metadata = template_data["summary_sections"]["analysis_metadata"]

    for label, key in [
        ("Scenarios Analyzed:", "num_scenarios"),
        ("Sensitivity Parameters:", "num_sensitivity_params"),
    ]:
        metric = soup.new_tag("div")
        metric["class"] = "metric"
        strong = soup.new_tag("strong")
        strong.string = label
        metric.append(strong)
        metric.append(f" {metadata[key]}")
        overview_section.append(metric)

    mc_metric = soup.new_tag("div")
    mc_metric["class"] = "metric"
    mc_strong = soup.new_tag("strong")
    mc_strong.string = "Monte Carlo Simulations:"
    mc_metric.append(mc_strong)
    mc_metric.append(f" {metadata['monte_carlo_simulations']:,}")
    overview_section.append(mc_metric)

    return overview_section


def _build_whatif_section(soup: BeautifulSoup, template_data: dict[str, Any]) -> Any:
    """Build what-if scenario analysis section."""
    whatif_section = soup.new_tag("div")
    whatif_section["class"] = "section"
    whatif_h2 = soup.new_tag("h2")
    whatif_h2.string = "What-If Scenario Analysis"
    whatif_section.append(whatif_h2)

    whatif_table = _build_table(
        soup,
        template_data["comparison_tables"]["what_if_scenarios"]["headers"],
        template_data["comparison_tables"]["what_if_scenarios"]["rows"],
    )
    whatif_section.append(whatif_table)

    return whatif_section


def _build_monte_carlo_section(soup: BeautifulSoup, template_data: dict[str, Any]) -> Any:
    """Build Monte Carlo simulation results section."""
    mc_section = soup.new_tag("div")
    mc_section["class"] = "section"
    mc_h2 = soup.new_tag("h2")
    mc_h2.string = "Monte Carlo Simulation Results"
    mc_section.append(mc_h2)

    mc_summary = template_data["monte_carlo_summary"]

    for section_title, section_key in [
        ("Simulation Parameters", "simulation_params"),
        ("Portfolio Outcomes", "portfolio_outcomes"),
        ("Risk Metrics", "risk_metrics"),
        ("Rebalancing Metrics", "rebalancing_metrics"),
    ]:
        h3 = soup.new_tag("h3")
        h3.string = section_title
        mc_section.append(h3)

        for k, v in mc_summary[section_key].items():
            metric_div = soup.new_tag("div", attrs={"class": "metric"})
            metric_strong = soup.new_tag("strong")
            metric_strong.string = f"{k}:"
            metric_div.append(metric_strong)
            metric_div.append(f" {v}")
            mc_section.append(metric_div)

    return mc_section


def _build_sensitivity_section(soup: BeautifulSoup, template_data: dict[str, Any]) -> Any:
    """Build sensitivity analysis section."""
    sens_section = soup.new_tag("div", attrs={"class": "section"})
    sens_h2 = soup.new_tag("h2")
    sens_h2.string = "Sensitivity Analysis"
    sens_section.append(sens_h2)

    sens_p = soup.new_tag("p")
    sens_p.string = "The following parameters show the highest sensitivity to portfolio outcomes:"
    sens_section.append(sens_p)

    for chart_data in template_data["sensitivity_charts"].values():
        chart_h3 = soup.new_tag("h3")
        chart_h3.string = chart_data["parameter_name"]
        sens_section.append(chart_h3)

        optimal_p = soup.new_tag("p")
        optimal_strong = soup.new_tag("strong")
        optimal_strong.string = "Optimal Value:"
        optimal_p.append(optimal_strong)
        optimal_p.append(f" {chart_data['optimal_label']}")
        sens_section.append(optimal_p)

        score_p = soup.new_tag("p")
        score_strong = soup.new_tag("strong")
        score_strong.string = "Sensitivity Score:"
        score_p.append(score_strong)
        score_p.append(f" {chart_data['sensitivity_score']:.1f}")
        sens_section.append(score_p)

    return sens_section


def _build_recommendations_section(soup: BeautifulSoup, template_data: dict[str, Any]) -> Any:
    """Build recommendations section."""
    rec_section = soup.new_tag("div", attrs={"class": "section"})
    rec_h2 = soup.new_tag("h2")
    rec_h2.string = "Recommendations"
    rec_section.append(rec_h2)

    # Optimal Parameters
    opt_h3 = soup.new_tag("h3")
    opt_h3.string = "Optimal Parameters"
    rec_section.append(opt_h3)

    for k, v in template_data["recommendations"]["optimal_parameters"].items():
        metric_div = soup.new_tag("div", attrs={"class": "metric"})
        metric_strong = soup.new_tag("strong")
        metric_strong.string = f"{k}:"
        metric_div.append(metric_strong)
        metric_div.append(f" {v}")
        rec_section.append(metric_div)

    # Priority Actions
    actions_h3 = soup.new_tag("h3")
    actions_h3.string = "Priority Actions"
    rec_section.append(actions_h3)

    for action in template_data["recommendations"]["priority_actions"]:
        action_div = soup.new_tag("div", attrs={"class": "recommendation"})
        action_div.string = action
        rec_section.append(action_div)

    # Implementation Notes
    impl_h3 = soup.new_tag("h3")
    impl_h3.string = "Implementation Notes"
    rec_section.append(impl_h3)

    for note in template_data["recommendations"]["implementation_notes"]:
        note_div = soup.new_tag("div", attrs={"class": "recommendation"})
        note_div.string = note
        rec_section.append(note_div)

    # Risk Warnings
    if template_data["recommendations"]["risk_warnings"]:
        warnings_h3 = soup.new_tag("h3")
        warnings_h3.string = "Risk Warnings"
        rec_section.append(warnings_h3)

        for warning in template_data["recommendations"]["risk_warnings"]:
            warning_div = soup.new_tag("div", attrs={"class": "warning"})
            warning_div.string = warning
            rec_section.append(warning_div)

    return rec_section


def _build_comparisons_section(soup: BeautifulSoup, template_data: dict[str, Any]) -> Any:
    """Build scenario comparisons section."""
    comp_section = soup.new_tag("div", attrs={"class": "section"})
    comp_h2 = soup.new_tag("h2")
    comp_h2.string = "Scenario Comparisons"
    comp_section.append(comp_h2)

    comparison_data = template_data["comparison_tables"]["scenario_comparisons"]
    if comparison_data["rows"]:
        comp_table = _build_table(soup, comparison_data["headers"], comparison_data["rows"])
        comp_section.append(comp_table)
    else:
        no_comp_p = soup.new_tag("p")
        no_comp_p.string = "No scenario comparisons available."
        comp_section.append(no_comp_p)

    return comp_section


def _build_footer(soup: BeautifulSoup, template_data: dict[str, Any]) -> Any:
    """Build footer section."""
    footer = soup.new_tag(
        "footer",
        style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em;",
    )

    footer_p1 = soup.new_tag("p")
    footer_p1.string = "Generated by FinWiz Portfolio Rebalancing Scenario Analyzer"
    footer.append(footer_p1)

    footer_p2 = soup.new_tag("p")
    footer_p2.string = f"Report generated on {template_data['timestamp'].strftime('%Y-%m-%d at %H:%M:%S')}"
    footer.append(footer_p2)

    return footer


def _build_table(soup: BeautifulSoup, headers: list[str], rows: list[list[Any]]) -> Any:
    """Build an HTML table."""
    table = soup.new_tag("table")
    thead = soup.new_tag("thead")
    header_row = soup.new_tag("tr")

    for header in headers:
        th = soup.new_tag("th")
        th.string = header
        header_row.append(th)

    thead.append(header_row)
    table.append(thead)

    tbody = soup.new_tag("tbody")
    for row in rows:
        tr = soup.new_tag("tr")
        for cell in row:
            td = soup.new_tag("td")
            td.string = str(cell)
            tr.append(td)
        tbody.append(tr)

    table.append(tbody)
    return table
