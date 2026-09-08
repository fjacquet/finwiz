# Design: remove the dead Jinja template chain

**Issue:** [#194](https://github.com/fjacquet/finwiz/issues/194)
**Date:** 2026-09-07
**Status:** approved

## Problem

Fourteen Jinja templates outside `src/finwiz/templates/crew_reports/` have no
reachable caller, and one `TEMPLATE_MAPPING` entry points at a file that is not
on disk. The templates are not dead on their own — they are the leaves of a
rendering chain whose root lost its caller in January and was never cleaned up.

Deleting the templates alone would leave the converter pointing at nothing,
which is the mistake this issue exists to document. The chain goes with them.

## Verified current state

A read-only trace confirmed every classification in the issue and found three
things the issue did not account for. Nothing in the trace overturned a
dead/live call.

### The converter chain

`JsonToHtmlConverter` (`infrastructure/json/to_html_converter.py:21`) has exactly
two callers, both in `html_auto_generator.py`: `auto_generate_html` (line 28) and
`auto_generate_html_for_crew` (line 73). Neither has a caller anywhere in `src/`
or `tests/`. No entry point in `pyproject.toml` (`[project.scripts]` holds only
`kickoff`, `run_crew`, `plot`), no Makefile target, no registry, no string
dispatch.

`auto_generate_html`'s last real call site was `store_crew_output()` in the old
`integration/storage.py`, deleted in **5b8279ab** ("remove persistence, storage,
lineage, and unused modules", 2026-01-05, ~17,600 lines). That commit was aimed
at the storage subsystem; `auto_generate_html` was an orphan it left behind, not
a live function someone removed by accident. `auto_generate_html_for_crew` was
born dead in **ebf3d6bc** and never had a caller in this repo's history.

Note for anyone reading the history: `git log -S'auto_generate_html'` also
surfaces **ebc11dd6** (2026-09-07), which deleted a different dead chain — the
`generate_all_crew_html_reports` / `CREW_GENERATORS` registry. That path never
touched `JsonToHtmlConverter`. Same words, different code.

### The two templates the issue could not trace

Both are attributes on two classes — `HTMLReportGenerator`
(`tools/html_report_generator.py:42-43`) and `HTMLReportFormatter`
(`tools/reporting/report_formatters.py:35-36`), where the former delegates to the
latter, so it is one chain.

Both attributes are genuinely read. `html_template.html` is loaded by
`_load_template()` via `Path.read_text()`; `unified_portfolio_report.html` reaches
a real `jinja2.Template(...).render()` in `generate_unified_html()`. The reading
code is correct. It simply has no caller: `generate_html()`,
`generate_unified_html()` and `generate_html_fallback()` are called from nowhere
in `src/` or `tests/` except each other.

So both templates are dead, and so are the methods that read them.

### The island those readers sit on

The initial trace stopped at `ScenarioComparisonReportGenerator`, which
constructs an `HTMLReportGenerator` and renders through
`render_scenario_report_template()`. Following it one step further closes the
loop:

- `HTMLReportFormatter`'s only consumer is `HTMLReportGenerator`
  (`html_report_generator.py:14,45`)
- `HTMLReportGenerator`'s only consumer is `ScenarioComparisonReportGenerator`
  (`scenario_comparison_report_generator.py:15,31`) — its two previous
  consumers, `orchestrators/portfolio_rebalancing.py` and
  `rebalancing_report_generator.py`, are already gone
- `ScenarioComparisonReportGenerator`'s only consumer is
  `tests/unit/tools/test_scenario_comparison_report_generator.py`
- `report_sections.py` (`ReportSectionBuilder`, `ReportSection`) is imported
  only by `html_report_generator.py`

Nothing outside this set imports any of it. It is a closed island whose only
inhabitant is a test, and `src/finwiz/tools/CLAUDE.md:45-62` already says so —
it records the scenario trio as "pre-existing dead code, issue #194", verified
at merge-base 171b8145, and instructs: "When #194 clears the scenario trio,
delete `HTMLReportGenerator` in the same pass — it becomes a true orphan then."

This design honours that instruction. An earlier draft proposed keeping the
classes because the scenario generator constructs one; that reasoning stopped
one link short of the end of the chain.

### Name collisions to not be confused by

`stress_test_section.html` (dead) shares a name with `generate_stress_test_section()`
in `reporting/sections/analysis.py`, which is live and used by
`python_report_generator.py`. That function builds HTML in Python and never opens
the template. A grep-only pass could easily conflate them.

## Decision

Delete the whole chain in one change: templates, converter, generators, and the
dead island the generators sit on.

**Delete:**

- The nine Group A templates, `base_template.html`, and the four Group B
  templates (`demo.html`, `portfolio_configuration.html` — 0 bytes,
  `rebalancing_template.html`, `stress_test_section.html`)
- `html_template.html` and `unified_portfolio_report.html`
- `infrastructure/json/to_html_converter.py` (`JsonToHtmlConverter` and
  `TEMPLATE_MAPPING`, including its broken `feedback_learning_report.html` entry)
- `reporting/html_auto_generator.py` (`auto_generate_html` and
  `auto_generate_html_for_crew`) — note the file lives under `reporting/`, not
  `infrastructure/json/` beside the converter
- `tests/unit/utils/test_json_to_html_converter.py` — the converter's last
  remaining caller. Keeping it would mean keeping the converter alive to satisfy
  its own test, which is the pattern #187 and #193 were both about.
- The whole island, as whole files rather than surgery inside live classes:
  - `tools/scenario_comparison_report_generator.py` (101 lines)
  - `tools/scenario_report_renderer.py` (360)
  - `tools/scenario_report_sections.py` (224)
  - `tools/html_report_generator.py` (188)
  - `tools/reporting/` entire package — `report_formatters.py` (526),
    `report_sections.py` (327), `__init__.py` (15)
  - `tests/unit/tools/test_scenario_comparison_report_generator.py` (258)

**Keep:**

- `crew_reports/base.html` and `crew_reports/deep_analysis_report.html.j2`, live
  and deliberately kept by #187.
- `enriched_analysis_report.html`, live and out of scope.

**Rewrite** `src/finwiz/templates/CLAUDE.md` and update `src/finwiz/tools/CLAUDE.md`
(its lines 45-62 describe the scenario trio and `HTMLReportGenerator` as
deletions pending on #194; once done, those notes and the tree entries go).
On `templates/CLAUDE.md`: Its "Major Entry Points" table
(lines 21-29) lists `portfolio_review.html`, `a_plus_discovery.html`,
`deep_analysis_consolidated.html` and `rebalancing_template.html` as if they were
live, and "Related Modules" (line 90) points at `finwiz.tools.html_report_generator`
as the HTML generation tool. All four templates and that path are being deleted.

## Testing

- `make check` — the deletion must not move it from its current state.
- `make coverage` ≥ 65%. Removing dead-but-covered code (the converter test) can
  move the ratio either way; report the real number.
- A pipeline run must still produce its HTML report. The live path
  (`python_report_generator.py` and `reporting/sections/`) is untouched by this
  change, and the run is the proof.
- `uv run plot` exits 0.

## Risk

Lower than the first draft assumed, because the change became whole-file
deletion rather than surgery inside a live class. The earlier plan — excising
four methods from `HTMLReportFormatter` while leaving its siblings — was the
riskier shape; there are no live siblings.

The risk that remains is scope: this deletes ~2,000 lines across eight files on
top of the template chain. Each file's deletion is justified only by the link
above it in the chain, so the chain must be verified end to end before the first
deletion, not assumed from this document.

Everything else is leaf deletion of code with no caller, verified both by
present-tense grep and by the history that removed each last reader.
