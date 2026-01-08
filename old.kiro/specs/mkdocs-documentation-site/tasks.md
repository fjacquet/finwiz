---
inclusion: fileMatch
fileMatchPattern: ['docs/**/*.md', 'mkdocs.yml', '.github/workflows/*docs*', 'scripts/*docs*']
---

# MkDocs Documentation Standards

## Core Architecture

**Platform**: MkDocs with Material theme, deployed via GitHub Pages  
**Content Framework**: Diátaxis (Tutorials, How-to, Reference, Explanations)  
**Package Manager**: `uv` with docs group dependencies

### Essential Commands

```bash
make docs-serve          # Development server
make docs-build          # Production build  
make docs-deploy         # Deploy to GitHub Pages
make docs-validate       # Link and content validation
```

## Content Organization (Required)

```text
docs/
├── index.md                    # Homepage
├── tutorials/                  # Learning-oriented (step-by-step)
├── how-to/                    # Problem-solving guides
├── reference/                 # Information lookup (APIs, schemas)
├── explanations/              # Understanding concepts
├── assets/                    # Images, diagrams
└── stylesheets/              # Custom CSS
```

### Diátaxis Classification Rules

- **Tutorials**: Step-by-step learning for beginners ("Getting started with FinWiz")
- **How-to**: Goal-oriented problem solving ("Deploy to production")  
- **Reference**: Comprehensive information lookup ("API documentation")
- **Explanations**: Context and understanding ("Architecture decisions")

## File Standards

### Naming Conventions

- **Files**: `snake_case.md` (consistent with Python codebase)
- **Directories**: `kebab-case/` (URL-friendly)
- **Images**: `descriptive-name.png` (optimized < 500KB)

### Content Structure (Required)

Every documentation page must follow this template:

```markdown
# Page Title (H1 - only one per page)

Brief description of content and target audience.

## Prerequisites

- Required knowledge/setup
- Links to dependencies

## Main Content

### Section (H2)

#### Subsection (H3)

## Next Steps

- Related content links
- Suggested follow-up actions
```

## Writing Standards

### Voice and Tone

- **Active voice**: "Configure the API" not "The API should be configured"
- **Present tense**: "The system validates" not "The system will validate"  
- **Direct address**: "You can configure" not "One can configure"
- **Professional but approachable**: Authoritative yet friendly

### Code Documentation

Always specify language for syntax highlighting:

```python
def analyze_stock(ticker: str) -> StockAnalysis:
    """Analyze stock with proper error handling."""
    return StockAnalysis(ticker=ticker)
```

Include comments for clarity:

```bash
# Start development server
make docs-serve
```

Show expected output when helpful:

```text
Expected: Server started at http://127.0.0.1:8000
```

### FinWiz-Specific Patterns

Document common codebase patterns:

```python
# CrewAI agent definition
@agent
def analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["analyst"],
        tools=get_stock_crew_tools(include_rag=True),
        verbose=True
    )

# Pydantic validation (strict mode)
class TickerInput(BaseModel):
    symbol: str = Field(..., pattern=r'^[A-Z]{1,5}$')
    model_config = {"str_strip_whitespace": True}
```

## Technical Configuration

### MkDocs Configuration (`mkdocs.yml`)

```yaml
site_name: FinWiz Documentation
theme:
  name: material
  features:
    - navigation.tabs
    - search.highlight
    - content.code.copy

plugins:
  - search
  - awesome-pages  # Custom navigation ordering

markdown_extensions:
  - pymdownx.superfences
  - admonition
  - toc
```

### GitHub Actions Deployment

- **Trigger**: Push to main branch
- **Build**: `mkdocs build`
- **Deploy**: GitHub Pages with custom domain support
- **Validation**: Link checking and content validation

## Content Quality Standards

### Required Elements

- [ ] **Clear H1 title** (only one per page)
- [ ] **Target audience** stated in introduction
- [ ] **Prerequisites** section when applicable
- [ ] **Code examples** with syntax highlighting
- [ ] **Next steps** or related content links
- [ ] **Alt text** for all images

### Validation Checklist

- [ ] **Links work**: All internal/external links functional
- [ ] **Code tested**: All examples verified to work
- [ ] **Mobile responsive**: Content readable on mobile
- [ ] **Search optimized**: Uses searchable terms
- [ ] **Accessible**: WCAG 2.1 AA compliance

## Schema Documentation Integration

### Custom Schema Plugin

Use schema blocks for interactive schema documentation:

```markdown
```schema:StockAnalysis
{
  "description": "Stock analysis result schema",
  "example": {
    "ticker": "AAPL", 
    "recommendation": "BUY",
    "confidence": 0.85
  }
}
```
```

### Schema Processing

- **Location**: `docs/schemas/*.schema.json`
- **Plugin**: `mkdocs_schema_plugin.py`
- **Validation**: JSON schema validation with examples
- **Cross-references**: Automatic linking between related schemas

## Maintenance Workflows

### Update Triggers

Update documentation when:

- **Code changes**: API or functionality changes
- **User feedback**: Reports of confusion or errors
- **Analytics data**: High bounce rates or low engagement
- **External changes**: Third-party tool updates

### Review Process

1. **Self-review**: Author completes quality checklist
2. **Peer review**: Technical accuracy and clarity
3. **Final approval**: Documentation maintainer approval for major changes
4. **Deployment**: Automatic via GitHub Actions

## Performance Standards

- **Page load time**: < 2 seconds
- **Search response**: < 500ms
- **Mobile performance**: 90+ Lighthouse score
- **Build time**: < 30 seconds

## Common Patterns

### Internal Links (Relative Paths)

```markdown
[Setup Guide](../how-to/setup.md)
[API Reference](../reference/api.md#endpoints)
```

### Admonitions

```markdown
!!! note
    Additional helpful information

!!! warning
    Important information that could prevent errors

!!! tip
    Best practices and suggestions
```

### Tables for Reference Data

```markdown
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | Yes | Stock symbol |
| `period` | int | No | Analysis period in days |
```

## Integration with Codebase

### Environment Variables Documentation

```markdown
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API key | `sk-proj-...` |
| `DEBUG_MODE` | No | Enable debug logging | `true` |
```

### CrewAI Configuration Examples

```yaml
# agents.yaml
analyst:
  role: "Financial Analyst"
  goal: "Analyze assets and provide investment recommendations"
  backstory: "Expert analyst with deep market knowledge"

# tasks.yaml
analysis_task:
  description: "Perform comprehensive financial analysis"
  expected_output: "Structured analysis with recommendations"
  output_pydantic: "StockAnalysis"
```

## Anti-Patterns (Avoid)

❌ **Multiple H1 headings** - Use only one H1 per page  
❌ **Broken links** - Validate all links before publishing  
❌ **Untested code** - All examples must be verified  
❌ **Generic titles** - Use specific, descriptive headings  
❌ **Missing alt text** - All images need descriptive alt text  
❌ **Inconsistent terminology** - Use standard FinWiz terms  
❌ **Outdated screenshots** - Keep visual content current

## Development Integration

### Makefile Targets

```makefile
docs-install:    # Install documentation dependencies
docs-serve:      # Start development server
docs-build:      # Build static site
docs-deploy:     # Deploy to GitHub Pages
docs-validate:   # Validate links and content
```

### Pre-commit Hooks

- **Markdown linting**: Consistent style enforcement
- **Link validation**: Broken link detection
- **Content quality**: Diátaxis compliance checking
- **Image optimization**: Size and format validation

### CI/CD Integration

- **Build validation**: Ensure site builds successfully
- **Link checking**: Automated broken link detection
- **Performance testing**: Page load time validation
- **Accessibility testing**: WCAG compliance verification