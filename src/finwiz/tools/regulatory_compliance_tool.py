"""
Regulatory compliance analysis tool for cryptocurrency investments.

Provides jurisdiction-specific regulatory risk assessment, compliance status analysis,
and regulatory clarity indicators for crypto investments across major markets.
"""

from datetime import datetime
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

from finwiz.schemas.tools import RegulatoryComplianceInput
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class RegulatoryComplianceTool(BaseTool):
    """
    Comprehensive regulatory compliance analysis tool for cryptocurrencies.

    Provides jurisdiction-specific analysis including:
    - Regulatory clarity and status by jurisdiction
    - Compliance requirements and restrictions
    - Risk assessment for regulatory changes
    - Investment suitability by jurisdiction
    - Regulatory trend analysis and outlook
    """

    name: str = "Regulatory Compliance Tool"
    description: str = "Analyze cryptocurrency regulatory compliance across multiple jurisdictions including risk assessment, compliance status, and regulatory clarity indicators."
    args_schema: type[BaseModel] = RegulatoryComplianceInput

    def _run(
        self,
        symbol: str,
        jurisdictions: list[str] | None = None,
        include_risk_assessment: bool = True,
        include_compliance_status: bool = True,
    ) -> dict[str, Any]:
        """Execute comprehensive regulatory compliance analysis."""
        try:
            symbol = symbol.upper().strip()
            if jurisdictions is None:
                jurisdictions = ["US", "EU", "Switzerland", "UK", "Singapore"]

            logger.info(f"Starting regulatory compliance analysis for {symbol} across {len(jurisdictions)} jurisdictions")

            # Get crypto classification
            crypto_classification = self._classify_cryptocurrency(symbol)

            result = {
                "symbol": symbol,
                "crypto_classification": crypto_classification,
                "analysis_timestamp": datetime.now().isoformat(),
                "jurisdictions_analyzed": jurisdictions,
            }

            # Compliance status analysis
            if include_compliance_status:
                result["compliance_status"] = self._analyze_compliance_status(symbol, jurisdictions, crypto_classification)

            # Regulatory risk assessment
            if include_risk_assessment:
                result["regulatory_risk"] = self._assess_regulatory_risk(symbol, jurisdictions, crypto_classification)

            # Overall regulatory summary
            result["regulatory_summary"] = self._generate_regulatory_summary(symbol, result)

            return result

        except Exception as e:
            logger.error(f"Regulatory compliance analysis failed for {symbol}: {e}")
            return {"error": f"Regulatory compliance analysis failed for {symbol}: {e}"}

    def _classify_cryptocurrency(self, symbol: str) -> dict[str, Any]:
        """Classify cryptocurrency for regulatory purposes."""
        try:
            # Cryptocurrency classifications based on regulatory frameworks
            crypto_classifications = {
                "BTC": {
                    "primary_classification": "commodity",
                    "sec_classification": "commodity",
                    "cftc_classification": "commodity",
                    "utility_token": False,
                    "security_token": False,
                    "payment_token": True,
                    "regulatory_clarity": "high",
                },
                "ETH": {
                    "primary_classification": "commodity",
                    "sec_classification": "commodity",
                    "cftc_classification": "commodity",
                    "utility_token": True,
                    "security_token": False,
                    "payment_token": True,
                    "regulatory_clarity": "high",
                },
                "ADA": {
                    "primary_classification": "utility_token",
                    "sec_classification": "unclear",
                    "cftc_classification": "commodity",
                    "utility_token": True,
                    "security_token": False,
                    "payment_token": False,
                    "regulatory_clarity": "medium",
                },
                "SOL": {
                    "primary_classification": "utility_token",
                    "sec_classification": "unclear",
                    "cftc_classification": "commodity",
                    "utility_token": True,
                    "security_token": False,
                    "payment_token": False,
                    "regulatory_clarity": "medium",
                },
                "LINK": {
                    "primary_classification": "utility_token",
                    "sec_classification": "utility",
                    "cftc_classification": "commodity",
                    "utility_token": True,
                    "security_token": False,
                    "payment_token": False,
                    "regulatory_clarity": "medium",
                },
                "UNI": {
                    "primary_classification": "governance_token",
                    "sec_classification": "unclear",
                    "cftc_classification": "commodity",
                    "utility_token": True,
                    "security_token": False,
                    "payment_token": False,
                    "regulatory_clarity": "low",
                },
                "AAVE": {
                    "primary_classification": "governance_token",
                    "sec_classification": "unclear",
                    "cftc_classification": "commodity",
                    "utility_token": True,
                    "security_token": False,
                    "payment_token": False,
                    "regulatory_clarity": "low",
                },
            }

            classification = crypto_classifications.get(
                symbol,
                {
                    "primary_classification": "utility_token",
                    "sec_classification": "unclear",
                    "cftc_classification": "unclear",
                    "utility_token": True,
                    "security_token": False,
                    "payment_token": False,
                    "regulatory_clarity": "low",
                },
            )

            classification["symbol"] = symbol
            return classification

        except Exception as e:
            logger.error(f"Crypto classification failed for {symbol}: {e}")
            return {"error": f"Crypto classification failed: {e}"}

    def _analyze_compliance_status(self, symbol: str, jurisdictions: list[str], classification: dict[str, Any]) -> dict[str, Any]:
        """Analyze compliance status across jurisdictions."""
        try:
            compliance_status = {}

            for jurisdiction in jurisdictions:
                status = self._get_jurisdiction_compliance(symbol, jurisdiction, classification)
                compliance_status[jurisdiction] = status

            return compliance_status

        except Exception as e:
            logger.error(f"Compliance status analysis failed for {symbol}: {e}")
            return {"error": f"Compliance status analysis failed: {e}"}

    def _get_jurisdiction_compliance(self, symbol: str, jurisdiction: str, classification: dict[str, Any]) -> dict[str, Any]:
        """Get compliance status for specific jurisdiction."""
        try:
            jurisdiction_frameworks = {
                "US": self._get_us_compliance(symbol, classification),
                "EU": self._get_eu_compliance(symbol, classification),
                "Switzerland": self._get_switzerland_compliance(symbol, classification),
                "UK": self._get_uk_compliance(symbol, classification),
                "Singapore": self._get_singapore_compliance(symbol, classification),
            }

            return jurisdiction_frameworks.get(
                jurisdiction,
                {
                    "status": "unknown",
                    "regulatory_framework": "unclear",
                    "investment_restrictions": "unknown",
                    "compliance_requirements": [],
                    "regulatory_clarity": "low",
                },
            )

        except Exception as e:
            logger.error(f"Jurisdiction compliance analysis failed for {symbol} in {jurisdiction}: {e}")
            return {"error": f"Jurisdiction compliance failed: {e}"}

    def _get_us_compliance(self, symbol: str, classification: dict[str, Any]) -> dict[str, Any]:
        """Get US regulatory compliance status."""
        primary_class = classification.get("primary_classification", "unknown")
        sec_class = classification.get("sec_classification", "unclear")

        if primary_class == "commodity" and symbol in ["BTC", "ETH"]:
            return {
                "status": "compliant",
                "regulatory_framework": "CFTC commodity regulation",
                "investment_restrictions": "minimal",
                "compliance_requirements": ["AML/KYC for exchanges", "Tax reporting"],
                "regulatory_clarity": "high",
                "notes": "Clear commodity classification by CFTC",
            }
        elif sec_class == "unclear":
            return {
                "status": "uncertain",
                "regulatory_framework": "SEC review pending",
                "investment_restrictions": "potential",
                "compliance_requirements": ["Possible securities registration", "AML/KYC", "Tax reporting"],
                "regulatory_clarity": "low",
                "notes": "SEC classification unclear, potential securities risk",
            }
        else:
            return {
                "status": "compliant",
                "regulatory_framework": "Utility token framework",
                "investment_restrictions": "minimal",
                "compliance_requirements": ["AML/KYC for exchanges", "Tax reporting"],
                "regulatory_clarity": "medium",
                "notes": "Utility token with reasonable regulatory clarity",
            }

    def _get_eu_compliance(self, symbol: str, classification: dict[str, Any]) -> dict[str, Any]:
        """Get EU regulatory compliance status."""
        return {
            "status": "transitioning",
            "regulatory_framework": "MiCA regulation (2024+)",
            "investment_restrictions": "moderate",
            "compliance_requirements": [
                "MiCA compliance for service providers",
                "AML/KYC requirements",
                "Consumer protection measures",
                "Environmental disclosures",
            ],
            "regulatory_clarity": "improving",
            "notes": "MiCA regulation provides clearer framework from 2024",
        }

    def _get_switzerland_compliance(self, symbol: str, classification: dict[str, Any]) -> dict[str, Any]:
        """Get Switzerland regulatory compliance status."""
        return {
            "status": "compliant",
            "regulatory_framework": "FINMA crypto-friendly regulation",
            "investment_restrictions": "minimal",
            "compliance_requirements": [
                "FINMA licensing for service providers",
                "AML/KYC requirements",
                "Tax reporting",
            ],
            "regulatory_clarity": "high",
            "notes": "Switzerland has crypto-friendly regulatory environment",
        }

    def _get_uk_compliance(self, symbol: str, classification: dict[str, Any]) -> dict[str, Any]:
        """Get UK regulatory compliance status."""
        return {
            "status": "evolving",
            "regulatory_framework": "FCA crypto regulation development",
            "investment_restrictions": "moderate",
            "compliance_requirements": [
                "FCA registration for crypto businesses",
                "AML/KYC requirements",
                "Consumer warnings compliance",
            ],
            "regulatory_clarity": "medium",
            "notes": "UK developing comprehensive crypto regulation framework",
        }

    def _get_singapore_compliance(self, symbol: str, classification: dict[str, Any]) -> dict[str, Any]:
        """Get Singapore regulatory compliance status."""
        return {
            "status": "compliant",
            "regulatory_framework": "MAS crypto services regulation",
            "investment_restrictions": "moderate",
            "compliance_requirements": [
                "MAS licensing for service providers",
                "AML/KYC requirements",
                "Retail investor protections",
            ],
            "regulatory_clarity": "high",
            "notes": "Singapore has clear regulatory framework for crypto services",
        }

    def _assess_regulatory_risk(self, symbol: str, jurisdictions: list[str], classification: dict[str, Any]) -> dict[str, Any]:
        """Assess regulatory risk across jurisdictions."""
        try:
            risk_factors = []
            risk_score = 2.0  # Base regulatory risk

            # Classification-based risk
            primary_class = classification.get("primary_classification", "unknown")
            regulatory_clarity = classification.get("regulatory_clarity", "low")

            if regulatory_clarity == "low":
                risk_factors.append("Low regulatory clarity increases compliance uncertainty")
                risk_score += 1.0
            elif regulatory_clarity == "medium":
                risk_factors.append("Moderate regulatory clarity with some uncertainty")
                risk_score += 0.5

            if primary_class == "governance_token":
                risk_factors.append("Governance tokens face higher securities regulation risk")
                risk_score += 0.8
            elif primary_class == "utility_token":
                risk_factors.append("Utility token classification may face regulatory scrutiny")
                risk_score += 0.4

            # Jurisdiction-specific risks
            high_risk_jurisdictions = ["US", "EU"]
            for jurisdiction in jurisdictions:
                if jurisdiction in high_risk_jurisdictions:
                    risk_factors.append(f"{jurisdiction} regulatory changes could impact accessibility")
                    risk_score += 0.3

            # General regulatory risks
            risk_factors.extend(
                [
                    "Evolving regulatory landscape creates ongoing compliance risk",
                    "Potential for sudden regulatory changes or restrictions",
                    "Cross-border regulatory coordination may increase restrictions",
                    "Tax treatment changes could impact investment returns",
                ]
            )
            risk_score += 0.5

            # DeFi-specific risks for governance tokens
            if symbol in ["UNI", "AAVE", "COMP", "MKR"]:
                risk_factors.append("DeFi governance tokens face additional regulatory scrutiny")
                risk_score += 0.4

            final_score = min(risk_score, 5.0)

            return {
                "symbol": symbol,
                "risk_score": round(final_score, 1),
                "risk_level": self._map_risk_score_to_level(final_score),
                "risk_factors": risk_factors,
                "jurisdictions_analyzed": jurisdictions,
                "assessment_date": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Regulatory risk assessment failed for {symbol}: {e}")
            return {"error": f"Regulatory risk assessment failed: {e}"}

    def _generate_regulatory_summary(self, symbol: str, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """Generate overall regulatory summary."""
        try:
            compliance_status = analysis_result.get("compliance_status", {})
            regulatory_risk = analysis_result.get("regulatory_risk", {})

            # Count compliant jurisdictions
            compliant_count = sum(1 for status in compliance_status.values() if status.get("status") == "compliant")
            total_jurisdictions = len(compliance_status)

            # Overall assessment
            if compliant_count >= total_jurisdictions * 0.8:
                overall_status = "favorable"
            elif compliant_count >= total_jurisdictions * 0.5:
                overall_status = "mixed"
            else:
                overall_status = "challenging"

            # Investment suitability
            risk_level = regulatory_risk.get("risk_level", "High")
            if risk_level in ["Low", "Medium"] and overall_status == "favorable":
                investment_suitability = "suitable"
            elif risk_level == "Medium" and overall_status in ["favorable", "mixed"]:
                investment_suitability = "moderate"
            else:
                investment_suitability = "high_risk"

            return {
                "overall_status": overall_status,
                "compliant_jurisdictions": compliant_count,
                "total_jurisdictions": total_jurisdictions,
                "investment_suitability": investment_suitability,
                "key_risks": regulatory_risk.get("risk_factors", [])[:3],  # Top 3 risks
                "recommendations": self._generate_recommendations(symbol, overall_status, investment_suitability),
            }

        except Exception as e:
            logger.error(f"Regulatory summary generation failed for {symbol}: {e}")
            return {"error": f"Regulatory summary generation failed: {e}"}

    def _generate_recommendations(self, symbol: str, overall_status: str, investment_suitability: str) -> list[str]:
        """Generate regulatory compliance recommendations."""
        recommendations = []

        if investment_suitability == "suitable":
            recommendations.extend(
                [
                    "Regulatory environment is favorable for investment",
                    "Monitor ongoing regulatory developments",
                    "Ensure compliance with local tax reporting requirements",
                ]
            )
        elif investment_suitability == "moderate":
            recommendations.extend(
                [
                    "Proceed with caution due to regulatory uncertainties",
                    "Consider smaller position size due to regulatory risk",
                    "Stay informed about regulatory developments in key jurisdictions",
                ]
            )
        else:
            recommendations.extend(
                [
                    "High regulatory risk - consider avoiding or minimal exposure",
                    "Wait for greater regulatory clarity before significant investment",
                    "Monitor regulatory developments closely before investing",
                ]
            )

        # Symbol-specific recommendations
        if symbol in ["UNI", "AAVE", "COMP"]:
            recommendations.append("DeFi governance tokens face elevated regulatory scrutiny")

        return recommendations

    def _map_risk_score_to_level(self, score: float) -> str:
        """Map numerical risk score to risk level."""
        if score <= 2.0:
            return "Low"
        elif score <= 3.0:
            return "Medium"
        elif score <= 4.0:
            return "High"
        else:
            return "Very High"
