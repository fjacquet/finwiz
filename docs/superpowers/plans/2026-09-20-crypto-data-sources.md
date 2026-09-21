# Crypto Market Data Sources Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace fabricated crypto fundamentals with real multi-source data, and
make a missing value read as missing everywhere instead of being invented.

**Architecture:** A new sync `CryptoSourceOrchestrator` resolves crypto market
data from a CoinGecko adapter (primary), the already-fetched yfinance price, and
a Kraken adapter (cross-check and last-resort price), recording per-field lineage
and a pinned confidence. Anything unresolved stays `None` all the way through:
the collector writes `None`, `missing_fields` reports it, and the crypto scorer
renormalizes its weights over the components that survived rather than treating
absence as a zero.

**Tech Stack:** Python 3.13, Pydantic, CrewAI custom tools
(`EnhancedCryptoAnalysisTool`, `KrakenTickerInfoTool`), pytest + pytest-mock.

**Spec:** `docs/superpowers/specs/2026-09-20-crypto-data-sources-design.md`

## Global Constraints

- **unittest.mock is BANNED.** Use pytest-mock only (`mocker.patch()`). Enforced
  by ruff and `make check-unittest-mock`.
- Line length 180 characters (ruff configured).
- All Pydantic models live in `schemas/`, not in domain folders. The dataclasses
  in this plan are plain `@dataclass`, not Pydantic, matching
  `data/adapters/base_adapter.py`.
- `json.dumps` always uses `default=str`.
- Tool output is parsed with `crewai_custom_tools.core.results.parse_tool_result()`,
  never by indexing the raw JSON string. It raises `ToolResultError` when the
  envelope reports failure.
- Crypto adapters are **synchronous**. The equity adapters in
  `data/adapters/` are async, but both underlying crypto tools are sync and the
  calling collector is sync; the repo already documents that thread-per-holding
  event loops make asyncio primitives unusable there.
- Never fabricate a numeric stand-in for missing data. `None` is the only
  allowed representation of "not available".
- Every code change ships with the ADR / CHANGELOG / module CLAUDE.md updates it
  invalidates, in the same branch (Task 8).
- In Markdown, fence non-executable code fragments as `text`, never `python` —
  `make lint` rewrites `python` fences inside Markdown on every run.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/finwiz/data/adapters/crypto/base.py` | `CryptoMarketData`, `BaseCryptoAdapter`, `normalize_crypto_symbol`, `positive_or_none` |
| `src/finwiz/data/adapters/crypto/coingecko_adapter.py` | `CoinGeckoAdapter` — price, market cap, volume, supplies; rejects the tool's fabricated fallback |
| `src/finwiz/data/adapters/crypto/kraken_adapter.py` | `KrakenAdapter` — price and single-venue volume from the public endpoint |
| `src/finwiz/data/adapters/crypto/genesis.py` | `CRYPTO_GENESIS_YEAR`, `crypto_age_years()` |
| `src/finwiz/data/crypto_source_orchestrator.py` | `CryptoLineage`, `CryptoOrchestrationResult`, `CryptoSourceOrchestrator` |
| `src/finwiz/scoring/asset_analyzers/crypto_analyzer.py` | weight renormalization over available components |
| `src/finwiz/scoring/deep_analysis_scorer.py` | tolerate a `None` fundamental score in the composite |
| `src/finwiz/orchestrators/deep_analysis_data_collector.py` | wire the orchestrator, delete the three fabrication sites |
| `src/finwiz/scoring/crew_export_generator.py` | add `market_cap` to the crypto `key_fields` |
| `src/finwiz/scoring/portfolio_deep_analyzer.py` | crypto branch stops fabricating defaults |

---

### Task 1: Crypto adapter base and CoinGecko adapter

**Files:**

- Create: `src/finwiz/data/adapters/crypto/__init__.py`
- Create: `src/finwiz/data/adapters/crypto/base.py`
- Create: `src/finwiz/data/adapters/crypto/coingecko_adapter.py`
- Test: `tests/unit/data/adapters/crypto/__init__.py` (empty)
- Test: `tests/unit/data/adapters/crypto/test_coingecko_adapter.py`

**Interfaces:**

- Consumes: `finwiz.tools.enhanced_crypto_tool.EnhancedCryptoAnalysisTool`
  (its `_run(symbol, include_thesis, include_risk_assessment, include_perplexity)`
  returns a dict whose `crypto_data` sub-dict carries `current_price`,
  `market_cap`, `total_volume`, `volume_24h`, `circulating_supply`,
  `max_supply`, `sources`).
- Produces:
  - `CryptoMarketData` dataclass with fields `ticker: str`, `source: str`,
    `timestamp: datetime`, `confidence: float`, `price: float | None`,
    `market_cap: float | None`, `volume_24h: float | None`,
    `circulating_supply: float | None`, `max_supply: float | None`,
    `raw_data: dict[str, Any] | None`, `warnings: list[str] | None`.
  - `BaseCryptoAdapter` abstract class with `source_name: str` property and
    `fetch(self, ticker: str) -> CryptoMarketData | None`.
  - `normalize_crypto_symbol(ticker: str) -> str`.
  - `positive_or_none(value: Any) -> float | None`.
  - `CoinGeckoAdapter(tool: Any | None = None)` with `source_name == "coingecko"`.

**Background the implementer needs:** `EnhancedCryptoAnalysisTool` never raises
on a failed lookup. When CoinGecko does not know the symbol it returns invented
numbers tagged `sources == ["Fallback Data"]` (see
`tools/enhanced_crypto_tool.py:210 _create_fallback_crypto_data`). Treating that
payload as data is the exact bug this whole plan exists to remove, so the
adapter must detect the marker and return `None`.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/data/adapters/crypto/__init__.py` as an empty file, then
`tests/unit/data/adapters/crypto/test_coingecko_adapter.py`:

```python
"""Tests for the CoinGecko crypto adapter."""

import json

import pytest

from finwiz.data.adapters.crypto.base import normalize_crypto_symbol, positive_or_none
from finwiz.data.adapters.crypto.coingecko_adapter import CoinGeckoAdapter


class _FakeTool:
    """Stands in for EnhancedCryptoAnalysisTool, recording the symbol it saw."""

    def __init__(self, payload, raises=None):
        self.payload = payload
        self.raises = raises
        self.seen_symbol = None

    def _run(self, symbol, include_thesis=True, include_risk_assessment=True, include_perplexity=True):
        self.seen_symbol = symbol
        if self.raises is not None:
            raise self.raises
        return self.payload


def _good_payload():
    return {
        "symbol": "BTC",
        "crypto_data": {
            "symbol": "BTC",
            "name": "Bitcoin",
            "current_price": 81114.0,
            "market_cap": 1629408510367.0,
            "total_volume": 23900006504.0,
            "volume_24h": 23900006504.0,
            "circulating_supply": 20087096.0,
            "max_supply": 21000000.0,
            "sources": ["CoinGecko (via crewai_custom_tools)"],
        },
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("BTC-USD", "BTC"), ("btc-usd", "BTC"), ("ETH-USDT", "ETH"), ("SOL", "SOL"), ("  xrp-usd  ", "XRP")],
)
def test_normalize_crypto_symbol(raw, expected):
    assert normalize_crypto_symbol(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(1.5, 1.5), (0, None), (-3, None), (None, None), ("abc", None), ("12.5", 12.5)],
)
def test_positive_or_none(raw, expected):
    assert positive_or_none(raw) == expected


def test_fetch_maps_every_field_and_strips_usd_suffix():
    tool = _FakeTool(_good_payload())
    adapter = CoinGeckoAdapter(tool=tool)

    result = adapter.fetch("BTC-USD")

    assert tool.seen_symbol == "BTC", "the -USD suffix must be stripped before the CoinGecko lookup"
    assert result is not None
    assert result.source == "coingecko"
    assert result.ticker == "BTC-USD"
    assert result.price == 81114.0
    assert result.market_cap == 1629408510367.0
    assert result.volume_24h == 23900006504.0
    assert result.circulating_supply == 20087096.0
    assert result.max_supply == 21000000.0


def test_fabricated_fallback_payload_counts_as_failure():
    payload = {
        "crypto_data": {
            "symbol": "BTC-USD",
            "name": "Cryptocurrency BTC-USD",
            "current_price": 0,
            "market_cap": 0,
            "total_volume": 0,
            "circulating_supply": 0,
            "sources": ["Fallback Data"],
        }
    }
    adapter = CoinGeckoAdapter(tool=_FakeTool(payload))

    assert adapter.fetch("BTC-USD") is None, "invented fallback data must never be returned as real data"


def test_tool_exception_returns_none():
    adapter = CoinGeckoAdapter(tool=_FakeTool(None, raises=RuntimeError("network down")))

    assert adapter.fetch("ETH-USD") is None


def test_missing_crypto_data_returns_none():
    adapter = CoinGeckoAdapter(tool=_FakeTool({"symbol": "ETH"}))

    assert adapter.fetch("ETH-USD") is None


def test_uncapped_supply_keeps_max_supply_none():
    payload = _good_payload()
    payload["crypto_data"]["max_supply"] = None

    result = CoinGeckoAdapter(tool=_FakeTool(payload)).fetch("ETH-USD")

    assert result is not None
    assert result.max_supply is None, "no cap is a fact about the asset, not a missing value"
    assert result.circulating_supply == 20087096.0


def test_zero_market_cap_becomes_none():
    payload = _good_payload()
    payload["crypto_data"]["market_cap"] = 0

    result = CoinGeckoAdapter(tool=_FakeTool(payload)).fetch("BTC-USD")

    assert result is not None
    assert result.market_cap is None


def test_raw_data_is_json_serialisable():
    result = CoinGeckoAdapter(tool=_FakeTool(_good_payload())).fetch("BTC-USD")

    assert result is not None
    json.dumps(result.raw_data, default=str)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/data/adapters/crypto/test_coingecko_adapter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'finwiz.data.adapters.crypto'`

- [ ] **Step 3: Create the package base**

Create `src/finwiz/data/adapters/crypto/__init__.py`:

```python
"""Crypto market-data adapters.

Separate from the equity adapters in the parent package: `BaseDataAdapter`
imposes `FundamentalData`, which is hardwired to four equity metrics with
equity validation bounds and has no place to put market cap, volume or supply.
"""

from finwiz.data.adapters.crypto.base import (
    BaseCryptoAdapter,
    CryptoMarketData,
    normalize_crypto_symbol,
    positive_or_none,
)
from finwiz.data.adapters.crypto.coingecko_adapter import CoinGeckoAdapter

__all__ = [
    "BaseCryptoAdapter",
    "CoinGeckoAdapter",
    "CryptoMarketData",
    "normalize_crypto_symbol",
    "positive_or_none",
]
```

Create `src/finwiz/data/adapters/crypto/base.py`:

```python
"""Shared shapes for crypto market-data adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

_QUOTE_SUFFIXES = ("-USD", "-USDT", "-USDC", "-EUR")


def normalize_crypto_symbol(ticker: str) -> str:
    """Strip the quote-currency suffix a yfinance-style crypto ticker carries.

    CoinGecko and Kraken both key on the bare base symbol; `BTC-USD` is a
    yfinance convention and resolves nowhere else.
    """
    symbol = ticker.strip().upper()
    for suffix in _QUOTE_SUFFIXES:
        if symbol.endswith(suffix):
            return symbol[: -len(suffix)]
    return symbol


def positive_or_none(value: Any) -> float | None:
    """Coerce to a strictly positive float, else None.

    Upstream sources signal "no data" with 0 as readily as with null, and a
    zero market cap or volume is never a real measurement.
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


@dataclass
class CryptoMarketData:
    """Market data as reported by a single source."""

    ticker: str
    source: str
    timestamp: datetime
    confidence: float
    price: float | None = None
    market_cap: float | None = None
    volume_24h: float | None = None
    circulating_supply: float | None = None
    max_supply: float | None = None
    raw_data: dict[str, Any] | None = None
    warnings: list[str] | None = None

    def __post_init__(self) -> None:
        """Normalize warnings and validate confidence."""
        if self.warnings is None:
            self.warnings = []
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


class BaseCryptoAdapter(ABC):
    """Base class for crypto market-data adapters.

    Synchronous by design: the underlying tools are synchronous and the calling
    collector runs one thread per holding.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the identifier recorded in lineage for this source."""

    @abstractmethod
    def fetch(self, ticker: str) -> CryptoMarketData | None:
        """Return market data, or None when this source cannot answer.

        Implementations never raise for an unavailable source and never invent
        a value: an unanswerable lookup is None.
        """
```

- [ ] **Step 4: Write the CoinGecko adapter**

Create `src/finwiz/data/adapters/crypto/coingecko_adapter.py`:

```python
"""CoinGecko crypto market-data adapter."""

from datetime import datetime
from typing import Any

from finwiz.data.adapters.crypto.base import (
    BaseCryptoAdapter,
    CryptoMarketData,
    normalize_crypto_symbol,
    positive_or_none,
)
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# EnhancedCryptoAnalysisTool does not raise on an unknown symbol: it returns
# invented numbers tagged with this marker. Treating that payload as data is
# how every crypto holding came to be scored on a fabricated $10B market cap.
FALLBACK_MARKER = "Fallback Data"


class CoinGeckoAdapter(BaseCryptoAdapter):
    """Reads price, market cap, volume and supply from CoinGecko."""

    def __init__(self, tool: Any | None = None) -> None:
        """Wire the underlying tool, constructed lazily so tests can inject one."""
        if tool is None:
            from finwiz.tools.enhanced_crypto_tool import EnhancedCryptoAnalysisTool

            tool = EnhancedCryptoAnalysisTool()
        self._tool = tool

    @property
    def source_name(self) -> str:
        """Return the lineage identifier for this source."""
        return "coingecko"

    def fetch(self, ticker: str) -> CryptoMarketData | None:
        """Fetch market data for one ticker, or None when CoinGecko cannot answer."""
        symbol = normalize_crypto_symbol(ticker)
        try:
            result = self._tool._run(
                symbol=symbol,
                include_thesis=False,
                include_risk_assessment=False,
                include_perplexity=False,
            )
        except Exception as exc:
            logger.warning("CoinGecko fetch failed for %s: %s", symbol, exc)
            return None

        if not isinstance(result, dict):
            logger.warning("CoinGecko returned a non-dict payload for %s", symbol)
            return None

        data = result.get("crypto_data")
        if not isinstance(data, dict):
            logger.warning("CoinGecko payload for %s carries no crypto_data", symbol)
            return None

        if FALLBACK_MARKER in (data.get("sources") or []):
            logger.warning("CoinGecko has no entry for %s; discarding fabricated fallback payload", symbol)
            return None

        volume = data.get("total_volume")
        if volume is None:
            volume = data.get("volume_24h")

        return CryptoMarketData(
            ticker=ticker,
            source=self.source_name,
            timestamp=datetime.now(),
            confidence=1.0,
            price=positive_or_none(data.get("current_price")),
            market_cap=positive_or_none(data.get("market_cap")),
            volume_24h=positive_or_none(volume),
            circulating_supply=positive_or_none(data.get("circulating_supply")),
            max_supply=positive_or_none(data.get("max_supply")),
            raw_data=data,
        )
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/unit/data/adapters/crypto/test_coingecko_adapter.py -v`
Expected: PASS, 15 tests

- [ ] **Step 6: Lint and commit**

```bash
make lint
git add src/finwiz/data/adapters/crypto/ tests/unit/data/adapters/crypto/
git commit -m "feat(data): crypto adapter base and CoinGecko adapter"
```

---

### Task 2: Kraken adapter

**Files:**

- Create: `src/finwiz/data/adapters/crypto/kraken_adapter.py`
- Modify: `src/finwiz/data/adapters/crypto/__init__.py` (export `KrakenAdapter`)
- Test: `tests/unit/data/adapters/crypto/test_kraken_adapter.py`

**Interfaces:**

- Consumes: `BaseCryptoAdapter`, `CryptoMarketData`, `normalize_crypto_symbol`,
  `positive_or_none` from Task 1;
  `crewai_custom_tools.KrakenTickerInfoTool` (its `_run(pair: str) -> str`
  returns a `{"success", "data", "error"}` envelope) and
  `crewai_custom_tools.core.results.parse_tool_result`.
- Produces: `KrakenAdapter(tool: Any | None = None)` with
  `source_name == "kraken"`.

**Background the implementer needs:** the Kraken public `Ticker` endpoint needs
no API key. Its payload uses `c` for the last trade (`[price, lot_volume]`) and
`v` for volume (`[today, last_24h]`). **The volume is denominated in base units**
(BTC, not USD), whereas CoinGecko reports USD. The adapter converts with the
Kraken price so the `volume_24h` field carries one consistent unit; the
orchestrator records in lineage that this figure is single-venue. Verified live
on 2026-09-20: `BTCUSD`, `ETHUSD`, `XRPUSD` and `SOLUSD` all resolve.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/data/adapters/crypto/test_kraken_adapter.py`:

```python
"""Tests for the Kraken crypto adapter."""

import json

from finwiz.data.adapters.crypto.kraken_adapter import KrakenAdapter


class _FakeTool:
    """Stands in for KrakenTickerInfoTool, recording the pair it saw."""

    def __init__(self, envelope, raises=None):
        self.envelope = envelope
        self.raises = raises
        self.seen_pair = None

    def _run(self, pair):
        self.seen_pair = pair
        if self.raises is not None:
            raise self.raises
        return self.envelope


def _envelope(data):
    return json.dumps({"success": True, "data": data, "error": None})


def _btc_payload():
    return {
        "a": ["81130.00000", "1", "1.000"],
        "b": ["81120.00000", "1", "1.000"],
        "c": ["81121.40000", "0.00100000"],
        "v": ["120.50000000", "1850.00000000"],
    }


def test_fetch_builds_pair_and_reads_last_trade():
    tool = _FakeTool(_envelope(_btc_payload()))
    adapter = KrakenAdapter(tool=tool)

    result = adapter.fetch("BTC-USD")

    assert tool.seen_pair == "BTCUSD"
    assert result is not None
    assert result.source == "kraken"
    assert result.ticker == "BTC-USD"
    assert result.price == 81121.4


def test_volume_is_converted_from_base_units_to_usd():
    result = KrakenAdapter(tool=_FakeTool(_envelope(_btc_payload()))).fetch("BTC-USD")

    assert result is not None
    # 1850 BTC over 24h at 81121.40 per BTC
    assert result.volume_24h == 1850.0 * 81121.4


def test_market_cap_and_supply_are_never_reported():
    result = KrakenAdapter(tool=_FakeTool(_envelope(_btc_payload()))).fetch("BTC-USD")

    assert result is not None
    assert result.market_cap is None
    assert result.circulating_supply is None
    assert result.max_supply is None


def test_unlisted_pair_returns_none():
    envelope = json.dumps({"success": False, "data": None, "error": "No data found for pair FOOUSD. Invalid pair."})
    adapter = KrakenAdapter(tool=_FakeTool(envelope))

    assert adapter.fetch("FOO-USD") is None


def test_transport_error_returns_none():
    adapter = KrakenAdapter(tool=_FakeTool(None, raises=RuntimeError("connection reset")))

    assert adapter.fetch("BTC-USD") is None


def test_missing_last_trade_returns_none():
    payload = _btc_payload()
    del payload["c"]
    adapter = KrakenAdapter(tool=_FakeTool(_envelope(payload)))

    assert adapter.fetch("BTC-USD") is None


def test_missing_volume_still_returns_price():
    payload = _btc_payload()
    del payload["v"]

    result = KrakenAdapter(tool=_FakeTool(_envelope(payload))).fetch("BTC-USD")

    assert result is not None
    assert result.price == 81121.4
    assert result.volume_24h is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/data/adapters/crypto/test_kraken_adapter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'finwiz.data.adapters.crypto.kraken_adapter'`

- [ ] **Step 3: Write the adapter**

Create `src/finwiz/data/adapters/crypto/kraken_adapter.py`:

```python
"""Kraken crypto market-data adapter (public Ticker endpoint, no API key)."""

from datetime import datetime
from typing import Any

from crewai_custom_tools.core.results import parse_tool_result

from finwiz.data.adapters.crypto.base import (
    BaseCryptoAdapter,
    CryptoMarketData,
    normalize_crypto_symbol,
    positive_or_none,
)
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def _indexed_float(value: Any, index: int) -> float | None:
    """Read one positive float out of a Kraken array field."""
    if not isinstance(value, (list, tuple)) or len(value) <= index:
        return None
    return positive_or_none(value[index])


class KrakenAdapter(BaseCryptoAdapter):
    """Reads the last traded price and single-venue 24h volume from Kraken."""

    def __init__(self, tool: Any | None = None) -> None:
        """Wire the underlying tool, constructed lazily so tests can inject one."""
        if tool is None:
            from crewai_custom_tools import KrakenTickerInfoTool

            tool = KrakenTickerInfoTool()
        self._tool = tool

    @property
    def source_name(self) -> str:
        """Return the lineage identifier for this source."""
        return "kraken"

    def fetch(self, ticker: str) -> CryptoMarketData | None:
        """Fetch price and volume for one ticker, or None when Kraken cannot answer."""
        symbol = normalize_crypto_symbol(ticker)
        pair = f"{symbol}USD"
        try:
            payload = parse_tool_result(self._tool._run(pair=pair))
        except Exception as exc:
            logger.warning("Kraken fetch failed for %s: %s", pair, exc)
            return None

        if not isinstance(payload, dict):
            logger.warning("Kraken returned a non-dict payload for %s", pair)
            return None

        price = _indexed_float(payload.get("c"), 0)
        if price is None:
            logger.warning("Kraken payload for %s carries no last trade price", pair)
            return None

        base_volume = _indexed_float(payload.get("v"), 1)

        return CryptoMarketData(
            ticker=ticker,
            source=self.source_name,
            timestamp=datetime.now(),
            confidence=1.0,
            price=price,
            # Kraken reports volume in base units for one venue; convert to USD
            # so the field carries the same unit as CoinGecko's aggregate.
            volume_24h=base_volume * price if base_volume is not None else None,
            raw_data=payload,
        )
```

- [ ] **Step 4: Export it**

In `src/finwiz/data/adapters/crypto/__init__.py`, add the import and the
`__all__` entry:

```python
from finwiz.data.adapters.crypto.kraken_adapter import KrakenAdapter
```

`__all__` becomes:

```python
__all__ = [
    "BaseCryptoAdapter",
    "CoinGeckoAdapter",
    "CryptoMarketData",
    "KrakenAdapter",
    "normalize_crypto_symbol",
    "positive_or_none",
]
```

- [ ] **Step 5: Write the integration test**

Create `tests/integration/test_kraken_adapter_live.py`. It is the only test in
this plan that touches the network, so it carries the `integration` marker and
is excluded from the default `make test` run.

```python
"""Live check that the Kraken public endpoint still answers for our pairs."""

import pytest

from finwiz.data.adapters.crypto.kraken_adapter import KrakenAdapter

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("ticker", ["BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD"])
def test_public_endpoint_answers_for_portfolio_pairs(ticker):
    result = KrakenAdapter().fetch(ticker)

    assert result is not None, f"Kraken no longer resolves {ticker}"
    assert result.price is not None
    assert result.price > 0
    assert result.market_cap is None, "Kraken never reports market cap"
```

- [ ] **Step 6: Run both suites to verify they pass**

Run: `uv run pytest tests/unit/data/adapters/crypto/ -v`
Expected: PASS, 22 tests

Run: `uv run pytest tests/integration/test_kraken_adapter_live.py -v -m integration`
Expected: PASS, 4 tests. This one needs network access; if it cannot reach
`api.kraken.com`, report that rather than deleting the test.

- [ ] **Step 7: Lint and commit**

```bash
make lint
git add src/finwiz/data/adapters/crypto/ tests/unit/data/adapters/crypto/ tests/integration/test_kraken_adapter_live.py
git commit -m "feat(data): Kraken crypto adapter"
```

---

### Task 3: CryptoSourceOrchestrator

**Files:**

- Create: `src/finwiz/data/crypto_source_orchestrator.py`
- Test: `tests/unit/data/test_crypto_source_orchestrator.py`

**Interfaces:**

- Consumes: `CoinGeckoAdapter`, `KrakenAdapter`, `CryptoMarketData` from
  Tasks 1-2.
- Produces:
  - `CryptoLineage` dataclass: `price_source: str | None`,
    `market_cap_source: str | None`, `volume_24h_source: str | None`,
    `supply_source: str | None`.
  - `CryptoOrchestrationResult` dataclass: `ticker: str`, `timestamp: datetime`,
    `price / market_cap / volume_24h / circulating_supply / max_supply:
    float | None`, `lineage: CryptoLineage`, `confidence: float`,
    `sources_attempted / sources_succeeded / sources_failed: list[str]`,
    `warnings: list[str]`, `price_divergence_pct: float | None`.
  - `CryptoSourceOrchestrator(coingecko=None, kraken=None)` with
    `fetch(self, ticker: str, *, yfinance_price: float | None = None) -> CryptoOrchestrationResult`.
  - Module constant `DIVERGENCE_WARN_PCT = 2.0`.

**The rules this task implements, verbatim from the spec:**

- Price value: CoinGecko if present; else `yfinance_price`; else Kraken.
- Disagreement never changes the value. It only warns and lowers confidence.
- `price_divergence_pct = (max - min) / min * 100` over the prices actually
  obtained, `None` when fewer than two are available.
- `market_cap`, `circulating_supply`, `max_supply` are CoinGecko-only; `None`
  when CoinGecko failed. No second source, nothing invented.
- `volume_24h`: CoinGecko when available, otherwise Kraken's, whose lineage
  reads `"kraken:single-venue"`.
- Confidence: 1.0 for a CoinGecko price, 0.8 for the yfinance fallback, 0.6 for
  the Kraken fallback, 0.0 when no source answered; minus 0.2 when divergence
  exceeds `DIVERGENCE_WARN_PCT`; minus 0.1 for each of market cap, volume and
  supply left unresolved; floored at 0.0. Supply counts as unresolved when
  `circulating_supply is None` — a `None` `max_supply` means uncapped, which is
  a fact, not a gap.
- Kraken is attempted on every fetch, so the cross-check exists even when
  CoinGecko succeeds.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/data/test_crypto_source_orchestrator.py`:

```python
"""Tests for the crypto multi-source orchestrator."""

from datetime import datetime

import pytest

from finwiz.data.adapters.crypto.base import CryptoMarketData
from finwiz.data.crypto_source_orchestrator import CryptoSourceOrchestrator


class _StubAdapter:
    """Returns a canned CryptoMarketData (or None) and records its calls."""

    def __init__(self, name, result):
        self._name = name
        self._result = result
        self.calls = []

    @property
    def source_name(self):
        return self._name

    def fetch(self, ticker):
        self.calls.append(ticker)
        return self._result


def _coingecko_data(price=81114.0, market_cap=1629408510367.0, volume=23900006504.0, circulating=20087096.0, max_supply=21000000.0):
    return CryptoMarketData(
        ticker="BTC-USD",
        source="coingecko",
        timestamp=datetime.now(),
        confidence=1.0,
        price=price,
        market_cap=market_cap,
        volume_24h=volume,
        circulating_supply=circulating,
        max_supply=max_supply,
    )


def _kraken_data(price=81121.4, volume=150074590.0):
    return CryptoMarketData(
        ticker="BTC-USD",
        source="kraken",
        timestamp=datetime.now(),
        confidence=1.0,
        price=price,
        volume_24h=volume,
    )


def _orchestrator(coingecko_result, kraken_result):
    return CryptoSourceOrchestrator(
        coingecko=_StubAdapter("coingecko", coingecko_result),
        kraken=_StubAdapter("kraken", kraken_result),
    )


def test_happy_path_uses_coingecko_for_every_field():
    result = _orchestrator(_coingecko_data(), _kraken_data()).fetch("BTC-USD", yfinance_price=81061.41)

    assert result.price == 81114.0
    assert result.market_cap == 1629408510367.0
    assert result.volume_24h == 23900006504.0
    assert result.circulating_supply == 20087096.0
    assert result.max_supply == 21000000.0
    assert result.lineage.price_source == "coingecko"
    assert result.lineage.market_cap_source == "coingecko"
    assert result.lineage.volume_24h_source == "coingecko"
    assert result.lineage.supply_source == "coingecko"
    assert result.confidence == pytest.approx(1.0)


def test_kraken_is_always_consulted_even_when_coingecko_succeeds():
    kraken = _StubAdapter("kraken", _kraken_data())
    orchestrator = CryptoSourceOrchestrator(coingecko=_StubAdapter("coingecko", _coingecko_data()), kraken=kraken)

    orchestrator.fetch("BTC-USD", yfinance_price=81061.41)

    assert kraken.calls == ["BTC-USD"], "the cross-check must run even on the happy path"


def test_disagreement_never_changes_the_value():
    # Kraken is 10% away; the primary still wins.
    result = _orchestrator(_coingecko_data(price=81114.0), _kraken_data(price=89225.4)).fetch("BTC-USD")

    assert result.price == 81114.0
    assert result.lineage.price_source == "coingecko"
    assert result.price_divergence_pct == pytest.approx(10.0, abs=0.01)
    assert any("divergence" in warning.lower() for warning in result.warnings)


def test_divergence_below_threshold_raises_no_warning():
    result = _orchestrator(_coingecko_data(price=81114.0), _kraken_data(price=81121.4)).fetch("BTC-USD")

    assert result.price_divergence_pct == pytest.approx(0.009, abs=0.01)
    assert result.warnings == []
    assert result.confidence == pytest.approx(1.0)


def test_price_divergence_is_none_with_a_single_source():
    result = _orchestrator(_coingecko_data(), None).fetch("BTC-USD")

    assert result.price_divergence_pct is None


def test_fallback_order_is_yfinance_then_kraken():
    result = _orchestrator(None, _kraken_data(price=81121.4)).fetch("BTC-USD", yfinance_price=81061.41)

    assert result.price == 81061.41
    assert result.lineage.price_source == "yfinance"


def test_kraken_is_the_last_resort_price():
    result = _orchestrator(None, _kraken_data(price=81121.4)).fetch("BTC-USD", yfinance_price=None)

    assert result.price == 81121.4
    assert result.lineage.price_source == "kraken"


def test_market_cap_and_supply_stay_none_when_coingecko_fails():
    result = _orchestrator(None, _kraken_data()).fetch("BTC-USD", yfinance_price=81061.41)

    assert result.market_cap is None
    assert result.circulating_supply is None
    assert result.max_supply is None
    assert result.lineage.market_cap_source is None
    assert result.lineage.supply_source is None


def test_kraken_volume_is_marked_single_venue():
    result = _orchestrator(None, _kraken_data(volume=150074590.0)).fetch("BTC-USD", yfinance_price=81061.41)

    assert result.volume_24h == 150074590.0
    assert result.lineage.volume_24h_source == "kraken:single-venue"


def test_every_source_failing_yields_all_none():
    result = _orchestrator(None, None).fetch("BTC-USD", yfinance_price=None)

    assert result.price is None
    assert result.market_cap is None
    assert result.volume_24h is None
    assert result.circulating_supply is None
    assert result.confidence == 0.0
    assert sorted(result.sources_failed) == ["coingecko", "kraken"]
    assert sorted(result.sources_attempted) == ["coingecko", "kraken"]
    assert result.sources_succeeded == []


def test_confidence_drops_for_each_unresolved_group():
    # yfinance price (0.8), no market cap, no volume, no supply: 0.8 - 0.3
    result = _orchestrator(None, None).fetch("BTC-USD", yfinance_price=81061.41)

    assert result.lineage.price_source == "yfinance"
    assert result.confidence == pytest.approx(0.5)


def test_uncapped_supply_does_not_count_as_a_gap():
    capped = _orchestrator(_coingecko_data(), _kraken_data()).fetch("BTC-USD")
    uncapped = _orchestrator(_coingecko_data(max_supply=None), _kraken_data()).fetch("ETH-USD")

    assert uncapped.max_supply is None
    assert uncapped.confidence == pytest.approx(capped.confidence), "no cap is a fact, not missing data"


def test_divergence_penalty_applies_to_confidence():
    result = _orchestrator(_coingecko_data(price=81114.0), _kraken_data(price=89225.4)).fetch("BTC-USD")

    assert result.confidence == pytest.approx(0.8)


def test_confidence_never_goes_below_zero():
    result = _orchestrator(None, _kraken_data(price=1.0, volume=None)).fetch("BTC-USD", yfinance_price=2.0)

    assert result.confidence >= 0.0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/data/test_crypto_source_orchestrator.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'finwiz.data.crypto_source_orchestrator'`

- [ ] **Step 3: Write the orchestrator**

Create `src/finwiz/data/crypto_source_orchestrator.py`:

```python
"""Multi-source acquisition of crypto market data.

Mirrors the contract of `DataSourceOrchestrator` (per-field lineage, pinned
confidence, None for anything unresolved) without reusing `FundamentalData`,
which is hardwired to equity metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime

from finwiz.data.adapters.crypto.base import BaseCryptoAdapter, CryptoMarketData
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

DIVERGENCE_WARN_PCT = 2.0

_PRICE_CONFIDENCE = {"coingecko": 1.0, "yfinance": 0.8, "kraken": 0.6}
_DIVERGENCE_PENALTY = 0.2
_UNRESOLVED_PENALTY = 0.1


@dataclass
class CryptoLineage:
    """Records which source supplied each field."""

    price_source: str | None = None
    market_cap_source: str | None = None
    volume_24h_source: str | None = None
    supply_source: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        """Convert to a dictionary for logging and export."""
        return {
            "price": self.price_source,
            "market_cap": self.market_cap_source,
            "volume_24h": self.volume_24h_source,
            "supply": self.supply_source,
        }


@dataclass
class CryptoOrchestrationResult:
    """Resolved crypto market data plus the provenance of every field."""

    ticker: str
    timestamp: datetime
    price: float | None = None
    market_cap: float | None = None
    volume_24h: float | None = None
    circulating_supply: float | None = None
    max_supply: float | None = None
    lineage: CryptoLineage = field(default_factory=CryptoLineage)
    confidence: float = 0.0
    sources_attempted: list[str] = field(default_factory=list)
    sources_succeeded: list[str] = field(default_factory=list)
    sources_failed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    price_divergence_pct: float | None = None


class CryptoSourceOrchestrator:
    """Resolves crypto market data across CoinGecko, yfinance and Kraken."""

    def __init__(self, coingecko: BaseCryptoAdapter | None = None, kraken: BaseCryptoAdapter | None = None) -> None:
        """Wire the adapters, constructed lazily so tests can inject stubs."""
        if coingecko is None:
            from finwiz.data.adapters.crypto.coingecko_adapter import CoinGeckoAdapter

            coingecko = CoinGeckoAdapter()
        if kraken is None:
            from finwiz.data.adapters.crypto.kraken_adapter import KrakenAdapter

            kraken = KrakenAdapter()
        self._coingecko = coingecko
        self._kraken = kraken

    def fetch(self, ticker: str, *, yfinance_price: float | None = None) -> CryptoOrchestrationResult:
        """Resolve every crypto field for one ticker, leaving gaps as None."""
        result = CryptoOrchestrationResult(ticker=ticker, timestamp=datetime.now())

        gecko = self._attempt(self._coingecko, ticker, result)
        # Kraken runs on every fetch: it is the cross-check when CoinGecko
        # answered, and a price candidate when it did not.
        kraken = self._attempt(self._kraken, ticker, result)

        self._resolve_price(result, gecko, kraken, yfinance_price)
        self._resolve_market_data(result, gecko, kraken)
        result.confidence = self._compute_confidence(result)

        logger.info(
            "Crypto sources for %s: price=%s lineage=%s confidence=%.2f divergence=%s",
            ticker,
            result.price,
            result.lineage.to_dict(),
            result.confidence,
            result.price_divergence_pct,
        )
        return result

    def _attempt(self, adapter: BaseCryptoAdapter, ticker: str, result: CryptoOrchestrationResult) -> CryptoMarketData | None:
        """Run one adapter, recording the attempt on the result."""
        name = adapter.source_name
        result.sources_attempted.append(name)
        data = adapter.fetch(ticker)
        if data is None:
            result.sources_failed.append(name)
        else:
            result.sources_succeeded.append(name)
        return data

    def _resolve_price(
        self,
        result: CryptoOrchestrationResult,
        gecko: CryptoMarketData | None,
        kraken: CryptoMarketData | None,
        yfinance_price: float | None,
    ) -> None:
        """Pick the price by fallback order, then observe the disagreement."""
        candidates: dict[str, float] = {}
        if gecko is not None and gecko.price is not None:
            candidates["coingecko"] = gecko.price
        if yfinance_price is not None and yfinance_price > 0:
            candidates["yfinance"] = float(yfinance_price)
        if kraken is not None and kraken.price is not None:
            candidates["kraken"] = kraken.price

        for source in ("coingecko", "yfinance", "kraken"):
            if source in candidates:
                result.price = candidates[source]
                result.lineage.price_source = source
                break

        if len(candidates) >= 2:
            values = list(candidates.values())
            low, high = min(values), max(values)
            result.price_divergence_pct = (high - low) / low * 100.0
            if result.price_divergence_pct > DIVERGENCE_WARN_PCT:
                message = f"Price divergence {result.price_divergence_pct:.2f}% across {sorted(candidates)}; keeping {result.lineage.price_source}"
                result.warnings.append(message)
                logger.warning("%s for %s", message, result.ticker)

    def _resolve_market_data(self, result: CryptoOrchestrationResult, gecko: CryptoMarketData | None, kraken: CryptoMarketData | None) -> None:
        """Fill market cap, supply and volume; leave gaps as None."""
        if gecko is not None:
            if gecko.market_cap is not None:
                result.market_cap = gecko.market_cap
                result.lineage.market_cap_source = "coingecko"
            if gecko.circulating_supply is not None:
                result.circulating_supply = gecko.circulating_supply
                result.max_supply = gecko.max_supply
                result.lineage.supply_source = "coingecko"
            if gecko.volume_24h is not None:
                result.volume_24h = gecko.volume_24h
                result.lineage.volume_24h_source = "coingecko"

        if result.volume_24h is None and kraken is not None and kraken.volume_24h is not None:
            # One venue in USD, not the all-venue aggregate CoinGecko reports.
            # Never cross-checked against CoinGecko's figure: they do not
            # measure the same thing.
            result.volume_24h = kraken.volume_24h
            result.lineage.volume_24h_source = "kraken:single-venue"

    def _compute_confidence(self, result: CryptoOrchestrationResult) -> float:
        """Score confidence from the price provenance and the remaining gaps."""
        confidence = _PRICE_CONFIDENCE.get(result.lineage.price_source or "", 0.0)
        if confidence == 0.0:
            return 0.0

        if result.price_divergence_pct is not None and result.price_divergence_pct > DIVERGENCE_WARN_PCT:
            confidence -= _DIVERGENCE_PENALTY

        # max_supply is deliberately excluded: None there means uncapped.
        for value in (result.market_cap, result.volume_24h, result.circulating_supply):
            if value is None:
                confidence -= _UNRESOLVED_PENALTY

        return max(0.0, round(confidence, 4))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/unit/data/test_crypto_source_orchestrator.py -v`
Expected: PASS, 14 tests

- [ ] **Step 5: Lint and commit**

```bash
make lint
git add src/finwiz/data/crypto_source_orchestrator.py tests/unit/data/test_crypto_source_orchestrator.py
git commit -m "feat(data): crypto source orchestrator with lineage and pinned confidence"
```

---

### Task 4: Crypto scorer renormalizes over available components

**Files:**

- Modify: `src/finwiz/scoring/asset_analyzers/crypto_analyzer.py:38-88`
  (`calculate_fundamental_score`)
- Modify: `src/finwiz/scoring/deep_analysis_scorer.py:263-290`
  (`_compute_weighted_score`)
- Test: `tests/unit/scoring/asset_analyzers/test_crypto_analyzer.py`

**Interfaces:**

- Consumes: nothing from earlier tasks.
- Produces: `CryptoAnalyzer.calculate_fundamental_score(data) -> tuple[float | None, dict[str, Any]]`.
  The details dict gains `excluded_components: list[str]` and
  `effective_weights: dict[str, float]`.

**Why this task exists:** `_safe_get_float(data, "market_cap", 0.0)` maps `None`
to `0.0`, and `_score_market_cap(0.0)` returns `0.2`. So once the collector
starts writing honest `None`s, a missing market cap would score as the worst
possible market cap — replacing a falsely good score with a falsely
catastrophic one. The component must be dropped and the remaining weights
renormalized instead.

**Weight table (unchanged when everything is present):** market cap 0.40,
volume 0.30, age 0.20, supply 0.10.

**Supply has a subtlety:** the component is available when
`circulating_supply` is not `None`. A `None` `max_supply` means the asset is
uncapped, which `_score_supply_metrics` already handles by returning the
neutral 0.5 when `max_supply <= 0` — so pass `0.0` for an absent cap, and keep
the component.

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/scoring/asset_analyzers/test_crypto_analyzer.py`:

```python
import pytest

from finwiz.scoring.asset_analyzers.crypto_analyzer import CryptoAnalyzer


def _full_data():
    return {
        "market_cap": 1629408510367.0,
        "volume_24h": 23900006504.0,
        "age_years": 17.0,
        "circulating_supply": 20087096.0,
        "max_supply": 21000000.0,
    }


class TestFundamentalScoreRenormalization:
    """Missing components are dropped, not scored as zero."""

    def test_all_components_present_uses_nominal_weights(self):
        score, details = CryptoAnalyzer().calculate_fundamental_score(_full_data())

        assert score == pytest.approx(1.0)
        assert details["excluded_components"] == []
        assert details["effective_weights"] == pytest.approx({"market_cap": 0.40, "volume": 0.30, "age": 0.20, "supply": 0.10})

    def test_missing_market_cap_is_excluded_not_scored_zero(self):
        data = _full_data()
        data["market_cap"] = None

        score, details = CryptoAnalyzer().calculate_fundamental_score(data)

        assert "market_cap" in details["excluded_components"]
        assert details["market_cap"] is None
        assert details["market_cap_score"] is None
        # The remaining 0.60 of weight renormalizes to 1.0, all components scoring 1.0
        assert score == pytest.approx(1.0)
        assert details["effective_weights"]["volume"] == pytest.approx(0.5)
        assert details["effective_weights"]["age"] == pytest.approx(1.0 / 3.0)
        assert details["effective_weights"]["supply"] == pytest.approx(1.0 / 6.0)

    def test_missing_market_cap_beats_a_fabricated_worst_case(self):
        data = _full_data()
        data["market_cap"] = None
        missing_score, _ = CryptoAnalyzer().calculate_fundamental_score(data)

        data["market_cap"] = 1.0  # a real but tiny market cap scores 0.2
        tiny_score, _ = CryptoAnalyzer().calculate_fundamental_score(data)

        assert missing_score > tiny_score, "absence must not be graded as the worst observed value"

    def test_every_component_missing_yields_none(self):
        score, details = CryptoAnalyzer().calculate_fundamental_score(
            {"market_cap": None, "volume_24h": None, "age_years": None, "circulating_supply": None, "max_supply": None}
        )

        assert score is None
        assert details["fundamental_score"] is None
        assert sorted(details["excluded_components"]) == ["age", "market_cap", "supply", "volume"]

    def test_absent_keys_count_as_missing(self):
        score, details = CryptoAnalyzer().calculate_fundamental_score({"age_years": 17.0})

        assert sorted(details["excluded_components"]) == ["market_cap", "supply", "volume"]
        assert score == pytest.approx(1.0)

    def test_uncapped_supply_keeps_the_component_with_a_neutral_score(self):
        data = _full_data()
        data["max_supply"] = None

        score, details = CryptoAnalyzer().calculate_fundamental_score(data)

        assert "supply" not in details["excluded_components"]
        assert details["supply_score"] == pytest.approx(0.5)
        assert score == pytest.approx(0.95)
```

Create `tests/unit/scoring/test_composite_with_missing_fundamental.py`:

```python
"""The composite score tolerates a fundamental score that could not be computed."""

import pytest

from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer


@pytest.fixture
def scorer(mocker):
    """A scorer whose additive overlays are neutralized.

    _compute_weighted_score applies a sentiment and a macro overlay after the
    composite. Both are gated on feature flags and can read real data, so they
    are stubbed to keep this test about the weighting alone.
    """
    instance = DeepAnalysisScorer()
    mocker.patch.object(instance, "_calculate_sentiment_overlay", return_value=(0.0, {"sentiment_overlay_applied": False}))
    mocker.patch.object(instance, "_calculate_macro_overlay", return_value=(0.0, {"macro_overlay_applied": False}))
    return instance


def test_composite_renormalizes_when_fundamental_is_none(scorer):
    scores = {"fundamental_score": None, "fundamental_details": {}, "technical_score": 0.8, "risk_score": 0.6}

    composite = scorer._compute_weighted_score(scores, {"asset_class": "crypto"})

    # technical 0.30 and risk 0.30 renormalize to 0.5 each: 0.5*0.8 + 0.5*0.6
    assert composite == pytest.approx(0.7)
    assert scores["weights_used"]["fundamental"] == 0.0


def test_composite_is_unchanged_when_fundamental_is_present(scorer):
    scores = {"fundamental_score": 0.9, "fundamental_details": {}, "technical_score": 0.8, "risk_score": 0.6}

    composite = scorer._compute_weighted_score(scores, {"asset_class": "crypto"})

    assert composite == pytest.approx(0.4 * 0.9 + 0.3 * 0.8 + 0.3 * 0.6)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/scoring/asset_analyzers/test_crypto_analyzer.py tests/unit/scoring/test_composite_with_missing_fundamental.py -v`
Expected: FAIL — `KeyError: 'excluded_components'` in the analyzer tests, and
`TypeError: unsupported operand type(s) for *: 'float' and 'NoneType'` in the
composite test.

- [ ] **Step 3: Rewrite `calculate_fundamental_score`**

Replace the body of `calculate_fundamental_score` in
`src/finwiz/scoring/asset_analyzers/crypto_analyzer.py`:

```python
    def calculate_fundamental_score(self, data: dict[str, Any]) -> tuple[float | None, dict[str, Any]]:
        """
        Calculate fundamental score for cryptocurrencies.

        Nominal weights: market cap 40%, volume 30%, age 20%, supply 10%.
        A component whose source data is missing is excluded and the remaining
        weights are renormalized, so absence never scores as the worst observed
        value. Returns None when no component survived.

        Args:
            data: Dictionary containing crypto analysis data

        Returns:
            Tuple of (score or None, details_dict)

        """
        details: dict[str, Any] = {}
        components: list[tuple[str, float, float]] = []
        excluded: list[str] = []

        market_cap = _optional_float(data.get("market_cap"))
        details["market_cap"] = market_cap
        if market_cap is None:
            details["market_cap_score"] = None
            excluded.append("market_cap")
        else:
            details["market_cap_score"] = self._score_market_cap(market_cap)
            components.append(("market_cap", 0.40, details["market_cap_score"]))

        volume_24h = _optional_float(data.get("volume_24h"))
        details["volume_24h"] = volume_24h
        if volume_24h is None:
            details["volume_score"] = None
            excluded.append("volume")
        else:
            details["volume_score"] = self._score_volume(volume_24h)
            components.append(("volume", 0.30, details["volume_score"]))

        age_years = _optional_float(data.get("age_years"))
        details["age_years"] = age_years
        if age_years is None:
            details["age_score"] = None
            excluded.append("age")
        else:
            details["age_score"] = self._score_age(age_years)
            components.append(("age", 0.20, details["age_score"]))

        circulating_supply = _optional_float(data.get("circulating_supply"))
        max_supply = _optional_float(data.get("max_supply"))
        details["circulating_supply"] = circulating_supply
        details["max_supply"] = max_supply
        if circulating_supply is None:
            details["supply_score"] = None
            excluded.append("supply")
        else:
            # A None max_supply means uncapped, which _score_supply_metrics
            # already treats as neutral via its `max_supply <= 0` branch.
            details["supply_score"] = self._score_supply_metrics(circulating_supply, max_supply or 0.0)
            components.append(("supply", 0.10, details["supply_score"]))

        details["excluded_components"] = excluded

        if not components:
            details["effective_weights"] = {}
            details["fundamental_score"] = None
            self.logger.warning("No crypto fundamental component available; score is None rather than 0.0")
            return None, details

        total_weight = sum(weight for _, weight, _ in components)
        details["effective_weights"] = {name: weight / total_weight for name, weight, _ in components}
        fundamental_score = sum(weight * score for _, weight, score in components) / total_weight

        details["fundamental_score"] = fundamental_score
        return fundamental_score, details
```

Add this module-level helper to the same file, just below the imports:

```python
def _optional_float(value: Any) -> float | None:
    """Coerce to float, mapping missing or unparsable values to None.

    Deliberately NOT `_safe_get_float`: that one substitutes a default, which
    turns a missing measurement into the worst possible measurement.
    """
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
```

- [ ] **Step 4: Teach the composite score about a None fundamental**

In `src/finwiz/scoring/deep_analysis_scorer.py:_compute_weighted_score`, replace
the `is_quality_company` assignment and the composite calculation.

Replace:

```text
is_quality_company = self.result_builder.is_quality_company(fundamental_score, fundamental_details)
```

with:

```python
        is_quality_company = False if fundamental_score is None else self.result_builder.is_quality_company(fundamental_score, fundamental_details)
```

Replace:

```text
composite_score = weight_fundamental * scores["fundamental_score"] + weight_technical * scores["technical_score"] + weight_risk * scores["risk_score"]
```

with:

```python
        if fundamental_score is None:
            # No fundamental component survived. Renormalize over the
            # components that exist rather than scoring the gap as a zero.
            remaining = weight_technical + weight_risk
            composite_score = (weight_technical * scores["technical_score"] + weight_risk * scores["risk_score"]) / remaining
            weight_fundamental = 0.0
            self.logger.warning("Fundamental score unavailable; composite renormalized over technical and risk only")
        else:
            composite_score = weight_fundamental * fundamental_score + weight_technical * scores["technical_score"] + weight_risk * scores["risk_score"]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/unit/scoring/asset_analyzers/test_crypto_analyzer.py tests/unit/scoring/test_composite_with_missing_fundamental.py -v`
Expected: PASS

- [ ] **Step 6: Run the wider scoring suite for regressions**

Run: `uv run pytest tests/unit/scoring/ -q`
Expected: PASS. If an existing test asserted a crypto fundamental score built on
`0.0` defaults, update that test — the new behavior is the intended one — and
say so in the commit body.

- [ ] **Step 7: Lint and commit**

```bash
make lint
git add src/finwiz/scoring/asset_analyzers/crypto_analyzer.py src/finwiz/scoring/deep_analysis_scorer.py tests/unit/scoring/
git commit -m "fix(scoring): renormalize crypto weights instead of scoring missing data as zero"
```

---

### Task 5: Genesis-year table

**Files:**

- Create: `src/finwiz/data/adapters/crypto/genesis.py`
- Modify: `src/finwiz/data/adapters/crypto/__init__.py` (export both names)
- Test: `tests/unit/data/adapters/crypto/test_genesis.py`

**Interfaces:**

- Consumes: `normalize_crypto_symbol` from Task 1.
- Produces: `CRYPTO_GENESIS_YEAR: dict[str, int]` and
  `crypto_age_years(ticker: str, *, today: date | None = None) -> float | None`.

**Why a table:** genesis dates are immutable facts, so rediscovering them over
the network every run buys nothing. The repo already carries a curated
expense-ratio table for ETFs on the same reasoning. The bug being fixed is not
the table but its two defects: it stored *ages* (`BTC: 15.0`), which rot every
year, and it defaulted an unlisted symbol to `3.0` — which is why XRP, live
since 2012, is currently scored as three years old.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/data/adapters/crypto/test_genesis.py`:

```python
"""Tests for the curated crypto genesis-year table."""

from datetime import date

import pytest

from finwiz.data.adapters.crypto.genesis import CRYPTO_GENESIS_YEAR, crypto_age_years


def test_known_symbol_age_is_derived_from_the_run_date():
    assert crypto_age_years("BTC", today=date(2026, 9, 20)) == pytest.approx(17.0)


def test_age_advances_with_the_calendar():
    assert crypto_age_years("BTC", today=date(2027, 9, 20)) == pytest.approx(18.0)


def test_usd_suffix_is_normalized():
    assert crypto_age_years("BTC-USD", today=date(2026, 9, 20)) == pytest.approx(17.0)


def test_xrp_is_not_three_years_old():
    age = crypto_age_years("XRP-USD", today=date(2026, 9, 20))

    assert age == pytest.approx(14.0), "XRP has been live since 2012"


def test_unknown_symbol_is_none_never_a_default():
    assert crypto_age_years("DOGE-USD", today=date(2026, 9, 20)) is None


@pytest.mark.parametrize(("symbol", "year"), [("BTC", 2009), ("ETH", 2015), ("XRP", 2012), ("SOL", 2020)])
def test_portfolio_holdings_are_covered(symbol, year):
    assert CRYPTO_GENESIS_YEAR[symbol] == year


def test_table_keys_are_bare_upper_case_symbols():
    for symbol in CRYPTO_GENESIS_YEAR:
        assert symbol == symbol.upper()
        assert "-" not in symbol
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/data/adapters/crypto/test_genesis.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'finwiz.data.adapters.crypto.genesis'`

- [ ] **Step 3: Write the table**

Create `src/finwiz/data/adapters/crypto/genesis.py`:

```python
"""Curated crypto genesis years.

Genesis dates are immutable, so they are curated here rather than fetched: the
same reasoning as the curated ETF expense-ratio table. Years, not ages — an age
constant is wrong again every January. An unlisted symbol yields None, never a
default: a guessed age silently feeds 20% of the crypto fundamental score.
"""

from datetime import date

from finwiz.data.adapters.crypto.base import normalize_crypto_symbol

CRYPTO_GENESIS_YEAR: dict[str, int] = {
    "ADA": 2017,
    "AVAX": 2020,
    "BTC": 2009,
    "DOT": 2020,
    "ETH": 2015,
    "LINK": 2017,
    "LTC": 2011,
    "SOL": 2020,
    "XRP": 2012,
}


def crypto_age_years(ticker: str, *, today: date | None = None) -> float | None:
    """Return the asset's age in whole years, or None when it is not curated."""
    symbol = normalize_crypto_symbol(ticker)
    genesis_year = CRYPTO_GENESIS_YEAR.get(symbol)
    if genesis_year is None:
        return None
    reference = today or date.today()
    return float(reference.year - genesis_year)
```

- [ ] **Step 4: Export it**

In `src/finwiz/data/adapters/crypto/__init__.py`, add:

```python
from finwiz.data.adapters.crypto.genesis import CRYPTO_GENESIS_YEAR, crypto_age_years
```

and add `"CRYPTO_GENESIS_YEAR"` and `"crypto_age_years"` to `__all__`, keeping
the list alphabetically sorted.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/unit/data/adapters/crypto/test_genesis.py -v`
Expected: PASS, 11 tests

- [ ] **Step 6: Lint and commit**

```bash
make lint
git add src/finwiz/data/adapters/crypto/ tests/unit/data/adapters/crypto/test_genesis.py
git commit -m "feat(data): curated crypto genesis years replacing the rotting age table"
```

---

### Task 6: Wire the orchestrator into the collector

**Files:**

- Modify: `src/finwiz/orchestrators/deep_analysis_data_collector.py:141-212`
  (`_collect_asset_specific_data` crypto branch and `_collect_crypto_data`)
- Modify: `src/finwiz/scoring/crew_export_generator.py:281-293`
  (`_identify_missing_fields`)
- Test: `tests/unit/orchestrators/test_crypto_data_collection.py`

**Interfaces:**

- Consumes: `CryptoSourceOrchestrator` and `CryptoOrchestrationResult` (Task 3),
  `crypto_age_years` (Task 5).
- Produces: `collected_data` keys `market_cap`, `volume_24h`, `age_years`,
  `circulating_supply`, `max_supply` — each `float | None` — plus
  `crypto_info` carrying `lineage`, `confidence`, `sources_succeeded`,
  `sources_failed`, `warnings`, `price_divergence_pct`.

**The three fabrication sites this task deletes:** lines 153-155 (the `except`
branch of `_collect_asset_specific_data`), line 182 (`market_cap_raw if
market_cap_raw > 0 else 10e9`), and lines 208-210 (the non-dict branch). None of
their values may survive anywhere.

**`_identify_missing_fields` already counts `None` as missing**, so writing
`None` makes `data_quality.missing_fields` truthful for `volume_24h` with no
further work. `market_cap` is absent from its `key_fields` list and must be
added for the crypto branch, otherwise a missing market cap still goes
unreported.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/orchestrators/test_crypto_data_collection.py`:

```python
"""The crypto collection path reports real data or nothing — never a stand-in."""

from datetime import date, datetime

import pytest

from finwiz.data.crypto_source_orchestrator import CryptoLineage, CryptoOrchestrationResult
from finwiz.orchestrators.deep_analysis_data_collector import DeepAnalysisDataCollector
from finwiz.scoring.crew_export_generator import CrewExportGenerator

FABRICATED_VALUES = {1e9, 10e9, 100e9, 3.0, 5.0}


class _FakeState:
    full_date = "2026-09-20"


def _collector(mocker):
    mocker.patch("finwiz.data.data_source_orchestrator.DataSourceOrchestrator", autospec=True)
    return DeepAnalysisDataCollector(_FakeState())


def _resolved():
    return CryptoOrchestrationResult(
        ticker="BTC-USD",
        timestamp=datetime.now(),
        price=81114.0,
        market_cap=1629408510367.0,
        volume_24h=23900006504.0,
        circulating_supply=20087096.0,
        max_supply=21000000.0,
        lineage=CryptoLineage(price_source="coingecko", market_cap_source="coingecko", volume_24h_source="coingecko", supply_source="coingecko"),
        confidence=1.0,
        sources_succeeded=["coingecko", "kraken"],
    )


def _empty():
    return CryptoOrchestrationResult(ticker="BTC-USD", timestamp=datetime.now(), confidence=0.0, sources_failed=["coingecko", "kraken"])


def test_resolved_data_reaches_collected_data(mocker):
    collector = _collector(mocker)
    mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.return_value": _resolved()}, create=True)

    result = collector._collect_crypto_data("BTC-USD", {"current_price": 81061.41})

    assert result["market_cap"] == 1629408510367.0
    assert result["volume_24h"] == 23900006504.0
    assert result["circulating_supply"] == 20087096.0
    assert result["max_supply"] == 21000000.0


def test_unresolved_fields_are_none_not_fabricated(mocker):
    collector = _collector(mocker)
    mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.return_value": _empty()}, create=True)

    result = collector._collect_crypto_data("BTC-USD", {})

    assert result["market_cap"] is None
    assert result["volume_24h"] is None
    assert result["circulating_supply"] is None
    for key in ("market_cap", "volume_24h", "age_years"):
        assert result[key] not in FABRICATED_VALUES


def test_age_comes_from_the_curated_table(mocker):
    collector = _collector(mocker)
    mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.return_value": _resolved()}, create=True)
    mocker.patch("finwiz.orchestrators.deep_analysis_data_collector.crypto_age_years", return_value=17.0)

    result = collector._collect_crypto_data("BTC-USD", {})

    assert result["age_years"] == 17.0


def test_uncurated_symbol_has_no_age(mocker):
    collector = _collector(mocker)
    mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.return_value": _resolved()}, create=True)
    mocker.patch("finwiz.orchestrators.deep_analysis_data_collector.crypto_age_years", return_value=None)

    result = collector._collect_crypto_data("DOGE-USD", {})

    assert result["age_years"] is None


def test_yfinance_price_is_handed_to_the_orchestrator(mocker):
    collector = _collector(mocker)
    fake = mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.return_value": _resolved()}, create=True)

    collector._collect_crypto_data("BTC-USD", {"current_price": 81061.41})

    fake.fetch.assert_called_once_with("BTC-USD", yfinance_price=81061.41)


def test_lineage_and_confidence_are_carried_for_the_report(mocker):
    collector = _collector(mocker)
    mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.return_value": _resolved()}, create=True)

    result = collector._collect_crypto_data("BTC-USD", {})

    assert result["crypto_info"]["confidence"] == 1.0
    assert result["crypto_info"]["lineage"]["market_cap"] == "coingecko"


def test_orchestrator_failure_does_not_crash_the_holding(mocker):
    collector = _collector(mocker)
    mocker.patch.object(collector, "_crypto_orchestrator", **{"fetch.side_effect": RuntimeError("boom")}, create=True)

    result = collector._collect_crypto_data("BTC-USD", {})

    assert result["market_cap"] is None
    assert result["volume_24h"] is None


def test_missing_market_cap_is_reported_for_crypto():
    generator = CrewExportGenerator()

    missing = generator._identify_missing_fields({"asset_class": "crypto", "current_price": 81114.0, "market_cap": None, "volume_24h": 1.0})

    assert "market_cap" in missing


def test_market_cap_is_not_demanded_of_equities():
    generator = CrewExportGenerator()

    missing = generator._identify_missing_fields({"asset_class": "stock", "current_price": 100.0, "volume": 1.0})

    assert "market_cap" not in missing
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/orchestrators/test_crypto_data_collection.py -v`
Expected: FAIL — the collector still writes `10e9` and has no `_crypto_orchestrator`.

- [ ] **Step 3: Replace `_collect_crypto_data`**

In `src/finwiz/orchestrators/deep_analysis_data_collector.py`, add to the
imports at the top of the file:

```python
from finwiz.data.adapters.crypto.genesis import crypto_age_years
```

In `DeepAnalysisDataCollector.__init__`, after the `DataSourceOrchestrator`
block, add:

```python
        from finwiz.data.crypto_source_orchestrator import CryptoSourceOrchestrator

        self._crypto_orchestrator = CryptoSourceOrchestrator()
```

Replace the whole of `_collect_crypto_data` (lines 164-212):

```python
    def _collect_crypto_data(self, ticker: str, collected_data: dict[str, Any]) -> dict[str, Any]:
        """Collect crypto market data from CoinGecko, yfinance and Kraken.

        Anything no source could resolve stays None. It is never replaced by a
        plausible-looking constant: a fabricated market cap is indistinguishable
        from a real one downstream, and 80% of the crypto fundamental score is
        built from these fields.
        """
        self.logger.info(f"🐍 Resolving crypto market data for {ticker}")
        yfinance_price = collected_data.get("current_price")

        try:
            resolved = self._crypto_orchestrator.fetch(ticker, yfinance_price=yfinance_price)
        except Exception as e:
            self.logger.error(f"❌ Crypto source orchestration failed for {ticker}: {e}", exc_info=True)
            collected_data.update({"market_cap": None, "volume_24h": None, "circulating_supply": None, "max_supply": None, "age_years": crypto_age_years(ticker)})
            collected_data["crypto_info"] = {"error": str(e)}
            return collected_data

        collected_data["market_cap"] = resolved.market_cap
        collected_data["volume_24h"] = resolved.volume_24h
        collected_data["circulating_supply"] = resolved.circulating_supply
        collected_data["max_supply"] = resolved.max_supply
        collected_data["age_years"] = crypto_age_years(ticker)

        if resolved.price is not None:
            collected_data["current_price"] = resolved.price

        collected_data["crypto_info"] = {
            "lineage": resolved.lineage.to_dict(),
            "confidence": resolved.confidence,
            "sources_succeeded": resolved.sources_succeeded,
            "sources_failed": resolved.sources_failed,
            "warnings": resolved.warnings,
            "price_divergence_pct": resolved.price_divergence_pct,
        }

        self.logger.info(
            f"✅ Crypto data for {ticker}: market_cap={resolved.market_cap}, volume_24h={resolved.volume_24h}, "
            f"age_years={collected_data['age_years']}, confidence={resolved.confidence:.2f}"
        )
        return collected_data
```

- [ ] **Step 4: Delete the fabricated defaults in the `except` branch**

In `_collect_asset_specific_data`, replace the crypto arm of the exception
handler (lines 152-156):

```text
            if asset_class.lower() == "crypto":
                collected_data["volume_24h"] = 1e9
                collected_data["age_years"] = 3.0
                collected_data["market_cap"] = 10e9
                collected_data["crypto_info"] = {}
```

with:

```python
            if asset_class.lower() == "crypto":
                collected_data["volume_24h"] = None
                collected_data["age_years"] = None
                collected_data["market_cap"] = None
                collected_data["crypto_info"] = {}
```

- [ ] **Step 5: Report a missing crypto market cap**

In `src/finwiz/scoring/crew_export_generator.py`, replace `_identify_missing_fields`:

```python
    def _identify_missing_fields(self, data: dict[str, Any]) -> list[str]:
        """Identify missing or null fields in the data."""
        is_crypto = "crypto" in str(data.get("asset_class", ""))
        key_fields = [
            "current_price",
            "volatility",
            "rsi",
            "macd",
            "beta",
            "sentiment_score",
            "volume_24h" if is_crypto else "volume",
        ]
        if is_crypto:
            # 40% of the crypto fundamental score; its absence has to be visible.
            key_fields.append("market_cap")
        return [field for field in key_fields if field not in data or data[field] is None]
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/unit/orchestrators/test_crypto_data_collection.py -v`
Expected: PASS, 9 tests

- [ ] **Step 7: Prove no fabricated constant survives**

Run: `rg -n "1e9|10e9|100e9" src/finwiz/orchestrators/deep_analysis_data_collector.py`
Expected: no output.

- [ ] **Step 8: Lint and commit**

```bash
make lint
git add src/finwiz/orchestrators/deep_analysis_data_collector.py src/finwiz/scoring/crew_export_generator.py tests/unit/orchestrators/test_crypto_data_collection.py
git commit -m "fix(orchestrators): real crypto market data, None when unresolved"
```

---

### Task 7: portfolio_deep_analyzer stops fabricating

**Files:**

- Modify: `src/finwiz/scoring/portfolio_deep_analyzer.py:240-247`
- Test: `tests/unit/scoring/test_portfolio_deep_analyzer_crypto.py`

**Interfaces:**

- Consumes: nothing from earlier tasks.
- Produces: no new names; the crypto branch passes `None` through.

**The deliberate asymmetry with the ETF branch above it:** the ETF arm raises
`CriticalFieldError` when its critical fields are absent, which skips the
holding. This task adopts only the *no-fabricated-default* half of that rule.
Raising would skip the holding, and "fail the holding" is the option the
brainstorm considered and rejected. Removing the default is what stops the lie;
failing the holding is a separate policy this work does not take. The
renormalizing scorer from Task 4 grades whatever survives.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/scoring/test_portfolio_deep_analyzer_crypto.py`:

```python
"""The crypto branch passes gaps through instead of inventing values."""

import inspect

from finwiz.scoring import portfolio_deep_analyzer


def test_crypto_branch_has_no_fabricated_defaults():
    source = inspect.getsource(portfolio_deep_analyzer)
    crypto_branch = source.split('elif asset_class == "crypto":', 1)[1].split("# Log asset-specific data", 1)[0]

    for fabricated in ("100e9", "1e9", '"age_years": perf_dict.get("age_years", 5)'):
        assert fabricated not in crypto_branch, f"{fabricated} is a fabricated default"


def test_crypto_branch_reads_every_field_without_a_default():
    source = inspect.getsource(portfolio_deep_analyzer)
    crypto_branch = source.split('elif asset_class == "crypto":', 1)[1].split("# Log asset-specific data", 1)[0]

    for field in ("market_cap", "volume_24h", "age_years"):
        assert f'perf_dict.get("{field}")' in crypto_branch
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/unit/scoring/test_portfolio_deep_analyzer_crypto.py -v`
Expected: FAIL — `AssertionError: 100e9 is a fabricated default`

- [ ] **Step 3: Remove the defaults**

In `src/finwiz/scoring/portfolio_deep_analyzer.py`, replace:

```text
            elif asset_class == "crypto":
                data.update(
                    {
                        "market_cap": perf_dict.get("market_cap", 100e9),
                        "volume_24h": perf_dict.get("volume_24h", 1e9),
                        "age_years": perf_dict.get("age_years", 5),
                    }
                )
```

with:

```python
            elif asset_class == "crypto":
                # No defaults: a fabricated market cap is indistinguishable from
                # a real one downstream. Unlike the ETF branch above, absence
                # does not raise either — CryptoAnalyzer renormalizes its
                # weights over the components that survived.
                data.update(
                    {
                        "market_cap": perf_dict.get("market_cap"),
                        "volume_24h": perf_dict.get("volume_24h"),
                        "age_years": perf_dict.get("age_years"),
                    }
                )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/unit/scoring/test_portfolio_deep_analyzer_crypto.py -v`
Expected: PASS, 2 tests

- [ ] **Step 5: Run the full unit suite**

Run: `make test`
Expected: PASS. Update any test that asserted the old fabricated crypto
defaults, and name it in the commit body.

- [ ] **Step 6: Lint and commit**

```bash
make lint
git add src/finwiz/scoring/portfolio_deep_analyzer.py tests/unit/scoring/test_portfolio_deep_analyzer_crypto.py
git commit -m "fix(scoring): crypto branch stops fabricating market cap, volume and age"
```

---

### Task 8: Documentation and end-to-end verification

**Files:**

- Create: `docs/adr/ADR-014-crypto-market-data-sources.md`
- Modify: `CHANGELOG.md` (Unreleased)
- Modify: `src/finwiz/data/CLAUDE.md` (or create it if absent)
- Modify: `src/finwiz/orchestrators/CLAUDE.md`
- Modify: `src/finwiz/tools/CLAUDE.md`

**Interfaces:**

- Consumes: everything from Tasks 1-7.
- Produces: no code.

- [ ] **Step 1: Write the ADR**

Create `docs/adr/ADR-014-crypto-market-data-sources.md`:

```markdown
# ADR-014: Crypto market data from real sources, with honest degradation

**Status:** Accepted
**Date:** 2026-09-20
**Supersedes:** nothing. Complements ADR-012 (research provider).

## Context

`_collect_crypto_data` passed the yfinance-normalized ticker (`BTC-USD`) to
CoinGecko, which keys on the bare symbol. Every crypto lookup failed, and
`EnhancedCryptoAnalysisTool` returned invented numbers tagged
`sources == ["Fallback Data"]` rather than an error. The collector layered its
own defaults on top (`market_cap 10e9`, `volume_24h 1e9`, `age_years 3.0`).

The 2026-09-20 full run scored all four crypto holdings on a $10B market cap,
zero volume and zero supply. Those fields carry 80% of the crypto fundamental
score, so the four holdings scored almost identically regardless of what they
are. `data_quality.missing_fields` read `[]` because a fabricated value counts
as present.

## Decision

A dedicated `CryptoSourceOrchestrator` resolves crypto market data from a
CoinGecko adapter (primary), the already-fetched yfinance price, and a Kraken
adapter, recording per-field lineage and a pinned confidence.

- Unresolved fields stay `None` everywhere. No fabricated stand-ins.
- Sources that disagree do not arbitrate: the primary keeps the value, the
  divergence is recorded and confidence drops.
- Price falls back CoinGecko, then yfinance, then Kraken. Absence is not
  disagreement.
- Market cap and supply are CoinGecko-only; there is no second source and none
  is invented.
- Kraken's volume is single-venue and in base units; it is converted to USD and
  used only as a last resort, never cross-checked against CoinGecko's aggregate.
- `CryptoAnalyzer` renormalizes its weights over available components, so a
  missing value is excluded rather than scored as the worst observed value.
- Ages come from a curated genesis-year table; an uncurated symbol yields
  `None`, never a default.

## Consequences

- Crypto fundamental scores change materially. BTC moves from roughly 0.63 to
  roughly 0.95 because its real market cap is 1 629 G$, not the fabricated 10 G$.
- During a CoinGecko outage crypto scores fall instead of looking normal, and
  the drop is visible in `missing_fields`, in confidence and in the run gate.
  This is the intended trade: a visible gap beats an invisible fabrication.
- One extra public Kraken call per crypto holding per run (four today), so the
  cross-check exists even on the happy path.
- The equity `DataSourceOrchestrator` is untouched. Two orchestrators now exist
  with the same contract and different field shapes.
- `portfolio_deep_analyzer`'s crypto branch no longer fabricates, but unlike its
  ETF neighbour it does not raise either: the holding is kept and graded on what
  survived.
```

- [ ] **Step 2: Update the CHANGELOG**

Add under `## [Unreleased]` in `CHANGELOG.md`:

```markdown
### Fixed

- Crypto market data was fabricated in production. `_collect_crypto_data` sent
  the yfinance-normalized ticker (`BTC-USD`) to CoinGecko, which keys on the
  bare symbol, and the failure was swallowed into invented defaults
  (`market_cap 10e9`, `volume_24h 1e9`, `age_years 3.0`). Those fields carry
  80% of the crypto fundamental score. Resolved through a new
  `CryptoSourceOrchestrator` over CoinGecko, yfinance and Kraken, with per-field
  lineage and confidence (ADR-014).
- `CryptoAnalyzer` scored a missing component as the worst possible value
  (`_safe_get_float(..., 0.0)`). It now excludes the component and renormalizes
  the remaining weights; with no component left the score is `None` and the
  composite renormalizes over technical and risk.
- `data_quality.missing_fields` reported `[]` for crypto holdings whose every
  fundamental field was fabricated. Gaps are now `None` and reported, and
  `market_cap` was added to the crypto field list.
- XRP was scored as three years old. Ages now derive from a curated genesis-year
  table (XRP 2012), and an uncurated symbol yields no age instead of a default.

### Added

- `data/adapters/crypto/` — CoinGecko and Kraken adapters, symbol normalization
  and the curated genesis-year table.
- `data/crypto_source_orchestrator.py` — multi-source resolution with lineage,
  pinned confidence and price-divergence observation.
```

- [ ] **Step 3: Update the module CLAUDE.md files**

In `src/finwiz/orchestrators/CLAUDE.md`, under the `deep_analysis_data_collector.py`
row's section, add:

```markdown
Crypto market data does not come from the collector directly: it is resolved by
`data/crypto_source_orchestrator.py` (CoinGecko primary, yfinance then Kraken as
price fallback, Kraken always consulted as a cross-check). Unresolved fields are
`None` and never a constant — the collector previously wrote `market_cap 10e9`
and `volume_24h 1e9` on every failed lookup, which silently fed 80% of the
crypto fundamental score. See ADR-014.
```

In `src/finwiz/tools/CLAUDE.md`, next to the `enhanced_crypto_tool.py` entry,
add:

```markdown
`EnhancedCryptoAnalysisTool` does NOT raise on an unknown symbol: it returns
invented numbers tagged `sources == ["Fallback Data"]`. Any programmatic caller
must check that marker and treat it as a failure. `data/adapters/crypto/
coingecko_adapter.py` is the reference consumer. It also keys on the bare
symbol, so `BTC-USD` must be normalized to `BTC` first.
```

Create or extend `src/finwiz/data/CLAUDE.md` with a section describing the two
orchestrators:

```markdown
## Two source orchestrators

| Module | Asset classes | Shape |
|---|---|---|
| `data_source_orchestrator.py` | stocks | `FundamentalData` — ROE, debt/equity, revenue growth, profit margin. Async adapters. |
| `crypto_source_orchestrator.py` | crypto | `CryptoMarketData` — price, market cap, volume, supplies. Sync adapters. |

They share a contract — per-field lineage, confidence, `None` for anything
unresolved — and deliberately not a base class: `FundamentalData` is hardwired
to four equity metrics with equity validation bounds. Crypto adapters are
synchronous because both underlying tools are, and the calling collector runs
one thread per holding.
```

- [ ] **Step 4: Run the full gate**

```bash
make check
uv run mypy src/finwiz
uvx vulture src/finwiz --min-confidence 80
```

Expected: all green. `make check` includes markdownlint over `docs/` and a
strict MkDocs build, so the ADR must be reachable from the docs navigation if
`mkdocs.yml` lists ADRs explicitly — check and add the entry if so.

- [ ] **Step 5: Cheap three-CSV verification run**

```bash
PORTFOLIO_STOCK_CSV=/tmp/mini/stock.csv \
PORTFOLIO_ETF_CSV=/tmp/mini/etf.csv \
PORTFOLIO_CRYPTO_CSV=data/crypto.csv \
uv run kickoff
```

Then verify the numbers are real:

```bash
uv run python - <<'EOF'
import glob, json
for path in sorted(glob.glob("output/crypto/*-USD_enriched.json")):
    metrics = json.load(open(path))["quantitative"]["fundamental_metrics"]
    print(path.split("/")[-1], {k: metrics.get(k) for k in ("market_cap", "volume_24h", "age_years", "circulating_supply")})
EOF
```

Expected: BTC's `market_cap` reads about 1.63e12 (not 1e10), `volume_24h` is
non-zero, `circulating_supply` is about 2.0e7, and `age_years` is 17. No value
equals `10000000000.0` or `1000000000.0`.

- [ ] **Step 6: Verify the degraded path (spec verification 3)**

Force the CoinGecko adapter to fail and confirm the run degrades visibly rather
than silently. This is the behaviour the whole design exists to produce, so it
is checked directly rather than assumed.

```bash
uv run python - <<'EOF'
from datetime import date

from finwiz.data.crypto_source_orchestrator import CryptoSourceOrchestrator
from finwiz.scoring.asset_analyzers.crypto_analyzer import CryptoAnalyzer


class _DeadCoinGecko:
    source_name = "coingecko"

    def fetch(self, ticker):
        return None


orchestrator = CryptoSourceOrchestrator(coingecko=_DeadCoinGecko())
resolved = orchestrator.fetch("BTC-USD", yfinance_price=81061.41)
print("price        :", resolved.price, "via", resolved.lineage.price_source)
print("market_cap   :", resolved.market_cap)
print("confidence   :", resolved.confidence)
print("failed       :", resolved.sources_failed)

score, details = CryptoAnalyzer().calculate_fundamental_score(
    {
        "market_cap": resolved.market_cap,
        "volume_24h": resolved.volume_24h,
        "age_years": 17.0,
        "circulating_supply": resolved.circulating_supply,
        "max_supply": resolved.max_supply,
    }
)
print("score        :", score)
print("excluded     :", details["excluded_components"])
EOF
```

Expected: the price still resolves through yfinance (81061.41), `market_cap` is
`None`, confidence is below 1.0, `coingecko` appears in `sources_failed`, the
fundamental score is computed on the surviving components, and
`excluded_components` names the missing ones. Kraken contacts the network here,
so it may also appear in `sources_failed` when offline — that is acceptable for
this check as long as the yfinance price still wins.

- [ ] **Step 7: Commit**

```bash
git add docs/adr/ADR-014-crypto-market-data-sources.md CHANGELOG.md src/finwiz/data/CLAUDE.md src/finwiz/orchestrators/CLAUDE.md src/finwiz/tools/CLAUDE.md
git commit -m "docs: ADR-014 crypto market data sources"
```
