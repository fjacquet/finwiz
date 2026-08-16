# FinWiz: AI-Powered Financial Analysis Platform

[![CI](https://github.com/fjacquet/finwiz/actions/workflows/ci.yml/badge.svg)](https://github.com/fjacquet/finwiz/actions/workflows/ci.yml)
[![Docs](https://github.com/fjacquet/finwiz/actions/workflows/docs.yml/badge.svg)](https://github.com/fjacquet/finwiz/actions/workflows/docs.yml)
[![Security](https://github.com/fjacquet/finwiz/actions/workflows/security.yml/badge.svg)](https://github.com/fjacquet/finwiz/actions/workflows/security.yml)
[![Release](https://img.shields.io/github/v/release/fjacquet/finwiz?sort=semver)](https://github.com/fjacquet/finwiz/releases/latest)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Coverage](https://img.shields.io/badge/coverage-77%25%20(gate%2065%25)-brightgreen.svg)](https://github.com/fjacquet/finwiz/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-success)](https://pre-commit.com/)

FinWiz analyzes portfolios of stocks, ETFs, and crypto using a hybrid approach: deterministic Python scoring ($0, <100ms) for quantitative analysis and CrewAI crews for qualitative insights only. Each holding is graded A+ to F with a composite score (40% fundamental, 30% technical, 30% risk) and an honest trust banner that shows exactly how much of the analysis succeeded.

## Quick Start

```bash
# Install
git clone https://github.com/fjacquet/finwiz.git && cd finwiz
uv sync

# Configure
cp .env.example .env   # add OPENAI_API_KEY and SERPER_API_KEY at minimum

# Run a full portfolio analysis
crewai flow kickoff
```

Reports are written to `output/` as styled HTML files, one per phase.

## Documentation

**For users / operators** — running FinWiz on your portfolio:

- [Getting Started](docs/tutorials/getting_started.md) — setup, configuration, and your first analysis
- [Operations Guide](docs/how-to/OPERATIONS_GUIDE.md) — deployment, operations, migration, troubleshooting
- [Tutorials](docs/tutorials/) — step-by-step: [first analysis](docs/tutorials/first_analysis.md), [portfolio analysis](docs/tutorials/portfolio_analysis.md)
- [How-to guides](docs/how-to/) — focused recipes (API keys, deployment, batch processing)
- [Reference](docs/reference/) — env vars, CLI flags, schema definitions
- [CHANGELOG](CHANGELOG.md) — version history (current: **v5.3.0** — tactical price targets & sell-level floors per holding (ADR-011))

**For contributors / extenders** — modifying FinWiz:

- [Developer Guide](docs/development/DEVELOPER_GUIDE.md) — architecture, code organization, core patterns, custom crews, testing, performance, deployment, contributing
- [Architecture Decision Records](docs/adr/) — ADR-001 through ADR-010 (latest: [ADR-010 Fact Pack — Grounded Qualitative](docs/adr/ADR-010-fact-pack-grounded-qualitative.md))
- [PRD](docs/PRD.md) — product requirements and scope boundaries
- [CLAUDE.md](CLAUDE.md) — Claude Code conventions, MCP usage, coding standards

## License

MIT — see [LICENSE](LICENSE).
