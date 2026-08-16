# FinWiz Documentation Style Guide

This style guide establishes consistent writing, formatting, and presentation standards for all FinWiz documentation.

## Writing Style

### Voice and Tone

#### Active Voice

Use active voice to make instructions clear and direct.

✅ **Correct**:

- "Configure the API key in your environment"
- "The system validates the input data"
- "Run the command to start the server"

❌ **Avoid**:

- "The API key should be configured in your environment"
- "The input data is validated by the system"
- "The command should be run to start the server"

#### Present Tense

Use present tense for current functionality and procedures.

✅ **Correct**:

- "The application connects to the database"
- "Click the button to save changes"
- "The function returns a boolean value"

❌ **Avoid**:

- "The application will connect to the database"
- "You would click the button to save changes"
- "The function would return a boolean value"

#### Direct Address

Address the reader directly using "you" rather than impersonal constructions.

✅ **Correct**:

- "You can configure multiple environments"
- "When you run the command, you'll see output"
- "Follow these steps to complete setup"

❌ **Avoid**:

- "One can configure multiple environments"
- "When the command is run, output will be seen"
- "These steps should be followed to complete setup"

#### Professional but Approachable

Maintain a professional tone while being friendly and accessible.

✅ **Correct**:

- "This guide walks you through the setup process"
- "Let's configure your development environment"
- "You'll find this feature helpful for debugging"

❌ **Too casual**:

- "This guide is gonna show you how to set things up"
- "Let's hack together your dev environment"
- "This feature is pretty cool for debugging"

❌ **Too formal**:

- "This document shall provide comprehensive instructions"
- "One must configure the development environment"
- "This feature provides utility for debugging purposes"

### Language Guidelines

#### Clarity and Simplicity

**Use simple, common words** when possible:

✅ **Preferred**: use, help, show, start, stop, make, get
❌ **Avoid**: utilize, facilitate, demonstrate, initiate, terminate, construct, obtain

**Keep sentences concise** (aim for 15-20 words):

✅ **Good**: "Run this command to install the required dependencies."
❌ **Too long**: "Execute the following command in your terminal to install all of the required dependencies that are needed for the application to function properly."

**Be specific and precise**:

✅ **Specific**: "Set the timeout to 30 seconds"
❌ **Vague**: "Set an appropriate timeout value"

#### Consistency

**Use consistent terminology** throughout all documentation:

| Preferred Term | Avoid |
|----------------|-------|
| API key | API token, access key, secret key |
| configuration | config, settings (unless referring to specific files) |
| command line | terminal, console, shell (unless specifically referring to those) |
| repository | repo (in formal documentation) |
| directory | folder (in technical contexts) |

**Maintain consistent formatting** for similar elements:

- File names: `filename.py`
- Commands: `make docs-serve`
- Variables: `API_KEY`
- UI elements: **Bold text**

#### Inclusivity

**Use gender-neutral language**:

✅ **Inclusive**: "When a developer needs to...", "The user can..."
❌ **Avoid**: "When he needs to...", "The user can configure his settings..."

**Consider non-native English speakers**:

- Avoid idioms and cultural references
- Define technical terms when first used
- Use simple sentence structures
- Provide context for abbreviations

**Use accessible language** for the target audience:

- Match technical complexity to audience expertise
- Explain concepts before using them
- Provide links to background information
- Use progressive disclosure (simple to complex)

## Content Structure

### Headings

#### Hierarchy

Use proper heading hierarchy with only one H1 per page:

```markdown
# Page Title (H1 - only one per page)
## Major Section (H2)
### Subsection (H3)
#### Sub-subsection (H4 - use sparingly)
```

#### Heading Style

**Use sentence case** for headings:

✅ **Correct**: "Getting started with FinWiz"
❌ **Avoid**: "Getting Started With FinWiz"

**Be descriptive and scannable**:

✅ **Good**: "Configure environment variables"
❌ **Vague**: "Configuration"

**Use parallel structure** for related headings:

✅ **Parallel**:

- "Install dependencies"
- "Configure settings"
- "Start the server"

❌ **Not parallel**:

- "Installing dependencies"
- "Configuration of settings"
- "How to start the server"

### Page Structure

#### Standard Page Template

```markdown
# Page Title

Brief introduction explaining what this page covers and who should read it.

## Prerequisites

- Requirement 1
- Requirement 2
- Link to setup guide if needed

## Main Content Sections

### Section 1

Content with clear explanations and examples...

### Section 2

More content following logical progression...

## Next Steps

- Links to related content
- Suggested follow-up actions

## Related Resources

- Internal links to related documentation
- External links to additional resources
```

#### Content Flow

**Organize information logically**:

1. **Overview**: What and why
2. **Prerequisites**: What's needed first
3. **Main content**: Step-by-step or detailed information
4. **Verification**: How to confirm success
5. **Troubleshooting**: Common issues and solutions
6. **Next steps**: Where to go from here

**Use progressive disclosure**:

- Start with essential information
- Add details and advanced topics later
- Use collapsible sections for optional content
- Link to comprehensive references

## Formatting Standards

### Code and Commands

#### Code Blocks

Always specify the language for syntax highlighting:

```markdown
```python
def example_function():
    """Example function with docstring."""
    return "Hello, World!"
```

```bash
# Shell commands with comments
make docs-serve --port 8080
```

```yaml
# Configuration files
site_name: FinWiz Documentation
theme:
  name: material
```

```

#### Inline Code

Use backticks for inline code elements:

- File names: `config.yaml`
- Commands: `make install`
- Variables: `API_KEY`
- Function names: `analyze_stock()`
- Short code snippets: `return True`

#### Command Examples

**Include comments** for clarity:

```bash
# Install documentation dependencies
uv sync --group docs

# Start development server on custom port
mkdocs serve --dev-addr 127.0.0.1:8080
```

**Show expected output** when helpful:

```bash
$ make docs-serve
🚀 Starting MkDocs development server...
INFO    -  Building documentation...
INFO    -  Serving on http://127.0.0.1:8000
```

**Use consistent prompt symbols**:

- `$` for regular user commands
- `#` for root/admin commands
- No prompt for code that should be copied

### Lists

#### Unordered Lists

Use for non-sequential items:

```markdown
- First item
- Second item
- Third item
  - Nested item
  - Another nested item
```

#### Ordered Lists

Use for sequential steps or ranked items:

```markdown
1. First step
2. Second step
3. Third step
   1. Sub-step
   2. Another sub-step
```

#### Task Lists

Use for checklists and requirements:

```markdown
- [ ] Incomplete task
- [x] Completed task
- [ ] Another incomplete task
```

### Links

#### Internal Links

Use relative paths for internal documentation links:

```markdown
# Link to file in same directory
[Related guide](related-guide.md)

# Link to file in parent directory
[Setup guide](../setup/installation.md)

# Link to specific section
[Configuration section](../setup/installation.md#configuration)
```

#### External Links

Use full URLs for external links:

```markdown
[MkDocs Documentation](https://www.mkdocs.org/)
[Python Official Site](https://python.org/)
```

#### Link Text

**Use descriptive link text**:

✅ **Good**: "See the [installation guide]setup guide for details"
❌ **Avoid**: "Click [here]setup guide for more information"

**Avoid "link" in link text**:

✅ **Good**: `"Download the [configuration file](config.yaml)"`
❌ **Avoid**: `"Download the [configuration file link](config.yaml)"`

### Images

#### Image Syntax

```markdown
![Descriptive alt text](../assets/image-name.png)
*Optional caption text*
```

#### Alt Text Guidelines

**Write descriptive alt text** that explains the image content:

✅ **Good**: "Screenshot of the dashboard showing portfolio performance metrics"
❌ **Poor**: "Dashboard screenshot"

**For decorative images**, use empty alt text:

```markdown
![](../assets/decorative-border.png)
```

#### Image Optimization

- **File size**: Keep under 500KB when possible
- **Format**: Use PNG for screenshots, JPG for photos, SVG for diagrams
- **Dimensions**: Optimize for web display (max 1200px wide)
- **Naming**: Use descriptive, kebab-case file names

### Tables

#### Basic Table Format

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```

#### Table Alignment

```markdown
| Left Aligned | Center Aligned | Right Aligned |
|:-------------|:--------------:|--------------:|
| Left         | Center         | Right         |
| Text         | Text           | Text          |
```

#### Table Guidelines

- **Keep tables simple**: Avoid complex nested information
- **Use headers**: Always include descriptive column headers
- **Consistent formatting**: Align similar data types consistently
- **Alternative formats**: Consider lists for simple two-column data

### Admonitions

#### Standard Admonitions

```markdown
!!! note
    Additional information that's helpful but not critical.

!!! tip
    Helpful suggestions or best practices.

!!! warning
    Important information that could prevent errors.

!!! danger
    Critical information about potential problems or security issues.
```

#### Custom Titles

```markdown
!!! note "Custom Title"
    Admonition with custom title text.
```

#### Collapsible Admonitions

```markdown
??? note "Click to expand"
    This content is collapsed by default.

???+ warning "Expanded by default"
    This content is expanded by default but can be collapsed.
```

## Technical Writing Guidelines

### API Documentation

#### Function Documentation

```markdown
## `analyze_stock(ticker, period=365)`

Analyzes stock performance and generates investment recommendations.

**Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `ticker` | string | Yes | Stock ticker symbol (e.g., "AAPL") | - |
| `period` | integer | No | Analysis period in days | 365 |

**Returns:**

`StockAnalysis` object containing:
- `recommendation`: "BUY", "HOLD", or "SELL"
- `confidence`: Float between 0.0 and 1.0
- `risk_score`: Integer between 1 and 10

**Example:**

```python
analysis = analyze_stock("AAPL", period=180)
print(f"Recommendation: {analysis.recommendation}")
print(f"Confidence: {analysis.confidence:.2f}")
```

**Raises:**

- `InvalidTickerError`: If ticker symbol is invalid
- `APIError`: If external data sources are unavailable

```

#### Error Documentation

```markdown
## Error Handling

### Common Errors

#### `InvalidTickerError`

**Cause**: Invalid or non-existent ticker symbol
**Solution**: Verify ticker symbol exists and is properly formatted
**Example**: "AAPL" not "Apple" or "aapl"

#### `APIError`

**Cause**: External API unavailable or rate limited
**Solution**: Check API key configuration and retry after delay
**Prevention**: Implement proper error handling and retry logic
```

### Configuration Documentation

#### Environment Variables

```markdown
## Environment Variables

| Variable | Required | Description | Example | Default |
|----------|----------|-------------|---------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM calls | `sk-proj-...` | - |
| `DEBUG_MODE` | No | Enable debug logging | `true` | `false` |
| `CACHE_TTL` | No | Cache timeout in seconds | `3600` | `1800` |
```

#### Configuration Files

```markdown
## Configuration File: `config.yaml`

```yaml
# Database configuration
database:
  host: localhost
  port: 5432
  name: finwiz_db

# API settings
api:
  timeout: 30
  retries: 3
```

**Configuration Options:**

- `database.host`: Database server hostname
- `database.port`: Database server port (default: 5432)
- `api.timeout`: Request timeout in seconds (default: 30)

```

### Tutorial Writing

#### Step-by-Step Instructions

```markdown
## Step 1: Install Dependencies

Install the required Python packages using uv:

```bash
uv sync --group docs
```

This command will:

- Install MkDocs and the Material theme
- Set up all required plugins
- Configure the development environment

**Expected output:**

```
✅ Documentation dependencies installed
```

## Step 2: Configure MkDocs

Create the configuration file...

```

#### Verification Steps

```markdown
## Verify Installation

Confirm everything is working correctly:

1. **Check MkDocs version**:
   ```bash
   uv run mkdocs --version
   ```

   Expected output: `mkdocs, version 1.5.x`

1. **Test build process**:

   ```bash
   make docs-build
   ```

   Should complete without errors.

2. **Start development server**:

   ```bash
   make docs-serve
   ```

   Visit <http://127.0.0.1:8000> to see the documentation site.

```

## Content-Specific Guidelines

### Diátaxis Framework Application

#### Tutorials (Learning-oriented)

**Characteristics**:
- Step-by-step learning experience
- Beginner-friendly approach
- Hands-on, practical exercises
- Clear learning objectives

**Writing approach**:
- Use "you will learn" language
- Include all necessary steps
- Provide expected outcomes
- Offer encouragement and context

**Example opening**:
> "In this tutorial, you'll learn how to set up your first FinWiz analysis. By the end, you'll be able to analyze any stock and generate investment recommendations."

#### How-to Guides (Problem-oriented)

**Characteristics**:
- Solve specific problems
- Assume existing knowledge
- Goal-oriented instructions
- Multiple approaches when relevant

**Writing approach**:
- Start with the problem/goal
- Provide direct solutions
- Include troubleshooting
- Link to related procedures

**Example opening**:
> "This guide shows you how to configure FinWiz for production deployment. Use this when you're ready to deploy your analysis system to a live environment."

#### Reference (Information-oriented)

**Characteristics**:
- Comprehensive information
- Accurate and complete
- Organized for lookup
- Minimal explanation

**Writing approach**:
- Use consistent formatting
- Include all parameters/options
- Provide examples
- Focus on facts, not procedures

**Example opening**:
> "This reference documents all available configuration options for the FinWiz analysis engine."

#### Explanations (Understanding-oriented)

**Characteristics**:
- Provide context and background
- Explain concepts and decisions
- Discuss alternatives and trade-offs
- Help readers understand "why"

**Writing approach**:
- Start with high-level concepts
- Provide historical context
- Explain design decisions
- Discuss implications

**Example opening**:
> "This explanation covers the architecture decisions behind FinWiz's analysis engine and why we chose this approach over alternatives."

### Code Documentation

#### Python Code Examples

```python
# Good: Clear, commented, complete example
def analyze_portfolio(holdings: List[Holding]) -> PortfolioAnalysis:
    """
    Analyze portfolio holdings and generate recommendations.

    Args:
        holdings: List of portfolio holdings to analyze

    Returns:
        PortfolioAnalysis with recommendations and risk assessment

    Raises:
        ValidationError: If holdings data is invalid
    """
    # Validate input data
    if not holdings:
        raise ValidationError("Holdings list cannot be empty")

    # Perform analysis
    analysis = PortfolioAnalysis()
    for holding in holdings:
        result = analyze_stock(holding.ticker)
        analysis.add_holding_result(result)

    return analysis

# Usage example
holdings = [
    Holding(ticker="AAPL", shares=100),
    Holding(ticker="GOOGL", shares=50)
]
analysis = analyze_portfolio(holdings)
print(f"Portfolio grade: {analysis.overall_grade}")
```

#### Shell Commands

```bash
# Good: Include context and expected results

# Set up development environment
make setup

# Start the analysis engine
uv run python src/finwiz/main.py

# Run tests to verify installation
make test

# Expected output:
# ✅ All tests passed
# 📊 Coverage: 85%
```

#### Configuration Examples

```yaml
# Good: Complete, commented configuration

# MkDocs configuration for FinWiz documentation
site_name: FinWiz Documentation
site_description: AI-powered financial analysis platform

# Theme configuration
theme:
  name: material
  features:
    - navigation.tabs      # Top-level navigation tabs
    - search.highlight     # Highlight search terms
    - content.code.copy    # Copy button for code blocks

# Plugin configuration
plugins:
  - search:               # Full-text search
      lang: en
  - awesome-pages         # Custom navigation ordering
```

## Quality Checklist

### Pre-Publication Checklist

#### Content Quality

- [ ] **Clear purpose**: Reader knows what they'll learn/accomplish
- [ ] **Target audience**: Appropriate for intended skill level
- [ ] **Complete information**: All necessary details included
- [ ] **Logical flow**: Information presented in sensible order
- [ ] **Actionable content**: Reader can successfully follow instructions

#### Technical Accuracy

- [ ] **Code examples tested**: All code has been verified to work
- [ ] **Current information**: No outdated references or deprecated features
- [ ] **Correct procedures**: Step-by-step instructions are accurate
- [ ] **Valid links**: All internal and external links work correctly

#### Editorial Standards

- [ ] **Grammar and spelling**: No language errors
- [ ] **Style compliance**: Follows this style guide consistently
- [ ] **Consistent terminology**: Uses standard FinWiz terms
- [ ] **Proper formatting**: Correct markdown syntax and structure

#### Framework Compliance

- [ ] **Diátaxis alignment**: Content fits chosen category correctly
- [ ] **Template usage**: Follows appropriate content template
- [ ] **Navigation integration**: Properly integrated into site structure
- [ ] **Cross-references**: Links to related content where appropriate

### Accessibility Checklist

- [ ] **Alt text**: All images have descriptive alt text
- [ ] **Heading structure**: Proper heading hierarchy (H1 → H2 → H3)
- [ ] **Link text**: Descriptive link text (not "click here")
- [ ] **Color contrast**: Text readable in both light and dark themes
- [ ] **Screen reader friendly**: Content works with assistive technology

### SEO and Discoverability

- [ ] **Descriptive titles**: Clear, searchable page titles
- [ ] **Meta descriptions**: Helpful page descriptions (if applicable)
- [ ] **Internal linking**: Connected to related content
- [ ] **Search keywords**: Uses terms users would search for

---

**Last Updated**: 2025-10-26
**Version**: 1.0
**Maintainer**: FinWiz Documentation Team
