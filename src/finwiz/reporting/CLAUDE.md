# Reporting Module

HTML report generation using Python/Jinja2 templates. All rendering is 100% Python — no AI involved (AI Minimalism).

## Directory Structure

```
reporting/
├── __init__.py                          # CREW_GENERATORS registry, get_generator_for_crew()
├── base_report_generator.py             # BaseReportGenerator (abstract base, 14 methods)
├── python_report_generator.py           # PythonReportGenerator, generate_python_report()
│
├── # Per-crew generators
├── stock_report_generator.py            # StockReportGenerator
├── etf_report_generator.py              # ETFReportGenerator
├── crypto_report_generator.py           # CryptoReportGenerator
├── discovery_report_generator.py        # DiscoveryReportGenerator
├── rebalancing_report_generator.py      # RebalancingReportGenerator
├── deep_analysis_report_generator.py    # DeepAnalysisReportGenerator
├── enriched_analysis_report_generator.py # EnrichedAnalysisReportGenerator
├── final_report_generator.py            # FinalReportGenerator
├── individual_report_generator.py       # generate_individual_report_html()
│
├── # HTML infrastructure
├── section_generators.py                # generate_executive_summary(), generate_holdings_analysis()
├── consolidator.py                      # ReportConsolidator
├── html_collector.py                    # collect_html_report_paths()
├── html_auto_generator.py               # auto_generate_html()
├── export_loaders.py                    # load_exports(), load_deep_analysis_exports()
├── css_styles.py                        # get_report_css() — reads assets/report_styles.css
│
├── assets/                              # Static CSS/JS files; one file per loader function,
│                                        # named after the function (report_styles.css is the
│                                        # top-level report stylesheet exception)
│
├── css/                                 # Modular CSS loaders (read from assets/)
│   ├── css_styles.py                    # get_rebalancing_css() — concatenates the loaders below
│   ├── css_elements.py                  # get_base_styles(), get_table_styles(), ...
│   └── css_layouts.py                   # get_responsive_styles(), ...
│
├── js/                                  # JavaScript loaders (read from assets/)
│   └── javascript_code.py              # get_rebalancing_javascript()
│
└── rebalancing/                         # Rebalancing report builders
    ├── rebalancing_html_builders.py     # RebalancingHTMLBuilder
    ├── template_builders.py             # TemplateBuilder
    └── template_renderers.py            # TemplateRenderer
```

## Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `__init__.py` | `CREW_GENERATORS` | Registry mapping crew names → generators |
| `__init__.py` | `get_generator_for_crew()` | Get generator by crew name |
| `base_report_generator.py` | `BaseReportGenerator` | Abstract base class |
| `base_report_generator.py` | `create_report_jinja_env()` | Shared Jinja2 env factory (autoescape on) — use for any new generator |
| `python_report_generator.py` | `PythonReportGenerator` | Main report engine |
| `consolidator.py` | `ReportConsolidator` | Consolidate multiple reports |
| `html_auto_generator.py` | `auto_generate_html()` | Auto-generate from crew exports |

## Usage

```python
from finwiz.reporting import get_generator_for_crew

generator = get_generator_for_crew("stock_crew")
html = generator.generate_report(data={...}, output_path="output/stock/AAPL_report.html")
```

## Related Modules

- `finwiz.templates` — Jinja2 HTML templates
- `finwiz.schemas.crew_exports` — Export schemas for report data
- `finwiz.orchestrators.reporting_orchestrator` — Orchestrates report generation
