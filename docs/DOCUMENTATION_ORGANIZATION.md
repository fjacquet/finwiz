---
layout: default
title: Documentation Organization
---

# Documentation Organization Guide

This guide explains how documentation is organized in FinWiz and where to place new documentation.

## Directory Structure

```
docs/
├── index.md                              # Homepage (navigation hub)
├── README.md                             # Project overview
├── USER_GUIDE.md                         # Complete user guide
├── DEVELOPER_GUIDE.md                    # Complete developer guide
├── QUICK_REFERENCE.md                    # Quick reference card
├── GITHUB_PAGES_SETUP.md                 # GitHub Pages setup
├── REQUIREMENTS.md                       # Requirements documentation
├── DOCUMENTATION_ENHANCEMENT_SUMMARY.md  # Documentation history
│
├── tutorials/                            # Learning-oriented guides
│   ├── index.md                         # Tutorial navigation
│   ├── getting_started.md               # First-time setup
│   ├── first_analysis.md                # Running first analysis
│   └── portfolio_analysis.md            # Portfolio workflows
│
├── how-to/                               # Problem-solving guides
│   ├── index.md                         # How-to navigation
│   ├── setup_environment.md             # Environment setup
│   ├── BATCH_PROCESSING.md              # Batch processing guide
│   ├── PYTHON_SCORING_ENGINE.md         # Scoring engine guide
│   ├── deployment-guide.md              # Deployment instructions
│   └── troubleshooting.md               # Common issues
│
├── reference/                            # Technical reference
│   ├── index.md                         # Reference navigation
│   ├── api/                             # API documentation
│   ├── schemas/                         # Schema documentation
│   ├── cli_commands.md                  # CLI reference
│   └── environment_variables.md         # Configuration reference
│
└── explanations/                         # Understanding-oriented
    ├── index.md                         # Explanation navigation
    ├── ARCHITECTURE.md                  # System architecture
    ├── design_principles.md             # Design philosophy
    ├── ai_architecture.md               # AI framework
    └── flow_architecture.md             # CrewAI Flow design
```

## Diátaxis Framework

FinWiz documentation follows the [Diátaxis framework](https://diataxis.fr/), which organizes documentation by purpose:

### 📚 Tutorials (Learning-Oriented)

**Purpose**: Help users learn by doing

**Characteristics**:

- Step-by-step lessons
- Assumes no prior knowledge
- Focus on getting started successfully
- Learning-oriented, not goal-oriented

**Location**: `docs/tutorials/`

**Examples**:

- Getting started guide
- First portfolio analysis
- Building custom workflows

**When to Add**:

- Onboarding new users
- Teaching new features
- Demonstrating workflows

### 🛠️ How-To Guides (Problem-Solving)

**Purpose**: Guide users to solve specific problems

**Characteristics**:

- Practical, goal-oriented
- Assumes some knowledge
- Focus on accomplishing tasks
- Step-by-step instructions

**Location**: `docs/how-to/`

**Examples**:

- Setting up batch processing
- Configuring Python scoring engine
- Deploying to production
- Troubleshooting issues

**When to Add**:

- Solving common problems
- Configuring specific features
- Optimizing performance
- Deployment scenarios

### 📖 Reference (Information-Oriented)

**Purpose**: Provide accurate technical information

**Characteristics**:

- Technical descriptions
- Comprehensive and accurate
- Organized for lookup
- No explanations or tutorials

**Location**: `docs/reference/`

**Examples**:

- API documentation
- CLI command reference
- Environment variables
- Schema definitions

**When to Add**:

- Documenting APIs
- Listing configuration options
- Defining data structures
- Command-line interfaces

### 💡 Explanations (Understanding-Oriented)

**Purpose**: Clarify and illuminate topics

**Characteristics**:

- Conceptual discussions
- Background and context
- Design decisions and trade-offs
- Understanding "why"

**Location**: `docs/explanations/`

**Examples**:

- System architecture
- Design principles
- AI minimalism philosophy
- Flow architecture patterns

**When to Add**:

- Explaining architecture
- Discussing design decisions
- Providing context
- Exploring concepts

## File Naming Conventions

### General Rules

1. **Use lowercase with hyphens**: `portfolio-analysis.md`
2. **Exception for guides**: `USER_GUIDE.md`, `DEVELOPER_GUIDE.md` (all caps)
3. **Descriptive names**: `batch-processing.md` not `bp.md`
4. **No dates in names**: Use git history for versioning

### Specific Patterns

**Tutorials**:

- `getting-started.md`
- `first-[feature].md`
- `[workflow]-tutorial.md`

**How-To Guides**:

- `setup-[feature].md`
- `configure-[feature].md`
- `troubleshoot-[feature].md`
- `deploy-to-[platform].md`

**Reference**:

- `[feature]-api.md`
- `[component]-schema.md`
- `cli-commands.md`
- `environment-variables.md`

**Explanations**:

- `[concept]-architecture.md`
- `[topic]-principles.md`
- `[system]-design.md`

## Front Matter

All documentation files must include YAML front matter:

```yaml
---
layout: default
title: Page Title
nav_order: 1  # Optional, for ordering
---
```

### Required Fields

- `layout`: Always `default` for GitHub Pages
- `title`: Human-readable page title

### Optional Fields

- `nav_order`: Number for ordering in navigation
- `parent`: Parent page for hierarchical navigation
- `has_children`: Boolean for pages with children

## Where to Place New Documentation

### Decision Tree

```
Is it teaching a beginner?
├─ YES → tutorials/
└─ NO
   └─ Is it solving a specific problem?
      ├─ YES → how-to/
      └─ NO
         └─ Is it technical reference?
            ├─ YES → reference/
            └─ NO → explanations/
```

### Examples

**"How do I analyze my first portfolio?"**
→ Tutorial (`tutorials/first-portfolio-analysis.md`)

**"How do I configure batch processing?"**
→ How-To (`how-to/configure-batch-processing.md`)

**"What are all the CLI commands?"**
→ Reference (`reference/cli-commands.md`)

**"Why does FinWiz use AI minimalism?"**
→ Explanation (`explanations/ai-minimalism-philosophy.md`)

## Documentation Root (`docs/`)

### Allowed Files (Whitelist)

Only these files are allowed in `docs/` root:

1. `index.md` - Homepage/navigation hub
2. `README.md` - Project overview
3. `USER_GUIDE.md` - Complete user guide
4. `DEVELOPER_GUIDE.md` - Complete developer guide
5. `QUICK_REFERENCE.md` - Quick reference card
6. `GITHUB_PAGES_SETUP.md` - Setup instructions
7. `REQUIREMENTS.md` - Requirements specification
8. `DOCUMENTATION_ENHANCEMENT_SUMMARY.md` - Documentation history

### Enforcement

The `.gitignore` file enforces this whitelist:

```gitignore
# Prevent docs/ root clutter - only allow essential files
docs/*
!docs/index.md
!docs/README.md
!docs/USER_GUIDE.md
!docs/DEVELOPER_GUIDE.md
!docs/QUICK_REFERENCE.md
!docs/GITHUB_PAGES_SETUP.md
!docs/REQUIREMENTS.md
!docs/DOCUMENTATION_ENHANCEMENT_SUMMARY.md
!docs/tutorials/
!docs/how-to/
!docs/reference/
!docs/explanations/
```

### Why This Restriction?

- **Clarity**: Easy to find essential guides
- **Organization**: Forces proper categorization
- **Navigation**: Prevents overwhelming root directory
- **Maintainability**: Clear structure for contributors

## Adding New Documentation

### Step 1: Determine Category

Use the decision tree above to determine the correct category.

### Step 2: Create File

```bash
# Create file in appropriate directory
touch docs/tutorials/my-tutorial.md
touch docs/how-to/my-guide.md
touch docs/reference/my-api.md
touch docs/explanations/my-concept.md
```

### Step 3: Add Front Matter

```yaml
---
layout: default
title: My Page Title
---

# Content starts here
```

### Step 4: Update Navigation

Add link to appropriate index file:

- `docs/tutorials/index.md`
- `docs/how-to/index.md`
- `docs/reference/index.md`
- `docs/explanations/index.md`

### Step 5: Cross-Reference

Link from related documentation:

```markdown
See also:
- [Related Tutorial](../tutorials/related.md)
- [API Reference](../reference/api.md)
```

## Avoiding Common Mistakes

### ❌ Don't Place Files in docs/ Root

```bash
# WRONG
docs/deployment-guide.md

# CORRECT
docs/how-to/deployment-guide.md
```

### ❌ Don't Mix Documentation Types

```bash
# WRONG - Tutorial in how-to/
docs/how-to/getting-started-tutorial.md

# CORRECT
docs/tutorials/getting-started.md
```

### ❌ Don't Create Deep Hierarchies

```bash
# WRONG - Too deep
docs/tutorials/portfolio/analysis/advanced/strategies.md

# CORRECT - Flat structure
docs/tutorials/advanced-portfolio-strategies.md
```

### ❌ Don't Use Unclear Names

```bash
# WRONG
docs/how-to/guide1.md
docs/explanations/arch.md

# CORRECT
docs/how-to/batch-processing-guide.md
docs/explanations/system-architecture.md
```

## Documentation Quality Standards

### Writing Style

1. **Clear and Concise**: Use simple language
2. **Active Voice**: "Configure the system" not "The system should be configured"
3. **Present Tense**: "The system validates" not "The system will validate"
4. **Second Person**: "You can configure" not "Users can configure"

### Code Examples

1. **Complete**: Include all necessary imports
2. **Runnable**: Test before committing
3. **Commented**: Explain non-obvious code
4. **Formatted**: Use proper syntax highlighting

```python
# ✅ GOOD - Complete, runnable, commented
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

# Initialize the scorer
scorer = DeepAnalysisScorer()

# Calculate score with example data
result = scorer.calculate_composite_score(
    ticker="AAPL",
    asset_class="stock",
    data={"roe": 0.25, "debt_to_equity": 0.3}
)
```

### Links

1. **Relative Links**: Use `../` for cross-references
2. **Descriptive Text**: "See the [User Guide](USER_GUIDE.md)" not "Click [here](USER_GUIDE.md)"
3. **Verify Links**: Ensure targets exist

### Structure

1. **Hierarchical Headers**: Use H2, H3, H4 appropriately
2. **Table of Contents**: Add for long documents
3. **Sections**: Break into logical sections
4. **Lists**: Use for enumerations

## Maintenance

### Regular Reviews

- **Quarterly**: Review for accuracy
- **After Features**: Update related documentation
- **On User Feedback**: Address confusion points

### Deprecation

When deprecating documentation:

1. Add deprecation notice at top
2. Link to replacement documentation
3. Keep for 2 releases minimum
4. Then move to `docs/archive/`

### Archive Structure

```
docs/archive/
├── deprecated/
│   └── old-feature-guide.md
└── historical/
    └── migration-notes-v1-to-v2.md
```

## Tools and Commands

### Preview Documentation

```bash
make docs-serve
```

### Validate Documentation

```bash
make docs-validate
```

### Lint Markdown

```bash
make docs-lint
```

### Clean Build Artifacts

```bash
make docs-clean
```

## Getting Help

- **Documentation Specialist**: Tag issues with `documentation`
- **Style Guide**: See `DEVELOPER_GUIDE.md`
- **Diátaxis**: <https://diataxis.fr/>

## Summary

**Key Points**:

- Follow Diátaxis framework (tutorials, how-to, reference, explanations)
- Keep `docs/` root clean (only essential files)
- Use proper front matter on all pages
- Cross-reference related documentation
- Write clear, actionable content
- Test all code examples

**Before Committing**:

- [ ] Placed in correct directory
- [ ] Added front matter
- [ ] Updated navigation
- [ ] Added cross-references
- [ ] Tested code examples
- [ ] Ran `make docs-validate`

Following this organization keeps documentation maintainable, discoverable, and useful for all users.
