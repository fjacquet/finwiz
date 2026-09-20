# Design: LLM prompt revalidation (deep-analysis crew and research prompts)

**Date:** 2026-09-20
**Status:** approved in chat, spec under review
**Path:** architectural (schema-as-prompt rewrite, crew wiring change, one
stage reorder in the per-holding pipeline)

## Problem

A probe of the deep-analysis crew's outbound request (captured before send,
2026-09-20, `google/gemini-3.8-flash` via OpenRouter) shows what the model
receives per holding:

| Part | Size | Origin |
|---|---|---|
| system message | 189 chars | agent role/goal/backstory |
| task description | ~3 700 chars static + holding data | `crews/deep_analysis/config/tasks.yaml` |
| appended JSON schema, pretty-printed | 9 003 chars, 39 field descriptions | CrewAI `build_task_prompt_with_schema` because the task uses `output_pydantic` |
| appended boilerplate | "IMPORTANT: Preserve the original content exactly as-is. Do NOT rewrite… Only structure it to match the schema format." | CrewAI converter text, same source |
| `response_format` | `json_schema`, `strict: true`, same schema | CrewAI native OpenRouter provider |

Consequences:

- About 2 500 prompt tokens per call are a duplicate of the schema already sent
  as `response_format`, placed after the per-holding data, so never cached.
- The boilerplate tells the model to restructure existing content, the wrong
  frame for a generation task.
- `force_json_object` in `config/llm/llm_config.py` (extra_body
  `response_format: json_object`) never reaches the request: the probe shows
  `json_schema` only. It is dead.
- The 39 field descriptions in `schemas/hybrid_analysis/qualitative.py` are the
  model's field-level instructions, and they are generic English
  ("Comprehensive business model analysis").
- The crew runs before SWOT/Porter (`analysis/stages/__init__.py`), so the
  web-grounded strategic research never informs the crew, and the strategic
  prompts see only the yfinance description, not the fact pack.
- `tasks.yaml` defects: `analysis_timestamp` is both forbidden and required;
  "SEC Insights" is asked of ETFs and crypto; `strategic_analysis` is not listed
  as Python-owned; word budgets are not met (thesis median 173 words for
  "200+", bull/base/bear ~60 for "100+" on the 2026-09-20 67-holding run).
- The 2026-09-20 run log shows `_FactPackRaw` rejecting `null` for
  `leadership` / `corporate_structure` (8 validation failures, retries), a
  global `model_validate_json` monkeypatch logging repair failures for research
  models, and stale log lines ("agent has PerplexitySearchTool", "Perplexity
  search completed") that no longer describe what runs.

Goal chosen in the brainstorm: output quality and faithfulness first; cost may
not rise. Scope: deep-analysis crew prompts and the research prompts.

## Design

### 1. Crew wiring: schema once, as `response_format`

`crews/deep_analysis/deep_analysis.py`, `deep_qualitative_analysis_task`:

- `Task(config=..., response_model=self.QualitativeInsightsRaw)` replaces
  `output_pydantic=`. CrewAI's guard (`agent/utils.py`
  `build_task_prompt_with_schema`: only when `output_pydantic` and not
  `response_model`) then appends nothing to the prompt, while
  `agent/core.py` still passes the model as `response_format` json_schema strict.
- Result extraction is unchanged: `stages/qualify.py` `_extract_qualitative`
  already falls through to `json.loads(crew_result.raw)` and
  `_QualitativeInsightsRaw.model_validate`, which is the path taken when the
  `pydantic` slot is empty.
- `get_configured_llm(force_json_object=...)` and its extra_body branch are
  deleted, with `tests/unit/config/test_llm_config_json_mode.py`. Proof of
  death: the probe above and the new test in §7.
- The log line "MINIMAL-TOOL MODE: agent has PerplexitySearchTool" in
  `deep_analysis.py` becomes "No tools: prompt + fact pack + strategic block
  only".

### 2. Schemas are prompts: field descriptions rewritten

Every field the model fills gets a French, one-sentence description that says
what to write, for which asset class, and how long. Field names do not change
(report sections and tests read them).

`schemas/hybrid_analysis/qualitative.py` (the nested classes reused by
`_QualitativeInsightsRaw`):

| Field | Description (French, final wording in the plan) |
|---|---|
| `sec_insights.business_model` | Modèle économique en 120-180 mots : comment le holding gagne de l'argent (action), stratégie de réplication et exposition (fonds), utilité et économie du protocole (crypto). |
| `sec_insights.competitive_advantages` | 3 à 5 avantages durables, chacun une phrase avec la preuve issue du FACT PACK ou de la recherche stratégique. |
| `sec_insights.risk_factors` | 3 à 5 risques propres au holding, chacun avec sa gravité (faible/moyenne/élevée). |
| `sec_insights.strategic_initiatives` | 2 à 4 initiatives en cours datées des 12 derniers mois, avec l'effet attendu. |
| `fundamental_context.industry_analysis` | Secteur et tendances en 80-120 mots, cohérents avec la DATE D'ANALYSE. |
| `fundamental_context.growth_drivers` | 3 à 5 moteurs de croissance, un par ligne, sans recopier les métriques Python. |
| `fundamental_context.competitive_positioning` | Position concurrentielle en 60-100 mots, appuyée sur la recherche stratégique (Porter). |
| `fundamental_context.management_assessment` | Direction et gouvernance (action), émetteur et gestion (fonds), équipe et gouvernance du protocole (crypto), 40-80 mots, uniquement des faits du FACT PACK. |
| `technical_strategy.chart_patterns` | 1 à 3 configurations lisibles dans les indicateurs fournis; vide si aucune. |
| `technical_strategy.support_resistance` | Niveaux clés déduits des indicateurs fournis, avec la logique. |
| `technical_strategy.entry_exit_strategy` | Plan d'entrée/sortie avec niveaux, 40-80 mots. |
| `technical_strategy.timing_assessment` | Momentum et timing en une ou deux phrases. |
| `contextual_risks.*` (4 lists) | 2 à 4 risques chacun, spécifiques au holding, datés si liés à un événement. |
| `contextual_risks.stress_scenarios` | 2 à 3 scénarios de stress avec l'effet attendu sur le holding. |
| `investment_synthesis.investment_thesis` | Thèse en 150-250 mots qui relie faits, recherche stratégique et scores Python. |
| `investment_synthesis.bull_case` / `base_case` / `bear_case` | 80-120 mots chacun avec les catalyseurs ou risques déclencheurs. |
| `scenario_probabilities` | Probabilités bull/base/bear, somme 1,0. |
| `final_recommendation`, `recommendation_confidence` | Inchangés. |
| `action_plan.*` | 2 à 4 éléments chacun, concrets et vérifiables. |
| `ai_confidence` | Confiance globale 0-1, fondée sur la couverture du FACT PACK et de la recherche stratégique. |

`schemas/hybrid_analysis/strategic.py` (`SwotAnalysis`, `ForceRating`,
`FiveForcesAnalysis`, `PortfolioPostureNarrative`): same treatment. These are
strict-schema calls, so the descriptions are the entire field spec. Caps
already expressed in the prompts (`MAX_BULLETS_SWOT`, `MAX_RATIONALE_CHARS`,
`MAX_PROSE_CHARS`) are repeated in the descriptions so the two never disagree.

`analysis/fact_pack_research.py` `_FactPackRaw`: French descriptions, and the
`mode="before"` validator maps `None` or a non-string `leadership` /
`corporate_structure` to `_PLACEHOLDER` instead of letting validation fail.
`schemas/perplexity.py` `NewsHeadline` / `NewsDigest`: French descriptions.

### 3. `tasks.yaml`: static rules only, asset framing in the dynamic block

Static block (before `---`), in this order, no placeholder:

1. Title, LANGUE.
2. ANTI-HALLUCINATION (unchanged text).
3. AUCUN OUTIL EXTERNE.
4. SOURCES, new: "Le FACT PACK et la RECHERCHE STRATÉGIQUE en fin de prompt
   sont tes sources primaires; le CONTEXT Python est secondaire; ta mémoire
   d'entraînement vient en dernier."
5. CHAMPS PYTHON-CONTRÔLÉS: `fact_pack`, `strategic_analysis`,
   `analysis_timestamp`. The "OUTPUT: analysis_timestamp ISO 8601" line is
   deleted.
6. BUDGET, one paragraph: the word ranges of §2, stated once ("respecte les
   longueurs indiquées par champ; ne remplis pas pour remplir").
7. OUTPUT: JSON valide uniquement, pas de texte hors JSON, pas de virgule
   finale. The "REQUIRED investment_synthesis structure" JSON example is
   deleted: the schema is sent as `response_format`.

Dynamic block (after `---`), in this order:

1. `📅 DATE D'ANALYSE : {current_date} ({current_date_iso}).`
2. `HOLDING : {ticker} ({asset_class})`
3. `{asset_focus}`: one paragraph per asset class, built in
   `analysis/_helpers._build_crew_inputs`:
   - stock: "Analyse une action : modèle économique, avantages concurrentiels,
     direction, initiatives des 12 derniers mois, risques réglementaires et
     opérationnels."
   - etf: "Analyse un fonds indiciel : émetteur, indice suivi, réplication,
     frais, concentration sectorielle et géographique, liquidité, risques de
     contrepartie. Ne décris pas un émetteur comme une entreprise à analyser."
   - crypto: "Analyse un actif crypto : protocole, utilité, offre et émission,
     activité des développeurs, gouvernance, garde et réglementation par
     juridiction."
4. `{fact_pack_block}` with the existing AUTORITAIRE paragraph.
5. `{strategic_block}` (§4).
6. CONTEXT (Python-calculated) lines, unchanged.
7. `{retry_guidance}`.

Two placeholders are added (`asset_focus`, `strategic_block`); the layout test
already checks every placeholder name against `_build_crew_inputs`.

### 4. Strategic research before the crew, rendered into the prompt

`analysis/stages/__init__.py`: `_safe_strategic(...)` runs right after the
fact-pack stage and before `qualify(...)`; its result is stored in
`stage_ctx.extras["strategic"]`. After qualify, the existing
`qual.model_copy(update={"strategic_analysis": strategic})` stays. Failure
semantics unchanged: strategic `None` is non-fatal.

`stages/qualify.py`: `_build_crew_inputs(ctx, quant, raw_data,
fact_pack=fact_pack, strategic=stage_ctx.extras.get("strategic"))`.

New module `analysis/strategic_render.py`, `to_prompt_block(strategic:
StrategicAnalysis | None, current_date: str) -> str`, one renderer like
`fact_pack/render.py`:

```text
🧭 RECHERCHE STRATÉGIQUE (web, au {current_date}, score SWOT {s:.2f}, moat {m:.2f})
SWOT
- Forces : … | … | …
- Faiblesses : …
- Opportunités : …
- Menaces : …
- Synthèse : {strategic_assessment}
Porter
- Nouveaux entrants : HIGH — {rationale ≤ 160 chars}
- Fournisseurs : …
- Clients : …
- Substituts : …
- Rivalité : …
- Position : {competitive_position_summary}
```

Bullets are capped at `MAX_BULLETS_SWOT` each and the whole block at 2 000
characters; a missing SWOT or Porter renders "non disponible" on its line;
`None` renders one line "Recherche stratégique non disponible." Estimated 500
to 700 tokens, less than the 2 500 removed in §1.

`strategic_research.py`: `gather_strategic_analysis` and `_sync` take
`facts: str = ""`. `_swot_prompt` and `_porter_prompt` insert, when non-empty:

```text
Faits vérifiés (sources structurées, à ne pas contredire; la recherche web
complète, elle ne remplace pas) :
{facts}
```

`stages/__init__.py` passes `facts=to_prompt_block(fact_pack)[:1500]`. The
posture, gap-fill and news prompts are unchanged.

### 5. Log and patch hygiene (same branch, small)

- `infrastructure/json/crewai_json_patch.py`: the patched
  `model_validate_json` repairs only classes registered through a new
  `register_repairable(cls)`; the crew registers `_QualitativeInsightsRaw` at
  init. Every other class goes straight to the original method, so research
  models stop producing "JSON repair failed" errors.
- `tools/perplexity_logging.py`: messages become "Web research initiated" /
  "Web research completed".
- `tools/perplexity_performance.py`: the 1 000 ms Sonar baseline warning is
  deleted (it fires on every OpenRouter call); the timing log stays.

### 6. Cost and cache

Per holding: about 2 500 prompt tokens removed (§1), 500 to 700 added (§4),
output budgets unchanged in tokens. The static prefix grows (SOURCES, BUDGET)
and stays first, so the layout test threshold is re-measured, not lowered.

### 7. Testing

Unit, pytest-mock only:

- `tests/unit/crews/test_deep_analysis_crew.py`: the task has `response_model`
  set and `output_pydantic` `None`; `crewai.agent.utils.build_task_prompt_with_schema(task, "x")`
  returns `"x"` unchanged.
- `test_deep_analysis_prompt_layout.py`: threshold re-measured; placeholder
  set includes `asset_focus` and `strategic_block`; the description contains
  no `analysis_timestamp` requirement and no literal `"investment_synthesis": {`.
- `tests/unit/analysis/test_helpers.py`: `asset_focus` per asset class;
  `strategic_block` present, and the "non disponible" line when `strategic`
  is `None`.
- `tests/unit/analysis/test_strategic_render.py` (new): caps, missing SWOT or
  Porter, `None`.
- `tests/unit/analysis/stages/test_pipeline.py`: strategic research is invoked
  before the crew (call order recorded through mocks) and its result reaches
  `_build_crew_inputs`; strategic failure still yields a qualitative result.
- `tests/unit/analysis/test_strategic_asset_classes.py`: `facts` appears in the
  SWOT and Porter prompts when given, absent otherwise.
- `tests/unit/analysis/test_fact_pack_research.py` (or existing file):
  `leadership=None` and `corporate_structure=None` validate to the placeholder.
- `tests/unit/config/test_llm_config_json_mode.py` deleted;
  `test_llm_config_reasoning_effort.py` and `test_deep_analysis_crew.py` lose their `force_json_object` cases.
- `tests/unit/infrastructure/test_crewai_json_patch.py`: unregistered class
  bypasses repair; registered class still repaired.
- Schema descriptions: one test asserting every field description in the four
  schema modules is non-empty and contains no English filler words from a
  short list ("Comprehensive", "Key", "List of").

Verification runs:

1. `make check`, `uv run mypy src/finwiz`, `uvx vulture src/finwiz --min-confidence 80`.
2. Three-CSV run on `main` before the change and on the branch after: compare
   in `output/run_summary.json` the crew prompt tokens and cost, the gate
   verdict, and the prose word medians per field (script from the brainstorm,
   kept under `scripts/` as `prose_lengths.py`). Expect fewer prompt tokens,
   thesis and cases inside their ranges, `asset_focus` visible in the log.
3. One full 67-holding run by the user after merge; the PR records the
   three-CSV numbers.

### 8. Documentation, same branch

- `docs/adr/ADR-013-schema-as-prompt-and-strategic-first-qualify.md`.
- `src/finwiz/crews/CLAUDE.md`: prompt layout section updated (placeholder
  list, "this task uses `response_model`, never `output_pydantic`", field
  descriptions are prompt text).
- `src/finwiz/analysis/CLAUDE.md`: stage order (fact pack, strategic, qualify).
- `CHANGELOG.md` Unreleased: Changed (prompt and schema rewrite, stage order),
  Fixed (`_FactPackRaw` null fields, JSON-patch scope, log labels), Removed
  (`force_json_object`).

## Out of scope

- Report rendering changes and citation fields on SWOT/Porter.
- Backtesting `IndexError` and the stale discovery-universe crypto tickers seen
  in the same run log.
- The TGT MAXIMUM_SPEED fallback observed on 2026-09-20 (1 of 67), to be
  investigated separately from its own run log.
- Changing models, temperatures or `max_tokens`.
