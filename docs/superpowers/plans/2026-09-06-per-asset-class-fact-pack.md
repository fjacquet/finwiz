# Per-Asset-Class Fact Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give each asset class a fact pack shaped for what it actually is — a company, a fund, or a protocol — instead of asking a fund who its CEO is.

**Architecture:** `FactPack` keeps its spine (`fetched_at`, `freshness`, `confidence`, `source_citations`, `sources_used`) and gains `asset_class` plus a `details` payload discriminated over `EquityFacts | FundFacts | CryptoFacts`. The equity path keeps the existing fragment-merge machinery, which genuinely merges three sources; funds and crypto get direct builders, since each is served by one source. Confidence is scored per class. One formatter module owns the labels used by both the prompt and the report.

**Tech Stack:** Python 3.13, Pydantic v2 discriminated unions, yfinance, pytest + pytest-mock + pytest-socket, uv.

**Spec:** `docs/superpowers/specs/2026-09-06-per-asset-class-fact-pack-design.md`

**Supersedes:** Tasks 5–7 of `docs/superpowers/plans/2026-09-06-deterministic-fact-pack.md`. Tasks 1–4 of that plan are complete and merged (`7bcfd04..f8d36a1`); its gap-fill task is replaced by Task 8 here, and its docs and live-verification tasks by Tasks 7 and 8.

## Global Constraints

- `unittest.mock` is BANNED. Use pytest-mock (`mocker.patch()`) only. Enforced by ruff and `make check-unittest-mock`.
- Unit tests make zero network calls; pytest-socket is armed. `yfinance_source._ticker` is the mandated patch point.
- All Pydantic models live in `schemas/`, never in domain folders.
- Line length 180 (ruff). `[tool.ruff.lint.mccabe] max-complexity = 10` is enforced.
- `json.dumps` always takes `default=str`.
- **Cast numerics taken from a DataFrame with `float(...)`.** Correction to an earlier version of this constraint, which claimed `numpy.float64` breaks `json.dumps`: it does not — `numpy.float64` subclasses Python `float`, so it serialises fine. `numpy.int64` does NOT subclass `int` and *does* raise `Object of type int64 is not JSON serializable`. No current field takes an integer straight from a DataFrame, so the cast is defence rather than a live fix — keep it, but do not expect a mutation check to kill it, and do not justify it with the JSON claim.
- **No source exception may reach the composer.** Every accessor wraps its body and returns an empty result rather than raising. This is why the branch exists: on 2026-09-06 one provider raising failed all 64 holdings.
- **Every source normalises into its schema's domain, AND wraps its model construction.** Both layers, always. Three sources on this branch have now shipped a raise because the schema declared a bound (`ge=0.0`, `ge=1900`) that the source never enforced and no fixture ever violated: a negative fund turnover, a negative crypto supply, an out-of-range launch year. A value outside the schema's domain is UNKNOWN — return `None`, never clamp to the boundary, because clamping asserts a fact. The construction guard is not redundant with normalisation: it catches the constraint whoever wrote the plan forgot to enumerate, which is exactly what happened each time.
- **`compose_fact_pack` returns `None` only when the ticker resolves to nothing.**
- **`maxSupply == 0` means "no cap", not "unknown".** Carried in data as `supply_is_capped`, never re-inferred from a magic zero.
- **A number whose unit cannot be stated is omitted.** `Total Net Assets` has no documented unit and is deliberately not modelled.
- Routing reads the declared `asset_class`; symbol shape is never inferred from. `to_yfinance_symbol(ticker, asset_class)` is the only place a query symbol is derived.
- Do NOT run `make lint` or `make check` — a known environment defect reformats ~66 unrelated markdown files. Use `uv run ruff check <files>` and `uv run ruff format --check <files>`.
- Do NOT run `crewai flow kickoff` or `uv run kickoff` — real money. Task 8 requires explicit authorisation.
- Never restore a file with `git checkout --`; edit it back instead. Never `git add -A` or `git add .` — add explicit paths. A broad add already swept a machine-specific symlink into a commit on this branch.
- Paste real captured terminal output in reports, or state plainly that it was not captured. Reviewers are instructed not to re-run your tests.

## Measured shapes — authoritative, do not re-derive

Probed 2026-09-06 reading raw types:

- `funds_data.fund_operations`: DataFrame, `columns == [<ticker>, "Category Average"]`, `index == ["Annual Report Expense Ratio", "Annual Holdings Turnover", "Total Net Assets"]`, cells are `numpy.float64`.
- `funds_data.top_holdings`: DataFrame, `index.name == "Symbol"`, `columns == ["Name", "Holding Percent"]`; a row is `{"Name": "NVIDIA Corp", "Holding Percent": 0.077756}`. 10 rows for `2B7K.DE`, **0 rows for `AEEM.PA`**.
- `funds_data.asset_classes`: `dict[str, float]` — `cashPosition`, `stockPosition`, `bondPosition`, `preferredPosition`, …
- `funds_data.sector_weightings`: `dict[str, float]`, 11 keys (`realestate`, `technology`, …).
- `funds_data.description`: empty string for European UCITS funds — not dependable.
- Crypto `info`: `description` (str, 349–411 chars), `startDate` (int epoch), `circulatingSupply` (int), `maxSupply` (int; `21000000` for BTC, **`0` for ETH and SOL**), `marketCap` (int), `volume24HrMarketCapPercent` (float), `coinMarketCapLink` (str).

## File Structure

| File | Responsibility |
|---|---|
| `src/finwiz/schemas/hybrid_analysis/fact_pack.py` (modify) | Envelope + the three facts models + `FundHolding` |
| `src/finwiz/analysis/fact_pack/confidence.py` (create) | Per-class confidence scoring |
| `src/finwiz/analysis/fact_pack/sources/fund_source.py` (create) | `funds_data` accessors + expense-ratio cross-check |
| `src/finwiz/analysis/fact_pack/sources/crypto_source.py` (create) | Crypto `info` accessors, no-cap semantics |
| `src/finwiz/analysis/fact_pack/composer.py` (modify) | Build `details` per class; clamps follow the new field homes |
| `src/finwiz/analysis/fact_pack/render.py` (create) | `to_rows` / `to_prompt_block`; the only place labels live |
| `src/finwiz/analysis/_helpers.py` (modify) | Inject one `fact_pack_block` |
| `src/finwiz/crews/deep_analysis/config/tasks.yaml` (modify) | One placeholder; drop the Perplexity claim |
| `src/finwiz/reporting/sections/insights.py`, `factpack.py` (modify) | Consume `to_rows` |
| `tests/integration/analysis/test_yfinance_shapes.py` (modify) | Canary covers fund and crypto fields |

---

### Task 1: The three facts models and the envelope

**Files:**

- Modify: `src/finwiz/schemas/hybrid_analysis/fact_pack.py`
- Test: `tests/unit/schemas/test_fact_pack.py`

**Interfaces:**

- Consumes: nothing.
- Produces: `FundHolding`, `EquityFacts`, `FundFacts`, `CryptoFacts`, and `FactPack` carrying `asset_class: Literal["stock", "etf", "crypto"]` and `details: EquityFacts | FundFacts | CryptoFacts` discriminated on `kind`.

Note the asset-class vocabulary: the portfolio CSVs and `AnalysisContext` use `"stock"`, `"etf"`, `"crypto"`. The models' `kind` discriminator uses `"equity"`, `"fund"`, `"crypto"` because those name the *thing*, not the CSV column. `FactPack.asset_class` keeps the CSV vocabulary so callers need no translation; the composer maps between them in Task 5.

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/schemas/test_fact_pack.py`:

```python
class TestPerClassDetails:
    @staticmethod
    def _envelope(**overrides):
        fetched_at = datetime.now(UTC)
        base = {
            "asset_class": "stock",
            "fetched_at": fetched_at,
            "freshness": FactPack.derive_freshness(fetched_at),
            "confidence": 1.0,
            "details": EquityFacts(business_summary="Designs phones.", leadership="Tim Cook (CEO)", recent_events=["2026-09-01 8-K: Changes"], events_from_filings=True),
        }
        return {**base, **overrides}

    def test_an_equity_pack_carries_equity_facts(self):
        pack = FactPack(**self._envelope())
        assert pack.details.kind == "equity"
        assert pack.details.leadership == "Tim Cook (CEO)"

    def test_a_fund_pack_carries_fund_facts(self):
        details = FundFacts(
            issuer="BlackRock Asset Management Ireland - ETF",
            legal_type="Exchange Traded Fund",
            inception_year=2020,
            expense_ratio=0.002,
            turnover=0.0,
            top_holdings=[FundHolding(symbol="NVDA", name="NVIDIA Corp", weight=0.077756)],
            asset_mix={"stockPosition": 0.9942},
            sector_weights={"technology": 0.25},
        )
        pack = FactPack(**self._envelope(asset_class="etf", details=details))
        assert pack.details.kind == "fund"
        assert pack.details.top_holdings[0].symbol == "NVDA"

    def test_a_capped_and_an_uncapped_crypto_are_distinguishable(self):
        """maxSupply == 0 means 'no cap'. It is information, not absence."""
        btc = CryptoFacts(
            description="Bitcoin is...",
            launched_year=2010,
            circulating_supply=20080456.0,
            max_supply=21000000.0,
            supply_is_capped=True,
            market_cap=1.6e12,
            volume_24h_market_cap_pct=0.0125,
        )
        eth = CryptoFacts(
            description="Ethereum is...",
            launched_year=2015,
            circulating_supply=122023856.0,
            max_supply=None,
            supply_is_capped=False,
            market_cap=4.0e11,
            volume_24h_market_cap_pct=0.02,
        )

        assert btc.supply_is_capped is True and btc.max_supply == 21000000.0
        assert eth.supply_is_capped is False and eth.max_supply is None

    def test_an_unknown_discriminator_is_rejected(self):
        """A payload naming a class we do not model must not validate.

        Asserting on a payload that is merely incomplete would pass for the
        wrong reason -- it would fail on a missing required field rather than
        on the discriminator.
        """
        envelope = self._envelope(asset_class="etf")
        envelope["details"] = {"kind": "commodity", "issuer": "Somebody"}
        with pytest.raises(ValidationError):
            FactPack.model_validate(envelope)

    def test_business_summary_is_capped_at_two_thousand(self):
        with pytest.raises(ValidationError):
            EquityFacts(business_summary="x" * 2001, leadership="Someone", recent_events=[], events_from_filings=False)
```

Ensure the module imports `pytest`, `ValidationError` from `pydantic`, and the new names.

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/unit/schemas/test_fact_pack.py -k PerClassDetails -v`
Expected: FAIL — `ImportError: cannot import name 'EquityFacts'`

- [ ] **Step 3: Write the models**

Replace `FactPack`'s three text fields in `src/finwiz/schemas/hybrid_analysis/fact_pack.py`. Add above the `FactPack` class:

```python
class FundHolding(BaseModel):
    """One line of a fund's published holdings."""

    symbol: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    weight: float = Field(ge=0.0, le=1.0, description="Fraction of the fund, as yfinance reports it (0.077756 == 7.78%)")

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EquityFacts(BaseModel):
    """A company: what it does, who runs it, what it filed."""

    kind: Literal["equity"] = "equity"
    business_summary: str = Field(min_length=1, max_length=2000)
    leadership: str = Field(min_length=1, max_length=1000)
    recent_events: list[str] = Field(default_factory=list, max_length=10)
    events_from_filings: bool = False

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FundFacts(BaseModel):
    """A fund: who issues it, what it costs, what it holds.

    There is no CEO here, and asking for one is what produced a 0.70 ceiling
    and an issuer's name standing in as `leadership`.
    """

    kind: Literal["fund"] = "fund"
    issuer: str = Field(min_length=1, max_length=200)
    legal_type: str = Field(default="", max_length=100)
    inception_year: int | None = Field(default=None, ge=1900, le=2200)
    expense_ratio: float | None = Field(default=None, ge=0.0, le=1.0, description="0.002 == 0.20% per year")
    turnover: float | None = Field(default=None, ge=0.0)
    top_holdings: list[FundHolding] = Field(default_factory=list, max_length=25)
    asset_mix: dict[str, float] = Field(default_factory=dict)
    sector_weights: dict[str, float] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CryptoFacts(BaseModel):
    """A protocol: what it is, when it launched, how its supply behaves."""

    kind: Literal["crypto"] = "crypto"
    description: str = Field(min_length=1, max_length=2000)
    launched_year: int | None = Field(default=None, ge=1900, le=2200)
    circulating_supply: float | None = Field(default=None, ge=0.0)
    max_supply: float | None = Field(default=None, ge=0.0, description="None when unknown OR uncapped; read supply_is_capped to tell them apart")
    supply_is_capped: bool = False
    market_cap: float | None = Field(default=None, ge=0.0)
    volume_24h_market_cap_pct: float | None = Field(default=None, ge=0.0)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
```

Then on `FactPack`, delete `corporate_structure`, `recent_events` and `leadership`, and add:

```python
    asset_class: Literal["stock", "etf", "crypto"]
    details: EquityFacts | FundFacts | CryptoFacts = Field(discriminator="kind")
```

Add `Literal` to the `typing` import and `ConfigDict` if not already imported. Leave `fetched_at`, `freshness`, `confidence`, `source_citations`, `sources_used` and `derive_freshness` exactly as they are — the run gate and the cache depend on them.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/unit/schemas/test_fact_pack.py -v`
Expected: PASS for the new class. Pre-existing tests that construct a `FactPack` with the removed fields will now fail — that is expected and correct; update them to the new shape rather than deleting them. The backward-compatibility test for packs cached without `sources_used` must be rewritten: those packs also lack `asset_class` and `details`, so they can no longer validate. Replace it with a test asserting that such a payload raises `ValidationError`, and note in a comment that the cache is invalidated once by Task 7 for exactly this reason.

- [ ] **Step 5: Run the wider suite to see the blast radius**

Run: `uv run pytest tests/unit/analysis/fact_pack/ tests/unit/reporting/test_fact_pack_rendering.py tests/unit/cache/test_fact_pack_cache.py -q`
Expected: FAILURES. Record the count and the failing test names in your report — Tasks 5 and 6 fix them. Do not fix them here; do not weaken them to pass.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/schemas/hybrid_analysis/fact_pack.py tests/unit/schemas/test_fact_pack.py
git commit -m "feat(fact-pack): three per-class facts models behind one envelope"
```

---

### Task 2: Per-class confidence

**Files:**

- Create: `src/finwiz/analysis/fact_pack/confidence.py`
- Test: `tests/unit/analysis/fact_pack/test_confidence.py`

**Interfaces:**

- Consumes: `EquityFacts`, `FundFacts`, `CryptoFacts` from Task 1; `PLACEHOLDER` from `fact_pack.fragment`.
- Produces: `score(details: EquityFacts | FundFacts | CryptoFacts, has_citation: bool) -> float`.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/analysis/fact_pack/test_confidence.py`:

```python
"""Confidence is scored over the fields that apply to each class."""

from finwiz.analysis.fact_pack.confidence import score
from finwiz.analysis.fact_pack.fragment import PLACEHOLDER
from finwiz.schemas.hybrid_analysis.fact_pack import CryptoFacts, EquityFacts, FundFacts, FundHolding


def _fund(**overrides) -> FundFacts:
    base = {
        "issuer": "BlackRock Asset Management Ireland - ETF",
        "legal_type": "Exchange Traded Fund",
        "expense_ratio": 0.002,
        "top_holdings": [FundHolding(symbol="NVDA", name="NVIDIA Corp", weight=0.0777)],
        "asset_mix": {"stockPosition": 0.9942},
    }
    return FundFacts(**{**base, **overrides})


class TestEquity:
    def test_filings_backed_equity_scores_one(self):
        facts = EquityFacts(business_summary="Designs phones.", leadership="Tim Cook (CEO)", recent_events=["2026-09-01 8-K"], events_from_filings=True)
        assert score(facts, has_citation=True) == 1.0

    def test_news_backed_equity_scores_0_85(self):
        facts = EquityFacts(business_summary="Builds planes.", leadership="Guillaume Faury (CEO)", recent_events=["Airbus wins order"], events_from_filings=False)
        assert score(facts, has_citation=True) == 0.85

    def test_placeholders_do_not_count_as_populated(self):
        facts = EquityFacts(business_summary=PLACEHOLDER, leadership=PLACEHOLDER, recent_events=[], events_from_filings=False)
        assert score(facts, has_citation=False) == 0.0


class TestFund:
    def test_a_complete_fund_scores_one(self):
        assert score(_fund(), has_citation=True) == 1.0

    def test_a_fund_without_top_holdings_scores_0_75(self):
        """AEEM.PA returns zero holdings while 2B7K.DE returns ten."""
        assert score(_fund(top_holdings=[]), has_citation=True) == 0.75

    def test_the_expense_ratio_carries_the_most_weight(self):
        without_ter = score(_fund(expense_ratio=None), has_citation=True)
        without_holdings = score(_fund(top_holdings=[]), has_citation=True)
        assert without_ter < without_holdings

    def test_a_zero_expense_ratio_still_counts_as_known(self):
        """0.0 is a real, remarkable fee — not a missing value."""
        assert score(_fund(expense_ratio=0.0), has_citation=True) == 1.0


class TestCrypto:
    def test_a_capped_asset_scores_one(self):
        facts = CryptoFacts(description="Bitcoin is...", launched_year=2010, circulating_supply=20080456.0, max_supply=21000000.0, supply_is_capped=True, market_cap=1.6e12)
        assert score(facts, has_citation=True) == 1.0

    def test_an_uncapped_asset_also_scores_one(self):
        """No cap is a monetary policy, not missing data. Ethereum must not be
        penalised for differing from Bitcoin."""
        facts = CryptoFacts(description="Ethereum is...", launched_year=2015, circulating_supply=122023856.0, max_supply=None, supply_is_capped=False, market_cap=4.0e11)
        assert score(facts, has_citation=True) == 1.0

    def test_unknown_supply_scores_lower_than_uncapped_supply(self):
        unknown = CryptoFacts(description="Something", launched_year=2020, circulating_supply=None, max_supply=None, supply_is_capped=False, market_cap=1.0)
        uncapped = CryptoFacts(description="Something", launched_year=2020, circulating_supply=585445184.0, max_supply=None, supply_is_capped=False, market_cap=1.0)
        assert score(unknown, has_citation=True) < score(uncapped, has_citation=True)
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_confidence.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'finwiz.analysis.fact_pack.confidence'`

- [ ] **Step 3: Write the implementation**

Create `src/finwiz/analysis/fact_pack/confidence.py`:

```python
"""Completeness scoring, per asset class.

A single scale across three structures is what capped a complete fund at 0.70:
it was marked down for lacking a CEO. Each class is scored over the fields that
apply to it, so 1.00 means "we know what there is to know about this kind of
thing", and scores are comparable between holdings of the same class.
"""

from __future__ import annotations

from finwiz.analysis.fact_pack.fragment import PLACEHOLDER
from finwiz.schemas.hybrid_analysis.fact_pack import CryptoFacts, EquityFacts, FundFacts

_W_CITATION = 0.10

_EQUITY_SUMMARY = 0.35
_EQUITY_LEADERSHIP = 0.25
_EQUITY_EVENTS_FILINGS = 0.30
_EQUITY_EVENTS_NEWS = 0.15

# The expense ratio outweighs everything else a fund can tell us: it is the one
# figure that reduces net return every year regardless of what the fund holds.
_FUND_IDENTITY = 0.20
_FUND_EXPENSE_RATIO = 0.30
_FUND_HOLDINGS = 0.25
_FUND_ASSET_MIX = 0.15

_CRYPTO_DESCRIPTION = 0.25
_CRYPTO_SUPPLY = 0.30
_CRYPTO_MARKET_CAP = 0.20
_CRYPTO_LAUNCHED = 0.15


def _populated(value: str | None) -> bool:
    return bool(value and value.strip() and value.strip() != PLACEHOLDER)


def _equity(facts: EquityFacts) -> float:
    total = 0.0
    if _populated(facts.business_summary):
        total += _EQUITY_SUMMARY
    if _populated(facts.leadership):
        total += _EQUITY_LEADERSHIP
    if facts.recent_events:
        total += _EQUITY_EVENTS_FILINGS if facts.events_from_filings else _EQUITY_EVENTS_NEWS
    return total


def _fund(facts: FundFacts) -> float:
    total = 0.0
    if _populated(facts.issuer):
        total += _FUND_IDENTITY
    # `is not None`, not truthiness: a 0.0% fee is a real and notable fact.
    if facts.expense_ratio is not None:
        total += _FUND_EXPENSE_RATIO
    if facts.top_holdings:
        total += _FUND_HOLDINGS
    if facts.asset_mix:
        total += _FUND_ASSET_MIX
    return total


def _crypto(facts: CryptoFacts) -> float:
    total = 0.0
    if _populated(facts.description):
        total += _CRYPTO_DESCRIPTION
    # Supply is known when we can state it, and "uncapped" is a statement.
    if facts.circulating_supply is not None and (facts.supply_is_capped or facts.max_supply is None):
        total += _CRYPTO_SUPPLY
    if facts.market_cap is not None:
        total += _CRYPTO_MARKET_CAP
    if facts.launched_year is not None:
        total += _CRYPTO_LAUNCHED
    return total


def score(details: EquityFacts | FundFacts | CryptoFacts, has_citation: bool) -> float:
    """Completeness in [0.0, 1.0], scored against the class's own fields."""
    if isinstance(details, EquityFacts):
        total = _equity(details)
    elif isinstance(details, FundFacts):
        total = _fund(details)
    else:
        total = _crypto(details)
    if has_citation:
        total += _W_CITATION
    return round(min(total, 1.0), 2)
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_confidence.py -v`
Expected: PASS (10 tests)

- [ ] **Step 5: Mutation check**

Change `_FUND_EXPENSE_RATIO` to `0.20` and re-run `test_the_expense_ratio_carries_the_most_weight`. It must FAIL. Restore by editing back — never `git checkout --`.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/analysis/fact_pack/confidence.py tests/unit/analysis/fact_pack/test_confidence.py
git commit -m "feat(fact-pack): score confidence against each class's own fields"
```

---

### Task 3: The fund source

**Files:**

- Create: `src/finwiz/analysis/fact_pack/sources/fund_source.py`
- Test: `tests/unit/analysis/fact_pack/test_fund_source.py`

**Interfaces:**

- Consumes: `FundFacts`, `FundHolding` from Task 1; `yfinance_source._ticker` as the network seam.
- Produces: `fund_facts(query_symbol: str, info: dict[str, Any]) -> tuple[FundFacts | None, tuple[str, ...]]` — the facts and its citation URLs.

Everything comes from `funds_data`, whose accessors each hit the network and each may fail independently. `Total Net Assets` is deliberately not read: its unit is undocumented, and an AUM without a unit is worse than no AUM.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/analysis/fact_pack/test_fund_source.py`:

```python
"""Fund facts from yfinance funds_data. Shapes are the real 2026-09-06 ones."""

import pandas as pd
import pytest

from finwiz.analysis.fact_pack.sources import fund_source
from finwiz.analysis.fact_pack.sources import yfinance_source


class _FakeFundsData:
    def __init__(self, operations=None, holdings=None, asset_classes=None, sectors=None):
        self._operations = operations
        self._holdings = holdings
        self._asset_classes = asset_classes if asset_classes is not None else {}
        self._sectors = sectors if sectors is not None else {}

    @property
    def fund_operations(self):
        if isinstance(self._operations, Exception):
            raise self._operations
        return self._operations

    @property
    def top_holdings(self):
        if isinstance(self._holdings, Exception):
            raise self._holdings
        return self._holdings

    @property
    def asset_classes(self):
        return self._asset_classes

    @property
    def sector_weightings(self):
        return self._sectors


class _FakeTicker:
    def __init__(self, funds_data):
        self.funds_data = funds_data


@pytest.fixture
def info():
    return {
        "quoteType": "ETF",
        "fundFamily": "BlackRock Asset Management Ireland - ETF",
        "legalType": "Exchange Traded Fund",
        "fundInceptionDate": 1602460800,
        "longName": "iShares MSCI World SRI UCITS ETF",
    }


@pytest.fixture
def operations():
    # Real shape: index carries the metric names, one column per ticker.
    return pd.DataFrame(
        {"2B7K.DE": [0.002, 0.0, 143259.6], "Category Average": [0.0031, 0.1, 500000.0]},
        index=["Annual Report Expense Ratio", "Annual Holdings Turnover", "Total Net Assets"],
    )


@pytest.fixture
def holdings():
    frame = pd.DataFrame({"Name": ["NVIDIA Corp", "ASML Holding"], "Holding Percent": [0.077756, 0.0421]}, index=["NVDA", "ASML.AS"])
    frame.index.name = "Symbol"
    return frame


class TestFundFacts:
    def test_identity_comes_from_info(self, mocker, info, operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        facts, _ = fund_source.fund_facts("2B7K.DE", info)
        assert facts.issuer == "BlackRock Asset Management Ireland - ETF"
        assert facts.legal_type == "Exchange Traded Fund"
        assert facts.inception_year == 2020

    def test_expense_ratio_is_read_from_the_ticker_column(self, mocker, info, operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        facts, _ = fund_source.fund_facts("2B7K.DE", info)
        assert facts.expense_ratio == pytest.approx(0.002)
        assert facts.turnover == pytest.approx(0.0)

    def test_total_net_assets_is_not_modelled(self, mocker, info, operations, holdings):
        """Its unit is undocumented; an AUM without a unit is worse than none."""
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        facts, _ = fund_source.fund_facts("2B7K.DE", info)
        assert not hasattr(facts, "total_net_assets")

    def test_holdings_are_converted_with_symbol_from_the_index(self, mocker, info, operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        facts, _ = fund_source.fund_facts("2B7K.DE", info)
        assert [h.symbol for h in facts.top_holdings] == ["NVDA", "ASML.AS"]
        assert facts.top_holdings[0].name == "NVIDIA Corp"
        assert facts.top_holdings[0].weight == pytest.approx(0.077756)
        # numpy scalars must not survive into the model, or JSON caching breaks.
        assert type(facts.top_holdings[0].weight) is float

    def test_a_fund_with_no_published_holdings_still_produces_facts(self, mocker, info, operations):
        """AEEM.PA returns an empty frame while 2B7K.DE returns ten rows."""
        empty = pd.DataFrame({"Name": [], "Holding Percent": []})
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, empty)))
        facts, _ = fund_source.fund_facts("AEEM.PA", info)
        assert facts.top_holdings == []
        assert facts.expense_ratio == pytest.approx(0.002)

    def test_a_failing_accessor_degrades_that_field_only(self, mocker, info, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(RuntimeError("boom"), holdings)))
        facts, _ = fund_source.fund_facts("2B7K.DE", info)
        assert facts.expense_ratio is None
        assert [h.symbol for h in facts.top_holdings] == ["NVDA", "ASML.AS"]

    def test_funds_data_failing_entirely_still_yields_identity_facts(self, mocker, info):
        mocker.patch.object(yfinance_source, "_ticker", side_effect=RuntimeError("network down"))
        facts, _ = fund_source.fund_facts("2B7K.DE", info)
        assert facts.issuer == "BlackRock Asset Management Ireland - ETF"
        assert facts.top_holdings == []

    def test_an_info_without_an_issuer_yields_none(self, mocker):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData()))
        facts, citations = fund_source.fund_facts("XXXX.DE", {"quoteType": "ETF"})
        assert facts is None
        assert citations == ()

    def test_the_quote_page_is_the_citation(self, mocker, info, operations, holdings):
        mocker.patch.object(yfinance_source, "_ticker", return_value=_FakeTicker(_FakeFundsData(operations, holdings)))
        _, citations = fund_source.fund_facts("2B7K.DE", info)
        assert citations == ("https://finance.yahoo.com/quote/2B7K.DE",)
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_fund_source.py -v`
Expected: FAIL — `ImportError: cannot import name 'fund_source'`

- [ ] **Step 3: Write the implementation**

Create `src/finwiz/analysis/fact_pack/sources/fund_source.py`:

```python
"""Fund facts from yfinance `funds_data`.

Each accessor on `funds_data` performs its own fetch and can fail on its own, so
each is guarded separately: a fund keeps its expense ratio when its holdings are
unavailable, and vice versa. Nothing here may raise — spec §6.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from finwiz.analysis.fact_pack.sources.yfinance_source import _ticker
from finwiz.schemas.hybrid_analysis.fact_pack import FundFacts, FundHolding
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_QUOTE_URL = "https://finance.yahoo.com/quote/{symbol}"
_EXPENSE_RATIO_ROW = "Annual Report Expense Ratio"
_TURNOVER_ROW = "Annual Holdings Turnover"
_MAX_HOLDINGS = 25


def _operations_value(operations: Any, symbol: str, row: str) -> float | None:
    """Read one metric from the operations frame.

    Columns are `[<symbol>, "Category Average"]`; the fund's own column is
    preferred and the first column is the fallback, because the header is
    whatever yfinance echoed back for the query.
    """
    if operations is None or getattr(operations, "empty", True):
        return None
    if row not in operations.index:
        return None
    column = symbol if symbol in operations.columns else operations.columns[0]
    value = operations.loc[row, column]
    # yfinance yields numpy.float64; Pydantic accepts it but json.dumps does not.
    return None if value is None else float(value)


def _holdings(frame: Any) -> list[FundHolding]:
    if frame is None or getattr(frame, "empty", True):
        return []
    rows: list[FundHolding] = []
    for symbol, row in frame.iterrows():
        name = str(row.get("Name") or "").strip()
        weight = row.get("Holding Percent")
        if not name or weight is None:
            continue
        rows.append(FundHolding(symbol=str(symbol), name=name[:200], weight=float(weight)))
        if len(rows) >= _MAX_HOLDINGS:
            break
    return rows


def _floats(mapping: Any) -> dict[str, float]:
    if not isinstance(mapping, dict):
        return {}
    return {str(k): float(v) for k, v in mapping.items() if isinstance(v, int | float)}


def fund_facts(query_symbol: str, info: dict[str, Any]) -> tuple[FundFacts | None, tuple[str, ...]]:
    """Build fund facts, or ``None`` when the fund has no identifiable issuer."""
    issuer = (info.get("fundFamily") or "").strip()
    if not issuer:
        logger.warning(f"fact_pack: {query_symbol} has no fundFamily; cannot build fund facts")
        return None, ()

    inception_year: int | None = None
    inception = info.get("fundInceptionDate")
    if isinstance(inception, int | float):
        try:
            inception_year = datetime.fromtimestamp(float(inception), tz=UTC).year
        except (OSError, OverflowError, ValueError) as e:
            logger.debug(f"fact_pack: {query_symbol} unusable fundInceptionDate: {e}")

    operations = holdings_frame = None
    asset_mix: dict[str, float] = {}
    sector_weights: dict[str, float] = {}
    try:
        funds = _ticker(query_symbol).funds_data
    except Exception as e:
        logger.warning(f"fact_pack: {query_symbol} funds_data unavailable: {e}")
        funds = None

    if funds is not None:
        for attribute, setter in (("fund_operations", "operations"), ("top_holdings", "holdings")):
            try:
                value = getattr(funds, attribute)
            except Exception as e:
                logger.debug(f"fact_pack: {query_symbol} funds_data.{attribute} unavailable: {e}")
                continue
            if setter == "operations":
                operations = value
            else:
                holdings_frame = value
        try:
            asset_mix = _floats(funds.asset_classes)
        except Exception as e:
            logger.debug(f"fact_pack: {query_symbol} funds_data.asset_classes unavailable: {e}")
        try:
            sector_weights = _floats(funds.sector_weightings)
        except Exception as e:
            logger.debug(f"fact_pack: {query_symbol} funds_data.sector_weightings unavailable: {e}")

    facts = FundFacts(
        issuer=issuer[:200],
        legal_type=(info.get("legalType") or "").strip()[:100],
        inception_year=inception_year,
        expense_ratio=_operations_value(operations, query_symbol, _EXPENSE_RATIO_ROW),
        turnover=_operations_value(operations, query_symbol, _TURNOVER_ROW),
        top_holdings=_holdings(holdings_frame),
        asset_mix=asset_mix,
        sector_weights=sector_weights,
    )
    return facts, (_QUOTE_URL.format(symbol=query_symbol),)
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_fund_source.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Verify against production**

Run and paste the real output in your report:

```bash
uv run python -c "
from finwiz.analysis.fact_pack.sources import fund_source, yfinance_source
for t in ('2B7K.DE', 'AEEM.PA', 'VUSA.L'):
    info = yfinance_source.resolve(t)
    f, c = fund_source.fund_facts(t, info)
    print(t, 'None' if f is None else f'ter={f.expense_ratio} holdings={len(f.top_holdings)} mix={len(f.asset_mix)} sectors={len(f.sector_weights)}')
"
```

Expected: `2B7K.DE` reports a TER around 0.002 with 10 holdings; `AEEM.PA` reports a TER with 0 holdings. If a fund reports `ter=None`, say so — that is data, not failure.

- [ ] **Step 6: Cross-check the expense ratio against the repo's own table**

`data/etf_expense_ratios.yaml` already exists. Read it, and for any fund present in both, log a WARNING when yfinance and the file disagree by more than 0.0005 (5 basis points). Add the comparison inside `fund_facts`, using the yfinance value as authoritative and the file as a tripwire — do not silently prefer either. Add a test with a stubbed table proving the warning fires on disagreement and stays silent on agreement.

If the file's structure does not map to tickers usable here, do not invent a mapping: report that in your report and skip this step, saying exactly what the file contains.

- [ ] **Step 7: Mutation check**

Delete the `float(...)` cast in `_holdings` and re-run `test_holdings_are_converted_with_symbol_from_the_index`. It must FAIL on the `type(...) is float` assertion. Restore by editing back.

- [ ] **Step 8: Commit**

```bash
git add src/finwiz/analysis/fact_pack/sources/fund_source.py tests/unit/analysis/fact_pack/test_fund_source.py
git commit -m "feat(fact-pack): fund facts from funds_data, with an expense-ratio tripwire"
```

---

### Task 4: The crypto source

**Files:**

- Create: `src/finwiz/analysis/fact_pack/sources/crypto_source.py`
- Test: `tests/unit/analysis/fact_pack/test_crypto_source.py`

**Interfaces:**

- Consumes: `CryptoFacts` from Task 1.
- Produces: `crypto_facts(query_symbol: str, info: dict[str, Any]) -> tuple[CryptoFacts | None, tuple[str, ...]]`.

Everything comes from `info`, which the composer already fetched — this source performs no further network calls.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/analysis/fact_pack/test_crypto_source.py`:

```python
"""Crypto facts from the info dict the composer already fetched."""

import pytest

from finwiz.analysis.fact_pack.sources import crypto_source

BTC = {
    "quoteType": "CRYPTOCURRENCY",
    "name": "Bitcoin",
    "description": "Bitcoin (BTC) is a cryptocurrency launched in 2010.",
    "startDate": 1278979200,
    "circulatingSupply": 20080456,
    "maxSupply": 21000000,
    "marketCap": 1604790386688,
    "volume24HrMarketCapPercent": 0.0125254495,
    "coinMarketCapLink": "https://coinmarketcap.com/currencies/bitcoin/",
}
ETH = {
    **BTC,
    "name": "Ethereum",
    "description": "Ethereum (ETH) is a cryptocurrency.",
    "startDate": 1438905600,
    "circulatingSupply": 122023856,
    "maxSupply": 0,
    "coinMarketCapLink": "https://coinmarketcap.com/currencies/ethereum/",
}


class TestCryptoFacts:
    def test_a_capped_asset_records_its_cap(self):
        facts, _ = crypto_source.crypto_facts("BTC-USD", BTC)
        assert facts.supply_is_capped is True
        assert facts.max_supply == 21000000.0
        assert facts.circulating_supply == 20080456.0

    def test_a_zero_max_supply_means_uncapped_not_unknown(self):
        """maxSupply == 0 is Ethereum's monetary policy, not a missing field."""
        facts, _ = crypto_source.crypto_facts("ETH-USD", ETH)
        assert facts.supply_is_capped is False
        assert facts.max_supply is None

    def test_an_absent_max_supply_is_also_uncapped_but_distinguishable_by_nothing_else(self):
        facts, _ = crypto_source.crypto_facts("XYZ-USD", {k: v for k, v in BTC.items() if k != "maxSupply"})
        assert facts.supply_is_capped is False
        assert facts.max_supply is None

    def test_the_launch_year_comes_from_start_date(self):
        facts, _ = crypto_source.crypto_facts("BTC-USD", BTC)
        assert facts.launched_year == 2010

    def test_the_coinmarketcap_link_is_the_citation(self):
        _, citations = crypto_source.crypto_facts("BTC-USD", BTC)
        assert citations == ("https://coinmarketcap.com/currencies/bitcoin/",)

    def test_a_non_http_citation_is_dropped(self):
        _, citations = crypto_source.crypto_facts("BTC-USD", {**BTC, "coinMarketCapLink": "javascript:alert(1)"})
        assert citations == ()

    def test_an_info_without_a_description_yields_none(self):
        facts, citations = crypto_source.crypto_facts("BTC-USD", {"quoteType": "CRYPTOCURRENCY"})
        assert facts is None
        assert citations == ()

    def test_an_oddly_typed_field_degrades_that_field_only(self):
        facts, _ = crypto_source.crypto_facts("BTC-USD", {**BTC, "marketCap": "lots", "startDate": "yesterday"})
        assert facts.market_cap is None
        assert facts.launched_year is None
        assert facts.circulating_supply == 20080456.0
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_crypto_source.py -v`
Expected: FAIL — `ImportError: cannot import name 'crypto_source'`

- [ ] **Step 3: Write the implementation**

Create `src/finwiz/analysis/fact_pack/sources/crypto_source.py`:

```python
"""Crypto facts from yfinance's `info`.

A protocol has no issuer and no officers, so none are asked for. What it does
have is a supply policy, and the distinction between "capped at 21 million",
"uncapped" and "we do not know" is the whole point of this module: yfinance
encodes the middle case as `maxSupply == 0`, which a naive reader would record
as a cap of zero.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from finwiz.schemas.hybrid_analysis.fact_pack import CryptoFacts
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_DESCRIPTION_MAX_CHARS = 2000


def _number(value: Any) -> float | None:
    """Floats only. A string where a number belongs is a missing field, not a crash."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _year(value: Any) -> int | None:
    epoch = _number(value)
    if epoch is None:
        return None
    try:
        return datetime.fromtimestamp(epoch, tz=UTC).year
    except (OSError, OverflowError, ValueError):
        return None


def crypto_facts(query_symbol: str, info: dict[str, Any]) -> tuple[CryptoFacts | None, tuple[str, ...]]:
    """Build crypto facts, or ``None`` when there is no description to anchor them."""
    description = (info.get("description") or "").strip()
    if not description:
        logger.warning(f"fact_pack: {query_symbol} has no description; cannot build crypto facts")
        return None, ()

    raw_max = _number(info.get("maxSupply"))
    # 0 is yfinance's encoding for "no maximum", not a cap of zero coins.
    capped = raw_max is not None and raw_max > 0
    facts = CryptoFacts(
        description=description[:_DESCRIPTION_MAX_CHARS],
        launched_year=_year(info.get("startDate")),
        circulating_supply=_number(info.get("circulatingSupply")),
        max_supply=raw_max if capped else None,
        supply_is_capped=capped,
        market_cap=_number(info.get("marketCap")),
        volume_24h_market_cap_pct=_number(info.get("volume24HrMarketCapPercent")),
    )

    link = str(info.get("coinMarketCapLink") or "")
    citations = (link,) if link.startswith(("http://", "https://")) else ()
    return facts, citations
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_crypto_source.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Mutation check**

Change `capped = raw_max is not None and raw_max > 0` to `capped = raw_max is not None` and re-run `test_a_zero_max_supply_means_uncapped_not_unknown`. It must FAIL. Restore by editing back.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/analysis/fact_pack/sources/crypto_source.py tests/unit/analysis/fact_pack/test_crypto_source.py
git commit -m "feat(fact-pack): crypto facts with explicit supply-cap semantics"
```

---

### Task 5: Composer builds the details

**Files:**

- Modify: `src/finwiz/analysis/fact_pack/composer.py`
- Test: `tests/unit/analysis/fact_pack/test_composer.py`

**Interfaces:**

- **Interface change agreed during Task 3:** `fund_facts(query_symbol, info)` returns a THREE-tuple `(facts, citations, sources)`, not a two-tuple. `sources` mirrors `FactPackFragment`'s existing `(citations, sources)` convention and is always `("yfinance.info", "yfinance.funds_data")`, plus `"etf_expense_ratios.yaml"` exactly when a false-zero expense ratio was substituted from the curated table. Use that tuple's `sources` for the fund branch instead of the hardcoded `("yfinance.funds_data",)` shown later in this task, so a substitution is visible in the pack's provenance. `crypto_facts` remains a two-tuple.
- Consumes: `fund_facts`, `crypto_facts`, `score`, the three facts models, and the existing equity machinery (`yfinance_source.equity_fragment/filing_events/news_events`, `merge_fragments`).
- Produces: `compose_fact_pack(ticker, company_name, sector, industry, asset_class) -> FactPack | None`, unchanged in signature.

The equity path keeps fragments, because three sources genuinely merge there. Funds and crypto call their builder directly — a text-shaped fragment would be a detour.

- [ ] **Step 1: Write the failing tests**

Add to `tests/unit/analysis/fact_pack/test_composer.py`:

```python
class TestPerClassComposition:
    def test_a_fund_gets_fund_facts_and_never_an_equity_shape(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "ETF", "fundFamily": "iShares"})
        mocker.patch.object(
            composer.fund_source,
            "fund_facts",
            return_value=(
                FundFacts(issuer="iShares", expense_ratio=0.002, asset_mix={"stockPosition": 1.0}, top_holdings=[FundHolding(symbol="NVDA", name="NVIDIA Corp", weight=0.07)]),
                ("https://finance.yahoo.com/quote/2B7K.DE",),
            ),
        )

        pack = composer.compose_fact_pack("2B7K.DE", "iShares World", None, None, "etf")

        assert pack.asset_class == "etf"
        assert pack.details.kind == "fund"
        assert pack.confidence == 1.0

    def test_a_crypto_holding_gets_crypto_facts(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "CRYPTOCURRENCY", "description": "Bitcoin is..."})
        mocker.patch.object(
            composer.crypto_source,
            "crypto_facts",
            return_value=(
                CryptoFacts(description="Bitcoin is...", launched_year=2010, circulating_supply=20080456.0, max_supply=21000000.0, supply_is_capped=True, market_cap=1.6e12),
                ("https://coinmarketcap.com/currencies/bitcoin/",),
            ),
        )

        pack = composer.compose_fact_pack("BTC", "Bitcoin", None, None, "crypto")

        assert pack.asset_class == "crypto"
        assert pack.details.kind == "crypto"
        assert pack.details.supply_is_capped is True

    def test_a_fund_whose_builder_returns_none_still_yields_a_pack(self, mocker):
        """A fund with no issuer is thin, not fatal — only an unresolvable ticker is fatal."""
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "ETF"})
        mocker.patch.object(composer.fund_source, "fund_facts", return_value=(None, ()))

        pack = composer.compose_fact_pack("XXXX.DE", "Unknown fund", None, None, "etf")

        assert pack is not None
        assert pack.details.kind == "fund"
        assert pack.confidence == 0.0

    def test_an_unresolvable_ticker_still_returns_none(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"trailingPegRatio": None})
        assert composer.compose_fact_pack("ZZZZNOTREAL", "Nothing", None, None, "stock") is None
```

Import `FundFacts`, `FundHolding`, `CryptoFacts` at the top of the test module.

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_composer.py -k PerClassComposition -v`
Expected: FAIL — `AttributeError: module ... has no attribute 'fund_source'`

- [ ] **Step 3: Rewrite the composition**

In `composer.py`, import `fund_source`, `crypto_source`, `score`, and the three facts models. Replace the body that built the flat `FactPack` with:

```python
_PLACEHOLDER_FUND = FundFacts(issuer=PLACEHOLDER)


def _equity_details(query_symbol: str, info: dict, ticker: str) -> tuple[EquityFacts, tuple[str, ...], tuple[str, ...]]:
    """The equity path keeps fragments: three sources genuinely merge here."""
    fragment = merge_fragments(
        yfinance_source.equity_fragment(query_symbol, info),
        yfinance_source.filing_events(query_symbol),
        yfinance_source.news_events(query_symbol),
    )
    facts = EquityFacts(
        business_summary=_clamp_text(ticker, "business_summary", fragment.corporate_structure or PLACEHOLDER, _CORPORATE_STRUCTURE_MAX_CHARS),
        leadership=_clamp_text(ticker, "leadership", fragment.leadership or PLACEHOLDER, _LEADERSHIP_MAX_CHARS),
        recent_events=list(fragment.recent_events),
        events_from_filings=fragment.events_from_filings,
    )
    return facts, fragment.citations, fragment.sources
```

and in `compose_fact_pack`, after the resolvability check and the `quoteType` warning, branch:

```python
    if asset_class == "etf":
        facts, citations = fund_source.fund_facts(query_symbol, info)
        details: EquityFacts | FundFacts | CryptoFacts = facts or _PLACEHOLDER_FUND
        sources: tuple[str, ...] = ("yfinance.funds_data",) if facts else ()
    elif asset_class == "crypto":
        crypto, citations = crypto_source.crypto_facts(query_symbol, info)
        details = crypto or CryptoFacts(description=PLACEHOLDER)
        sources = ("yfinance.info",) if crypto else ()
    else:
        details, citations, sources = _equity_details(query_symbol, info, ticker)

    fetched_at = datetime.now(UTC)
    try:
        return FactPack(
            asset_class=asset_class,
            details=details,
            fetched_at=fetched_at,
            freshness=FactPack.derive_freshness(fetched_at),
            confidence=score(details, has_citation=bool(citations)),
            source_citations=_clamp_citations(ticker, tuple(citations)),
            sources_used=list(sources),
        )
    except Exception as e:
        logger.error(f"fact_pack: {_describe(ticker, query_symbol)} FactPack construction failed unexpectedly: {e}", exc_info=True)
        return FactPack(
            asset_class=asset_class,
            details=EquityFacts(business_summary=PLACEHOLDER, leadership=PLACEHOLDER),
            fetched_at=fetched_at,
            freshness=FactPack.derive_freshness(fetched_at),
            confidence=0.0,
            source_citations=[],
            sources_used=[*sources, _SCHEMA_FALLBACK_SOURCE],
        )
```

**Retire the old scoring path entirely in this task.** `score()` replaces
`fragment.derive_confidence`, and leaving the old one alive would strand a second copy of the equity
weights (0.35 / 0.25 / 0.30 / 0.15 / 0.10) in `fragment.py`, to be kept in sync with
`confidence.py` by hand forever. Delete from `fragment.py`: the `derive_confidence` function and the
five `_W_*` constants it uses. Keep `_populated` and `PLACEHOLDER` — `merge_fragments` still needs
them. Then remove the five assertions in `tests/unit/analysis/fact_pack/test_fragment.py` that
exercise `derive_confidence` (they are at roughly lines 44, 53, 61, 65 and 69) along with its
import; those behaviours are now covered by `test_confidence.py`. Deleting the function without
touching that test file introduces new failures, so do both in one commit.

While you are in `confidence.py`, make its dispatch exhaustive: it currently reads
`isinstance(EquityFacts)` / `isinstance(FundFacts)` / bare `else` → crypto, so a fourth facts class
added later would be silently scored as crypto. Change the last branch to
`elif isinstance(details, CryptoFacts): ...` followed by
`raise TypeError(f"unscored fact-pack details type: {type(details)!r}")`, and add a test asserting
the raise. Silent misclassification is the failure mode this whole branch exists to eliminate. Keep `_clamp_text`, `_clamp_citations`, `_describe`, `_EXPECTED_QUOTE_TYPES`, the `to_yfinance_symbol` call and the ERROR-logged backstop exactly as they are — all were reviewed and are load-bearing. `_missing_fields` and `_gap_fill` are no longer called from the equity branch in this task; leave them in place, unused, for Task 8.

- [ ] **Step 4: Run the package suite**

Run: `uv run pytest tests/unit/analysis/fact_pack/ -v`
Expected: PASS. Tests written against the old flat shape will need updating to read `pack.details.*`; update them rather than deleting them, and list every test you changed in your report.

- [ ] **Step 5: Verify against production**

```bash
uv run python -c "
from finwiz.analysis.fact_pack import compose_fact_pack
for t, c in (('AAPL','stock'), ('AIR.PA','stock'), ('2B7K.DE','etf'), ('AEEM.PA','etf'), ('BTC','crypto'), ('ETH','crypto'), ('ZZZZNOTREAL','stock')):
    p = compose_fact_pack(t, t, None, None, c)
    print(t, 'None' if p is None else f'{p.details.kind:7} conf={p.confidence}')
"
```

Expected: `AAPL` equity 1.00; `2B7K.DE` fund 1.00; `AEEM.PA` fund 0.75; `BTC`/`ETH` crypto 1.00; `ZZZZNOTREAL` None. Paste the real output.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/analysis/fact_pack/composer.py tests/unit/analysis/fact_pack/
git commit -m "feat(fact-pack): compose per-class details behind the shared envelope"
```

---

### Task 6: Rendering and the prompt

**Files:**

- Create: `src/finwiz/analysis/fact_pack/render.py`
- Modify: `src/finwiz/analysis/_helpers.py`, `src/finwiz/crews/deep_analysis/config/tasks.yaml`, `src/finwiz/reporting/sections/insights.py`, `src/finwiz/reporting/sections/factpack.py`, `src/finwiz/orchestrators/reporting/enrichment.py`
- Also migrate to the envelope (controller ruling 2026-09-06 — the plan named no owner for these, and
  they fail today because their fixtures still build `FactPack` with `corporate_structure` /
  `leadership` / `recent_events` and no `asset_class` / `details`):
  `tests/unit/analysis/test_helpers.py`, `tests/unit/analysis/stages/test_fact_pack.py`,
  `tests/unit/analysis/stages/test_pipeline.py`, `tests/unit/analysis/stages/test_qualify.py`,
  `tests/unit/analysis/test_deep_analysis_pipeline.py`,
  `tests/unit/crews/test_deep_analysis_prompt.py`,
  `tests/unit/orchestrators/test_reporting_orchestrator.py`, `tests/unit/reporting/test_insights.py`,
  `tests/unit/reporting/test_fact_pack_rendering.py`
- Test: `tests/unit/analysis/fact_pack/test_render.py`

**Interfaces:**

- Consumes: the three facts models.
- Produces: `to_rows(pack: FactPack) -> list[tuple[str, str]]`, `to_prompt_block(pack: FactPack) -> str`.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/analysis/fact_pack/test_render.py`:

```python
"""One module owns the labels, so the prompt and the report cannot drift apart."""

from datetime import UTC, datetime

from finwiz.analysis.fact_pack.render import to_prompt_block, to_rows
from finwiz.schemas.hybrid_analysis.fact_pack import CryptoFacts, EquityFacts, FactPack, FundFacts, FundHolding


def _pack(asset_class, details) -> FactPack:
    fetched_at = datetime.now(UTC)
    return FactPack(
        asset_class=asset_class, details=details, fetched_at=fetched_at, freshness=FactPack.derive_freshness(fetched_at), confidence=1.0, source_citations=[], sources_used=[]
    )


class TestLabels:
    def test_an_equity_is_described_in_company_terms(self):
        pack = _pack("stock", EquityFacts(business_summary="Designs phones.", leadership="Tim Cook (CEO)", recent_events=["2026-09-01 8-K: Changes"], events_from_filings=True))
        labels = [label for label, _ in to_rows(pack)]
        assert "Structure" in labels
        assert "Direction" in labels

    def test_a_fund_is_never_asked_about_a_director(self):
        pack = _pack(
            "etf", FundFacts(issuer="iShares", legal_type="Exchange Traded Fund", expense_ratio=0.002, top_holdings=[FundHolding(symbol="NVDA", name="NVIDIA Corp", weight=0.0777)])
        )
        labels = [label for label, _ in to_rows(pack)]
        assert "Direction" not in labels
        assert "Émetteur" in labels
        assert "Frais courants" in labels

    def test_the_expense_ratio_is_rendered_as_a_percentage(self):
        pack = _pack("etf", FundFacts(issuer="iShares", expense_ratio=0.002))
        assert any("0,20 %" in value for _, value in to_rows(pack))

    def test_an_uncapped_supply_says_so_rather_than_showing_zero(self):
        pack = _pack("crypto", CryptoFacts(description="Ethereum is...", circulating_supply=122023856.0, max_supply=None, supply_is_capped=False))
        supply = next(value for label, value in to_rows(pack) if label == "Offre")
        assert "0" != supply.strip()
        assert "aucun plafond" in supply.lower()

    def test_a_capped_supply_states_the_cap(self):
        pack = _pack("crypto", CryptoFacts(description="Bitcoin is...", circulating_supply=20080456.0, max_supply=21000000.0, supply_is_capped=True))
        supply = next(value for label, value in to_rows(pack) if label == "Offre")
        assert "21" in supply


class TestPromptBlock:
    def test_the_block_carries_every_row(self):
        pack = _pack("etf", FundFacts(issuer="iShares", expense_ratio=0.002))
        block = to_prompt_block(pack)
        for label, value in to_rows(pack):
            assert label in block
            assert value in block

    def test_the_block_names_freshness_and_confidence(self):
        pack = _pack("stock", EquityFacts(business_summary="Designs phones.", leadership="Tim Cook (CEO)"))
        block = to_prompt_block(pack)
        assert "fresh" in block
        assert "1.00" in block
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_render.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'finwiz.analysis.fact_pack.render'`

- [ ] **Step 3: Write the renderer**

Create `src/finwiz/analysis/fact_pack/render.py`:

```python
"""Presentation for fact packs. The only place class labels are defined.

The prompt and the HTML report both read from here, so a label cannot say
"Direction" in one and "Émetteur" in the other for the same holding.
"""

from __future__ import annotations

from finwiz.schemas.hybrid_analysis.fact_pack import CryptoFacts, EquityFacts, FactPack, FundFacts

_MAX_HOLDINGS_SHOWN = 5


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.2f}".replace(".", ",") + " %"


def _supply(facts: CryptoFacts) -> str:
    circulating = "—" if facts.circulating_supply is None else f"{facts.circulating_supply:,.0f}".replace(",", " ")
    if facts.supply_is_capped and facts.max_supply is not None:
        cap = f"{facts.max_supply:,.0f}".replace(",", " ")
        return f"{circulating} en circulation, plafond {cap}"
    return f"{circulating} en circulation, aucun plafond"


def _equity_rows(facts: EquityFacts) -> list[tuple[str, str]]:
    rows = [("Structure", facts.business_summary), ("Direction", facts.leadership)]
    if facts.recent_events:
        source = "dépôts réglementaires" if facts.events_from_filings else "presse"
        rows.append((f"Événements récents ({source})", "\n".join(f"- {e}" for e in facts.recent_events)))
    return rows


def _fund_rows(facts: FundFacts) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = [("Émetteur", facts.issuer)]
    if facts.legal_type:
        rows.append(("Forme", facts.legal_type))
    if facts.inception_year is not None:
        rows.append(("Création", str(facts.inception_year)))
    rows.append(("Frais courants", _pct(facts.expense_ratio)))
    if facts.top_holdings:
        lines = [f"- {h.symbol} ({h.name}) {_pct(h.weight)}" for h in facts.top_holdings[:_MAX_HOLDINGS_SHOWN]]
        rows.append(("Principales lignes", "\n".join(lines)))
    if facts.asset_mix:
        mix = ", ".join(f"{k} {_pct(v)}" for k, v in sorted(facts.asset_mix.items(), key=lambda kv: -kv[1]) if v > 0)
        if mix:
            rows.append(("Allocation", mix))
    return rows


def _crypto_rows(facts: CryptoFacts) -> list[tuple[str, str]]:
    rows = [("Protocole", facts.description)]
    if facts.launched_year is not None:
        rows.append(("Lancement", str(facts.launched_year)))
    rows.append(("Offre", _supply(facts)))
    if facts.market_cap is not None:
        rows.append(("Capitalisation", f"{facts.market_cap:,.0f}".replace(",", " ")))
    return rows


def to_rows(pack: FactPack) -> list[tuple[str, str]]:
    """Ordered (label, value) pairs suited to the pack's asset class."""
    details = pack.details
    if isinstance(details, FundFacts):
        return _fund_rows(details)
    if isinstance(details, CryptoFacts):
        return _crypto_rows(details)
    return _equity_rows(details)


def to_prompt_block(pack: FactPack) -> str:
    """The fact pack as one block for the qualitative prompt."""
    header = f"📋 FACT PACK (sources structurées, fraîcheur : {pack.freshness}, confidence : {pack.confidence:.2f})"
    body = "\n".join(f"- {label} : {value}" for label, value in to_rows(pack))
    return f"{header}\n{body}"
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_render.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Rewire the prompt**

In `src/finwiz/analysis/_helpers.py`, replace the block that sets `corporate_structure`, `recent_events`, `leadership`, `fact_pack_freshness` and `fact_pack_confidence` (around lines 204–208) with a single assignment:

```python
        inputs["fact_pack_block"] = to_prompt_block(fact_pack)
```

Import `to_prompt_block` from `finwiz.analysis.fact_pack.render`.

In `src/finwiz/crews/deep_analysis/config/tasks.yaml`, replace lines 18–22 — the header claiming the pack is "vérifié via Perplexity" and the four field lines — with:

```yaml
    {fact_pack_block}
```

Also update the field list around line 68, which enumerates `corporate_structure`, `recent_events` and `leadership` as sub-fields of `fact_pack`; those names no longer exist. Describe the pack as carrying class-appropriate facts instead.

- [ ] **Step 6: Prove the template validator still passes**

Run: `uv run python -c "from finwiz.validation import validate_template_variables_at_startup; validate_template_variables_at_startup(); print('template variables OK')"`
Expected: prints OK. If it reports an unknown or unused variable, the YAML and `_helpers.py` disagree — fix them together, never by loosening the validator.

- [ ] **Step 7: Rewire the report sections**

**Corrected 2026-09-06 (controller ruling — the original instruction here mandated a silent failure).**
The original text said to build a `FactPack` in `insights.py` via `FactPack.model_validate(fact_pack)`
inside a `try/except ValidationError`. `insights.py` never receives a `FactPack`:
`orchestrators/reporting/enrichment.py:329-335` distils the pack into a five-key flat dict
(`corporate_structure`, `recent_events`, `leadership`, `freshness`, `source_citations`) and that is
what reaches `_fact_pack_block()`. `model_validate` would therefore fail for *every* holding and the
prescribed `except` would swallow it — the fact-pack block would vanish from every report with no
test failing.

Do this instead. `render.py` is the single seam:

- In `src/finwiz/orchestrators/reporting/enrichment.py`, replace the five flat keys with
  `"rows": [list(r) for r in to_rows(pack)]` plus `"freshness"` and `"source_citations"`. The rows
  are already (label, value) pairs, rendered once, per class.
- In `src/finwiz/reporting/sections/insights.py`, `_fact_pack_block` iterates `fact_pack.get("rows")`
  and renders each pair generically. It reconstructs no `FactPack` and imports no schema.
- Delete the hardcoded `"Faits vérifiés (Perplexity)"` attribution at `insights.py:100`. The spec
  requires that claim dropped, and it lives in the block being rewritten.

This satisfies design decision D5 (labels defined once, consumed by both the prompt and the report)
and removes a round-trip that cannot work by construction. Cached `*_enriched.json` from earlier runs
carries the old five keys and renders no fact-pack block until re-analysed; Task 7 invalidates the
cache anyway.

In `src/finwiz/reporting/sections/factpack.py`, keep the freshness and confidence chrome exactly as it is and render the body from `to_rows`.

- [ ] **Step 8: Run the reporting and analysis suites**

Run: `uv run pytest tests/unit/reporting/ tests/unit/analysis/ -q`
Expected: PASS. Update any test that asserted the old labels; list them in your report.

- [ ] **Step 9: Commit**

```bash
git add src/finwiz/analysis/fact_pack/render.py src/finwiz/analysis/_helpers.py src/finwiz/crews/deep_analysis/config/tasks.yaml src/finwiz/reporting/sections/insights.py src/finwiz/reporting/sections/factpack.py tests/unit/analysis/fact_pack/test_render.py tests/unit/reporting/
git commit -m "feat(fact-pack): one renderer owns the labels for prompt and report"
```

---

### Task 7: Canary, cache invalidation, and documentation

**Files:**

- Modify: `tests/integration/analysis/test_yfinance_shapes.py`
- Modify: `docs/adr/ADR-010-fact-pack-grounded-qualitative.md`, `CHANGELOG.md`, `CLAUDE.md`, `docs/PRD.md`
- Migrate to the envelope (controller ruling 2026-09-06 — the plan invalidated the cache but never
  updated the tests that build cached packs, so these 11 stay red until this task fixes them):
  `tests/unit/cache/test_fact_pack_cache.py` (9 failures),
  `tests/unit/scripts/test_invalidate_fact_pack.py` (2 failures)

**Interfaces:** none produced.

- [ ] **Step 0: Migrate the cache tests to the envelope**

These fixtures still construct `FactPack` with `corporate_structure` / `leadership` /
`recent_events` and no `asset_class` / `details`, so they fail against the shipped schema. This is
the same mechanical shape change Task 6 applied to nine other files — batch it, and **migrate rather
than delete**: a test asserting something about the old shape must assert the equivalent about the
new one. A cache round-trip test is exactly where a discriminated union earns its keep, so at least
one test must write a pack of each class and read it back with `details.kind` intact.

Run: `uv run pytest tests/unit/cache/test_fact_pack_cache.py tests/unit/scripts/test_invalidate_fact_pack.py -q`
Expected: all pass. Then `uv run pytest tests/unit -q` must report **0 failed** — this task is the
last one holding the suite red.

- [ ] **Step 1: Extend the canary to the fund and crypto fields**

Add two tests asserting the production shapes Tasks 3 and 4 depend on, in the same hard-assertion style the file now uses (key presence asserted before type, never `.get(key, default)`):

- for a fund (`2B7K.DE`): `funds_data.fund_operations` is a DataFrame whose index contains `"Annual Report Expense Ratio"`; `funds_data.top_holdings` is a DataFrame whose columns contain `"Name"` and `"Holding Percent"`; `funds_data.asset_classes` is a `dict`.
- for a crypto (`BTC-USD`): `info` contains `description`, `startDate`, `circulatingSupply`, `maxSupply`, `marketCap`, and their types are `str`/`int`/`int`/`int`/`int`.

Assert types and key presence only — never a specific expense ratio or supply figure, which change daily.

Run: `uv run pytest tests/integration/analysis/test_yfinance_shapes.py -m integration -v` and paste the real output.

- [ ] **Step 2: Invalidate the cache**

Run: `uv run python scripts/invalidate_fact_pack.py --all` (check the script's actual flags with `--help` first and use what it offers).

Expected: it reports the number of packs removed. Paste the real output. Packs written under the old flat shape can no longer validate, so this is required, not optional.

- [ ] **Step 3: Supersede ADR-010's source decision**

Append to `docs/adr/ADR-010-fact-pack-grounded-qualitative.md`:

```markdown
## Superseded in part (2026-09-06)

The grounding decision stands: qualitative analysis is fed verified facts rather
than trusting the model's recall. Two things this ADR assumed no longer hold.

**The source.** It specified Perplexity as the fact pack's provider. On
2026-09-06 a quota error (`insufficient_quota`, served as HTTP 401) made that
single provider fail all 64 holdings in one run — `fact_pack failed ×64`, zero
holdings analysed. Facts now come from free structured sources, with Perplexity
called only for fields those sources leave empty.

**The shape.** It specified one fact pack for every holding, with
`corporate_structure`, `leadership` and `recent_events`. Those are a company's
attributes. A fund has no CEO and a protocol has no head office, so two of the
three asset classes were being asked questions that did not apply: funds scored
0.70 with the issuer's name standing in as `leadership`, and crypto returned two
placeholders. `FactPack` now carries a payload typed per class.

See `docs/superpowers/specs/2026-09-06-per-asset-class-fact-pack-design.md`.
```

- [ ] **Step 4: CHANGELOG**

Add under `Unreleased` (create the heading below the intro block if absent):

```markdown
### Changed

- **Fact packs are built from structured data, not an LLM.** For equities:
  business summaries, officer lists, and for US listings and ADRs the SEC filing
  index with EDGAR links. Perplexity is called only for fields those sources
  leave empty, so a quota outage costs a few event lists instead of every
  holding in the run.
- **Each asset class now has its own fact pack shape.** A fund reports its
  issuer, legal form, ongoing charges and top holdings; a crypto asset reports
  its supply and whether that supply is capped. Neither is asked who its chief
  executive is.
- **`FactPack.confidence` is Python-derived and scored per class**, so a
  complete fund reaches 1.00 rather than being capped by a field it cannot have.
- **The fact-pack cache is invalidated once** by this change. Rebuilding it is
  free, which it was not when Perplexity was the only source.
```

- [ ] **Step 5: CLAUDE.md and the PRD**

In `CLAUDE.md`'s environment-variable block, state that `FF_PERPLEXITY_RESEARCH=false` makes fact packs fully deterministic and that fact packs never fail a holding for want of Perplexity.

Run `grep -n "fact.pack\|fact_pack\|Perplexity" docs/PRD.md` and correct any sentence presenting Perplexity as *the* fact-pack source, or describing one fact-pack shape for all holdings. Change only those sentences.

- [ ] **Step 6: Verify no document still claims the old behaviour**

Run:

```bash
grep -rn "corporate_structure\|fact.pack" --include="*.md" docs/adr docs/PRD.md CLAUDE.md README.md | grep -iv "superseded\|gap-fill\|per-asset"
```

Expected: every remaining hit is historical record inside the ADR, or already describes the new design. Any line presenting Perplexity as the source, or naming `corporate_structure` as a live field, is a miss — fix it.

- [ ] **Step 7: Commit**

```bash
git add tests/integration/analysis/test_yfinance_shapes.py docs/adr/ADR-010-fact-pack-grounded-qualitative.md CHANGELOG.md CLAUDE.md docs/PRD.md
git commit -m "docs(fact-pack): supersede ADR-010's source and shape decisions"
```

---

### Task 8: Gap-fill for equities, and live verification

**Files:**

- Modify: `src/finwiz/analysis/stages/fact_pack.py` **(Step 0 — see below)**
- Modify: `src/finwiz/analysis/fact_pack/composer.py`
- Create: `src/finwiz/analysis/fact_pack/sources/perplexity_source.py`
- Test: `tests/unit/analysis/fact_pack/test_gap_fill.py`, `tests/unit/analysis/stages/test_fact_pack.py`

- [ ] **Step 0: Wire the composer into production — do this FIRST**

**Controller ruling 2026-09-06, found by Task 7's implementer.** No task in this plan wired
`compose_fact_pack` into the running system. `compose_fact_pack` has zero production callers —
only its own `__init__.py` re-export — while `src/finwiz/analysis/stages/fact_pack.py:62` still
calls `fetch_fact_pack_sync` from the superseded `analysis/fact_pack_research.py`. Everything
Tasks 1-7 built is unreachable from a real run. Without this step the branch merges as dead code.

It is also now urgent rather than merely wrong. Task 7 invalidated all 58 cached packs, which was
required, so the next live run is a 100% cache miss. Every holding therefore reaches the old
fetcher, which constructs a flat `FactPack(corporate_structure=..., leadership=..., ...)` that the
current schema rejects; the resulting `ValidationError` is not caught by that fetcher, and
`stages/_resilience.py:114,146` deliberately re-raises `ValidationError` rather than recording
FAILED. A live run would crash rather than degrade holding by holding.

In `_fact_pack_inner`, replace the `fetch_fact_pack_sync` call with `compose_fact_pack`, threading
`asset_class` through:

```python
from finwiz.analysis.fact_pack import compose_fact_pack


def _fact_pack_inner(ticker: str, company_name: str, sector: str | None, industry: str | None, asset_class: str) -> FactPack:
    ...
    fetched = compose_fact_pack(ticker, company_name, sector, industry, asset_class)
```

and in the `fact_pack` stage entry point pass `analysis_ctx.asset_class`, which
`AnalysisContext` already carries (`deep_analysis_pipeline.py:63`). Note that `stages/emit.py:73`
constructs a context with `asset_class="unknown"`; the composer normalises any unenumerated value
to `"stock"` with a warning, so that path is safe.

Keep the surrounding cache logic exactly as it is — cache hit, stale-cache fallback, and the
`TransientStageError` on total failure are unchanged and still correct. Only the fetch call and the
one new parameter change. Update the docstring's step 3, which names Perplexity as the fetcher.

Tests: `tests/unit/analysis/stages/test_fact_pack.py` must assert the stage calls
`compose_fact_pack` and threads `asset_class` through. Add a test that a cache miss on an ETF
produces a pack whose `details.kind == "fund"` — that is the end-to-end proof the routing survives
the stage boundary, which is the whole point of this step.

Run `uv run pytest tests/unit -q` after this step: it must report **0 failed** once the
`test_fact_pack_research.py` failure is resolved by Step 1's demotion of that module.

**Interfaces:**

- Consumes: everything above; the existing `perplexity_with_retry`, `_FactPackRaw` and `_SYSTEM_FR` in `fact_pack_research.py`.
- Produces: `fetch_missing_events(ticker, company_name, sector, industry, timeout=15.0) -> tuple[str, ...]`.

Funds and crypto are complete from deterministic sources, so gap-fill narrows to **equities with neither filings nor allowlisted news — 6 of 67 holdings measured**. It fills `recent_events` and nothing else.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/analysis/fact_pack/test_gap_fill.py`:

```python
"""Gap-fill may add events to an equity. It may never overwrite, and never fail a pack."""

import pytest

from finwiz.analysis.fact_pack import composer
from finwiz.analysis.fact_pack.sources import perplexity_source


class TestGapFillScope:
    def test_an_equity_without_events_asks_perplexity(self, mocker):
        mocker.patch.object(
            composer.yfinance_source,
            "resolve",
            return_value={"quoteType": "EQUITY", "longBusinessSummary": "Builds planes.", "companyOfficers": [{"name": "G. Faury", "title": "CEO"}]},
        )
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer, "is_feature_enabled", return_value=True)
        fetch = mocker.patch.object(perplexity_source, "fetch_missing_events", return_value=("Airbus wins order",))

        pack = composer.compose_fact_pack("AIR.PA", "Airbus SE", None, None, "stock")

        fetch.assert_called_once()
        assert pack.details.recent_events == ["Airbus wins order"]
        assert pack.details.events_from_filings is False

    def test_an_equity_with_filing_events_never_asks(self, mocker):
        mocker.patch.object(
            composer.yfinance_source,
            "resolve",
            return_value={"quoteType": "EQUITY", "longBusinessSummary": "Designs phones.", "companyOfficers": [{"name": "T. Cook", "title": "CEO"}]},
        )
        mocker.patch.object(
            composer.yfinance_source,
            "filing_events",
            return_value=composer.FactPackFragment(recent_events=("2026-09-01 8-K: Changes",), events_from_filings=True, sources=("yfinance.sec_filings",)),
        )
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer, "is_feature_enabled", return_value=True)
        fetch = mocker.patch.object(perplexity_source, "fetch_missing_events")

        composer.compose_fact_pack("AAPL", "Apple Inc.", None, None, "stock")

        fetch.assert_not_called()

    def test_a_fund_never_asks_however_thin_it_is(self, mocker):
        """Funds are complete from deterministic sources; there is nothing to buy."""
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "ETF"})
        mocker.patch.object(composer.fund_source, "fund_facts", return_value=(None, ()))
        mocker.patch.object(composer, "is_feature_enabled", return_value=True)
        fetch = mocker.patch.object(perplexity_source, "fetch_missing_events")

        composer.compose_fact_pack("XXXX.DE", "Unknown fund", None, None, "etf")

        fetch.assert_not_called()

    def test_the_feature_flag_switches_it_off(self, mocker):
        mocker.patch.object(
            composer.yfinance_source,
            "resolve",
            return_value={"quoteType": "EQUITY", "longBusinessSummary": "Builds planes.", "companyOfficers": [{"name": "G. Faury", "title": "CEO"}]},
        )
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer, "is_feature_enabled", return_value=False)
        fetch = mocker.patch.object(perplexity_source, "fetch_missing_events")

        composer.compose_fact_pack("AIR.PA", "Airbus SE", None, None, "stock")

        fetch.assert_not_called()

    def test_a_quota_401_leaves_the_deterministic_pack_intact(self, mocker):
        """The 2026-09-06 outage in one assertion."""
        mocker.patch.object(
            composer.yfinance_source,
            "resolve",
            return_value={"quoteType": "EQUITY", "longBusinessSummary": "Builds planes.", "companyOfficers": [{"name": "G. Faury", "title": "CEO"}]},
        )
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=composer.FactPackFragment())
        mocker.patch.object(composer, "is_feature_enabled", return_value=True)
        mocker.patch.object(perplexity_source, "fetch_missing_events", side_effect=RuntimeError("Perplexity HTTP 401 insufficient_quota"))

        pack = composer.compose_fact_pack("AIR.PA", "Airbus SE", None, None, "stock")

        assert pack is not None
        assert pack.details.business_summary == "Builds planes."
        assert pack.details.recent_events == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_gap_fill.py -v`
Expected: FAIL — `ImportError: cannot import name 'perplexity_source'`

- [ ] **Step 3: Write the narrowed Perplexity source**

Create `src/finwiz/analysis/fact_pack/sources/perplexity_source.py`:

```python
"""Perplexity, narrowed to the one field structured data cannot supply.

Funds and crypto are complete without it. Equities are too, when the company
files with the SEC or a wire service covered it. What remains is a company with
neither — measured at 6 of 67 holdings.
"""

from __future__ import annotations

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_EVENT_MAX_CHARS = 200
_MAX_EVENTS = 10


def fetch_missing_events(ticker: str, company_name: str, sector: str | None, industry: str | None, timeout: float = 15.0) -> tuple[str, ...]:
    """Material events for one company. Any failure returns empty; never raises."""
    from finwiz.analysis._helpers import _today_french
    from finwiz.analysis.fact_pack_research import _SYSTEM_FR, _FactPackRaw, _run_coroutine_sync
    from finwiz.infrastructure.resilience.perplexity_retry import perplexity_with_retry

    prompt = (
        f"Date du jour : {_today_french()}.\n\n"
        f"Recherche UNIQUEMENT les événements matériels des 12 derniers mois pour "
        f"{company_name} ({ticker}, {sector or 'secteur inconnu'} / {industry or 'industrie inconnue'}) : "
        "résultats trimestriels notables, fusions-acquisitions, changements de direction, "
        "décisions réglementaires ou judiciaires majeures. Pas de bavardage marketing, "
        "pas de prévisions. Si tu n'as pas de source fiable, renvoie une liste vide."
    )

    try:
        raw = _run_coroutine_sync(
            perplexity_with_retry(prompt=prompt, schema=_FactPackRaw, system=_SYSTEM_FR, search_recency_filter="month", timeout=timeout),
            timeout=timeout,
        )
    except Exception as e:
        logger.warning(f"fact_pack gap-fill failed for {ticker}: {e}")
        return ()

    if raw is None:
        return ()
    return tuple(event[:_EVENT_MAX_CHARS] for event in raw.recent_events[:_MAX_EVENTS])
```

`_run_coroutine_sync` was extracted in the superseded plan's Task 5 and may not exist yet. If it is absent from `fact_pack_research.py`, extract it there from the body of `fetch_fact_pack_sync` — the event-loop handling that runs a coroutine from sync code, using a worker thread when a loop is already running — and say in your report that you did so.

- [ ] **Step 4: Wire it into the equity branch only**

In `composer.py`'s `_equity_details`, after merging the fragments, when `fragment.recent_events` is empty and `is_feature_enabled("perplexity_research")` is true, call `perplexity_source.fetch_missing_events(...)` inside a `try/except Exception` that logs a warning and returns `()` on failure. Use the result as `recent_events` with `events_from_filings=False`, and append `"perplexity.gap_fill"` to the sources when it returns anything.

The bare `ticker` goes to Perplexity, not the query symbol — it is a research prompt about a company, not a yfinance query.

`is_feature_enabled` is not currently imported in `composer.py`; add `from finwiz.config.features.flags import is_feature_enabled`. The tests patch it as `composer.is_feature_enabled`, so it must be bound in that module's namespace rather than called through its package path.

- [ ] **Step 5: Run the package suite**

Run: `uv run pytest tests/unit/analysis/fact_pack/ -v`
Expected: PASS.

- [ ] **Step 6: Run the whole suite**

Run: `make test`
Expected: PASS with no regressions. Report the count.

- [ ] **Step 7: Deterministic-only verification (no authorisation needed)**

```bash
FF_PERPLEXITY_RESEARCH=false uv run python -c "
import csv
from finwiz.analysis.fact_pack import compose_fact_pack
rows = []
for path, cls in (('data/stock.csv','stock'), ('data/etf.csv','etf'), ('data/crypto.csv','crypto')):
    with open(path) as f:
        for r in csv.DictReader(f):
            t = (r.get('Ticker') or '').replace('Yahoo:', '').strip()
            if t: rows.append((t, cls))
import statistics
scores = {}
for t, c in rows:
    p = compose_fact_pack(t, t, None, None, c)
    scores.setdefault(c, []).append(0.0 if p is None else p.confidence)
for c, v in scores.items():
    print(f'{c:6} n={len(v):3} mean={statistics.mean(v):.2f} min={min(v):.2f} max={max(v):.2f} zero={sum(1 for x in v if x == 0.0)}')
"
```

Paste the real output. This is the headline evidence: mean confidence per class with Perplexity switched off entirely.

- [ ] **Step 8: Full run — REQUIRES EXPLICIT AUTHORISATION**

Do not start this on your own initiative; it spends real money. When authorised:

Run: `uv run kickoff; echo "exit=$?"`

Then capture the run gate's eight lines (`grep 'run gate:' logs/finwiz.log | tail -9`) and confirm `coverage` is far above the 0/64 of 2026-09-06. Record the verdict, the exit code and the per-class confidence in the PR body.

- [ ] **Step 9: Commit**

```bash
git add src/finwiz/analysis/fact_pack/ tests/unit/analysis/fact_pack/
git commit -m "feat(fact-pack): gap-fill narrowed to equities missing events"
```

---

## Self-Review

**Spec coverage.** D1 envelope + discriminated payload → Task 1. D2 per-class confidence → Task 2. D3 `maxSupply == 0` means uncapped → Task 1 (`supply_is_capped`), Task 4 (the `> 0` test), Task 6 (rendered as "aucun plafond"), each with a test that bites. D4 one prompt block → Task 6. D5 labels in one module → Task 6 (`render.py`, consumed by prompt and both report sections). D6 legacy fields removed, cache invalidated → Task 1 (removal), Task 7 Step 2 (invalidation). D7 no number without a unit → Task 3 (`Total Net Assets` unread, with a test asserting the attribute does not exist). Measured-availability tables → Tasks 3 and 4 fixtures. §3 rendering → Task 6. §4 migration → Tasks 1 and 7. §5 gap-fill narrowed to equities → Task 8. Risks: canary extension → Task 7 Step 1; `funds_data` unevenly populated → Task 3's AEEM.PA test; expense-ratio cross-check → Task 3 Step 6.

**Placeholder scan.** None. Every code step carries runnable code. Task 3 Step 6 and Task 8 Step 3 contain conditional instructions, but each names what to do in both branches and what to report — they are not deferrals.

**Type consistency.** `FundHolding(symbol, name, weight)` is identical in Tasks 1, 3, 5 and 6. `score(details, has_citation)` is defined in Task 2 and called with that shape in Task 5. `fund_facts(query_symbol, info) -> tuple[FundFacts | None, tuple[str, ...]]` and `crypto_facts(query_symbol, info) -> tuple[CryptoFacts | None, tuple[str, ...]]` match their Task 5 call sites, including the two-tuple unpacking. `to_rows(pack)` / `to_prompt_block(pack)` take the envelope, not the details, in both their definition (Task 6) and their uses (Tasks 6, 7). `fetch_missing_events` returns `tuple[str, ...]` in Task 8's source and is consumed as such. The `kind` discriminator values (`equity`/`fund`/`crypto`) are distinct from `FactPack.asset_class` values (`stock`/`etf`/`crypto`) deliberately, and Task 1 says so explicitly so nobody "fixes" the mismatch.
