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
