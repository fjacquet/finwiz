"""
Shared Jinja2 environment factory for report generators.

This is the foundation for AI Minimalism - HTML generation via Python templates
instead of LLM calls (100% cost reduction, 500x faster, 100% reliable).

The BaseReportGenerator abstract base class that used to live here was deleted:
its five subclasses (stock/etf/crypto/discovery/rebalancing report generators)
were removed in ebc11dd6 along with the CREW_GENERATORS registry, and nothing
else subclassed it. create_report_jinja_env below is still live — it backs
enriched_analysis_report_generator.py and deep_analysis_report_generator.py.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def create_report_jinja_env(template_dir: Path | str) -> Environment:
    """Jinja2 environment with the report-rendering configuration shared by all generators."""
    return Environment(  # nosemgrep: python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True,  # Security: auto-escape HTML
        trim_blocks=True,
        lstrip_blocks=True,
    )
