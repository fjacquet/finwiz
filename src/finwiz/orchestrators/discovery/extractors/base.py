"""
Base class for opportunity extraction using Template Method pattern.

This module defines the abstract base class for extracting A+ investment opportunities
from discovery crew outputs. The Template Method pattern eliminates ~200 lines of
duplicate extraction logic across stock, ETF, and crypto extractors.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any


class OpportunityExtractor(ABC):
    """
    Abstract base class for extracting opportunities using Template Method pattern.

    The Template Method pattern defines the skeleton of the extraction algorithm,
    with asset-specific logic delegated to subclasses through abstract methods.

    This eliminates duplicate JSON loading, parsing, and iteration logic while
    allowing each asset class to implement its own inclusion criteria and
    opportunity building logic.
    """

    # Mirrors ExtractionEngine._NO_PRODUCER_REASON (orchestrators/extraction/engine.py)
    # -- same convention, so every "we don't have this" marker in this codebase reads
    # the same way to a downstream consumer, whichever extractor produced it.
    _NO_DATA_REASON = "writer does not emit this measurement for this candidate's source"

    def __init__(self) -> None:
        """Initialize the opportunity extractor."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def _unavailable(self, field_name: str) -> dict[str, Any]:
        """Marker for a key_metrics value this extractor cannot measure from the candidate.

        A metric that was never measured must never be indistinguishable from one
        that measured as zero: ``ter: 0.0`` or ``aum_formatted: "$0"`` reads as a
        real, often flattering data point, not as "we don't know". Use this instead
        of defaulting an absent field to 0 in ``key_metrics``.
        """
        self.logger.info(f"{field_name} unavailable for this candidate: {self._NO_DATA_REASON}.")
        return {"unavailable": True, "field": field_name, "reason": self._NO_DATA_REASON}

    def _refuse(self, candidate: dict[str, Any], idx: int, reason: str) -> None:
        """Log and refuse to build an opportunity for this candidate, naming it.

        Returns None so a caller can ``return self._refuse(...)`` directly. Used
        for a deliberate business-rule refusal -- e.g. a required derived value
        such as composite_score cannot be computed from any real data, and
        fabricating one (a "perfect" score synthesised from absent inputs) would
        be worse than skipping the candidate. This is distinct from extract()'s
        per-candidate exception handling: that catches an unexpected raise, this
        is an intentional "we won't guess" decision, so it needs its own log --
        a bare ``return None`` here is invisible to extract()'s ``if opportunity``
        check, which skips silently.
        """
        identifier = candidate.get("symbol") or candidate.get("ticker") or f"index {idx}"
        self.logger.warning(f"Refusing to build opportunity for {identifier}: {reason}")
        return None

    @staticmethod
    def _passthrough_rationale(candidate: dict[str, Any], structured_rationale: list[str]) -> list[str]:
        """Append the writer's flat rationale/recommendation onto the structured rationale.

        NewcomerDiscoveryPipeline's writer (``_to_legacy_format``) emits a flat
        ``rationale`` string and a ``recommendation`` string per candidate; the
        moat/diversification/technology-derived rationale this method receives
        never reads either, so both were silently discarded for every candidate
        that only carries this shape (i.e. every candidate this pipeline produces).

        Appended, not replacing. NewcomerDiscoveryPipeline-shaped candidates only
        ever carry reasoning in this flat pair (moat_analysis/diversification/
        technology are never populated for them), so for them this recovers
        previously-discarded data outright. Legacy AI-crew-shaped candidates
        *also* populate a flat top-level "rationale" -- as a list, not a string --
        because DataParser's wrapper-unwrapping (parsers.py's
        ``load_and_parse_json``) merges the outer wrapper's ``rationale`` list
        into the inner candidate dict when the inner dict has no "rationale" key
        of its own. Appending it here recovers that too (it was discarded before
        this method existed) without duplicating anything: the structured-field
        rationale (e.g. moat analysis) and this flat one (e.g. a numeric ROE/CAGR
        summary) describe different things. "recommendation" has no legacy-wrapper
        equivalent (the wrapper's field is "recommended_action", never merged
        under the key "recommendation"), so it remains newcomer-pipeline-only.
        """
        items = list(structured_rationale)

        writer_rationale = candidate.get("rationale")
        if isinstance(writer_rationale, str) and writer_rationale:
            items.append(writer_rationale)
        elif isinstance(writer_rationale, list):
            items.extend(str(item) for item in writer_rationale if item)

        recommendation = candidate.get("recommendation")
        if isinstance(recommendation, str) and recommendation:
            items.append(f"Recommendation: {recommendation}")

        return items

    def extract(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Template method defining the extraction algorithm.

        This method implements the common extraction logic:
        1. Iterate through candidates
        2. Check if each candidate should be included (asset-specific)
        3. Build opportunity object for included candidates (asset-specific)

        Each candidate is wrapped in its own try/except: a single malformed
        candidate (e.g. a field present but the wrong type) is skipped and
        logged by identity, not allowed to wipe every sibling in the same
        batch by escaping to a single try around the whole loop.

        Args:
            candidates: List of candidate dictionaries from JSON files

        Returns:
            List of opportunity dictionaries matching APlusOpportunity schema

        """
        if not candidates:
            return []

        opportunities = []

        for idx, candidate in enumerate(candidates):
            try:
                # Asset-specific inclusion logic
                if not self._should_include(candidate):
                    continue

                # Asset-specific opportunity building
                opportunity = self._build_opportunity(candidate, idx)

                if opportunity:
                    opportunities.append(opportunity)

            except Exception as e:
                identifier = candidate.get("symbol") or candidate.get("ticker") or f"index {idx}"
                self.logger.error(f"Skipping malformed candidate {identifier}: {e!s}", exc_info=True)
                continue

        self.logger.info(f"Extracted {len(opportunities)} opportunities")
        return opportunities

    @abstractmethod
    def _should_include(self, candidate: dict[str, Any]) -> bool:
        """
        Determine if candidate should be included (asset-specific).

        Subclasses implement their own inclusion criteria based on:
        - Grade requirements (A+ or A)
        - Asset-specific thresholds
        - Data quality checks

        Args:
            candidate: Candidate dictionary from JSON file

        Returns:
            True if candidate should be included, False otherwise

        """
        pass

    @abstractmethod
    def _build_opportunity(self, candidate: dict[str, Any], idx: int) -> dict[str, Any] | None:
        """
        Build opportunity object from candidate (asset-specific).

        Subclasses implement their own opportunity building logic:
        - Extract asset-specific metrics
        - Calculate composite scores
        - Format key metrics
        - Build rationale

        Args:
            candidate: Candidate dictionary from JSON file
            idx: Index of candidate in list (for ranking)

        Returns:
            Opportunity dictionary matching APlusOpportunity schema, or None if building fails

        """
        pass
