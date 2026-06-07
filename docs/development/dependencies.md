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
gate: `osv-scanner` runs in CI (`.github/workflows/osv-scanner.yml`) on every
PR and fails on newly-introduced advisories. When it fails, raise the affected
floor and re-lock. Locally, `make audit` (pip-audit) gives a quick equivalent
check.

Accepted/unfixable advisories are recorded in `osv-scanner.toml` (read
automatically by osv-scanner) with a written justification, and mirrored to
`make audit` via `--ignore-vuln`; they are reviewed on each dependency change.

## SBOM

A CycloneDX SBOM is generated in CI and attached to every GitHub Release.
Generate it locally with `make sbom`; scan locally with `make audit`.
