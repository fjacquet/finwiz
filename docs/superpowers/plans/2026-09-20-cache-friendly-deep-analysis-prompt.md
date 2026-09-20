# Cache-Friendly Deep-Analysis Prompt Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorder the deep-analysis crew prompt so every per-holding request shares a long static prefix, letting OpenRouter's implicit Gemini prompt cache serve the 67 near-identical calls per run.

**Architecture:** Two YAML files change and nothing else in `src/`. The agent `goal` loses its `{ticker}` placeholder so the system prompt is identical for every holding. The task `description` is reordered: every static rule first, then a `---` separator, then all per-holding data (date, holding, fact pack, context, retry guidance). A new layout test pins the invariant so a future prompt edit cannot silently break the prefix.

**Tech Stack:** CrewAI 1.15.22 YAML config (`@CrewBase` interpolates `{placeholders}` from the kickoff inputs dict), PyYAML, pytest.

**Spec:** `docs/superpowers/specs/2026-09-20-cache-friendly-deep-analysis-prompt-design.md`

## Global Constraints

- No placeholder is added or removed. The placeholder set stays exactly the keys `analysis/_helpers._build_crew_inputs` produces: `ticker, asset_class, company_name, current_date, current_date_iso, grade, composite_score, preliminary_recommendation, fundamental_score, technical_score, risk_score, fundamental_metrics, technical_indicators, risk_metrics, python_rationale, sector, industry, company_description, fact_pack_block, retry_guidance`.
- Existing prompt tests in `tests/unit/crews/test_deep_analysis_prompt.py` must keep passing: `{fact_pack_block}` present, "FACT PACK" present, "AUTORITAIRE" present, none of "vérifié via Perplexity" / "OUTIL DE VÉRIFICATION" / "Perplexity Sonar Search" / "Maximum 1 appel", and the YAML must parse with key `deep_qualitative_analysis_task`.
- `unittest.mock` is banned; use `pytest-mock` (`mocker`) only. This plan needs no mocks.
- CHANGELOG wording for the gain: "cents per run". No cost claim beyond that.
- Docs ship in the same branch: `CHANGELOG.md` Unreleased and one paragraph in `src/finwiz/crews/CLAUDE.md`.
- Branch: `feat/cache-friendly-deep-analysis-prompt` off `main`. Merge with `gh pr merge --merge` (never squash).
- Commits end with the two attribution lines from the session reminder (`Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB`).
- Shell commands are prefixed with `rtk` (`rtk git ...`, `rtk uv run pytest ...`).

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `src/finwiz/crews/deep_analysis/config/agents.yaml` | Modify line 3 | Static agent goal (no `{ticker}`) |
| `src/finwiz/crews/deep_analysis/config/tasks.yaml` | Rewrite lines 4-107 | Static block first, dynamic block after `---` |
| `tests/unit/crews/test_deep_analysis_prompt_layout.py` | Create | Pins the static-prefix invariant |
| `src/finwiz/crews/CLAUDE.md` | Add one section | Documents the rule for the next editor |
| `CHANGELOG.md` | Add Unreleased entry | Records the change |

---

### Task 1: Layout test (red)

**Files:**
- Create: `tests/unit/crews/test_deep_analysis_prompt_layout.py`

**Interfaces:**
- Consumes: `src/finwiz/crews/deep_analysis/config/agents.yaml` (`asset_analyst.goal`), `src/finwiz/crews/deep_analysis/config/tasks.yaml` (`deep_qualitative_analysis_task.description`), `finwiz.analysis._helpers._build_crew_inputs(ctx, quant, raw_data=None, *, fact_pack=None) -> dict[str, Any]`.
- Produces: three tests that Task 2 and Task 3 turn green.

The third test builds real inputs through `_build_crew_inputs` rather than hardcoding the key list, so a renamed placeholder is caught on either side. The `QuantitativeAnalysis` fixture copies `_make_quant()` from `tests/unit/analysis/test_helpers.py:33-59`, the smallest valid instance the suite already uses.

- [ ] **Step 1: Write the failing tests**

```python
"""The deep-analysis prompt must keep a long static prefix for implicit prompt caching.

OpenRouter applies Gemini's implicit cache when two requests share a prefix
longer than ~1 024 tokens. CrewAI renders the agent goal into the system
prompt and the task description into the user turn, so the cacheable prefix
is exactly: system prompt + the text of the description before its first
placeholder. These tests pin that prefix so a future prompt edit cannot move
per-holding data back to the top.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

import yaml

from finwiz.analysis._helpers import _build_crew_inputs
from finwiz.analysis.deep_analysis_pipeline import AnalysisContext
from finwiz.schemas.hybrid_analysis import QuantitativeAnalysis
from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONFIG = _REPO_ROOT / "src/finwiz/crews/deep_analysis/config"

# Static French instruction text is ~3 500 characters (~1 200 tokens), just
# above the Flash cache threshold. Guard a little below that so a wording
# tweak does not flap the test, but a reorder cannot pass.
_MIN_STATIC_PREFIX_CHARS = 3000

_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


def _agent_goal() -> str:
    agents = yaml.safe_load((_CONFIG / "agents.yaml").read_text(encoding="utf-8"))
    return agents["asset_analyst"]["goal"]


def _task_description() -> str:
    tasks = yaml.safe_load((_CONFIG / "tasks.yaml").read_text(encoding="utf-8"))
    return tasks["deep_qualitative_analysis_task"]["description"]


def test_agent_goal_has_no_placeholder() -> None:
    """The goal lands in the system prompt; one placeholder there breaks the prefix for every holding."""
    assert "{" not in _agent_goal()


def test_task_description_starts_with_a_long_static_block() -> None:
    description = _task_description()
    first = description.find("{")
    assert first != -1, "the description must still interpolate per-holding data"
    assert first >= _MIN_STATIC_PREFIX_CHARS, f"first placeholder at char {first}; static prefix too short for the cache threshold"


def test_every_placeholder_is_a_crew_input_key() -> None:
    """A renamed placeholder would raise at kickoff; catch it here instead."""
    ctx = AnalysisContext(ticker="TEST", asset_class="stock", company_name="Test Co")
    # Same minimal valid shape as tests/unit/analysis/test_helpers.py::_make_quant.
    quant = QuantitativeAnalysis(
        composite_score=0.65,
        fundamental_score=0.70,
        technical_score=0.60,
        risk_score=2.5,
        grade="B",
        preliminary_recommendation="HOLD",
        fundamental_metrics={"roe": 0.15},
        technical_indicators={"rsi": 55.0},
        risk_metrics={"volatility": 0.18},
        calculation_timestamp=datetime.now(UTC),
        data_quality=DataQualityMetrics(completeness_score=0.9, freshness_score=1.0, accuracy_confidence=0.85, source_reliability=0.85, missing_fields=[]),
        confidence_level=0.85,
        python_rationale="fixture",
    )
    inputs = _build_crew_inputs(ctx, quant)

    placeholders = set(_PLACEHOLDER.findall(_task_description()))
    assert placeholders, "no placeholder found; the regex or the template is wrong"
    assert placeholders <= set(inputs), f"placeholders without a crew input: {placeholders - set(inputs)}"
```

- [ ] **Step 2: Run the tests to verify the first two fail**

Run: `rtk uv run pytest tests/unit/crews/test_deep_analysis_prompt_layout.py -v`
Expected: `test_agent_goal_has_no_placeholder` FAILS (goal contains `{ticker}`), `test_task_description_starts_with_a_long_static_block` FAILS (first `{` is at char ~27), `test_every_placeholder_is_a_crew_input_key` PASSES (the placeholder set is unchanged by this plan).

- [ ] **Step 3: Commit the red test**

```bash
rtk git checkout -b feat/cache-friendly-deep-analysis-prompt main
rtk git add tests/unit/crews/test_deep_analysis_prompt_layout.py
rtk git commit -m "test(crews): pin a static prefix on the deep-analysis prompt

Red: the agent goal still carries {ticker} and the task description opens
with per-holding data, so no two requests share a cacheable prefix.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB"
```

---

### Task 2: Agent goal without the ticker

**Files:**
- Modify: `src/finwiz/crews/deep_analysis/config/agents.yaml:3`
- Test: `tests/unit/crews/test_deep_analysis_prompt_layout.py::test_agent_goal_has_no_placeholder`

**Interfaces:**
- Produces: system prompt `You are Financial Analyst (Qualitative). Expert financier qualitative.\nYour personal goal is: Provide qualitative insights in French for the holding described in the task. Output JSON only.` identical for every holding.

- [ ] **Step 1: Edit the goal**

Replace line 3 of `agents.yaml`:

```yaml
  goal: Provide qualitative insights in French for {ticker}. Output JSON only.
```

with:

```yaml
  goal: Provide qualitative insights in French for the holding described in the task. Output JSON only.
```

Role and backstory stay as they are.

- [ ] **Step 2: Run the goal test**

Run: `rtk uv run pytest tests/unit/crews/test_deep_analysis_prompt_layout.py::test_agent_goal_has_no_placeholder -v`
Expected: PASS

- [ ] **Step 3: Run the crew contract tests to be sure the crew still builds**

Run: `rtk uv run pytest tests/unit/crews/ -v`
Expected: all PASS except `test_task_description_starts_with_a_long_static_block` (still red until Task 3).

- [ ] **Step 4: Commit**

```bash
rtk git add src/finwiz/crews/deep_analysis/config/agents.yaml
rtk git commit -m "feat(crews): drop the ticker from the deep-analysis agent goal

CrewAI renders the goal into the system prompt, so a {ticker} there made
the system prompt differ per holding and defeated implicit prompt caching.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB"
```

---

### Task 3: Reorder the task description

**Files:**
- Modify: `src/finwiz/crews/deep_analysis/config/tasks.yaml:4-107`
- Test: `tests/unit/crews/test_deep_analysis_prompt_layout.py`, `tests/unit/crews/test_deep_analysis_prompt.py`

**Interfaces:**
- Consumes: the 20 placeholder names listed in Global Constraints.
- Produces: a description whose first `{` sits after ≥ 3 000 characters of static text.

The rule text is moved, not rewritten, with two exceptions the spec requires: the title line loses its placeholders, and the two inline `{current_date}` mentions inside ANTI-HALLUCINATION become "la DATE D'ANALYSE indiquée en fin de prompt". The "Le FACT PACK ci-dessus" wording in the static block is changed to "ci-dessous" where the fact pack now comes later.

- [ ] **Step 1: Replace the `deep_qualitative_analysis_task` block**

Replace everything from line 4 (`deep_qualitative_analysis_task:`) through line 107 (`  agent: asset_analyst`) with:

```yaml
deep_qualitative_analysis_task:
  description: >
    Analyse qualitative d'un holding.

    LANGUE: Rédigez en FRANÇAIS. Noms de champs JSON en anglais, contenu en français.

    🚨 ANTI-HALLUCINATION 🚨
    - Tes données d'entraînement peuvent être périmées : la structure corporate
      et la direction (action), l'émetteur (fonds), ou le protocole (crypto) du
      holding, ainsi que ses événements récents, ont pu changer depuis ton
      cutoff. Le FACT PACK fourni en fin de prompt est ta source de vérité sur
      son état actuel — pas tes souvenirs d'entraînement. Tous tes constats
      doivent être cohérents avec la DATE D'ANALYSE indiquée en fin de prompt.
    - Le FACT PACK est ta source PRIMAIRE pour les faits propres à la classe
      d'actif (structure corporate et direction pour une action, émetteur et
      frais pour un fonds, protocole et offre pour une crypto) ainsi que pour
      les événements récents (12 derniers mois). Le champ Description du
      CONTEXT est secondaire.
    - N'invente JAMAIS de filiales, partenariats, ou intégrations non mentionnés
      dans le FACT PACK ou la `Description`.
    - Si tu te souviens d'une structure différente (acquisition, joint-venture,
      filiale) connue avant ton cutoff de formation et NON présente dans le
      FACT PACK ou la `Description`, considère-la comme OBSOLÈTE à la DATE
      D'ANALYSE indiquée en fin de prompt et ignore-la.
    - Quand tu cites des évolutions "récentes", elles doivent dater des 12 mois
      précédant la DATE D'ANALYSE indiquée en fin de prompt, pas d'années
      antérieures.

    🛠️ AUCUN OUTIL EXTERNE — tu n'as accès à aucun tool. Le FACT PACK est déjà
    le résultat de sources structurées vérifiées par Python avant cette tâche,
    donc toute vérification supplémentaire est redondante. Réponds directement
    à partir du FACT PACK et du CONTEXT fournis ; n'émets aucun appel d'outil.

    PROVIDE QUALITATIVE ANALYSIS ONLY:
    1. SEC Insights: Business model (100+ words), competitive advantages, risk factors
    2. Fundamental Context: Industry analysis (100+ words), growth drivers, positioning
    3. Technical Strategy: Chart patterns, support/resistance, entry/exit strategy
    4. Contextual Risks: Regulatory, geopolitical, competitive, operational
    5. Investment Synthesis: Thesis (200+ words), bull/base/bear cases (100+ words each),
       scenario probabilities as floats summing to 1.0, and a concrete action plan.

    🔒 CHAMPS PYTHON-CONTRÔLÉS — NE PAS INCLURE DANS TA SORTIE :
    Python alimente lui-même les champs suivants à partir de sources
    déterministes ; les inclure dans ta réponse n'a AUCUN effet et déclenche
    des cycles de validation inutiles :
    - `fact_pack` (et tous ses sous-champs : les faits propres à la classe
      d'actif affichés dans le FACT PACK — structure/direction pour une action,
      émetteur/frais/lignes pour un fonds, protocole/offre pour une crypto —
      plus `fetched_at`, `freshness`, `confidence`, `source_citations`)
    - `analysis_timestamp`

    Le FACT PACK est en lecture seule pour toi — cite-le si nécessaire dans
    tes narratifs (sec_insights, fundamental_context, contextual_risks), mais
    ne le ré-émets PAS comme champ JSON.

    REQUIRED investment_synthesis structure (all fields mandatory):
    "investment_synthesis": {
      "investment_thesis": "...",
      "bull_case": "...",
      "base_case": "...",
      "bear_case": "...",
      "scenario_probabilities": {"bull": 0.30, "base": 0.50, "bear": 0.20},
      "final_recommendation": "BUY|HOLD|SELL",
      "recommendation_confidence": "LOW|MEDIUM|HIGH",
      "action_plan": {
        "immediate_actions": ["action 1", "action 2"],
        "monitoring_points": ["metric to watch 1", "metric to watch 2"],
        "exit_triggers": ["condition 1", "condition 2"]
      }
    }

    OUTPUT: Valid JSON matching QualitativeInsights schema.
    - ai_confidence: 0.0-1.0
    - analysis_timestamp: ISO 8601 format

    NO trailing commas. NO text outside JSON.

    ---

    📅 DATE D'ANALYSE : {current_date} ({current_date_iso}).

    HOLDING : {ticker} ({asset_class})

    {fact_pack_block}

    Le FACT PACK ci-dessus est AUTORITAIRE pour les faits qu'il contient
    (structure corporate et direction pour une action, émetteur et frais pour
    un fonds, protocole et offre pour une crypto), ainsi que pour les
    événements récents. Tu ne dois JAMAIS le contredire. Si tes souvenirs
    divergent du FACT PACK, le FACT PACK gagne.

    CONTEXT (Python-calculated - DO NOT recalculate):
    - Company: {company_name} | Sector: {sector} | Industry: {industry}
    - Description: {company_description}
    - Grade: {grade}, Score: {composite_score}, Recommendation: {preliminary_recommendation}
    - Scores: Fundamental {fundamental_score}, Technical {technical_score}, Risk {risk_score}
    - Metrics: {fundamental_metrics}
    - Indicators: {technical_indicators}
    - Risk: {risk_metrics}

    {retry_guidance}

  expected_output: >
    QualitativeInsights JSON with sec_insights, fundamental_context,
    technical_strategy, contextual_risks, investment_synthesis.

  agent: asset_analyst
```

Keep the two comment blocks at the top (lines 1-2) and bottom (lines 109-111, `# NOTE: generate_enriched_analysis_task was REMOVED ...`) as they are.

- [ ] **Step 2: Run the layout and prompt tests**

Run: `rtk uv run pytest tests/unit/crews/test_deep_analysis_prompt_layout.py tests/unit/crews/test_deep_analysis_prompt.py -v`
Expected: all 8 PASS. If `test_task_description_starts_with_a_long_static_block` reports the first `{` below 3 000, count with:

```bash
rtk uv run python -c "import yaml;d=yaml.safe_load(open('src/finwiz/crews/deep_analysis/config/tasks.yaml'))['deep_qualitative_analysis_task']['description'];print(d.find('{'))"
```

The static block above is ~3 400 characters after YAML folding. If it prints below 3 000, the block was trimmed during the edit; restore the missing text rather than lowering the threshold.

- [ ] **Step 3: Run the whole crews suite and the analysis helpers tests**

Run: `rtk uv run pytest tests/unit/crews/ tests/unit/analysis/test_helpers.py -v -p no:randomly -q`
Expected: all PASS. (If `tests/unit/analysis/test_helpers.py` does not exist, run `tests/unit/analysis/ -q` instead.)

- [ ] **Step 4: Commit**

```bash
rtk git add src/finwiz/crews/deep_analysis/config/tasks.yaml
rtk git commit -m "feat(crews): put every static rule before per-holding data in the deep-analysis prompt

The description opened with the ticker, the date and the fact pack, so the
shared instruction text was never a shared prefix and OpenRouter's implicit
Gemini cache never hit. Static rules now come first, then a --- separator,
then the date, holding, fact pack, context and retry guidance. No placeholder
was added or removed.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB"
```

---

### Task 4: Docs and changelog

**Files:**
- Modify: `src/finwiz/crews/CLAUDE.md` (insert a section after "Critical Rules", before "## Testing" at line 66)
- Modify: `CHANGELOG.md:9-11` (Unreleased / Changed)

- [ ] **Step 1: Add the prompt-layout section to `src/finwiz/crews/CLAUDE.md`**

Insert before `## Testing`:

```markdown
## Prompt layout: static prefix first

`deep_analysis/config/agents.yaml` and `tasks.yaml` are ordered for
OpenRouter's implicit Gemini prompt cache, which serves a cache read (10× cheaper
input) when two requests share a prefix longer than ~1 024 tokens. CrewAI renders
the agent `goal` into the system prompt and the task `description` into the user
turn, so:

- the `goal` must contain no `{placeholder}`;
- every static rule (language, anti-hallucination, no-tools, the five sections,
  Python-controlled fields, required structure, output rules) comes first in the
  `description`, then a `---` line, then the per-holding data (date, holding,
  `{fact_pack_block}`, CONTEXT, `{retry_guidance}`).

`tests/unit/crews/test_deep_analysis_prompt_layout.py` pins this: the first `{`
in the description must sit after 3 000 characters of static text. When editing
the prompt, add rules to the top block and data to the bottom block. Holdings run
in parallel, so the first wave of a run misses the cache; the gain is cents per
run, and the layout costs nothing to keep.
```

- [ ] **Step 2: Add the CHANGELOG entry**

Under `## [Unreleased]` / `### Changed`, before the existing "Consolidated family report" bullet, add:

```markdown
- Deep-analysis crew prompt reordered for implicit prompt caching. The agent
  goal no longer carries the ticker, and the task description puts every
  static rule before a `---` separator, with the date, holding, fact pack,
  context and retry guidance after it. OpenRouter's Gemini cache now sees a
  shared prefix across the 67 per-holding calls; the saving is cents per run.
  `tests/unit/crews/test_deep_analysis_prompt_layout.py` pins the layout.
```

- [ ] **Step 3: Lint and run the full unit suite**

Run: `rtk make lint && rtk make test`
Expected: lint clean, suite green. `make lint` runs `ruff format` on Markdown python fences; the two snippets above are `markdown`/none, so nothing is rewritten.

- [ ] **Step 4: Commit**

```bash
rtk git add src/finwiz/crews/CLAUDE.md CHANGELOG.md
rtk git commit -m "docs(crews): record the static-prefix prompt layout rule

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB"
```

---

### Task 5: Live verification and PR

**Files:** none modified.

- [ ] **Step 1: Three-holding pipeline run**

Confirm the three one-line CSVs exist (memory: "Verify the pipeline for $0.04"): `ls output/verify_*.csv` or wherever `PORTFOLIO_STOCK_CSV` / `PORTFOLIO_ETF_CSV` / `PORTFOLIO_CRYPTO_CSV` were pointed last time (`rtk git log -S'PORTFOLIO_STOCK_CSV' --oneline | head -3` to find the recipe). Then:

```bash
PORTFOLIO_STOCK_CSV=<stock.csv> PORTFOLIO_ETF_CSV=<etf.csv> PORTFOLIO_CRYPTO_CSV=<crypto.csv> rtk uv run kickoff; echo "exit=$?"
```

Expected: exit 0, three `output/*/<ticker>_enriched.json` with a non-fallback `qualitative` section (`ai_confidence > 0.1`), and `output/run_summary.json` `per_crew.deep_analysis_*` cost not above the previous run's for the same three holdings.

- [ ] **Step 2: Optional cache check**

Open the OpenRouter activity page for the account and inspect the second or third deep-analysis generation of the run. `cached_tokens > 0` confirms the prefix is being served from cache. Record the number in the PR body if seen; if not seen, say so, the three holdings likely ran in the same wave.

- [ ] **Step 3: Push and open the PR**

```bash
rtk git push -u origin feat/cache-friendly-deep-analysis-prompt
rtk gh pr create --title "feat(crews): cache-friendly deep-analysis prompt layout" --body "$(cat <<'EOF'
## Summary

- Agent goal no longer carries `{ticker}`; the system prompt is identical for every holding.
- Task description reordered: every static rule first, then `---`, then date / holding / fact pack / context / retry guidance.
- New `tests/unit/crews/test_deep_analysis_prompt_layout.py` pins the static prefix (≥ 3 000 chars before the first placeholder, goal has no placeholder, every placeholder is a `_build_crew_inputs` key).
- Docs: `src/finwiz/crews/CLAUDE.md` section, CHANGELOG.

Spec: `docs/superpowers/specs/2026-09-20-cache-friendly-deep-analysis-prompt-design.md`.

## Test plan

- [ ] `make lint`, `make test` green
- [ ] Three-CSV pipeline run: qualitative section validates for all three holdings, crew cost not higher than before
- [ ] (optional) OpenRouter dashboard shows `cached_tokens > 0` on a later holding

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB
EOF
)"
```

- [ ] **Step 4: Wait for CI, merge, sync main**

```bash
rtk gh pr checks --watch
rtk gh pr merge --merge --delete-branch
rtk git checkout main && rtk git pull
```

Expected: PR merged with a merge commit, local `main` at the merge commit. Then start the research-provider plan from a fresh branch off `main`.
