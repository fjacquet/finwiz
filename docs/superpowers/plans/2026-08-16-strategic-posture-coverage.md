# Strategic Posture: Coverage, Dedicated Page, Safe Rendering — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the portfolio strategic posture cover every holding with real data, move it to its own readable page, and render model markdown safely instead of dumping it into HTML.

**Architecture:** Three layers, in dependency order. First the pipeline stops losing holdings (cap the model's output so it never overruns our token ceiling; stop timeouts from opening the circuit breaker; digest instead of truncate). Then the schema is made incapable of hiding a gap (coverage fields and scores become required). Then the report gains a markdown render boundary and a dedicated posture page.

**Tech Stack:** Python 3.13, Pydantic v2, pytest + pytest-mock, CrewAI Flows, Perplexity via `crewai-custom-tools`.

**Spec:** `docs/superpowers/specs/2026-08-16-strategic-posture-coverage-design.md`

## Global Constraints

- **unittest.mock is BANNED** — use pytest-mock (`mocker.patch()`). Enforced by ruff and `make check-unittest-mock`.
- **Line length 180** — `pyproject.toml:93` `line-length = 180`.
- **Target Python:** 3.13 — `pyproject.toml:97` `target-version = "py313"`.
- **`json.dumps` always uses `default=str`.**
- **All Pydantic models live in `schemas/`**, not in domain folders.
- **Reports are French.** User-visible strings in this plan are French and stay French.
- **AI Minimalism:** Python does deterministic work (digesting, clamping, counting coverage, rendering). AI is asked only for judgement. When Python and AI disagree, Python wins.
- **No fabricated defaults.** A field that means "no answer" must read as no answer, never as a plausible middle value. See `c2a17d1a`.

---

## File Structure

**Modify:**

- `src/finwiz/infrastructure/resilience/crew_execution.py` — breaker: exclude timeouts, wait rather than fail-fast (Tasks 1–2)
- `src/finwiz/schemas/hybrid_analysis/strategic.py` — field caps, coverage fields, required scores, verdicts (Tasks 3, 6)
- `src/finwiz/analysis/strategic_research.py` — prompts state caps; digest replaces truncation; per-asset-class prompts (Tasks 4, 5, 8)
- `src/finwiz/analysis/stages/__init__.py:100` — remove the stock-only gate (Task 8)
- `src/finwiz/orchestrators/reporting/enrichment.py:323` — pass coverage into the synthesis (Task 7)
- `src/finwiz/reporting/sections/insights.py` — family artifact shrinks to a 3-line summary + link (Task 11)

**Create:**

- `src/finwiz/reporting/markdown_fragment.py` — the render boundary (Task 9)
- `src/finwiz/reporting/sections/posture_page.py` — the dedicated page (Task 10)
- `tests/unit/reporting/test_markdown_fragment.py` (Task 9)
- `tests/unit/reporting/test_posture_page.py` (Task 10)

---

### Task 1: Timeouts must not open the circuit breaker

**Why:** In the 2026-08-16 run, five consecutive crew timeouts opened the breaker and 31 further holdings failed instantly without being attempted — after `collect`, `quantify` and `fact_pack` had all succeeded for them. `ValidationError` already bypasses the counter for exactly this reason (see the comment citing the 2026-04-28 ETF cascade at `crew_execution.py:150-155`); `TimeoutError` never got the same treatment.

**Files:**

- Modify: `src/finwiz/infrastructure/resilience/crew_execution.py:157-166`
- Test: `tests/unit/infrastructure/resilience/test_crew_execution.py`

**Interfaces:**

- Consumes: nothing from earlier tasks.
- Produces: no signature change. `execute_crew_with_timeout` keeps raising `TimeoutError`; only the breaker bookkeeping changes.

- [ ] **Step 1: Write the failing test**

```python
def test_timeout_does_not_increment_breaker_counter(mocker):
    """A timeout is a per-holding event, not an upstream outage.

    Five slow holdings must not blind 31 healthy ones. ValidationError already
    bypasses the counter for the same reason (the 2026-04-28 ETF cascade); this
    pins the timeout half of that lesson.
    """
    from finwiz.infrastructure.resilience import crew_execution

    crew_execution.reset_circuit_breakers()
    mocker.patch.object(crew_execution, "CREW_TIMEOUT", 0.01)

    slow_crew = mocker.Mock()
    slow_crew.kickoff = lambda inputs: time.sleep(1.0)

    for _ in range(6):
        with pytest.raises(TimeoutError):
            asyncio.run(crew_execution.execute_crew_with_timeout(slow_crew, "deep_analysis_stock", {}))

    assert crew_execution._crew_failures.get("deep_analysis_stock", 0) == 0
    assert "deep_analysis_stock" not in crew_execution._crew_circuit_open
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/infrastructure/resilience/test_crew_execution.py::test_timeout_does_not_increment_breaker_counter -v`
Expected: FAIL — the counter reaches 6 and the breaker opens.

- [ ] **Step 3: Write minimal implementation**

Split the handler at `crew_execution.py:157`. Replace `except (TimeoutError, Exception) as exc:` with two clauses:

```python
    except TimeoutError:
        # A timeout is a per-holding event, not an upstream failure. Counting it
        # opens the breaker, and because holdings run concurrently an open breaker
        # fails every queued holding instantly — 31 lost in the 2026-08-16 run,
        # each of which had already completed collect, quantify and fact_pack.
        # Same reasoning as the ValidationError clause above.
        logger.warning(f"Crew {crew_name} timed out after {effective_timeout}s (breaker counter unchanged)")
        raise

    except Exception as exc:
        _crew_failures[crew_name] = _crew_failures.get(crew_name, 0) + 1
        failure_count = _crew_failures[crew_name]
        logger.warning(f"Crew {crew_name} failed ({failure_count}/{failure_threshold}): {exc!r}")

        if failure_count >= failure_threshold:
            _crew_circuit_open[crew_name] = time.time()
            logger.error(f"Circuit breaker OPEN for {crew_name} after {failure_count} consecutive failures")

        raise
```

Note `{exc!r}` rather than `{exc}`: `TimeoutError()` stringifies to empty, which is why the run logged `Crew deep_analysis_stock failed (5/5):` with no reason. `repr` always shows the type.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/infrastructure/resilience/test_crew_execution.py -v`
Expected: PASS, including the existing breaker tests (a non-timeout exception must still open it).

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/infrastructure/resilience/crew_execution.py tests/unit/infrastructure/resilience/test_crew_execution.py
git commit -m "fix(resilience): stop timeouts from opening the crew circuit breaker"
```

---

### Task 2: An open breaker makes a holding wait, not fail

**Why:** Even with Task 1, a genuine outage opens the breaker and every concurrent holding is rejected in the same instant. The cooldown exists to be waited out.

**Files:**

- Modify: `src/finwiz/infrastructure/resilience/crew_execution.py:124-131`
- Test: `tests/unit/infrastructure/resilience/test_crew_execution.py`

**Interfaces:**

- Consumes: Task 1's split exception handling.
- Produces: `execute_crew_with_timeout` may now sleep up to the remaining cooldown before raising. The outer `FINWIZ_HOLDING_TIMEOUT` (900s) remains the hard bound.

- [ ] **Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_open_breaker_waits_for_cooldown_then_retries(mocker):
    """An open breaker should cost a holding time, not its analysis."""
    from finwiz.infrastructure.resilience import crew_execution

    crew_execution.reset_circuit_breakers()
    mocker.patch.object(crew_execution, "_get_recovery_timeout", lambda: 0.2)
    crew_execution._crew_circuit_open["deep_analysis_stock"] = time.time()

    good_crew = mocker.Mock()
    good_crew.kickoff = mocker.Mock(return_value="ok")

    result = await crew_execution.execute_crew_with_timeout(good_crew, "deep_analysis_stock", {})

    assert result == "ok"
    good_crew.kickoff.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/infrastructure/resilience/test_crew_execution.py::test_open_breaker_waits_for_cooldown_then_retries -v`
Expected: FAIL with `CircuitBreakerOpenError`.

- [ ] **Step 3: Write minimal implementation**

Replace the breaker check at `crew_execution.py:124-131`:

```python
    if crew_name in _crew_circuit_open:
        elapsed = time.time() - _crew_circuit_open[crew_name]
        remaining = recovery_timeout - elapsed
        if remaining > 0:
            # Wait the cooldown out rather than failing instantly. Holdings run
            # concurrently, so fail-fast here rejects every queued holding in the
            # same instant — the 31-holding cascade of 2026-08-16. The outer
            # FINWIZ_HOLDING_TIMEOUT still bounds total time.
            logger.warning(f"Circuit breaker OPEN for {crew_name}; waiting {remaining:.0f}s for cooldown")
            await asyncio.sleep(remaining)
        logger.info(f"Circuit breaker half-open for {crew_name}, allowing retry")
        _crew_circuit_open.pop(crew_name, None)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/infrastructure/resilience/ -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/infrastructure/resilience/crew_execution.py tests/unit/infrastructure/resilience/test_crew_execution.py
git commit -m "fix(resilience): wait out the breaker cooldown instead of failing queued holdings"
```

---

### Task 3: Cap the strategic schema fields

**Why:** AAPL's `strategic_analysis` is 33,505 chars — every one of the 18 sub-dimensions is a paragraph-length essay. That size overruns `max_tokens=40960` (six parse failures in one run, $0.63 each) and produces a 626,286-char synthesis payload. Clamping in the schema is the guarantee; the prompt (Task 4) is only the request.

**Files:**

- Modify: `src/finwiz/schemas/hybrid_analysis/strategic.py`
- Test: `tests/unit/schemas/test_strategic_caps.py` (create)

**Interfaces:**

- Consumes: nothing.
- Produces: `PestelAnalysis.political` … `.legal` become `list[str]` (was `str`). All other field names unchanged. Constants exported for reuse: `MAX_BULLETS_PESTEL = 3`, `MAX_BULLETS_SWOT = 4`, `MAX_BULLET_CHARS = 200`, `MAX_PROSE_CHARS = 400`, `MAX_RATIONALE_CHARS = 250`.

- [ ] **Step 1: Write the failing test**

```python
def test_oversized_model_output_is_clamped_not_rejected():
    """An over-long response must be trimmed, never raise.

    Rejecting would turn verbosity into a lost holding, which is the failure this
    whole plan exists to remove.
    """
    from finwiz.schemas.hybrid_analysis.strategic import MAX_BULLET_CHARS, PestelAnalysis

    pestel = PestelAnalysis.model_validate({
        "political": ["x" * 5000, "y" * 5000, "z" * 5000, "w" * 5000, "v" * 5000],
        "strategic_score": 0.7,
        "confidence": 0.8,
    })

    assert len(pestel.political) == 3
    assert all(len(b) <= MAX_BULLET_CHARS for b in pestel.political)


def test_prose_fields_are_clamped():
    from finwiz.schemas.hybrid_analysis.strategic import MAX_PROSE_CHARS, SwotAnalysis

    swot = SwotAnalysis.model_validate({"strategic_assessment": "a" * 9000, "strategic_score": 0.5, "confidence": 0.5})

    assert len(swot.strategic_assessment) <= MAX_PROSE_CHARS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/schemas/test_strategic_caps.py -v`
Expected: FAIL — `political` is currently a `str`, so `len()` is the character count, not 3.

- [ ] **Step 3: Write minimal implementation**

Add near the top of `strategic.py`, after `_coerce_str_list`:

```python
MAX_BULLETS_PESTEL = 3
MAX_BULLETS_SWOT = 4
MAX_BULLET_CHARS = 200
MAX_PROSE_CHARS = 400
MAX_RATIONALE_CHARS = 250


def _clamp_bullets(v: object, max_items: int) -> list[str]:
    """Trim a model's bullet list to the contract. Never raises: an over-long
    response is clamped, because rejecting it would cost the holding entirely."""
    items = _coerce_str_list(v)
    return [item[:MAX_BULLET_CHARS].rstrip() for item in items[:max_items]]


def _clamp_prose(v: object, max_chars: int) -> str:
    return _coerce_prose(v)[:max_chars].rstrip()
```

Change `PestelAnalysis`'s six dimension fields from `str` to `list[str]`:

```python
    political: list[str] = Field(default_factory=list, description="Political factors: max 3 bullets")
    economic: list[str] = Field(default_factory=list, description="Economic factors: max 3 bullets")
    social: list[str] = Field(default_factory=list, description="Social factors: max 3 bullets")
    technological: list[str] = Field(default_factory=list, description="Technological factors: max 3 bullets")
    environmental: list[str] = Field(default_factory=list, description="Environmental factors: max 3 bullets")
    legal: list[str] = Field(default_factory=list, description="Legal factors: max 3 bullets")
```

and replace its `_coerce_dimension` validator:

```python
    @field_validator("political", "economic", "social", "technological", "environmental", "legal", mode="before")
    @classmethod
    def _clamp_dimension(cls, v: object) -> list[str]:
        return _clamp_bullets(v, MAX_BULLETS_PESTEL)

    @field_validator("key_threats", "key_opportunities", mode="before")
    @classmethod
    def _clamp_key_lists(cls, v: object) -> list[str]:
        return _clamp_bullets(v, MAX_BULLETS_PESTEL)
```

In `SwotAnalysis`:

```python
    @field_validator("strengths", "weaknesses", "opportunities", "threats", mode="before")
    @classmethod
    def _clamp_lists(cls, v: object) -> list[str]:
        return _clamp_bullets(v, MAX_BULLETS_SWOT)

    @field_validator("strategic_assessment", mode="before")
    @classmethod
    def _clamp_assessment(cls, v: object) -> str:
        return _clamp_prose(v, MAX_PROSE_CHARS)
```

In `ForceRating`:

```python
    @field_validator("rationale", mode="before")
    @classmethod
    def _clamp_rationale(cls, v: object) -> str:
        return _clamp_prose(v, MAX_RATIONALE_CHARS)
```

In `FiveForcesAnalysis`:

```python
    @field_validator("competitive_position_summary", mode="before")
    @classmethod
    def _clamp_summary(cls, v: object) -> str:
        return _clamp_prose(v, MAX_PROSE_CHARS)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/schemas/ -v && uv run pytest tests/ -q -k strategic`
Expected: PASS. Any existing test treating `pestel.political` as a string must be updated to a list — that is the intended contract change, not a regression to work around.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/schemas/hybrid_analysis/strategic.py tests/unit/schemas/test_strategic_caps.py
git commit -m "feat(schemas): cap strategic fields so an over-long response is clamped, not lost"
```

---

### Task 4: Prompts request the caps

**Why:** The schema clamps, but clamping mid-sentence wastes the tokens we paid for and truncates meaning. The prompt has to ask for the right size in the first place — that is what removes the 40,960 overrun and the 224s crew runs.

**Files:**

- Modify: `src/finwiz/analysis/strategic_research.py:61-98` (the three prompt builders)
- Test: `tests/unit/analysis/test_strategic_prompts.py` (create)

**Interfaces:**

- Consumes: `MAX_BULLETS_PESTEL`, `MAX_BULLETS_SWOT`, `MAX_BULLET_CHARS` from Task 3.
- Produces: no signature change to `_pestel_prompt` / `_swot_prompt` / `_porter_prompt`.

- [ ] **Step 1: Write the failing test**

```python
def test_prompts_state_the_output_limits():
    """The caps must be requested, not only enforced.

    A prompt that asks for essays and a schema that clamps them means paying for
    tokens that are then thrown away.
    """
    from finwiz.analysis.strategic_research import _pestel_prompt, _porter_prompt, _swot_prompt

    pestel = _pestel_prompt("AAPL", "Tech", "Consumer Electronics", "", "16 août 2026")
    assert "3 puces" in pestel
    assert "200 caractères" in pestel

    swot = _swot_prompt("AAPL", "Tech", "Consumer Electronics", "", "16 août 2026")
    assert "4 puces" in swot

    porter = _porter_prompt("AAPL", "Tech", "Consumer Electronics", "", "16 août 2026")
    assert "250 caractères" in porter
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/analysis/test_strategic_prompts.py -v`
Expected: FAIL — the current prompts ask for "2-4 phrases chacune".

- [ ] **Step 3: Write minimal implementation**

Replace the body of `_pestel_prompt`:

```python
def _pestel_prompt(ticker: str, sector: str, industry: str, description: str, current_date: str) -> str:
    return (
        _date_preamble(current_date) + f"Analyse PESTEL pour {ticker} ({sector} / {industry}).\n"
        f"Description: {description or 'Non fournie'}\n\n"
        f"Pour chacune des six dimensions (politique, économique, social, technologique, "
        f"environnemental, légal) : au maximum {MAX_BULLETS_PESTEL} puces, chacune de "
        f"{MAX_BULLET_CHARS} caractères maximum. Pas de paragraphes, pas de prose. "
        f"Chaque puce cite une évolution des 12 mois précédant {current_date}. "
        f"Liste ensuite au maximum {MAX_BULLETS_PESTEL} menaces et {MAX_BULLETS_PESTEL} "
        f"opportunités, même format. "
        f"Termine en attribuant strategic_score et confidence."
    )
```

Apply the same shape to `_swot_prompt` (using `MAX_BULLETS_SWOT` and requiring `strategic_assessment` ≤ 400 caractères) and `_porter_prompt` (each `rationale` ≤ `MAX_RATIONALE_CHARS` caractères, `competitive_position_summary` ≤ 400 caractères).

Add the import at the top of `strategic_research.py`:

```python
from finwiz.schemas.hybrid_analysis.strategic import (
    MAX_BULLET_CHARS,
    MAX_BULLETS_PESTEL,
    MAX_BULLETS_SWOT,
    MAX_RATIONALE_CHARS,
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/analysis/test_strategic_prompts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/analysis/strategic_research.py tests/unit/analysis/test_strategic_prompts.py
git commit -m "feat(strategic): ask the model for bullets within the schema caps"
```

---

### Task 5: Digest the synthesis payload; never truncate the holding list

**Why:** `_serialize_holdings` ends in `[:30000]`. Against a 626,286-char payload that kept 4.8%, and only `AAPL`'s key survived — which is why a 64-holding portfolio's posture discussed two companies whose data never reached the model.

**Files:**

- Modify: `src/finwiz/analysis/strategic_research.py:241-248`
- Test: `tests/unit/analysis/test_strategic_digest.py` (create)

**Interfaces:**

- Consumes: Task 3's caps.
- Produces: `SYNTHESIS_PAYLOAD_BUDGET_CHARS = 240_000` (module-level in `strategic_research.py`); `_serialize_holdings(holdings_strategic) -> str` keeps its signature.

- [ ] **Step 1: Write the failing test**

```python
def test_every_holding_survives_the_digest():
    """Detail may shrink. The holding list may not.

    The 2026-08-16 posture was built from 1 of 26 holdings because the serializer
    ended in [:30000].
    """
    import json

    from finwiz.analysis.strategic_research import _serialize_holdings
    from finwiz.schemas.hybrid_analysis.strategic import PestelAnalysis, StrategicAnalysis

    holdings = {
        f"TICK{i}": StrategicAnalysis(
            pestel=PestelAnalysis(political=["p" * 200] * 3, economic=["e" * 200] * 3, strategic_score=0.6, confidence=0.7)
        )
        for i in range(200)
    }

    payload = _serialize_holdings(holdings)
    parsed = json.loads(payload)

    assert len(parsed) == 200
    for i in range(200):
        assert f"TICK{i}" in parsed


def test_digest_shrinks_detail_under_budget(mocker):
    from finwiz.analysis import strategic_research
    from finwiz.schemas.hybrid_analysis.strategic import PestelAnalysis, StrategicAnalysis

    mocker.patch.object(strategic_research, "SYNTHESIS_PAYLOAD_BUDGET_CHARS", 5_000)
    holdings = {
        f"T{i}": StrategicAnalysis(pestel=PestelAnalysis(political=["p" * 200] * 3, strategic_score=0.6, confidence=0.7))
        for i in range(100)
    }

    payload = strategic_research._serialize_holdings(holdings)

    assert len(json.loads(payload)) == 100
    assert len(payload) <= 5_000 * 1.1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/analysis/test_strategic_digest.py -v`
Expected: FAIL — output is truncated mid-JSON, so `json.loads` raises.

- [ ] **Step 3: Write minimal implementation**

Replace `_serialize_holdings` entirely:

```python
SYNTHESIS_PAYLOAD_BUDGET_CHARS = 240_000
"""Char budget for the portfolio-synthesis payload (~60K tokens).

With the Task 3 caps a 64-holding portfolio lands near 190K, so the degradation
ladder below is a guard-rail rather than the normal path.
"""


def _digest_one(sa: StrategicAnalysis, *, bullets: int, include_prose: bool) -> dict[str, Any]:
    """One holding's contribution at a given detail level."""
    out: dict[str, Any] = {}
    if sa.pestel:
        out["pestel"] = {"score": sa.pestel.strategic_score, "threats": sa.pestel.key_threats[:bullets], "opportunities": sa.pestel.key_opportunities[:bullets]}
    if sa.swot:
        out["swot"] = {"score": sa.swot.strategic_score, "strengths": sa.swot.strengths[:bullets], "threats": sa.swot.threats[:bullets]}
        if include_prose:
            out["swot"]["assessment"] = sa.swot.strategic_assessment
    if sa.five_forces:
        out["moat"] = {"score": sa.five_forces.strategic_score}
        if include_prose:
            out["moat"]["summary"] = sa.five_forces.competitive_position_summary
    return out


def _serialize_holdings(holdings_strategic: dict[str, StrategicAnalysis]) -> str:
    """Compact JSON digest of every holding, fitted to the budget.

    Detail degrades before the holding list does. Dropping a holding is not an
    operation this function can perform: the 2026-08-16 posture was synthesized
    from 1 of 26 holdings because the old implementation ended in ``[:30000]``.
    """
    import json

    for bullets, include_prose in ((3, True), (2, True), (1, True), (1, False)):
        compact = {ticker: _digest_one(sa, bullets=bullets, include_prose=include_prose) for ticker, sa in holdings_strategic.items()}
        payload = json.dumps(compact, ensure_ascii=False, default=str)
        if len(payload) <= SYNTHESIS_PAYLOAD_BUDGET_CHARS:
            return payload

    # Floor: scores only. Still every holding.
    scores = {
        ticker: {
            "pestel": sa.pestel.strategic_score if sa.pestel else None,
            "swot": sa.swot.strategic_score if sa.swot else None,
            "moat": sa.five_forces.strategic_score if sa.five_forces else None,
        }
        for ticker, sa in holdings_strategic.items()
    }
    return json.dumps(scores, ensure_ascii=False, default=str)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/analysis/test_strategic_digest.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/analysis/strategic_research.py tests/unit/analysis/test_strategic_digest.py
git commit -m "fix(strategic): digest every holding into the synthesis instead of truncating to one"
```

---

### Task 6: Coverage becomes part of the posture, and scores become required

**Why:** `PortfolioStrategicPosture` has no coverage field, so no renderer could have told the truth about 26-of-64. And `strategic_score` / `confidence` default to `0.5`, so a posture built from nothing reports 50% favourability at 50% confidence — the `EnrichedAnalysis` `C`/`0.5`/`HOLD` defect (`c2a17d1a`) in a second place.

**Files:**

- Modify: `src/finwiz/schemas/hybrid_analysis/strategic.py:158-180`
- Test: `tests/unit/schemas/test_posture_coverage.py` (create)

**Interfaces:**

- Consumes: nothing.
- Produces: `PortfolioStrategicPosture` gains required `holdings_covered: int`, `holdings_total: int`, `value_covered_pct: float`, `macro_verdict: str`, `competitive_verdict: str`, `swot_verdict: str`; optional `uncovered_tickers: list[str]`; `strategic_score` and `confidence` become required.

- [ ] **Step 1: Write the failing test**

```python
def test_posture_cannot_be_built_without_stating_its_coverage():
    """A portfolio-level number must carry what it covers, inseparably."""
    import pytest
    from pydantic import ValidationError

    from finwiz.schemas.hybrid_analysis.strategic import PortfolioStrategicPosture

    with pytest.raises(ValidationError):
        PortfolioStrategicPosture(strategic_score=0.71, confidence=0.83)


def test_posture_score_has_no_plausible_default():
    """No score must mean no score — never a confident midpoint."""
    import pytest
    from pydantic import ValidationError

    from finwiz.schemas.hybrid_analysis.strategic import PortfolioStrategicPosture

    with pytest.raises(ValidationError):
        PortfolioStrategicPosture(
            holdings_covered=64, holdings_total=64, value_covered_pct=100.0,
            macro_verdict="m", competitive_verdict="c", swot_verdict="s",
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/schemas/test_posture_coverage.py -v`
Expected: FAIL — both construct successfully today, taking `0.5` defaults.

- [ ] **Step 3: Write minimal implementation**

In `PortfolioStrategicPosture`, add the coverage block and the verdicts, and make the scores required:

```python
    # Coverage — required, so a posture cannot omit what it covers. The
    # 2026-08-16 report printed "71%" from 1 of 64 holdings because this
    # schema had no way to say otherwise.
    holdings_covered: int = Field(..., ge=0, description="Holdings with a real strategic analysis")
    holdings_total: int = Field(..., ge=0, description="Holdings in the portfolio")
    value_covered_pct: float = Field(..., ge=0.0, le=100.0, description="Share of portfolio value covered")
    uncovered_tickers: list[str] = Field(default_factory=list, description="Named, never silently omitted")

    # One-sentence verdicts, requested from the model rather than extracted from
    # prose by Python — first-sentence extraction is how a markdown bullet list
    # ends up as a headline.
    macro_verdict: str = Field(..., max_length=200, description="One sentence on the macro environment")
    competitive_verdict: str = Field(..., max_length=200, description="One sentence on the competitive landscape")
    swot_verdict: str = Field(..., max_length=200, description="One sentence on the aggregated SWOT")

    strategic_score: float = Field(..., ge=0.0, le=1.0, description="Overall portfolio strategic favorability")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this synthesis")
```

Extend `_portfolio_prompt` in `strategic_research.py` to request the three verdicts:

```python
        "- macro_verdict / competitive_verdict / swot_verdict : UNE phrase chacun, "
        "200 caractères maximum, compréhensible par un lecteur non financier.\n"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/schemas/ -v && uv run pytest tests/ -q -k posture`
Expected: PASS. Update every in-tree construction site to pass the new required fields.

- [ ] **Step 5: Audit for `model_construct` leaks**

Run: `rg "PortfolioStrategicPosture.model_construct" src tests`
Expected: no matches. `model_construct` bypasses validation, which is exactly how the `EnrichedAnalysis` defaults reached disk.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/schemas/hybrid_analysis/strategic.py src/finwiz/analysis/strategic_research.py tests/unit/schemas/test_posture_coverage.py
git commit -m "feat(schemas): make posture coverage and scores required, add one-sentence verdicts"
```

---

### Task 7: Populate coverage and trip on a gap

**Why:** Task 6 makes coverage expressible. This makes it true, and makes a gap impossible to ship silently — the report cheerfully printed 71% off one holding and nothing objected.

**Files:**

- Modify: `src/finwiz/orchestrators/reporting/enrichment.py:323-358`
- Test: `tests/unit/orchestrators/test_posture_coverage_wiring.py` (create)

**Interfaces:**

- Consumes: Task 6's required fields.
- Produces: `_synthesize_portfolio_strategic(deep_analysis_results, records=None, *, all_tickers: list[str])` — new keyword-only argument.

- [ ] **Step 1: Write the failing test**

```python
def test_uncovered_holdings_are_named_in_the_posture(mocker):
    """A gap must be named, not averaged away."""
    from finwiz.orchestrators.reporting.enrichment import ReportEnrichmentMixin

    mixin = ReportEnrichmentMixin()
    mocker.patch.object(mixin, "_extract_holdings_strategic", return_value={"AAPL": _valid_strategic()})
    mocker.patch("finwiz.analysis.strategic_research.synthesize_portfolio_posture_sync", return_value=_valid_posture())

    result = mixin._synthesize_portfolio_strategic({}, all_tickers=["AAPL", "MSFT", "TSLA"])

    assert result["holdings_covered"] == 1
    assert result["holdings_total"] == 3
    assert sorted(result["uncovered_tickers"]) == ["MSFT", "TSLA"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/orchestrators/test_posture_coverage_wiring.py -v`
Expected: FAIL — `_synthesize_portfolio_strategic` takes no `all_tickers`.

- [ ] **Step 3: Write minimal implementation**

In `_synthesize_portfolio_strategic`, after `posture = synthesize_portfolio_posture_sync(holdings_models)`:

```python
            covered = sorted(holdings_models)
            uncovered = sorted(set(all_tickers) - set(covered))
            posture = posture.model_copy(update={
                "holdings_covered": len(covered),
                "holdings_total": len(all_tickers),
                "uncovered_tickers": uncovered,
            })

            if uncovered:
                self.logger.error(
                    "Strategic coverage incomplete: %d/%d holdings. Missing: %s",
                    len(covered), len(all_tickers), ", ".join(uncovered),
                )
```

Update the call site at `enrichment.py:79` to pass `all_tickers=[h.ticker for h in portfolio_review.holdings if h.ticker]`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/orchestrators/ -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/orchestrators/reporting/enrichment.py tests/unit/orchestrators/test_posture_coverage_wiring.py
git commit -m "feat(reporting): populate posture coverage and name every uncovered holding"
```

---

### Task 8: Strategic analysis for every asset class

**Why:** `stages/__init__.py:100` reads `do_strategic = ctx.asset_class == "stock"`. ETFs and crypto — 38 of 64 holdings — are structurally excluded, so full coverage is impossible without this.

**Files:**

- Modify: `src/finwiz/analysis/stages/__init__.py:100`, `src/finwiz/analysis/strategic_research.py`
- Test: `tests/unit/analysis/test_strategic_asset_classes.py` (create)

**Interfaces:**

- Consumes: Task 4's prompt builders.
- Produces: `gather_strategic_analysis(..., asset_class: str = "stock")`; prompt builders gain an `asset_class` parameter and dispatch internally.

- [ ] **Step 1: Write the failing test**

```python
def test_etf_prompt_asks_about_cost_and_concentration_not_moats():
    from finwiz.analysis.strategic_research import _pestel_prompt

    etf = _pestel_prompt("VUSA.L", "", "", "", "16 août 2026", asset_class="etf")

    assert "concentration" in etf.lower()
    assert "frais" in etf.lower()


def test_crypto_prompt_asks_about_protocol_and_regulation():
    from finwiz.analysis.strategic_research import _pestel_prompt

    crypto = _pestel_prompt("BTC-USD", "", "", "", "16 août 2026", asset_class="crypto")

    assert "protocole" in crypto.lower()
    assert "réglementaire" in crypto.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/analysis/test_strategic_asset_classes.py -v`
Expected: FAIL — `_pestel_prompt` takes no `asset_class`.

- [ ] **Step 3: Write minimal implementation**

Add `asset_class: str = "stock"` to each prompt builder and branch on it. For `_pestel_prompt`:

```python
    if asset_class == "etf":
        focus = (
            "Pour un ETF, traite : régime réglementaire et fiscal, concentration "
            "sectorielle et géographique, frais et qualité de réplication, liquidité."
        )
    elif asset_class == "crypto":
        focus = (
            "Pour un actif crypto, traite : économie du protocole et émission, "
            "posture réglementaire par juridiction, effets de réseau et activité "
            "des développeurs, risque de conservation et de contrepartie."
        )
    else:
        focus = "Couvre les six dimensions PESTEL classiques pour l'entreprise."
```

and interpolate `focus` into the returned prompt. Apply the same pattern to `_swot_prompt` and `_porter_prompt` (for ETFs, Porter's forces map to provider competition and fee pressure).

Then at `stages/__init__.py:100`:

```python
    # Every asset class gets strategic analysis. The old stock-only gate excluded
    # 38 of 64 holdings, which made full coverage structurally impossible.
    strategic = _safe_strategic(ctx.ticker, sector, industry, description, asset_class=ctx.asset_class)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/analysis/ -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/analysis/strategic_research.py src/finwiz/analysis/stages/__init__.py tests/unit/analysis/test_strategic_asset_classes.py
git commit -m "feat(strategic): analyse ETFs and crypto with framings that fit them"
```

---

### Task 9: The markdown render boundary

**Why:** The report carries 42 literal `**` markers and 470 `[n]` citation markers pointing at nothing. `_portfolio_prompt` never specified an output format, so the model emits markdown into HTML. The `citations` URL list is already returned by `perplexity_structured` and discarded.

**Files:**

- Create: `src/finwiz/reporting/markdown_fragment.py`
- Test: `tests/unit/reporting/test_markdown_fragment.py`

**Interfaces:**

- Consumes: nothing.
- Produces: `render_markdown_fragment(text: str, *, citations: list[str] | None = None) -> str`.

- [ ] **Step 1: Write the failing test**

```python
def test_html_in_model_output_is_escaped_not_executed():
    """Perplexity quotes live web pages into its output. Treat it as text."""
    from finwiz.reporting.markdown_fragment import render_markdown_fragment

    out = render_markdown_fragment("<script>alert(1)</script> et **gras**")

    assert "<script>" not in out
    assert "&lt;script&gt;" in out
    assert "<strong>gras</strong>" in out


def test_bullets_and_bold_become_html():
    from finwiz.reporting.markdown_fragment import render_markdown_fragment

    out = render_markdown_fragment("- **Politique** : durcissement\n- Économique : porteur")

    assert out.count("<li>") == 2
    assert "<strong>Politique</strong>" in out


def test_citation_marker_without_a_source_is_removed():
    """A number that looks like sourcing must not point at nothing."""
    from finwiz.reporting.markdown_fragment import render_markdown_fragment

    out = render_markdown_fragment("Un fait[7].", citations=["https://a.example"])

    assert "[7]" not in out
    assert "7" not in out


def test_citation_marker_with_a_source_becomes_a_link():
    from finwiz.reporting.markdown_fragment import render_markdown_fragment

    out = render_markdown_fragment("Un fait[1].", citations=["https://a.example"])

    assert 'href="https://a.example"' in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/reporting/test_markdown_fragment.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

```python
"""Convert model-authored markdown into safe HTML.

Escape first, then allow a fixed subset. The model is never a source of markup:
Perplexity quotes live web pages into its output, so anything that looks like a
tag is escaped and rendered as visible text.
"""

from __future__ import annotations

import re
from html import escape

_BOLD = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", re.DOTALL)
_CITATION = re.compile(r"\[(\d{1,3})\]")


def render_markdown_fragment(text: str, *, citations: list[str] | None = None) -> str:
    """Render a markdown fragment to HTML using a strict allowlist."""
    if not text:
        return ""

    safe = escape(text)

    def _cite(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        sources = citations or []
        if 1 <= idx <= len(sources):
            return f'<sup><a href="{escape(sources[idx - 1])}" rel="noopener noreferrer" target="_blank">{idx}</a></sup>'
        return ""  # Dangling marker: remove rather than show a reference to nothing.

    safe = _CITATION.sub(_cite, safe)
    safe = _BOLD.sub(r"<strong>\1</strong>", safe)
    safe = _ITALIC.sub(r"<em>\1</em>", safe)

    blocks: list[str] = []
    bullets: list[str] = []
    for raw_line in safe.split("\n"):
        line = raw_line.strip()
        if line.startswith("- "):
            bullets.append(f"<li>{line[2:].strip()}</li>")
            continue
        if bullets:
            blocks.append("<ul>" + "".join(bullets) + "</ul>")
            bullets = []
        if line:
            blocks.append(f"<p>{line}</p>")
    if bullets:
        blocks.append("<ul>" + "".join(bullets) + "</ul>")

    return "".join(blocks)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/reporting/test_markdown_fragment.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/reporting/markdown_fragment.py tests/unit/reporting/test_markdown_fragment.py
git commit -m "feat(reporting): add an escape-first markdown render boundary with real citations"
```

---

### Task 10: The dedicated posture page

**Why:** The posture is unreadable inside the family artifact — a wall of analyst prose where the family needs a verdict.

**Files:**

- Create: `src/finwiz/reporting/sections/posture_page.py`
- Test: `tests/unit/reporting/test_posture_page.py`

**Interfaces:**

- Consumes: `render_markdown_fragment` (Task 9); the coverage and verdict fields (Task 6).
- Produces: `generate_posture_page(posture: dict, *, holdings_strategic: dict[str, dict] | None = None, citations: list[str] | None = None) -> str` returning a complete HTML document.

- [ ] **Step 1: Write the failing test**

```python
def test_coverage_leads_the_page():
    """Coverage is the first thing a reader sees, not a footnote."""
    from finwiz.reporting.sections.posture_page import generate_posture_page

    html = generate_posture_page({
        "holdings_covered": 26, "holdings_total": 64, "value_covered_pct": 38.2,
        "uncovered_tickers": ["TSLA"], "macro_verdict": "Environnement porteur.",
        "competitive_verdict": "Moats solides.", "swot_verdict": "Équilibré.",
        "strategic_score": 0.71, "confidence": 0.83,
        "macro_environment_summary": "- **Politique** : durcissement",
    })

    assert "26 / 64" in html
    assert html.index("26 / 64") < html.index("Environnement porteur.")


def test_detail_is_behind_a_disclosure():
    from finwiz.reporting.sections.posture_page import generate_posture_page

    html = generate_posture_page(_full_posture())

    assert "<details>" in html
    assert "<strong>Politique</strong>" in html  # markdown rendered, not literal
    assert "**" not in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/reporting/test_posture_page.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

```python
"""The dedicated strategic posture page.

Separate from the family artifact because the posture is analyst-length and the
family artifact is a decision sheet. Coverage leads the page: a portfolio score
is meaningless without the fraction of the portfolio it speaks for.
"""

from __future__ import annotations

from html import escape
from typing import Any

from finwiz.reporting.css_styles import get_report_css
from finwiz.reporting.markdown_fragment import render_markdown_fragment

_THEMES = (
    ("🌍 Environnement Macro", "macro_verdict", "macro_environment_summary"),
    ("⚔️ Paysage Concurrentiel", "competitive_verdict", "competitive_landscape_summary"),
    ("📐 SWOT Agrégé", "swot_verdict", "overall_assessment"),
)


def _coverage_banner(posture: dict[str, Any]) -> str:
    covered = posture["holdings_covered"]
    total = posture["holdings_total"]
    pct = posture["value_covered_pct"]
    uncovered = posture.get("uncovered_tickers") or []
    warn = "" if covered == total else ' class="warning"'
    missing = f"<p>Non couverts : {escape(', '.join(uncovered))}</p>" if uncovered else ""
    return f'<div id="couverture"{warn}><h2>Couverture</h2><p><strong>{covered} / {total}</strong> holdings · {pct:.1f} % de la valeur</p>{missing}</div>'


def _theme_block(title: str, verdict: str, detail_md: str, citations: list[str] | None) -> str:
    detail = render_markdown_fragment(detail_md, citations=citations)
    body = f"<details><summary>Détail</summary>{detail}</details>" if detail else ""
    return f'<section><h2>{escape(title)}</h2><p class="verdict">{escape(verdict)}</p>{body}</section>'


def _sources(citations: list[str] | None) -> str:
    if not citations:
        return ""
    items = "".join(f'<li id="src{i}"><a href="{escape(u)}" rel="noopener noreferrer" target="_blank">{escape(u)}</a></li>' for i, u in enumerate(citations, 1))
    return f"<section><h2>Sources</h2><ol>{items}</ol></section>"


def generate_posture_page(
    posture: dict[str, Any],
    *,
    holdings_strategic: dict[str, dict] | None = None,
    citations: list[str] | None = None,
) -> str:
    """Render the standalone posture page as a complete HTML document."""
    score_pct = posture["strategic_score"] * 100
    conf_pct = posture["confidence"] * 100
    themes = "".join(_theme_block(t, posture.get(v, ""), posture.get(d, ""), citations) for t, v, d in _THEMES)

    cards = ""
    if holdings_strategic:
        rows = "".join(f"<li><strong>{escape(tk)}</strong></li>" for tk in sorted(holdings_strategic))
        cards = f"<section><h2>Par ligne</h2><ul>{rows}</ul></section>"

    return (
        "<!DOCTYPE html><html lang=\"fr\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>Posture Stratégique — FinWiz</title>"
        f"<style>{get_report_css()}</style></head><body>"
        "<h1>Posture Stratégique du Portefeuille</h1>"
        f"{_coverage_banner(posture)}"
        f"<p>Score stratégique : <strong>{score_pct:.0f} %</strong> · Confiance : {conf_pct:.0f} %</p>"
        f"{themes}{cards}{_sources(citations)}"
        "</body></html>"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/reporting/test_posture_page.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/reporting/sections/posture_page.py tests/unit/reporting/test_posture_page.py
git commit -m "feat(reporting): add the dedicated strategic posture page"
```

---

### Task 11: Shrink the family artifact and link out

**Why:** The family artifact should carry a verdict and a link, not the analysis.

**Files:**

- Modify: `src/finwiz/reporting/python_report_generator.py:435-439`, `src/finwiz/reporting/sections/insights.py`
- Test: `tests/unit/reporting/test_posture_page.py`

**Interfaces:**

- Consumes: Tasks 6, 9, 10.
- Produces: `generate_posture_page` is written to `output/finwiz_posture_strategique.html` beside the family report.

- [ ] **Step 1: Write the failing test**

```python
def test_family_artifact_summarises_and_links_out():
    """Three lines and a link — the analysis lives on its own page."""
    from finwiz.reporting.section_generators import generate_strategic_posture_section

    html = generate_strategic_posture_section(_full_posture())

    assert "Environnement porteur." in html
    assert "finwiz_posture_strategique.html" in html
    assert "PESTEL" not in html
    assert len(html) < 2000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/reporting/test_posture_page.py::test_family_artifact_summarises_and_links_out -v`
Expected: FAIL — the current section embeds the full prose.

- [ ] **Step 3: Write minimal implementation**

Rewrite `generate_strategic_posture_section` in `src/finwiz/reporting/sections/insights.py`:

```python
def generate_strategic_posture_section(portfolio_strategic_posture: dict | None) -> str:
    """Three lines and a link. The analysis itself lives on its own page.

    This section used to embed the full PESTEL/SWOT/Porter prose, which rendered
    as a wall of raw markdown in a document meant for a family.
    """
    if not portfolio_strategic_posture:
        return ""

    p = portfolio_strategic_posture
    covered = p.get("holdings_covered")
    total = p.get("holdings_total")
    coverage = f" (sur {covered}/{total} lignes)" if covered is not None and total else ""

    return f"""
  <div class="section">
    <h2>🎯 Posture Stratégique du Portefeuille</h2>
    <p><strong>{p["strategic_score"] * 100:.0f} %</strong>{coverage} · Confiance : {p["confidence"] * 100:.0f} %</p>
    <ul>
      <li>{escape(p.get("macro_verdict", ""))}</li>
      <li>{escape(p.get("competitive_verdict", ""))}</li>
      <li>{escape(p.get("swot_verdict", ""))}</li>
    </ul>
    <p><a href="finwiz_posture_strategique.html">Analyse stratégique complète →</a></p>
  </div>
"""
```

Then write the page beside the family report. In `ReportEnrichmentMixin.report()` (`enrichment.py`), after `generate_python_report(...)` returns:

```python
        if portfolio_strategic_posture:
            from finwiz.reporting.sections.posture_page import generate_posture_page

            posture_path = Path(report_path).parent / "finwiz_posture_strategique.html"
            posture_path.write_text(
                generate_posture_page(portfolio_strategic_posture, holdings_strategic=self._extract_holdings_strategic(deep_analysis_results, records=enriched_records)),
                encoding="utf-8",
            )
            self.logger.info("Posture page written: %s", posture_path)
```

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q -n auto --dist=loadscope`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/reporting/ tests/unit/reporting/
git commit -m "feat(reporting): reduce the family artifact's posture to a verdict and a link"
```

---

## Verification

After Task 11, run a real `crewai flow kickoff` from a clean `uv sync` in the main checkout and confirm from `output/run_ledger/*.jsonl`:

- `qualify` failures are zero or near-zero, with **no `CircuitBreakerOpenError`**
- `holdings_covered == holdings_total` in the posture, or the run logged the gap with named tickers
- `grep -c '\*\*' output/finwiz_posture_strategique.html` returns `0`
- every `[n]` in the page resolves to an entry in the sources list
