# Design: cache-friendly deep-analysis prompt

**Date:** 2026-09-20
**Status:** approved
**Path:** bounded (template reorder, one test)

## Problem

Every LLM slot runs `openrouter/google/gemini-3.8-flash`. OpenRouter applies
Gemini's implicit prompt caching automatically: no cache-write cost, cache reads
billed at $0.075 per million input tokens instead of $0.75, once two requests share
a prefix longer than the model's threshold (1 024 tokens for the Flash family).

The deep-analysis crew makes 67 near-identical requests per run and gets no cache
hits, because the shared text is not a prefix:

- `crews/deep_analysis/config/agents.yaml` puts `{ticker}` in the agent `goal`, and
  CrewAI renders the goal into the system prompt (`You are {role}. {backstory}\nYour
  personal goal is: {goal}`), so the system prompt differs per holding.
- `crews/deep_analysis/config/tasks.yaml` opens the task description with
  `Qualitative analysis for {ticker}`, the date, and the fact pack. All the static
  rules come after the per-holding data.

The cacheable prefix today is about 20 tokens.

## Expected gain, stated honestly

Static instruction text is roughly 3 500 characters of French, about 1 200 tokens,
just above the threshold. Ceiling: 67 calls × ~1.5k cached tokens × $0.675 per
million ≈ **$0.07 per run** out of $0.89 measured for the crew. Holdings run in
parallel (`max_workers` semaphore in `orchestrators/deep_analysis_orchestrator.py`),
so the first wave misses. This is a hygiene change, not a cost project; the
CHANGELOG entry says "cents per run".

## Design

### `tasks.yaml` — description reordered

Static block first, in this order:

1. Title line without placeholders: "Analyse qualitative d'un holding."
2. LANGUE rule.
3. ANTI-HALLUCINATION rules. Inline `{current_date}` mentions become "la DATE
   D'ANALYSE indiquée en fin de prompt".
4. AUCUN OUTIL EXTERNE notice.
5. PROVIDE QUALITATIVE ANALYSIS ONLY (the five sections).
6. CHAMPS PYTHON-CONTRÔLÉS.
7. REQUIRED `investment_synthesis` structure, OUTPUT rules, "NO trailing commas".

Dynamic block last, separated by a `---` line:

1. `📅 DATE D'ANALYSE : {current_date} ({current_date_iso}).` plus the sentence
   about training-data staleness.
2. `HOLDING : {ticker} ({asset_class})`.
3. `{fact_pack_block}` with its AUTORITAIRE framing.
4. CONTEXT (Python-calculated) lines.
5. `{retry_guidance}`.

No placeholder is added or removed, so `analysis/_helpers._build_crew_inputs` is
untouched.

### `agents.yaml` — goal without ticker

`goal: Provide qualitative insights in French for the holding described in the
task. Output JSON only.` Role and backstory unchanged.

### Test

`tests/unit/crews/test_deep_analysis_prompt_layout.py`:

- Load both YAML files. Assert the agent goal contains no `{`.
- Assert the index of the first `{` in the task description is ≥ 3 000 characters,
  and that every placeholder name in the description is in the set
  `_build_crew_inputs` produces (guards against a rename breaking interpolation).

## Files

- `src/finwiz/crews/deep_analysis/config/tasks.yaml`
- `src/finwiz/crews/deep_analysis/config/agents.yaml`
- `tests/unit/crews/test_deep_analysis_prompt_layout.py` (new)
- `CHANGELOG.md` Unreleased. `src/finwiz/crews/CLAUDE.md` does not describe the
  prompt layout; add one paragraph there stating the static-prefix rule so the
  next prompt edit keeps it.

## Verification

1. `make test`, `make lint`.
2. Three-CSV `$0.04` pipeline run (`PORTFOLIO_*_CSV`), confirm the qualitative
   section still validates for all three holdings and the crew cost in
   `output/run_summary.json` is not higher than before.
3. Optional: one OpenRouter generation inspected in the dashboard shows
   `cached_tokens > 0` on the second holding of the same run.

## Out of scope

Reading `usage.cost` / `cached_tokens` back from OpenRouter for the cost summary.
CrewAI's OpenAI-compatible provider discards `prompt_tokens_details`; the research
swap spec records exact cost for its own calls, the crew stays on the litellm
price estimate.
