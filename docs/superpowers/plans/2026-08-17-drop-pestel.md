# Drop PESTEL and Shrink the Synthesis Payload — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove PESTEL from the FinWiz pipeline and replace the portfolio synthesis payload with fixed-size aggregates plus the ten extreme holdings.

**Architecture:** PESTEL is removed consumer-first so the suite stays green at every commit: reporting stops rendering it, then the posture schema and prompt drop the macro fields, then the serializer is replaced, then research stops calling it, and only then does the schema delete the type. The synthesis payload stops being a per-holding digest and becomes portfolio aggregates (count, means, score distribution) plus the 5 weakest and 5 strongest holdings with one bullet each — a payload that does not grow with portfolio size.

**Tech Stack:** Python 3.13, Pydantic v2, CrewAI, pytest + pytest-mock + pytest-socket + pytest-xdist, ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-08-17-drop-pestel-design.md`

## Global Constraints

- **`unittest.mock` is BANNED.** Use pytest-mock (`mocker.patch`, `mocker.AsyncMock`) only. Enforced by ruff and a pre-commit hook.
- **No network in unit tests.** pytest-socket blocks it; mock the seam, never widen the allow-list.
- **`json.dumps` always takes `default=str`.**
- **Line length 180** (ruff).
- **Never trade data for time.** Losing a holding is worse than a slow run.
- **Run `make test`** before every commit. Do **not** run `make lint` or `make check` — a known environment defect makes them reformat ~66 unrelated markdown files. Instead run `uv run ruff check` and `uv run ruff format --check` on touched files, plus `uv run mypy` on them.
- **Baseline suite: 5114 passed, 31 skipped.** Task counts may rise; failures may not.
- **PESTEL removal is decided.** Do not relitigate it in code comments, commit messages, or review. Record mechanics, not justification.
- **Coverage semantics must not change.** `holdings_covered`, `value_covered_pct` and `uncovered_tickers` are Python-computed and merged after the model responds. An all-`None` `StrategicAnalysis` must still yield `composite_strategic_score is None` and be excluded from coverage; a partial analysis must still count as covered.

---

### Task 1: Reporting stops rendering PESTEL and the macro block

**Why:** Consumers go first so no commit leaves the suite red.

**Files:**

- Modify: `src/finwiz/reporting/sections/posture_page.py:26-31` (`_THEMES`), `:41-46` (`_FRAMEWORK_COLUMNS`), `:151-153` (legend)
- Modify: `src/finwiz/reporting/sections/portfolio_summary.py:138`
- Test: `tests/unit/reporting/test_posture_page.py`

**Interfaces:**

- Consumes: nothing new.
- Produces: `generate_posture_page` renders two theme sections (competitive, SWOT) and a per-holding table with two score columns. `generate_strategic_posture_section` renders two verdict bullets.

- [ ] **Step 1: Write the failing tests**

```python
def test_the_macro_block_is_gone_from_the_posture_page():
    """PESTEL moved out of FinWiz; the macro section has no producer."""
    from finwiz.reporting.sections.posture_page import generate_posture_page

    html = generate_posture_page(_full_posture())

    assert "Environnement Macro" not in html
    assert "PESTEL" not in html


def test_the_per_holding_table_has_two_score_columns():
    from finwiz.reporting.sections.posture_page import generate_posture_page

    html = generate_posture_page(
        _full_posture(),
        holdings_strategic={"AAPL": {"swot": {"strategic_score": 0.7}, "five_forces": {"strategic_score": 0.6}}},
    )

    assert "<th>SWOT</th>" in html
    assert "<th>Porter</th>" in html
    assert "<th>PESTEL</th>" not in html


def test_the_family_section_carries_two_verdicts():
    from finwiz.reporting.section_generators import generate_strategic_posture_section

    html = generate_strategic_posture_section(_full_posture())

    assert "Moats solides." in html
    assert "Équilibré." in html
    assert "macro" not in html.lower()
```

`_full_posture()` already exists in this test file. Remove `macro_verdict` and `macro_environment_summary` from the dict it returns as part of this step.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/reporting/test_posture_page.py -v -p no:randomly`
Expected: FAIL — the macro theme and PESTEL column are still rendered.

- [ ] **Step 3: Write the implementation**

In `posture_page.py`, delete the macro row from `_THEMES`:

```python
_THEMES = (
    ("⚔️ Paysage Concurrentiel", "competitive_verdict", "competitive_landscape_summary"),
    ("📐 SWOT Agrégé", "swot_verdict", "overall_assessment"),
)
```

Delete the PESTEL row from `_FRAMEWORK_COLUMNS`:

```python
_FRAMEWORK_COLUMNS = (
    ("SWOT", "swot"),
    ("Porter", "five_forces"),
)
```

Replace the legend so it describes only what the table shows:

```python
legend = '<p class="muted small">SWOT évalue les forces et faiblesses internes, et Porter la solidité de l\'avantage concurrentiel.</p>'
```

In `portfolio_summary.py`, delete the macro bullet at line 138 (`<li>{render_markdown_inline(posture.get("macro_verdict"))}</li>`), leaving the competitive and SWOT bullets.

- [ ] **Step 4: Run the full suite**

Run: `make test`
Expected: PASS. Other reporting tests may assert three columns or a macro bullet — update them; they pin the old shape, not a behaviour worth keeping.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/reporting/sections/ tests/unit/reporting/
git commit -m "feat(reporting): drop the macro block and the PESTEL column"
```

---

### Task 2: The posture schema and synthesis prompt drop the macro fields

**Files:**

- Modify: `src/finwiz/schemas/hybrid_analysis/strategic.py:274` (field), `:289` (verdict field), `:296-299` (prose validator list), `:301` (verdict validator list)
- Modify: `src/finwiz/analysis/strategic_research.py:208-224` (`_portfolio_prompt`)
- Test: `tests/unit/schemas/test_strategic_caps.py`

**Interfaces:**

- Consumes: Task 1 — nothing renders these fields any more.
- Produces: `PortfolioPostureNarrative` without `macro_environment_summary` / `macro_verdict`. `competitive_verdict` and `swot_verdict` stay required (`Field(...)`).

- [ ] **Step 1: Write the failing test**

```python
def test_the_posture_schema_has_no_macro_fields():
    """PESTEL is gone, so nothing can fill a macro summary or verdict."""
    from finwiz.schemas.hybrid_analysis.strategic import PortfolioPostureNarrative

    fields = PortfolioPostureNarrative.model_fields

    assert "macro_environment_summary" not in fields
    assert "macro_verdict" not in fields
    assert "competitive_verdict" in fields
    assert "swot_verdict" in fields


def test_a_legacy_posture_carrying_macro_fields_still_validates():
    """Stale artifacts must not fail validation — they are reused on re-analysis failure."""
    from finwiz.schemas.hybrid_analysis.strategic import PortfolioPostureNarrative

    posture = PortfolioPostureNarrative.model_validate(
        {
            "macro_verdict": "Environnement porteur.",
            "macro_environment_summary": "- Politique : durcissement",
            "competitive_verdict": "Moats solides.",
            "swot_verdict": "Équilibré.",
            "strategic_score": 0.71,
            "confidence": 0.83,
        },
    )

    assert not hasattr(posture, "macro_verdict")
    assert posture.competitive_verdict == "Moats solides."
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/schemas/test_strategic_caps.py -v -p no:randomly`
Expected: FAIL — both fields are still declared.

- [ ] **Step 3: Write the implementation**

In `strategic.py`, delete the `macro_environment_summary` and `macro_verdict` field declarations, and remove both names from the two validator decorator lists so they read:

```python
    @field_validator("competitive_landscape_summary", "overall_assessment", mode="before")
```

```python
    @field_validator("competitive_verdict", "swot_verdict", mode="before")
```

Pydantic's default `extra="ignore"` makes the legacy-payload test pass with no further work — do not add `extra="forbid"`.

In `strategic_research.py`, rewrite `_portfolio_prompt` so it neither mentions PESTEL nor asks for the macro fields:

```python
def _portfolio_prompt(per_holding_payload: str, current_date: str) -> str:
    return (
        _date_preamble(current_date) + "Voici la synthèse des analyses stratégiques (SWOT / Five Forces) "
        "du portefeuille au format JSON — agrégats et positions extrêmes :\n\n"
        f"{per_holding_payload}\n\n"
        f"Synthétise une posture stratégique au niveau PORTEFEUILLE à la date du {current_date} :\n"
        "- portfolio_strengths / weaknesses / opportunities / threats : SWOT agrégé.\n"
        f"- competitive_landscape_summary : industries avec moats les plus forts/faibles, "
        f"{MAX_PORTFOLIO_PROSE_CHARS} caractères maximum.\n"
        "- dominant_themes : 3 à 5 thèmes stratégiques récurrents.\n"
        f"- overall_assessment : narratif final, {MAX_PORTFOLIO_PROSE_CHARS} caractères maximum.\n"
        f"- competitive_verdict / swot_verdict : UNE phrase chacun, "
        f"{MAX_VERDICT_CHARS} caractères maximum, compréhensible par un lecteur non financier.\n"
        "Évalue strategic_score (favorabilité stratégique globale du portefeuille) et confidence."
    )
```

- [ ] **Step 4: Run the full suite**

Run: `make test`
Expected: PASS. Fixtures constructing a posture with `macro_verdict` keep working (`extra="ignore"`), but any test *asserting* a macro field must be deleted — it pins a field that no longer exists.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/schemas/hybrid_analysis/strategic.py src/finwiz/analysis/strategic_research.py tests/unit/schemas/
git commit -m "feat(schemas): drop macro_environment_summary and macro_verdict from the posture"
```

---

### Task 3: The synthesis payload becomes aggregates plus extremes

**Why:** 39,001 chars of per-holding digest buys ~2,000 chars of verdict, of which 869 reach the family artifact — and it grows linearly with holdings.

**Files:**

- Modify: `src/finwiz/analysis/strategic_research.py` — delete `_SERIALIZE_RUNGS`, `_digest_all`, `_digest_one`; rewrite `_serialize_holdings`
- Test: `tests/unit/analysis/test_strategic_synthesis_seam.py`

**Interfaces:**

- Consumes: `StrategicAnalysis` with `swot` and `five_forces` (PESTEL may still be present at this point; ignore it).
- Produces: `_serialize_holdings(holdings_strategic: dict[str, StrategicAnalysis]) -> str` returning a JSON string of the shape below. Signature unchanged, so `synthesize_portfolio_posture` needs no edit.

- [ ] **Step 1: Write the failing tests**

```python
def _analysis(score: float, strength: str, threat: str):
    from finwiz.schemas.hybrid_analysis.strategic import FiveForcesAnalysis, StrategicAnalysis, SwotAnalysis

    return StrategicAnalysis(
        swot=SwotAnalysis(strengths=[strength], threats=[threat], strategic_score=score),
        five_forces=FiveForcesAnalysis(strategic_score=score),
    )


def test_the_payload_is_aggregates_and_extremes_not_every_holding():
    import json

    from finwiz.analysis.strategic_research import _serialize_holdings

    holdings = {f"T{i}": _analysis(i / 100, f"force {i}", f"menace {i}") for i in range(60)}

    payload = json.loads(_serialize_holdings(holdings))

    assert payload["n"] == 60
    assert len(payload["weakest"]) == 5
    assert len(payload["strongest"]) == 5
    assert payload["weakest"][0]["t"] == "T0"
    assert payload["strongest"][-1]["t"] == "T59"
    # The 50 mid-pack holdings are represented by the distribution, not by name.
    assert "T30" not in _serialize_holdings(holdings)


def test_the_payload_does_not_grow_with_portfolio_size():
    from finwiz.analysis.strategic_research import _serialize_holdings

    small = {f"T{i}": _analysis(i / 100, "force", "menace") for i in range(20)}
    large = {f"T{i}": _analysis(i / 200, "force", "menace") for i in range(200)}

    assert len(_serialize_holdings(large)) < 2 * len(_serialize_holdings(small))


def test_an_empty_portfolio_serializes_without_raising():
    import json

    from finwiz.analysis.strategic_research import _serialize_holdings

    payload = json.loads(_serialize_holdings({}))

    assert payload["n"] == 0
    assert payload["weakest"] == []
    assert payload["strongest"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/analysis/test_strategic_synthesis_seam.py -v -p no:randomly`
Expected: FAIL — the current payload is a per-holding dict keyed by ticker.

- [ ] **Step 3: Write the implementation**

`json` is **not** imported at module level in `strategic_research.py` — the current `_serialize_holdings` does `import json` inside the function body (line 579). Move it to the module imports alongside `import logging` (line 20), since the new implementation needs it at the top of the function.

Delete `_SERIALIZE_RUNGS`, `_digest_all` and `_digest_one` entirely, and replace `_serialize_holdings` with:

```python
_EXTREMES = 5
"""Holdings named at each end. Fixed, so the payload does not scale with the portfolio."""

_SCORE_BUCKETS = ((0.5, "<0.5"), (0.65, "0.5-0.65"), (0.8, "0.65-0.8"))


def _bucket(score: float) -> str:
    for upper, label in _SCORE_BUCKETS:
        if score < upper:
            return label
    return ">=0.8"


def _serialize_holdings(holdings_strategic: dict[str, StrategicAnalysis]) -> str:
    """Portfolio aggregates plus the extreme holdings, as a JSON string.

    A portfolio posture is a judgement about distribution and outliers, not a
    reading of every line. Sending all 64 digests cost ~39,000 chars to produce
    ~2,000 chars of verdict and grew linearly with the portfolio; this shape is
    ~3,000 chars at any size.

    The mid-pack holdings are represented by ``distribution``, never dropped
    silently: ``n`` always reports the true count, so the model cannot mistake
    the extremes for the whole portfolio.
    """
    rows: list[tuple[float, str, StrategicAnalysis]] = []
    for ticker, sa in sorted(holdings_strategic.items()):
        composite = sa.composite_strategic_score
        if composite is None:
            continue
        rows.append((composite, ticker, sa))
    rows.sort(key=lambda r: (r[0], r[1]))

    swot_scores = [sa.swot.strategic_score for _, _, sa in rows if sa.swot is not None]
    moat_scores = [sa.five_forces.strategic_score for _, _, sa in rows if sa.five_forces is not None]

    distribution: dict[str, int] = {}
    for composite, _, _ in rows:
        label = _bucket(composite)
        distribution[label] = distribution.get(label, 0) + 1

    def _weak(entry: tuple[float, str, StrategicAnalysis]) -> dict[str, Any]:
        composite, ticker, sa = entry
        threats = sa.swot.threats if sa.swot else []
        return {"t": ticker, "c": round(composite, 2), "T": threats[0] if threats else None}

    def _strong(entry: tuple[float, str, StrategicAnalysis]) -> dict[str, Any]:
        composite, ticker, sa = entry
        strengths = sa.swot.strengths if sa.swot else []
        return {"t": ticker, "c": round(composite, 2), "S": strengths[0] if strengths else None}

    payload = {
        "n": len(rows),
        "swot_mean": round(sum(swot_scores) / len(swot_scores), 2) if swot_scores else None,
        "moat_mean": round(sum(moat_scores) / len(moat_scores), 2) if moat_scores else None,
        "distribution": distribution,
        "weakest": [_weak(r) for r in rows[:_EXTREMES]],
        "strongest": [_strong(r) for r in rows[-_EXTREMES:]],
    }

    serialized = json.dumps(payload, ensure_ascii=False, default=str)
    if len(serialized) > SYNTHESIS_PAYLOAD_BUDGET_CHARS:
        logger.warning(
            f"Synthesis payload {len(serialized)} chars exceeds the {SYNTHESIS_PAYLOAD_BUDGET_CHARS} budget "
            f"for {len(rows)} holdings — the payload is meant to be size-independent, so this indicates "
            f"unusually long bullets rather than a large portfolio."
        )
    return serialized
```

Keep `SYNTHESIS_PAYLOAD_BUDGET_CHARS` and update its docstring to say it is a guard that should never trigger, not a trimming target.

Note `n` counts holdings with a real composite score. Holdings whose `composite_strategic_score` is `None` are excluded here exactly as they are excluded from coverage — the two must not disagree.

- [ ] **Step 4: Run the full suite**

Run: `make test`
Expected: PASS. Tests asserting the old per-ticker payload shape are rewritten to the new shape, not deleted — they pin that every holding is accounted for, which is still true via `n` and `distribution`.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/analysis/strategic_research.py tests/unit/analysis/
git commit -m "perf(strategic): send portfolio aggregates and extremes, not 64 digests"
```

---

### Task 4: Strategic research stops running PESTEL

**Files:**

- Modify: `src/finwiz/analysis/strategic_research.py` — `_pestel_prompt`, the PESTEL call in `gather_strategic_analysis`, the `MAX_BULLETS_PESTEL` import
- Test: `tests/unit/analysis/test_strategic_research_retry.py`, `tests/unit/analysis/test_strategic_empty_result.py`

**Interfaces:**

- Consumes: `perplexity_with_retry` (unchanged).
- Produces: `gather_strategic_analysis` issues **two** calls and returns `None` when both fail.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.asyncio
async def test_only_two_frameworks_are_researched(mocker):
    """PESTEL is macro and runs outside FinWiz."""
    from finwiz.analysis import strategic_research

    wrapper = mocker.patch(
        "finwiz.analysis.strategic_research.perplexity_with_retry",
        new=mocker.AsyncMock(return_value=None),
    )

    await strategic_research.gather_strategic_analysis(ticker="ORCL", sector="Tech", industry="Software", description="d")

    assert wrapper.await_count == 2
    schemas = {call.kwargs["schema"].__name__ for call in wrapper.await_args_list}
    assert schemas == {"SwotAnalysis", "FiveForcesAnalysis"}


@pytest.mark.asyncio
async def test_gather_returns_none_when_both_frameworks_fail(mocker):
    from finwiz.analysis import strategic_research

    mocker.patch(
        "finwiz.analysis.strategic_research.perplexity_with_retry",
        new=mocker.AsyncMock(return_value=None),
    )

    assert await strategic_research.gather_strategic_analysis(ticker="ORCL", sector="", industry="", description="") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/analysis/test_strategic_research_retry.py -v -p no:randomly`
Expected: FAIL — `await_count == 3` and the schema set includes `PestelAnalysis`.

- [ ] **Step 3: Write the implementation**

Delete `_pestel_prompt` and the `_pestel_dimensions_instruction` helper it uses (line ~100), delete the `pestel_coro` block, and change the gather to two coroutines:

```python
    swot, porter = await asyncio.gather(swot_coro, porter_coro)
    if swot is None and porter is None:
        logger.warning(f"Both strategic analyses failed for {ticker}; returning None (no evidence, not an empty analysis)")
        return None
    return StrategicAnalysis(swot=swot, five_forces=porter)
```

Remove `MAX_BULLETS_PESTEL` from the import block at line 26. Its only users are the three `_pestel_prompt` interpolations you are deleting here (lines 114, 117) and the `PestelAnalysis` validators in `strategic.py` (lines 158, 163), which Task 5 deletes — verified by grep, so nothing else references it. Leave the constant defined in `strategic.py:99` until Task 5 removes it with the class.

- [ ] **Step 4: Run the full suite**

Run: `make test`
Expected: PASS. `test_strategic_empty_result.py` asserts all-`None` behaviour over three frameworks; rewrite it for two. Its partial-coverage case must survive: one framework of two present still yields a real composite and still counts as covered.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/analysis/strategic_research.py tests/unit/analysis/
git commit -m "feat(strategic): research SWOT and Five Forces only"
```

---

### Task 5: Delete the PESTEL type and clean up residual references

**Files:**

- Modify: `src/finwiz/schemas/hybrid_analysis/strategic.py` — delete `PestelAnalysis` (and its `_clamp_dimension` / `_clamp_key_lists` validators), `StrategicAnalysis.pestel`, and `MAX_BULLETS_PESTEL` at line 99, whose last users go with the class
- Modify: `src/finwiz/schemas/hybrid_analysis/qualitative.py:224-225`, `src/finwiz/scoring/thresholds.py:216`, `src/finwiz/validation/ai_output.py`, `src/finwiz/reporting/deep_analysis_report_generator.py`, `src/finwiz/templates/crew_reports/deep_analysis_report.html.j2`
- Test: `tests/unit/schemas/test_strategic_caps.py`

**Interfaces:**

- Consumes: Tasks 1-4 — nothing produces or reads PESTEL any more.
- Produces: `StrategicAnalysis` with two optional framework fields; `composite_strategic_score` averages those two.

- [ ] **Step 1: Write the failing tests**

```python
def test_strategic_analysis_has_two_frameworks():
    from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis

    assert set(StrategicAnalysis.model_fields) == {"swot", "five_forces"}


def test_a_legacy_analysis_carrying_pestel_still_validates():
    """Stale *_enriched.json is reused when re-analysis fails; it must not break."""
    from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis

    analysis = StrategicAnalysis.model_validate(
        {
            "pestel": {"political": ["x"], "strategic_score": 0.9, "confidence": 0.9},
            "swot": {"strengths": ["s"], "strategic_score": 0.6, "confidence": 0.7},
        },
    )

    assert not hasattr(analysis, "pestel")
    assert analysis.composite_strategic_score == 0.6


def test_an_empty_analysis_still_has_no_composite():
    from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis

    assert StrategicAnalysis().composite_strategic_score is None


def test_a_partial_analysis_still_counts():
    from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis, SwotAnalysis

    analysis = StrategicAnalysis(swot=SwotAnalysis(strategic_score=0.62))

    assert analysis.composite_strategic_score == 0.62
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/schemas/test_strategic_caps.py -v -p no:randomly`
Expected: FAIL — `model_fields` still contains `pestel`, and the legacy composite averages 0.75.

- [ ] **Step 3: Write the implementation**

Delete the whole `PestelAnalysis` class and the `pestel` field from `StrategicAnalysis`, then update both composite properties:

```python
@property
def composite_strategic_score(self) -> float | None:
    """Average of the framework scores. None if both are missing."""
    scores = [f.strategic_score for f in (self.swot, self.five_forces) if f is not None]
    return sum(scores) / len(scores) if scores else None


@property
def composite_confidence(self) -> float | None:
    """Average of the framework confidences. None if both are missing."""
    confs = [f.confidence for f in (self.swot, self.five_forces) if f is not None]
    return sum(confs) / len(confs) if confs else None
```

Update the remaining references, all comments or descriptions:

- `qualitative.py:224-225` — comment and `description` become `"Strategic frameworks (SWOT/Porter)"`.
- `thresholds.py:216` — comment becomes `# 15% strategic (AI-rated SWOT/Porter average)`.
- `validation/ai_output.py`, `reporting/deep_analysis_report_generator.py`, `templates/crew_reports/deep_analysis_report.html.j2` — remove PESTEL mentions and any block rendering a `pestel` key.

Run `rtk grep -rn "pestel\|PESTEL" src/finwiz/` and confirm the only remaining hits are in this plan and the spec.

- [ ] **Step 4: Run the full suite**

Run: `make test`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/ tests/
git commit -m "feat(schemas): delete PestelAnalysis and the pestel framework field"
```

---

## Verification

After Task 5, run a real `crewai flow kickoff` from a **clean** `output/` — stale `*_enriched.json` files are reused for holdings that fail re-analysis, and pre-change files carry PESTEL. Then confirm:

- `grep -c PESTEL output/finwiz_posture_strategique.html` returns `0`
- the per-holding table has two score columns
- the posture page has no "Environnement Macro" section
- the synthesis payload logged no budget warning
- `holdings_covered` still equals the number of holdings with a real composite score
- posture verdicts are read against the previous run's before the result is trusted — the spec records that themes will be sharper and less consensual, and this is where that shows up

Baseline for comparison: the 2026-08-16 run at 74% on 64/64 lignes.
