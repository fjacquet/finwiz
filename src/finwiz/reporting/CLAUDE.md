# Reporting Module

HTML report generation using Python/Jinja2 templates. All rendering is 100% Python — no AI involved (AI Minimalism).

## Directory Structure

```
reporting/
├── __init__.py                          # Package exports
├── base_report_generator.py             # create_report_jinja_env() — shared Jinja2 env factory
├── python_report_generator.py           # PythonReportGenerator, generate_python_report()
│
├── deep_analysis_report_generator.py    # DeepAnalysisReportGenerator
├── enriched_analysis_report_generator.py # EnrichedAnalysisReportGenerator — live per-holding HTML producer
│
├── # HTML infrastructure
├── section_generators.py                # Facade only — re-exports from sections/
├── sections/                            # THE REAL SECTION GENERATORS
│   ├── analysis.py                      # generate_deep_analysis_section()
│   ├── common.py
│   ├── discovery.py
│   ├── factpack.py
│   ├── holdings.py
│   ├── insights.py
│   ├── macro.py
│   ├── portfolio_summary.py
│   └── sentiment.py
└── css_styles.py                        # get_report_css() — reads assets/report_styles.css
```

`assets/` holds one static file: `report_styles.css`, read by `css_styles.py`'s
`get_report_css()` — the live stylesheet for `python_report_generator.py` and
`sections/posture_page.py`. The `css/` and `js/` subdirectories (modular
rebalancing-report CSS/JS loaders — `css/css_styles.py`'s `get_rebalancing_css()`,
`css/css_elements.py`, `css/css_layouts.py`, `js/javascript_code.py`) and the ten
`css_*.css` + one `rebalancing_javascript.js` files they read from `assets/` were
deleted: their only consumer, `reporting/rebalancing/template_builders.py`, was
deleted along with the rest of the `rebalancing/` subdirectory below.

The `rebalancing/` subdirectory (`rebalancing_html_builders.py`, `template_builders.py`,
`template_renderers.py`) was deleted along with `orchestrators/portfolio_rebalancing.py`
and `tools/rebalancing_report_generator.py` — its only consumers — once the two crews
that used those tools (`investment_discovery_crew`, `portfolio_rebalancing_crew`) were
removed.

The five per-crew report generators (`stock_report_generator.py`,
`etf_report_generator.py`, `crypto_report_generator.py`,
`discovery_report_generator.py`, `rebalancing_report_generator.py`) and the
`CREW_GENERATORS` registry / `get_generator_for_crew()` were deleted: they
were reachable only from `generate_all_crew_html_reports`, which a live run
never called (`crew_export_paths` was always empty — nothing populated it
after the crew subsystem was removed, see #187). The live per-holding HTML
path is `enriched_analysis_report_generator.py`, rendered at analysis time by
`DeepAnalysisOrchestrator._store_enriched_analysis()`. A second, redundant
reporting-phase render (`ReportingOrchestrator.generate_enriched_html_reports()`,
producing byte-identical `{ticker}_enriched.html` files) was deleted; see #195.

`BaseReportGenerator`, the abstract base those five generators subclassed, was
itself deleted from `base_report_generator.py` once its last subclass was
gone — `create_report_jinja_env()` in the same file is unrelated and stays live.

## Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `base_report_generator.py` | `create_report_jinja_env()` | Shared Jinja2 env factory (autoescape on) — use for any new generator |
| `python_report_generator.py` | `PythonReportGenerator` | Main report engine |
| `enriched_analysis_report_generator.py` | `EnrichedAnalysisReportGenerator` | Live per-holding HTML generator |

## Usage

```python
from finwiz.reporting.enriched_analysis_report_generator import EnrichedAnalysisReportGenerator

generator = EnrichedAnalysisReportGenerator()
generator.generate_and_save_report(data={...}, output_path="output/stock/AAPL_report.html")
```

## Related Modules

- `finwiz.templates` — Jinja2 HTML templates
- `finwiz.schemas.crew_exports` — Export schemas for report data
- `finwiz.orchestrators.reporting_orchestrator` — Orchestrates report generation
