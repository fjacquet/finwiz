"""
CoinMarketCap API tools for cryptocurrency data.

This module provides tools for retrieving cryptocurrency data from the CoinMarketCap API,
including pricing, market cap, and other relevant metrics for cryptocurrency analysis.
"""

import os

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Base URL for CoinMarketCap API
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"


class CoinMarketCapException(Exception):
    """Exception raised for CoinMarketCap API errors."""

    pass


class CoinInfoInput(BaseModel):
    """Input schema for CoinMarketCapInfoTool."""

    symbol: str = Field(
        ..., description="Cryptocurrency symbol/ticker (e.g., BTC, ETH, SOL)"
    )


class CryptocurrencyListInput(BaseModel):
    """Input schema for CoinMarketCapListTool."""

    limit: int = Field(
        25, description="Number of cryptocurrencies to return (default: 25, max: 100)"
    )
    sort: str = Field(
        "market_cap",
        description="Sort cryptocurrencies by: 'market_cap', 'volume_24h', 'price', or 'percent_change_24h'",
    )


class CryptocurrencyHistoricalInput(BaseModel):
    """Input schema for CoinMarketCapHistoricalTool."""

    symbol: str = Field(
        ..., description="Cryptocurrency symbol/ticker (e.g., BTC, ETH, SOL)"
    )
    time_period: str = Field(
        "30d",
        description="Time period for historical data: '24h', '7d', '30d', '3m', '1y', or 'ytd'",
    )


class CryptocurrencyNewsInput(BaseModel):
    """Input schema for CoinMarketCapNewsTool."""

    symbol: str | None = Field(
        None, description="Cryptocurrency symbol to get news for (optional)"
    )
    limit: int = Field(
        10, description="Number of news articles to return (default: 10, max: 100)"
    )


class CoinMarketCapInfoTool(BaseTool):
    """
    Tool for retrieving detailed information about a specific cryptocurrency.

    This tool provides current price, market cap, volume, circulating supply,
    and other key metrics for a given cryptocurrency symbol.
    """

    name: str = "CoinMarketCap Cryptocurrency Info"
    description: str = (
        "Get detailed information about a specific cryptocurrency including price, "
        "market cap, volume, circulating supply, and other key metrics. "
        "Provide the cryptocurrency symbol (e.g., BTC, ETH, SOL)."
    )
    args_schema: type[BaseModel] = CoinInfoInput

    def _run(self, symbol: str) -> str:
        """
        Retrieve detailed information about a specific cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol/ticker (e.g., BTC, ETH)

        Returns:
            A string containing detailed information about the cryptocurrency

        Raises:
            CoinMarketCapException: If the API request fails

        """
        logger.info(f"Retrieving information for cryptocurrency: {symbol}")

        try:
            headers = {
                "X-CMC_PRO_API_KEY": os.environ.get("X-CMC_PRO_API_KEY", ""),
                "Accept": "application/json",
            }

            params = {"symbol": symbol.upper(), "convert": "USD"}

            response = requests.get(
                f"{CMC_BASE_URL}/cryptocurrency/quotes/latest",
                headers=headers,
                params=params,
            )

            if response.status_code != 200:
                error_msg = (
                    f"CoinMarketCap API error: {response.status_code} - {response.text}"
                )
                logger.error(error_msg)
                return f"Error retrieving cryptocurrency data: {error_msg}"

            data = response.json()

            if "data" not in data or symbol.upper() not in data["data"]:
                logger.warning(f"No data found for symbol: {symbol}")
                return f"No data found for cryptocurrency symbol: {symbol}"

            crypto_data = data["data"][symbol.upper()]
            quote = crypto_data["quote"]["USD"]

            # Format the information
            info = f"## {crypto_data.get('name')} ({crypto_data.get('symbol')})\n\n"
            info += f"**Current Price:** ${quote.get('price', 0):.4f} USD\n"
            info += f"**Market Cap:** ${quote.get('market_cap', 0):,.0f} USD\n"
            info += f"**24h Volume:** ${quote.get('volume_24h', 0):,.0f} USD\n"
            info += f"**24h Change:** {quote.get('percent_change_24h', 0):.2f}%\n"
            info += f"**7d Change:** {quote.get('percent_change_7d', 0):.2f}%\n"
            info += f"**Circulating Supply:** {crypto_data.get('circulating_supply', 0):,.0f} {crypto_data.get('symbol')}\n"

            if crypto_data.get("max_supply"):
                info += f"**Max Supply:** {crypto_data.get('max_supply', 0):,.0f} {crypto_data.get('symbol')}\n"

            info += f"**Market Cap Rank:** #{crypto_data.get('cmc_rank', 'N/A')}\n"
            info += f"**Last Updated:** {quote.get('last_updated', 'N/A')}\n\n"

            # Add additional details if available
            if "platform" in crypto_data and crypto_data["platform"]:
                info += f"**Token Platform:** {crypto_data['platform'].get('name', 'N/A')}\n"

            if "tags" in crypto_data and crypto_data["tags"]:
                info += f"**Categories:** {', '.join(crypto_data['tags'][:5])}\n"

            logger.info(f"Successfully retrieved information for {symbol}")
            return info

        except Exception as e:
            error_msg = f"Error retrieving cryptocurrency data for {symbol}: {str(e)}"
            logger.error(error_msg)
            return error_msg


class CoinMarketCapListTool(BaseTool):
    """
    Tool for retrieving a list of top cryptocurrencies.

    This tool provides a list of cryptocurrencies sorted by market cap,
    volume, or price with their current metrics.
    """

    name: str = "CoinMarketCap Cryptocurrency List"
    description: str = (
        "Get a list of top cryptocurrencies sorted by market cap, volume, price, "
        "or recent performance. Returns key metrics for each cryptocurrency."
    )
    args_schema: type[BaseModel] = CryptocurrencyListInput

    def _run(self, limit: int = 25, sort: str = "market_cap") -> str:
        """
        Retrieve a list of top cryptocurrencies.

        Args:
            limit: Number of cryptocurrencies to return (default: 25, max: 100)
            sort: Sort by 'market_cap', 'volume_24h', 'price', or 'percent_change_24h'

        Returns:
            A string containing a list of top cryptocurrencies with their metrics

        Raises:
            CoinMarketCapException: If the API request fails

        """
        logger.info(f"Retrieving top {limit} cryptocurrencies sorted by {sort}")

        # Validate and cap limit
        if limit > 100:
            limit = 100
            logger.warning("Limit capped at 100 cryptocurrencies")

        # Map sort parameter to API sort parameter
        sort_map = {
            "market_cap": "market_cap",
            "volume_24h": "volume_24h",
            "price": "price",
            "percent_change_24h": "percent_change_24h",
        }

        sort_by = sort_map.get(sort, "market_cap")

        try:
            headers = {
                "X-CMC_PRO_API_KEY": os.environ.get("X-CMC_PRO_API_KEY", ""),
                "Accept": "application/json",
            }

            params = {"limit": limit, "sort": sort_by, "convert": "USD"}

            response = requests.get(
                f"{CMC_BASE_URL}/cryptocurrency/listings/latest",
                headers=headers,
                params=params,
            )

            if response.status_code != 200:
                error_msg = (
                    f"CoinMarketCap API error: {response.status_code} - {response.text}"
                )
                logger.error(error_msg)
                return f"Error retrieving cryptocurrency list: {error_msg}"

            data = response.json()

            if "data" not in data:
                logger.warning("No cryptocurrency data found")
                return "No cryptocurrency data found"

            # Format the information
            result = f"## Top {limit} Cryptocurrencies by {sort.replace('_', ' ').title()}\n\n"
            result += "| Rank | Name | Symbol | Price (USD) | 24h Change | Market Cap | 24h Volume |\n"
            result += "|------|------|--------|------------|------------|------------|------------|\n"

            for crypto in data["data"]:
                quote = crypto["quote"]["USD"]
                result += f"| {crypto.get('cmc_rank', 'N/A')} "
                result += f"| {crypto.get('name', 'Unknown')} "
                result += f"| {crypto.get('symbol', 'N/A')} "
                result += f"| ${quote.get('price', 0):.4f} "
                result += f"| {quote.get('percent_change_24h', 0):.2f}% "
                result += f"| ${quote.get('market_cap', 0) / 1e9:.2f}B "
                result += f"| ${quote.get('volume_24h', 0) / 1e6:.2f}M |\n"

            logger.info(
                f"Successfully retrieved list of {len(data['data'])} cryptocurrencies"
            )
            return result

        except Exception as e:
            error_msg = f"Error retrieving cryptocurrency list: {str(e)}"
            logger.error(error_msg)
            return error_msg


class CoinMarketCapHistoricalTool(BaseTool):
    """
    Tool for retrieving historical price data for a specific cryptocurrency.

    This tool provides historical price, volume, and market cap data for
    a given cryptocurrency over various time periods.
    """

    name: str = "CoinMarketCap Historical Data"
    description: str = (
        "Get historical price, volume, and market cap data for a specific cryptocurrency "
        "over various time periods (24h, 7d, 30d, 3m, 1y, or ytd)."
    )
    args_schema: type[BaseModel] = CryptocurrencyHistoricalInput

    def _run(self, symbol: str, time_period: str = "30d") -> str:
        """
        Retrieve historical data for a specific cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol/ticker (e.g., BTC, ETH)
            time_period: Time period for historical data

        Returns:
            A string containing historical data for the cryptocurrency

        Raises:
            CoinMarketCapException: If the API request fails

        """
        logger.info(f"Retrieving {time_period} historical data for {symbol}")

        # Map time period to interval
        time_map = {
            "24h": "hourly",
            "7d": "daily",
            "30d": "daily",
            "3m": "daily",
            "1y": "weekly",
            "ytd": "daily",
        }

        interval = time_map.get(time_period, "daily")

        try:
            headers = {
                "X-CMC_PRO_API_KEY": os.environ.get("X-CMC_PRO_API_KEY", ""),
                "Accept": "application/json",
            }

            # For historical data, we first need to get the crypto ID
            id_params = {"symbol": symbol.upper()}

            id_response = requests.get(
                f"{CMC_BASE_URL}/cryptocurrency/map", headers=headers, params=id_params
            )

            if id_response.status_code != 200:
                error_msg = f"CoinMarketCap API error: {id_response.status_code} - {id_response.text}"
                logger.error(error_msg)
                return f"Error retrieving cryptocurrency ID: {error_msg}"

            id_data = id_response.json()

            if "data" not in id_data or not id_data["data"]:
                logger.warning(f"No ID found for symbol: {symbol}")
                return f"No ID found for cryptocurrency symbol: {symbol}"

            crypto_id = id_data["data"][0]["id"]

            # Now get the historical data
            history_params = {
                "id": crypto_id,
                "convert": "USD",
                "interval": interval,
                "time_period": time_period,
            }

            history_response = requests.get(
                f"{CMC_BASE_URL}/cryptocurrency/quotes/historical",
                headers=headers,
                params=history_params,
            )

            if history_response.status_code != 200:
                error_msg = f"CoinMarketCap API error: {history_response.status_code} - {history_response.text}"
                logger.error(error_msg)
                return f"Error retrieving historical data: {error_msg}"

            history_data = history_response.json()

            if "data" not in history_data or "quotes" not in history_data["data"]:
                logger.warning(f"No historical data found for {symbol}")
                return f"No historical data found for {symbol} over {time_period}"

            quotes = history_data["data"]["quotes"]

            # Format the information
            result = f"## Historical Data for {symbol} over {time_period}\n\n"

            # Determine the format based on the interval
            if interval == "hourly":
                result += "| Date & Time | Price (USD) | Volume | Market Cap |\n"
                result += "|-------------|-------------|--------|------------|\n"

                for quote in quotes:
                    timestamp = quote.get("timestamp", "N/A")
                    price = quote["quote"]["USD"].get("price", 0)
                    volume = quote["quote"]["USD"].get("volume_24h", 0)
                    market_cap = quote["quote"]["USD"].get("market_cap", 0)

                    result += f"| {timestamp} "
                    result += f"| ${price:.4f} "
                    result += f"| ${volume / 1e6:.2f}M "
                    result += f"| ${market_cap / 1e9:.2f}B |\n"
            else:
                result += "| Date | Price (USD) | 24h Change | Volume | Market Cap |\n"
                result += "|------|-------------|------------|--------|------------|\n"

                for quote in quotes:
                    timestamp = quote.get("timestamp", "N/A").split("T")[0]
                    price = quote["quote"]["USD"].get("price", 0)
                    change = quote["quote"]["USD"].get("percent_change_24h", 0)
                    volume = quote["quote"]["USD"].get("volume_24h", 0)
                    market_cap = quote["quote"]["USD"].get("market_cap", 0)

                    result += f"| {timestamp} "
                    result += f"| ${price:.4f} "
                    result += f"| {change:.2f}% "
                    result += f"| ${volume / 1e6:.2f}M "
                    result += f"| ${market_cap / 1e9:.2f}B |\n"

            logger.info(f"Successfully retrieved historical data for {symbol}")
            return result

        except Exception as e:
            error_msg = f"Error retrieving historical data for {symbol}: {str(e)}"
            logger.error(error_msg)
            return error_msg


class CoinMarketCapNewsTool(BaseTool):
    """
    Tool for retrieving cryptocurrency news from CoinMarketCap.

    This tool provides the latest news articles about cryptocurrencies
    in general or about a specific cryptocurrency.
    """

    name: str = "CoinMarketCap News"
    description: str = (
        "Get the latest news about cryptocurrencies from CoinMarketCap. "
        "Can be filtered for a specific cryptocurrency or show general crypto news."
    )
    args_schema: type[BaseModel] = CryptocurrencyNewsInput

    def _run(self, symbol: str | None = None, limit: int = 10) -> str:
        """
        Retrieve cryptocurrency news articles.

        Args:
            symbol: The cryptocurrency symbol/ticker to filter news for (optional)
            limit: Number of news articles to return (default: 10, max: 100)

        Returns:
            A string containing cryptocurrency news articles

        Raises:
            CoinMarketCapException: If the API request fails

        """
        if symbol:
            logger.info(f"Retrieving top {limit} news articles for {symbol}")
        else:
            logger.info(f"Retrieving top {limit} cryptocurrency news articles")

        # Validate and cap limit
        if limit > 100:
            limit = 100
            logger.warning("Limit capped at 100 news articles")

        try:
            headers = {
                "X-CMC_PRO_API_KEY": os.environ.get("X-CMC_PRO_API_KEY", ""),
                "Accept": "application/json",
            }

            params = {"limit": limit}

            # If symbol is provided, get its ID first
            if symbol:
                id_params = {"symbol": symbol.upper()}

                id_response = requests.get(
                    f"{CMC_BASE_URL}/cryptocurrency/map",
                    headers=headers,
                    params=id_params,
                )

                if id_response.status_code != 200:
                    error_msg = f"CoinMarketCap API error: {id_response.status_code} - {id_response.text}"
                    logger.error(error_msg)
                    return f"Error retrieving cryptocurrency ID: {error_msg}"

                id_data = id_response.json()

                if "data" not in id_data or not id_data["data"]:
                    logger.warning(f"No ID found for symbol: {symbol}")
                    return f"No ID found for cryptocurrency symbol: {symbol}"

                params["cryptocurrencies"] = id_data["data"][0]["id"]

            response = requests.get(
                f"{CMC_BASE_URL}/content/latest", headers=headers, params=params
            )

            if response.status_code != 200:
                error_msg = (
                    f"CoinMarketCap API error: {response.status_code} - {response.text}"
                )
                logger.error(error_msg)
                return f"Error retrieving cryptocurrency news: {error_msg}"

            data = response.json()

            if "data" not in data:
                logger.warning("No news articles found")
                return "No cryptocurrency news articles found"

            # Format the information
            if symbol:
                result = f"## Latest News for {symbol}\n\n"
            else:
                result = "## Latest Cryptocurrency News\n\n"

            for article in data["data"]:
                result += f"### {article.get('title', 'No Title')}\n"
                result += f"**Date:** {article.get('published_at', 'N/A')}\n"
                result += f"**Source:** {article.get('source', 'Unknown')}\n\n"
                result += (
                    f"{article.get('description', 'No description available.')}\n\n"
                )
                result += f"[Read more]({article.get('url', '#')})\n\n"
                result += "---\n\n"

            logger.info(f"Successfully retrieved {len(data['data'])} news articles")
            return result

        except Exception as e:
            error_msg = f"Error retrieving cryptocurrency news: {str(e)}"
            logger.error(error_msg)
            return error_msg


def get_coinmarketcap_tools() -> list[BaseTool]:
    """
    Get a list of all CoinMarketCap tools.

    Returns:
        A list of CoinMarketCap tool instances

    """
    return [
        CoinMarketCapInfoTool(),
        CoinMarketCapListTool(),
        CoinMarketCapHistoricalTool(),
        CoinMarketCapNewsTool(),
    ]
