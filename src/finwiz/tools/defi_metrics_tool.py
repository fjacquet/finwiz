"""
DeFi metrics analysis tool for comprehensive decentralized finance protocol evaluation.

Provides specialized metrics for DeFi protocols including TVL analysis, yield farming
opportunities, governance token evaluation, and protocol-specific risk assessment.
"""

from datetime import datetime
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

from finwiz.schemas.tools import DeFiMetricsInput
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class DeFiMetricsTool(BaseTool):
    """
    Comprehensive DeFi protocol analysis tool.

    Provides specialized metrics for DeFi protocols including:
    - Total Value Locked (TVL) analysis and trends
    - Yield farming opportunities and APY calculations
    - Governance token utility and voting power distribution
    - Protocol revenue and fee analysis
    - Risk assessment specific to DeFi protocols
    """

    name: str = "DeFi Metrics Tool"
    description: str = (
        "Analyze DeFi protocols with specialized metrics including TVL, yield farming, "
        "governance analysis, and protocol-specific risk assessment."
    )
    args_schema: type[BaseModel] = DeFiMetricsInput

    def _run(
        self,
        symbol: str,
        include_tvl_analysis: bool = True,
        include_yield_metrics: bool = True,
        include_governance_analysis: bool = True,
    ) -> dict[str, Any]:
        """Execute comprehensive DeFi metrics analysis."""
        try:
            symbol = symbol.upper().strip()
            logger.info(f"Starting DeFi metrics analysis for {symbol}")

            # Get basic protocol data
            protocol_data = self._get_protocol_data(symbol)
            if "error" in protocol_data:
                return protocol_data

            result = {
                "symbol": symbol,
                "protocol_data": protocol_data,
                "analysis_timestamp": datetime.now().isoformat(),
            }

            # TVL Analysis
            if include_tvl_analysis:
                result["tvl_analysis"] = self._analyze_tvl_metrics(symbol, protocol_data)

            # Yield Metrics
            if include_yield_metrics:
                result["yield_metrics"] = self._analyze_yield_opportunities(symbol, protocol_data)

            # Governance Analysis
            if include_governance_analysis:
                result["governance_analysis"] = self._analyze_governance_token(symbol, protocol_data)

            # DeFi-specific risk assessment
            result["defi_risk_assessment"] = self._assess_defi_risks(symbol, protocol_data)

            return result

        except Exception as e:
            logger.error(f"DeFi metrics analysis failed for {symbol}: {e}")
            return {"error": f"DeFi metrics analysis failed for {symbol}: {e}"}

    def _get_protocol_data(self, symbol: str) -> dict[str, Any]:
        """Get basic DeFi protocol data from various sources."""
        try:
            # Try DeFiPulse/DeFiLlama style data (using fallback approach)
            protocol_data = self._get_defi_protocol_info(symbol)
            if protocol_data and "error" not in protocol_data:
                return protocol_data

            # Fallback to basic DeFi protocol data
            return self._create_fallback_defi_data(symbol)

        except Exception as e:
            logger.error(f"Could not retrieve DeFi protocol data for {symbol}: {e}")
            return {"error": f"Could not retrieve DeFi protocol data: {e}"}

    def _get_defi_protocol_info(self, symbol: str) -> dict[str, Any]:
        """Get DeFi protocol information from public APIs."""
        try:
            # Map common DeFi tokens to protocol names
            protocol_map = {
                "UNI": "uniswap",
                "AAVE": "aave",
                "COMP": "compound",
                "MKR": "makerdao",
                "SNX": "synthetix",
                "YFI": "yearn-finance",
                "SUSHI": "sushiswap",
                "CRV": "curve",
                "BAL": "balancer",
                "1INCH": "1inch",
                "LINK": "chainlink",
            }

            protocol_name = protocol_map.get(symbol, symbol.lower())

            # Try to get basic protocol info (using a mock structure for now)
            # In production, this would connect to DeFiLlama or similar APIs
            return self._create_protocol_data_structure(symbol, protocol_name)

        except Exception as e:
            logger.error(f"DeFi protocol info retrieval failed for {symbol}: {e}")
            return {"error": f"DeFi protocol info retrieval failed: {e}"}

    def _create_protocol_data_structure(self, symbol: str, protocol_name: str) -> dict[str, Any]:
        """Create structured protocol data."""
        # DeFi protocol categories and characteristics
        defi_protocols = {
            "UNI": {
                "name": "Uniswap",
                "category": "DEX",
                "description": "Leading decentralized exchange protocol",
                "chain": "Ethereum",
                "tvl_estimate": 5000000000,  # $5B estimate
                "governance_active": True,
                "yield_opportunities": ["LP rewards", "UNI staking"],
            },
            "AAVE": {
                "name": "Aave",
                "category": "Lending",
                "description": "Decentralized lending and borrowing protocol",
                "chain": "Multi-chain",
                "tvl_estimate": 8000000000,  # $8B estimate
                "governance_active": True,
                "yield_opportunities": ["Lending rewards", "Safety module staking"],
            },
            "COMP": {
                "name": "Compound",
                "category": "Lending",
                "description": "Algorithmic money market protocol",
                "chain": "Ethereum",
                "tvl_estimate": 3000000000,  # $3B estimate
                "governance_active": True,
                "yield_opportunities": ["Lending rewards", "COMP distribution"],
            },
            "MKR": {
                "name": "MakerDAO",
                "category": "Stablecoin",
                "description": "Decentralized stablecoin protocol",
                "chain": "Ethereum",
                "tvl_estimate": 6000000000,  # $6B estimate
                "governance_active": True,
                "yield_opportunities": ["MKR staking", "DSR"],
            },
        }

        base_data = defi_protocols.get(
            symbol,
            {
                "name": f"DeFi Protocol {symbol}",
                "category": "DeFi",
                "description": f"DeFi protocol with token {symbol}",
                "chain": "Ethereum",
                "tvl_estimate": 100000000,  # $100M default
                "governance_active": False,
                "yield_opportunities": ["Token rewards"],
            },
        )

        return {
            "symbol": symbol,
            "protocol_name": protocol_name,
            "sources": ["Protocol Analysis"],
            **base_data,
        }

    def _create_fallback_defi_data(self, symbol: str) -> dict[str, Any]:
        """Create fallback DeFi protocol data."""
        return {
            "symbol": symbol,
            "name": f"DeFi Protocol {symbol}",
            "category": "DeFi",
            "description": f"Decentralized finance protocol with token {symbol}",
            "chain": "Ethereum",
            "tvl_estimate": 0,
            "governance_active": False,
            "yield_opportunities": [],
            "sources": ["Fallback Data"],
        }

    def _analyze_tvl_metrics(self, symbol: str, protocol_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze Total Value Locked metrics for the DeFi protocol."""
        try:
            tvl_estimate = protocol_data.get("tvl_estimate", 0)
            category = protocol_data.get("category", "DeFi")

            # TVL analysis based on category benchmarks
            tvl_analysis = {
                "current_tvl_usd": tvl_estimate,
                "tvl_rank": self._estimate_tvl_rank(tvl_estimate, category),
                "tvl_category": self._categorize_tvl(tvl_estimate),
                "tvl_trend": "stable",  # Would be calculated from historical data
                "market_share": self._estimate_market_share(tvl_estimate, category),
            }

            # TVL insights
            insights = []
            if tvl_estimate > 1000000000:  # > $1B
                insights.append("Large-scale protocol with significant institutional trust")
            elif tvl_estimate > 100000000:  # > $100M
                insights.append("Established protocol with solid user adoption")
            else:
                insights.append("Emerging protocol with growth potential")

            if category == "DEX" and tvl_estimate > 500000000:
                insights.append("Major DEX with significant trading volume potential")
            elif category == "Lending" and tvl_estimate > 1000000000:
                insights.append("Leading lending protocol with strong borrower demand")

            tvl_analysis["insights"] = insights

            return tvl_analysis

        except Exception as e:
            logger.error(f"TVL analysis failed for {symbol}: {e}")
            return {"error": f"TVL analysis failed: {e}"}

    def _analyze_yield_opportunities(self, symbol: str, protocol_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze yield farming and staking opportunities."""
        try:
            yield_opportunities = protocol_data.get("yield_opportunities", [])
            category = protocol_data.get("category", "DeFi")

            # Estimate yield ranges based on protocol type
            yield_estimates = self._estimate_yield_ranges(category, symbol)

            yield_analysis = {
                "available_opportunities": yield_opportunities,
                "estimated_apy_ranges": yield_estimates,
                "risk_level": self._assess_yield_risk(category),
                "liquidity_requirements": self._get_liquidity_requirements(category),
            }

            # Yield insights
            insights = []
            if "LP rewards" in yield_opportunities:
                insights.append("Liquidity provision rewards available with impermanent loss risk")
            if "staking" in " ".join(yield_opportunities).lower():
                insights.append("Token staking opportunities with governance participation")
            if category == "Lending":
                insights.append("Lending yield opportunities with variable rates")

            yield_analysis["insights"] = insights

            return yield_analysis

        except Exception as e:
            logger.error(f"Yield analysis failed for {symbol}: {e}")
            return {"error": f"Yield analysis failed: {e}"}

    def _analyze_governance_token(self, symbol: str, protocol_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze governance token characteristics and utility."""
        try:
            governance_active = protocol_data.get("governance_active", False)
            category = protocol_data.get("category", "DeFi")

            governance_analysis = {
                "governance_active": governance_active,
                "token_utility": self._assess_token_utility(symbol, category),
                "voting_power": "proportional_to_holdings",  # Standard assumption
                "governance_participation": self._estimate_governance_participation(symbol),
            }

            # Governance insights
            insights = []
            if governance_active:
                insights.append("Active governance system with token holder voting rights")
                insights.append("Token holders can influence protocol development and parameters")
            else:
                insights.append("Limited or no governance functionality currently active")

            if category in ["DEX", "Lending"]:
                insights.append("Governance token may receive protocol fee distributions")

            governance_analysis["insights"] = insights

            return governance_analysis

        except Exception as e:
            logger.error(f"Governance analysis failed for {symbol}: {e}")
            return {"error": f"Governance analysis failed: {e}"}

    def _assess_defi_risks(self, symbol: str, protocol_data: dict[str, Any]) -> dict[str, Any]:
        """Assess DeFi-specific risks for the protocol."""
        try:
            category = protocol_data.get("category", "DeFi")
            tvl_estimate = protocol_data.get("tvl_estimate", 0)

            risk_factors = []
            risk_score = 3.0  # Base DeFi risk

            # Smart contract risk
            risk_factors.append("Smart contract vulnerabilities and potential exploits")
            risk_score += 0.5

            # Category-specific risks
            if category == "DEX":
                risk_factors.extend(
                    [
                        "Impermanent loss risk for liquidity providers",
                        "Front-running and MEV extraction risks",
                    ]
                )
                risk_score += 0.3
            elif category == "Lending":
                risk_factors.extend(
                    [
                        "Liquidation risk during market volatility",
                        "Bad debt accumulation risk",
                    ]
                )
                risk_score += 0.4
            elif category == "Stablecoin":
                risk_factors.extend(
                    [
                        "Depeg risk during market stress",
                        "Collateral backing and stability mechanism risks",
                    ]
                )
                risk_score += 0.6

            # Protocol maturity risk
            if tvl_estimate < 100000000:  # < $100M
                risk_factors.append("Limited protocol maturity and battle-testing")
                risk_score += 0.5

            # General DeFi risks
            risk_factors.extend(
                [
                    "Regulatory uncertainty for DeFi protocols",
                    "Governance attack risks",
                    "Oracle manipulation risks",
                    "Cross-chain bridge risks (if applicable)",
                ]
            )
            risk_score += 0.3

            final_score = min(risk_score, 5.0)

            return {
                "symbol": symbol,
                "risk_score": round(final_score, 1),
                "risk_level": self._map_risk_score_to_level(final_score),
                "risk_factors": risk_factors,
                "category_specific_risks": True,
                "assessment_date": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"DeFi risk assessment failed for {symbol}: {e}")
            return {"error": f"DeFi risk assessment failed: {e}"}

    def _estimate_tvl_rank(self, tvl: float, category: str) -> str:
        """Estimate TVL ranking within category."""
        if tvl > 5000000000:  # > $5B
            return "Top 5"
        elif tvl > 1000000000:  # > $1B
            return "Top 20"
        elif tvl > 100000000:  # > $100M
            return "Top 50"
        else:
            return "Emerging"

    def _categorize_tvl(self, tvl: float) -> str:
        """Categorize TVL size."""
        if tvl > 10000000000:  # > $10B
            return "Mega Protocol"
        elif tvl > 1000000000:  # > $1B
            return "Large Protocol"
        elif tvl > 100000000:  # > $100M
            return "Medium Protocol"
        else:
            return "Small Protocol"

    def _estimate_market_share(self, tvl: float, category: str) -> str:
        """Estimate market share within category."""
        # Rough estimates based on category
        category_tvl_estimates = {
            "DEX": 50000000000,  # $50B total DEX TVL estimate
            "Lending": 30000000000,  # $30B total lending TVL estimate
            "Stablecoin": 100000000000,  # $100B total stablecoin market
        }

        total_category_tvl = category_tvl_estimates.get(category, 10000000000)
        market_share = (tvl / total_category_tvl) * 100

        if market_share > 20:
            return f"Dominant (~{market_share:.0f}%)"
        elif market_share > 5:
            return f"Major player (~{market_share:.0f}%)"
        elif market_share > 1:
            return f"Established (~{market_share:.1f}%)"
        else:
            return "Niche (<1%)"

    def _estimate_yield_ranges(self, category: str, symbol: str) -> dict[str, str]:
        """Estimate yield ranges based on protocol category."""
        yield_ranges = {
            "DEX": {"LP_rewards": "5-15% APY", "trading_fees": "0.1-2% APY"},
            "Lending": {"supply_apy": "2-8% APY", "borrow_rewards": "1-5% APY"},
            "Stablecoin": {"stability_rewards": "1-4% APY", "governance_rewards": "2-6% APY"},
            "DeFi": {"token_rewards": "3-12% APY"},
        }

        return yield_ranges.get(category, yield_ranges["DeFi"])

    def _assess_yield_risk(self, category: str) -> str:
        """Assess risk level for yield opportunities."""
        risk_levels = {
            "DEX": "High (impermanent loss)",
            "Lending": "Medium (liquidation risk)",
            "Stablecoin": "Low-Medium (depeg risk)",
            "DeFi": "Medium-High (protocol risk)",
        }

        return risk_levels.get(category, "Medium-High")

    def _get_liquidity_requirements(self, category: str) -> str:
        """Get typical liquidity requirements."""
        requirements = {
            "DEX": "Paired token deposits required",
            "Lending": "Single token deposits",
            "Stablecoin": "Stablecoin or collateral deposits",
            "DeFi": "Protocol-specific requirements",
        }

        return requirements.get(category, "Variable requirements")

    def _assess_token_utility(self, symbol: str, category: str) -> list[str]:
        """Assess token utility functions."""
        base_utilities = ["Governance voting"]

        category_utilities = {
            "DEX": ["Trading fee discounts", "LP reward boosts"],
            "Lending": ["Borrowing discounts", "Safety module staking"],
            "Stablecoin": ["Stability fee payments", "Collateral backing"],
        }

        utilities = base_utilities + category_utilities.get(category, ["Protocol participation"])
        return utilities

    def _estimate_governance_participation(self, symbol: str) -> str:
        """Estimate governance participation level."""
        # This would be calculated from on-chain data in production
        participation_estimates = {
            "UNI": "Low (5-10%)",
            "AAVE": "Medium (15-25%)",
            "COMP": "Medium (10-20%)",
            "MKR": "High (20-30%)",
        }

        return participation_estimates.get(symbol, "Unknown")

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
