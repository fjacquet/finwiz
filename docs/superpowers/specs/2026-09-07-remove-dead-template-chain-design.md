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

The one subclass, `ScenarioComparisonReportGenerator`, constructs an
`HTMLReportGenerator` but never calls any of those three methods — it renders
through `render_scenario_report_template()`, a separate path.

So both templates are dead, and so are the methods that read them.

### Name collisions to not be confused by

`stress_test_section.html` (dead) shares a name with `generate_stress_test_section()`
in `reporting/sections/analysis.py`, which is live and used by
`python_report_generator.py`. That function builds HTML in Python and never opens
the template. A grep-only pass could easily conflate them.

## Decision

Delete the whole chain in one change: templates, converter, generators, and the
uncalled reader methods.

**Delete:**

- The nine Group A templates, `base_template.html`, and the four Group B
  templates (`demo.html`, `portfolio_configuration.html` — 0 bytes,
  `rebalancing_template.html`, `stress_test_section.html`)
- `html_template.html` and `unified_portfolio_report.html`
- `infrastructure/json/to_html_converter.py` (`JsonToHtmlConverter` and
  `TEMPLATE_MAPPING`, including its broken `feedback_learning_report.html` entry)
- `html_auto_generator.py` (`auto_generate_html` and `auto_generate_html_for_crew`)
- `tests/unit/utils/test_json_to_html_converter.py` — the converter's last
  remaining caller. Keeping it would mean keeping the converter alive to satisfy
  its own test, which is the pattern #187 and #193 were both about.
- On `HTMLReportFormatter` and `HTMLReportGenerator`: `generate_html()`,
  `generate_unified_html()`, `generate_html_fallback()`, `_load_template()`, and
  the two template-path attributes, along with any helper left with no caller
  once they are gone.

**Keep:**

- `HTMLReportGenerator` and `HTMLReportFormatter` as classes —
  `ScenarioComparisonReportGenerator` constructs one, and its live rendering path
  must not be disturbed.
- `crew_reports/base.html` and `crew_reports/deep_analysis_report.html.j2`, live
  and deliberately kept by #187.
- `enriched_analysis_report.html`, live and out of scope.

**Rewrite** `src/finwiz/templates/CLAUDE.md`. Its "Major Entry Points" table
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

Moderate, and concentrated in one place: the reader methods being deleted from
`HTMLReportFormatter` live in a class whose other methods are live. The deletion
must be surgical, and `ScenarioComparisonReportGenerator`'s path must be
exercised after it.

Everything else is leaf deletion of code with no caller, verified both by
present-tense grep and by the history that removed each last reader.
