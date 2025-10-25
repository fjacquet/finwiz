"""
Ticker Existence Validation Tool.

Validates symbol existence and basic classification using Yahoo Finance (stocks/ETFs)
and Coinbase Products API (crypto). No country/UCITS logic.
"""

from __future__ import annotations

from typing import Any, Literal

import requests
import yfinance as yf  # type: ignore[import-untyped]  # yfinance has no official type stubs
from crewai.tools import BaseTool
from pydantic import BaseModel

# Import schema from centralized location
from finwiz.schemas.tools import TickerValidationInput

AssetClass = Literal["stock", "etf", "crypto", "auto"]


class TickerExistenceValidationTool(BaseTool):
    """
    Validate ticker existence and classify asset class when possible.

    - Stocks/ETFs: Yahoo Finance `Ticker.info` presence and `quoteType` checks
    - Crypto: Coinbase Products API listing check
    """

    name: str = "Ticker Existence Validation Tool"
    description: str = (
        "Validate that a ticker exists on Yahoo Finance (equities/ETFs) or Coinbase (crypto),"
        " returning a compact dict: {symbol, asset_class, valid, reason, meta}."
    )
    args_schema: type[BaseModel] = TickerValidationInput

    def _run(self, symbol: str, asset_class: AssetClass = "auto") -> dict:
        try:
            if asset_class == "crypto":
                return self._validate_crypto(symbol)
            # Default path uses Yahoo first; will fall back to crypto if symbol like 'BTC'
            res = self._validate_yahoo(symbol, asset_class)
            if res["reason"] == "unknown_quote_type_try_crypto":
                return self._validate_crypto(symbol)
            return res
        except Exception as e:  # pragma: no cover - defensive
            return {
                "symbol": symbol,
                "asset_class": asset_class,
                "valid": False,
                "reason": f"validation_error: {e}",
                "meta": {},
            }

    # --- Helpers ---
    def _validate_yahoo(self, symbol: str, asset_class: AssetClass) -> dict:
        t = yf.Ticker(symbol)
        info: dict[str, Any] = t.info or {}
        if not info:
            return {
                "symbol": symbol,
                "asset_class": asset_class,
                "valid": False,
                "reason": "not_found_on_yahoo",
                "meta": {"source": "yahoo"},
            }
        quote_type = (info.get("quoteType") or "").upper()
        exchange = (info.get("exchange") or "").upper()
        long_name = info.get("longName") or info.get("shortName") or ""
        currency = info.get("currency") or ""

        detected: AssetClass = asset_class
        if asset_class == "auto":
            if quote_type == "ETF":
                detected = "etf"
            elif quote_type in {"EQUITY", "COMMONSTOCK", "PREFERREDSTOCK"}:
                detected = "stock"
            else:
                return {
                    "symbol": symbol,
                    "asset_class": "auto",
                    "valid": False,
                    "reason": "unknown_quote_type_try_crypto",
                    "meta": {"source": "yahoo", "quoteType": quote_type},
                }

        if detected == "etf":
            valid = quote_type == "ETF"
        else:
            valid = quote_type in {"EQUITY", "COMMONSTOCK", "PREFERREDSTOCK"}

        return {
            "symbol": symbol,
            "asset_class": detected,
            "valid": bool(valid and exchange),
            "reason": None if bool(valid and exchange) else "invalid_or_unknown_exchange",
            "meta": {
                "exchange": exchange,
                "currency": currency,
                "name": long_name,
                "quoteType": quote_type,
                "source": "yahoo",
            },
        }

    def _validate_crypto(self, symbol: str) -> dict:
        sym = symbol.upper()
        try:
            r = requests.get("https://api.exchange.coinbase.com/products", timeout=10)
            r.raise_for_status()
            products: list[dict[str, Any]] = r.json()
            listed_pairs = [p.get("id") for p in products if isinstance(p.get("id"), str)]
            
            # Check if the symbol itself is in the list (e.g., BTC-USD)
            # or if any pair starts with the symbol (e.g., BTC matches BTC-USD, BTC-EUR)
            exists = sym in listed_pairs or any(str(pid).startswith(f"{sym}-") for pid in listed_pairs)
            
            # Find matching pairs for metadata
            matching_pairs = [pid for pid in listed_pairs if pid == sym or str(pid).startswith(f"{sym}-")]
            
            return {
                "symbol": sym,
                "asset_class": "crypto",
                "valid": exists,
                "reason": None if exists else "not_listed_on_coinbase",
                "meta": {
                    "pairs": matching_pairs[:10],
                    "source": "coinbase",
                },
            }
        except Exception as e:
            return {
                "symbol": sym,
                "asset_class": "crypto",
                "valid": False,
                "reason": f"coinbase_error:{e}",
                "meta": {"source": "coinbase"},
            }
