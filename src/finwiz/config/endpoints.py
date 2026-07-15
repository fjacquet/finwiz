"""Centralized API endpoint configuration.

All API base URLs are defined here with environment variable overrides.
Tools and services import from this module instead of hardcoding URLs.
"""

import os

# --- Stock / Market Data ---
ALPHA_VANTAGE_BASE: str = os.getenv("AV_BASE_URL", "https://www.alphavantage.co/query")
TWELVE_DATA_BASE: str = os.getenv("TD_BASE_URL", "https://api.twelvedata.com")

# --- AI / Search ---
# Perplexity's chat-completions endpoint (PPLX_BASE_URL) is now read directly by
# crewai_custom_tools at import time; finwiz no longer has a production consumer
# for it, so no local PERPLEXITY_CHAT constant is kept here.
PERPLEXITY_SEARCH: str = os.getenv("PPLX_SEARCH_URL", "https://api.perplexity.ai/search")
OPENAI_BASE: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# --- SEC / Regulatory ---
SEC_EDGAR_BASE: str = os.getenv("SEC_EDGAR_BASE_URL", "https://www.sec.gov")
SEC_EFTS_BASE: str = os.getenv("SEC_EFTS_BASE_URL", "https://efts.sec.gov/LATEST")
SEC_DATA_BASE: str = os.getenv("SEC_DATA_BASE_URL", "https://data.sec.gov")

# --- News / Sentiment ---
FINNHUB_BASE: str = os.getenv("FINNHUB_BASE_URL", "https://finnhub.io/api/v1")

# --- Market Indicators ---
FEAR_GREED_BASE: str = os.getenv("FEAR_GREED_BASE_URL", "https://production.dataviz.cnn.io/index/fearandgreed/graphdata")

# --- Web (no API key, not overridable) ---
YAHOO_FINANCE_WEB: str = "https://finance.yahoo.com"
