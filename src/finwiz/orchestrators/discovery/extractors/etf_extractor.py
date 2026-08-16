"""
ETF opportunity extractor implementation.

This module implements ETF-specific extraction logic for A+ investment opportunities.
"""

from typing import Any

from finwiz.orchestrators.discovery.extractors.base import OpportunityExtractor


class ETFOpportunityExtractor(OpportunityExtractor):
    """Extract ETF opportunities with ETF-specific logic."""

    def _should_include(self, candidate: dict[str, Any]) -> bool:
        """
        ETF-specific inclusion logic.

        Includes ETFs with:
        - Grade A+ or A
        - Valid symbol and name
        - Low expense ratio (TER <= 0.15%)

        Args:
            candidate: ETF candidate dictionary

        Returns:
            True if ETF should be included

        """
        grade = candidate.get("grade", "")
        if grade not in ["A+", "A"]:
            return False

        # NewcomerDiscoveryPipeline's writer emits "ticker", not "symbol" --
        # accept either so its payload isn't silently filtered out.
        symbol = candidate.get("symbol") or candidate.get("ticker", "")
        fund_name = candidate.get("name", "")

        if not (symbol and fund_name):
            return False

        # Check expense ratio threshold
        # Try cost_metrics first, then key_metrics (for test data compatibility)
        cost_metrics = candidate.get("cost_metrics", {})
        key_metrics = candidate.get("key_metrics", {})
        if "ter" in cost_metrics:
            ter = cost_metrics["ter"]
        elif "ter" in key_metrics:
            ter = key_metrics["ter"]
        else:
            # No TER signal at all -- e.g. NewcomerDiscoveryPipeline's candidates
            # never carry cost_metrics/key_metrics. Defaulting to a fail-value
            # here would silently exclude every candidate from that source; not
            # having the signal is not the same as having a bad one.
            return True

        return bool(ter <= 0.15)

    def _build_opportunity(self, candidate: dict[str, Any], idx: int) -> dict[str, Any] | None:
        """
        Build ETF opportunity object.

        Extracts:
        - Cost metrics (TER, AUM, tracking error)
        - Composite score calculation
        - Diversification as rationale
        - Risk assessment

        Args:
            candidate: ETF candidate dictionary
            idx: Index for ranking

        Returns:
            ETF opportunity dictionary

        """
        try:
            symbol = candidate.get("symbol") or candidate.get("ticker", "")
            fund_name = candidate.get("name", "")
            grade = candidate.get("grade", "")

            # Use pre-calculated composite score if available, otherwise calculate from cost metrics
            if "composite_score" in candidate:
                composite_score = candidate.get("composite_score", 0.0)
            else:
                # Extract cost metrics for composite score calculation
                cost_metrics = candidate.get("cost_metrics", {})
                ter = cost_metrics.get("ter", 0.0)
                aum = cost_metrics.get("aum_usd", 0)
                tracking_error = cost_metrics.get("tracking_error_3y", 0.0)
                # Calculate composite score from cost efficiency
                composite_score = min((1 - ter) * 0.4 + (1 - tracking_error) * 0.4 + 0.2, 1.0)

            # Use pre-calculated confidence if available
            if "confidence_level" in candidate:
                confidence = candidate.get("confidence_level", 0.90)
            else:
                confidence = 0.90 if grade == "A+" else 0.80

            # Extract cost metrics for key metrics. "cost_metrics" itself being
            # absent (not merely {}) means this candidate's source never measured
            # these -- distinct from an explicit {} (measured, found nothing).
            has_cost_metrics = "cost_metrics" in candidate
            cost_metrics = candidate.get("cost_metrics", {})
            ter = cost_metrics.get("ter", 0.0) if has_cost_metrics else None
            aum = cost_metrics.get("aum_usd", 0) if has_cost_metrics else None
            tracking_error = cost_metrics.get("tracking_error_3y", 0.0) if has_cost_metrics else None

            # Format AUM for display -- an unmeasured AUM must not render as "$0",
            # which reads as a real (and oddly tiny) fund size, not as "unknown".
            if aum is None:
                aum_str: Any = self._unavailable("aum_formatted")
            elif aum >= 1e9:
                aum_str = f"${aum / 1e9:.1f}B"
            elif aum >= 1e6:
                aum_str = f"${aum / 1e6:.1f}M"
            else:
                aum_str = f"${aum:,.0f}"

            # Extract risk assessment
            risk_assessment = candidate.get("risk_assessment") or {}
            risk_score = risk_assessment.get("score", 3.0)

            # Extract diversification as rationale using helper method, then append
            # the writer's flat rationale/recommendation so neither is dropped.
            # "diversification" itself being absent (not merely {}) means this
            # candidate's source never measured it; _extract_diversification_info
            # treats {} as "measured, found nothing" (its own tested contract), so
            # the presence check has to happen here, before the call.
            from finwiz.orchestrators.extraction.aplus import APlusDataExtractor

            extractor = APlusDataExtractor()
            if "diversification" in candidate:
                diversification = candidate["diversification"]
                holdings_count, _top_10_concentration, rationale = extractor._extract_diversification_info(diversification)
            else:
                diversification = {}
                holdings_count, rationale = None, []
            rationale = self._passthrough_rationale(candidate, rationale)

            # Build key metrics. An unmeasured metric is marked unavailable rather
            # than defaulted to 0 -- e.g. ter: 0.0 reads as a real, excellent (and
            # gate-passing) measurement, not as "unknown".
            key_metrics = {
                "ter": ter if ter is not None else self._unavailable("ter"),
                "aum_usd": aum if aum is not None else self._unavailable("aum_usd"),
                "aum_formatted": aum_str,
                "tracking_error_3y": tracking_error if tracking_error is not None else self._unavailable("tracking_error_3y"),
                "holdings_count": holdings_count if holdings_count is not None else self._unavailable("holdings_count"),
            }

            # Return dict matching APlusOpportunity schema
            return {
                "symbol": symbol,
                "name": fund_name,
                "grade": grade,
                "composite_score": composite_score,
                "confidence": confidence,
                "risk_score": risk_score,
                "allocation_recommendation": diversification.get("sector_breakdown", "") if isinstance(diversification, dict) else "",
                "replacement_note": candidate.get("implementation", {}).get("entry_strategy", ""),
                "rationale": rationale,
                "key_metrics": key_metrics,
            }

        except Exception as e:
            self.logger.error(f"Failed to build ETF opportunity: {e!s}", exc_info=True)
            return None
