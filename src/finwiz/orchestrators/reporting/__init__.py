"""Mixins composing :class:`finwiz.orchestrators.reporting_orchestrator.ReportingOrchestrator`.

The reporting orchestrator was split into cohesive mixins (data loading/merge,
report enrichment, crew HTML generation) to keep each file focused and within
the 300-line norm. ``ReportingOrchestrator`` inherits all three, so behavior is
unchanged.
"""
