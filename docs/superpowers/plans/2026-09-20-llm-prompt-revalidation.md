# LLM Prompt Revalidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Send the deep-analysis schema once (as `response_format`), make every
schema field description the field's French prompt, frame the task per asset
class, run strategic research before the crew and feed it into the prompt, and
ground SWOT/Porter with the fact pack.

**Architecture:** CrewAI appends a 9 kB schema text plus converter boilerplate
to the user prompt whenever a Task uses `output_pydantic`; switching the task to
`response_model` keeps the strict `json_schema` response format and drops the
text. Field descriptions in the Pydantic schemas travel inside that
`json_schema`, so they become the per-field instructions. The per-holding
pipeline (`analysis/stages/__init__.py`) moves `_safe_strategic` before
`qualify`, and a new renderer turns the `StrategicAnalysis` into a prompt block.

**Tech Stack:** Python 3.13, CrewAI 1.15.22 (native OpenRouter provider),
Pydantic 2, pytest + pytest-mock, ruff (line length 180), mypy, vulture.

**Spec:** `docs/superpowers/specs/2026-09-20-llm-prompt-revalidation-design.md`

## Global Constraints

- `unittest.mock` is banned; use `mocker` from pytest-mock only.
- `json.dumps` always with `default=str`.
- Pydantic models live under `src/finwiz/schemas/`; the two bridging schemas
  (`_QualitativeInsightsRaw` in `analysis/stages/qualify.py`, `_FactPackRaw` in
  `analysis/fact_pack_research.py`) stay where they are.
- Line length 180. Run `make lint` before every commit.
- Field descriptions and prompt text are French; JSON field names stay English
  and unchanged (the report and tests read them).
- The deep-analysis task uses `response_model=`, never `output_pydantic=`.
- Never print, log or commit an API key or a `.env` value.
- Docs (ADR, CHANGELOG, CLAUDE.md files) ship in this branch.
- Prefix shell commands with `rtk`. Run tests with
  `uv run pytest <path> -q -p no:randomly`.
- Commit messages end with:

```text
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB
```

## File Structure

| File | Responsibility |
|---|---|
| `src/finwiz/crews/deep_analysis/deep_analysis.py` | Task wiring (`response_model`), LLM config call, log line |
| `src/finwiz/config/llm/llm_config.py` | `get_configured_llm` without `force_json_object` |
| `src/finwiz/schemas/hybrid_analysis/qualitative.py` | Qualitative field descriptions (French, budgets) |
| `src/finwiz/schemas/hybrid_analysis/strategic.py` | SWOT/Porter/posture field descriptions |
| `src/finwiz/analysis/fact_pack_research.py` | `_FactPackRaw` descriptions, null-tolerant validator |
| `src/finwiz/schemas/perplexity.py` | `NewsHeadline`/`NewsDigest` descriptions |
| `src/finwiz/crews/deep_analysis/config/tasks.yaml` | Static rules block, dynamic block with `{asset_focus}` and `{strategic_block}` |
| `src/finwiz/analysis/strategic_render.py` (new) | `to_prompt_block(strategic, current_date)` |
| `src/finwiz/analysis/_helpers.py` | `_build_crew_inputs`: `asset_focus`, `strategic_block` |
| `src/finwiz/analysis/stages/__init__.py` | Strategic research before qualify, facts to SWOT/Porter |
| `src/finwiz/analysis/stages/qualify.py` | `_safe_strategic(..., facts=)`, `_try_ai_qualify(..., strategic=)` |
| `src/finwiz/analysis/strategic_research.py` | `facts` kwarg through to the SWOT/Porter prompts |
| `src/finwiz/infrastructure/json/crewai_json_patch.py` | Repair only registered classes |
| `src/finwiz/tools/perplexity_logging.py`, `perplexity_performance.py` | Log labels, baseline warning removed |
| `scripts/prose_lengths.py` (new) | Word medians per qualitative field over `output/**/*_enriched.json` |
| `docs/adr/ADR-013-schema-as-prompt-and-strategic-first-qualify.md` (new) | Decision record |

---

### Task 1: Task wiring — schema once, `force_json_object` removed

**Files:**

- Modify: `src/finwiz/crews/deep_analysis/deep_analysis.py:255-320`, `:396-401`
- Modify: `src/finwiz/config/llm/llm_config.py:266-300`, `:373-380`
- Delete: `tests/unit/config/test_llm_config_json_mode.py`
- Modify: `tests/unit/config/test_llm_config_reasoning_effort.py:136-145`
- Modify: `tests/unit/crews/test_deep_analysis_crew.py:62-93`
- Test: `tests/unit/crews/test_deep_analysis_crew.py`

**Interfaces:**

- Consumes: `crewai.Task(response_model=...)` (CrewAI 1.15.22, `task.py:195`);
  `crewai.agent.utils.build_task_prompt_with_schema(task, prompt)` appends the
  schema text only when `output_pydantic` is set and `response_model` is not.
- Produces: `get_configured_llm(model_override=None, model_type="standard", max_tokens=None)` (no `force_json_object`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/crews/test_deep_analysis_crew.py` inside the existing test class (same indentation as the neighbouring tests):

```text
    def test_task_uses_response_model_not_output_pydantic(self, monkeypatch):
        """CrewAI appends a 9 kB schema text + converter boilerplate to the prompt when a
        Task carries output_pydantic. response_model keeps the strict json_schema
        response_format and appends nothing (crewai.agent.utils.build_task_prompt_with_schema)."""
        # CrewBase resolves the task's agent at init, which builds the LLM and validates keys.
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
        from crewai.agent.utils import build_task_prompt_with_schema

        from finwiz.analysis.stages.qualify import _QualitativeInsightsRaw
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        task = DeepAnalysisCrew().deep_qualitative_analysis_task()

        assert task.response_model is _QualitativeInsightsRaw
        assert task.output_pydantic is None
        assert build_task_prompt_with_schema(task, "PROMPT") == "PROMPT"
```

Replace the two `force_json_object` assertions in the same file (`assert kwargs["force_json_object"] is True`, lines 76 and 93) with:

```text
        assert "force_json_object" not in kwargs
```

and rename `test_configured_llm_forces_json_and_honors_model_override` to `test_configured_llm_honors_model_override` with the docstring `"""_get_configured_llm respects LLM_MODEL_DEEP_ANALYSIS and no longer asks for json_object mode."""`.

In `tests/unit/config/test_llm_config_reasoning_effort.py`, delete
`test_should_combine_with_force_json_object_in_same_extra_body` (lines 136-145).

Delete `tests/unit/config/test_llm_config_json_mode.py` with `rtk git rm`.

- [ ] **Step 2: Run the new test to verify it fails**

Run: `uv run pytest tests/unit/crews/test_deep_analysis_crew.py -q -p no:randomly`
Expected: FAIL on `assert task.response_model is _QualitativeInsightsRaw` (it is `None`) and the two `"force_json_object" not in kwargs` assertions.

- [ ] **Step 3: Rewire the task and drop the kwarg**

In `src/finwiz/crews/deep_analysis/deep_analysis.py`:

Replace the task body (the `return Task(...)` at lines 309-316) with:

```text
        return Task(
            config=self.tasks_config["deep_qualitative_analysis_task"],
            # response_model, not output_pydantic: CrewAI sends the schema as a strict
            # json_schema response_format either way, but output_pydantic ALSO appends the
            # pretty-printed schema (9 kB) plus "Preserve the original content exactly
            # as-is" converter boilerplate to the user prompt
            # (crewai.agent.utils.build_task_prompt_with_schema). qualify._extract_qualitative
            # reads the raw JSON, so the empty `pydantic` slot costs nothing.
            response_model=self.QualitativeInsightsRaw,
        )
```

Replace the two `get_configured_llm(...)` calls at lines 274-275 with the same calls minus `force_json_object=True`, and delete the comment block that starts with `# force_json_object:` (lines 268-271). Replace it with:

```text
        # No provider "json_object" mode: CrewAI already sends the task's response_model as
        # a strict json_schema response_format, which wins over any extra_body override
        # (verified on the outbound request, 2026-09-20).
```

Replace the log line at line 401 with:

```text
            logger.info("No tools: the analyst answers from the prompt, the fact pack and the strategic block only.")
```

and the comment block above it (lines 395-400) with:

```text
            # Python pre-summarizes the bulk of inputs to keep the prompt small. The
            # asset_analyst agent has no tools (see _build_asset_analyst_tools): every
            # fact it may use is already in the prompt.
```

Rewrite the `asset_analyst` docstring (lines 279-289) to:

```text
        """Qualitative analyst. No tools: answers from the prompt only.

        The fact pack and the strategic block are interpolated into the task
        description by ``analysis/_helpers._build_crew_inputs``; there is nothing
        left for a tool to verify (see ``_build_asset_analyst_tools``).
        """
```

In `src/finwiz/config/llm/llm_config.py`: remove the `force_json_object: bool = False` parameter, its docstring paragraph (`force_json_object: When True ...` through `... at the request level.`), and the block at lines 373-380 (from the comment `# Provider-enforced JSON output` through the `logger.info("Provider JSON mode enabled ...")` line).

- [ ] **Step 4: Run the tests and the gates**

Run: `uv run pytest tests/unit/crews/test_deep_analysis_crew.py tests/unit/config -q -p no:randomly`
Expected: PASS.
Run: `rtk grep -rn "force_json_object" src tests` → no output.
Run: `make lint && uv run mypy src/finwiz`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
rtk git add -A src/finwiz/crews/deep_analysis/deep_analysis.py src/finwiz/config/llm/llm_config.py tests/unit/crews/test_deep_analysis_crew.py tests/unit/config
rtk git commit -m "feat(crews): send the qualitative schema once, as response_format

Task(response_model=) replaces output_pydantic on the deep-analysis task so
CrewAI stops appending the 9 kB schema text and its converter boilerplate to
every prompt. force_json_object is deleted: the json_schema response_format
always won over the extra_body json_object override."
```

---

### Task 2: Qualitative field descriptions are the field prompt

**Files:**

- Modify: `src/finwiz/schemas/hybrid_analysis/qualitative.py` (every `Field(... description=...)`)
- Modify: `src/finwiz/analysis/stages/qualify.py:66-71` (`_QualitativeInsightsRaw` field descriptions)
- Create: `tests/unit/schemas/test_prompt_descriptions.py`

**Interfaces:**

- Produces: French descriptions on every model-filled field; Task 3 extends the same test to three more modules.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/schemas/test_prompt_descriptions.py`:

```python
"""Field descriptions are prompt text: they travel inside the json_schema response_format.

Every field the research or crew model fills must carry a French, specific
description. English filler ("Comprehensive", "Key", "List of") is the
signature of the generic descriptions this replaced.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from finwiz.analysis.stages.qualify import _QualitativeInsightsRaw
from finwiz.schemas.hybrid_analysis.qualitative import (
    ActionPlan,
    ContextualRiskInsights,
    FundamentalContextInsights,
    InvestmentSynthesis,
    ScenarioProbabilities,
    SecAnalysisInsights,
    TechnicalStrategyInsights,
)

_ENGLISH_FILLER = ("Comprehensive", "Key ", "List of", "AI's ", "Identified")

MODEL_FILLED: list[type[BaseModel]] = [
    SecAnalysisInsights,
    FundamentalContextInsights,
    TechnicalStrategyInsights,
    ContextualRiskInsights,
    ScenarioProbabilities,
    ActionPlan,
    InvestmentSynthesis,
    _QualitativeInsightsRaw,
]


@pytest.mark.parametrize("model", MODEL_FILLED, ids=lambda m: m.__name__)
def test_every_field_has_a_french_description(model: type[BaseModel]) -> None:
    for name, field in model.model_fields.items():
        description = field.description or ""
        assert len(description) >= 25, f"{model.__name__}.{name}: description missing or too short"
        for filler in _ENGLISH_FILLER:
            assert filler not in description, f"{model.__name__}.{name}: English filler {filler!r} in description"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/unit/schemas/test_prompt_descriptions.py -q -p no:randomly`
Expected: FAIL for every model (English descriptions; `_QualitativeInsightsRaw` fields have none).

- [ ] **Step 3: Rewrite the descriptions**

In `src/finwiz/schemas/hybrid_analysis/qualitative.py`, replace each `description="..."` value (nothing else on the line changes):

```text
SecAnalysisInsights
  business_model:          "Modèle économique en 120-180 mots : comment le holding gagne de l'argent (action), stratégie de réplication et exposition (fonds), utilité et économie du protocole (crypto)."
  competitive_advantages:  "3 à 5 avantages durables, une phrase chacun, avec la preuve tirée du FACT PACK ou de la RECHERCHE STRATÉGIQUE."
  risk_factors:            "3 à 5 risques propres au holding, une phrase chacun, terminée par la gravité entre parenthèses : (faible), (moyenne) ou (élevée)."
  strategic_initiatives:   "2 à 4 initiatives en cours datées des 12 derniers mois avant la DATE D'ANALYSE, avec l'effet attendu."

FundamentalContextInsights
  industry_analysis:       "Secteur et tendances en 80-120 mots, cohérents avec la DATE D'ANALYSE ; pas de chiffres déjà fournis par le CONTEXT Python."
  growth_drivers:          "3 à 5 moteurs de croissance, un par ligne, sans recopier les métriques Python."
  competitive_positioning: "Position concurrentielle en 60-100 mots, appuyée sur les cinq forces de la RECHERCHE STRATÉGIQUE."
  management_assessment:   "Direction et gouvernance (action), émetteur et gestion (fonds), équipe et gouvernance du protocole (crypto), 40-80 mots, uniquement des faits du FACT PACK."

TechnicalStrategyInsights
  chart_patterns:          "1 à 3 configurations lisibles dans les indicateurs fournis, nommées en une ligne ; liste vide si aucune."
  support_resistance:      "Niveaux de support et de résistance déduits des indicateurs fournis, avec la logique en une ou deux phrases."
  entry_exit_strategy:     "Plan d'entrée et de sortie avec des niveaux de prix, 40-80 mots."
  timing_assessment:       "Momentum et timing en une ou deux phrases, cohérents avec le score technique du CONTEXT."

ContextualRiskInsights
  regulatory_risks:        "2 à 4 risques réglementaires ou de conformité propres au holding, datés s'ils tiennent à un événement."
  geopolitical_risks:      "2 à 4 risques géopolitiques ou macroéconomiques qui touchent ce holding en particulier."
  competitive_risks:       "2 à 4 risques concurrentiels ou de marché, nommant les acteurs concernés."
  operational_risks:       "2 à 4 risques opérationnels ou d'exécution propres au holding."
  stress_scenarios:        "2 à 3 scénarios de stress, chacun avec l'effet attendu sur le holding en une phrase."

ScenarioProbabilities
  bull:                    "Probabilité du scénario haussier entre 0 et 1 ; bull + base + bear = 1,0."
  base:                    "Probabilité du scénario central entre 0 et 1 ; bull + base + bear = 1,0."
  bear:                    "Probabilité du scénario baissier entre 0 et 1 ; bull + base + bear = 1,0."

ActionPlan
  immediate_actions:       "2 à 4 actions concrètes et vérifiables à mener maintenant."
  monitoring_points:       "2 à 4 métriques ou événements à surveiller, avec le seuil qui compte."
  exit_triggers:           "2 à 4 conditions précises qui déclencheraient la sortie."

InvestmentSynthesis
  investment_thesis:       "Thèse d'investissement en 150-250 mots qui relie les faits, la recherche stratégique et les scores Python."
  bull_case:               "Scénario haussier en 80-120 mots avec ses catalyseurs."
  base_case:               "Scénario central en 80-120 mots, le plus probable."
  bear_case:               "Scénario baissier en 80-120 mots avec ses risques déclencheurs."
  scenario_probabilities:  "Probabilités bull, base et bear ; leur somme vaut 1,0."
  final_recommendation:    "Recommandation finale : BUY, HOLD ou SELL."
  recommendation_confidence: "Confiance dans la recommandation : LOW, MEDIUM ou HIGH."
  action_plan:             "Plan d'action : immediate_actions, monitoring_points, exit_triggers."

QualitativeInsights (canonical, Python-filled fields keep an English description; model-filled ones align with the raw schema)
  investment_synthesis:    "Synthèse d'investissement et recommandation."
  sec_insights:            "Modèle économique, avantages, risques et initiatives du holding."
  fundamental_context:     "Contexte sectoriel, moteurs de croissance, positionnement, direction."
  technical_strategy:      "Lecture technique et plan d'entrée/sortie."
  contextual_risks:        "Risques réglementaires, géopolitiques, concurrentiels, opérationnels et scénarios de stress."
  ai_confidence:           "Confiance globale entre 0 et 1, fondée sur la couverture du FACT PACK et de la RECHERCHE STRATÉGIQUE."
```

In `src/finwiz/analysis/stages/qualify.py`, give `_QualitativeInsightsRaw`'s six fields the same descriptions as the matching `QualitativeInsights` fields above (`investment_synthesis`, `sec_insights`, `fundamental_context`, `technical_strategy`, `contextual_risks`, `ai_confidence`), e.g. `investment_synthesis: InvestmentSynthesis | None = Field(default=None, description="Synthèse d'investissement et recommandation.")`.

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/unit/schemas -q -p no:randomly && uv run pytest tests/unit/analysis/stages tests/unit/crews -q -p no:randomly`
Expected: PASS.
Run: `make lint`
Expected: clean (line length 180 accommodates the longest description; wrap the string with implicit concatenation if ruff complains).

- [ ] **Step 5: Commit**

```bash
rtk git add src/finwiz/schemas/hybrid_analysis/qualitative.py src/finwiz/analysis/stages/qualify.py tests/unit/schemas/test_prompt_descriptions.py
rtk git commit -m "feat(schemas): French, budgeted descriptions on every qualitative field

The descriptions travel inside the json_schema response_format, so they are
the model's per-field instructions."
```

---

### Task 3: Research schema descriptions and a null-tolerant `_FactPackRaw`

**Files:**

- Modify: `src/finwiz/schemas/hybrid_analysis/strategic.py:163-300` (descriptions only)
- Modify: `src/finwiz/analysis/fact_pack_research.py:53-57`, `:93-104` (and the `corporate_structure` branch)
- Modify: `src/finwiz/schemas/perplexity.py:140-155`
- Modify: `tests/unit/schemas/test_prompt_descriptions.py` (extend `MODEL_FILLED`)
- Test: `tests/unit/analysis/test_fact_pack_research.py`

**Interfaces:**

- Consumes: constants `MAX_BULLETS_SWOT = 4`, `MAX_PROSE_CHARS = 400`, `MAX_RATIONALE_CHARS = 250`, `MAX_VERDICT_CHARS = 200`, `MAX_PORTFOLIO_PROSE_CHARS = 800` from `strategic.py:98-112`.
- Produces: nothing new; `_FactPackRaw(leadership=None)` validates.

- [ ] **Step 1: Write the failing tests**

Extend `MODEL_FILLED` in `tests/unit/schemas/test_prompt_descriptions.py`:

```text
from finwiz.analysis.fact_pack_research import _FactPackRaw
from finwiz.schemas.hybrid_analysis.strategic import FiveForcesAnalysis, ForceRating, PortfolioPostureNarrative, SwotAnalysis
from finwiz.schemas.perplexity import NewsDigest, NewsHeadline
...
MODEL_FILLED = [
    ...existing eight...,
    SwotAnalysis,
    ForceRating,
    FiveForcesAnalysis,
    PortfolioPostureNarrative,
    _FactPackRaw,
    NewsHeadline,
    NewsDigest,
]
```

Add to `tests/unit/analysis/test_fact_pack_research.py`, a new class at the end of the file:

```python
class TestFactPackRawNullProse:
    """Gemini returns null, not "", for a prose field it could not source
    (2026-09-20 run: 8 validation failures, 39 field errors, all retried).
    Null and non-string prose must map to the placeholder, never raise."""

    def test_null_leadership_and_structure_become_placeholder(self) -> None:
        raw = _FactPackRaw.model_validate({"leadership": None, "corporate_structure": None, "recent_events": []})
        assert raw.leadership == "Information indisponible"
        assert raw.corporate_structure == "Information indisponible"

    def test_non_string_prose_becomes_placeholder(self) -> None:
        raw = _FactPackRaw.model_validate({"leadership": ["CEO"], "corporate_structure": 42})
        assert raw.leadership == "Information indisponible"
        assert raw.corporate_structure == "Information indisponible"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/schemas/test_prompt_descriptions.py tests/unit/analysis/test_fact_pack_research.py -q -p no:randomly`
Expected: description test FAILS for the seven new models; `TestFactPackRawNullProse` FAILS with `ValidationError: Input should be a valid string`.

- [ ] **Step 3: Descriptions and the validator**

`src/finwiz/schemas/hybrid_analysis/strategic.py`, description values only:

```text
SwotAnalysis
  strengths:              f"Au plus {MAX_BULLETS_SWOT} forces internes, une phrase chacune, avec un fait vérifié par la recherche web."
  weaknesses:             f"Au plus {MAX_BULLETS_SWOT} faiblesses internes, une phrase chacune, avec un fait vérifié."
  opportunities:          f"Au plus {MAX_BULLETS_SWOT} opportunités externes datées des 12 derniers mois, une phrase chacune."
  threats:                f"Au plus {MAX_BULLETS_SWOT} menaces externes actuelles, une phrase chacune, avec l'acteur ou l'événement concerné."
  strategic_assessment:   f"Synthèse en {MAX_PROSE_CHARS} caractères maximum qui pèse forces et opportunités contre faiblesses et menaces."
  strategic_score:        "Favorabilité stratégique entre 0 et 1 : 0 = défavorable, 1 = très favorable (S+O contre W+T)."
  confidence:             "Confiance entre 0 et 1 fondée sur la qualité et la fraîcheur des sources consultées."

ForceRating
  intensity:              "LOW = favorable au holding, MEDIUM = neutre, HIGH = défavorable."
  rationale:              f"Justification en {MAX_RATIONALE_CHARS} caractères maximum avec des acteurs nommés et des chiffres récents vérifiés."

FiveForcesAnalysis
  threat_of_new_entrants:     "Barrières à l'entrée : intensité et justification."
  bargaining_power_suppliers: "Pouvoir de négociation des fournisseurs (ou du fournisseur d'indice, des validateurs) : intensité et justification."
  bargaining_power_customers: "Pouvoir de négociation des clients (ou des investisseurs, des plateformes) : intensité et justification."
  threat_of_substitutes:      "Menace des produits, fonds ou protocoles de substitution : intensité et justification."
  competitive_rivalry:        "Intensité de la rivalité entre acteurs, émetteurs ou protocoles : intensité et justification."
  competitive_position_summary: f"Position concurrentielle et solidité du moat en {MAX_PROSE_CHARS} caractères maximum."
  strategic_score:            "Solidité du moat entre 0 et 1 : 1 = moat large, 0 = aucun moat."
  confidence:                 "Confiance entre 0 et 1 fondée sur la qualité et la fraîcheur des sources consultées."

PortfolioPostureNarrative
  portfolio_strengths:     "Forces agrégées du portefeuille : concentration de moats, avantages structurels, une phrase chacune."
  portfolio_weaknesses:    "Faiblesses agrégées : risques de concentration, moats faibles, lacunes d'exposition."
  portfolio_opportunities: "Vents porteurs transversaux dont plusieurs lignes peuvent profiter."
  portfolio_threats:       "Risques systémiques qui touchent plusieurs lignes à la fois."
  competitive_landscape_summary: f"Synthèse Porter inter-lignes (industries aux moats les plus forts et les plus faibles), {MAX_PORTFOLIO_PROSE_CHARS} caractères maximum."
  dominant_themes:         "3 à 5 thèmes stratégiques récurrents dans le portefeuille."
  overall_assessment:      f"Narratif final sur la posture stratégique du portefeuille, {MAX_PORTFOLIO_PROSE_CHARS} caractères maximum."
  competitive_verdict:     f"Une phrase sur le paysage concurrentiel, {MAX_VERDICT_CHARS} caractères maximum, lisible par un non-financier."
  swot_verdict:            f"Une phrase sur le SWOT agrégé, {MAX_VERDICT_CHARS} caractères maximum, lisible par un non-financier."
  strategic_score:         "Favorabilité stratégique globale du portefeuille entre 0 et 1."
  confidence:              "Confiance entre 0 et 1 dans cette synthèse."
```

The constants are defined above the classes in the same module (lines 98-112), so the f-strings resolve at import.

`src/finwiz/analysis/fact_pack_research.py`, `_FactPackRaw` fields:

```text
    corporate_structure: str = Field(
        default=_PLACEHOLDER,
        max_length=_CORPORATE_STRUCTURE_MAX_CHARS,
        description="Structure corporate actuelle en 2000 caractères maximum : maison mère, filiales, acquisitions et cessions des 24 derniers mois, vérifiées sur le web. Écris « Information indisponible » si aucune source fiable.",
    )
    recent_events: list[str] = Field(default_factory=list, max_length=10, description="Au plus 10 événements des 12 derniers mois, une phrase de 200 caractères maximum chacun, datés, tirés de pages web consultées.")
    leadership: str = Field(
        default=_PLACEHOLDER,
        max_length=_LEADERSHIP_MAX_CHARS,
        description="Dirigeants actuels (PDG, directeur financier, président du conseil) avec leur date de prise de fonction, 1000 caractères maximum. Écris « Information indisponible » si aucune source fiable.",
    )
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confiance entre 0 et 1 fondée sur la qualité et la fraîcheur des sources consultées.")
    source_citations: list[str] = Field(default_factory=list, max_length=20, description="URLs http(s) exactes des pages consultées, au plus 20.")
```

In `_normalize_llm_payload`, replace the `leadership` and `corporate_structure` blocks so a non-string value maps to the placeholder. For `leadership` (the `corporate_structure` block gets the identical shape with its own constant):

```text
        leadership = data.get("leadership")
        if not isinstance(leadership, str):
            if leadership is not None:
                logger.debug(f"leadership was {type(leadership).__name__}, using placeholder")
            data["leadership"] = _PLACEHOLDER
        else:
            stripped = leadership.strip()
            if not stripped:
                data["leadership"] = _PLACEHOLDER
            elif len(stripped) > _LEADERSHIP_MAX_CHARS:
                logger.warning(f"leadership truncated from {len(stripped)} to {_LEADERSHIP_MAX_CHARS} chars")
                data["leadership"] = stripped[:_LEADERSHIP_MAX_CHARS].rstrip()
            else:
                data["leadership"] = stripped
```

`src/finwiz/schemas/perplexity.py`:

```text
class NewsHeadline(BaseModel):
    """One headline the research model found on the web."""

    title: str = Field(description="Titre exact de l'article tel qu'il apparaît sur la page consultée.")
    url: str = Field(description="URL http(s) exacte de la page consultée, sans raccourcisseur.")
    one_line_summary: str = Field(default="", description="Résumé factuel en une phrase de ce que l'article annonce.")


class NewsDigest(BaseModel):
    """Minimal structured reply for the sentiment news search.

    No numeric or length constraints: this model is sent as a strict
    ``json_schema`` and a rejected keyword would fail every call. Clamping
    happens in Python.
    """

    headlines: list[NewsHeadline] = Field(default_factory=list, description="Titres trouvés, du plus récent au plus ancien ; liste vide si aucune page fiable.")
```

(add `from pydantic import BaseModel, Field` if `Field` is not imported yet).

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/unit/schemas tests/unit/analysis/test_fact_pack_research.py tests/unit/analysis/fact_pack tests/unit/analysis/test_strategic_asset_classes.py tests/unit/tools -q -p no:randomly`
Expected: PASS.
Run: `make lint && uv run mypy src/finwiz`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
rtk git add src/finwiz/schemas/hybrid_analysis/strategic.py src/finwiz/analysis/fact_pack_research.py src/finwiz/schemas/perplexity.py tests/unit/schemas/test_prompt_descriptions.py tests/unit/analysis/test_fact_pack_research.py
rtk git commit -m "feat(schemas): French descriptions on the research schemas, null-tolerant fact-pack prose

_FactPackRaw maps a null or non-string leadership/corporate_structure to the
placeholder instead of failing validation and burning retries."
```

---

### Task 4: `analysis/strategic_render.py` — the strategic block

**Files:**

- Create: `src/finwiz/analysis/strategic_render.py`
- Create: `tests/unit/analysis/test_strategic_render.py`

**Interfaces:**

- Consumes: `StrategicAnalysis`, `SwotAnalysis`, `FiveForcesAnalysis`, `MAX_BULLETS_SWOT` from `finwiz.schemas.hybrid_analysis.strategic`.
- Produces: `to_prompt_block(strategic: StrategicAnalysis | None, current_date: str) -> str`; constants `STRATEGIC_BLOCK_MAX_CHARS = 2000`, `RATIONALE_PREVIEW_CHARS = 160`, `UNAVAILABLE = "Recherche stratégique non disponible."`.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/analysis/test_strategic_render.py`:

```python
"""to_prompt_block renders the SWOT/Porter research as one prompt block for the crew."""

from __future__ import annotations

from finwiz.analysis.strategic_render import RATIONALE_PREVIEW_CHARS, STRATEGIC_BLOCK_MAX_CHARS, UNAVAILABLE, to_prompt_block
from finwiz.schemas.hybrid_analysis.strategic import FiveForcesAnalysis, ForceRating, StrategicAnalysis, SwotAnalysis

_DATE = "20 septembre 2026"


def _full() -> StrategicAnalysis:
    swot = SwotAnalysis(
        strengths=["Marque forte", "Trésorerie nette"],
        weaknesses=["Dépendance à un fournisseur"],
        opportunities=["Marché indien"],
        threats=["Réglementation UE"],
        strategic_assessment="Position solide malgré la pression réglementaire.",
        strategic_score=0.7,
        confidence=0.8,
    )
    porter = FiveForcesAnalysis(
        threat_of_new_entrants=ForceRating(intensity="LOW", rationale="Capex élevé"),
        bargaining_power_suppliers=ForceRating(intensity="MEDIUM", rationale="Deux fondeurs"),
        bargaining_power_customers=ForceRating(intensity="HIGH", rationale="Clients concentrés " * 20),
        threat_of_substitutes=ForceRating(intensity="LOW", rationale="Peu d'alternatives"),
        competitive_rivalry=ForceRating(intensity="HIGH", rationale="Guerre des prix"),
        competitive_position_summary="Moat large sur le segment premium.",
        strategic_score=0.65,
        confidence=0.75,
    )
    return StrategicAnalysis(swot=swot, five_forces=porter)


def test_none_renders_the_unavailable_line() -> None:
    assert to_prompt_block(None, _DATE) == UNAVAILABLE


def test_full_block_lists_swot_and_five_forces() -> None:
    block = to_prompt_block(_full(), _DATE)
    assert block.startswith("🧭 RECHERCHE STRATÉGIQUE (web, au 20 septembre 2026")
    assert "score SWOT 0.70" in block and "moat 0.65" in block
    assert "- Forces : Marque forte | Trésorerie nette" in block
    assert "- Menaces : Réglementation UE" in block
    assert "- Synthèse : Position solide malgré la pression réglementaire." in block
    assert "- Nouveaux entrants : LOW — Capex élevé" in block
    assert "- Rivalité : HIGH — Guerre des prix" in block
    assert "- Position : Moat large sur le segment premium." in block


def test_rationale_is_previewed_and_block_is_capped() -> None:
    block = to_prompt_block(_full(), _DATE)
    clients_line = next(line for line in block.splitlines() if line.startswith("- Clients :"))
    assert len(clients_line) <= len("- Clients : HIGH — ") + RATIONALE_PREVIEW_CHARS + 1
    assert len(block) <= STRATEGIC_BLOCK_MAX_CHARS


def test_missing_framework_renders_non_disponible() -> None:
    only_swot = StrategicAnalysis(swot=_full().swot, five_forces=None)
    block = to_prompt_block(only_swot, _DATE)
    assert "Porter : non disponible" in block
    assert "- Forces : Marque forte" in block
    only_porter = StrategicAnalysis(swot=None, five_forces=_full().five_forces)
    assert "SWOT : non disponible" in to_prompt_block(only_porter, _DATE)


def test_empty_swot_lists_render_a_dash() -> None:
    empty = StrategicAnalysis(swot=SwotAnalysis(), five_forces=None)
    assert "- Forces : —" in to_prompt_block(empty, _DATE)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/analysis/test_strategic_render.py -q -p no:randomly`
Expected: FAIL with `ModuleNotFoundError: finwiz.analysis.strategic_render`.

- [ ] **Step 3: Write the renderer**

Create `src/finwiz/analysis/strategic_render.py`:

```python
"""Render the SWOT/Porter research as one block for the deep-analysis prompt.

One renderer owns the wording, like ``analysis/fact_pack/render.py`` does for
the fact pack, so the crew prompt cannot drift from what the research
produced. The block is capped so a verbose model cannot push the per-holding
data out of the model's attention or past the cache budget.
"""

from __future__ import annotations

from finwiz.schemas.hybrid_analysis.strategic import MAX_BULLETS_SWOT, FiveForcesAnalysis, ForceRating, StrategicAnalysis, SwotAnalysis

STRATEGIC_BLOCK_MAX_CHARS = 2000
RATIONALE_PREVIEW_CHARS = 160
UNAVAILABLE = "Recherche stratégique non disponible."

_FORCE_LABELS: tuple[tuple[str, str], ...] = (
    ("threat_of_new_entrants", "Nouveaux entrants"),
    ("bargaining_power_suppliers", "Fournisseurs"),
    ("bargaining_power_customers", "Clients"),
    ("threat_of_substitutes", "Substituts"),
    ("competitive_rivalry", "Rivalité"),
)


def _bullets(items: list[str]) -> str:
    kept = [item.strip() for item in items[:MAX_BULLETS_SWOT] if item and item.strip()]
    return " | ".join(kept) if kept else "—"


def _preview(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _swot_lines(swot: SwotAnalysis | None) -> list[str]:
    if swot is None:
        return ["SWOT : non disponible"]
    return [
        "SWOT",
        f"- Forces : {_bullets(swot.strengths)}",
        f"- Faiblesses : {_bullets(swot.weaknesses)}",
        f"- Opportunités : {_bullets(swot.opportunities)}",
        f"- Menaces : {_bullets(swot.threats)}",
        f"- Synthèse : {_preview(swot.strategic_assessment, 400) or '—'}",
    ]


def _force_line(label: str, force: ForceRating) -> str:
    return f"- {label} : {force.intensity} — {_preview(force.rationale, RATIONALE_PREVIEW_CHARS) or '—'}"


def _porter_lines(porter: FiveForcesAnalysis | None) -> list[str]:
    if porter is None:
        return ["Porter : non disponible"]
    lines = ["Porter"]
    lines.extend(_force_line(label, getattr(porter, attr)) for attr, label in _FORCE_LABELS)
    lines.append(f"- Position : {_preview(porter.competitive_position_summary, 400) or '—'}")
    return lines


def _score(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def to_prompt_block(strategic: StrategicAnalysis | None, current_date: str) -> str:
    """The strategic research as one block for the qualitative prompt.

    ``None`` (both frameworks failed) renders one explicit line so the model
    knows the section is absent rather than guessing it was never asked.
    """
    if strategic is None:
        return UNAVAILABLE
    swot_score = _score(strategic.swot.strategic_score if strategic.swot else None)
    moat_score = _score(strategic.five_forces.strategic_score if strategic.five_forces else None)
    header = f"🧭 RECHERCHE STRATÉGIQUE (web, au {current_date}, score SWOT {swot_score}, moat {moat_score})"
    lines = [header, *_swot_lines(strategic.swot), *_porter_lines(strategic.five_forces)]
    block = "\n".join(lines)
    if len(block) > STRATEGIC_BLOCK_MAX_CHARS:
        block = block[: STRATEGIC_BLOCK_MAX_CHARS - 1].rstrip() + "…"
    return block
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/unit/analysis/test_strategic_render.py -q -p no:randomly && make lint && uv run mypy src/finwiz`
Expected: PASS, clean.

- [ ] **Step 5: Commit**

```bash
rtk git add src/finwiz/analysis/strategic_render.py tests/unit/analysis/test_strategic_render.py
rtk git commit -m "feat(analysis): render the strategic research as a capped prompt block"
```

---

### Task 5: `tasks.yaml` rewrite and the new crew inputs

**Files:**

- Modify: `src/finwiz/crews/deep_analysis/config/tasks.yaml` (description replaced in full)
- Modify: `src/finwiz/analysis/_helpers.py:154-221`
- Modify: `tests/unit/crews/test_deep_analysis_prompt_layout.py`
- Modify: `tests/unit/analysis/test_helpers.py`

**Interfaces:**

- Consumes: `to_prompt_block` from Task 4.
- Produces: `_build_crew_inputs(ctx, quant, raw_data=None, *, fact_pack=None, strategic=None)` with keys `asset_focus` and `strategic_block`; constant `ASSET_FOCUS: dict[str, str]` in `_helpers.py`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/analysis/test_helpers.py`:

```python
def test_build_crew_inputs_asset_focus_per_asset_class() -> None:
    from finwiz.analysis._helpers import _build_crew_inputs
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext

    quant = _make_quant()
    stock = _build_crew_inputs(AnalysisContext(ticker="AAPL", asset_class="stock", company_name="Apple"), quant, {})
    etf = _build_crew_inputs(AnalysisContext(ticker="VUSA.L", asset_class="etf", company_name="Vanguard"), quant, {})
    crypto = _build_crew_inputs(AnalysisContext(ticker="BTC-USD", asset_class="crypto", company_name="Bitcoin"), quant, {})

    assert stock["asset_focus"].startswith("Analyse une action")
    assert "Ne décris pas un émetteur" in etf["asset_focus"]
    assert crypto["asset_focus"].startswith("Analyse un actif crypto")
    assert len({stock["asset_focus"], etf["asset_focus"], crypto["asset_focus"]}) == 3


def test_build_crew_inputs_unknown_asset_class_falls_back_to_stock_focus() -> None:
    from finwiz.analysis._helpers import ASSET_FOCUS, _build_crew_inputs
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext

    inputs = _build_crew_inputs(AnalysisContext(ticker="X", asset_class="bond", company_name="X"), _make_quant(), {})
    assert inputs["asset_focus"] == ASSET_FOCUS["stock"]


def test_build_crew_inputs_strategic_block_defaults_to_unavailable() -> None:
    from finwiz.analysis._helpers import _build_crew_inputs
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext
    from finwiz.analysis.strategic_render import UNAVAILABLE

    inputs = _build_crew_inputs(AnalysisContext(ticker="X", asset_class="stock", company_name="X"), _make_quant(), {})
    assert inputs["strategic_block"] == UNAVAILABLE


def test_build_crew_inputs_renders_strategic_block() -> None:
    from finwiz.analysis._helpers import _build_crew_inputs
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext
    from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis, SwotAnalysis

    strategic = StrategicAnalysis(swot=SwotAnalysis(strengths=["Marque forte"], strategic_score=0.7), five_forces=None)
    inputs = _build_crew_inputs(AnalysisContext(ticker="X", asset_class="stock", company_name="X"), _make_quant(), {}, strategic=strategic)
    assert inputs["strategic_block"].startswith("🧭 RECHERCHE STRATÉGIQUE")
    assert "Marque forte" in inputs["strategic_block"]
    assert "Porter : non disponible" in inputs["strategic_block"]
```

In `tests/unit/crews/test_deep_analysis_prompt_layout.py`, add after `test_every_placeholder_is_a_crew_input_key`:

```python
def test_dynamic_block_carries_asset_focus_and_strategic_block() -> None:
    description = _task_description()
    static, _, dynamic = description.partition("\n---\n")
    assert "{asset_focus}" in dynamic and "{strategic_block}" in dynamic
    assert dynamic.index("{fact_pack_block}") < dynamic.index("{strategic_block}") < dynamic.index("{retry_guidance}")
    assert "{" not in static


def test_static_block_has_no_contradiction_and_no_inline_schema() -> None:
    description = _task_description()
    assert "analysis_timestamp: ISO" not in description
    assert '"investment_synthesis": {' not in description
    assert "SEC Insights" not in description
    assert "strategic_analysis" in description  # listed as Python-controlled
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/analysis/test_helpers.py tests/unit/crews/test_deep_analysis_prompt_layout.py -q -p no:randomly`
Expected: the four new helper tests FAIL with `KeyError: 'asset_focus'` / `TypeError: unexpected keyword 'strategic'`; the two new layout tests FAIL.

- [ ] **Step 3: Rewrite the task description**

Replace the whole `description: >` value of `deep_qualitative_analysis_task` in `src/finwiz/crews/deep_analysis/config/tasks.yaml` with (keep `expected_output` and `agent` as they are):

```yaml
  description: >
    Analyse qualitative d'un holding.

    LANGUE : rédige en FRANÇAIS. Noms de champs JSON en anglais, contenu en français.

    🚨 ANTI-HALLUCINATION 🚨
    - Tes données d'entraînement peuvent être périmées : la structure corporate
      et la direction (action), l'émetteur (fonds), ou le protocole (crypto) du
      holding, ainsi que ses événements récents, ont pu changer depuis ton
      cutoff. Le FACT PACK fourni en fin de prompt est ta source de vérité sur
      son état actuel — pas tes souvenirs d'entraînement. Tous tes constats
      doivent être cohérents avec la DATE D'ANALYSE indiquée en fin de prompt.
    - N'invente JAMAIS de filiales, partenariats, ou intégrations non mentionnés
      dans le FACT PACK, la RECHERCHE STRATÉGIQUE ou la Description.
    - Si tu te souviens d'une structure différente (acquisition, joint-venture,
      filiale) connue avant ton cutoff de formation et NON présente dans le
      FACT PACK ou la Description, considère-la comme OBSOLÈTE à la DATE
      D'ANALYSE et ignore-la.
    - Quand tu cites des évolutions "récentes", elles doivent dater des 12 mois
      précédant la DATE D'ANALYSE, pas d'années antérieures.

    🛠️ AUCUN OUTIL EXTERNE — tu n'as accès à aucun tool. Réponds directement à
    partir du prompt ; n'émets aucun appel d'outil.

    📚 SOURCES, par ordre de priorité :
    1. Le FACT PACK (faits structurés vérifiés par Python) et la RECHERCHE
       STRATÉGIQUE (SWOT et cinq forces, issus d'une recherche web datée),
       tous deux en fin de prompt : sources primaires, à ne jamais contredire.
    2. Le CONTEXT calculé par Python (scores, métriques, indicateurs) : source
       secondaire, à citer sans recalculer.
    3. Ta mémoire d'entraînement : en dernier recours, uniquement pour des
       mécanismes généraux, jamais pour des faits datés.

    🔒 CHAMPS PYTHON-CONTRÔLÉS — NE PAS INCLURE DANS TA SORTIE :
    Python alimente lui-même `fact_pack`, `strategic_analysis` et
    `analysis_timestamp` ; les inclure n'a aucun effet et déclenche des cycles
    de validation inutiles. Cite le FACT PACK et la RECHERCHE STRATÉGIQUE dans
    tes narratifs, mais ne les ré-émets pas comme champs JSON.

    📏 BUDGET : respecte la longueur indiquée dans la description de chaque
    champ du schéma (thèse 150-250 mots ; scénarios bull, base et bear 80-120
    mots chacun ; modèle économique 120-180 mots ; listes de 2 à 5 éléments).
    Ne remplis pas pour remplir : un champ sans fait solide reste court.

    OUTPUT : un objet JSON valide conforme au schéma fourni, sans texte hors
    JSON, sans balise markdown, sans virgule finale. ai_confidence entre 0.0 et
    1.0.

    ---

    📅 DATE D'ANALYSE : {current_date} ({current_date_iso}).

    HOLDING : {ticker} ({asset_class})

    {asset_focus}

    {fact_pack_block}

    Le FACT PACK ci-dessus est AUTORITAIRE pour les faits qu'il contient
    (structure corporate et direction pour une action, émetteur et frais pour
    un fonds, protocole et offre pour une crypto), ainsi que pour les
    événements récents. Tu ne dois JAMAIS le contredire. Si tes souvenirs
    divergent du FACT PACK, le FACT PACK gagne.

    {strategic_block}

    CONTEXT (Python-calculated - DO NOT recalculate):
    - Company: {company_name} | Sector: {sector} | Industry: {industry}
    - Description: {company_description}
    - Grade: {grade}, Score: {composite_score}, Recommendation: {preliminary_recommendation}
    - Scores: Fundamental {fundamental_score}, Technical {technical_score}, Risk {risk_score}
    - Metrics: {fundamental_metrics}
    - Indicators: {technical_indicators}
    - Risk: {risk_metrics}

    {retry_guidance}
```

- [ ] **Step 4: Extend `_build_crew_inputs`**

In `src/finwiz/analysis/_helpers.py`, add the import `from finwiz.analysis.strategic_render import to_prompt_block as strategic_to_prompt_block` (the module already imports `to_prompt_block` from `fact_pack.render`; keep both names distinct) and `from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis` (under `TYPE_CHECKING` if the module uses that pattern for `FactPack`; match the existing import style).

Add the module-level constant above `_build_crew_inputs`:

```text
# One paragraph per asset class, interpolated as {asset_focus} in the dynamic
# block of tasks.yaml. The static block stays asset-neutral so it caches.
ASSET_FOCUS: dict[str, str] = {
    "stock": (
        "Analyse une action : modèle économique, avantages concurrentiels, direction, "
        "initiatives des 12 derniers mois, risques réglementaires et opérationnels."
    ),
    "etf": (
        "Analyse un fonds indiciel : émetteur, indice suivi, réplication, frais, concentration "
        "sectorielle et géographique, liquidité, risques de contrepartie. "
        "Ne décris pas un émetteur comme une entreprise à analyser."
    ),
    "crypto": (
        "Analyse un actif crypto : protocole, utilité, offre et émission, activité des "
        "développeurs, gouvernance, garde et réglementation par juridiction."
    ),
}
```

Change the signature to `def _build_crew_inputs(ctx: AnalysisContext, quant: QuantitativeAnalysis, raw_data: dict[str, Any] | None = None, *, fact_pack: FactPack | None = None, strategic: StrategicAnalysis | None = None) -> dict[str, Any]:` and, right after the `fact_pack_block` assignment, add:

```text
    inputs["asset_focus"] = ASSET_FOCUS.get(inputs["asset_class"], ASSET_FOCUS["stock"])
    # Strategic research (SWOT/Porter) now runs before the crew (stages/__init__.py)
    # and is rendered by one renderer so the prompt cannot drift from the report.
    inputs["strategic_block"] = strategic_to_prompt_block(strategic, inputs["current_date"])
```

- [ ] **Step 5: Re-measure the static prefix**

Run:

```bash
uv run python -c "
import re, yaml
d = yaml.safe_load(open('src/finwiz/crews/deep_analysis/config/tasks.yaml'))['deep_qualitative_analysis_task']['description']
print(re.search(r'\{([A-Za-z_][A-Za-z0-9_-]*)\}', d).start())"
```

Set `_MIN_STATIC_PREFIX_CHARS` in `tests/unit/crews/test_deep_analysis_prompt_layout.py` to the printed value rounded down to the nearest 100 minus 300 (e.g. printed 4180 → 3800), and update the comment above it with the measured position. The value must be ≥ 3400 (the previous floor); if it is lower, the static block lost text and the rewrite is wrong.

- [ ] **Step 6: Run the tests**

Run: `uv run pytest tests/unit/analysis/test_helpers.py tests/unit/crews tests/unit/analysis/stages -q -p no:randomly && make lint && uv run mypy src/finwiz`
Expected: PASS, clean.

- [ ] **Step 7: Commit**

```bash
rtk git add src/finwiz/crews/deep_analysis/config/tasks.yaml src/finwiz/analysis/_helpers.py tests/unit/crews/test_deep_analysis_prompt_layout.py tests/unit/analysis/test_helpers.py
rtk git commit -m "feat(crews): asset-class framing and the strategic block in the qualitative prompt

The static block keeps only rules (sources, Python-owned fields, budget,
output); the dynamic block gains {asset_focus} and {strategic_block}. The
analysis_timestamp contradiction and the inline JSON example are gone."
```

---

### Task 6: Strategic research before the crew, grounded by the fact pack

**Files:**

- Modify: `src/finwiz/analysis/strategic_research.py:107-113`, `:152-157`, `:195-300`
- Modify: `src/finwiz/analysis/stages/qualify.py:118-140`, `:211-215`, `:256-270`
- Modify: `src/finwiz/analysis/stages/__init__.py:88-108`
- Modify: `tests/unit/analysis/test_strategic_asset_classes.py`
- Modify: `tests/unit/analysis/stages/test_pipeline.py`

**Interfaces:**

- Consumes: `to_prompt_block(fact_pack)` from `finwiz.analysis.fact_pack.render`; `_build_crew_inputs(..., strategic=)` from Task 5.
- Produces: `gather_strategic_analysis(..., facts: str = "")`, `gather_strategic_analysis_sync(..., facts: str = "")`, `_swot_prompt(..., asset_class="stock", facts="")`, `_porter_prompt(..., asset_class="stock", facts="")`, `_safe_strategic(ticker, sector, industry, description, *, asset_class="stock", facts="")`, `_try_ai_qualify(ctx, quant, raw_data=None, fact_pack=None, strategic=None)`; `stage_ctx.extras["strategic"]`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/unit/analysis/test_strategic_asset_classes.py` a new class at the end:

```python
class TestFactsGrounding:
    """SWOT/Porter prompts carry the fact pack when the pipeline has one."""

    def test_swot_prompt_inserts_verified_facts(self):
        from finwiz.analysis.strategic_research import _swot_prompt

        prompt = _swot_prompt("DELL", "Tech", "Hardware", "desc", "20 septembre 2026", asset_class="stock", facts="- Direction : Michael Dell (CEO)")
        assert "Faits vérifiés" in prompt
        assert "Michael Dell" in prompt
        assert prompt.index("Faits vérifiés") < prompt.index("Sois spécifique")

    def test_porter_prompt_inserts_verified_facts(self):
        from finwiz.analysis.strategic_research import _porter_prompt

        prompt = _porter_prompt("DELL", "Tech", "Hardware", "desc", "20 septembre 2026", asset_class="stock", facts="- Direction : Michael Dell (CEO)")
        assert "Faits vérifiés" in prompt and "Michael Dell" in prompt

    def test_prompts_without_facts_are_unchanged(self):
        from finwiz.analysis.strategic_research import _porter_prompt, _swot_prompt

        assert "Faits vérifiés" not in _swot_prompt("DELL", "", "", "", "20 septembre 2026")
        assert "Faits vérifiés" not in _porter_prompt("DELL", "", "", "", "20 septembre 2026")

    def test_gather_forwards_facts_to_both_prompts(self, mocker):
        import finwiz.analysis.strategic_research as sr

        seen: list[str] = []

        async def fake_research(**kwargs):
            seen.append(kwargs["prompt"])
            return None

        mocker.patch.object(sr, "research_with_retry", side_effect=fake_research)
        assert sr.gather_strategic_analysis_sync(ticker="DELL", facts="- Direction : Michael Dell (CEO)") is None
        assert len(seen) == 2 and all("Michael Dell" in p for p in seen)
```

Add to `tests/unit/analysis/stages/test_pipeline.py` a new test (reuse the mocks of `test_strategic_research_runs_for_every_asset_class`, lines 215-247, verbatim, then replace the strategic mock and the assertions):

```python
def test_strategic_research_runs_before_the_crew_and_reaches_its_inputs(tmp_path: Path, mocker: Any) -> None:
    """Strategic research must run before qualify so the crew prompt can carry it,
    and it must receive the fact pack as `facts`."""
    mocker.patch("finwiz.analysis.stages.collect._collect_raw_data_inner", return_value={"price_history": [1, 2, 3], "sector": "Tech"})
    fake_partial = DeepAnalysisResult.model_construct(ticker="X", asset_class="stock", grade="B", composite_score=0.7, recommendation="HOLD")
    fake_quant = QuantitativeAnalysis.model_construct()
    mocker.patch("finwiz.analysis.stages.quantify._calculate_quantitative_inner", return_value=(fake_partial, fake_quant))
    mocker.patch("finwiz.analysis.stages._compute_options_probabilities", return_value=None)

    from datetime import UTC, datetime

    fake_fact_pack = FactPack(
        asset_class="stock",
        details=EquityFacts(business_summary="Test Corp — independent.", leadership="CEO Test"),
        fetched_at=datetime.now(UTC),
        freshness="fresh",
        confidence=0.9,
        source_citations=[],
    )
    mocker.patch("finwiz.analysis.stages.fact_pack._fact_pack_inner", return_value=fake_fact_pack)

    from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis, SwotAnalysis

    fake_strategic = StrategicAnalysis(swot=SwotAnalysis(strengths=["Marque forte"]), five_forces=None)
    order: list[str] = []

    def _strategic(*args: Any, **kwargs: Any) -> StrategicAnalysis:
        order.append("strategic")
        assert "CEO Test" in kwargs["facts"]
        return fake_strategic

    def _ai(analysis_ctx: Any, quant: Any, raw_data: Any = None, fact_pack: Any = None, strategic: Any = None) -> QualitativeInsights:
        order.append("crew")
        assert strategic is fake_strategic
        return QualitativeInsights.model_construct()

    mocker.patch("finwiz.analysis.stages.qualify._safe_strategic", side_effect=_strategic)
    mocker.patch("finwiz.analysis.stages.qualify._try_ai_qualify", side_effect=_ai)
    fake_enriched = EnrichedAnalysis.model_construct()
    mocker.patch("finwiz.analysis.stages.synthesize._synthesize_inner", return_value=fake_enriched)
    fake_verdict = DeepAnalysisResult.model_construct(ticker="X", asset_class="stock", grade="B", composite_score=0.7, recommendation="HOLD")
    mocker.patch("finwiz.analysis.stages.emit._build_verdict_inner", return_value=(fake_verdict, fake_enriched))

    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext

    ledger = RunLedger(run_id="strategic-first", artifact_dir=tmp_path)
    ctx = AnalysisContext(ticker="AAPL", asset_class="stock", company_name="Test", ledger=ledger, run_id=ledger.run_id)
    run_pipeline(ctx)

    assert order == ["strategic", "crew"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/analysis/test_strategic_asset_classes.py tests/unit/analysis/stages/test_pipeline.py -q -p no:randomly`
Expected: `TestFactsGrounding` FAILS with `TypeError: unexpected keyword argument 'facts'`; the pipeline test FAILS with `order == ["crew", "strategic"]`.

- [ ] **Step 3: Thread `facts` through the strategic prompts**

In `src/finwiz/analysis/strategic_research.py` add, above `_swot_prompt`:

```text
def _facts_fragment(facts: str) -> str:
    """Fact-pack facts for grounding; empty when the pipeline has none."""
    if not facts.strip():
        return ""
    return "Faits vérifiés (sources structurées, à ne pas contredire ; la recherche web complète, elle ne remplace pas) :\n" + facts.strip() + "\n\n"
```

Change `_swot_prompt` to:

```text
def _swot_prompt(ticker: str, sector: str, industry: str, description: str, current_date: str, *, asset_class: str = "stock", facts: str = "") -> str:
    return (
        _date_preamble(current_date) + f"Analyse SWOT pour {ticker} ({sector} / {industry}).\n"
        f"Description: {description or 'Non fournie'}\n\n"
        f"{_facts_fragment(facts)}"
        f"{_swot_focus(asset_class)}\n\n"
        f"{_swot_caps_fragment(current_date)}"
    )
```

and `_porter_prompt` to:

```text
def _porter_prompt(ticker: str, sector: str, industry: str, description: str, current_date: str, *, asset_class: str = "stock", facts: str = "") -> str:
    return (
        _date_preamble(current_date) + f"Analyse des Cinq Forces de Porter pour {ticker} ({sector} / {industry}).\n"
        f"Description: {description or 'Non fournie'}\n\n"
        f"{_facts_fragment(facts)}"
        f"{_porter_focus(asset_class)} {_porter_caps_fragment(current_date)}"
    )
```

Add `facts: str = ""` as the last keyword parameter of both `gather_strategic_analysis` and `gather_strategic_analysis_sync`; pass `facts=facts` to both prompt builders in `gather_strategic_analysis` and forward it in the sync wrapper's `coro = gather_strategic_analysis(..., facts=facts)`. Add one docstring line to `gather_strategic_analysis`: ``` ``facts`` is the rendered fact pack (``fact_pack.render.to_prompt_block``), truncated by the caller; it grounds both prompts. ```

- [ ] **Step 4: Reorder the stages and pass the strategic result to the crew**

In `src/finwiz/analysis/stages/qualify.py`:

- `_safe_strategic` gains `facts: str = ""` (keyword) and forwards `facts=facts` to `gather_strategic_analysis_sync`.
- `_try_ai_qualify` gains `strategic: Any = None` after `fact_pack` and calls `_build_crew_inputs(ctx, quant, raw_data, fact_pack=fact_pack, strategic=strategic)`.
- `qualify` reads `strategic = ctx.extras.get("strategic")` and calls `_try_ai_qualify(analysis_ctx, quant, raw, fact_pack=fact_pack, strategic=strategic)`.

In `src/finwiz/analysis/stages/__init__.py`, replace lines 88-108 (from the `# Phase 3: Qualify` comment through `qual = qual.model_copy(update={"strategic_analysis": strategic})`) with:

```text
    # Phase 2d: Strategic research (SWOT/Porter) for every asset class, before the
    # crew so the qualitative prompt can carry it ({strategic_block}). Grounded by
    # the fact pack. Non-fatal: None means "no evidence", and the crew prompt says so.
    from finwiz.analysis.fact_pack.render import to_prompt_block as fact_pack_to_prompt_block
    from finwiz.analysis.stages.qualify import _safe_strategic

    sector = str(raw_data.get("sector") or raw_data.get("Sector") or "")
    industry = str(raw_data.get("industry") or raw_data.get("Industry") or "")
    description = str(raw_data.get("longBusinessSummary") or raw_data.get("description") or raw_data.get("company_description") or "")
    facts = fact_pack_to_prompt_block(fpr.payload)[:_FACTS_MAX_CHARS]
    strategic = _safe_strategic(ctx.ticker, sector, industry, description, asset_class=ctx.asset_class, facts=facts)
    stage_ctx.extras["strategic"] = strategic

    # Phase 3: Qualify — any FAILED result short-circuits to AnalysePending.
    qr3 = qualify(stage_ctx, quant, raw_data)
    if qr3.payload is None:
        return _emit_pending(stage_ctx, reason=qr3.provenance.reason), _pending_enriched(stage_ctx, reason=qr3.provenance.reason)
    qual = qr3.payload
    if strategic is not None:
        qual = qual.model_copy(update={"strategic_analysis": strategic})
```

and add the module constant near the top of `stages/__init__.py`:

```text
# The fact pack rendered for the SWOT/Porter prompts; capped so a long fund
# holdings list cannot crowd out the research question.
_FACTS_MAX_CHARS = 1500
```

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/unit/analysis tests/unit/crews tests/regression -q -p no:randomly && make lint && uv run mypy src/finwiz`
Expected: PASS, clean. `test_three_holding_pipeline_ok_degraded_failed`, `test_pipeline_short_circuits_when_fact_pack_fails` and `test_strategic_research_runs_for_every_asset_class` still pass (they patch `_safe_strategic` and `_try_ai_qualify`; the fake `_ai_qualify` in the first test must accept the new `strategic` kwarg: add `strategic: Any = None` to its signature at line 76).

- [ ] **Step 6: Commit**

```bash
rtk git add src/finwiz/analysis/strategic_research.py src/finwiz/analysis/stages/qualify.py src/finwiz/analysis/stages/__init__.py tests/unit/analysis/test_strategic_asset_classes.py tests/unit/analysis/stages/test_pipeline.py
rtk git commit -m "feat(analysis): run strategic research before the crew and ground it with the fact pack

SWOT/Porter now precede qualify; their result is rendered into the crew
prompt as {strategic_block}, and both research prompts carry the rendered
fact pack as verified facts."
```

---

### Task 7: JSON-repair patch scoped to registered classes, log hygiene

**Files:**

- Modify: `src/finwiz/infrastructure/json/crewai_json_patch.py`
- Modify: `src/finwiz/crews/deep_analysis/deep_analysis.py:114`, `:172-177`
- Modify: `src/finwiz/tools/perplexity_logging.py:74-100`
- Modify: `src/finwiz/tools/perplexity_performance.py:33-58`
- Create: `tests/unit/infrastructure/test_crewai_json_patch.py`
- Modify: `tests/tools/test_perplexity_performance_validation.py` (delete `test_should_validate_response_time_requirement_correctly`, lines 30-39, and the `meets_2x_requirement` / `EXCEEDS 2x BASELINE REQUIREMENT` assertions at lines 79 and 90-91; the warning-path test becomes an info-path test asserting `"Web research latency"` in the message) and `tests/tools/test_perplexity_rate_limiting_validation.py` (delete `test_should_validate_response_time_requirements`, lines 64-74).

**Interfaces:**

- Produces: `register_repairable(cls: type[BaseModel]) -> None`, `is_repairable(cls) -> bool` in `crewai_json_patch.py`.

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/infrastructure/test_crewai_json_patch.py`:

```python
"""The JSON-repair monkeypatch must only touch classes that opted in.

It patches BaseModel.model_validate_json process-wide; on the 2026-09-20 run it
fired on every research schema (SwotAnalysis, FiveForcesAnalysis, NewsDigest)
and logged 16 "JSON repair failed" errors for validations the research client
handles itself.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from finwiz.infrastructure.json import crewai_json_patch as patch_module


class _Registered(BaseModel):
    value: int


class _Unregistered(BaseModel):
    value: int


@pytest.fixture
def patched():
    patch_module.apply_json_repair_patch()
    patch_module.register_repairable(_Registered)
    yield
    patch_module.remove_json_repair_patch()
    patch_module._REPAIRABLE.clear()


def test_registered_class_is_repaired(patched) -> None:
    assert _Registered.model_validate_json('{"value": 1,}').value == 1


def test_unregistered_class_bypasses_repair(patched, mocker) -> None:
    spy = mocker.patch.object(patch_module, "repair_json", wraps=patch_module.repair_json)
    with pytest.raises(ValidationError):
        _Unregistered.model_validate_json('{"value": 1,}')
    spy.assert_not_called()


def test_is_repairable_reflects_registration(patched) -> None:
    assert patch_module.is_repairable(_Registered)
    assert not patch_module.is_repairable(_Unregistered)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/infrastructure/test_crewai_json_patch.py -q -p no:randomly`
Expected: FAIL with `AttributeError: register_repairable`.

- [ ] **Step 3: Scope the patch**

In `src/finwiz/infrastructure/json/crewai_json_patch.py`, add after `_patch_lock`:

```text
# Classes that opted in to repair. Everything else goes straight to Pydantic:
# the research client validates its own replies and logs field paths itself.
_REPAIRABLE: set[type[BaseModel]] = set()


def register_repairable(cls: type[BaseModel]) -> None:
    """Opt a model class in to JSON repair on validation failure."""
    with _patch_lock:
        _REPAIRABLE.add(cls)


def is_repairable(cls: type[BaseModel]) -> bool:
    return cls in _REPAIRABLE
```

and make `_patched_model_validate_json` start with:

```text
    if cls not in _REPAIRABLE:
        return _original_model_validate_json(cls, json_data, **kwargs)
```

(the existing `try:` block follows unchanged).

In `src/finwiz/crews/deep_analysis/deep_analysis.py`, next to `self.QualitativeInsightsRaw = _QualitativeInsightsRaw` (line 177) add `register_repairable(_QualitativeInsightsRaw)` and extend the import on line 79 to `from finwiz.infrastructure.json.crewai_json_patch import apply_json_repair_patch, register_repairable`.

In `src/finwiz/tools/perplexity_logging.py`: `"Perplexity search initiated"` → `"Web research initiated"`, `"Perplexity search completed successfully"` → `"Web research completed"`; the `operation` extras stay.

In `src/finwiz/tools/perplexity_performance.py` `log_performance_metrics`: delete `meets_requirement`, `"meets_2x_requirement"`, the `log_level` branch and the warning; keep one `logger.info(f"Web research latency: {latency_ms}ms", extra=extra_data)` with `extra_data` minus the two removed keys. Delete `validate_response_time_requirement` and `MAX_ACCEPTABLE_RESPONSE_TIME_MS` (their only readers are the two tests named above; confirm with `rtk grep -rn "validate_response_time_requirement\|MAX_ACCEPTABLE_RESPONSE_TIME_MS" src tests`), keep `BASELINE_RESPONSE_TIME_MS` only if `performance_ratio` is still logged.

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/unit/infrastructure tests/tools tests/unit/crews -q -p no:randomly && make lint && uv run mypy src/finwiz && uvx vulture src/finwiz --min-confidence 80`
Expected: PASS, clean.

- [ ] **Step 5: Commit**

```bash
rtk git add src/finwiz/infrastructure/json/crewai_json_patch.py src/finwiz/crews/deep_analysis/deep_analysis.py src/finwiz/tools/perplexity_logging.py src/finwiz/tools/perplexity_performance.py tests/unit/infrastructure/test_crewai_json_patch.py tests/tools
rtk git commit -m "fix(infra): repair JSON only for registered crew schemas, retire the Sonar log labels"
```

---

### Task 8: Docs, prose-length script, verification run

**Files:**

- Create: `docs/adr/ADR-013-schema-as-prompt-and-strategic-first-qualify.md`
- Create: `scripts/prose_lengths.py`
- Modify: `src/finwiz/crews/CLAUDE.md:66-85`
- Modify: `src/finwiz/analysis/CLAUDE.md:26-62`
- Modify: `CHANGELOG.md` (Unreleased)
- Test: `tests/unit/scripts/test_prose_lengths.py` (create; mirror the layout of the nearest existing test under `tests/unit/scripts/`, or create the directory with an empty `__init__.py` if none exists)

**Interfaces:**

- Produces: `scripts/prose_lengths.py` with `summarise(paths: Iterable[Path]) -> dict[str, float]` (field → median words) and a `main()` printing one line per field.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/scripts/test_prose_lengths.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from scripts.prose_lengths import summarise


def test_summarise_returns_median_words_per_prose_field(tmp_path: Path) -> None:
    def write(name: str, thesis: str) -> Path:
        path = tmp_path / f"{name}_enriched.json"
        path.write_text(json.dumps({"qualitative": {"investment_synthesis": {"investment_thesis": thesis, "bull_case": "a b c"}}}, default=str), encoding="utf-8")
        return path

    files = [write("A", "un deux trois"), write("B", "un deux trois quatre cinq"), write("C", "un")]
    medians = summarise(files)
    assert medians["investment_synthesis.investment_thesis"] == 3
    assert medians["investment_synthesis.bull_case"] == 3
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/unit/scripts/test_prose_lengths.py -q -p no:randomly`
Expected: FAIL with `ModuleNotFoundError: scripts.prose_lengths`.

- [ ] **Step 3: Write the script**

Create `scripts/prose_lengths.py`:

```python
"""Median word count per qualitative prose field over enriched analyses.

Usage: uv run python scripts/prose_lengths.py [output]
Compares a run against the budgets the prompt asks for (thesis 150-250 words,
scenarios 80-120, business model 120-180).
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

_SECTIONS = ("sec_insights", "fundamental_context", "technical_strategy", "contextual_risks", "investment_synthesis")


def summarise(paths: Iterable[Path]) -> dict[str, float]:
    words: dict[str, list[int]] = defaultdict(list)
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        qualitative = data.get("qualitative") or {}
        for section in _SECTIONS:
            body = qualitative.get(section) or {}
            for key, value in body.items():
                if isinstance(value, str) and value.strip():
                    words[f"{section}.{key}"].append(len(value.split()))
    return {field: statistics.median(counts) for field, counts in sorted(words.items())}


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path("output")
    medians = summarise(root.glob("**/*_enriched.json"))
    for field, median in medians.items():
        print(f"{field:55s} median words = {median:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Write the docs**

Create `docs/adr/ADR-013-schema-as-prompt-and-strategic-first-qualify.md`:

```markdown
# ADR-013: Schema as Prompt and Strategic-First Qualify

- **Status:** Accepted
- **Date:** 2026-09-20
- **Deciders:** FinWiz Core Team
- **Related:** ADR-010 (fact-pack grounded qualitative), ADR-012 (OpenRouter research provider)

## Context

A capture of the deep-analysis crew's outbound request showed the model
receiving the task description, then a 9 kB pretty-printed JSON schema plus a
"preserve the original content exactly as-is" converter instruction, plus the
same schema again as a strict `json_schema` response format. CrewAI appends the
text whenever a Task uses `output_pydantic`. The `force_json_object` override
never reached the request. Field descriptions in the Pydantic schemas were
generic English, yet they are what the model reads for each field. The crew
ran before the SWOT/Porter research, so the web-grounded findings never
informed the qualitative narrative, and the research prompts never saw the
fact pack.

## Decision

1. The deep-analysis task uses `Task(response_model=...)`, never
   `output_pydantic`. The schema is sent once, as `response_format`.
2. Every model-filled field carries a French description with a length target
   and asset-class wording. Descriptions are prompt text and are reviewed as
   such; `tests/unit/schemas/test_prompt_descriptions.py` rejects English
   filler.
3. `tasks.yaml` keeps only static rules before the `---` line; asset-class
   framing (`{asset_focus}`) and the strategic block (`{strategic_block}`) sit
   in the dynamic block.
4. Strategic research runs before `qualify` (`analysis/stages/__init__.py`),
   grounded by the rendered fact pack, and is rendered into the crew prompt by
   `analysis/strategic_render.py`.
5. The JSON-repair monkeypatch applies only to classes registered with
   `register_repairable`.

## Consequences

- About 2 500 prompt tokens per holding removed, 500-700 added for the
  strategic block; the cacheable static prefix grows.
- Strategic research latency now precedes the crew instead of following it;
  total per-holding time is unchanged (both were sequential).
- A change to a schema description changes the prompt; the description test
  is the review gate.
- `force_json_object` is gone; provider JSON mode is CrewAI's `json_schema`.
```

`src/finwiz/crews/CLAUDE.md`, replace the "Prompt layout: static prefix first" section body with:

```markdown
`deep_analysis/config/agents.yaml` and `tasks.yaml` are ordered for
OpenRouter's implicit Gemini prompt cache, which serves a cache read (10× cheaper
input) when two requests share a prefix longer than ~1 024 tokens. CrewAI renders
the agent `goal` into the system prompt and the task `description` into the user
turn, so:

- the `goal` must contain no `{placeholder}`;
- every static rule (language, anti-hallucination, no-tools, sources,
  Python-controlled fields, budget, output rules) comes first in the
  `description`, then a `---` line, then the per-holding data (date, holding,
  `{asset_focus}`, `{fact_pack_block}`, `{strategic_block}`, CONTEXT,
  `{retry_guidance}`).

Three rules that are easy to break:

- The task uses `Task(response_model=...)`, **never** `output_pydantic`. With
  `output_pydantic` CrewAI appends the whole pretty-printed schema plus a
  "preserve the original content" converter instruction to every prompt
  (`crewai.agent.utils.build_task_prompt_with_schema`); with `response_model`
  it sends the schema once, as a strict `json_schema` response format.
- Field descriptions in `schemas/hybrid_analysis/qualitative.py` travel inside
  that `json_schema`. They are the model's per-field instructions: French, with
  a length target. `tests/unit/schemas/test_prompt_descriptions.py` enforces it.
- `{asset_focus}` (one paragraph per asset class) and `{strategic_block}`
  (rendered by `analysis/strategic_render.py`) are per-holding data and belong
  after the `---` line.

`tests/unit/crews/test_deep_analysis_prompt_layout.py` pins the layout: the
first placeholder must sit after the measured static prefix. When editing the
prompt, add rules to the top block and data to the bottom block.
```

`src/finwiz/analysis/CLAUDE.md`: in the stage tree add `strategic_research.py` under "3b. strategic (OpenRouter web research, before qualify)" and update the architecture diagram to list `strategic  -> StrategicAnalysis  [web research]` between `fact_pack` and `qualify`; add one sentence under the diagram: "Strategic research runs before qualify so the crew prompt carries it (`{strategic_block}`); its result is still attached to `qualitative.strategic_analysis` after qualify."

`CHANGELOG.md`, under `## [Unreleased]`:

```markdown
### Changed

- Deep-analysis prompt revalidated. The task sends its schema once, as a
  strict `json_schema` response format (`Task(response_model=...)`), instead
  of also appending the 9 kB schema text and CrewAI's converter boilerplate
  to every prompt. Every model-filled field in the qualitative, strategic,
  fact-pack and news schemas now carries a French description with a length
  target. `tasks.yaml` keeps static rules first and frames the task per asset
  class (`{asset_focus}`). Strategic research (SWOT/Porter) runs before the
  crew and is rendered into its prompt (`{strategic_block}`); the research
  prompts carry the fact pack as verified facts. See ADR-013.

### Fixed

- `_FactPackRaw` accepts a null `leadership` / `corporate_structure` (mapped
  to the placeholder) instead of failing validation and retrying.
- The JSON-repair monkeypatch repairs only registered crew schemas; research
  models no longer log "JSON repair failed".
- Log labels: "Web research initiated/completed" replace the Perplexity
  wording; the 1 000 ms Sonar baseline warning is gone.

### Removed

- `get_configured_llm(force_json_object=...)`: the extra_body `json_object`
  override never reached the request.
```

(merge into the existing `### Changed` / add the other headings in Keep-a-Changelog order: Added, Changed, Fixed, Removed).

- [ ] **Step 5: Run the gates**

Run: `uv run pytest tests/unit/scripts/test_prose_lengths.py -q -p no:randomly && make check && uv run mypy src/finwiz && uvx vulture src/finwiz --min-confidence 80`
Expected: all green (`make check` includes markdownlint on `docs/` and the MkDocs build; the `docs` dependency group must be installed: `uv sync --group docs`).

- [ ] **Step 6: Commit**

```bash
rtk git add docs/adr/ADR-013-schema-as-prompt-and-strategic-first-qualify.md scripts/prose_lengths.py tests/unit/scripts src/finwiz/crews/CLAUDE.md src/finwiz/analysis/CLAUDE.md CHANGELOG.md
rtk git commit -m "docs: ADR-013, prompt-layout rules, changelog and a prose-length script for the prompt revalidation"
```

- [ ] **Step 7: Verification runs (controller, not the implementer)**

Before the PR, on the branch:

```bash
PORTFOLIO_STOCK_CSV=<mini>/stock.csv PORTFOLIO_ETF_CSV=<mini>/etf.csv PORTFOLIO_CRYPTO_CSV=<mini>/crypto.csv uv run kickoff
uv run python scripts/prose_lengths.py output
```

Record in the PR body: gate verdict, `run_summary.json` crew cost and prompt
tokens against the same three-CSV run on `main` (`c5900774` or later), the
prose medians (thesis 150-250, cases 80-120 expected), and one log line
showing `asset_focus` and the strategic block interpolated (search the log for
"RECHERCHE STRATÉGIQUE").
