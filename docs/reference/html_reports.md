# HTML Reports Reference

## The template-conversion chain was removed (#194)

This page used to document a JSON-to-HTML conversion system: nine Jinja
templates in `src/finwiz/templates/`, a `JsonToHtmlConverter` with a
`TEMPLATE_MAPPING` dict, an `auto_generate_html()` helper, and
`scripts/generate_html_reports.py` to batch-convert saved JSON files. None of
it had a reachable caller in the production flow — it was deleted in #194
along with the templates it rendered (`backtesting_results.html`,
`portfolio_review.html`, `a_plus_discovery.html`,
`deep_analysis_consolidated.html`, `discovery_latest.html`,
`validation_report.html`, `portfolio_processing_summary.html`,
`optimization_report.html`, `base_template.html`, and others).

## The live HTML report path

FinWiz's production reports are generated directly by Python, not by
converting saved JSON through a template-mapping layer. See
`src/finwiz/reporting/CLAUDE.md` for the module layout, and
`src/finwiz/templates/CLAUDE.md` for the surviving templates
(`crew_reports/base.html`, `crew_reports/deep_analysis_report.html.j2`,
`enriched_analysis_report.html`, and the `partials/` they include).

Key entry points:

- `finwiz.reporting.python_report_generator.PythonReportGenerator` — main
  report engine.
- `finwiz.reporting.enriched_analysis_report_generator.EnrichedAnalysisReportGenerator` —
  live per-holding HTML generator, invoked by `DeepAnalysisOrchestrator`
  (`_store_enriched_analysis()`) at analysis time.
- `finwiz.reporting.css_styles.get_report_css()` — shared stylesheet.

See [`docs/reference/integration/python_pipeline_integration.md`](integration/python_pipeline_integration.md)
for how this fits into the flow, and [`docs/how-to/use_python_pipeline.md`](../how-to/use_python_pipeline.md)
for running it.
