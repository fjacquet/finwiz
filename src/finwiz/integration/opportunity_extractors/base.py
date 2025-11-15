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

    def __init__(self) -> None:
        """Initialize the opportunity extractor."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Template method defining the extraction algorithm.

        This method implements the common extraction logic:
        1. Iterate through candidates
        2. Check if each candidate should be included (asset-specific)
        3. Build opportunity object for included candidates (asset-specific)

        Args:
            candidates: List of candidate dictionaries from JSON files

        Returns:
            List of opportunity dictionaries matching APlusOpportunity schema

        """
        if not candidates:
            return []

        opportunities = []

        try:
            for idx, candidate in enumerate(candidates):
                # Asset-specific inclusion logic
                if not self._should_include(candidate):
                    continue

                # Asset-specific opportunity building
                opportunity = self._build_opportunity(candidate, idx)

                if opportunity:
                    opportunities.append(opportunity)

            self.logger.info(f"Extracted {len(opportunities)} opportunities")
            return opportunities

        except Exception as e:
            self.logger.error(f"Failed to extract opportunities: {str(e)}", exc_info=True)
            return []

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
