# CLAUDE.md

Guidance for Claude Code. Use `/skill-name` for detailed standards.

## Quick Reference

```bash
# Essential commands
crewai flow kickoff                    # Run full portfolio analysis
uv sync                                # Install dependencies
make test                              # Unit tests only
make check                             # All quality checks

# Single test
uv run pytest tests/path/test.py::test_name -v -s

# Code quality
make lint && make format               # Fix linting and formatting
make mypy                              # Type checking
```

## Project Overview

FinWiz is an AI-powered financial analysis platform built with CrewAI for stocks, ETFs, crypto, and portfolios. Uses Python scoring engine (not AI) for 100% cost reduction.

## Architecture

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| Domain | `schemas/`, `scoring/` | Business logic, Pydantic models |
| Application | `orchestrators/`, `flows/` | Workflow orchestration |
| Infrastructure | `data/`, `cache/` | External APIs, databases |
| Presentation | `reporting/`, `templates/` | HTML, CLI |

**Dependency**: `Presentation → Application → Domain ← Infrastructure`

## Key Entry Points

| Purpose | Location |
|---------|----------|
| Flow orchestration | `src/finwiz/flows/hybrid_analysis_flow.py` |
| Crew factory | `src/finwiz/crew_factory.py` |
| Tool factories | `src/finwiz/tools/tool_factories.py` |
| Schemas | `src/finwiz/schemas/` |
| Scoring engine | `src/finwiz/scoring/deep_analysis_scorer.py` |

## Critical Rules

- **unittest.mock BANNED** - Use pytest-mock only (`mocker.patch()`)
- **json.dumps** - Always use `default=str`
- **File size** - Max 300 lines, split if larger
- **Pydantic models** - Put in `schemas/`, not domain folders
- **Final reporters** - Must have empty tools list
- **Flow methods** - Must return `dict[str, Any]`
- **self.inputs** - NEVER use (deprecated), use `self.state`

## Available Skills

Use `/skill-name` for detailed standards:

| Skill | Purpose |
|-------|---------|
| `/finwiz-crewai` | CrewAI agents, tasks, crews, flows |
| `/finwiz-testing` | pytest-mock patterns, test structure |
| `/finwiz-ai-minimalism` | Python vs AI decision framework |
| `/finwiz-flow-architecture` | Flow patterns and state management |
| `/finwiz-validation` | Pydantic strict mode, schemas |
| `/finwiz-output-standards` | HTML reports, French language |
| `/finwiz-financial-libraries` | TA-Lib, Backtrader, QuantLib |
| `/finwiz-refactoring` | File splitting, backward compat |
| `/finwiz-security` | API keys, input validation |
| `/finwiz-development` | Dependencies, code quality |
| `/finwiz-documentation` | Diátaxis framework |
| `/finwiz-context7` | Up-to-date library docs via MCP |

## Environment Variables

```bash
OPENAI_API_KEY=your_key      # Required
SERPER_API_KEY=your_key      # Required
```
