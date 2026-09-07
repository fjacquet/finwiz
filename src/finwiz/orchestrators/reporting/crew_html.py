"""Enriched-file HTML report generation mixin."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from finwiz.flow_state import FinwizState


class CrewHtmlMixin:
    """Generates per-enriched-file HTML reports."""

    # Provided by ReportingOrchestrator.__init__
    state: FinwizState
    logger: Any

    def _iter_enriched_files(self) -> Iterator[tuple[str, Path]]:  # pragma: no cover - provided by ReportEnrichmentMixin
        """Declared for type-checking; implemented by ReportEnrichmentMixin."""
        raise NotImplementedError

    def generate_enriched_html_reports(self) -> dict[str, list[Path]]:
        """
        Generate HTML reports from all enriched JSON files.

        Locates ``*_enriched.json`` via the shared
        :meth:`ReportEnrichmentMixin._iter_enriched_files` resolver (session-scoped →
        generic enriched → canonical ``output/{asset_class}``, first existing dir wins)
        and generates corresponding HTML using EnrichedAnalysisReportGenerator.

        Returns:
            Dictionary mapping asset classes to lists of generated HTML paths

        """
        from finwiz.reporting.enriched_analysis_report_generator import EnrichedAnalysisReportGenerator

        generated_reports: dict[str, list[Path]] = {}
        total_generated = 0
        total_failed = 0

        generator = EnrichedAnalysisReportGenerator()
        self.logger.info("🔄 Generating HTML reports from enriched JSON files...")

        for asset_class, json_file in self._iter_enriched_files():
            try:
                data = json.loads(json_file.read_text())
                html_path = json_file.with_suffix(".html")
                generator.generate_and_save_report(data, str(html_path))

                generated_reports.setdefault(asset_class, []).append(html_path)
                total_generated += 1
                self.logger.debug(f"✅ Generated HTML: {html_path}")

            except Exception as e:
                total_failed += 1
                self.logger.warning(f"Failed to generate HTML for {json_file}: {e}")

        self.logger.info(f"📊 HTML report generation complete: {total_generated} generated, {total_failed} failed")

        return generated_reports
