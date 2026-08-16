"""
Crypto opportunity extractor implementation.

This module implements crypto-specific extraction logic for A+ investment opportunities.
"""

from typing import Any

from finwiz.orchestrators.discovery.extractors.base import OpportunityExtractor


class CryptoOpportunityExtractor(OpportunityExtractor):
    """Extract crypto opportunities with crypto-specific logic."""

    def _should_include(self, candidate: dict[str, Any]) -> bool:
        """
        Crypto-specific inclusion logic.

        Includes cryptocurrencies with:
        - Grade A+ or A
        - Valid symbol and name
        - Market cap >= $10B

        Args:
            candidate: Crypto candidate dictionary

        Returns:
            True if crypto should be included

        """
        grade = candidate.get("grade", "")
        if grade not in ["A+", "A"]:
            return False

        # NewcomerDiscoveryPipeline's writer emits "ticker", not "symbol" --
        # accept either so its payload isn't silently filtered out.
        symbol = candidate.get("symbol") or candidate.get("ticker", "")
        crypto_name = candidate.get("name", "")

        if not (symbol and crypto_name):
            return False

        # Check market cap threshold
        # Try market_cap_usd first, then market_cap (for test data compatibility)
        if "market_cap_usd" in candidate:
            market_cap = candidate["market_cap_usd"]
        elif "market_cap" in candidate:
            market_cap = candidate["market_cap"]
        else:
            # No market-cap signal at all -- e.g. NewcomerDiscoveryPipeline's
            # candidates never carry market_cap_usd/market_cap. Defaulting to a
            # fail-value here would silently exclude every candidate from that
            # source; not having the signal is not the same as having a bad one.
            return True

        return bool(market_cap >= 10_000_000_000)  # $10B minimum

    def _build_opportunity(self, candidate: dict[str, Any], idx: int) -> dict[str, Any] | None:
        """
        Build crypto opportunity object.

        Extracts:
        - Market metrics (market cap, volume)
        - Composite score calculation
        - Technology as rationale
        - Risk assessment

        Args:
            candidate: Crypto candidate dictionary
            idx: Index for ranking

        Returns:
            Crypto opportunity dictionary

        """
        symbol = candidate.get("symbol") or candidate.get("ticker", "")
        crypto_name = candidate.get("name", "")
        grade = candidate.get("grade", "")
        has_market_data = "market_cap_usd" in candidate or "volume_24h_usd" in candidate

        # Use pre-calculated composite score if available, otherwise calculate from
        # market metrics. If neither is available, refuse rather than synthesise a
        # score from absent inputs -- market_cap/volume both 0 does floor at a
        # correctly-low 0.0 here, but that's fabricated agreement, not a genuine
        # "this asset scored zero"; refusing keeps the two indistinguishable cases
        # (no data vs. a real bottom score) from being merged into one value.
        if "composite_score" in candidate:
            composite_score = candidate.get("composite_score", 0.0)
        elif has_market_data:
            market_cap = candidate.get("market_cap_usd", 0)
            volume_24h = candidate.get("volume_24h_usd", 0)
            # Higher market cap and volume = higher score
            market_cap_score = min(market_cap / 100e9, 1.0)  # Normalize to $100B
            volume_score = min(volume_24h / 10e9, 1.0)  # Normalize to $10B daily volume
            composite_score = (market_cap_score * 0.6 + volume_score * 0.4) * 0.9  # Max 0.9 for crypto
        else:
            self._refuse(candidate, idx, "no composite_score and no market data to derive one from")
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

        # Extract market metrics for key metrics. Each field's own absence (not
        # merely a 0 value) means this candidate's source never measured it --
        # distinct from an explicit 0 (measured, genuinely zero).
        market_cap = candidate["market_cap_usd"] if "market_cap_usd" in candidate else None
        volume_24h = candidate["volume_24h_usd"] if "volume_24h_usd" in candidate else None

        # Extract risk assessment, noting when the score is a default rather than
        # a real measurement (same reasoning as confidence, above).
        risk_assessment = candidate.get("risk_assessment") or {}
        risk_provenance = None
        if isinstance(risk_assessment, dict) and "score" in risk_assessment:
            risk_score = risk_assessment["score"]
        else:
            risk_score = 6.0  # Crypto typically higher risk
            risk_provenance = f"Risk score {risk_score} is a default, not measured"

        # Extract technology as rationale using helper method, then append the
        # writer's flat rationale/recommendation so neither is dropped.
        from finwiz.orchestrators.extraction.aplus import APlusDataExtractor

        extractor = APlusDataExtractor()
        technology = candidate.get("technology", {})
        has_technology = "technology" in candidate
        consensus, use_case, rationale = extractor._extract_technology_info(technology)
        rationale = self._passthrough_rationale(candidate, rationale)
        if confidence_provenance:
            rationale.append(confidence_provenance)
        if risk_provenance:
            rationale.append(risk_provenance)

        # Build key metrics. An unmeasured metric is marked unavailable rather
        # than defaulted to 0/"" -- market_cap_usd: 0 reads as a real, tiny
        # (and gate-failing) measurement, not as "unknown".
        key_metrics = {
            "market_cap_usd": market_cap if market_cap is not None else self._unavailable("market_cap_usd"),
            "volume_24h_usd": volume_24h if volume_24h is not None else self._unavailable("volume_24h_usd"),
            "consensus_mechanism": consensus if has_technology else self._unavailable("consensus_mechanism"),
        }

        # Return dict matching APlusOpportunity schema
        return {
            "symbol": symbol.replace("-USD", ""),  # Clean symbol
            "name": crypto_name,
            "grade": grade,
            "composite_score": composite_score,
            "confidence": confidence,
            "risk_score": risk_score,
            "allocation_recommendation": technology.get("competitive_advantage", "") if isinstance(technology, dict) else "",
            "replacement_note": candidate.get("implementation", {}).get("entry_strategy", ""),
            "rationale": rationale,
            "key_metrics": key_metrics,
        }
