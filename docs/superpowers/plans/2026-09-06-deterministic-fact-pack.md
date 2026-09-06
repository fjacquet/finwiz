# Deterministic Fact Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build fact packs from free structured sources (yfinance) so no billing state can halt every holding, with Perplexity demoted to filling only the fields structured data left empty.

**Architecture:** A new `finwiz/analysis/fact_pack/` package holds per-source fragment builders and one composer. The composer routes by the holding's *declared* asset class, merges fragments first-non-empty-wins, derives `confidence` from field completeness, and calls Perplexity only for still-empty fields. The public seam `fetch_fact_pack_sync` keeps its name and its meaning to the caller; only its body changes. `analysis/stages/fact_pack.py`, the cache, and the stage's OK/FAILED contract are not modified except to pass one new argument.

**Tech Stack:** Python 3.13, yfinance (already a core dependency), Pydantic v2, pytest + pytest-mock + pytest-socket, uv.

**Spec:** `docs/superpowers/specs/2026-09-06-deterministic-fact-pack-design.md`

## Global Constraints

- `unittest.mock` is BANNED. Use pytest-mock (`mocker.patch()`) only. Enforced by ruff and `make check-unittest-mock`.
- Unit tests make zero network calls. pytest-socket is armed; mock the seam, never widen the allow-list.
- `json.dumps` always takes `default=str`.
- All Pydantic models live in `schemas/`, never in domain folders.
- Line length 180 (ruff).
- Do NOT run `make lint` or `make check` — a known environment defect reformats ~66 unrelated markdown files. Run `uv run ruff check <files>` and `uv run ruff format --check <files>` on changed files only.
- Do NOT run `crewai flow kickoff` or `uv run kickoff` without explicit authorisation — it spends real money.
- Every new test gets a mutation check: break the implementation line the test targets, confirm the test fails, restore. A test that does not bite does not count.
- Branch: `feat/run-gate` in worktree `/Users/fjacquet/Projects/finwiz/.claude/worktrees/run-gate`. All work happens there. Do not create additional branches.
- Never restore files with `git checkout --` — it has destroyed uncommitted work in this repo twice. Copy to the scratchpad first.
- AI Minimalism: Python does deterministic work; AI only qualitative reasoning. When Python and AI disagree, Python wins.
- **Documentation ships with the change, never as a follow-up.** A doc that still describes the old behaviour is read as current and acted on — that is how `CLAUDE.md` came to promise a truthful `make gate` exit code that make cannot produce. Task 6 owns the doc updates for this plan; if a task invalidates a claim Task 6 does not cover, fix it in that task and say so in the commit.

## File Structure

| File | Responsibility |
|---|---|
| `src/finwiz/analysis/fact_pack/__init__.py` (create) | Package marker; re-exports `compose_fact_pack` |
| `src/finwiz/analysis/fact_pack/fragment.py` (create) | `FactPackFragment` dataclass + `merge_fragments` + `derive_confidence` |
| `src/finwiz/analysis/fact_pack/sources/__init__.py` (create) | Package marker |
| `src/finwiz/analysis/fact_pack/sources/yfinance_source.py` (create) | Ticker resolution, equity/ETF/crypto identity fragments, filing and news events |
| `src/finwiz/analysis/fact_pack/sources/perplexity_source.py` (create) | Narrowed Perplexity call returning a fragment for named missing fields only |
| `src/finwiz/analysis/fact_pack/composer.py` (create) | Asset-class routing, merge order, gap-fill decision, `FactPack` construction |
| `src/finwiz/schemas/hybrid_analysis/fact_pack.py` (modify) | Add `sources_used`; correct the `confidence` description |
| `src/finwiz/analysis/fact_pack_research.py` (modify) | `fetch_fact_pack_sync` body delegates to the composer; keeps `_FactPackRaw`, `_SYSTEM_FR` |
| `src/finwiz/analysis/stages/fact_pack.py` (modify) | Thread `asset_class` from `analysis_ctx` into `_fact_pack_inner` |

Tests mirror the source tree under `tests/unit/analysis/fact_pack/`.

---

### Task 1: Fragment type and schema change

**Files:**
- Create: `src/finwiz/analysis/fact_pack/__init__.py`
- Create: `src/finwiz/analysis/fact_pack/fragment.py`
- Modify: `src/finwiz/schemas/hybrid_analysis/fact_pack.py`
- Test: `tests/unit/analysis/fact_pack/test_fragment.py`
- Test: `tests/unit/schemas/test_fact_pack.py` (append)

**Interfaces:**
- Consumes: nothing.
- Produces: `FactPackFragment` (frozen dataclass, fields `corporate_structure: str | None`, `leadership: str | None`, `recent_events: tuple[str, ...]`, `citations: tuple[str, ...]`, `sources: tuple[str, ...]`, `events_from_filings: bool`); `merge_fragments(*fragments: FactPackFragment) -> FactPackFragment`; `derive_confidence(fragment: FactPackFragment) -> float`; `FactPack.sources_used: list[str]`.

- [ ] **Step 1: Write the failing test for the fragment**

Create `tests/unit/analysis/fact_pack/__init__.py` (empty) and `tests/unit/analysis/fact_pack/test_fragment.py`:

```python
"""Fragment merge and confidence derivation."""

from finwiz.analysis.fact_pack.fragment import FactPackFragment, derive_confidence, merge_fragments


class TestMergeFragments:
    def test_first_non_empty_wins_and_nothing_overwrites(self):
        first = FactPackFragment(corporate_structure="Independent entity.", sources=("yfinance.equity",))
        second = FactPackFragment(corporate_structure="A later, weaker guess.", leadership="Jane Doe, CEO", sources=("perplexity",))

        merged = merge_fragments(first, second)

        assert merged.corporate_structure == "Independent entity."
        assert merged.leadership == "Jane Doe, CEO"
        assert merged.sources == ("yfinance.equity", "perplexity")

    def test_citations_concatenate_and_deduplicate_preserving_order(self):
        first = FactPackFragment(citations=("https://a.example", "https://b.example"))
        second = FactPackFragment(citations=("https://b.example", "https://c.example"))

        assert merge_fragments(first, second).citations == ("https://a.example", "https://b.example", "https://c.example")

    def test_events_from_filings_survives_a_later_news_fragment(self):
        filings = FactPackFragment(recent_events=("2026-09-01 8-K: Corporate Changes",), events_from_filings=True)
        news = FactPackFragment(recent_events=("Some headline",))

        merged = merge_fragments(filings, news)

        # recent_events is first-non-empty like every other field, so the filing
        # events win outright and the flag must still describe what was kept.
        assert merged.recent_events == ("2026-09-01 8-K: Corporate Changes",)
        assert merged.events_from_filings is True


class TestDeriveConfidence:
    def test_us_stock_with_filings_scores_one(self):
        fragment = FactPackFragment(
            corporate_structure="Apple Inc. designs...",
            leadership="Tim Cook, CEO",
            recent_events=("2026-09-01 8-K: Corporate Changes",),
            citations=("https://example.com/edgar",),
            events_from_filings=True,
        )
        assert derive_confidence(fragment) == 1.0

    def test_european_stock_with_news_events_scores_0_85(self):
        fragment = FactPackFragment(
            corporate_structure="Airbus SE manufactures...",
            leadership="Guillaume Faury, CEO",
            recent_events=("Airbus wins order",),
            citations=("https://example.com/news",),
        )
        assert derive_confidence(fragment) == 0.85

    def test_typical_etf_scores_0_70(self):
        fragment = FactPackFragment(
            corporate_structure="UCITS ETF issued by BlackRock...",
            leadership="BlackRock Asset Management Ireland - ETF",
            citations=("https://finance.yahoo.com/quote/2B7K.DE",),
        )
        assert derive_confidence(fragment) == 0.70

    def test_crypto_with_news_only_scores_0_25(self):
        fragment = FactPackFragment(recent_events=("Bitcoin headline",), citations=("https://example.com/news",))
        assert derive_confidence(fragment) == 0.25

    def test_placeholder_text_does_not_count_as_populated(self):
        fragment = FactPackFragment(corporate_structure="Information indisponible", leadership="Information indisponible")
        assert derive_confidence(fragment) == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_fragment.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'finwiz.analysis.fact_pack'`

- [ ] **Step 3: Write the implementation**

Create `src/finwiz/analysis/fact_pack/__init__.py`:

```python
"""Deterministic fact pack construction from free structured sources."""
```

Create `src/finwiz/analysis/fact_pack/fragment.py`:

```python
"""A fragment is one source's partial answer; only the composer builds a FactPack.

Sources deliberately cannot return a ``FactPack``. Keeping them to fragments is
what makes "which source said what" answerable after the fact, and it is what
lets the merge rule guarantee that a paid LLM can only add to a deterministic
answer, never replace one.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

# Same sentinel the Perplexity path has always written for an unknown field.
# Imported by value rather than from fact_pack_research to keep this module free
# of any dependency on the LLM path.
PLACEHOLDER = "Information indisponible"

_W_STRUCTURE = 0.35
_W_LEADERSHIP = 0.25
_W_EVENTS_FILINGS = 0.30
_W_EVENTS_NEWS = 0.15
_W_CITATIONS = 0.10


@dataclass(frozen=True)
class FactPackFragment:
    """One source's contribution. Every field is optional by construction."""

    corporate_structure: str | None = None
    leadership: str | None = None
    recent_events: tuple[str, ...] = ()
    citations: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    events_from_filings: bool = False


def _populated(value: str | None) -> bool:
    return bool(value and value.strip() and value.strip() != PLACEHOLDER)


def merge_fragments(*fragments: FactPackFragment) -> FactPackFragment:
    """Merge in argument order: the first non-empty value for a field wins.

    Argument order is the precedence, and callers pass a fixed per-asset-class
    list, so two runs over identical inputs compose identically.
    """
    merged = FactPackFragment()
    citations: list[str] = []
    sources: list[str] = []

    for fragment in fragments:
        if not _populated(merged.corporate_structure) and _populated(fragment.corporate_structure):
            merged = replace(merged, corporate_structure=fragment.corporate_structure)
        if not _populated(merged.leadership) and _populated(fragment.leadership):
            merged = replace(merged, leadership=fragment.leadership)
        if not merged.recent_events and fragment.recent_events:
            merged = replace(merged, recent_events=fragment.recent_events, events_from_filings=fragment.events_from_filings)
        for url in fragment.citations:
            if url not in citations:
                citations.append(url)
        for source in fragment.sources:
            if source not in sources:
                sources.append(source)

    return replace(merged, citations=tuple(citations), sources=tuple(sources))


def derive_confidence(fragment: FactPackFragment) -> float:
    """Completeness score, not self-assessment.

    A self-rated number cannot be checked against anything. This one can be
    recomputed from the stored pack, compared between holdings, and trended
    across runs -- which is the whole reason it replaces the AI's own rating.
    """
    score = 0.0
    if _populated(fragment.corporate_structure):
        score += _W_STRUCTURE
    if _populated(fragment.leadership):
        score += _W_LEADERSHIP
    if fragment.recent_events:
        score += _W_EVENTS_FILINGS if fragment.events_from_filings else _W_EVENTS_NEWS
    if fragment.citations:
        score += _W_CITATIONS
    return round(min(score, 1.0), 2)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_fragment.py -v`
Expected: PASS (10 tests)

- [ ] **Step 5: Write the failing schema test**

Append to `tests/unit/schemas/test_fact_pack.py`:

```python
class TestSourcesUsed:
    def test_sources_used_round_trips(self):
        fetched_at = datetime.now(UTC)
        pack = FactPack(
            corporate_structure="Apple Inc. designs...",
            leadership="Tim Cook, CEO",
            fetched_at=fetched_at,
            freshness=FactPack.derive_freshness(fetched_at),
            confidence=1.0,
            sources_used=["yfinance.info", "yfinance.sec_filings"],
        )
        assert pack.sources_used == ["yfinance.info", "yfinance.sec_filings"]

    def test_a_pack_cached_before_sources_used_existed_still_loads(self):
        """The 58 packs already in cache/fact_packs were written without this field.

        FactPack is extra="forbid", so the field had to be added explicitly; this
        pins that adding it did not invalidate everything already on disk.
        """
        fetched_at = datetime.now(UTC)
        legacy = {
            "corporate_structure": "Apple Inc. designs...",
            "recent_events": [],
            "leadership": "Tim Cook, CEO",
            "fetched_at": fetched_at.isoformat(),
            "freshness": FactPack.derive_freshness(fetched_at),
            "confidence": 0.8,
            "source_citations": [],
        }
        assert FactPack.model_validate(legacy).sources_used == []
```

Check the file's existing imports first; add `from datetime import UTC, datetime` only if absent.

- [ ] **Step 6: Run it to verify it fails**

Run: `uv run pytest tests/unit/schemas/test_fact_pack.py -k SourcesUsed -v`
Expected: FAIL — `ValidationError ... Extra inputs are not permitted [type=extra_forbidden]`

- [ ] **Step 7: Add the schema field**

In `src/finwiz/schemas/hybrid_analysis/fact_pack.py`, after the `source_citations` field:

```python
    sources_used: list[str] = Field(
        default_factory=list,
        description="Which sources produced this pack, e.g. ['yfinance.info', 'yfinance.sec_filings']",
    )
```

The `default_factory` is load-bearing: `FactPack` is `extra="forbid"`, and the packs already on disk were written without this key.

Change the `confidence` field's description in the same file from `"AI-rated 0.0-1.0"` to:

```python
    confidence: float = Field(ge=0.0, le=1.0, description="Python-derived completeness score 0.0-1.0 (see analysis/fact_pack/fragment.py)")
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `uv run pytest tests/unit/schemas/test_fact_pack.py tests/unit/analysis/fact_pack/ -v`
Expected: PASS

- [ ] **Step 9: Mutation check**

Change `_W_LEADERSHIP` from `0.25` to `0.20` and re-run `test_european_stock_with_news_events_scores_0_85`. It must FAIL. Restore `0.25` by editing the value back — do NOT use `git checkout --`.

- [ ] **Step 10: Commit**

```bash
git add src/finwiz/analysis/fact_pack/ src/finwiz/schemas/hybrid_analysis/fact_pack.py tests/unit/analysis/fact_pack/ tests/unit/schemas/test_fact_pack.py
git commit -m "feat(fact-pack): fragment type, merge rule, and completeness-derived confidence"
```

---

### Task 2: yfinance identity sources

**Files:**
- Create: `src/finwiz/analysis/fact_pack/sources/__init__.py`
- Create: `src/finwiz/analysis/fact_pack/sources/yfinance_source.py`
- Test: `tests/unit/analysis/fact_pack/test_yfinance_source.py`

**Interfaces:**
- Consumes: `FactPackFragment` from Task 1.
- Produces: `resolve(ticker: str) -> dict[str, Any]`; `is_resolvable(info: dict[str, Any]) -> bool`; `equity_fragment(info: dict[str, Any]) -> FactPackFragment`; `etf_fragment(ticker: str, info: dict[str, Any]) -> FactPackFragment`; `crypto_fragment(info: dict[str, Any]) -> FactPackFragment`; module-level seam `_ticker(symbol: str) -> Any`.

**Field shapes**, verified against live responses on 2026-09-06 — do not re-derive:
- `info["quoteType"]` is `"EQUITY"` / `"ETF"` / `"CRYPTOCURRENCY"`; an unresolvable ticker returns a dict of exactly one key with `quoteType` absent.
- `info["companyOfficers"]` is a list of dicts with `name`, `title`, `age`, `fiscalYear`.
- ETF `info` carries `fundFamily`, `legalType`, `longName`, `fundInceptionDate` (epoch seconds int), and `category` which may be `None`.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/analysis/fact_pack/test_yfinance_source.py`:

```python
"""Identity fragments built from yfinance `info`.

Fixtures mirror real 2026-09-06 responses; the network seam is `_ticker`.
"""

import pytest

from finwiz.analysis.fact_pack.sources import yfinance_source as src


@pytest.fixture
def equity_info():
    return {
        "quoteType": "EQUITY",
        "longName": "Apple Inc.",
        "longBusinessSummary": "Apple Inc. designs, manufactures and markets smartphones.",
        "companyOfficers": [
            {"name": "Mr. Timothy D. Cook", "title": "CEO & Director"},
            {"name": "Mr. Kevan Parekh", "title": "Senior VP & CFO"},
            {"name": "Ms. Deirdre O'Brien", "title": "Senior VP of Retail"},
        ],
    }


@pytest.fixture
def etf_info():
    return {
        "quoteType": "ETF",
        "longName": "iShares MSCI World SRI UCITS ETF EUR (Acc)",
        "fundFamily": "BlackRock Asset Management Ireland - ETF",
        "legalType": "Exchange Traded Fund",
        "fundInceptionDate": 1602460800,
        "category": None,
    }


class TestResolvability:
    def test_a_real_instrument_is_resolvable(self, equity_info):
        assert src.is_resolvable(equity_info) is True

    def test_an_unknown_ticker_is_not_resolvable(self):
        # A bogus symbol comes back as a single-key dict with no quoteType.
        assert src.is_resolvable({"trailingPegRatio": None}) is False

    def test_resolve_returns_an_empty_dict_when_yfinance_raises(self, mocker):
        mocker.patch.object(src, "_ticker", side_effect=RuntimeError("network is down"))
        assert src.resolve("AAPL") == {}


class TestEquityFragment:
    def test_business_summary_becomes_corporate_structure(self, equity_info):
        assert src.equity_fragment(equity_info).corporate_structure == "Apple Inc. designs, manufactures and markets smartphones."

    def test_officers_become_leadership_as_name_and_title(self, equity_info):
        leadership = src.equity_fragment(equity_info).leadership
        assert "Mr. Timothy D. Cook (CEO & Director)" in leadership
        assert "Mr. Kevan Parekh (Senior VP & CFO)" in leadership

    def test_officers_without_a_name_or_title_are_skipped(self):
        info = {"quoteType": "EQUITY", "companyOfficers": [{"name": "", "title": "CEO"}, {"name": "Real Person", "title": ""}]}
        assert src.equity_fragment(info).leadership is None

    def test_a_missing_summary_yields_none_not_an_empty_string(self):
        assert src.equity_fragment({"quoteType": "EQUITY"}).corporate_structure is None

    def test_the_source_is_labelled(self, equity_info):
        assert src.equity_fragment(equity_info).sources == ("yfinance.info",)


class TestEtfFragment:
    def test_structure_names_issuer_legal_type_and_inception(self, etf_info):
        structure = src.etf_fragment("2B7K.DE", etf_info).corporate_structure
        assert "BlackRock Asset Management Ireland - ETF" in structure
        assert "Exchange Traded Fund" in structure
        assert "2020" in structure

    def test_the_manager_is_the_honest_answer_for_leadership(self, etf_info):
        assert src.etf_fragment("2B7K.DE", etf_info).leadership == "BlackRock Asset Management Ireland - ETF"

    def test_the_quote_page_is_the_citation(self, etf_info):
        assert src.etf_fragment("2B7K.DE", etf_info).citations == ("https://finance.yahoo.com/quote/2B7K.DE",)


class TestCryptoFragment:
    def test_crypto_has_no_structure_or_leadership_to_report(self):
        fragment = src.crypto_fragment({"quoteType": "CRYPTOCURRENCY", "longName": "Bitcoin USD"})
        assert fragment.corporate_structure is None
        assert fragment.leadership is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_yfinance_source.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'finwiz.analysis.fact_pack.sources'`

- [ ] **Step 3: Write the implementation**

Create `src/finwiz/analysis/fact_pack/sources/__init__.py`:

```python
"""Per-source fragment builders."""
```

Create `src/finwiz/analysis/fact_pack/sources/yfinance_source.py`:

```python
"""Fact pack fragments from yfinance.

yfinance is already a core dependency -- it fetches every price in this
project -- so nothing new is taken on here. It is also scraped rather than
contractual, which is why every accessor below degrades to an empty fragment
instead of raising: a shape change must cost one field, never a holding.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import yfinance as yf

from finwiz.analysis.fact_pack.fragment import FactPackFragment
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_MAX_OFFICERS = 6
_QUOTE_URL = "https://finance.yahoo.com/quote/{ticker}"


def _ticker(symbol: str) -> Any:
    """Network seam. Tests patch this, never yfinance itself."""
    return yf.Ticker(symbol)


def resolve(ticker: str) -> dict[str, Any]:
    """Fetch `info`, or an empty dict if yfinance fails for any reason."""
    try:
        return _ticker(ticker).info or {}
    except Exception as e:
        logger.warning(f"yfinance info lookup failed for {ticker}: {e}")
        return {}


def is_resolvable(info: dict[str, Any]) -> bool:
    """A real instrument always carries a quoteType; an unknown symbol never does."""
    return info.get("quoteType") is not None


def equity_fragment(info: dict[str, Any]) -> FactPackFragment:
    summary = (info.get("longBusinessSummary") or "").strip() or None

    people: list[str] = []
    for officer in info.get("companyOfficers") or []:
        name = (officer.get("name") or "").strip()
        title = (officer.get("title") or "").strip()
        if name and title:
            people.append(f"{name} ({title})")
        if len(people) >= _MAX_OFFICERS:
            break

    return FactPackFragment(
        corporate_structure=summary,
        leadership="; ".join(people) or None,
        sources=("yfinance.info",),
    )


def etf_fragment(ticker: str, info: dict[str, Any]) -> FactPackFragment:
    """For a fund, the issuer IS the corporate structure and the manager IS the leadership.

    Stating that plainly beats asking an LLM to write prose about a CEO the fund
    does not have.
    """
    issuer = (info.get("fundFamily") or "").strip()
    legal_type = (info.get("legalType") or "").strip()
    long_name = (info.get("longName") or ticker).strip()

    parts = [long_name]
    if legal_type:
        parts.append(legal_type)
    if issuer:
        parts.append(f"issued by {issuer}")
    inception = info.get("fundInceptionDate")
    if isinstance(inception, int | float):
        parts.append(f"inception {datetime.fromtimestamp(inception, tz=UTC).year}")

    return FactPackFragment(
        corporate_structure=", ".join(parts) + "." if parts else None,
        leadership=issuer or None,
        citations=(_QUOTE_URL.format(ticker=ticker),),
        sources=("yfinance.info",),
    )


def crypto_fragment(info: dict[str, Any]) -> FactPackFragment:
    """Crypto has no issuer and no officers; say nothing rather than invent one.

    Both fields stay None so the composer writes the placeholder and confidence
    scores this holding as the thin pack it genuinely is.
    """
    return FactPackFragment(sources=("yfinance.info",)) if is_resolvable(info) else FactPackFragment()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_yfinance_source.py -v`
Expected: PASS (12 tests)

- [ ] **Step 5: Mutation check**

Change `if name and title:` to `if name or title:` and re-run `test_officers_without_a_name_or_title_are_skipped`. It must FAIL. Restore by editing back.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/analysis/fact_pack/sources/ tests/unit/analysis/fact_pack/test_yfinance_source.py
git commit -m "feat(fact-pack): identity fragments from yfinance info"
```

---

### Task 3: yfinance event sources

**Files:**
- Modify: `src/finwiz/analysis/fact_pack/sources/yfinance_source.py`
- Test: `tests/unit/analysis/fact_pack/test_yfinance_events.py`

**Interfaces:**
- Consumes: `FactPackFragment`, `_ticker` seam from Task 2.
- Produces: `filing_events(ticker: str, now: datetime | None = None) -> FactPackFragment`; `news_events(ticker: str, now: datetime | None = None) -> FactPackFragment`.

**Field shapes**, verified 2026-09-06:
- `Ticker.sec_filings` is a list of dicts with `date` (`"2026-09-01"`), `type` (`"8-K/A"`), `title` (`"Corporate Changes & Voting Matters"`), `edgarUrl`. Returns `[]` for European-only listings, ETFs and crypto — and yfinance logs an internal HTTP 404 doing so.
- `Ticker.news` is a list of `{"id": ..., "content": {...}}`; `content` has `title`, `pubDate` (`"2026-09-05T19:40:00Z"`), `provider` (`{"displayName": "Motley Fool", ...}`) and `canonicalUrl` (`{"url": ...}`).

`now` is injected so tests are not time-dependent. Callers pass nothing.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/analysis/fact_pack/test_yfinance_events.py`:

```python
"""Event fragments: filings preferred, news filtered.

Yahoo's news feed mixes wire copy with opinion pieces ("Prediction: Amazon Will
Join..."). The project rule is to filter noise out, not emit it with a low
grade, so these tests pin exclusion rather than down-weighting.
"""

from datetime import UTC, datetime

import pytest

from finwiz.analysis.fact_pack.fragment import FactPackFragment
from finwiz.analysis.fact_pack.sources import yfinance_source as src

NOW = datetime(2026, 9, 6, tzinfo=UTC)


class _FakeTicker:
    def __init__(self, sec_filings=None, news=None):
        self._sec_filings = sec_filings
        self._news = news

    @property
    def sec_filings(self):
        if isinstance(self._sec_filings, Exception):
            raise self._sec_filings
        return self._sec_filings

    @property
    def news(self):
        if isinstance(self._news, Exception):
            raise self._news
        return self._news


@pytest.fixture
def filings():
    return [
        {"date": "2026-09-01", "type": "8-K", "title": "Corporate Changes & Voting Matters", "edgarUrl": "https://example.com/edgar/1"},
        {"date": "2026-06-15", "type": "10-Q", "title": "Quarterly Report", "edgarUrl": "https://example.com/edgar/2"},
        {"date": "2019-01-02", "type": "8-K", "title": "Ancient Event", "edgarUrl": "https://example.com/edgar/old"},
        {"date": "2026-08-01", "type": "CORRESP", "title": "Correspondence", "edgarUrl": "https://example.com/edgar/3"},
    ]


class TestFilingEvents:
    def test_material_filings_inside_the_window_become_events(self, mocker, filings):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))

        fragment = src.filing_events("AAPL", now=NOW)

        assert fragment.recent_events == (
            "2026-09-01 8-K: Corporate Changes & Voting Matters",
            "2026-06-15 10-Q: Quarterly Report",
        )
        assert fragment.events_from_filings is True

    def test_filings_older_than_twelve_months_are_dropped(self, mocker, filings):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))
        assert not any("Ancient" in e for e in src.filing_events("AAPL", now=NOW).recent_events)

    def test_immaterial_filing_types_are_dropped(self, mocker, filings):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))
        assert not any("Correspondence" in e for e in src.filing_events("AAPL", now=NOW).recent_events)

    def test_edgar_urls_become_citations(self, mocker, filings):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=filings))
        assert src.filing_events("AAPL", now=NOW).citations == ("https://example.com/edgar/1", "https://example.com/edgar/2")

    def test_a_european_listing_with_no_filings_yields_an_empty_fragment(self, mocker):
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=[]))
        assert src.filing_events("AIR.PA", now=NOW).recent_events == ()

    def test_an_internal_404_degrades_the_field_and_does_not_raise(self, mocker):
        # yfinance raises internally for non-US tickers; that must cost events only.
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(sec_filings=RuntimeError("HTTP Error 404")))
        assert src.filing_events("NESN.SW", now=NOW) == FactPackFragment()


class TestNewsEvents:
    @staticmethod
    def _item(title, provider, url, pub_date="2026-09-05T19:40:00Z"):
        return {"content": {"title": title, "pubDate": pub_date, "provider": {"displayName": provider}, "canonicalUrl": {"url": url}}}

    def test_allowlisted_providers_become_events(self, mocker):
        news = [self._item("Airbus wins 40-jet order", "Reuters", "https://example.com/reuters/1")]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(news=news))

        fragment = src.news_events("AIR.PA", now=NOW)

        assert fragment.recent_events == ("2026-09-05 Airbus wins 40-jet order",)
        assert fragment.citations == ("https://example.com/reuters/1",)
        assert fragment.events_from_filings is False

    def test_opinion_providers_are_excluded_entirely(self, mocker):
        news = [self._item("Prediction: Amazon Will Join Nvidia", "Motley Fool", "https://example.com/fool/1")]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(news=news))
        assert src.news_events("AMZN", now=NOW).recent_events == ()

    def test_items_older_than_twelve_months_are_dropped(self, mocker):
        news = [self._item("Old wire story", "Reuters", "https://example.com/r/old", pub_date="2024-01-01T00:00:00Z")]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(news=news))
        assert src.news_events("AAPL", now=NOW).recent_events == ()

    def test_event_text_is_truncated_to_two_hundred_chars(self, mocker):
        news = [self._item("x" * 400, "Reuters", "https://example.com/r/long")]
        mocker.patch.object(src, "_ticker", return_value=_FakeTicker(news=news))
        assert all(len(e) <= 200 for e in src.news_events("AAPL", now=NOW).recent_events)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_yfinance_events.py -v`
Expected: FAIL — `AttributeError: module ... has no attribute 'filing_events'`

- [ ] **Step 3: Write the implementation**

Append to `src/finwiz/analysis/fact_pack/sources/yfinance_source.py`:

```python
_EVENT_MAX_CHARS = 200
_EVENT_WINDOW_DAYS = 365
_MAX_EVENTS = 10

# Filing types that describe something material. CORRESP, S-8, 25-NSE and the
# rest are administrative traffic and would crowd out the events that matter.
_MATERIAL_FILING_TYPES = frozenset({"8-K", "8-K/A", "10-K", "10-Q", "20-F", "6-K", "6-K/A", "DEF 14A", "SC 13D", "SC 13G"})

# Wire services and regulatory-filing distributors only. Yahoo's feed also
# carries opinion sites whose headlines are predictions, not events; per the
# project rule those are excluded outright rather than emitted at low grade.
_NEWS_PROVIDER_ALLOWLIST = frozenset(
    {
        "Reuters",
        "Bloomberg",
        "Associated Press",
        "AP Finance",
        "Financial Times",
        "Business Wire",
        "PR Newswire",
        "GlobeNewswire",
        "Dow Jones Newswires",
        "The Wall Street Journal",
    },
)


def _within_window(when: datetime, now: datetime) -> bool:
    return 0 <= (now - when).days <= _EVENT_WINDOW_DAYS


def filing_events(ticker: str, now: datetime | None = None) -> FactPackFragment:
    """Material SEC filings in the last 12 months, with EDGAR links.

    This is the strongest evidence available for `recent_events`: dated, filed,
    and citable. It covers US listings and foreign issuers with ADRs (ASML files
    20-F / 6-K); a European-only listing returns nothing and falls back to news.
    """
    now = now or datetime.now(UTC)
    try:
        filings = _ticker(ticker).sec_filings or []
    except Exception as e:
        logger.debug(f"sec_filings unavailable for {ticker}: {e}")
        return FactPackFragment()

    events: list[str] = []
    citations: list[str] = []
    for filing in filings:
        if filing.get("type") not in _MATERIAL_FILING_TYPES:
            continue
        raw_date = filing.get("date") or ""
        try:
            filed = datetime.strptime(raw_date, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            continue
        if not _within_window(filed, now):
            continue
        title = (filing.get("title") or "").strip()
        events.append(f"{raw_date} {filing['type']}: {title}"[:_EVENT_MAX_CHARS])
        url = filing.get("edgarUrl")
        if url:
            citations.append(url)
        if len(events) >= _MAX_EVENTS:
            break

    if not events:
        return FactPackFragment()
    return FactPackFragment(
        recent_events=tuple(events),
        citations=tuple(citations),
        sources=("yfinance.sec_filings",),
        events_from_filings=True,
    )


def news_events(ticker: str, now: datetime | None = None) -> FactPackFragment:
    """Wire-service headlines in the last 12 months. Weaker than filings, still cited."""
    now = now or datetime.now(UTC)
    try:
        items = _ticker(ticker).news or []
    except Exception as e:
        logger.debug(f"news unavailable for {ticker}: {e}")
        return FactPackFragment()

    events: list[str] = []
    citations: list[str] = []
    for item in items:
        content = item.get("content") or {}
        provider = ((content.get("provider") or {}).get("displayName") or "").strip()
        if provider not in _NEWS_PROVIDER_ALLOWLIST:
            continue
        raw_date = (content.get("pubDate") or "").replace("Z", "+00:00")
        try:
            published = datetime.fromisoformat(raw_date)
        except ValueError:
            continue
        if not _within_window(published, now):
            continue
        title = (content.get("title") or "").strip()
        if not title:
            continue
        events.append(f"{published.date().isoformat()} {title}"[:_EVENT_MAX_CHARS])
        url = (content.get("canonicalUrl") or {}).get("url")
        if url:
            citations.append(url)
        if len(events) >= _MAX_EVENTS:
            break

    if not events:
        return FactPackFragment()
    return FactPackFragment(recent_events=tuple(events), citations=tuple(citations), sources=("yfinance.news",))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/analysis/fact_pack/ -v`
Expected: PASS

- [ ] **Step 5: Mutation check**

Remove `"Motley Fool"`'s exclusion by changing the provider check to `if False:` and re-run `test_opinion_providers_are_excluded_entirely`. It must FAIL. Restore by editing back.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/analysis/fact_pack/sources/yfinance_source.py tests/unit/analysis/fact_pack/test_yfinance_events.py
git commit -m "feat(fact-pack): filing and filtered-news events from yfinance"
```

---

### Task 4: The composer

**Files:**
- Create: `src/finwiz/analysis/fact_pack/composer.py`
- Modify: `src/finwiz/analysis/fact_pack/__init__.py`
- Test: `tests/unit/analysis/fact_pack/test_composer.py`

**Interfaces:**
- Consumes: everything from Tasks 1–3.
- Produces: `compose_fact_pack(ticker: str, company_name: str, sector: str | None, industry: str | None, asset_class: str) -> FactPack | None`. Returns `None` only when the ticker is unresolvable; every other outcome is a `FactPack`.

Perplexity gap-fill is wired in Task 5; this task builds the deterministic path and leaves an explicit hook.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/analysis/fact_pack/test_composer.py`:

```python
"""Routing, merge order and FactPack construction."""

import pytest

from finwiz.analysis.fact_pack import composer
from finwiz.analysis.fact_pack.fragment import PLACEHOLDER, FactPackFragment


@pytest.fixture(autouse=True)
def _no_gap_fill(mocker):
    """Deterministic path only; Task 5 wires and tests the Perplexity hook."""
    mocker.patch.object(composer, "_gap_fill", return_value=FactPackFragment())


class TestRouting:
    def test_asset_class_comes_from_the_caller_never_from_the_symbol(self, mocker):
        """ASML.AS is 7 characters; a symbol-shape heuristic once called that crypto.

        Routing reads the declared class and nothing else.
        """
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "EQUITY", "longBusinessSummary": "Chip lithography."})
        equity = mocker.patch.object(composer.yfinance_source, "equity_fragment", return_value=FactPackFragment(corporate_structure="Chip lithography."))
        crypto = mocker.patch.object(composer.yfinance_source, "crypto_fragment", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        composer.compose_fact_pack("ASML.AS", "ASML Holding", None, None, "stock")

        equity.assert_called_once()
        crypto.assert_not_called()

    def test_a_declared_class_that_contradicts_quote_type_is_warned_about(self, mocker, caplog):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "ETF", "fundFamily": "iShares"})
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        composer.compose_fact_pack("2B7K.DE", "iShares World", None, None, "stock")

        assert any("declared asset_class" in r.message for r in caplog.records)


class TestUnresolvable:
    def test_an_unresolvable_ticker_returns_none(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"trailingPegRatio": None})
        assert composer.compose_fact_pack("ZZZZNOTREAL", "Nothing", None, None, "stock") is None


class TestPackConstruction:
    def test_filings_outrank_news_for_recent_events(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "EQUITY", "longBusinessSummary": "Designs phones."})
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment(recent_events=("2026-09-01 8-K: Changes",), events_from_filings=True, sources=("yfinance.sec_filings",)))
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment(recent_events=("A headline",), sources=("yfinance.news",)))

        pack = composer.compose_fact_pack("AAPL", "Apple Inc.", None, None, "stock")

        assert pack.recent_events == ["2026-09-01 8-K: Changes"]
        assert "yfinance.sec_filings" in pack.sources_used

    def test_empty_fields_become_the_placeholder_not_an_empty_string(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "CRYPTOCURRENCY", "longName": "Bitcoin USD"})
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        pack = composer.compose_fact_pack("BTC-USD", "Bitcoin", None, None, "crypto")

        # FactPack requires min_length=1 on both; the placeholder satisfies the
        # schema without asserting a fact nobody has.
        assert pack.corporate_structure == PLACEHOLDER
        assert pack.leadership == PLACEHOLDER
        assert pack.confidence == 0.0

    def test_freshness_stays_python_owned(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "EQUITY", "longBusinessSummary": "Designs phones."})
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())

        pack = composer.compose_fact_pack("AAPL", "Apple Inc.", None, None, "stock")

        assert pack.freshness == "fresh"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_composer.py -v`
Expected: FAIL — `ImportError: cannot import name 'composer'`

- [ ] **Step 3: Write the implementation**

Create `src/finwiz/analysis/fact_pack/composer.py`:

```python
"""Route by declared asset class, merge fragments, build the FactPack."""

from __future__ import annotations

from datetime import UTC, datetime

from finwiz.analysis.fact_pack.fragment import PLACEHOLDER, FactPackFragment, derive_confidence, merge_fragments
from finwiz.analysis.fact_pack.sources import yfinance_source
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# quoteType values that corroborate a declared asset class. A mismatch does not
# change routing -- the declared value is authoritative -- it only warns. This
# repo once classified 33 European tickers as crypto from symbol length alone
# and nothing said a word; this is the cheap detector for that class of bug.
_EXPECTED_QUOTE_TYPES: dict[str, frozenset[str]] = {
    "stock": frozenset({"EQUITY"}),
    "etf": frozenset({"ETF", "MUTUALFUND"}),
    "crypto": frozenset({"CRYPTOCURRENCY"}),
}


def _gap_fill(ticker: str, company_name: str, sector: str | None, industry: str | None, missing: tuple[str, ...]) -> FactPackFragment:
    """Hook for the Perplexity gap-fill. Wired in Task 5; inert until then."""
    return FactPackFragment()


def _identity_fragment(ticker: str, asset_class: str, info: dict) -> FactPackFragment:
    if asset_class == "etf":
        return yfinance_source.etf_fragment(ticker, info)
    if asset_class == "crypto":
        return yfinance_source.crypto_fragment(info)
    return yfinance_source.equity_fragment(info)


def _missing_fields(fragment: FactPackFragment) -> tuple[str, ...]:
    missing: list[str] = []
    if not fragment.corporate_structure:
        missing.append("corporate_structure")
    if not fragment.leadership:
        missing.append("leadership")
    if not fragment.recent_events:
        missing.append("recent_events")
    return tuple(missing)


def compose_fact_pack(ticker: str, company_name: str, sector: str | None, industry: str | None, asset_class: str) -> FactPack | None:
    """Build a pack from free structured sources.

    Returns None ONLY when the ticker resolves to nothing. Every other outcome is
    a pack, however thin -- one provider must never be able to halt a holding,
    which is exactly what happened on 2026-09-06 when a quota error took all 64.
    """
    info = yfinance_source.resolve(ticker)
    if not yfinance_source.is_resolvable(info):
        logger.warning(f"fact_pack: {ticker} resolves to nothing (no quoteType); cannot build a pack")
        return None

    quote_type = info.get("quoteType")
    expected = _EXPECTED_QUOTE_TYPES.get(asset_class)
    if expected is not None and quote_type not in expected:
        logger.warning(f"fact_pack: {ticker} declared asset_class={asset_class!r} but yfinance reports quoteType={quote_type!r}; routing follows the declared value")

    # Fixed precedence per asset class: identity first, then filings, then news.
    # Filings outrank news because merge takes the first non-empty events tuple.
    fragment = merge_fragments(
        _identity_fragment(ticker, asset_class, info),
        yfinance_source.filing_events(ticker),
        yfinance_source.news_events(ticker),
    )

    missing = _missing_fields(fragment)
    if missing:
        fragment = merge_fragments(fragment, _gap_fill(ticker, company_name, sector, industry, missing))

    fetched_at = datetime.now(UTC)
    return FactPack(
        corporate_structure=fragment.corporate_structure or PLACEHOLDER,
        recent_events=list(fragment.recent_events),
        leadership=fragment.leadership or PLACEHOLDER,
        fetched_at=fetched_at,
        freshness=FactPack.derive_freshness(fetched_at),
        confidence=derive_confidence(fragment),
        source_citations=list(fragment.citations),
        sources_used=list(fragment.sources),
    )
```

Replace the contents of `src/finwiz/analysis/fact_pack/__init__.py` with:

```python
"""Deterministic fact pack construction from free structured sources."""

from finwiz.analysis.fact_pack.composer import compose_fact_pack

__all__ = ["compose_fact_pack"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/analysis/fact_pack/ -v`
Expected: PASS

- [ ] **Step 5: Mutation check**

Swap the `filing_events` and `news_events` arguments in the `merge_fragments` call and re-run `test_filings_outrank_news_for_recent_events`. It must FAIL. Restore by editing back.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/analysis/fact_pack/ tests/unit/analysis/fact_pack/test_composer.py
git commit -m "feat(fact-pack): composer routes by declared asset class and builds the pack"
```

---

### Task 5: Perplexity gap-fill and the seam swap

**Files:**
- Create: `src/finwiz/analysis/fact_pack/sources/perplexity_source.py`
- Modify: `src/finwiz/analysis/fact_pack/composer.py` (replace `_gap_fill`)
- Modify: `src/finwiz/analysis/fact_pack_research.py` (`fetch_fact_pack_sync` body, new `asset_class` parameter)
- Modify: `src/finwiz/analysis/stages/fact_pack.py` (thread `asset_class`)
- Test: `tests/unit/analysis/fact_pack/test_gap_fill.py`
- Test: `tests/unit/analysis/test_fact_pack_research.py` (update existing)

**Interfaces:**
- Consumes: `FactPackFragment`; the existing `perplexity_with_retry`, `_FactPackRaw` and `_SYSTEM_FR` from `fact_pack_research.py`.
- Produces: `fetch_missing(ticker, company_name, sector, industry, missing: tuple[str, ...], timeout: float = 15.0) -> FactPackFragment`; `fetch_fact_pack_sync(ticker, company_name, sector=None, industry=None, *, asset_class="stock", timeout=15.0) -> FactPack | None`.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/analysis/fact_pack/test_gap_fill.py`:

```python
"""Gap-fill may add. It may never overwrite, and it may never fail a pack."""

import pytest

from finwiz.analysis.fact_pack import composer
from finwiz.analysis.fact_pack.fragment import FactPackFragment
from finwiz.analysis.fact_pack.sources import perplexity_source


@pytest.fixture
def resolved_etf(mocker):
    mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "ETF", "fundFamily": "iShares", "legalType": "Exchange Traded Fund", "longName": "iShares World"})
    mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
    mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())


class TestGapFillIsCalledOnlyForMissingFields:
    def test_only_the_empty_fields_are_requested(self, mocker, resolved_etf):
        fetch = mocker.patch.object(perplexity_source, "fetch_missing", return_value=FactPackFragment())
        mocker.patch.object(composer, "is_feature_enabled", return_value=True)

        composer.compose_fact_pack("2B7K.DE", "iShares World", None, None, "etf")

        # The ETF fragment already supplies structure and leadership.
        assert fetch.call_args.args[4] == ("recent_events",)

    def test_a_complete_pack_never_calls_perplexity(self, mocker):
        mocker.patch.object(composer.yfinance_source, "resolve", return_value={"quoteType": "EQUITY", "longBusinessSummary": "Designs phones.", "companyOfficers": [{"name": "Tim Cook", "title": "CEO"}]})
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment(recent_events=("2026-09-01 8-K: Changes",), events_from_filings=True))
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())
        fetch = mocker.patch.object(perplexity_source, "fetch_missing")
        mocker.patch.object(composer, "is_feature_enabled", return_value=True)

        composer.compose_fact_pack("AAPL", "Apple Inc.", None, None, "stock")

        fetch.assert_not_called()

    def test_the_feature_flag_switches_it_off_entirely(self, mocker, resolved_etf):
        fetch = mocker.patch.object(perplexity_source, "fetch_missing")
        mocker.patch.object(composer, "is_feature_enabled", return_value=False)

        composer.compose_fact_pack("2B7K.DE", "iShares World", None, None, "etf")

        fetch.assert_not_called()


class TestGapFillCannotDamageAPack:
    def test_it_may_add_but_never_overwrite(self, mocker, resolved_etf):
        mocker.patch.object(composer, "is_feature_enabled", return_value=True)
        mocker.patch.object(
            perplexity_source,
            "fetch_missing",
            return_value=FactPackFragment(corporate_structure="An LLM's rival account.", recent_events=("Fund rebalanced",), sources=("perplexity",)),
        )

        pack = composer.compose_fact_pack("2B7K.DE", "iShares World", None, None, "etf")

        assert "iShares" in pack.corporate_structure  # deterministic answer survived
        assert pack.recent_events == ["Fund rebalanced"]  # the genuinely empty field was filled

    def test_a_quota_401_leaves_the_deterministic_pack_intact(self, mocker, resolved_etf):
        mocker.patch.object(composer, "is_feature_enabled", return_value=True)
        mocker.patch.object(perplexity_source, "fetch_missing", side_effect=RuntimeError("Perplexity HTTP 401 insufficient_quota"))

        pack = composer.compose_fact_pack("2B7K.DE", "iShares World", None, None, "etf")

        # The 2026-09-06 outage in one assertion: this must not raise and must
        # not return None.
        assert pack is not None
        assert "iShares" in pack.corporate_structure
        assert pack.recent_events == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/analysis/fact_pack/test_gap_fill.py -v`
Expected: FAIL — `ImportError: cannot import name 'perplexity_source'`

- [ ] **Step 3: Write the gap-fill source**

Create `src/finwiz/analysis/fact_pack/sources/perplexity_source.py`:

```python
"""Perplexity, narrowed to the fields structured data could not supply.

It is called for a minority of holdings and asked for a minority of fields. On
this portfolio that is 31 calls a run instead of 64, and zero with
FF_PERPLEXITY_RESEARCH off.
"""

from __future__ import annotations

from finwiz.analysis.fact_pack.fragment import FactPackFragment
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_FIELD_INSTRUCTIONS: dict[str, str] = {
    "corporate_structure": "**corporate_structure** (≤2000 chars) : structure actuelle de l'entité — société-mère, filiales, divisions, et toute cession ou acquisition majeure des 24 derniers mois.",
    "leadership": "**leadership** (≤1000 chars) : CEO et CFO actuels avec dates de prise de fonction si récents (<24 mois).",
    "recent_events": "**recent_events** (liste de 0 à 10 strings, ≤200 chars chacun) : événements matériels des 12 derniers mois. Pas de bavardage marketing.",
}


def _build_prompt(ticker: str, company_name: str, sector: str | None, industry: str | None, missing: tuple[str, ...]) -> str:
    from finwiz.analysis._helpers import _today_french

    asked = "\n\n".join(_FIELD_INSTRUCTIONS[field] for field in missing if field in _FIELD_INSTRUCTIONS)
    return (
        f"Date du jour : {_today_french()}.\n\n"
        f"Recherche les faits VÉRIFIÉS et ACTUELS sur {company_name} ({ticker}, "
        f"{sector or 'secteur inconnu'} / {industry or 'industrie inconnue'}).\n\n"
        f"Réponds UNIQUEMENT pour les champs suivants :\n\n{asked}\n\n"
        "Ajoute source_citations (URLs, max 20). Si tu n'as PAS de source fiable "
        "pour un champ, laisse-le vide — ne pas inventer."
    )


def fetch_missing(
    ticker: str,
    company_name: str,
    sector: str | None,
    industry: str | None,
    missing: tuple[str, ...],
    timeout: float = 15.0,
) -> FactPackFragment:
    """Ask only for `missing`. Any failure returns an empty fragment, never raises."""
    from finwiz.analysis.fact_pack_research import _SYSTEM_FR, _FactPackRaw, _run_coroutine_sync
    from finwiz.infrastructure.resilience.perplexity_retry import perplexity_with_retry

    try:
        raw = _run_coroutine_sync(
            perplexity_with_retry(
                prompt=_build_prompt(ticker, company_name, sector, industry, missing),
                schema=_FactPackRaw,
                system=_SYSTEM_FR,
                search_recency_filter="month",
                timeout=timeout,
            ),
            timeout=timeout,
        )
    except Exception as e:
        logger.warning(f"fact_pack gap-fill failed for {ticker} ({', '.join(missing)}): {e}")
        return FactPackFragment()

    if raw is None:
        return FactPackFragment()

    return FactPackFragment(
        corporate_structure=raw.corporate_structure if "corporate_structure" in missing else None,
        leadership=raw.leadership if "leadership" in missing else None,
        recent_events=tuple(raw.recent_events) if "recent_events" in missing else (),
        citations=tuple(raw.source_citations),
        sources=("perplexity.gap_fill",),
    )
```

- [ ] **Step 4: Wire it into the composer**

In `composer.py`, add the imports:

```python
from finwiz.analysis.fact_pack.sources import perplexity_source, yfinance_source
from finwiz.config.features.flags import is_feature_enabled
```

and replace the `_gap_fill` stub with:

```python
def _gap_fill(ticker: str, company_name: str, sector: str | None, industry: str | None, missing: tuple[str, ...]) -> FactPackFragment:
    """Ask Perplexity for the empty fields only. Never raises, never overwrites.

    Merge order at the call site puts the deterministic fragment first, so this
    result can only occupy fields nothing else filled.
    """
    if not is_feature_enabled("perplexity_research"):
        logger.debug(f"fact_pack gap-fill skipped for {ticker}: perplexity_research disabled")
        return FactPackFragment()
    try:
        return perplexity_source.fetch_missing(ticker, company_name, sector, industry, missing)
    except Exception as e:
        logger.warning(f"fact_pack gap-fill raised for {ticker}; keeping the deterministic pack: {e}")
        return FactPackFragment()
```

- [ ] **Step 5: Extract the sync runner and swap the seam**

In `src/finwiz/analysis/fact_pack_research.py`, extract the existing event-loop juggling from `fetch_fact_pack_sync` into a reusable helper so `perplexity_source` can share it verbatim:

```python
def _run_coroutine_sync(coro: Any, *, timeout: float) -> Any:
    """Run a coroutine from sync code, including from inside a running loop.

    Inside a running event loop, asyncio.run() raises; a worker thread is the
    escape. shutdown(wait=False, cancel_futures=True) keeps a timeout from
    blocking on that thread.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(asyncio.run, coro)
            try:
                return future.result(timeout=timeout + 5.0)
            except concurrent.futures.TimeoutError:
                future.cancel()
                return None
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    return asyncio.run(coro)
```

Then replace `fetch_fact_pack_sync` entirely:

```python
def fetch_fact_pack_sync(
    ticker: str,
    company_name: str,
    sector: str | None = None,
    industry: str | None = None,
    *,
    asset_class: str = "stock",
    timeout: float = 15.0,
) -> FactPack | None:
    """Build a fact pack from free structured sources, gap-filled by Perplexity.

    Returns None only when the ticker resolves to nothing; the caller treats that
    as "cannot build a pack" and falls back to cache or FAILED. `timeout` is
    accepted for call-site compatibility and applies to the gap-fill leg.
    """
    from finwiz.analysis.fact_pack import compose_fact_pack

    return compose_fact_pack(ticker, company_name, sector, industry, asset_class)
```

Leave `fetch_fact_pack`, `_FactPackRaw`, `_SYSTEM_FR` and `_build_prompt` in place — `_FactPackRaw` and `_SYSTEM_FR` are imported by `perplexity_source`.

- [ ] **Step 6: Thread asset_class through the stage**

In `src/finwiz/analysis/stages/fact_pack.py`, change `_fact_pack_inner`'s signature to take `asset_class: str` and pass it on:

```python
def _fact_pack_inner(ticker: str, company_name: str, sector: str | None, industry: str | None, asset_class: str) -> FactPack:
```

and inside it:

```python
    fetched = fetch_fact_pack_sync(ticker, company_name, sector, industry, asset_class=asset_class)
```

In the `fact_pack` stage function, read the declared class and pass it:

```python
    asset_class = getattr(analysis_ctx, "asset_class", None) or "stock"
    return _fact_pack_inner(ticker, company_name, sector, industry, asset_class)
```

- [ ] **Step 7: Run the full affected suite**

Run: `uv run pytest tests/unit/analysis/ tests/unit/schemas/test_fact_pack.py tests/unit/cache/test_fact_pack_cache.py -v`
Expected: PASS. Existing tests in `tests/unit/analysis/test_fact_pack_research.py` that assert the old Perplexity-first behaviour of `fetch_fact_pack_sync` will fail — update them to target `fetch_fact_pack` (the async Perplexity path, unchanged) or to the new composed behaviour. Do not delete a test to make it pass; if a test no longer describes intended behaviour, rewrite what it asserts and say so in the commit message.

- [ ] **Step 8: Run the whole suite**

Run: `make test`
Expected: PASS, no regressions.

- [ ] **Step 9: Mutation check**

In `_gap_fill`, change `if not is_feature_enabled("perplexity_research"):` to `if False:` and re-run `test_the_feature_flag_switches_it_off_entirely`. It must FAIL. Restore by editing back.

- [ ] **Step 10: Lint and commit**

```bash
uv run ruff check src/finwiz/analysis/ tests/unit/analysis/
uv run ruff format --check src/finwiz/analysis/ tests/unit/analysis/
uv run mypy src/finwiz/analysis/fact_pack/
git add src/finwiz/analysis/ tests/unit/analysis/
git commit -m "feat(fact-pack): Perplexity fills only the fields structured data left empty"
```

---

### Task 6: Documentation

**Files:**
- Modify: `docs/adr/ADR-010-fact-pack-grounded-qualitative.md`
- Modify: `CHANGELOG.md`
- Modify: `CLAUDE.md`
- Modify: `docs/PRD.md`
- Test: none — prose only. Verified by reading, and by the grep in Step 5.

**Interfaces:**
- Consumes: the behaviour built in Tasks 1–5.
- Produces: nothing code depends on.

No task may leave a doc asserting the old behaviour. ADR-010 currently describes
the fact pack as Perplexity-fetched; that is now false for the majority of
holdings, and an ADR read as current is acted on.

- [ ] **Step 1: Supersede the relevant part of ADR-010**

Read `docs/adr/ADR-010-fact-pack-grounded-qualitative.md`. Do NOT rewrite the
decision — an ADR is a dated record. Add a section at the end:

```markdown
## Superseded in part (2026-09-06)

The *grounding* decision stands: qualitative analysis is fed verified facts
rather than trusting the model's recall. The *source* decision does not. This
ADR specified Perplexity as the fact pack's provider; on 2026-09-06 a quota
error (`insufficient_quota`, served as HTTP 401) made that single provider fail
all 64 holdings in one run — `fact_pack failed ×64`, zero holdings analysed.

Fact packs are now built from free structured sources (yfinance `info`,
`companyOfficers`, `sec_filings`, filtered `news`), with Perplexity called only
for fields the structured data left empty. `confidence` is derived by Python
from field completeness rather than self-rated by the model.

See `docs/superpowers/specs/2026-09-06-deterministic-fact-pack-design.md`.
```

- [ ] **Step 2: Add the CHANGELOG entry**

Add under the `Unreleased` heading (create it directly below the intro block if
absent), matching the file's existing bullet style:

```markdown
### Changed

- **Fact packs are built from structured data, not an LLM.** `corporate_structure`,
  `leadership` and `recent_events` now come from yfinance — business summaries,
  officer lists, and for US listings and ADRs the SEC filing index with EDGAR
  links. Perplexity is called only for fields those sources leave empty, so a
  quota outage costs a few ETF event lists instead of every holding in the run.
- **`FactPack.confidence` is Python-derived.** It is a completeness score over the
  populated fields, not the model's opinion of itself, so it is comparable
  between holdings and across runs.
- **`FactPack.sources_used`** records which sources produced each pack. Packs
  cached before this field existed still load.
```

- [ ] **Step 3: Correct CLAUDE.md**

In the Environment Variables block, the line describing `FF_PERPLEXITY_RESEARCH`
must state its new scope. Replace the existing feature-flag comment line with:

```
# Feature flags are all FF_-prefixed, e.g. FF_PERPLEXITY_RESEARCH
#   (full registry: config/features/definitions.py)
# FF_PERPLEXITY_RESEARCH=false makes fact packs fully deterministic: yfinance
#   supplies every field and no gap-fill call is made. Fact packs never fail a
#   holding for want of Perplexity.
```

- [ ] **Step 4: Correct docs/PRD.md**

Run `grep -n "fact.pack\|fact_pack\|Perplexity" docs/PRD.md`. Where it states or
implies that fact packs come from Perplexity, correct it to name the structured
sources with Perplexity as gap-filler. Change only those sentences; leave the
rest of the PRD alone.

- [ ] **Step 5: Fix the two stale docstrings the Task 1 review found**

Docstrings rot the same way prose docs do, and these two now contradict the code beside them.

In `src/finwiz/schemas/hybrid_analysis/fact_pack.py`, the `FactPack` class docstring still reads "fetched once per holding via Perplexity, cached 7 days". Replace that clause with:

```
    Lifecycle: built once per holding from structured sources (see
    analysis/fact_pack/composer.py), gap-filled by Perplexity only where those
    sources are empty, and cached 7 days. The `freshness` field is Python-derived
    from `fetched_at` -- AI cannot lie about it (cross-checked by model_validator).
```

In `src/finwiz/analysis/fact_pack/fragment.py`, `merge_fragments`'s docstring claims "the first non-empty value for a field wins", which is true of `corporate_structure`, `leadership` and `recent_events` but not of `citations` and `sources`, which accumulate across every fragment. Add that clause so a reader who skims only the docstring is not misled.

- [ ] **Step 6: Verify nothing still claims the old behaviour**

Run:

```bash
grep -rn "fact.pack" --include="*.md" docs/adr docs/PRD.md CLAUDE.md README.md | grep -i perplexity
```

Expected: every remaining hit is either inside the ADR's own historical record
(the decision as it was taken) or explicitly describes gap-fill. Any line that
presents Perplexity as *the* fact-pack source is a miss — fix it.

- [ ] **Step 7: Commit**

```bash
git add docs/adr/ADR-010-fact-pack-grounded-qualitative.md CHANGELOG.md CLAUDE.md docs/PRD.md src/finwiz/schemas/hybrid_analysis/fact_pack.py src/finwiz/analysis/fact_pack/fragment.py
git commit -m "docs(fact-pack): supersede ADR-010's source decision; record the new provider chain"
```

---

### Task 7: Live verification

**Files:** none changed. This task produces evidence.

**Interfaces:**
- Consumes: everything above, Task 6 included.
- Produces: the numbers for the PR body, and proof that a Perplexity outage can no longer empty a run.

**Requires explicit authorisation before running** — the flow spends real money. Do not start it on your own initiative.

- [ ] **Step 1: Prove the deterministic path alone covers the portfolio**

Run, with no network mocking and the cache untouched:

```bash
uv run python -c "
from finwiz.analysis.fact_pack import compose_fact_pack
for ticker, name, cls in [('AAPL','Apple Inc.','stock'), ('ASML','ASML Holding','stock'), ('AIR.PA','Airbus SE','stock'), ('2B7K.DE','iShares MSCI World SRI','etf'), ('BTC-USD','Bitcoin','crypto'), ('ZZZZNOTREAL','Nothing','stock')]:
    p = compose_fact_pack(ticker, name, None, None, cls)
    print(f'{ticker:12} {\"None\" if p is None else f\"conf={p.confidence} events={len(p.recent_events)} cites={len(p.source_citations)} src={p.sources_used}\"}')
"
```

Expected: AAPL and ASML around 1.0 with filing-derived events; AIR.PA 0.85 or 0.70 depending on wire coverage that day; 2B7K.DE 0.70 with 0 events; BTC-USD 0.25 or lower; ZZZZNOTREAL `None`.

- [ ] **Step 2: Prove the outage cannot recur**

Run the same command with the flag off and the fact-pack cache moved aside:

```bash
mv cache/fact_packs /tmp/fact_packs_backup_$(date +%s)
FF_PERPLEXITY_RESEARCH=false uv run python -c "..."   # same script as Step 1
```

Expected: every resolvable ticker still returns a pack. This is the 2026-09-06 condition exactly — cold cache, no Perplexity — which previously produced `fact_pack failed ×64`.

Restore the cache directory afterwards.

- [ ] **Step 3: Full run (authorisation required)**

Run: `uv run kickoff; echo "exit=$?"`

Expected: `run gate: coverage` well above 0/64, and `fact_pack_missing` far below 64. Record the eight gate lines for the PR body.

- [ ] **Step 4: Cross-check the packs on disk**

```bash
uv run python -c "
import json, pathlib, statistics
packs = [json.loads(p.read_text()) for p in pathlib.Path('cache/fact_packs').glob('*.json')]
print('packs', len(packs))
print('mean confidence', round(statistics.mean(p['confidence'] for p in packs), 3))
print('with filings', sum(1 for p in packs if 'yfinance.sec_filings' in p.get('sources_used', [])))
print('gap-filled', sum(1 for p in packs if 'perplexity.gap_fill' in p.get('sources_used', [])))
"
```

Expected: `sources_used` populated on every newly written pack; the filing count roughly matches the US-listed holdings.

- [ ] **Step 5: Record the results**

Append the numbers to `.superpowers/sdd/<session>/progress.md` and to the PR body.

---

## Self-Review

**Spec coverage.** D1 gap-filler → Task 5. D2 FAIL only when unresolvable → Task 4 (`compose_fact_pack` returns `None` solely on `is_resolvable` false) and Task 2's resolvability tests. D3 cache and ladder kept → untouched by construction; Task 5 Step 7 runs the cache tests to prove it. D4 confidence derived → Task 1. D5 declared routing → Task 4's first test, plus the `quoteType` warning. D6 CoinGecko out of scope → no task, deliberately. §2 components → Tasks 1–4 file-for-file. §3 composition order → Task 4. §4 confidence table → Task 1's weights and four expected-value tests. §5 schema change → Task 1 Steps 5–7 including the backward-compatibility test for the 58 cached packs. §6 error handling: unresolvable → Task 4; per-source degradation → Tasks 2 and 3; inert Perplexity failure → Task 5's 401 test; `quoteType` cross-check → Task 4. 429 backoff is NOT separately implemented — `resolve` and both event accessors already swallow every exception into an empty fragment, which is the specified degradation; sequential fetching is the existing call pattern, unchanged. §7 testing → every task ends with a mutation check. Documentation → Task 6, added after the plan was first written on the standing instruction that docs ship with the change; it supersedes ADR-010's source decision rather than rewriting it.

**Placeholder scan.** None. Every code step carries runnable code. Task 6 Step 2's `# same script as Step 1` refers to a script written out in full one step earlier, in the same task.

**Type consistency.** `FactPackFragment` field names are identical across Tasks 1–5. `merge_fragments(*fragments)` is variadic in Task 1 and called variadically in Task 4. `derive_confidence(fragment)` matches. `_gap_fill(ticker, company_name, sector, industry, missing)` has the same five parameters as its Task 5 replacement, and Task 5's test asserts `call_args.args[4] == ("recent_events",)`, which is `missing` — the fifth positional argument of `fetch_missing`, whose signature places `missing` fifth. `fetch_fact_pack_sync` gains `asset_class` as a keyword-only argument in Task 5 and the stage passes it by keyword. `compose_fact_pack` is positional-only at every call site and its five parameters match Task 4's definition. `_run_coroutine_sync(coro, *, timeout)` is defined in Task 5 Step 5 and called with that shape in `perplexity_source.fetch_missing`.
