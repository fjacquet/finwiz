# FinWiz Claude Code Skills Overview

This document provides an overview of all Claude Code Skills created for the FinWiz project, converted from the original Kiro steering files.

## Skills Collection

We have **13 specialized Skills** that Claude Code will automatically apply based on your requests:

### Core Development Skills

| Skill | Description | When Claude Uses It |
|-------|-------------|-------------------|
| **finwiz-development** | General development standards, dependency management, version control | Setting up projects, managing dependencies, development workflows |
| **finwiz-testing** | pytest-mock standards, test organization, coverage requirements | Writing tests, mocking, test organization |
| **finwiz-security** | Type safety, API key security, input validation, rate limiting | Security implementations, API integrations |
| **finwiz-refactoring** | File organization, size limits, backward compatibility patterns | Splitting large files, reorganizing code structure |

### FinWiz-Specific Skills

| Skill | Description | When Claude Uses It |
|-------|-------------|-------------------|
| **finwiz-crewai** | CrewAI agents, tasks, flows, performance optimization | CrewAI implementations, agent configuration |
| **finwiz-flow-architecture** | Flow patterns, state management, architectural lessons | Flow design, state management, architecture decisions |
| **finwiz-ai-minimalism** | When to use AI vs Python, cost optimization | Deciding between AI agents and Python code |
| **finwiz-validation** | Pydantic strict mode, schema compliance, data quality | Data validation, schema design, quality standards |

### Financial & Data Skills

| Skill | Description | When Claude Uses It |
|-------|-------------|-------------------|
| **finwiz-financial-libraries** | TA-Lib, Empyrical, Backtrader vs custom code decisions | Financial calculations, technical analysis |
| **finwiz-data-lineage** | Traceability, audit trails, calculation transparency | Financial calculations, regulatory compliance |
| **finwiz-output-standards** | HTML reports, French language, emoji usage, final reporters | Report generation, output formatting |

### Documentation & Integration Skills

| Skill | Description | When Claude Uses It |
|-------|-------------|-------------------|
| **finwiz-documentation** | Diátaxis framework, writing standards, content organization | Writing documentation, organizing content |
| **finwiz-context7** | Automatic library documentation lookup via MCP | Working with external libraries, API integrations |

## How Skills Work

### Automatic Application

Claude Code automatically applies relevant Skills based on your request. You don't need to explicitly call them.

**Example**: If you ask "Help me implement a CrewAI Flow", Claude will automatically apply:
- `finwiz-crewai` (for CrewAI patterns)
- `finwiz-flow-architecture` (for Flow design)
- `finwiz-context7` (to fetch current CrewAI docs)
- `finwiz-validation` (for Pydantic state models)

### Skill Triggers

Each Skill has specific trigger terms in its description that Claude uses to decide when to apply it:

- **"CrewAI", "agents", "tasks", "flows"** → `finwiz-crewai`
- **"testing", "pytest", "mocking"** → `finwiz-testing`
- **"financial calculations", "technical indicators"** → `finwiz-financial-libraries`
- **"refactoring", "splitting files", "large files"** → `finwiz-refactoring`
- **"reports", "HTML", "French output"** → `finwiz-output-standards`

## Conversion from Kiro Steering

These Skills were converted from the original `.kiro/steering/` files:

### Direct Conversions

| Original Steering File | Claude Skill | Status |
|----------------------|--------------|--------|
| `ai-minimalism.md` | `finwiz-ai-minimalism` | ✅ Converted |
| `crewai-standards.md` | `finwiz-crewai` | ✅ Converted |
| `testing-standards.md` | `finwiz-testing` | ✅ Converted |
| `security.md` | `finwiz-security` | ✅ Converted |
| `validation.md` | `finwiz-validation` | ✅ Converted |
| `flow-architecture-lessons.md` | `finwiz-flow-architecture` | ✅ Converted |
| `financial-libraries-strategy.md` | `finwiz-financial-libraries` | ✅ Converted |
| `data-lineage.md` | `finwiz-data-lineage` | ✅ Converted |
| `development-standards.md` | `finwiz-development` | ✅ Converted |
| `context7.md` | `finwiz-context7` | ✅ Converted |
| `documentation-standards.md` | `finwiz-documentation` | ✅ Converted |
| `codebase-refactoring-patterns.md` | `finwiz-refactoring` | ✅ Converted |
| `output-standards.md` | `finwiz-output-standards` | ✅ Converted |

### Remaining Steering Files

These files could be converted to additional Skills if needed:

- `backtrader-standards.md` → Could become `finwiz-backtesting`
- `talib-standards.md` → Could become `finwiz-technical-analysis`
- `empyrical-standards.md` → Could become `finwiz-risk-metrics`
- `library-standards.md` → Could become `finwiz-library-usage`
- `mcp-best-practices.md` → Could become `finwiz-mcp`

## Usage Examples

### Checking Available Skills

Ask Claude: "What Skills are available?" to see all loaded Skills.

### Testing Specific Skills

- **CrewAI**: "Help me create a CrewAI Flow with state management"
- **Testing**: "Write unit tests for this financial calculation"
- **Refactoring**: "This file is 400 lines, help me split it"
- **Output**: "Generate an HTML report in French for this analysis"

## Benefits

### For Developers

- **Automatic guidance** - No need to remember all standards
- **Consistent patterns** - Skills ensure consistent code across the project
- **Current practices** - Skills reflect latest FinWiz patterns and lessons learned

### For the Project

- **Knowledge preservation** - Critical patterns captured in Skills
- **Onboarding** - New developers get guidance automatically
- **Quality assurance** - Standards applied consistently

## Maintenance

### Updating Skills

To update a Skill:
1. Edit the `SKILL.md` file directly
2. Exit and restart Claude Code for changes to take effect

### Adding New Skills

To add new Skills:
1. Create new directory in `.claude/skills/`
2. Add `SKILL.md` file with proper frontmatter
3. Restart Claude Code

### Skill Quality

Each Skill follows the official Claude Code Skill standards:
- Clear, specific descriptions for automatic triggering
- Actionable guidance with examples
- Proper YAML frontmatter with required fields
- Focused scope without overlap

## Next Steps

1. **Test the Skills** by asking Claude to perform tasks that should trigger them
2. **Refine descriptions** if Skills aren't triggering as expected
3. **Add more Skills** from remaining steering files if needed
4. **Update Skills** as FinWiz patterns evolve

---

**Created**: 2025-12-01  
**Skills Count**: 13  
**Coverage**: Core development, FinWiz-specific, financial, documentation, and integration patterns