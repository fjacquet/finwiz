"""
Enhanced crypto analysis tool for investment thesis generation and risk assessment.

Provides comprehensive crypto analysis with investment thesis generation,
standardized risk assessment on 1-10 scale, and structured output for FinWiz crews.
Enhanced with optional Perplexity Sonar integration for recent regulatory updates and adoption news.
"""

import asyncio
from datetime import datetime
from typing import Any

import requests
from crewai.tools import BaseTool
from crewai_custom_tools import EnhancedCryptoAnalysisTool as CentralEnhancedCryptoAnalysisTool
from crewai_custom_tools.core.results import parse_tool_result
from pydantic import BaseModel

from finwiz.config.endpoints import COINGECKO_BASE
from finwiz.config.features.flags import get_feature_flags
from finwiz.schemas.perplexity import SonarArticle
from finwiz.schemas.tools import (
    EnhancedCryptoAnalysisInput,
)
from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration

logger = get_logger(__name__)

# Symbol -> CoinGecko coin id, for the minimal supplemental volume fetch
# (kept in sync with the mapping crewai_custom_tools' EnhancedCryptoAnalysisTool
# uses internally, since central does not expose the resolved coin id).
_COINGECKO_SYMBOL_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "ADA": "cardano",
    "DOT": "polkadot",
    "SOL": "solana",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
    "LINK": "chainlink",
}


class EnhancedCryptoAnalysisTool(BaseTool):
    """
    Enhanced crypto analysis tool with comprehensive thesis generation.

    Provides detailed crypto analysis including:
    - Investment thesis generation with structured bullets
    - Standardized risk assessment on 1-10 scale (mapped to 0-5 internally)
    - Market dynamics analysis and tokenomics evaluation
    - Structured output for downstream processing
    - Optional Perplexity Sonar integration for recent regulatory updates and adoption news
    """

    name: str = "Enhanced Crypto Analysis Tool"
    description: str = (
        "Comprehensive crypto analysis tool that generates investment thesis, "
        "performs standardized risk assessment, and analyzes market dynamics. "
        "Optionally enhanced with Perplexity Sonar for recent regulatory updates and adoption news."
    )
    args_schema: type[BaseModel] = EnhancedCryptoAnalysisInput

    def model_post_init(self, __context: object) -> None:
        """Wire up the centralized crypto analysis tool used for the data fetch."""
        super().model_post_init(__context)
        self._central = CentralEnhancedCryptoAnalysisTool()

    def _get_perplexity_integration(self) -> PerplexityAnalysisIntegration | None:
        """Get Perplexity integration instance if enabled."""
        feature_flags = get_feature_flags()

        # Check feature flag status and log for debugging
        is_enabled = feature_flags.is_enabled("perplexity_research")
        fallback_strategy = feature_flags.get_fallback_strategy("perplexity_research").value

        from finwiz.tools.perplexity_analysis_integration import PerplexityOperationLogger

        PerplexityOperationLogger.log_feature_flag_status("crypto_analysis", is_enabled, fallback_strategy)

        if not is_enabled:
            return None

        try:
            integration = PerplexityAnalysisIntegration()
            if integration.is_available:
                logger.debug("Perplexity Sonar integration available for crypto analysis")
                return integration
            else:
                logger.warning("Perplexity integration initialized but API key not available")
                return None
        except Exception as e:
            logger.error(f"Failed to initialize Perplexity integration: {e!s}")
            return None

    def _run(
        self,
        symbol: str,
        include_thesis: bool = True,
        include_risk_assessment: bool = True,
        max_thesis_bullets: int = 10,
        include_perplexity: bool = True,
    ) -> dict[str, Any]:
        """Execute enhanced crypto analysis."""
        try:
            logger.info(f"Starting enhanced crypto analysis for {symbol}")

            # Normalize symbol
            symbol = symbol.upper().strip()

            # Get basic crypto data
            crypto_data = self._get_crypto_data(symbol, max_thesis_bullets)
            if "error" in crypto_data:
                return crypto_data

            # Generate investment thesis if requested
            thesis = None
            if include_thesis:
                thesis = self._generate_investment_thesis(symbol, crypto_data, max_thesis_bullets)

            # Perform risk assessment if requested
            risk_assessment = None
            if include_risk_assessment:
                risk_assessment = self._perform_crypto_risk_assessment(symbol, crypto_data)

            # Optionally get Perplexity crypto insights
            perplexity_insights = []
            if include_perplexity:
                perplexity_integration = self._get_perplexity_integration()
                if perplexity_integration:
                    perplexity_insights = asyncio.run(self._get_perplexity_crypto_insights(symbol))

            return {
                "symbol": symbol,
                "crypto_data": crypto_data,
                "investment_thesis": thesis,
                "risk_assessment": risk_assessment,
                "perplexity_insights": perplexity_insights,
                "analysis_timestamp": datetime.now().isoformat(),
                "data_sources": crypto_data.get("sources", []),
            }

        except Exception as e:
            logger.error(f"Enhanced crypto analysis failed for {symbol}: {e!s}")
            return {"error": f"Enhanced crypto analysis failed for {symbol}: {e}"}

    def _get_crypto_data(self, symbol: str, max_thesis_bullets: int = 10) -> dict[str, Any]:
        """Get basic cryptocurrency data via the centralized EnhancedCryptoAnalysisTool.

        Delegates the primary CoinGecko fetch to `crewai_custom_tools`'
        `EnhancedCryptoAnalysisTool`, which provides its own rate limiting. On
        any failure (invalid symbol, network error, rate limit) this falls back
        to `_create_fallback_crypto_data`, matching the tool's prior behavior of
        never surfacing a bare fetch error from this method.
        """
        try:
            central_result = parse_tool_result(self._central._run(symbol=symbol, max_thesis_bullets=max_thesis_bullets))
        except Exception as e:
            logger.warning(f"Central crypto data fetch failed for {symbol}: {e}")
            return self._create_fallback_crypto_data(symbol)

        central_crypto_data = central_result.get("crypto_data") if isinstance(central_result, dict) else None
        if not central_crypto_data:
            return self._create_fallback_crypto_data(symbol)

        return self._map_central_crypto_data(symbol, central_crypto_data)

    def _map_central_crypto_data(self, symbol: str, central_crypto_data: dict[str, Any]) -> dict[str, Any]:
        """Map central's crypto_data payload onto the shape expected downstream.

        Consumers are this tool's own thesis/risk generators plus
        deep_analysis_data_collector.py and portfolio_price_service.py.

        Key-mapping table (full version in the task report):
          - current_price_usd -> current_price
          - market_cap_usd    -> market_cap
          - circulating_supply, total_supply, max_supply, market_cap_rank,
            price_change_24h/7d/30d, categories: same names, passed through.
          - total_volume / volume_24h: NOT present in central's payload at all;
            backfilled via `_fetch_volume_24h`, a minimal direct CoinGecko call
            (the one field central's EnhancedCryptoAnalysisTool does not fetch).
          - description, homepage, ath, atl: NOT present in central's payload;
            left absent. finwiz's thesis/risk generators already `.get(key, default)`
            these, so they degrade gracefully (fewer text-based thesis/risk
            matches) rather than crashing — see report for the behavior note.
        """
        volume_24h = self._fetch_volume_24h(symbol)

        return {
            "symbol": central_crypto_data.get("symbol", symbol),
            "name": central_crypto_data.get("name", symbol),
            "current_price": central_crypto_data.get("current_price_usd", 0),
            "market_cap": central_crypto_data.get("market_cap_usd", 0),
            "market_cap_rank": central_crypto_data.get("market_cap_rank", 999),
            "total_volume": volume_24h,
            "volume_24h": volume_24h,
            "price_change_24h": central_crypto_data.get("price_change_24h", 0),
            "price_change_7d": central_crypto_data.get("price_change_7d", 0),
            "price_change_30d": central_crypto_data.get("price_change_30d", 0),
            "circulating_supply": central_crypto_data.get("circulating_supply", 0),
            "total_supply": central_crypto_data.get("total_supply", 0),
            "max_supply": central_crypto_data.get("max_supply"),
            "categories": central_crypto_data.get("categories", []),
            "sources": ["CoinGecko (via crewai_custom_tools)"],
        }

    def _fetch_volume_24h(self, symbol: str) -> float:
        """Minimal direct CoinGecko call for 24h trading volume.

        This is the one field required by downstream consumers
        (`total_volume`/`volume_24h`) that central's `EnhancedCryptoAnalysisTool`
        payload does not provide. Failures here degrade to 0.0 rather than
        discarding the otherwise-successful central data.
        """
        try:
            coin_id = _COINGECKO_SYMBOL_MAP.get(symbol, symbol.lower())
            url = f"{COINGECKO_BASE}/coins/{coin_id}"
            response = requests.get(url, headers={"Accept": "application/json"}, timeout=15)

            if response.status_code != 200:
                return 0.0

            market_data = response.json().get("market_data", {})
            return market_data.get("total_volume", {}).get("usd", 0.0) or 0.0

        except Exception as e:
            logger.warning(f"Supplemental CoinGecko volume fetch failed for {symbol}: {e}")
            return 0.0

    def _create_fallback_crypto_data(self, symbol: str) -> dict[str, Any]:
        """Create fallback crypto data structure."""
        # Basic data for common cryptocurrencies
        fallback_data = {
            "BTC": {
                "name": "Bitcoin",
                "description": "The first and largest cryptocurrency by market capitalization",
                "categories": ["Store of Value", "Digital Gold"],
                "market_cap_rank": 1,
            },
            "ETH": {
                "name": "Ethereum",
                "description": "Smart contract platform and second-largest cryptocurrency",
                "categories": ["Smart Contract Platform", "DeFi"],
                "market_cap_rank": 2,
            },
            "ADA": {
                "name": "Cardano",
                "description": "Proof-of-stake blockchain platform focused on sustainability",
                "categories": ["Smart Contract Platform", "Proof of Stake"],
                "market_cap_rank": 10,
            },
        }

        base_data = fallback_data.get(
            symbol,
            {
                "name": f"Cryptocurrency {symbol}",
                "description": f"Cryptocurrency with symbol {symbol}",
                "categories": ["Cryptocurrency"],
                "market_cap_rank": 100,
            },
        )

        return {
            "symbol": symbol,
            "current_price": 0,
            "market_cap": 0,
            "total_volume": 0,
            "price_change_24h": 0,
            "price_change_7d": 0,
            "price_change_30d": 0,
            "circulating_supply": 0,
            "sources": ["Fallback Data"],
            **base_data,
        }

    def _generate_investment_thesis(self, symbol: str, crypto_data: dict[str, Any], max_bullets: int) -> dict[str, Any]:
        """Generate structured investment thesis for the cryptocurrency."""
        try:
            thesis_bullets = []
            references = []

            # Generate thesis bullets based on crypto characteristics
            name = crypto_data.get("name", symbol)
            categories = crypto_data.get("categories", [])
            market_cap_rank = crypto_data.get("market_cap_rank", 999)
            description = crypto_data.get("description", "")

            # Market position thesis
            if market_cap_rank <= 10:
                thesis_bullets.append(f"{name} is a top-10 cryptocurrency by market capitalization, indicating strong market acceptance and liquidity")
            elif market_cap_rank <= 50:
                thesis_bullets.append(f"{name} maintains a solid market position in the top 50 cryptocurrencies with established market presence")
            else:
                thesis_bullets.append(f"{name} represents an emerging opportunity with potential for significant growth from current market position")

            # Technology and use case thesis
            if "Smart Contract Platform" in categories or "smart contract" in description.lower():
                thesis_bullets.append("Strong technological foundation with smart contract capabilities enabling diverse DeFi and dApp ecosystems")

            if "DeFi" in categories or "defi" in description.lower():
                thesis_bullets.append("Positioned to benefit from the growing decentralized finance (DeFi) sector and yield farming opportunities")

            if "Store of Value" in categories or symbol == "BTC":
                thesis_bullets.append("Serves as a digital store of value and hedge against traditional financial system risks")

            if "Proof of Stake" in categories or "proof-of-stake" in description.lower():
                thesis_bullets.append("Energy-efficient proof-of-stake consensus mechanism aligns with ESG investment criteria")

            # Supply dynamics thesis
            max_supply = crypto_data.get("max_supply")
            if max_supply:
                thesis_bullets.append(f"Fixed maximum supply of {max_supply:,.0f} tokens creates scarcity value and potential deflationary pressure")
            elif symbol == "BTC":
                thesis_bullets.append("Capped supply of 21 million BTC creates digital scarcity similar to precious metals")

            # Performance and momentum thesis
            price_change_7d = crypto_data.get("price_change_7d", 0)
            price_change_30d = crypto_data.get("price_change_30d", 0)

            if price_change_7d > 10:
                thesis_bullets.append("Strong recent price momentum indicates positive market sentiment and potential trend continuation")
            elif price_change_30d > 20:
                thesis_bullets.append("Significant monthly gains demonstrate strong fundamental support and investor confidence")

            # Adoption and ecosystem thesis
            if symbol in ["BTC", "ETH"]:
                thesis_bullets.append("Widespread institutional adoption and integration into traditional financial products")

            if "Layer 1" in categories or symbol in ["ETH", "ADA", "SOL", "AVAX"]:
                thesis_bullets.append("Layer 1 blockchain infrastructure benefits from network effects and developer ecosystem growth")

            # Add generic thesis bullets if needed
            while len(thesis_bullets) < max_bullets:
                generic_bullets = [
                    f"{name} benefits from increasing cryptocurrency mainstream adoption and regulatory clarity",
                    "Potential for significant returns as cryptocurrency market matures and institutional adoption increases",
                    "Diversification benefits within a cryptocurrency portfolio due to unique technological approach",
                    "Strong community support and active development team driving continuous innovation",
                    "Positioned to benefit from macroeconomic trends favoring alternative assets",
                ]

                for bullet in generic_bullets:
                    if bullet not in thesis_bullets and len(thesis_bullets) < max_bullets:
                        thesis_bullets.append(bullet)
                break

            # Add reference URLs
            homepage = crypto_data.get("homepage", [])
            if homepage and isinstance(homepage, list) and len(homepage) > 0:
                references.append(homepage[0])

            # Add CoinGecko reference if available
            if "CoinGecko" in crypto_data.get("sources", []):
                references.append(f"https://www.coingecko.com/en/coins/{symbol.lower()}")

            return {
                "schema_version": 1,
                "symbol": symbol,
                "thesis_bullets": thesis_bullets[:max_bullets],
                "references": references,
            }

        except Exception as e:
            # Return minimal thesis on error
            return {
                "schema_version": 1,
                "symbol": symbol,
                "thesis_bullets": [
                    f"{symbol} represents a cryptocurrency investment opportunity",
                    "Potential for growth in the expanding digital asset market",
                    "Diversification benefits within a crypto portfolio",
                ],
                "references": [],
                "error": f"Thesis generation error: {e}",
            }

    def _perform_crypto_risk_assessment(self, symbol: str, crypto_data: dict[str, Any]) -> dict[str, Any]:
        """Perform standardized risk assessment for cryptocurrency."""
        try:
            risk_factors = []
            base_score = 2.0  # Start with medium risk for crypto

            # Market cap and liquidity risk
            market_cap_rank = crypto_data.get("market_cap_rank", 999)
            if market_cap_rank > 100:
                risk_factors.append("Low market capitalization increases volatility risk")
                base_score += 1.0
            elif market_cap_rank > 50:
                risk_factors.append("Mid-cap cryptocurrency with moderate liquidity risk")
                base_score += 0.5
            elif market_cap_rank <= 10:
                risk_factors.append("Large-cap cryptocurrency with established liquidity")
                base_score -= 0.3

            # Volatility risk based on recent performance
            price_change_24h = abs(crypto_data.get("price_change_24h", 0))
            if price_change_24h > 20:
                risk_factors.append("Extreme daily volatility indicates high price risk")
                base_score += 1.0
            elif price_change_24h > 10:
                risk_factors.append("High daily volatility typical of cryptocurrency markets")
                base_score += 0.5

            # Technology and adoption risk
            categories = crypto_data.get("categories", [])
            if "DeFi" in categories:
                risk_factors.append("DeFi protocol risks including smart contract vulnerabilities")
                base_score += 0.3

            if "Meme" in categories or "meme" in crypto_data.get("description", "").lower():
                risk_factors.append("Meme coin speculation risk with limited fundamental value")
                base_score += 1.5

            # Supply risk
            max_supply = crypto_data.get("max_supply")
            total_supply = crypto_data.get("total_supply", 0)
            circulating_supply = crypto_data.get("circulating_supply", 0)

            if not max_supply and total_supply > 0:
                risk_factors.append("Unlimited supply creates inflation risk")
                base_score += 0.4

            if circulating_supply > 0 and total_supply > 0:
                supply_ratio = circulating_supply / total_supply
                if supply_ratio < 0.5:
                    risk_factors.append("Large portion of tokens not yet in circulation")
                    base_score += 0.3

            # Regulatory risk (general crypto risks)
            risk_factors.extend(
                [
                    "Regulatory uncertainty in major jurisdictions",
                    "Potential for government restrictions or bans",
                    "Tax treatment changes could impact returns",
                ]
            )
            base_score += 0.5

            # Technology and security risks
            risk_factors.extend(
                [
                    "Cybersecurity risks including exchange hacks",
                    "Smart contract bugs and protocol vulnerabilities",
                    "Network congestion and scalability challenges",
                ]
            )
            base_score += 0.3

            # Market structure risks
            risk_factors.extend(
                [
                    "Market manipulation in less regulated environment",
                    "Correlation with broader cryptocurrency market",
                    "Liquidity risk during market stress periods",
                ]
            )
            base_score += 0.2

            # Calculate final score (crypto uses higher baseline risk)
            final_score = min(base_score, 5.0)
            risk_level = self._map_score_to_level(final_score)

            return {
                "symbol": symbol,
                "scale": "0_5",
                "score": round(final_score, 1),
                "level": risk_level,
                "risk_factors": risk_factors[:10],  # Limit to 10 factors
                "assessment_date": datetime.now().isoformat(),
                "crypto_specific_risks": True,
            }

        except Exception as e:
            # Return default high-risk assessment for crypto
            return {
                "symbol": symbol,
                "scale": "0_5",
                "score": 4.0,  # High risk default for crypto
                "level": "High",
                "risk_factors": [
                    "High cryptocurrency market volatility",
                    "Regulatory uncertainty",
                    "Technology and security risks",
                    "Market manipulation potential",
                ],
                "assessment_date": datetime.now().isoformat(),
                "error": f"Risk assessment error: {e}",
            }

    def _map_score_to_level(self, score: float) -> str:
        """Map numerical risk score to standardized risk level."""
        if score <= 1.5:
            return "Low"
        elif score <= 2.5:
            return "Medium"
        elif score <= 4.0:
            return "High"
        else:
            return "Very High"

    async def _get_perplexity_crypto_insights(self, symbol: str) -> list[SonarArticle]:
        """Get crypto-specific insights from Perplexity Sonar."""
        perplexity_integration = self._get_perplexity_integration()
        if not perplexity_integration:
            return []

        try:
            # Create crypto-specific search query
            query = f"{symbol} cryptocurrency regulatory updates adoption news blockchain technology"

            sonar_result = await perplexity_integration.search_financial_news(query=query, ticker=symbol, asset_type="crypto", analysis_type="general", max_results=6)

            if sonar_result.success:
                logger.info(f"Retrieved {len(sonar_result.results)} Perplexity crypto insights for {symbol}")
                return sonar_result.results
                # Success tracking is handled automatically in PerplexityOperationLogger.log_search_success
            else:
                logger.warning(f"Perplexity crypto search failed for {symbol}: {sonar_result.error_message}")
                # Failure tracking is handled automatically in PerplexityOperationLogger.log_search_failure
                return []

        except Exception as e:
            logger.warning(f"Perplexity crypto search failed for {symbol}: {e!s}")

            # Record failure for feature flag tracking
            from finwiz.tools.perplexity_logging import PerplexityFeatureFlagTracker

            PerplexityFeatureFlagTracker.record_operation_failure(symbol, "crypto", "integration_error")
            return []
