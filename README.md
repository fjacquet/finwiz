# FinWiz: AI-Powered Financial Analysis Platform

[![CI](https://github.com/fjacquet/finwiz/actions/workflows/quality.yml/badge.svg)](https://github.com/fjacquet/finwiz/actions/workflows/quality.yml)
[![Docs](https://github.com/fjacquet/finwiz/actions/workflows/docs.yml/badge.svg)](https://github.com/fjacquet/finwiz/actions/workflows/docs.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Coverage](https://img.shields.io/badge/coverage-72%25-yellow.svg)](htmlcov/index.html)
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

| Guide | Contents |
|-------|----------|
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Architecture, configuration, testing, workflows |
| [User Guide](docs/USER_GUIDE.md) | Portfolio setup, reading reports, interpreting grades |
| [Tutorials](docs/tutorials/) | Step-by-step walkthroughs for first analysis, discovery, rebalancing |
| [ADRs](docs/adr/) | Architecture Decision Records (ADR-001 through ADR-009) |

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history. Current release: **v0.4.0** (trust spine, honest degradation, discovery always runs).

## License

MIT — see [LICENSE](LICENSE).
