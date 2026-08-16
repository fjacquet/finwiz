"""
Stock opportunity extractor implementation.

This module implements stock-specific extraction logic for A+ investment opportunities.
"""

from typing import Any

from finwiz.orchestrators.discovery.extractors.base import OpportunityExtractor


class StockOpportunityExtractor(OpportunityExtractor):
    """Extract stock opportunities with stock-specific logic."""

    def _should_include(self, candidate: dict[str, Any]) -> bool:
        """
        Stock-specific inclusion logic.

        Includes stocks with:
        - Grade A+ or A
        - Valid symbol and name

        Args:
            candidate: Stock candidate dictionary

        Returns:
            True if stock should be included

        """
        grade = candidate.get("grade", "")
        if grade not in ["A+", "A"]:
            return False

        # NewcomerDiscoveryPipeline's writer emits "ticker", not "symbol" --
        # accept either so its payload isn't silently filtered out.
        symbol = candidate.get("symbol") or candidate.get("ticker", "")
        company_name = candidate.get("name", "")

        return bool(symbol and company_name)

    def _build_opportunity(self, candidate: dict[str, Any], idx: int) -> dict[str, Any] | None:
        """
        Build stock opportunity object.

        Extracts:
        - Fundamental metrics (ROE, revenue growth, debt ratio)
        - Composite score calculation
        - Moat analysis as rationale
        - Risk assessment

        Args:
            candidate: Stock candidate dictionary
            idx: Index for ranking

        Returns:
            Stock opportunity dictionary

        """
        symbol = candidate.get("symbol") or candidate.get("ticker", "")
        company_name = candidate.get("name", "")
        grade = candidate.get("grade", "")
        has_fundamentals = "fundamentals" in candidate

        # Use pre-calculated composite score if available, otherwise calculate from
        # fundamentals. If neither is available, refuse rather than synthesise a
        # score from absent inputs -- e.g. an all-zero fundamentals fallback would
        # score a 0.2, a number that looks computed but means nothing.
        if "composite_score" in candidate:
            composite_score = candidate.get("composite_score", 0.0)
        elif has_fundamentals:
            fundamentals = candidate["fundamentals"]
            roe = fundamentals.get("roe_3y_avg", 0)
            revenue_growth = fundamentals.get("revenue_cagr_5y", 0)
            debt_ratio = fundamentals.get("debt_to_equity", 0)
            composite_score = min((roe / 20 * 0.4) + (revenue_growth / 15 * 0.4) + ((1 - min(debt_ratio, 1)) * 0.2), 1.0)
        else:
            self._refuse(candidate, idx, "no composite_score and no fundamentals to derive one from")
            return None

        # Use pre-calculated confidence if available, otherwise fall back to a
        # grade-derived default -- and note that it's a default, not a measurement,
        # so a reader can't mistake it for one sitting beside real key_metrics.
        confidence_provenance = None
        if "confidence_level" in candidate:
            confidence = candidate.get("confidence_level", 0.85)
        else:
            confidence = 0.85 if grade == "A+" else 0.75
            confidence_provenance = f"Confidence {confidence} derived from grade {grade}, not measured"

        # Extract fundamentals for key metrics. "fundamentals" itself being
        # absent (not merely {}) means this candidate's source never measured
        # these -- distinct from an explicit {} (measured, found nothing).
        if has_fundamentals:
            fundamentals = candidate["fundamentals"]
            roe = fundamentals.get("roe_3y_avg", 0)
            revenue_growth = fundamentals.get("revenue_cagr_5y", 0)
            debt_ratio = fundamentals.get("debt_to_equity", 0)
        else:
            roe = revenue_growth = debt_ratio = None

        # Extract risk assessment, noting when the score is a default rather than
        # a real measurement (same reasoning as confidence, above).
        risk_assessment = candidate.get("risk_assessment") or {}
        risk_provenance = None
        if isinstance(risk_assessment, dict) and "score" in risk_assessment:
            risk_score = risk_assessment["score"]
        else:
            risk_score = 5.0
            risk_provenance = f"Risk score {risk_score} is a default, not measured"

        # Extract moat analysis as rationale, then append the writer's flat
        # rationale/recommendation -- NewcomerDiscoveryPipeline candidates carry
        # their reasoning there, not in moat_analysis, so neither is dropped.
        from finwiz.orchestrators.extraction.aplus import APlusDataExtractor

        extractor = APlusDataExtractor()
        moat_analysis = candidate.get("moat_analysis", {})
        moat_type, moat_strength, rationale = extractor._extract_moat_info(moat_analysis)
        rationale = self._passthrough_rationale(candidate, rationale)
        if confidence_provenance:
            rationale.append(confidence_provenance)
        if risk_provenance:
            rationale.append(risk_provenance)

        # Extract key metrics from fundamentals. An unmeasured metric is marked
        # unavailable rather than defaulted to 0 -- a 0 reads as a real, often
        # flattering measurement (e.g. debt_to_equity: 0), not as "unknown".
        key_metrics = {
            "roe_3y_avg": roe if roe is not None else self._unavailable("roe_3y_avg"),
            "revenue_cagr_5y": revenue_growth if revenue_growth is not None else self._unavailable("revenue_cagr_5y"),
            "debt_to_equity": debt_ratio if debt_ratio is not None else self._unavailable("debt_to_equity"),
            "market_cap_usd": candidate["market_cap_usd"] if "market_cap_usd" in candidate else self._unavailable("market_cap_usd"),
        }

        # Return dict matching APlusOpportunity schema
        return {
            "symbol": symbol,
            "name": company_name,
            "grade": grade,
            "composite_score": composite_score,
            "confidence": confidence,
            "risk_score": risk_score,
            "allocation_recommendation": moat_analysis.get("competitive_advantage", "") if isinstance(moat_analysis, dict) else "",
            "replacement_note": candidate.get("implementation", {}).get("entry_strategy", ""),
            "rationale": rationale,
            "key_metrics": key_metrics,
        }
