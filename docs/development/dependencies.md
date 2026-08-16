# Dependency Policy

FinWiz keeps its dependency surface small on purpose: fewer packages means
fewer upgrades to chase and a smaller supply-chain attack surface.

## Adding a dependency

Before adding a package, in order of preference:

1. Use the Python standard library.
2. Use a capability already provided by an existing dependency.
3. Only then add a new dependency — and justify it in the PR description
   (what it does, why nothing we have covers it, rough transitive weight).

Prefer small, single-purpose, actively-maintained libraries over frameworks
that pull large transitive trees.

## Upgrades

Routine minor/patch drift is **not** chased. Upgrades are driven by the CVE
gate: `osv-scanner` runs in CI via `.github/workflows/security.yml`, which
delegates to the reusable `fjacquet/ci/.github/workflows/python-security.yml@v1.3.0`
workflow (there is no standalone `osv-scanner.yml`), on every PR and fails on
newly-introduced advisories. When it fails, raise the affected floor and
re-lock. Locally, `make audit` (pip-audit) gives a quick equivalent check.

Accepted/unfixable advisories are recorded in `osv-scanner.toml` (read
automatically by osv-scanner) with a written justification, and mirrored to
`make audit` via `--ignore-vuln`; they are reviewed on each dependency change.

## Centralized tools package

Generic CrewAI tools (Yahoo Finance, Perplexity search, ticker validation,
Kraken, AlphaVantage news sentiment, ChartImg, DeFi metrics, the A+
scoring/screening cluster, `ValuationTool`, `ETFAnalysisTool`, etc.) were
migrated out of `src/finwiz/tools/` into the separate
[`crewai-custom-tools`](https://github.com/fjacquet/crewai-custom-tools)
package over a 4-wave migration. FinWiz pins it to a git tag in
`pyproject.toml`:

```toml
"crewai-custom-tools @ git+https://github.com/fjacquet/crewai-custom-tools.git@v0.6.0",
```

Package releases roughly track the migration waves (`v0.4.0` = wave 1,
`v0.5.0` = wave 2, `v0.6.0` = wave 3's analytics/files surface); wave 4 was
a finwiz-side cleanup (dropping now-unused local retry/result shims) with
no corresponding central release. Bump the pinned tag whenever a new
central release is needed, then re-run `uv lock && uv sync`.

### Local co-development

To iterate on `crewai-custom-tools` and FinWiz together, add (do **not**
commit this) to `pyproject.toml`:

```toml
[tool.uv.sources]
crewai-custom-tools = { path = "../crewai_custom_tools", editable = true }
```

then `uv sync`. Remove the override and re-run `uv lock && uv sync` before
committing — the git-tag pin above is the only source of truth that ships.
See `src/finwiz/tools/CLAUDE.md` for the full tool-inventory and import
conventions.

## SBOM

A CycloneDX SBOM is generated in CI and attached to every GitHub Release.
Generate it locally with `make sbom`; scan locally with `make audit`.
